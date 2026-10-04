"""Additional fixture contracts against the independently frozen local DLL.

This module is separately hashed evidence; it is not part of the DLL receipt's
six-source build set. Run in its own pytest process for the one-backend owner.
"""

import copy
import ctypes as ct
import hashlib
import json
import os
import shutil
from array import array
from itertools import product
from pathlib import Path
from sys import getsizeof

import pytest

from aluclu.alc_r0.banded_edit_token_visibility_native import (
    NativeBandedBackend,
    NativeBandedInfrastructureError,
    read_build_receipt,
)
from aluclu.alc_r0.banded_edit_token_visibility_reference import (
    audit_banded_edit_token_visibility,
)


@pytest.fixture(scope="module")
def receipt():
    path = os.environ.get("ALUCLU_BANDED_NATIVE_RECEIPT")
    assert path, "reviewed actual receipt required; absent backend cannot skip"
    return path, read_build_receipt(path)


@pytest.fixture(scope="module")
def backend(receipt):
    return NativeBandedBackend(receipt[0])


def test_ternary_swap_nested_and_all_retained(backend):
    sequences = [s for n in range(3) for s in product((0, 1, 2), repeat=n)]
    for first in sequences:
        for second in sequences:
            for K in range(len(first) + len(second) + 2):
                args = dict(code_budgets=(1, 2, 3), distance_threshold=K)
                result = backend.audit(first, second, **args)
                assert result == audit_banded_edit_token_visibility(
                    first, second, **args
                )
                swapped = backend.audit(second, first, **args)
                if result.edit_distance is None:
                    assert swapped.edit_distance is None and not swapped.budgets
                    continue
                for row, other in zip(result.budgets, swapped.budgets):
                    assert (row.first_min, row.first_max) == (
                        other.second_min,
                        other.second_max,
                    )
                    assert (row.second_min, row.second_max) == (
                        other.first_min,
                        other.first_max,
                    )
                    remapped = sum(
                        1 << (((s & 1) << 1) | ((s & 2) >> 1))
                        for s in range(4)
                        if row.joint_signature_bits & (1 << s)
                    )
                    assert other.joint_signature_bits == remapped
                assert all(
                    a.total_min <= b.total_min and a.total_max <= b.total_max
                    for a, b in zip(result.budgets, result.budgets[1:])
                )
                assert (
                    result.budgets[-1].total_min
                    == result.budgets[-1].total_max
                    == result.edit_distance
                )


def test_crossed_direct_total_and_joint(backend):
    result = backend.audit((1, 2), (2, 1), code_budgets=(1,), distance_threshold=2)
    row = result.budgets[0]
    assert result.edit_distance == 2
    assert (
        row.first_min,
        row.first_max,
        row.second_min,
        row.second_max,
        row.total_min,
        row.total_max,
        row.joint_signature_bits,
    ) == (0, 1, 0, 1, 1, 1, 6)


@pytest.mark.parametrize("length,K", [(32768, 0), (32769, 0), (0, 512), (600, 512)])
def test_endpoint_and_threshold_boundaries(backend, length, K):
    endpoint = (7,) * length
    args = dict(code_budgets=(1, 2, 3, 4, 5), distance_threshold=K)
    result = backend.audit(endpoint, endpoint, **args)
    assert result == audit_banded_edit_token_visibility(endpoint, endpoint, **args)
    if length == 32769:
        assert (
            result.reason == "endpoint-token-limit" and result.visited_band_cells == 0
        )
    else:
        assert (
            result.edit_distance == 0
            and result.visited_band_cells == result.scheduled_band_cells
        )


def _raw_buffers(n=1, m=1, B=1, K=0):
    """Caller must retain all four returns through the native call.

    Offset pointers made with byref do not retain storage/output owning arrays.
    Input arrays and budgets are held directly in args; workspace/output owners
    are the separate named returns. Never unpack those owners into throwaways.
    """
    first = (ct.c_uint32 * max(n, 1))()
    second = (ct.c_uint32 * max(m, 1))()
    budgets = (ct.c_uint32 * 5)(1, 1, 1, 1, 1)
    policy = (ct.c_uint32 * 8)(
        32768,
        4194304,
        67108864,
        512,
        getsizeof(array("I")),
        getsizeof(array("B")),
        1 if n or m else 0,
        0,
    )
    baseline = audit_banded_edit_token_visibility(
        (0,) * n, (0,) * m, code_budgets=tuple(range(1, B + 1)), distance_threshold=K
    )
    payload = baseline.allocated_packed_payload_bytes
    storage = (ct.c_uint32 * ((payload + 3) // 4 + 2))(
        *([0xA5A5A5A5] * ((payload + 3) // 4 + 2))
    )
    output = (ct.c_uint32 * 66)(*([0xDEADBEEF] * 66))
    workspace = ct.cast(ct.byref(storage, 4), ct.POINTER(ct.c_uint8))
    out = ct.cast(ct.byref(output, 4), ct.POINTER(ct.c_uint32))
    args = [first, n, second, m, budgets, B, K, policy, workspace, payload, out, 64]
    return args, storage, output, baseline


@pytest.mark.parametrize(
    "n,m,B,K", [(0, 0, 1, 0), (1, 1, 1, 0), (1, 1, 3, 0), (2, 3, 5, 1)]
)
def test_accepted_logical_workspace_and_output_canaries(backend, n, m, B, K):
    args, storage, output, baseline = _raw_buffers(n, m, B, K)
    payload = baseline.allocated_packed_payload_bytes
    assert backend.dll.aluclu_banded_audit_v1(*args) == 0
    assert output[0] == output[-1] == 0xDEADBEEF
    raw = bytes(storage)
    assert raw[:4] == b"\xa5" * 4
    assert raw[4 + payload :] == b"\xa5" * (len(raw) - 4 - payload)
    assert args[-2][17] == payload and args[-2][18] == 0
    assert args[-2][12] == baseline.scheduled_band_cells and args[-2][13] == 0
    assert args[-2][19] == baseline.edit_distance
    args, storage, output, _ = _raw_buffers(n, m, B, K)
    args[9] -= 1
    before = bytes(storage), bytes(output)
    assert backend.dll.aluclu_banded_audit_v1(*args) == 2
    assert (bytes(storage), bytes(output)) == before


@pytest.mark.parametrize(
    "kind",
    [
        "B0",
        "B6",
        "K513",
        "endpoint0",
        "endpoint32769",
        "cells0",
        "cells4194305",
        "scratch0",
        "scratch67108865",
        "threshold513",
        "headerI0",
        "headerI4097",
        "headerB0",
        "headerB4097",
        "ranks0",
        "ranks65537",
        "reserved",
        "null-first",
        "null-second",
        "null-budgets",
        "null-policy",
        "null-workspace-capacity",
        "rank-overflow",
        "budget0",
        "budget-overflow",
    ],
)
def test_safe_abi_input_rejections_leave_buffers_unchanged(backend, kind):
    args, storage, output, _ = _raw_buffers()
    if kind == "B0":
        args[5] = 0
    elif kind == "B6":
        args[5] = 6
    elif kind == "K513":
        args[6] = 513
    elif kind.startswith("null-"):
        slot = {
            "null-first": 0,
            "null-second": 2,
            "null-budgets": 4,
            "null-policy": 7,
            "null-workspace-capacity": 8,
        }[kind]
        args[slot] = None
    elif kind == "rank-overflow":
        args[0][0] = 1
    elif kind == "budget0":
        args[4][0] = 0
    elif kind == "budget-overflow":
        args[4][0] = 2
    else:
        slot, value = {
            "endpoint0": (0, 0),
            "endpoint32769": (0, 32769),
            "cells0": (1, 0),
            "cells4194305": (1, 4194305),
            "scratch0": (2, 0),
            "scratch67108865": (2, 67108865),
            "threshold513": (3, 513),
            "headerI0": (4, 0),
            "headerI4097": (4, 4097),
            "headerB0": (5, 0),
            "headerB4097": (5, 4097),
            "ranks0": (6, 0),
            "ranks65537": (6, 65537),
            "reserved": (7, 1),
        }[kind]
        args[7][slot] = value
    before = bytes(storage), bytes(output)
    assert backend.dll.aluclu_banded_audit_v1(*args) == 1
    assert (bytes(storage), bytes(output)) == before


def test_large_count_endpoint_reject_does_not_scan_inputs(backend):
    args, storage, output, _ = _raw_buffers()
    args[1], args[3], args[8], args[9] = 0xFFFFFFFF, 0, None, 0
    before = bytes(storage)
    assert backend.dll.aluclu_banded_audit_v1(*args) == 0
    assert args[-2][2] == 1 and args[-2][3] == 0xFFFFFFFF
    assert args[-2][7] == args[-2][12] == args[-2][17] == 0
    assert bytes(storage) == before and output[0] == output[-1] == 0xDEADBEEF


def test_empty_null_input_pointers_are_valid(backend):
    args, storage, output, baseline = _raw_buffers(0, 0)
    args[0] = args[2] = None
    assert backend.dll.aluclu_banded_audit_v1(*args) == 0
    assert args[-2][19] == 0
    # byref-offset pointers do not retain owners; keep both arrays through call.
    assert bytes(storage)[:4] == b"\xa5" * 4
    assert output[0] == output[-1] == 0xDEADBEEF
    assert args[-2][17] == baseline.allocated_packed_payload_bytes


@pytest.mark.parametrize("capacity", [0, 1, 31])
def test_short_build_id_does_not_write(backend, capacity):
    out = (ct.c_uint8 * 34)(*([0xA5] * 34))
    pointer = ct.cast(ct.byref(out, 1), ct.POINTER(ct.c_uint8))
    assert backend.dll.aluclu_banded_build_id_v1(pointer, capacity) == 1
    assert bytes(out) == b"\xa5" * 34


def test_build_id_null_and_exact_guarded_output(backend, receipt):
    assert backend.dll.aluclu_banded_build_id_v1(None, 32) == 1
    out = (ct.c_uint8 * 34)(*([0xA5] * 34))
    assert (
        backend.dll.aluclu_banded_build_id_v1(
            ct.cast(ct.byref(out, 1), ct.POINTER(ct.c_uint8)), 32
        )
        == 0
    )
    assert out[0] == out[-1] == 0xA5
    assert bytes(out)[1:33].hex() == receipt[1]["native_source_sha256"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("compiler_sha256", "0" * 64),
        ("linker_sha256", "0" * 64),
        ("compiler_version", "other"),
        ("linker_version", "other"),
        ("generated_include_sha256", "0" * 64),
        ("native_snapshot_sha256", "0" * 64),
        ("dependencies_sha256", "0" * 64),
        ("build_exit", 1),
        ("build_exit", True),
        ("dependency_exit", 1),
        ("sdk_version", "other"),
        ("architecture", "x86"),
        ("command", []),
        ("dependency_command", []),
        ("build_logs", {}),
        ("compiler_environment", {}),
        ("native_source_sha256", "0" * 64),
        ("tree", "0" * 40),
    ],
)
def test_deep_receipt_tamper_from_full_valid_control(receipt, tmp_path, field, value):
    original = read_build_receipt(receipt[0])
    changed = copy.deepcopy(original)
    changed[field] = value
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(NativeBandedInfrastructureError):
        read_build_receipt(path)
    assert read_build_receipt(receipt[0]) == original


@pytest.mark.parametrize("artifact", ["include", "snapshot", "exitlog"])
def test_artifact_content_tamper_with_updated_hash_preserves_original(
    receipt, tmp_path, artifact
):
    original = read_build_receipt(receipt[0])
    changed = copy.deepcopy(original)
    old = Path(original["dll_path"]).parent
    copied = tmp_path / "build"
    copied.mkdir()
    for name in (
        "alc_r0_banded_fixture.dll",
        "alc_r0_build_id.h",
        "banded_edit_visibility.cpp",
        "dependencies.log",
        "build.stdout.log",
        "build.stderr.log",
        "build.exit.log",
    ):
        shutil.copyfile(old / name, copied / name)
    for field in (
        "dll_path",
        "generated_include_path",
        "native_snapshot_path",
        "dependencies_path",
    ):
        changed[field] = str(copied / Path(changed[field]).name)
    changed["build_logs"] = {
        str(copied / Path(p).name): digest
        for p, digest in changed["build_logs"].items()
    }
    changed["command"] = [
        part.replace(str(old), str(copied)) for part in changed["command"]
    ]
    changed["dependency_command"] = [
        part.replace(str(old), str(copied)) for part in changed["dependency_command"]
    ]
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps(changed), encoding="utf-8")
    assert read_build_receipt(path) == changed  # Full positive clone before mutation.
    target = (
        copied
        / {
            "include": "alc_r0_build_id.h",
            "snapshot": "banded_edit_visibility.cpp",
            "exitlog": "build.exit.log",
        }[artifact]
    )
    target.write_bytes(b"1\n" if artifact == "exitlog" else target.read_bytes() + b"\n")
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    if artifact == "include":
        changed["generated_include_sha256"] = digest
    elif artifact == "snapshot":
        changed["native_snapshot_sha256"] = digest
    else:
        changed["build_logs"][str(target)] = digest
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(NativeBandedInfrastructureError):
        read_build_receipt(path)
    assert read_build_receipt(receipt[0]) == original
