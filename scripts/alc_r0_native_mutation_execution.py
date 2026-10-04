"""Reviewed closed fixture mutation execution; explicit CLI only, no import work.

No native build/load is performed by the data-only tests. The real execution
positive path must be independently reviewed and approved before first use.
"""

import argparse
import ctypes as ct
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from array import array
from pathlib import Path
from sys import getsizeof

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_SHA = "466742508428b1d2cdadda088bab27429795d5dbe2faa4c4a312baa99ac6f6f7"
BUILDER_SHA = "b6b541aebbd0840104cbba9b50dd3992b8b536c0c64c1c2ff4719871dbba8620"
EXECUTION_PLAN_SHA = "041d8150f2035984ed8729d926a68bd4a53fda8892aaf1cd228d7a7677e5a723"
COMPILER = Path(
    "C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/cl.exe"
)
PYTHON = Path(
    "C:/Users/kaann/AppData/Local/Packages/OpenAI.Codex_2p2nqsd0c76g0/LocalCache/Local/ALUCLU/research/alc-r0-smollm2-135m-v1/windows-training/.venv/Scripts/python.exe"
)
FLAGS = ["/nologo", "/O2", "/std:c++17", "/EHsc", "/MT", "/LD"]
IDS = (
    "control",
    "drop-equal-indel-ties",
    "single-predecessor",
    "strip-equal-ends",
    "marginal-total",
    "marginal-joint",
    "inward-parity",
    "exclude-boundary",
    "stale-column",
    "accept-over-threshold",
)
OWN_SOURCES = (
    "scripts/alc_r0_native_mutation_execution.py",
    "tests/test_alc_r0_native_mutation_execution.py",
    "scripts/alc_r0_native_mutation_fixture_probe.py",
    "tests/test_alc_r0_native_mutation_fixture_probe.py",
    "scripts/alc_r0_build_banded_native.py",
    "docs/superpowers/plans/2026-10-02-alc-r0-native-mutation-execution-detail.md",
)
_OWNER = None


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message="invalid closed fixture evidence"):
    if not condition:
        raise ValueError(message)


def decode_document(text, keys):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError("nonfinite JSON value")

    document = json.loads(text, object_pairs_hook=pairs, parse_constant=nonfinite)
    require(type(document) is dict and set(document) == set(keys))
    require(type(document["schema"]) is int and document["schema"] == 1)
    require(
        document["training_authority"] is False
        and document["held_out_data_present"] is False
    )
    return document


def document(path, keys):
    return decode_document(Path(path).read_text(encoding="utf-8"), keys)


def write_document(path, data):
    Path(path).write_bytes(
        (
            json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n"
        ).encode("utf-8")
    )


def capture_manifest_binding(path):
    return sha(external(path))


def verify_manifest_unchanged(path, binding):
    require(capture_manifest_binding(path) == binding, "raw manifest bytes changed")


def external(path, fresh=False):
    path = Path(path)
    require(
        path.is_absolute()
        and path.resolve() == path
        and path != ROOT
        and ROOT not in path.parents,
        "canonical external path required",
    )
    for component in (path, *path.parents):
        if component.exists():
            require(
                not getattr(component.stat(), "st_file_attributes", 0) & 0x400,
                "reparse relocation forbidden",
            )
    if fresh:
        require(not path.exists(), "fresh output required")
    return path


def closed_id(value):
    require(type(value) is str and value in IDS, "unknown closed variant")
    return value


def helper(relative, expected):
    path = ROOT / relative
    require(sha(path) == expected, "frozen helper identity mismatch")
    spec = importlib.util.spec_from_file_location("fixture_" + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generator():
    return helper("scripts/alc_r0_native_mutation_fixture_probe.py", GENERATOR_SHA)


def builder():
    return helper("scripts/alc_r0_build_banded_native.py", BUILDER_SHA)


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def execution_provenance(clean=False):
    if clean:
        require(
            not git("status", "--porcelain", "--untracked-files=all"),
            "clean reviewed execution commit required",
        )
    return dict(
        commit=git("rev-parse", "HEAD"),
        tree=git("rev-parse", "HEAD^{tree}"),
        source_hashes={str(ROOT / p): sha(ROOT / p) for p in OWN_SOURCES},
        python_path=str(PYTHON),
        python_sha256=sha(PYTHON),
        python_version=sys.version,
    )


def verify_provenance(data):
    require(
        type(data) is dict
        and set(data)
        == {
            "commit",
            "tree",
            "source_hashes",
            "python_path",
            "python_sha256",
            "python_version",
        }
    )
    require(
        type(data["commit"]) is str
        and len(data["commit"]) == 40
        and all(c in "0123456789abcdef" for c in data["commit"])
    )
    require(git("rev-parse", data["commit"] + "^{tree}") == data["tree"])
    expected_paths = {str(ROOT / p) for p in OWN_SOURCES}
    require(
        type(data["source_hashes"]) is dict
        and set(data["source_hashes"]) == expected_paths
    )
    for relative in OWN_SOURCES:
        path = ROOT / relative
        committed = subprocess.check_output(
            ["git", "-C", str(ROOT), "show", data["commit"] + ":" + relative]
        )
        require(
            sha(path)
            == data["source_hashes"][str(path)]
            == hashlib.sha256(committed).hexdigest()
        )
    require(sha(ROOT / OWN_SOURCES[-1]) == EXECUTION_PLAN_SHA)
    require(
        data["python_path"] == str(PYTHON)
        and data["python_sha256"] == sha(PYTHON)
        and data["python_version"] == sys.version
    )
    require(Path(sys.executable).resolve() == PYTHON)


MANIFEST_KEYS = {
    "schema",
    "stage",
    "baseline_commit",
    "baseline_sha256",
    "provenance",
    "variants",
    "training_authority",
    "held_out_data_present",
}


def verify_manifest(path):
    from aluclu.alc_r0.banded_edit_token_visibility_native import read_build_receipt

    path = external(path)
    require(path.name == "manifest.json")
    data = document(path, MANIFEST_KEYS)
    pure = generator()
    baseline = (ROOT / "native/alc_r0/banded_edit_visibility.cpp").read_bytes()
    expected = pure.manifest(baseline, data["provenance"])
    require(data == json.loads(json.dumps(expected)), "regenerated manifest mismatch")
    provenance = data["provenance"]
    for source, expected_sha in provenance["verified_paths"].items():
        require(sha(source) == expected_sha)
    require(sha(ROOT / OWN_SOURCES[-1]) == EXECUTION_PLAN_SHA)
    receipt_path = external(provenance["baseline_receipt_path"])
    require(sha(receipt_path) == provenance["baseline_receipt_sha256"])
    receipt = read_build_receipt(receipt_path)
    require(
        receipt["commit"] == pure.BASELINE_COMMIT
        and receipt["native_source_sha256"] == pure.BASELINE_SHA256
    )
    variants = pure.generate_variants(baseline)
    require(
        {p.name for p in path.parent.iterdir()} == {"manifest.json", *IDS},
        "generation directory has unexpected artifacts",
    )
    for variant_id in IDS:
        directory = external(path.parent / variant_id)
        require(
            directory.is_dir()
            and {p.name for p in directory.iterdir()} == {"banded_edit_visibility.cpp"}
        )
        source = external(directory / "banded_edit_visibility.cpp")
        require(
            source.read_bytes() == variants[variant_id]["source_bytes"],
            "generated variant bytes changed",
        )
    return data, receipt, variants


def build_environment(original):
    env = dict(original)
    env.pop("CL", None)
    env.pop("_CL_", None)
    vc = COMPILER.parents[3]
    sdk = Path("C:/Program Files (x86)/Windows Kits/10")
    env["INCLUDE"] = os.pathsep.join(
        str(p)
        for p in [
            vc / "include",
            *[sdk / "Include/10.0.26100.0" / p for p in ("ucrt", "shared", "um")],
        ]
    )
    env["LIB"] = os.pathsep.join(
        str(p)
        for p in [
            vc / "lib/x64",
            *[sdk / "Lib/10.0.26100.0" / p / "x64" for p in ("ucrt", "um")],
        ]
    )
    env["PATH"] = str(COMPILER.parent) + os.pathsep + env.get("PATH", "")
    return env


def build_command(out):
    return [
        str(COMPILER),
        *FLAGS,
        "/I" + str(out),
        str(out / "banded_edit_visibility.cpp"),
        "/Fo" + str(out / "banded.obj"),
        "/Fe" + str(out / "variant.dll"),
        "/link",
        "/IMPLIB:" + str(out / "banded.lib"),
    ]


def tools_state(env):
    state = {}
    for name in ("cl.exe", "link.exe", "dumpbin.exe"):
        tool = COMPILER.with_name(name)
        run = subprocess.run([str(tool)], env=env, capture_output=True)
        state[str(tool)] = dict(
            sha256=sha(tool),
            version=(run.stdout + run.stderr).decode(errors="replace"),
            exit=run.returncode,
        )
    return state


BUILD_KEYS = {
    "schema",
    "variant_id",
    "manifest_path",
    "manifest_sha256",
    "provenance",
    "status",
    "command",
    "environment",
    "tools",
    "source_sha256",
    "include_sha256",
    "build_exit",
    "logs",
    "dependency_command",
    "dependency_exit",
    "dependency_sha256",
    "dll_sha256",
    "dll_size",
    "training_authority",
    "held_out_data_present",
}


def build_all(manifest_path, build_root):
    require(os.name == "nt")
    data, baseline_receipt, variants = verify_manifest(manifest_path)
    manifest_binding = capture_manifest_binding(manifest_path)
    provenance = execution_provenance(clean=True)
    verify_provenance(provenance)
    build_root = external(build_root, fresh=True)
    env = build_environment(os.environ)
    build_root.mkdir(parents=True)
    build_helper = builder()
    for variant_id in IDS:
        before = tools_state(env)
        require(
            before[str(COMPILER)]["sha256"] == baseline_receipt["compiler_sha256"]
            and before[str(COMPILER.with_name("link.exe"))]["sha256"]
            == baseline_receipt["linker_sha256"]
        )
        out = build_root / variant_id
        out.mkdir()
        source, include = out / "banded_edit_visibility.cpp", out / "alc_r0_build_id.h"
        source.write_bytes(variants[variant_id]["source_bytes"])
        include.write_bytes(
            build_helper.build_id_include(variants[variant_id]["source_sha256"])
        )
        command = build_command(out)
        run = build_helper.compile_locked_snapshot(command, out, env, source, include)
        (out / "build.stdout.log").write_bytes(run.stdout)
        (out / "build.stderr.log").write_bytes(run.stderr)
        build_helper.write_build_exit(out / "build.exit.log", run.returncode)
        dep_command = [
            str(COMPILER.with_name("dumpbin.exe")),
            "/dependents",
            str(out / "variant.dll"),
        ]
        dep_exit = None
        if run.returncode == 0:
            deps = subprocess.run(dep_command, env=env, capture_output=True)
            (out / "dependencies.log").write_bytes(deps.stdout + deps.stderr)
            dep_exit = deps.returncode
        require(tools_state(env) == before, "tools changed during build")
        require(
            execution_provenance(clean=True) == provenance,
            "source changed during build",
        )
        verify_manifest_unchanged(manifest_path, manifest_binding)
        verify_manifest(manifest_path)
        require(
            source.read_bytes() == variants[variant_id]["source_bytes"]
            and include.read_bytes()
            == build_helper.build_id_include(variants[variant_id]["source_sha256"])
        )
        dll = out / "variant.dll"
        record = dict(
            schema=1,
            variant_id=variant_id,
            manifest_path=str(Path(manifest_path)),
            manifest_sha256=sha(manifest_path),
            provenance=provenance,
            status="built"
            if run.returncode == 0 and dep_exit == 0
            else "compile-failed",
            command=command,
            environment={k: env[k] for k in ("INCLUDE", "LIB", "PATH")},
            tools=before,
            source_sha256=sha(source),
            include_sha256=sha(include),
            build_exit=run.returncode,
            logs={
                str(out / name): sha(out / name)
                for name in ("build.stdout.log", "build.stderr.log", "build.exit.log")
            },
            dependency_command=dep_command,
            dependency_exit=dep_exit,
            dependency_sha256=sha(out / "dependencies.log")
            if dep_exit is not None
            else None,
            dll_sha256=sha(dll) if dll.exists() else None,
            dll_size=dll.stat().st_size if dll.exists() else None,
            training_authority=False,
            held_out_data_present=False,
        )
        write_document(out / "build-record.json", record)
    return build_root


def verify_build(manifest_path, build_root, variant_id):
    variant_id = closed_id(variant_id)
    _, receipt, variants = verify_manifest(manifest_path)
    out = external(external(build_root) / variant_id)
    record = document(external(out / "build-record.json"), BUILD_KEYS)
    require(
        record["variant_id"] == variant_id
        and record["manifest_path"] == str(Path(manifest_path))
        and record["manifest_sha256"] == sha(manifest_path)
    )
    verify_provenance(record["provenance"])
    require(
        record["source_sha256"]
        == variants[variant_id]["source_sha256"]
        == sha(external(out / "banded_edit_visibility.cpp"))
    )
    require(
        (out / "banded_edit_visibility.cpp").read_bytes()
        == variants[variant_id]["source_bytes"]
    )
    require(
        (out / "alc_r0_build_id.h").read_bytes()
        == builder().build_id_include(record["source_sha256"])
        and sha(external(out / "alc_r0_build_id.h")) == record["include_sha256"]
    )
    require(record["command"] == build_command(out))
    env = record["environment"]
    require(
        type(env) is dict
        and set(env) == {"INCLUDE", "LIB", "PATH"}
        and all(type(v) is str for v in env.values())
    )
    require(
        env
        == {
            k: build_environment(
                {"PATH": env["PATH"][len(str(COMPILER.parent)) + 1 :]}
            )[k]
            for k in env
        }
    )
    require(
        type(record["tools"]) is dict
        and set(record["tools"])
        == {
            str(COMPILER.with_name(name))
            for name in ("cl.exe", "link.exe", "dumpbin.exe")
        }
    )
    for tool, state in record["tools"].items():
        require(
            type(state) is dict
            and set(state) == {"sha256", "version", "exit"}
            and state["sha256"] == sha(tool)
            and type(state["exit"]) is int
            and type(state["version"]) is str
        )
        require(
            ("19.44.35228" if Path(tool).name == "cl.exe" else "14.44.35228")
            in state["version"]
        )
    require(
        record["tools"][str(COMPILER)]["sha256"] == receipt["compiler_sha256"]
        and record["tools"][str(COMPILER.with_name("link.exe"))]["sha256"]
        == receipt["linker_sha256"]
    )
    logs = {
        str(out / name)
        for name in ("build.stdout.log", "build.stderr.log", "build.exit.log")
    }
    require(type(record["logs"]) is dict and set(record["logs"]) == logs)
    for path, expected in record["logs"].items():
        require(sha(external(path)) == expected)
    require(
        type(record["build_exit"]) is int
        and (out / "build.exit.log").read_bytes()
        == str(record["build_exit"]).encode() + b"\n"
    )
    require(
        record["dependency_command"]
        == [
            str(COMPILER.with_name("dumpbin.exe")),
            "/dependents",
            str(out / "variant.dll"),
        ]
    )
    if record["status"] == "compile-failed":
        require(
            record["build_exit"] != 0
            or (
                type(record["dependency_exit"]) is int
                and record["dependency_exit"] != 0
            )
        )
        return record, out
    require(
        record["status"] == "built"
        and record["build_exit"] == 0
        and type(record["dependency_exit"]) is int
        and record["dependency_exit"] == 0
    )
    require(sha(external(out / "dependencies.log")) == record["dependency_sha256"])
    dll = external(out / "variant.dll")
    require(
        type(record["dll_size"]) is int
        and record["dll_size"] > 0
        and dll.stat().st_size == record["dll_size"]
        and sha(dll) == record["dll_sha256"]
    )
    return record, out


class _ClosedArtifactOwner:
    """One retained locally authored variant owner until isolated child exit."""

    def __init__(self, manifest_path, build_root, variant_id):
        global _OWNER
        require(_OWNER is None and os.name == "nt")
        self.record, self.out = verify_build(manifest_path, build_root, variant_id)
        require(self.record["status"] == "built")
        self.path = self.out / "variant.dll"
        self.handle = None
        self.kernel = ct.WinDLL("kernel32", use_last_error=True)
        k = self.kernel
        k.CreateFileW.argtypes = [
            ct.c_wchar_p,
            ct.c_uint32,
            ct.c_uint32,
            ct.c_void_p,
            ct.c_uint32,
            ct.c_uint32,
            ct.c_void_p,
        ]
        k.CreateFileW.restype = ct.c_void_p
        k.CloseHandle.argtypes = [ct.c_void_p]
        k.CloseHandle.restype = ct.c_int
        try:
            self.handle = k.CreateFileW(
                str(self.path), 0x80000000, 1, None, 3, 0x00200000, None
            )
            require(
                self.handle != ct.c_void_p(-1).value, "cannot hold variant artifact"
            )
            self.identity = self.file_identity(self.handle)
            self.verify_bytes()
            self.dll = ct.CDLL(str(self.path), winmode=0x100 | 0x800)
            _OWNER = self  # Retain even if subsequent ABI validation fails.
            k.GetModuleFileNameW.argtypes = [ct.c_void_p, ct.c_wchar_p, ct.c_uint32]
            k.GetModuleFileNameW.restype = ct.c_uint32
            name = ct.create_unicode_buffer(32768)
            length = k.GetModuleFileNameW(self.dll._handle, name, len(name))
            require(0 < length < len(name) and Path(name.value) == self.path)
            check = k.CreateFileW(name.value, 0x80000000, 1, None, 3, 0x00200000, None)
            require(check != ct.c_void_p(-1).value)
            try:
                require(self.file_identity(check) == self.identity)
            finally:
                k.CloseHandle(check)
            u32 = ct.POINTER(ct.c_uint32)
            self.dll.aluclu_banded_abi_v1.argtypes = []
            self.dll.aluclu_banded_abi_v1.restype = ct.c_uint32
            self.dll.aluclu_banded_build_id_v1.argtypes = [
                ct.POINTER(ct.c_uint8),
                ct.c_uint32,
            ]
            self.dll.aluclu_banded_build_id_v1.restype = ct.c_uint32
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
            require(
                self.dll.aluclu_banded_abi_v1() == 1
                and self.dll.aluclu_banded_build_id_v1(identifier, 32) == 0
                and bytes(identifier).hex() == self.record["source_sha256"]
            )
        except BaseException:
            if (
                self.handle
                and self.handle != ct.c_void_p(-1).value
                and not hasattr(self, "dll")
            ):
                k.CloseHandle(self.handle)
                self.handle = None
            raise

    def file_identity(self, handle):
        class Info(ct.Structure):
            _fields_ = [
                ("attributes", ct.c_uint32),
                ("creation", ct.c_uint32 * 2),
                ("access", ct.c_uint32 * 2),
                ("write", ct.c_uint32 * 2),
                ("volume", ct.c_uint32),
                ("size_hi", ct.c_uint32),
                ("size_lo", ct.c_uint32),
                ("links", ct.c_uint32),
                ("index_hi", ct.c_uint32),
                ("index_lo", ct.c_uint32),
            ]

        data = Info()
        self.kernel.GetFileInformationByHandle.argtypes = [
            ct.c_void_p,
            ct.POINTER(Info),
        ]
        self.kernel.GetFileInformationByHandle.restype = ct.c_int
        require(
            self.kernel.GetFileInformationByHandle(handle, ct.byref(data))
            and not data.attributes & 0x400
        )
        return data.volume, data.index_hi, data.index_lo, data.size_hi, data.size_lo

    def verify_bytes(self):
        import msvcrt

        require(self.file_identity(self.handle) == self.identity)
        k = self.kernel
        k.GetCurrentProcess.argtypes = []
        k.GetCurrentProcess.restype = ct.c_void_p
        k.DuplicateHandle.argtypes = [
            ct.c_void_p,
            ct.c_void_p,
            ct.c_void_p,
            ct.POINTER(ct.c_void_p),
            ct.c_uint32,
            ct.c_int,
            ct.c_uint32,
        ]
        k.DuplicateHandle.restype = ct.c_int
        process = k.GetCurrentProcess()
        duplicate = ct.c_void_p()
        require(
            k.DuplicateHandle(
                process, self.handle, process, ct.byref(duplicate), 0, False, 2
            )
        )
        try:
            fd = msvcrt.open_osfhandle(duplicate.value, os.O_RDONLY)
        except BaseException:
            k.CloseHandle(duplicate)
            raise
        with os.fdopen(fd, "rb") as stream:
            stream.seek(0)
            data = stream.read()
        require(
            len(data) == self.record["dll_size"]
            and hashlib.sha256(data).hexdigest() == self.record["dll_sha256"]
        )


def call_owned(owner, variant_id, case):
    """All arrays named and live through C call; no native allocation query."""
    from aluclu.alc_r0.banded_edit_token_visibility_native import rank_tokens
    from aluclu.alc_r0.banded_edit_token_visibility_reference import (
        audit_banded_edit_token_visibility,
    )

    first, second, K = case
    reference = audit_banded_edit_token_visibility(
        first, second, code_budgets=(1,), distance_threshold=K
    )
    payload = reference.allocated_packed_payload_bytes
    left, right, ranks = rank_tokens(first, second)
    first_array = (ct.c_uint32 * len(left))(*left)
    second_array = (ct.c_uint32 * len(right))(*right)
    budgets = (ct.c_uint32 * 1)(1)
    policy = (ct.c_uint32 * 8)(
        32768,
        4194304,
        67108864,
        512,
        getsizeof(array("I")),
        getsizeof(array("B")),
        ranks,
        0,
    )
    workspace = (ct.c_uint32 * ((payload + 3) // 4 + 2))(
        *([0xA5A5A5A5] * ((payload + 3) // 4 + 2))
    )
    output = (ct.c_uint32 * 66)(*([0xDEADBEEF] * 66))
    wp = ct.cast(ct.byref(workspace, 4), ct.POINTER(ct.c_uint8)) if payload else None
    op = ct.cast(ct.byref(output, 4), ct.POINTER(ct.c_uint32))
    before_workspace, before_output = bytes(workspace), bytes(output)
    transport = owner.dll.aluclu_banded_audit_v1(
        first_array,
        len(first),
        second_array,
        len(second),
        budgets,
        1,
        K,
        policy,
        wp,
        payload,
        op,
        64,
    )
    actual_workspace, actual_output = bytes(workspace), bytes(output)
    guards = (
        actual_workspace[:4] == before_workspace[:4]
        and actual_workspace[4 + payload :] == before_workspace[4 + payload :]
        and output[0] == output[-1] == 0xDEADBEEF
    )
    no_write = (
        transport not in (1, 2)
        or (actual_workspace == before_workspace and actual_output == before_output)
    ) and (transport != 3 or actual_output == before_output)
    raw = dict(
        variant_id=variant_id,
        compile_exit=0,
        child_exit=0,
        transport=transport,
        canaries_intact=bool(guards and no_write),
        output_words=list(output)[1:65],
        case=case,
    )
    try:
        classified = generator().classify_observation(raw)
    except ValueError as error:
        classified = dict(status="invalid-ABI", differences=[], error=str(error))
    return dict(
        observation=raw,
        status=classified["status"],
        differences=classified["differences"],
        expected_words=generator().expected_words(case),
        allocation=dict(
            required_payload=payload,
            allocated_backing_bytes=ct.sizeof(workspace),
            logical_capacity=payload,
            output_words=64,
        ),
        workspace_guards_intact=guards,
        no_write_contract_intact=no_write,
        guard_evidence=dict(
            workspace_prefix_hex=actual_workspace[:4].hex(),
            workspace_suffix_hex=actual_workspace[4 + payload :].hex(),
            output_prefix=output[0],
            output_suffix=output[-1],
            workspace_before_sha256=hashlib.sha256(before_workspace).hexdigest(),
            workspace_after_sha256=hashlib.sha256(actual_workspace).hexdigest(),
            output_before_sha256=hashlib.sha256(before_output).hexdigest(),
            output_after_sha256=hashlib.sha256(actual_output).hexdigest(),
        ),
    )


def verify_allocation(allocation, case):
    from aluclu.alc_r0.banded_edit_token_visibility_reference import (
        audit_banded_edit_token_visibility,
    )

    first, second, K = case
    payload = audit_banded_edit_token_visibility(
        first, second, code_budgets=(1,), distance_threshold=K
    ).allocated_packed_payload_bytes
    expected = dict(
        required_payload=payload,
        logical_capacity=payload,
        allocated_backing_bytes=4 * ((payload + 3) // 4 + 2),
        output_words=64,
    )
    require(
        type(allocation) is dict
        and allocation == expected
        and all(type(v) is int for v in allocation.values()),
        "reference allocation proof mismatch",
    )
    return expected


def interpret_completed_prefix(rows):
    require(type(rows) is list and rows)
    if any(
        row["workspace_guards_intact"] is not True
        or row["no_write_contract_intact"] is not True
        for row in rows
    ):
        return "canary-failed"
    return rows[-1]["status"]


def admit_completed_schedule(variant_id, rows):
    """Pure coverage admission only; does not establish build/child provenance."""
    variant_id = closed_id(variant_id)
    schedule = generator().schedule(variant_id)
    require(type(rows) is list and 0 < len(rows) <= len(schedule))
    allowed = {
        "survived",
        "semantic-killed",
        "control-disagreed",
        "invalid-ABI",
        "invariant-detected",
        "transport-rejected",
        "canary-failed",
    }
    for index, row in enumerate(rows):
        require(
            type(row) is dict
            and row["status"] in allowed
            and type(row["workspace_guards_intact"]) is bool
            and type(row["no_write_contract_intact"]) is bool
        )
        observation = row["observation"]
        require(
            observation["variant_id"] == variant_id
            and generator()._case(observation["case"]) == schedule[index]
        )
        if row["status"] == "semantic-killed":
            require(index == len(rows) - 1)
    if variant_id == "control":
        require(
            len(rows) == len(schedule) == 1473
            and all(
                row["status"] == "survived"
                and row["workspace_guards_intact"]
                and row["no_write_contract_intact"]
                for row in rows
            ),
            "control coverage failed",
        )
    elif rows[-1]["status"] not in ("semantic-killed", "canary-failed"):
        require(len(rows) == len(schedule), "mutant schedule incomplete")
    return interpret_completed_prefix(rows)


def match_evidence_binding(process, build):
    """Equality of previously independently verified record bindings."""
    for field in ("variant_id", "manifest_path", "manifest_sha256", "provenance"):
        require(
            field in process and field in build and process[field] == build[field],
            "build/process provenance mismatch",
        )


CHILD_KEYS = {
    "schema",
    "variant_id",
    "manifest_path",
    "manifest_sha256",
    "build_record_sha256",
    "provenance",
    "records",
    "post_artifact_verified",
    "training_authority",
    "held_out_data_present",
}
PROCESS_KEYS = {
    "schema",
    "variant_id",
    "manifest_path",
    "manifest_sha256",
    "build_root",
    "build_record_sha256",
    "provenance",
    "command",
    "environment",
    "exit",
    "timeout",
    "logs",
    "result_sha256",
    "observations_sha256",
    "training_authority",
    "held_out_data_present",
}


def child_command(manifest_path, build_root, variant_id):
    return [
        str(PYTHON),
        "-B",
        "-X",
        "faulthandler",
        str(ROOT / OWN_SOURCES[0]),
        "child",
        "--manifest",
        str(manifest_path),
        "--build-root",
        str(build_root),
        "--variant",
        closed_id(variant_id),
    ]


def child_run(manifest_path, build_root, variant_id):
    variant_id = closed_id(variant_id)
    record, out = verify_build(manifest_path, build_root, variant_id)
    require(record["status"] == "built")
    require(
        not (out / "child-result.json").exists()
        and not (out / "observations.jsonl").exists()
    )
    owner = _ClosedArtifactOwner(manifest_path, build_root, variant_id)
    rows = []
    with (out / "observations.jsonl").open("x", encoding="utf-8") as stream:
        for case in generator().schedule(variant_id):
            row = call_owned(owner, variant_id, case)
            rows.append(row)
            stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
            if row["status"] == "canary-failed" or (
                variant_id != "control" and row["status"] == "semantic-killed"
            ):
                break
    owner.verify_bytes()
    verify_build(manifest_path, build_root, variant_id)
    data = dict(
        schema=1,
        variant_id=variant_id,
        manifest_path=str(Path(manifest_path)),
        manifest_sha256=sha(manifest_path),
        build_record_sha256=sha(out / "build-record.json"),
        provenance=record["provenance"],
        records=rows,
        post_artifact_verified=True,
        training_authority=False,
        held_out_data_present=False,
    )
    write_document(out / "child-result.json", data)


def launch_all(manifest_path, build_root):
    require(os.name == "nt")
    verify_manifest(manifest_path)
    records = {}
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for variant_id in IDS:
        build, out = verify_build(manifest_path, build_root, variant_id)
        require(not (out / "process-record.json").exists(), "no automatic retry")
        command = child_command(manifest_path, build_root, variant_id)
        timeout = False
        code = None
        stdout = b""
        stderr = b""
        if build["status"] == "built":
            try:
                run = subprocess.run(command, env=env, capture_output=True, timeout=120)
                code, stdout, stderr = run.returncode, run.stdout, run.stderr
            except subprocess.TimeoutExpired as error:
                timeout = True
                stdout = error.stdout or b""
                stderr = error.stderr or b""
        (out / "child.stdout.log").write_bytes(stdout)
        (out / "child.stderr.log").write_bytes(stderr)
        (out / "child.exit.log").write_bytes(
            (
                "timeout" if timeout else "not-launched" if code is None else str(code)
            ).encode()
            + b"\n"
        )
        data = dict(
            schema=1,
            variant_id=variant_id,
            manifest_path=str(Path(manifest_path)),
            manifest_sha256=sha(manifest_path),
            build_root=str(Path(build_root)),
            build_record_sha256=sha(out / "build-record.json"),
            provenance=build["provenance"],
            command=command,
            environment={k: env[k] for k in ("PYTHONPATH", "PYTHONDONTWRITEBYTECODE")},
            exit=code,
            timeout=timeout,
            logs={
                str(out / name): sha(out / name)
                for name in ("child.stdout.log", "child.stderr.log", "child.exit.log")
            },
            result_sha256=sha(out / "child-result.json")
            if (out / "child-result.json").exists()
            else None,
            observations_sha256=sha(out / "observations.jsonl")
            if (out / "observations.jsonl").exists()
            else None,
            training_authority=False,
            held_out_data_present=False,
        )
        write_document(out / "process-record.json", data)
        records[variant_id] = data
        if variant_id == "control":
            status, rows, _ = verify_process(data)
            require(
                status == "survived" and len(rows) == 1473,
                "control gate failed before mutant launch",
            )
    report = aggregate_verified_records(records)
    write_document(Path(build_root) / "aggregate.json", report)
    return report


def verify_process(data):
    require(
        type(data) is dict
        and set(data) == PROCESS_KEYS
        and type(data["schema"]) is int
        and data["schema"] == 1
        and data["training_authority"] is False
        and data["held_out_data_present"] is False
    )
    variant_id = closed_id(data["variant_id"])
    manifest_path = external(data["manifest_path"])
    build_root = external(data["build_root"])
    build, out = verify_build(manifest_path, build_root, variant_id)
    match_evidence_binding(data, build)
    require(
        document(external(out / "process-record.json"), PROCESS_KEYS) == data,
        "process record bytes/data mismatch",
    )
    require(
        data["manifest_sha256"] == sha(manifest_path)
        and data["build_record_sha256"] == sha(out / "build-record.json")
        and data["provenance"] == build["provenance"]
    )
    require(
        data["command"] == child_command(manifest_path, build_root, variant_id)
        and data["environment"]
        == {"PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"}
    )
    paths = {
        str(out / name)
        for name in ("child.stdout.log", "child.stderr.log", "child.exit.log")
    }
    require(type(data["logs"]) is dict and set(data["logs"]) == paths)
    for path, expected in data["logs"].items():
        require(sha(external(path)) == expected)
    require(
        type(data["timeout"]) is bool
        and (data["exit"] is None or type(data["exit"]) is int)
    )
    exit_text = (
        "timeout"
        if data["timeout"]
        else "not-launched"
        if data["exit"] is None
        else str(data["exit"])
    )
    require((out / "child.exit.log").read_bytes() == exit_text.encode() + b"\n")
    if build["status"] == "compile-failed":
        require(
            data["exit"] is None
            and not data["timeout"]
            and data["result_sha256"] is None
        )
        return "compile-failed", [], build
    if data["timeout"]:
        return "child-timed-out", [], build
    if data["exit"] != 0:
        return "child-crashed", [], build
    require(
        data["result_sha256"] == sha(external(out / "child-result.json"))
        and data["observations_sha256"] == sha(external(out / "observations.jsonl"))
    )
    child = document(out / "child-result.json", CHILD_KEYS)
    require(
        child["variant_id"] == variant_id
        and child["manifest_path"] == str(manifest_path)
        and child["manifest_sha256"] == data["manifest_sha256"]
        and child["build_record_sha256"] == data["build_record_sha256"]
        and child["provenance"] == data["provenance"]
        and child["post_artifact_verified"] is True
    )
    rows = child["records"]
    require(type(rows) is list and rows)
    jsonl = [
        json.loads(line)
        for line in (out / "observations.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    require(rows == jsonl)
    expected_schedule = generator().schedule(variant_id)
    require(len(rows) <= len(expected_schedule))
    statuses = []
    for index, row in enumerate(rows):
        require(
            type(row) is dict
            and set(row)
            == {
                "observation",
                "status",
                "differences",
                "expected_words",
                "allocation",
                "workspace_guards_intact",
                "no_write_contract_intact",
                "guard_evidence",
            }
        )
        observation = row["observation"]
        require(
            observation["variant_id"] == variant_id
            and observation["case"] == json.loads(json.dumps(expected_schedule[index]))
            and observation["compile_exit"] == observation["child_exit"] == 0
        )
        require(
            row["expected_words"]
            == generator().expected_words(expected_schedule[index])
        )
        layout = verify_allocation(row["allocation"], expected_schedule[index])
        guard = row["guard_evidence"]
        require(
            type(guard) is dict
            and set(guard)
            == {
                "workspace_prefix_hex",
                "workspace_suffix_hex",
                "output_prefix",
                "output_suffix",
                "workspace_before_sha256",
                "workspace_after_sha256",
                "output_before_sha256",
                "output_after_sha256",
            }
        )
        require(
            guard["workspace_before_sha256"]
            == hashlib.sha256(b"\xa5" * layout["allocated_backing_bytes"]).hexdigest()
            and guard["output_before_sha256"]
            == hashlib.sha256((ct.c_uint32 * 66)(*([0xDEADBEEF] * 66))).hexdigest()
        )
        require(
            guard["output_after_sha256"]
            == hashlib.sha256(
                (ct.c_uint32 * 66)(
                    guard["output_prefix"],
                    *observation["output_words"],
                    guard["output_suffix"],
                )
            ).hexdigest()
        )
        guard_ok = (
            guard["workspace_prefix_hex"] == "a5" * 4
            and guard["workspace_suffix_hex"]
            == "a5"
            * (layout["allocated_backing_bytes"] - 4 - layout["required_payload"])
            and guard["output_prefix"] == guard["output_suffix"] == 0xDEADBEEF
        )
        unchanged_workspace = (
            guard["workspace_before_sha256"] == guard["workspace_after_sha256"]
        )
        unchanged_output = guard["output_before_sha256"] == guard["output_after_sha256"]
        no_write_ok = (
            observation["transport"] not in (1, 2)
            or (unchanged_workspace and unchanged_output)
        ) and (observation["transport"] != 3 or unchanged_output)
        require(
            row["workspace_guards_intact"] == guard_ok
            and row["no_write_contract_intact"] == no_write_ok
        )
        require(
            type(row["workspace_guards_intact"]) is bool
            and type(row["no_write_contract_intact"]) is bool
            and observation["canaries_intact"]
            == (row["workspace_guards_intact"] and row["no_write_contract_intact"])
        )
        try:
            classified = generator().classify_observation(observation)
        except ValueError:
            classified = dict(status="invalid-ABI", differences=[])
        require(
            row["status"] == classified["status"]
            and row["differences"] == classified["differences"]
        )
        statuses.append(row["status"])
        if row["status"] == "semantic-killed":
            require(index == len(rows) - 1)
    return admit_completed_schedule(variant_id, rows), rows, build


def aggregate_verified_records(records):
    require(
        type(records) is dict and set(records) == set(IDS),
        "exact control plus nine required",
    )
    verified = {"control": verify_process(records["control"])}
    require(
        verified["control"][0] == "survived" and len(verified["control"][1]) == 1473,
        "control gate failed; mutant interpretation forbidden",
    )
    for name in IDS[1:]:
        verified[name] = verify_process(records[name])
    control_process = records["control"]
    for name in IDS:
        require(
            records[name]["manifest_path"] == control_process["manifest_path"]
            and records[name]["manifest_sha256"] == control_process["manifest_sha256"]
            and records[name]["build_root"] == control_process["build_root"]
            and records[name]["provenance"] == control_process["provenance"]
        )
    categories = {}
    detection_counts = {}
    mutants = []
    for name in IDS[1:]:
        status, rows, build = verified[name]
        categories[status] = categories.get(status, 0) + 1
        for row in rows:
            detection_counts[row["status"]] = detection_counts.get(row["status"], 0) + 1
        mutants.append(
            dict(
                variant_id=name,
                status=status,
                records=rows,
                source_sha256=build["source_sha256"],
                process_record_sha256=sha(
                    Path(records[name]["build_root"]) / name / "process-record.json"
                ),
                process_record_path=str(
                    Path(records[name]["build_root"]) / name / "process-record.json"
                ),
                observations_path=str(
                    Path(records[name]["build_root"]) / name / "observations.jsonl"
                ),
                observations_sha256=records[name]["observations_sha256"],
                child_exit=records[name]["exit"],
                child_timeout=records[name]["timeout"],
            )
        )
    return dict(
        schema=1,
        status="all-nine-semantic-killed-non-authorizing"
        if categories.get("semantic-killed") == 9
        else "mutation-gate-unresolved-non-authorizing",
        control_cases=1473,
        control_source_sha256=verified["control"][2]["source_sha256"],
        manifest_sha256=control_process["manifest_sha256"],
        provenance=control_process["provenance"],
        category_counts=categories,
        detection_counts=detection_counts,
        control_process_record_path=str(
            Path(control_process["build_root"]) / "control/process-record.json"
        ),
        control_process_record_sha256=sha(
            Path(control_process["build_root"]) / "control/process-record.json"
        ),
        mutants=mutants,
        training_authority=False,
        held_out_data_present=False,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("build", "run", "child"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--build-root", type=Path, required=True)
    parser.add_argument("--variant", choices=IDS)
    args = parser.parse_args()
    if args.stage == "build":
        require(args.variant is None)
        build_all(args.manifest, args.build_root)
    elif args.stage == "run":
        require(args.variant is None)
        print(json.dumps(launch_all(args.manifest, args.build_root), sort_keys=True))
    else:
        require(args.variant is not None)
        child_run(args.manifest, args.build_root, args.variant)


if __name__ == "__main__":
    main()
