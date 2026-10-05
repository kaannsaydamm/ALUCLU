"""Substituted tiny base: mount checks only, not host/forward qualification."""

import pytest
import torch
from torch import nn

from aluclu.alc_r0.checkpoint_parity_factory import PARITY_SEED
from aluclu.alc_r0.reference_official_guard import ReferencePhaseGuard
from aluclu.alc_r0.reference_qv_lora import ReferenceQVLoRA
from aluclu.alc_r0.reference_qv_wrapper import PinnedLlamaQVReferenceWrapper


@pytest.fixture
def wrapper():
    # Explicitly bypass the verified-host constructor for checks-only tests.
    result = PinnedLlamaQVReferenceWrapper.__new__(PinnedLlamaQVReferenceWrapper)
    nn.Module.__init__(result)
    result.base = nn.Linear(576, 8, bias=False).requires_grad_(False).eval()
    result.reference = ReferenceQVLoRA(seed=PARITY_SEED)
    result.capsule = None
    return result.eval()


@pytest.mark.parametrize("mounted,b", [(True, 0.0), (True, 0.01), (False, 0.0)])
def test_declared_phase_read_only(wrapper, mounted, b):
    with torch.no_grad():
        for name, parameter in wrapper.reference.named_parameters():
            if name.endswith(".B"):
                parameter.fill_(b)
    if not mounted:
        wrapper.detach()
    rng = torch.get_rng_state().clone()
    guard = ReferencePhaseGuard(wrapper, wrapper.base, mounted=mounted, expected_b=b)
    with torch.inference_mode():
        guard.check()
    assert torch.equal(rng, torch.get_rng_state())
    assert all(p.grad is None for p in wrapper.parameters())


@pytest.mark.parametrize(
    "mutation",
    [
        "A",
        "B",
        "negative_zero",
        "seed",
        "gradient",
        "train",
        "base_train",
        "alias",
        "base_alias",
        "buffer",
        "co_mount",
        "detach",
        "replace",
    ],
)
def test_reject_phase_mutations(wrapper, mutation):
    guard = ReferencePhaseGuard(wrapper, wrapper.base, mounted=True)
    block = wrapper.reference.factors["29"]["v"]
    with torch.no_grad():
        if mutation in ("A", "B"):
            getattr(block, mutation)[0, 0] += 0.001
        elif mutation == "negative_zero":
            block.B[0, 0] = -0.0
        elif mutation == "seed":
            wrapper.reference.initialization_seed += 1
        elif mutation == "gradient":
            block.A.grad = torch.zeros_like(block.A)
        elif mutation == "train":
            wrapper.reference.train()
        elif mutation == "base_train":
            wrapper.base.train()
        elif mutation == "alias":
            block.A = wrapper.reference.factors["28"]["v"].A
        elif mutation == "base_alias":
            wrapper.base.weight = nn.Parameter(block.A.detach(), requires_grad=False)
        elif mutation == "buffer":
            wrapper.reference.register_buffer("extra", torch.zeros(1))
        elif mutation == "co_mount":
            wrapper.capsule = nn.Identity()
        elif mutation == "detach":
            wrapper.detach()
        elif mutation == "replace":
            wrapper.reference = ReferenceQVLoRA(seed=PARITY_SEED).eval()
    with pytest.raises(ValueError):
        guard.check()


def test_seeded_a_required_before_snapshot(wrapper):
    with torch.no_grad():
        wrapper.reference.factors["0"]["q"].A[0, 0] += 0.001
    with pytest.raises(ValueError):
        ReferencePhaseGuard(wrapper, wrapper.base, mounted=True)


def test_unmounted_rejects_hidden_effective_mount(wrapper):
    with pytest.raises(ValueError):
        ReferencePhaseGuard(wrapper, wrapper.base, mounted=False)


@pytest.mark.parametrize(
    "mounted,b", [(1, 0.0), (True, 0.125), (True, True), (True, -0.0), (False, -0.0)]
)
def test_exact_declared_arguments(wrapper, mounted, b):
    with pytest.raises(ValueError):
        ReferencePhaseGuard(wrapper, wrapper.base, mounted=mounted, expected_b=b)


def test_negative_zero_argument_cannot_authorize_negative_zero_masters(wrapper):
    with torch.no_grad():
        for name, parameter in wrapper.reference.named_parameters():
            if name.endswith(".B"):
                parameter.fill_(-0.0)
    with pytest.raises(ValueError):
        ReferencePhaseGuard(wrapper, wrapper.base, mounted=True, expected_b=-0.0)
