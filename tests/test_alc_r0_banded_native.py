"""Fixture-only native contract tests; an absent backend is a failure."""

import ctypes as ct
import os
from itertools import product

import pytest

from aluclu.alc_r0.banded_edit_token_visibility_native import (
    NativeBandedBackend,
    NativeBandedInfrastructureError,
    rank_tokens,
    read_build_receipt,
)
from aluclu.alc_r0.banded_edit_token_visibility_reference import (
    BandedEditVisibilityLimits,
    audit_banded_edit_token_visibility,
)


def test_rank_bijection_preserves_arbitrary_integer_equality():
    first, second, count = rank_tokens((0, 1 << 200, 0), (1 << 200, 256))
    assert (first, second, count) == ((0, 1, 0), (1, 2), 3)


def test_missing_receipt_is_infrastructure_failure(tmp_path):
    with pytest.raises(NativeBandedInfrastructureError):
        NativeBandedBackend(tmp_path / "absent.json")


@pytest.mark.parametrize(
    "text", ['{"abi":1,"abi":1}', '{"abi":NaN}', "{}", '{"abi":true}']
)
def test_data_only_invalid_receipts_fail_before_load(tmp_path, text):
    path = tmp_path / "receipt.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(NativeBandedInfrastructureError):
        read_build_receipt(path)


@pytest.mark.parametrize(
    "field,value",
    [
        ("dirty_at_start", True),
        ("dirty_at_end", 0),
        ("training_authority", True),
        ("held_out_data_present", None),
        ("commit", "f" * 39),
        ("tree", "G" * 40),
        ("source_hashes", {}),
        ("source_hashes", {"foreign.cpp": "0" * 64}),
    ],
)
def test_data_only_receipt_policy_and_source_allowlist(tmp_path, field, value):
    import json

    # Deliberately synthetic, data-only receipt. It can never authorize a load.
    receipt = dict(
        abi=1,
        commit="0" * 40,
        tree="0" * 40,
        dirty_at_start=False,
        dirty_at_end=False,
        training_authority=False,
        held_out_data_present=False,
        source_hashes={},
        native_source_sha256="0" * 64,
        generated_include_path="",
        generated_include_sha256="",
        native_snapshot_path="",
        native_snapshot_sha256="",
        compiler_path="",
        compiler_sha256="",
        compiler_version="",
        linker_path="",
        linker_sha256="",
        linker_version="",
        sdk_version="",
        architecture="",
        command=[],
        compiler_environment={},
        dll_path="",
        dll_size=0,
        dll_sha256="",
        build_exit=0,
        build_logs={},
        dependency_command=[],
        dependency_exit=0,
        dependencies_path="",
        dependencies_sha256="",
    )
    receipt[field] = value
    path = tmp_path / "synthetic.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(NativeBandedInfrastructureError):
        read_build_receipt(path)


def test_build_snapshot_pure_bytes():
    import importlib.util
    from pathlib import Path

    script = (
        Path(__file__).resolve().parents[1] / "scripts/alc_r0_build_banded_native.py"
    )
    spec = importlib.util.spec_from_file_location("banded_build_fixture", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert (
        module.build_id_include("00" * 32)
        == b"static const unsigned char ALC_R0_BUILD_ID[32] = {"
        + b",".join([b"0"] * 32)
        + b"};\n"
    )


@pytest.mark.parametrize("exit_code", [0, 4])
def test_build_exit_canonical_bytes(tmp_path, exit_code):
    import importlib.util
    from pathlib import Path

    script = (
        Path(__file__).resolve().parents[1] / "scripts/alc_r0_build_banded_native.py"
    )
    spec = importlib.util.spec_from_file_location("banded_exit_fixture", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    path = tmp_path / "build.exit.log"
    module.write_build_exit(path, exit_code)
    assert path.read_bytes() == str(exit_code).encode("ascii") + b"\n"


def _private_response_backend(reference, overrides):
    """Data-only decoder test: no shared DLL mutation, build or native load."""
    from types import SimpleNamespace

    words = [0] * 64
    words[:7] = [
        1,
        int(reference.reason is not None),
        {
            None: 0,
            "endpoint-token-limit": 1,
            "distance-threshold-exceeded": 2,
            "band-cell-limit": 3,
            "scratch-byte-limit": 4,
        }[reference.reason],
        reference.first_tokens,
        reference.second_tokens,
        len(reference.requested_code_budgets),
        reference.distance_threshold,
    ]
    for bit, slot, value in (
        (1, 8, reference.band_lower_diagonal),
        (2, 9, reference.band_upper_diagonal),
        (4, 10, reference.scheduled_band_cells),
        (8, 14, reference.max_row_width),
        (16, 15, reference.estimated_scratch_bytes),
        (32, 19, reference.edit_distance),
    ):
        if value is not None:
            words[7] |= bit
            words[slot] = value & 0xFFFFFFFF
    words[12] = reference.visited_band_cells
    words[17] = reference.allocated_packed_payload_bytes
    for i, row in enumerate(reference.budgets):
        words[20 + 7 * i : 27 + 7 * i] = list(vars(row).values())[1:]
    for slot, value in overrides.items():
        words[slot] = value

    def respond(*args):
        for slot, value in enumerate(words):
            args[-2][slot] = value
        return 0

    instance = object.__new__(NativeBandedBackend)
    instance._verify_artifact = lambda: None
    instance.dll = SimpleNamespace(aluclu_banded_audit_v1=respond)
    return instance


def test_data_only_impossible_distance_is_rejected():
    args = dict(code_budgets=(1,), distance_threshold=2)
    reference = audit_banded_edit_token_visibility((), (), **args)
    private = _private_response_backend(reference, {19: 2})
    with pytest.raises(NativeBandedInfrastructureError):
        private.audit((), (), **args)


@pytest.mark.parametrize("kind", ["endpoint", "cells", "scratch"])
@pytest.mark.parametrize("forge_exact", [False, True])
def test_data_only_preflight_status_and_reason_bound(kind, forge_exact):
    first, second = (1, 2), (2, 1)
    args = dict(code_budgets=(1,), distance_threshold=2)
    base = audit_banded_edit_token_visibility(first, second, **args)
    limits = {
        "endpoint": BandedEditVisibilityLimits(max_endpoint_tokens=1),
        "cells": BandedEditVisibilityLimits(
            max_band_cells=base.scheduled_band_cells - 1
        ),
        "scratch": BandedEditVisibilityLimits(
            max_scratch_bytes=base.estimated_scratch_bytes - 1
        ),
    }[kind]
    reference = audit_banded_edit_token_visibility(first, second, limits=limits, **args)
    overrides = {2: 2}
    if forge_exact:
        overrides = {1: 0, 2: 0, 7: reference_geometry_presence(reference) | 32, 26: 1}
    private = _private_response_backend(reference, overrides)
    with pytest.raises(NativeBandedInfrastructureError):
        private.audit(first, second, limits=limits, **args)


def reference_geometry_presence(reference):
    return sum(
        bit
        for bit, value in (
            (1, reference.band_lower_diagonal),
            (2, reference.band_upper_diagonal),
            (4, reference.scheduled_band_cells),
            (8, reference.max_row_width),
            (16, reference.estimated_scratch_bytes),
        )
        if value is not None
    )


@pytest.mark.parametrize(
    "first,second,overrides",
    [
        ((1, 2), (2, 1), {20: 1, 22: 1}),
        ((1, 2), (2, 1), {25: 3}),
        ((1,), (1,), {21: 1, 25: 1}),
    ],
)
def test_data_only_impossible_exposure_is_rejected(first, second, overrides):
    args = dict(code_budgets=(1,), distance_threshold=2)
    reference = audit_banded_edit_token_visibility(first, second, **args)
    private = _private_response_backend(reference, overrides)
    with pytest.raises(NativeBandedInfrastructureError):
        private.audit(first, second, **args)


def test_data_only_unmodified_response_controls():
    sequences = [s for n in range(4) for s in product((0, 1), repeat=n)]
    for first in sequences:
        for second in sequences:
            for threshold in range(len(first) + len(second) + 2):
                args = dict(code_budgets=(1, 2, 3, 4, 5), distance_threshold=threshold)
                reference = audit_banded_edit_token_visibility(first, second, **args)
                assert (
                    _private_response_backend(reference, {}).audit(
                        first, second, **args
                    )
                    == reference
                )


@pytest.fixture(scope="module")
def backend():
    receipt = os.environ.get("ALUCLU_BANDED_NATIVE_RECEIPT")
    assert receipt, (
        "A reviewed locally built receipt is required; no absent-native skip"
    )
    return NativeBandedBackend(receipt)


def test_binary_parity_all_thresholds(backend):
    sequences = [s for n in range(5) for s in product((0, 1), repeat=n)]
    for first in sequences:
        for second in sequences:
            for threshold in range(len(first) + len(second) + 2):
                args = dict(code_budgets=(1, 2, 3, 4, 5), distance_threshold=threshold)
                assert backend.audit(
                    first, second, **args
                ) == audit_banded_edit_token_visibility(first, second, **args)


def test_giant_ids_and_saturated_budget_slots(backend):
    args = dict(code_budgets=(1, 2, 1 << 200), distance_threshold=2)
    first, second = (1 << 100, 256), (256, 1 << 100)
    assert backend.audit(first, second, **args) == audit_banded_edit_token_visibility(
        first, second, **args
    )


def test_independent_recursive_oracle(backend):
    from test_alc_r0_banded_edit_token_visibility_reference import _independent_oracle

    sequences = [s for n in range(5) for s in product((0, 1), repeat=n)]
    for first in sequences:
        for second in sequences:
            expected = [_independent_oracle(first, second, b) for b in range(1, 6)]
            for K in range(len(first) + len(second) + 2):
                actual = backend.audit(
                    first, second, code_budgets=(1, 2, 3, 4, 5), distance_threshold=K
                )
                if expected[0][0] <= K:
                    assert actual.edit_distance == expected[0][0]
                    for row, (_, states) in zip(actual.budgets, expected):
                        assert tuple(vars(row).values())[1:] == states
                else:
                    assert actual.edit_distance is None and actual.budgets == ()


def test_resource_boundaries(backend):
    args = dict(code_budgets=(1, 2, 3, 4, 5), distance_threshold=2)
    base = audit_banded_edit_token_visibility((1, 2), (2, 1), **args)
    for limits in (
        BandedEditVisibilityLimits(max_endpoint_tokens=1),
        BandedEditVisibilityLimits(max_band_cells=base.scheduled_band_cells - 1),
        BandedEditVisibilityLimits(max_scratch_bytes=base.estimated_scratch_bytes - 1),
        BandedEditVisibilityLimits(
            max_band_cells=base.scheduled_band_cells,
            max_scratch_bytes=base.estimated_scratch_bytes,
        ),
    ):
        assert backend.audit(
            (1, 2), (2, 1), limits=limits, **args
        ) == audit_banded_edit_token_visibility((1, 2), (2, 1), limits=limits, **args)


@pytest.mark.parametrize(
    "mutation",
    [
        "null-output",
        "short-output",
        "small-workspace",
        "unaligned-workspace",
        "bad-budget",
        "bad-rank",
        "bad-policy",
    ],
)
def test_transport_rejections_do_not_write(backend, mutation):
    from array import array
    from sys import getsizeof

    first = (ct.c_uint32 * 1)(0)
    budget = (ct.c_uint32 * 1)(1)
    policy = (ct.c_uint32 * 8)(
        32768,
        4194304,
        67108864,
        512,
        getsizeof(array("I")),
        getsizeof(array("B")),
        1,
        0,
    )
    workspace = (ct.c_uint32 * 20)(*([0xA5A5A5A5] * 20))
    output = (ct.c_uint32 * 66)(*([0xDEADBEEF] * 66))
    pointer = ct.cast(workspace, ct.POINTER(ct.c_uint8))
    out = ct.cast(ct.byref(output, 4), ct.POINTER(ct.c_uint32))
    capacity, words = 66, 64
    if mutation == "null-output":
        out = None
    if mutation == "short-output":
        words = 63
    if mutation == "small-workspace":
        capacity = 65
    if mutation == "unaligned-workspace":
        pointer = ct.cast(ct.byref(workspace, 1), ct.POINTER(ct.c_uint8))
    if mutation == "bad-budget":
        budget[0] = 0
    if mutation == "bad-rank":
        first[0] = 1
    if mutation == "bad-policy":
        policy[7] = 1
    before_workspace, before_output = bytes(workspace), bytes(output)
    status = backend.dll.aluclu_banded_audit_v1(
        first, 1, first, 1, budget, 1, 0, policy, pointer, capacity, out, words
    )
    assert status in (1, 2)
    assert bytes(workspace) == before_workspace and bytes(output) == before_output


def test_long_and_max_width_corners(backend):
    fixtures = [
        (tuple(range(10000)), tuple(range(10000)), 0),
        ((7,) * 10000, (7,) * 10001, 1),
        ((), (), 512),
        (tuple(range(600)), tuple(range(600)), 512),
    ]
    for first, second, K in fixtures:
        args = dict(code_budgets=(1, 2, 3, 4, 5), distance_threshold=K)
        assert backend.audit(
            first, second, **args
        ) == audit_banded_edit_token_visibility(first, second, **args)


@pytest.mark.parametrize(
    "slot,value,K",
    [
        (0, 2, 0),
        (55, 1, 0),
        (63, 1, 0),
        (7, 127, 0),
        (19, 1, 0),
        (19, 1, 1),
        (54, 1, 0),
        (8, 1, 0),
    ],
)
def test_corrupted_output_fails_closed(backend, slot, value, K):
    from types import SimpleNamespace

    original = backend.dll.aluclu_banded_audit_v1

    def corrupt(*args):
        status = original(*args)
        args[-2][slot] = value
        return status

    private = object.__new__(NativeBandedBackend)
    private.__dict__.update(backend.__dict__)
    private.dll = SimpleNamespace(aluclu_banded_audit_v1=corrupt)
    with pytest.raises(NativeBandedInfrastructureError):
        private.audit((), (), code_budgets=(1,), distance_threshold=K)


@pytest.mark.parametrize(
    "field,value",
    [
        ("abi", 2),
        ("native_source_sha256", "00" * 32),
        ("dll_sha256", "00" * 32),
        ("dll_size", 1),
    ],
)
def test_changed_receipt_is_rejected(backend, tmp_path, field, value):
    import json

    receipt = dict(backend.receipt)
    receipt[field] = value
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(NativeBandedInfrastructureError):
        NativeBandedBackend(path)


def test_unsafe_pointer_rejection_is_child_isolated(backend):
    import subprocess
    import sys

    # Invalid policy address is never dereferenced when B is invalid. A crash
    # is a failure; arbitrary accessible-address assumptions stay out of parent.
    code = """
import ctypes as ct
import os
from aluclu.alc_r0.banded_edit_token_visibility_native import NativeBandedBackend
b = NativeBandedBackend(os.environ['ALUCLU_BANDED_NATIVE_RECEIPT'])
p = ct.cast(ct.c_void_p(1), ct.POINTER(ct.c_uint32))
out = (ct.c_uint32 * 64)(*([123]*64))
s = b.dll.aluclu_banded_audit_v1(p,1,p,1,p,0,0,p,None,0,out,64)
assert s == 1 and tuple(out) == (123,)*64
"""
    run = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True)
    assert run.returncode == 0, (run.returncode, run.stdout, run.stderr)
