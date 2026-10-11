"""Stdlib-only admission arithmetic; no project/model/Torch import or launch."""

import importlib.util
import sys
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "resource_admission_fixture",
    Path(__file__).parents[1] / "src/aluclu/alc_r0/checkpoint_resource_admission.py",
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

DAY = 86400 * 10**9
HOUR = 3600 * 10**9
GIB = 1 << 30


def history(**changes):
    values = dict(
        complete=True,
        first_development_utc_ns=DAY,
        consumed_gpu_ns=HOUR,
        evidence_sha256="a" * 64,
    )
    return module.ProgramAccounting(**(values | changes))


def request(**changes):
    values = dict(
        accounting=history(),
        phase="D",
        device="gpu",
        now_utc_ns=2 * DAY,
        research_bytes=4 * GIB,
        free_c_bytes=30 * GIB,
        projected_growth_bytes=GIB,
        pending_gpu_ns=HOUR,
        pending_growth_bytes=GIB,
    )
    return module.ResourceRequest(**(values | changes))


def test_fixed_single_gpu_reservation_and_no_authority():
    result = module.assess_resources(request())
    assert result.resource_fit
    assert result.reasons == ()
    assert result.required_gpu_reservation_ns == 45 * 60 * 10**9
    assert result.remaining_gpu_ns == 598 * HOUR
    assert result.program_deadline_utc_ns == 46 * DAY
    assert not hasattr(result, "training_authority")
    assert not hasattr(result, "launch_authority")


@pytest.mark.parametrize(
    "changes",
    [
        {"complete": False},
        {"consumed_gpu_ns": None},
        {"first_development_utc_ns": None},
        {"evidence_sha256": None},
    ],
)
def test_unknown_history_never_becomes_fresh_budget(changes):
    result = module.assess_resources(request(accounting=history(**changes)))
    assert not result.resource_fit
    assert "history-unreconciled" in result.reasons
    assert result.remaining_gpu_ns is None
    assert result.program_deadline_utc_ns is None


@pytest.mark.parametrize(
    "phase,minutes", [("D", 45), ("E1", 30), ("E2", 10), ("E3", 30)]
)
def test_fixed_phase_ceilings(phase, minutes):
    assert (
        module.assess_resources(request(phase=phase)).required_gpu_reservation_ns
        == minutes * 60 * 10**9
    )


def test_cpu_has_no_gpu_reservation():
    assert (
        module.assess_resources(request(device="cpu")).required_gpu_reservation_ns == 0
    )


@pytest.mark.parametrize("phase", ["E1", "E2", "E3"])
def test_resource_matrix_is_gpu_only(phase):
    with pytest.raises(ValueError):
        module.assess_resources(request(phase=phase, device="cpu"))


def test_pending_reservations_prevent_overbooking():
    result = module.assess_resources(request(pending_gpu_ns=599 * HOUR))
    assert not result.resource_fit
    assert "gpu-budget-insufficient" in result.reasons
    assert result.remaining_gpu_ns == 0


def test_exact_gpu_budget_boundary_is_accepted():
    reserved = 45 * 60 * 10**9
    result = module.assess_resources(request(pending_gpu_ns=599 * HOUR - reserved))
    assert result.resource_fit
    assert result.remaining_gpu_ns == reserved


def test_overbudget_is_not_clamped_or_discarded():
    result = module.assess_resources(
        request(accounting=history(consumed_gpu_ns=601 * HOUR))
    )
    assert not result.resource_fit
    assert result.remaining_gpu_ns == -2 * HOUR


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"research_bytes": 24 * GIB}, "research-storage-insufficient"),
        ({"free_c_bytes": 21 * GIB}, "c-free-space-insufficient"),
    ],
)
def test_pending_and_projected_storage_both_count(changes, reason):
    result = module.assess_resources(request(**changes))
    assert not result.resource_fit
    assert reason in result.reasons


def test_exact_storage_and_free_floor_boundary():
    assert module.assess_resources(
        request(research_bytes=23 * GIB, free_c_bytes=22 * GIB)
    ).resource_fit


@pytest.mark.parametrize("offset", [0, 1, -1])
def test_complete_attempt_ceiling_must_fit_window(offset):
    now = 46 * DAY - 45 * 60 * 10**9 + offset
    result = module.assess_resources(request(now_utc_ns=now))
    assert result.resource_fit is (offset <= 0)


@pytest.mark.parametrize("now", [46 * DAY, 47 * DAY, 0])
def test_elapsed_or_backwards_clock_denied(now):
    result = module.assess_resources(request(now_utc_ns=now))
    assert not result.resource_fit
    assert "program-window-invalid" in result.reasons


@pytest.mark.parametrize("value", [True, -1, 1.0, None, 1 << 64])
@pytest.mark.parametrize(
    "field",
    [
        "now_utc_ns",
        "research_bytes",
        "free_c_bytes",
        "projected_growth_bytes",
        "pending_gpu_ns",
        "pending_growth_bytes",
    ],
)
def test_malformed_measurements_rejected(field, value):
    with pytest.raises(ValueError):
        module.assess_resources(request(**{field: value}))


@pytest.mark.parametrize(
    "field,value", [("phase", "pilot"), ("device", "cuda"), ("phase", True)]
)
def test_unknown_modes_rejected(field, value):
    with pytest.raises(ValueError):
        module.assess_resources(request(**{field: value}))


@pytest.mark.parametrize(
    "field,value",
    [
        ("complete", 1),
        ("consumed_gpu_ns", True),
        ("consumed_gpu_ns", -1),
        ("first_development_utc_ns", 1.0),
        ("evidence_sha256", "A" * 64),
        ("evidence_sha256", "a" * 63),
        ("evidence_sha256", "z" * 64),
    ],
)
def test_malformed_history_rejected(field, value):
    with pytest.raises(ValueError):
        module.assess_resources(request(accounting=history(**{field: value})))


def test_frozen_input_and_result_not_mutated():
    original = request()
    snapshot = replace(original)
    result = module.assess_resources(original)
    assert original == snapshot
    with pytest.raises(FrozenInstanceError):
        original.pending_gpu_ns = 0
    with pytest.raises(FrozenInstanceError):
        result.resource_fit = False


def test_foreign_objects_rejected():
    with pytest.raises(ValueError):
        module.assess_resources({})
    with pytest.raises(ValueError):
        module.assess_resources(request(accounting={}))


def test_known_zero_is_not_unknown():
    result = module.assess_resources(
        request(
            accounting=history(consumed_gpu_ns=0, first_development_utc_ns=0),
            now_utc_ns=0,
            pending_gpu_ns=0,
        )
    )
    assert result.resource_fit
    assert result.remaining_gpu_ns == 600 * HOUR
    assert result.program_deadline_utc_ns == 45 * DAY


def test_independent_denials_are_not_hidden_by_unknown_history():
    result = module.assess_resources(
        request(
            accounting=history(complete=False),
            research_bytes=25 * GIB,
            free_c_bytes=20 * GIB,
        )
    )
    assert result.reasons == (
        "history-unreconciled",
        "research-storage-insufficient",
        "c-free-space-insufficient",
    )


def test_deadline_overflow_is_denied():
    result = module.assess_resources(
        request(
            accounting=history(first_development_utc_ns=(1 << 63) - 1),
            now_utc_ns=(1 << 63) - 1,
        )
    )
    assert not result.resource_fit
    assert "program-window-invalid" in result.reasons
