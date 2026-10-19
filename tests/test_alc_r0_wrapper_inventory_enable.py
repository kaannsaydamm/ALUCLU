"""Explicit tiny-wrapper opt-in; not actual-host or learning acceptance."""

import pytest
import torch
from test_alc_r0_wrapper_method_inventory import KINDS, owner

from aluclu.alc_r0.checkpoint_execution import CheckpointExecutionError
from aluclu.alc_r0.checkpoint_state import computational_state_fingerprint


@pytest.mark.parametrize("kind", KINDS)
def test_enable_preserves_controller_and_repeat_binding(kind):
    wrapper = owner(kind)
    controller = wrapper._checkpoint_controller
    assert controller.state_fingerprint_getter is None
    wrapper.enable_checkpoint_inventory()
    getter = controller.state_fingerprint_getter
    assert getter() == computational_state_fingerprint({"wrapper": wrapper})
    wrapper.enable_checkpoint_inventory()
    assert wrapper._checkpoint_controller is controller
    assert controller.state_fingerprint_getter is getter
    with wrapper.checkpoint_session():
        with pytest.raises(CheckpointExecutionError, match="during lease"):
            wrapper.enable_checkpoint_inventory()
    assert controller._active is None


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("drift", ["method", "getter"])
def test_enabled_boundary_drift_aborts_and_cleans_gradients(kind, drift, monkeypatch):
    wrapper = owner(kind)
    wrapper.enable_checkpoint_inventory()
    controller = wrapper._checkpoint_controller
    with pytest.raises(CheckpointExecutionError, match="fingerprint|getter"):
        with wrapper.checkpoint_session() as session:
            for parameter in wrapper.parameters():
                if parameter.requires_grad:
                    parameter.grad = torch.ones_like(parameter)
            if drift == "method":
                method = kind.forward
                monkeypatch.setattr(method, "__defaults__", (123,))
            else:
                controller.state_fingerprint_getter = lambda: "b" * 64
            session.begin_forward(wrapper, {"position_ids": torch.zeros(1)})
    assert controller._active is None
    assert all(parameter.grad is None for parameter in wrapper.parameters())


@pytest.mark.parametrize("kind", KINDS)
def test_enable_rejects_subclass_without_callback_publication(kind):
    wrapper = owner(type("Unreviewed", (kind,), {}))
    controller = wrapper._checkpoint_controller
    with pytest.raises(CheckpointExecutionError, match="subclass"):
        wrapper.enable_checkpoint_inventory()
    assert controller.state_fingerprint_getter is None


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("invalid", ["unknown", "override", "missing", "foreign"])
def test_enable_rejection_does_not_install_or_replace(kind, invalid):
    wrapper = owner(kind)
    controller = wrapper._checkpoint_controller
    if invalid == "unknown":
        wrapper.unreviewed_field = 7
    elif invalid == "override":
        wrapper.forward = lambda *args: None
    elif invalid == "missing":
        wrapper._modules["lora" if "lora" in wrapper._modules else "capsule"] = None
    else:
        controller._install_state_fingerprint_getter(lambda: "a" * 64)
    original = controller.state_fingerprint_getter
    with pytest.raises(CheckpointExecutionError):
        wrapper.enable_checkpoint_inventory()
    assert controller.state_fingerprint_getter is original
    assert controller._active is None


@pytest.mark.parametrize("kind", KINDS)
def test_enabled_getter_follows_current_factors_between_leases(kind):
    wrapper = owner(kind)
    wrapper.enable_checkpoint_inventory()
    controller = wrapper._checkpoint_controller
    getter = controller.state_fingerprint_getter
    field = "lora" if "lora" in wrapper._modules else "capsule"
    with wrapper.checkpoint_session():
        with pytest.raises(CheckpointExecutionError, match="during lease"):
            setattr(wrapper, field, getattr(owner(kind), field))
    setattr(wrapper, field, getattr(owner(kind), field))
    assert getter() == computational_state_fingerprint({"wrapper": wrapper})
    with wrapper.checkpoint_session():
        pass
    assert controller.state_fingerprint_getter is getter
