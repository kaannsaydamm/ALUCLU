"""Tiny registry closure controls; no host weights/forward or learning claim."""

import types

import pytest
import torch
from test_alc_r0_attention_dependencies import make_owner
from transformers.modeling_utils import AttentionInterface

from aluclu.alc_r0 import matched_lora
from aluclu.alc_r0.checkpoint_execution import CheckpointExecutionError
from aluclu.alc_r0.checkpoint_registry import _builtin_binding


@pytest.mark.parametrize("route", ["eager", "sdpa"])
@pytest.mark.parametrize("phase", ["preparation", "replay"])
@pytest.mark.parametrize(
    "changed", ["registry", "fallback", "dispatch", "code", "defaults", "entry"]
)
def test_q_alias_drift_denied_before_side_effects(route, phase, changed, monkeypatch):
    owner, controller, _ = make_owner(route)
    calls = []
    with pytest.raises(CheckpointExecutionError):
        with controller.session() as session:
            if phase == "replay":
                ticket = session.begin_forward(owner, {"position_ids": torch.zeros(1)})

                def block(hidden, metadata):
                    calls.append(1)
                    return owner.factors(hidden).square()

                output = ticket.run(0, block, torch.ones(1, 2))
                ticket.bind_output(output)
            if changed == "registry":
                monkeypatch.setattr(
                    matched_lora, "ALL_ATTENTION_FUNCTIONS", AttentionInterface()
                )
            elif changed == "fallback":
                monkeypatch.setattr(
                    matched_lora, "eager_attention_forward", lambda *args: None
                )
            elif changed == "dispatch":
                monkeypatch.setattr(
                    AttentionInterface, "get_interface", lambda *args: None
                )
            elif changed == "code":

                def replacement():
                    marker = None

                    def changed_code(*args):
                        return marker

                    return changed_code

                monkeypatch.setattr(
                    AttentionInterface.get_interface, "__code__", replacement().__code__
                )
            elif changed == "defaults":
                monkeypatch.setattr(
                    AttentionInterface.get_interface, "__defaults__", (None,)
                )
            else:
                monkeypatch.setitem(
                    matched_lora.ALL_ATTENTION_FUNCTIONS._local_mapping,
                    route,
                    lambda *args: None,
                )
            for p in owner.factors.parameters():
                p.grad = torch.ones_like(p)
            if phase == "preparation":
                session.begin_forward(owner, {"position_ids": torch.zeros(1)})
                calls.append(1)
            else:
                session.backward(output.sum())
    assert calls == ([] if phase == "preparation" else [1])
    assert controller._active is None
    assert all(p.grad is None for p in owner.factors.parameters())


@pytest.mark.parametrize("route", ["eager", "sdpa"])
def test_foreign_q_registry_rejected_without_calling_resolver(route, monkeypatch):
    _, _, getter = make_owner(route)
    calls = []

    class Foreign:
        def get_interface(self, route, default):
            calls.append(route)
            return default

    monkeypatch.setattr(matched_lora, "ALL_ATTENTION_FUNCTIONS", Foreign())
    with pytest.raises(CheckpointExecutionError):
        getter()
    assert not calls


@pytest.mark.parametrize("route", ["eager", "sdpa"])
@pytest.mark.parametrize(
    "bad", ["override", "attribute", "mapping", "entry", "bound", "super"]
)
def test_registry_schema_rejected_without_resolver_execution(route, bad, monkeypatch):
    _, _, getter = make_owner(route)
    registry = matched_lora.ALL_ATTENTION_FUNCTIONS
    calls = []

    def resolver(*args):
        calls.append(1)
        return None

    if bad == "override":
        # setattr teardown restores an inherited bound method as an instance
        # attribute. Dict patching removes this newly inserted override instead.
        monkeypatch.setitem(vars(registry), "get_interface", resolver)
    elif bad == "attribute":
        monkeypatch.setattr(registry, "unknown", 1, raising=False)
    elif bad == "mapping":
        monkeypatch.setattr(registry, "_local_mapping", [])
    elif bad == "entry":
        monkeypatch.setitem(registry._local_mapping, route, None)
    elif bad == "bound":
        monkeypatch.setattr(
            registry, "_local_mapping", {str(i): resolver for i in range(129)}
        )
    else:
        monkeypatch.setitem(
            AttentionInterface.get_interface.__globals__, "super", resolver
        )
    with pytest.raises(CheckpointExecutionError):
        getter()
    assert not calls


@pytest.mark.parametrize("route", ["eager", "sdpa"])
def test_local_mapping_data_descriptor_rejected_without_access(route, monkeypatch):
    _, _, getter = make_owner(route)
    calls = []

    def redirect(registry):
        calls.append(1)
        return {}

    monkeypatch.setattr(
        AttentionInterface, "_local_mapping", property(redirect), raising=False
    )
    with pytest.raises(CheckpointExecutionError):
        getter()
    assert not calls


@pytest.mark.parametrize("name,expected", [("KeyError", KeyError), ("super", super)])
def test_resolver_uses_function_actual_builtins_not_rebound_namespace(name, expected):
    actual = {"KeyError": KeyError, "super": super}
    namespace = {"__builtins__": actual}
    original = AttentionInterface.get_interface
    function = types.FunctionType(
        original.__code__, namespace, closure=original.__closure__
    )
    namespace["__builtins__"] = dict(actual)
    assert function.__builtins__ is actual
    actual[name] = lambda *args: None
    with pytest.raises(CheckpointExecutionError):
        _builtin_binding(function, name, expected)


def test_registry_negative_controls_leave_no_instance_override():
    assert set(vars(matched_lora.ALL_ATTENTION_FUNCTIONS)) == {"_local_mapping"}


@pytest.mark.parametrize("name,expected", [("KeyError", KeyError), ("super", super)])
def test_rebound_advertised_builtins_ignored_but_actual_global_shadow_checked(
    name, expected
):
    namespace = {"__builtins__": {"KeyError": KeyError, "super": super}}
    original = AttentionInterface.get_interface
    function = types.FunctionType(
        original.__code__, namespace, closure=original.__closure__
    )
    before = _builtin_binding(function, name, expected)
    namespace["__builtins__"] = {name: None}
    assert _builtin_binding(function, name, expected) == before
    namespace[name] = None
    with pytest.raises(CheckpointExecutionError):
        _builtin_binding(function, name, expected)
