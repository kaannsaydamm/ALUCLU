"""Reference construction over shared fake projections, not a real host/E3."""

from dataclasses import replace

import pytest
import torch
from test_alc_r0_parity_factory import FakeBase
from torch import nn

from aluclu.alc_r0 import host_wrapper
from aluclu.alc_r0.checkpoint_parity_factory import make_reference_wrapper
from aluclu.alc_r0.host import SMOLLM2_135M_CONFIG, VerifiedHost
from aluclu.alc_r0.reference_qv_wrapper import PinnedLlamaQVReferenceWrapper


@pytest.fixture
def host(monkeypatch):
    monkeypatch.setattr(host_wrapper, "LlamaForCausalLM", FakeBase)
    base = FakeBase()
    # One shared fake attention roster, not thirty independent decoder blocks.
    attention = nn.Module()
    attention.q_proj = nn.Linear(576, 576, bias=False)
    attention.v_proj = nn.Linear(576, 192, bias=False)
    for layer in base.model.layers:
        layer.self_attn = attention
    base.requires_grad_(False).eval()
    return VerifiedHost(
        base,
        {},
        SMOLLM2_135M_CONFIG.as_dict(),
        sum(p.numel() for p in base.parameters()),
        0,
    )


@pytest.mark.parametrize("state", ["zero", "nonzero"])
def test_reference_factory_independent_arms_without_rng_or_base_mutation(host, state):
    before = torch.random.get_rng_state().clone()
    base_values = {
        name: p.detach().clone() for name, p in host.model.named_parameters()
    }
    off = make_reference_wrapper(host, False, state=state)
    on = make_reference_wrapper(host, True, state=state)
    assert type(off) is type(on) is PinnedLlamaQVReferenceWrapper
    assert off.base is on.base is host.model
    assert off.reference is not on.reference
    assert off._checkpoint_controller is not on._checkpoint_controller
    assert off._checkpoint_controller.state_fingerprint_getter is None
    assert callable(on._checkpoint_controller.state_fingerprint_getter)
    assert torch.equal(before, torch.random.get_rng_state())
    assert off.reference.initialization_seed == 20260916
    assert sum(p.numel() for p in off.reference.parameters()) == 460800
    other = dict(on.reference.named_parameters())
    for name, parameter in off.reference.named_parameters():
        assert torch.equal(parameter, other[name])
        assert (
            parameter.untyped_storage().data_ptr()
            != other[name].untyped_storage().data_ptr()
        )
        if name.endswith(".B"):
            expected = torch.zeros_like(parameter)
            if state == "nonzero":
                expected = (
                    (torch.arange(parameter.numel()) % 17 - 8).float() * 1e-4
                ).reshape(parameter.shape)
            assert torch.equal(parameter, expected)
    assert all(
        torch.equal(p, base_values[name]) for name, p in host.model.named_parameters()
    )
    assert all(not p.requires_grad and p.grad is None for p in host.model.parameters())
    assert all(not module.training for module in host.model.modules())
    with on.checkpoint_session():
        pass


@pytest.mark.parametrize(
    "checkpoint,state", [(1, "zero"), (None, "zero"), (False, True), (True, "trained")]
)
def test_invalid_reference_arguments_rejected(host, checkpoint, state):
    with pytest.raises(ValueError):
        make_reference_wrapper(host, checkpoint, state=state)


@pytest.mark.parametrize("bad", ["count", "trainable", "dtype", "geometry"])
def test_bad_reference_base_rejected_without_repair(host, bad):
    if bad == "count":
        host = replace(host, parameter_count=2)
    elif bad == "trainable":
        host.model.weight.requires_grad_(True)
    elif bad == "dtype":
        host.model.to(dtype=torch.float16)
    else:
        host.model.model.layers[-1].self_attn.v_proj = (
            nn.Linear(576, 576, bias=False).requires_grad_(False).eval()
        )
        host = replace(
            host, parameter_count=sum(p.numel() for p in host.model.parameters())
        )
    modes = tuple(module.training for module in host.model.modules())
    flags = tuple(p.requires_grad for p in host.model.parameters())
    with pytest.raises(ValueError):
        make_reference_wrapper(host, True, state="nonzero")
    assert tuple(module.training for module in host.model.modules()) == modes
    assert tuple(p.requires_grad for p in host.model.parameters()) == flags
