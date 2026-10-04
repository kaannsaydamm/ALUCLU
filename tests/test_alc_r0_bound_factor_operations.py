"""CPU-only captured operations; no host assets, optimizer or training corpus."""

from types import SimpleNamespace

import pytest
import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.checkpoint import checkpoint

from aluclu.alc_r0.matched_lora import MatchedQProjLoRA
from aluclu.alc_r0.research_capsule import ResearchCapsuleV0


class FrozenProjection(nn.Module):
    def __init__(self, multiplier=2.0):
        super().__init__()
        self.weight = nn.Parameter(torch.tensor(multiplier), requires_grad=False)

    def forward(self, hidden):
        return hidden * self.weight


def make_operation(arm, port=14):
    factors = arm(ports=(14, 29), rank=4, seed=20260916)
    with torch.no_grad():
        for block in factors.factors.values():
            block.B.fill_(0.01)
    attention = SimpleNamespace(q_proj=FrozenProjection())
    if arm is ResearchCapsuleV0:
        bound = factors.bind_port(port)

        def live(h):
            return factors.apply_port(port, h)
    else:
        bound = factors.bind_q_projection(port, attention)

        def live(h):
            return factors.q_projection(port, attention, h)

    return factors, attention, bound, live


@pytest.mark.parametrize("arm", [ResearchCapsuleV0, MatchedQProjLoRA])
@pytest.mark.parametrize("port", [14, 29])
@pytest.mark.parametrize("dtype", [torch.float32, torch.bfloat16])
def test_bound_math_and_gradients_equal_live_path(arm, port, dtype):
    factors, _, bound, live = make_operation(arm, port)
    hidden = torch.linspace(-1, 1, 2 * 576).reshape(1, 2, 576).to(dtype)
    parameters = tuple(factors.factors[str(port)].parameters())
    expected = live(hidden)
    expected_grads = torch.autograd.grad(expected.float().square().sum(), parameters)
    actual = bound(hidden)
    actual_grads = torch.autograd.grad(actual.float().square().sum(), parameters)
    assert torch.equal(actual, expected)
    for actual_grad, expected_grad in zip(actual_grads, expected_grads, strict=True):
        assert torch.equal(actual_grad, expected_grad)


@pytest.mark.parametrize("arm", [ResearchCapsuleV0, MatchedQProjLoRA])
@pytest.mark.parametrize("port", [14, 29])
def test_binding_captures_parameters_not_mutable_factor_module(arm, port):
    factors, _, bound, live = make_operation(arm, port)
    hidden = torch.ones(1, 2, 576)
    old = factors.factors[str(port)]
    original_parameters = tuple(old.parameters())
    expected = bound(hidden).detach().clone()
    # Replacement on the SAME module catches closures that capture only the module.
    old.A = nn.Parameter(torch.zeros_like(old.A))
    old.B = nn.Parameter(torch.zeros_like(old.B))
    assert torch.equal(bound(hidden), expected)
    assert not torch.equal(live(hidden), expected)
    bound(hidden).sum().backward()
    assert all(p.grad is not None for p in original_parameters)
    assert all(p.grad is None for p in old.parameters())


def test_q_binding_captures_projection_module_not_attention_lookup():
    _, attention, bound, live = make_operation(MatchedQProjLoRA)
    hidden = torch.ones(1, 2, 576)
    expected = bound(hidden).detach().clone()
    attention.q_proj = FrozenProjection(7.0)
    assert torch.equal(bound(hidden), expected)
    assert not torch.equal(live(hidden), expected)


@pytest.mark.parametrize("arm", [ResearchCapsuleV0, MatchedQProjLoRA])
@pytest.mark.parametrize("port", [14, 29])
def test_checkpoint_replay_uses_original_parameters_with_frozen_input(arm, port):
    factors, attention, bound, _ = make_operation(arm, port)
    hidden = torch.linspace(-1, 1, 2 * 576).reshape(1, 2, 576)
    original_parameters = tuple(factors.factors[str(port)].parameters())
    expected = bound(hidden)
    expected_grads = torch.autograd.grad(expected.square().sum(), original_parameters)
    actual = checkpoint(bound, hidden, use_reentrant=False, preserve_rng_state=True)
    replacement = arm(ports=(14, 29), rank=4, seed=0)
    factors.factors = replacement.factors
    attention.q_proj = FrozenProjection(7.0)
    actual.square().sum().backward()
    assert torch.equal(actual, expected)
    for parameter, expected_grad in zip(
        original_parameters, expected_grads, strict=True
    ):
        assert torch.equal(parameter.grad, expected_grad)
    assert all(p.grad is None for p in replacement.parameters())


@pytest.mark.parametrize("arm", [ResearchCapsuleV0, MatchedQProjLoRA])
def test_unselected_port_rejected_at_binding(arm):
    factors = arm(ports=(14,), rank=4, seed=0)
    with pytest.raises(ValueError, match="port"):
        if arm is ResearchCapsuleV0:
            factors.bind_port(29)
        else:
            factors.bind_q_projection(29, SimpleNamespace(q_proj=FrozenProjection()))


@pytest.mark.parametrize("arm", [ResearchCapsuleV0, MatchedQProjLoRA])
def test_captured_factor_dtype_revalidated_at_execution(arm):
    factors, _, bound, _ = make_operation(arm)
    factors.factors["14"].A.data = factors.factors["14"].A.data.double()
    with pytest.raises(ValueError, match="FP32"):
        bound(torch.ones(1, 2, 576))


@pytest.mark.parametrize("arm", [ResearchCapsuleV0, MatchedQProjLoRA])
@pytest.mark.parametrize("dtype", [torch.float32, torch.bfloat16])
def test_bound_operation_matches_independent_formula_under_cpu_autocast(arm, dtype):
    factors, _, bound, _ = make_operation(arm)
    block = factors.factors["14"]
    ref_a = block.A.detach().clone().requires_grad_()
    ref_b = block.B.detach().clone().requires_grad_()
    hidden = torch.linspace(-1, 1, 2 * 576).reshape(1, 2, 576).to(dtype)
    source = hidden.float()
    if arm is ResearchCapsuleV0:
        source = source / torch.sqrt(source.square().mean(-1, keepdim=True) + 1e-5)
    delta = F.linear(F.linear(source, ref_a), ref_b)
    expected = (hidden if arm is ResearchCapsuleV0 else hidden * 2.0) + delta.to(dtype)
    expected_grads = torch.autograd.grad(
        expected.float().square().sum(), (ref_a, ref_b)
    )
    with torch.autocast(device_type="cpu", dtype=torch.bfloat16):
        actual = bound(hidden)
    actual_grads = torch.autograd.grad(
        actual.float().square().sum(), (block.A, block.B)
    )
    assert torch.equal(actual, expected)
    for actual_grad, expected_grad in zip(actual_grads, expected_grads, strict=True):
        assert torch.equal(actual_grad, expected_grad)


@pytest.mark.parametrize("arm", [ResearchCapsuleV0, MatchedQProjLoRA])
def test_captured_factor_device_mismatch_rejected_before_math(arm):
    _, _, bound, _ = make_operation(arm)
    with pytest.raises(ValueError, match="device"):
        bound(torch.empty(1, 2, 576, device="meta"))
