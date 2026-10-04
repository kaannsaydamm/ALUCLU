"""Real factors over fake CPU base; no host weights/forward/learning claim."""

import importlib
from dataclasses import replace
from functools import partial

import pytest
import torch
from torch import nn

from aluclu.alc_r0 import host_wrapper
from aluclu.alc_r0.host import SMOLLM2_135M_CONFIG, VerifiedHost
from aluclu.alc_r0.host_wrapper import PinnedLlamaCapsuleWrapper
from aluclu.alc_r0.matched_lora import PinnedLlamaLoRAWrapper


class FakeBase(nn.Module):
    def __init__(self):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(2), requires_grad=False)
        self.model = nn.Module()
        self.model.layers = nn.ModuleList(nn.Identity() for _ in range(30))
        self.eval()


@pytest.fixture
def fake_host(monkeypatch):
    # Only substitute the constructor's host type check. Exact real wrapper and
    # factor classes are used; no forward or actual model construction occurs.
    monkeypatch.setattr(host_wrapper, "LlamaForCausalLM", FakeBase)
    base = FakeBase()
    return VerifiedHost(base, {}, SMOLLM2_135M_CONFIG.as_dict(), 2, 0)


def make(host, **kwargs):
    module = importlib.import_module("aluclu.alc_r0.checkpoint_parity_factory")
    return module.make_parity_wrapper(host, **kwargs)


@pytest.mark.parametrize("arm", ["capsule", "q_lora"])
@pytest.mark.parametrize("state", ["zero", "nonzero"])
@pytest.mark.parametrize("ports", [(14,), (29,), (14, 29)])
@pytest.mark.parametrize("rank", [4, 8, 16])
def test_all_cells_share_base_and_independent_identical_factors(
    fake_host, arm, state, ports, rank
):
    rng = torch.random.get_rng_state().clone()
    base_values = fake_host.model.weight.detach().clone()
    kwargs = dict(arm=arm, state=state, ports=ports, rank=rank)
    off = make(fake_host, checkpoint=False, **kwargs)
    on = make(fake_host, checkpoint=True, **kwargs)
    cls = PinnedLlamaCapsuleWrapper if arm == "capsule" else PinnedLlamaLoRAWrapper
    assert type(off) is type(on) is cls
    assert off is not on
    assert off.base is on.base is fake_host.model
    assert off.training and on.training
    assert all(not module.training for module in fake_host.model.modules())
    assert off._checkpoint_controller.state_fingerprint_getter is None
    assert callable(on._checkpoint_controller.state_fingerprint_getter)
    assert torch.equal(rng, torch.random.get_rng_state())
    assert torch.equal(fake_host.model.weight, base_values)
    assert fake_host.model.weight.grad is None
    off_factors, on_factors = off._checkpoint_factors(), on._checkpoint_factors()
    assert off_factors is not on_factors
    assert off_factors.initialization_seed == on_factors.initialization_seed == 20260916
    assert sum(p.numel() for p in off_factors.parameters()) == 2 * 576 * rank * len(
        ports
    )
    off_named, on_named = (
        dict(off_factors.named_parameters()),
        dict(on_factors.named_parameters()),
    )
    assert off_named.keys() == on_named.keys()
    for name, parameter in off_named.items():
        other = on_named[name]
        assert parameter is not other
        assert (
            parameter.untyped_storage().data_ptr() != other.untyped_storage().data_ptr()
        )
        assert torch.equal(parameter, other)
        assert parameter.dtype is torch.float32 and parameter.requires_grad
        assert parameter.grad is None and other.grad is None
        if name.endswith(".B"):
            expected = torch.zeros_like(parameter)
            if state == "nonzero":
                expected = (
                    (torch.arange(parameter.numel()) % 17 - 8).float() * 1e-4
                ).reshape(parameter.shape)
            assert torch.equal(parameter, expected)
    with on.checkpoint_session():
        pass


@pytest.mark.parametrize("state", ["zero", "nonzero"])
def test_parameter_matched_arms_have_exact_same_seeded_A(fake_host, state):
    common = dict(state=state, ports=(14, 29), rank=16, checkpoint=False)
    capsule = make(fake_host, arm="capsule", **common)._checkpoint_factors()
    lora = make(fake_host, arm="q_lora", **common)._checkpoint_factors()
    for name, parameter in capsule.named_parameters():
        assert torch.equal(parameter, dict(lora.named_parameters())[name])


@pytest.mark.parametrize(
    "key,value",
    [
        ("arm", "lora"),
        ("arm", None),
        ("state", "trained"),
        ("state", True),
        ("ports", [14]),
        ("ports", (0,)),
        ("rank", True),
        ("rank", 4.0),
        ("rank", 2),
        ("checkpoint", 1),
        ("checkpoint", None),
    ],
)
def test_invalid_cell_rejected_before_base_mutation(fake_host, key, value):
    kwargs = dict(arm="capsule", state="zero", ports=(14,), rank=4, checkpoint=False)
    kwargs[key] = value
    values = fake_host.model.weight.detach().clone()
    with pytest.raises(ValueError):
        make(fake_host, **kwargs)
    assert torch.equal(fake_host.model.weight, values)
    assert not fake_host.model.training


@pytest.mark.parametrize(
    "bad", ["host", "mode", "child_mode", "trainable", "grad", "dtype", "meta"]
)
def test_invalid_base_rejected_without_silent_repair(fake_host, bad):
    host = fake_host
    if bad == "host":
        host = None
    elif bad == "mode":
        host.model.train()
    elif bad == "child_mode":
        host.model.model.layers[0].train()
    elif bad == "trainable":
        host.model.weight.requires_grad_(True)
    elif bad == "grad":
        host.model.weight.grad = torch.ones_like(host.model.weight)
    elif bad == "dtype":
        host.model.to(dtype=torch.float16)
    else:
        host.model.to("meta")
    modes = tuple(module.training for module in fake_host.model.modules())
    flags = tuple(p.requires_grad for p in fake_host.model.parameters())
    with pytest.raises(ValueError):
        make(host, arm="capsule", state="zero", ports=(14,), rank=4, checkpoint=False)
    assert tuple(module.training for module in fake_host.model.modules()) == modes
    assert tuple(p.requires_grad for p in fake_host.model.parameters()) == flags


@pytest.mark.parametrize(
    "bad",
    [
        "model",
        "count",
        "trainable_count",
        "buffer_grad",
        "buffer_meta",
        "default_device",
    ],
)
def test_base_metadata_and_buffer_preflight_rejection(fake_host, bad, monkeypatch):
    host = fake_host
    if bad == "model":
        host = replace(host, model=None)
    elif bad == "count":
        host = replace(host, parameter_count=3)
    elif bad == "trainable_count":
        host = replace(host, trainable_parameter_count=True)
    elif bad == "buffer_grad":
        host.model.register_buffer("scratch", torch.ones(2, requires_grad=True))
    elif bad == "buffer_meta":
        host.model.register_buffer("scratch", torch.empty(2, device="meta"))
    else:
        monkeypatch.setattr(torch, "get_default_device", lambda: torch.device("meta"))
    modes = tuple(module.training for module in fake_host.model.modules())
    with pytest.raises(ValueError):
        make(host, arm="capsule", state="zero", ports=(14,), rank=4, checkpoint=False)
    assert tuple(module.training for module in fake_host.model.modules()) == modes


@pytest.mark.parametrize("arm", ["capsule", "q_lora"])
def test_partial_accepts_accumulation_pair_positional_flags(fake_host, arm):
    module = importlib.import_module("aluclu.alc_r0.checkpoint_parity_factory")
    factory = partial(
        module.make_parity_wrapper,
        fake_host,
        arm=arm,
        ports=(14,),
        rank=4,
        state="nonzero",
    )
    off, on = factory(False), factory(True)
    assert off.base is on.base is fake_host.model
    assert off._checkpoint_controller is not on._checkpoint_controller
    assert off._checkpoint_controller.state_fingerprint_getter is None
    assert callable(on._checkpoint_controller.state_fingerprint_getter)
    for name, parameter in off._checkpoint_factors().named_parameters():
        assert torch.equal(
            parameter, dict(on._checkpoint_factors().named_parameters())[name]
        )
