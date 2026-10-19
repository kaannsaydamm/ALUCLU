"""Read-only E3 start checks on a substituted fake host, not E3 execution."""

from dataclasses import replace

import pytest
import torch
from test_alc_r0_reference_qv_forward import host as host

from aluclu.alc_r0.checkpoint_observation import _base_digest
from aluclu.alc_r0.checkpoint_parity_factory import make_reference_wrapper
from aluclu.alc_r0.reference_stress_inputs import build_stress_schedule
from aluclu.alc_r0.reference_stress_start import (
    StressStartError,
    inspect_reference_stress_start,
)


@pytest.fixture
def start(host):
    # Metadata only: no enlarged embedding/model allocation or actual forward.
    host.model.config.vocab_size = 49152
    host.model.config.max_position_embeddings = 8192
    wrapper = make_reference_wrapper(host, True, state="zero")
    schedule = build_stress_schedule(
        prefix_ids=(7, 8), suffix_ids=(9,), safe_ids=(10,), vulnerable_ids=(11, 12)
    )
    return wrapper, schedule


def test_start_read_only_complete_seed_and_rng(start):
    wrapper, schedule = start
    rng = torch.get_rng_state().clone()
    base = _base_digest(wrapper.base)
    factors = [p.detach().clone() for p in wrapper.reference.parameters()]
    record = inspect_reference_stress_start(wrapper, schedule)
    assert record.factor_count == 120
    assert record.parameter_count == 460800
    assert record.device == "cpu" and record.base_dtype == "torch.float32"
    assert record.sequence_lengths == (4095, 4096) * 8
    assert record.base_digest == base
    assert len(record.schedule_digest) == len(record.factor_digest) == 64
    assert torch.equal(rng, torch.get_rng_state())
    assert all(
        torch.equal(p, old) for p, old in zip(wrapper.reference.parameters(), factors)
    )
    assert all(p.grad is None for p in wrapper.parameters())


@pytest.mark.parametrize(
    "mutation",
    [
        "A",
        "B",
        "seed",
        "gradient",
        "base_train",
        "base_grad",
        "factor_train",
        "vocab",
        "positions",
        "inventory",
    ],
)
def test_reject_dirty_or_incompatible_start(start, mutation):
    wrapper, schedule = start
    block = wrapper.reference.factors["29"]["v"]
    with torch.no_grad():
        if mutation in ("A", "B"):
            getattr(block, mutation)[0, 0] += 0.001
        elif mutation == "seed":
            wrapper.reference.initialization_seed += 1
        elif mutation == "gradient":
            block.A.grad = torch.zeros_like(block.A)
        elif mutation == "base_train":
            wrapper.base.train()
        elif mutation == "base_grad":
            next(wrapper.base.parameters()).requires_grad_(True)
        elif mutation == "factor_train":
            wrapper.reference.eval()
        elif mutation == "vocab":
            wrapper.base.config.vocab_size = 8
        elif mutation == "positions":
            wrapper.base.config.max_position_embeddings = 128
        elif mutation == "inventory":
            wrapper._checkpoint_controller.state_fingerprint_getter = None
    with pytest.raises(StressStartError):
        inspect_reference_stress_start(wrapper, schedule)


def test_schedule_rejected_before_factor_allocation(start, monkeypatch):
    wrapper, schedule = start
    from aluclu.alc_r0 import reference_stress_start

    def forbidden(*args, **kwargs):
        pytest.fail("seed reconstruction reached for malformed schedule")

    monkeypatch.setattr(reference_stress_start, "ReferenceQVLoRA", forbidden)
    with pytest.raises(StressStartError):
        inspect_reference_stress_start(wrapper, replace(schedule, inputs=()))


def test_active_lease_rejected_without_clearing_gradients(start):
    wrapper, schedule = start
    with wrapper.checkpoint_session():
        with pytest.raises(StressStartError):
            inspect_reference_stress_start(wrapper, schedule)


def test_exact_wrapper_required(start):
    _, schedule = start
    with pytest.raises(StressStartError):
        inspect_reference_stress_start(object(), schedule)


@pytest.mark.parametrize("context", [torch.no_grad, torch.inference_mode])
def test_reject_disabled_grad_context(start, context):
    wrapper, schedule = start
    with context(), pytest.raises(StressStartError):
        inspect_reference_stress_start(wrapper, schedule)


def test_reject_foreign_getter_without_invoking_it(start):
    wrapper, schedule = start

    def forbidden():
        pytest.fail("foreign getter invoked")

    wrapper._checkpoint_controller.state_fingerprint_getter = forbidden
    with pytest.raises(StressStartError):
        inspect_reference_stress_start(wrapper, schedule)


def test_reject_negative_zero_seed_bytes(start):
    wrapper, schedule = start
    with torch.no_grad():
        wrapper.reference.factors["29"]["v"].B[0, 0] = -0.0
    with pytest.raises(StressStartError):
        inspect_reference_stress_start(wrapper, schedule)
