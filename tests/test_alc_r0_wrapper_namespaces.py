"""Wrapper namespace drift controls on tiny modules, not host qualification."""

import builtins
import types

import pytest
import torch
from test_alc_r0_wrapper_method_inventory import KINDS, owner

from aluclu.alc_r0 import host_wrapper, matched_lora
from aluclu.alc_r0.checkpoint_execution import CheckpointExecutionError
from aluclu.alc_r0.checkpoint_state import computational_state_fingerprint
from aluclu.alc_r0.host_wrapper import PinnedLlamaCapsuleWrapper
from aluclu.alc_r0.matched_lora import PinnedLlamaLoRAWrapper


def changed_or_denied(wrapper, before):
    try:
        after = computational_state_fingerprint({"wrapper": wrapper})
    except CheckpointExecutionError:
        return
    assert after != before


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize(
    "name",
    [
        "torch",
        "nn",
        "CheckpointSession",
        "CausalLMOutputWithPast",
        "cast",
        "create_causal_mask",
    ],
)
def test_actual_host_wrapper_alias_drift_detected(kind, name, monkeypatch):
    wrapper = owner(kind)
    before = computational_state_fingerprint({"wrapper": wrapper})
    monkeypatch.setattr(host_wrapper, name, lambda *args: None)
    changed_or_denied(wrapper, before)


@pytest.mark.parametrize("name", ["torch", "nn", "_q_attention_with_projection"])
def test_actual_lora_wrapper_alias_drift_detected(name, monkeypatch):
    wrapper = owner(PinnedLlamaLoRAWrapper)
    before = computational_state_fingerprint({"wrapper": wrapper})
    monkeypatch.setattr(matched_lora, name, lambda *args: None)
    changed_or_denied(wrapper, before)


@pytest.mark.parametrize("kind", KINDS)
def test_wrapper_native_arange_endpoint_rebinding_detected(kind, monkeypatch):
    wrapper = owner(kind)
    before = computational_state_fingerprint({"wrapper": wrapper})
    monkeypatch.setattr(torch, "arange", lambda *args: None)
    changed_or_denied(wrapper, before)


@pytest.mark.parametrize("kind", KINDS)
def test_wrapper_builtin_global_shadow_detected(kind, monkeypatch):
    wrapper = owner(kind)
    before = computational_state_fingerprint({"wrapper": wrapper})
    monkeypatch.setitem(vars(host_wrapper), "next", lambda *args: None)
    changed_or_denied(wrapper, before)


@pytest.mark.parametrize("kind", KINDS)
def test_actual_function_builtin_table_drift_detected(kind, monkeypatch):
    wrapper = owner(kind)
    original = kind.forward
    namespace = dict(original.__globals__)
    namespace["__builtins__"] = dict(vars(builtins))
    function = types.FunctionType(
        original.__code__,
        namespace,
        original.__name__,
        original.__defaults__,
        original.__closure__,
    )
    function.__kwdefaults__ = original.__kwdefaults__
    monkeypatch.setattr(kind, "forward", function)
    before = computational_state_fingerprint({"wrapper": wrapper})
    function.__builtins__["next"] = lambda *args: None
    changed_or_denied(wrapper, before)


@pytest.mark.parametrize("kind", KINDS)
def test_wrapper_namespace_drift_denied_before_owned_preparation(kind, monkeypatch):
    wrapper = owner(kind)
    controller = wrapper._checkpoint_controller
    controller._install_state_fingerprint_getter(
        lambda: computational_state_fingerprint({"wrapper": wrapper})
    )
    with pytest.raises(CheckpointExecutionError, match="namespace|fingerprint drifted"):
        with controller.session() as session:
            monkeypatch.setattr(
                host_wrapper, "CausalLMOutputWithPast", lambda **kw: None
            )
            session.begin_forward(wrapper, {"position_ids": torch.zeros(1)})
    assert controller._active is None
    assert all(parameter.grad is None for parameter in wrapper.parameters())


@pytest.mark.parametrize("name", ["_bind_checkpoint_block", "_run_decoder_layer"])
@pytest.mark.parametrize("changed", ["code", "defaults"])
def test_lora_super_fallback_method_state_detected(name, changed, monkeypatch):
    wrapper = owner(PinnedLlamaLoRAWrapper)
    before = computational_state_fingerprint({"wrapper": wrapper})
    function = getattr(PinnedLlamaCapsuleWrapper, name)
    if changed == "code":
        monkeypatch.setattr(
            function, "__code__", function.__code__.replace(co_name="fallback_drift")
        )
    else:
        monkeypatch.setattr(function, "__defaults__", (987,))
    changed_or_denied(wrapper, before)
