"""Wrapper lifecycle bridge only; fake frozen base, no real host assets."""

import pytest
import torch
from torch import nn

from aluclu.alc_r0.checkpoint_execution import CheckpointExecutionError
from aluclu.alc_r0.host_wrapper import PinnedLlamaCapsuleWrapper
from aluclu.alc_r0.matched_lora import MatchedQProjLoRA, PinnedLlamaLoRAWrapper
from aluclu.alc_r0.research_capsule import ResearchCapsuleV0


def make_wrapper(kind):
    # Deliberately does NOT instantiate or certify a VerifiedHost/Llama model.
    wrapper = kind.__new__(kind)
    nn.Module.__init__(wrapper)
    wrapper.base = nn.Linear(4, 4, bias=False).requires_grad_(False).eval()
    wrapper.capsule = None
    if kind is PinnedLlamaLoRAWrapper:
        wrapper.lora = None
    wrapper._initialize_checkpoint_controller()
    wrapper.train()
    factors = (
        MatchedQProjLoRA(ports=(14,), rank=4, seed=0)
        if kind is PinnedLlamaLoRAWrapper
        else ResearchCapsuleV0(ports=(14,), rank=4, seed=0)
    )
    if kind is PinnedLlamaLoRAWrapper:
        wrapper.mount_lora(factors)
    else:
        wrapper.mount(factors)
    return wrapper, factors


@pytest.mark.parametrize("kind", [PinnedLlamaCapsuleWrapper, PinnedLlamaLoRAWrapper])
def test_session_factory_uses_one_owner_controller_and_arm(kind):
    wrapper, factors = make_wrapper(kind)
    controller = wrapper._checkpoint_controller
    assert controller.owner is wrapper
    assert controller.base_getter() is wrapper.base
    assert controller.factor_getter() is factors
    assert controller.layer_count == 30
    with wrapper.checkpoint_session() as session:
        assert session._controller is controller
        assert session.pending_count == 0
        with pytest.raises(CheckpointExecutionError, match="nesting"):
            with wrapper.checkpoint_session():
                pass
    with wrapper.checkpoint_session():
        pass
    assert wrapper._checkpoint_controller is controller


@pytest.mark.parametrize("kind", [PinnedLlamaCapsuleWrapper, PinnedLlamaLoRAWrapper])
@pytest.mark.parametrize(
    "mutation",
    ["train", "eval", "to", "detach", "mount", "base", "factor", "controller", "init"],
)
def test_active_lease_denies_wrapper_mutation_before_state_changes(kind, mutation):
    wrapper, factors = make_wrapper(kind)
    base = wrapper.base
    controller = wrapper._checkpoint_controller
    before = [(p, p.dtype, p.device, p._version) for p in wrapper.parameters()]
    with wrapper.checkpoint_session():
        with pytest.raises(CheckpointExecutionError, match="mutation"):
            if mutation == "train":
                wrapper.train(False)
            elif mutation == "eval":
                wrapper.eval()
            elif mutation == "to":
                wrapper.to(dtype=torch.float64)
            elif mutation == "detach":
                wrapper.detach()
            elif mutation == "mount":
                if kind is PinnedLlamaLoRAWrapper:
                    wrapper.mount_lora(factors)
                else:
                    wrapper.mount(factors)
            elif mutation == "base":
                wrapper.base = nn.Linear(4, 4)
            elif mutation == "factor":
                setattr(
                    wrapper,
                    "lora" if kind is PinnedLlamaLoRAWrapper else "capsule",
                    None,
                )
            elif mutation == "controller":
                wrapper._checkpoint_controller = None
            else:
                wrapper._initialize_checkpoint_controller()
        assert wrapper.training and factors.training and not base.training
        assert wrapper.base is base
        assert wrapper._checkpoint_controller is controller
        assert controller.factor_getter() is factors
        for p, dtype, device, version in before:
            assert (p.dtype, p.device, p._version) == (dtype, device, version)


@pytest.mark.parametrize("kind", [PinnedLlamaCapsuleWrapper, PinnedLlamaLoRAWrapper])
def test_default_forward_cannot_bypass_active_lease(kind):
    wrapper, _ = make_wrapper(kind)
    with wrapper.checkpoint_session():
        with pytest.raises(CheckpointExecutionError, match="mutation"):
            wrapper(input_ids=torch.ones(1, 2, dtype=torch.int64), use_cache=False)


@pytest.mark.parametrize("kind", [PinnedLlamaCapsuleWrapper, PinnedLlamaLoRAWrapper])
def test_closed_lease_releases_mutation_and_unmounted_entry_denied(kind):
    wrapper, _ = make_wrapper(kind)
    with wrapper.checkpoint_session():
        pass
    wrapper.eval()
    wrapper.detach()
    wrapper.train()
    with pytest.raises(CheckpointExecutionError, match="mounted"):
        with wrapper.checkpoint_session():
            pass


def test_controller_reinitialization_denied_even_without_lease():
    wrapper, _ = make_wrapper(PinnedLlamaCapsuleWrapper)
    with pytest.raises(CheckpointExecutionError, match="already"):
        wrapper._initialize_checkpoint_controller()


@pytest.mark.parametrize("kind", [PinnedLlamaCapsuleWrapper, PinnedLlamaLoRAWrapper])
@pytest.mark.parametrize(
    "mutation",
    [
        "load",
        "requires_grad",
        "zero_grad",
        "add_module",
        "register_module",
        "set_submodule",
        "buffer",
        "parameter",
    ],
)
def test_other_supported_mutators_are_denied_before_changes(kind, mutation):
    wrapper, factors = make_wrapper(kind)
    parameters = tuple(wrapper.parameters())
    for p in factors.parameters():
        p.grad = torch.ones_like(p)
    gradients = [p.grad for p in factors.parameters()]
    states = {name: p.detach().clone() for name, p in wrapper.named_parameters()}
    with wrapper.checkpoint_session():
        with pytest.raises(CheckpointExecutionError, match="mutation"):
            if mutation == "load":
                wrapper.load_state_dict(
                    {name: value + 1 for name, value in states.items()}
                )
            elif mutation == "requires_grad":
                wrapper.requires_grad_(False)
            elif mutation == "zero_grad":
                wrapper.zero_grad()
            elif mutation == "add_module":
                wrapper.add_module("base", nn.Linear(4, 4))
            elif mutation == "register_module":
                wrapper.register_module("base", nn.Linear(4, 4))
            elif mutation == "set_submodule":
                wrapper.set_submodule("base", nn.Linear(4, 4))
            elif mutation == "buffer":
                wrapper.register_buffer("extra", torch.ones(1))
            else:
                wrapper.register_parameter("extra", nn.Parameter(torch.ones(1)))
        assert tuple(wrapper.parameters()) == parameters
        for name, p in wrapper.named_parameters():
            assert torch.equal(p, states[name])
        assert all(p.requires_grad for p in factors.parameters())
        for p, grad in zip(factors.parameters(), gradients, strict=True):
            assert p.grad is grad


@pytest.mark.parametrize("name", ["base", "capsule", "_checkpoint_controller"])
def test_protected_deletion_denied_in_lease(name):
    wrapper, _ = make_wrapper(PinnedLlamaCapsuleWrapper)
    original = getattr(wrapper, name)
    with wrapper.checkpoint_session():
        with pytest.raises(CheckpointExecutionError, match="mutation"):
            delattr(wrapper, name)
        assert getattr(wrapper, name) is original


def test_controller_cannot_be_replaced_or_deleted_after_close():
    wrapper, _ = make_wrapper(PinnedLlamaCapsuleWrapper)
    controller = wrapper._checkpoint_controller
    with wrapper.checkpoint_session():
        pass
    with pytest.raises(CheckpointExecutionError, match="already"):
        wrapper._checkpoint_controller = None
    with pytest.raises(CheckpointExecutionError, match="deleted"):
        del wrapper._checkpoint_controller
    assert wrapper._checkpoint_controller is controller


@pytest.mark.parametrize(
    "mutation",
    ["module", "parameter", "buffer", "plain", "delete_module", "delete_buffer"],
)
def test_arbitrary_wrapper_attribute_mutation_denied_before_write(mutation):
    wrapper, _ = make_wrapper(PinnedLlamaCapsuleWrapper)
    wrapper.extra = nn.Identity()
    wrapper.register_buffer("scratch", torch.ones(1))
    wrapper.setting = 1
    module, buffer = wrapper.extra, wrapper.scratch
    with wrapper.checkpoint_session():
        with pytest.raises(CheckpointExecutionError, match="mutation"):
            if mutation == "module":
                wrapper.extra = nn.Linear(4, 4)
            elif mutation == "parameter":
                wrapper.new_parameter = nn.Parameter(torch.ones(1))
            elif mutation == "buffer":
                wrapper.scratch = torch.zeros(1)
            elif mutation == "plain":
                wrapper.setting = 2
            elif mutation == "delete_module":
                del wrapper.extra
            else:
                del wrapper.scratch
        assert wrapper.extra is module
        assert wrapper.scratch is buffer
        assert wrapper.setting == 1


@pytest.mark.parametrize("kind", [PinnedLlamaCapsuleWrapper, PinnedLlamaLoRAWrapper])
def test_supported_mutators_delegate_normally_without_lease(kind):
    wrapper, factors = make_wrapper(kind)
    state = {name: p.detach().clone() for name, p in wrapper.named_parameters()}
    result = wrapper.load_state_dict(state, strict=True, assign=False)
    assert not result.missing_keys and not result.unexpected_keys
    for p in factors.parameters():
        p.grad = torch.ones_like(p)
    assert wrapper.zero_grad(set_to_none=True) is None
    assert all(p.grad is None for p in factors.parameters())
    assert wrapper.requires_grad_(False) is wrapper
    assert not any(p.requires_grad for p in wrapper.parameters())
    assert wrapper.to(dtype=torch.float64) is wrapper
    assert all(p.dtype == torch.float64 for p in wrapper.parameters())
    wrapper.register_module("extra", nn.Identity())
    replacement = nn.Identity()
    wrapper.set_submodule("extra", replacement, strict=True)
    assert wrapper.extra is replacement
    wrapper.register_buffer("scratch", torch.ones(1), persistent=False)
    wrapper.register_parameter("extra_parameter", nn.Parameter(torch.ones(1)))
    assert "scratch" not in wrapper.state_dict()
    assert wrapper.extra_parameter.requires_grad
    del wrapper.extra
    del wrapper.scratch
    del wrapper.extra_parameter
    wrapper.setting = 1
    del wrapper.setting
