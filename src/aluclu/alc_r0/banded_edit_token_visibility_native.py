"""Explicitly loaded, locally built fixture-only native CPU backend."""

import ctypes as ct
import hashlib
import json
import os
import re
import subprocess
from array import array
from pathlib import Path
from sys import getsizeof

from .banded_edit_token_visibility_reference import (
    BandedEditVisibilityLimits,
    BandedEditVisibilityResult,
    _validate,
)
from .edit_token_visibility_reference import BudgetExposure


class NativeBandedInfrastructureError(RuntimeError):
    """Artifact or transport failure, never a mathematical unresolved result."""


def rank_tokens(first, second):
    ranks = {}

    def endpoint(tokens):
        result = []
        for token in tokens:
            if type(token) is not int or token < 0:
                raise ValueError("exact nonnegative integer tokens required")
            if token not in ranks:
                ranks[token] = len(ranks)
            result.append(ranks[token])
        return tuple(result)

    left, right = endpoint(first), endpoint(second)
    return left, right, len(ranks)


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


_SOURCE_FILES = (
    "native/alc_r0/banded_edit_visibility.cpp",
    "src/aluclu/alc_r0/banded_edit_token_visibility_native.py",
    "src/aluclu/alc_r0/banded_edit_token_visibility_reference.py",
    "docs/superpowers/plans/2026-10-02-alc-r0-banded-native-fixture-design.md",
    "scripts/alc_r0_build_banded_native.py",
    "tests/test_alc_r0_banded_native.py",
)
_COMPILER = Path(
    "C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/cl.exe"
)
_PROCESS_BACKEND = None


def read_build_receipt(receipt_path):
    """Data-only local provenance validation; does not load or execute a DLL."""

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate receipt key")
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError("nonfinite receipt number")

    def require(condition):
        if not condition:
            raise ValueError("invalid local build receipt")

    def canonical(value):
        require(type(value) is str)
        path = Path(value)
        require(path.is_absolute() and path.resolve() == path)
        return path

    def hashed(path, expected):
        require(type(expected) is str and re.fullmatch("[0-9a-f]{64}", expected))
        require(_hash(path) == expected)

    try:
        r = json.loads(
            Path(receipt_path).read_text(encoding="utf-8"),
            object_pairs_hook=pairs,
            parse_constant=nonfinite,
        )
        required = {
            "abi",
            "commit",
            "tree",
            "dirty_at_start",
            "dirty_at_end",
            "source_hashes",
            "native_source_sha256",
            "generated_include_path",
            "generated_include_sha256",
            "native_snapshot_path",
            "native_snapshot_sha256",
            "compiler_path",
            "compiler_sha256",
            "compiler_version",
            "linker_path",
            "linker_sha256",
            "linker_version",
            "sdk_version",
            "architecture",
            "command",
            "compiler_environment",
            "dll_path",
            "dll_size",
            "dll_sha256",
            "build_exit",
            "build_logs",
            "dependency_command",
            "dependency_exit",
            "dependencies_path",
            "dependencies_sha256",
            "training_authority",
            "held_out_data_present",
        }
        require(type(r) is dict and set(r) == required)
        require(type(r["abi"]) is int and r["abi"] == 1)
        for key in ("commit", "tree"):
            require(type(r[key]) is str and re.fullmatch("[0-9a-f]{40}", r[key]))
        for key in (
            "dirty_at_start",
            "dirty_at_end",
            "training_authority",
            "held_out_data_present",
        ):
            require(r[key] is False)
        root = Path(__file__).resolve().parents[3]
        sources = {str(root / p) for p in _SOURCE_FILES}
        require(type(r["source_hashes"]) is dict and set(r["source_hashes"]) == sources)
        for path, expected in r["source_hashes"].items():
            hashed(canonical(path), expected)
        committed_tree = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", r["commit"] + "^{tree}"], text=True
        ).strip()
        require(committed_tree == r["tree"])
        for relative in _SOURCE_FILES:
            committed = subprocess.check_output(
                ["git", "-C", str(root), "show", r["commit"] + ":" + relative]
            )
            require(
                hashlib.sha256(committed).hexdigest()
                == r["source_hashes"][str(root / relative)]
            )
        require(
            r["native_source_sha256"]
            == r["source_hashes"][str(root / _SOURCE_FILES[0])]
        )
        dll = canonical(r["dll_path"])
        out = dll.parent
        require(
            root != out
            and root not in out.parents
            and dll.name == "alc_r0_banded_fixture.dll"
        )
        require(
            type(r["dll_size"]) is int
            and r["dll_size"] > 0
            and dll.stat().st_size == r["dll_size"]
        )
        hashed(dll, r["dll_sha256"])
        for key, name in (
            ("generated_include", "alc_r0_build_id.h"),
            ("native_snapshot", "banded_edit_visibility.cpp"),
            ("dependencies", "dependencies.log"),
        ):
            path = canonical(r[key + "_path"])
            require(path == out / name)
            hashed(path, r[key + "_sha256"])
        require(r["native_snapshot_sha256"] == r["native_source_sha256"])
        expected_include = (
            "static const unsigned char ALC_R0_BUILD_ID[32] = {"
            + ",".join(str(b) for b in bytes.fromhex(r["native_source_sha256"]))
            + "};\n"
        ).encode("ascii")
        require((out / "alc_r0_build_id.h").read_bytes() == expected_include)
        for key, tool in (
            ("compiler", _COMPILER),
            ("linker", _COMPILER.with_name("link.exe")),
        ):
            require(canonical(r[key + "_path"]) == tool)
            hashed(tool, r[key + "_sha256"])
            require(
                type(r[key + "_version"]) is str
                and "19.44.35228" in r[key + "_version"]
                if key == "compiler"
                else type(r[key + "_version"]) is str
                and "14.44.35228" in r[key + "_version"]
            )
        require(r["sdk_version"] == "10.0.26100.0" and r["architecture"] == "x64")
        require(
            type(r["build_exit"]) is int
            and r["build_exit"] == 0
            and type(r["dependency_exit"]) is int
            and r["dependency_exit"] == 0
        )
        logs = {
            str(out / name)
            for name in ("build.stdout.log", "build.stderr.log", "build.exit.log")
        }
        require(type(r["build_logs"]) is dict and set(r["build_logs"]) == logs)
        for path, expected in r["build_logs"].items():
            hashed(canonical(path), expected)
        require((out / "build.exit.log").read_bytes() == b"0\n")
        require(
            r["command"]
            == [
                str(_COMPILER),
                "/nologo",
                "/O2",
                "/std:c++17",
                "/EHsc",
                "/MT",
                "/LD",
                "/I" + str(out),
                str(out / "banded_edit_visibility.cpp"),
                "/Fo" + str(out / "banded.obj"),
                "/Fe" + str(dll),
                "/link",
                "/IMPLIB:" + str(out / "banded.lib"),
            ]
        )
        require(
            r["dependency_command"]
            == [str(_COMPILER.with_name("dumpbin.exe")), "/dependents", str(dll)]
        )
        require(
            type(r["compiler_environment"]) is dict
            and set(r["compiler_environment"]) == {"INCLUDE", "LIB", "PATH"}
            and all(type(v) is str and v for v in r["compiler_environment"].values())
        )
        sdk = Path("C:/Program Files (x86)/Windows Kits/10")
        vc = _COMPILER.parents[3]
        require(
            r["compiler_environment"]["INCLUDE"]
            == os.pathsep.join(
                str(p)
                for p in [
                    vc / "include",
                    *[
                        sdk / "Include/10.0.26100.0" / p
                        for p in ("ucrt", "shared", "um")
                    ],
                ]
            )
        )
        require(
            r["compiler_environment"]["LIB"]
            == os.pathsep.join(
                str(p)
                for p in [
                    vc / "lib/x64",
                    *[sdk / "Lib/10.0.26100.0" / p / "x64" for p in ("ucrt", "um")],
                ]
            )
        )
        require(
            r["compiler_environment"]["PATH"].startswith(
                str(_COMPILER.parent) + os.pathsep
            )
        )
        return r
    except Exception as exc:
        raise NativeBandedInfrastructureError(str(exc)) from exc


class NativeBandedBackend:
    """One retained backend per bounded fixture process, held until process exit.

    No close/unload API is provided while native function pointers are callable.
    This is a fixture-process owner, not a general serving lifecycle abstraction.
    """

    def __init__(self, receipt_path):
        global _PROCESS_BACKEND
        self._handle = None
        try:
            self.receipt = read_build_receipt(receipt_path)
            if _PROCESS_BACKEND is not None:
                raise ValueError("one retained backend per fixture process")
            if os.name != "nt" or self.receipt["abi"] != 1:
                raise ValueError("Windows ABI1 artifact required")
            self._path = Path(self.receipt["dll_path"])
            if not self._path.is_absolute() or self._path.resolve() != self._path:
                raise ValueError("canonical absolute DLL path required")
            for path, expected in self.receipt["source_hashes"].items():
                if _hash(path) != expected:
                    raise ValueError("source identity mismatch")
            for component in (self._path, *self._path.parents):
                if component.stat().st_file_attributes & 0x400:
                    raise ValueError("reparse artifact path forbidden")
            self._kernel = ct.WinDLL("kernel32", use_last_error=True)
            self._kernel.CreateFileW.argtypes = [
                ct.c_wchar_p,
                ct.c_uint32,
                ct.c_uint32,
                ct.c_void_p,
                ct.c_uint32,
                ct.c_uint32,
                ct.c_void_p,
            ]
            self._kernel.CreateFileW.restype = ct.c_void_p
            self._kernel.CloseHandle.argtypes = [ct.c_void_p]
            self._kernel.CloseHandle.restype = ct.c_int
            # FILE_SHARE_READ only: hold a read handle denying writes and deletion.
            self._handle = self._kernel.CreateFileW(
                str(self._path), 0x80000000, 1, None, 3, 0x00200000, None
            )
            if self._handle == ct.c_void_p(-1).value:
                self._handle = None
                raise OSError(ct.get_last_error(), "cannot lock artifact")
            self._identity = self._file_identity(self._handle)
            self._verify_artifact()
            self.dll = ct.CDLL(str(self._path), winmode=0x100 | 0x800)
            self._kernel.GetModuleFileNameW.argtypes = [
                ct.c_void_p,
                ct.c_wchar_p,
                ct.c_uint32,
            ]
            self._kernel.GetModuleFileNameW.restype = ct.c_uint32
            loaded = ct.create_unicode_buffer(32768)
            count = self._kernel.GetModuleFileNameW(
                self.dll._handle, loaded, len(loaded)
            )
            if (
                not count
                or count >= len(loaded)
                or Path(loaded.value).resolve() != self._path
            ):
                raise ValueError("loaded module path mismatch")
            check = self._kernel.CreateFileW(
                loaded.value, 0x80000000, 1, None, 3, 0x00200000, None
            )
            if check == ct.c_void_p(-1).value:
                raise ValueError("loaded artifact identity unavailable")
            try:
                if self._file_identity(check) != self._identity:
                    raise ValueError("loaded artifact file identity mismatch")
            finally:
                self._kernel.CloseHandle(check)
            self.dll.aluclu_banded_abi_v1.argtypes = []
            self.dll.aluclu_banded_abi_v1.restype = ct.c_uint32
            self.dll.aluclu_banded_build_id_v1.argtypes = [
                ct.POINTER(ct.c_uint8),
                ct.c_uint32,
            ]
            self.dll.aluclu_banded_build_id_v1.restype = ct.c_uint32
            u32 = ct.POINTER(ct.c_uint32)
            self.dll.aluclu_banded_audit_v1.argtypes = [
                u32,
                ct.c_uint32,
                u32,
                ct.c_uint32,
                u32,
                ct.c_uint32,
                ct.c_uint32,
                u32,
                ct.POINTER(ct.c_uint8),
                ct.c_uint64,
                u32,
                ct.c_uint32,
            ]
            self.dll.aluclu_banded_audit_v1.restype = ct.c_uint32
            identifier = (ct.c_uint8 * 32)()
            if (
                self.dll.aluclu_banded_abi_v1() != 1
                or self.dll.aluclu_banded_build_id_v1(identifier, 32)
                or bytes(identifier).hex() != self.receipt["native_source_sha256"]
            ):
                raise ValueError("compiled identity mismatch")
            _PROCESS_BACKEND = self
        except Exception as exc:
            if self._handle and not hasattr(self, "dll"):
                self._kernel.CloseHandle(self._handle)
                self._handle = None
            elif self._handle:
                # Keep the failed loaded owner alive too; its DLL remains callable.
                _PROCESS_BACKEND = self
            raise NativeBandedInfrastructureError(str(exc)) from exc

    def _file_identity(self, handle):
        class Information(ct.Structure):
            _fields_ = [
                ("attributes", ct.c_uint32),
                ("creation", ct.c_uint32 * 2),
                ("access", ct.c_uint32 * 2),
                ("write", ct.c_uint32 * 2),
                ("volume", ct.c_uint32),
                ("size_high", ct.c_uint32),
                ("size_low", ct.c_uint32),
                ("links", ct.c_uint32),
                ("index_high", ct.c_uint32),
                ("index_low", ct.c_uint32),
            ]

        info = Information()
        self._kernel.GetFileInformationByHandle.argtypes = [
            ct.c_void_p,
            ct.POINTER(Information),
        ]
        self._kernel.GetFileInformationByHandle.restype = ct.c_int
        if (
            not self._kernel.GetFileInformationByHandle(handle, ct.byref(info))
            or info.attributes & 0x400
        ):
            raise NativeBandedInfrastructureError("regular file identity unavailable")
        return (
            info.volume,
            info.index_high,
            info.index_low,
            info.size_high,
            info.size_low,
        )

    def _verify_artifact(self):
        import msvcrt

        duplicate = ct.c_void_p()
        kernel = self._kernel
        if self._file_identity(self._handle) != self._identity:
            raise NativeBandedInfrastructureError("held artifact identity changed")
        kernel.GetCurrentProcess.restype = ct.c_void_p
        kernel.DuplicateHandle.argtypes = [
            ct.c_void_p,
            ct.c_void_p,
            ct.c_void_p,
            ct.POINTER(ct.c_void_p),
            ct.c_uint32,
            ct.c_int,
            ct.c_uint32,
        ]
        kernel.DuplicateHandle.restype = ct.c_int
        process = kernel.GetCurrentProcess()
        if not kernel.DuplicateHandle(
            process, self._handle, process, ct.byref(duplicate), 0, False, 2
        ):
            raise NativeBandedInfrastructureError("artifact handle duplication failed")
        fd = msvcrt.open_osfhandle(duplicate.value, os.O_RDONLY)
        with os.fdopen(fd, "rb") as stream:
            stream.seek(0)
            data = stream.read()
        if (
            len(data) != self.receipt["dll_size"]
            or hashlib.sha256(data).hexdigest() != self.receipt["dll_sha256"]
        ):
            raise NativeBandedInfrastructureError("artifact bytes mismatch")

    def audit(
        self,
        first,
        second,
        *,
        code_budgets,
        distance_threshold,
        limits=BandedEditVisibilityLimits(),
    ):
        _validate(first, second, code_budgets, distance_threshold, limits)
        self._verify_artifact()
        n, m, B, K = len(first), len(second), len(code_budgets), distance_threshold
        lower = upper = cells = width = scratch = None
        payload = 0
        if max(n, m) <= limits.max_endpoint_tokens:
            if abs(n - m) > K:
                cells = width = 0
            else:
                lower, upper = -((K - n + m) // 2), (n - m + K) // 2
                cells = width = 0
                for i in range(n + 1):
                    w = max(0, min(m, i - lower) - max(0, i - upper) + 1)
                    cells += w
                    width = max(width, w)
                payload = 2 * (1 + 7 * B) * 4 * width + B * (n + m)
                scratch = (
                    payload
                    + 2 * (1 + 7 * B) * getsizeof(array("I"))
                    + 2 * B * getsizeof(array("B"))
                    + 65536
                )
        admitted = (
            scratch is not None
            and cells <= limits.max_band_cells
            and scratch <= limits.max_scratch_bytes
        )
        if max(n, m) > limits.max_endpoint_tokens:
            expected_preflight_reason = "endpoint-token-limit"
        elif abs(n - m) > K:
            expected_preflight_reason = "distance-threshold-exceeded"
        elif cells > limits.max_band_cells:
            expected_preflight_reason = "band-cell-limit"
        elif scratch > limits.max_scratch_bytes:
            expected_preflight_reason = "scratch-byte-limit"
        else:
            expected_preflight_reason = None
        # Endpoint rejection precedes rank mapping and input buffers.
        left, right, ranks = (
            rank_tokens(first, second)
            if max(n, m) <= limits.max_endpoint_tokens
            else ((), (), 1)
        )
        first_buffer = (ct.c_uint32 * len(left))(*left)
        second_buffer = (ct.c_uint32 * len(right))(*right)
        effective = (ct.c_uint32 * B)(*(min(b, max(n, m, 1)) for b in code_budgets))
        policy = (ct.c_uint32 * 8)(
            limits.max_endpoint_tokens,
            limits.max_band_cells,
            limits.max_scratch_bytes,
            limits.max_distance_threshold,
            getsizeof(array("I")),
            getsizeof(array("B")),
            ranks,
            0,
        )
        workspace = (ct.c_uint32 * ((payload + 3) // 4))() if admitted else None
        output = (ct.c_uint32 * 64)()
        status = self.dll.aluclu_banded_audit_v1(
            first_buffer,
            n,
            second_buffer,
            m,
            effective,
            B,
            K,
            policy,
            ct.cast(workspace, ct.POINTER(ct.c_uint8)) if workspace else None,
            payload if admitted else 0,
            output,
            64,
        )
        if status:
            raise NativeBandedInfrastructureError(f"native transport status {status}")
        values = tuple(output)

        def wide(slot):
            return values[slot] | values[slot + 1] << 32

        def signed(slot):
            return ct.c_int32(values[slot]).value

        if (
            values[0] != 1
            or values[1] not in (0, 1)
            or values[2] not in range(5)
            or values[3:7] != (n, m, B, K)
            or any(values[55:])
            or values[7] & ~63
        ):
            raise NativeBandedInfrastructureError("invalid native output metadata")
        exact = values[1] == 0
        reason = (
            None,
            "endpoint-token-limit",
            "distance-threshold-exceeded",
            "band-cell-limit",
            "scratch-byte-limit",
        )[values[2]]
        geometry = (
            signed(8) if values[7] & 1 else None,
            signed(9) if values[7] & 2 else None,
            wide(10) if values[7] & 4 else None,
            values[14] if values[7] & 8 else None,
            wide(15) if values[7] & 16 else None,
        )
        if (
            geometry != (lower, upper, cells, width, scratch)
            or exact != (reason is None)
            or wide(17) != (payload if admitted else 0)
            or wide(12) != (cells if admitted else 0)
            or bool(values[7] & 32) != exact
            or (exact and not admitted)
            or (not admitted and reason != expected_preflight_reason)
            or (admitted and not exact and reason != "distance-threshold-exceeded")
        ):
            raise NativeBandedInfrastructureError("impossible native output geometry")
        for bit, slots in (
            (1, (8,)),
            (2, (9,)),
            (4, (10, 11)),
            (8, (14,)),
            (16, (15, 16)),
            (32, (19,)),
        ):
            if not values[7] & bit and any(values[s] for s in slots):
                raise NativeBandedInfrastructureError("absent native field is nonzero")
        exposures = (
            tuple(
                BudgetExposure(b, *values[20 + 7 * i : 27 + 7 * i])
                for i, b in enumerate(code_budgets)
            )
            if exact
            else ()
        )
        if any(values[20 + 7 * B : 55]) or (not exact and any(values[20:55])):
            raise NativeBandedInfrastructureError("unused exposure slots are nonzero")
        for row in exposures:
            if not (
                0 <= row.first_min <= row.first_max <= n
                and 0 <= row.second_min <= row.second_max <= m
                and row.total_min <= row.total_max <= n + m
                and row.total_min >= row.first_min + row.second_min
                and row.total_max <= row.first_max + row.second_max
                and max(row.first_max, row.second_max, row.total_max) <= values[19]
                and 1 <= row.joint_signature_bits <= 15
            ):
                raise NativeBandedInfrastructureError("invalid native exposure")
        if exact and (
            values[19] > min(K, n + m)
            or values[19] < abs(n - m)
            or (values[19] - (n - m)) % 2
        ):
            raise NativeBandedInfrastructureError("native distance exceeds threshold")
        return BandedEditVisibilityResult(
            "exact-non-authorizing" if exact else "resource-unresolved-non-authorizing",
            reason,
            n,
            m,
            code_budgets,
            K,
            lower,
            upper,
            cells,
            wide(12),
            width,
            scratch,
            wide(17),
            values[19] if exact else None,
            exposures,
            limits,
        )
