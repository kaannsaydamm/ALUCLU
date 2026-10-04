"""Tiny Python dispatch/lookup drift, not host or native semantic proof."""

import types

import pytest
import torch
from test_alc_r0_factor_dependency_state import make_owner
from torch import nn

from aluclu.alc_r0 import matched_lora, research_capsule
from aluclu.alc_r0.checkpoint_execution import CheckpointExecutionError
from aluclu.alc_r0.checkpoint_state import computational_state_fingerprint


def call(self, *args, **kwargs):
    return nn.Module._call_impl(self, *args, **kwargs)


def alternate_call(self, *args, **kwargs):
    _unused = None
    return nn.Module._call_impl(self, *args, **kwargs)


def attribute(self, name):
    return object.__getattribute__(self, name)


def alternate_attribute(self, name):
    _unused = None
    return object.__getattribute__(self, name)


@pytest.mark.parametrize(
    "name", ["__call__", "_call_impl", "_wrapped_call_impl", "__getattribute__"]
)
def test_same_function_dispatch_code_must_change_fingerprint(name, monkeypatch):
    original = attribute if name == "__getattribute__" else call
    replacement = alternate_attribute if name == "__getattribute__" else alternate_call
    function = types.FunctionType(original.__code__, original.__globals__)
    cls = type("DispatchLinear", (nn.Linear,), {name: function})
    module = cls(2, 2)
    before = computational_state_fingerprint({"module": module})
    monkeypatch.setattr(function, "__code__", replacement.__code__)
    assert computational_state_fingerprint({"module": module}) != before


@pytest.mark.parametrize("arm", ["capsule", "lora"])
@pytest.mark.parametrize("changed", ["getitem", "cast"])
def test_factor_lookup_code_or_cast_alias_must_change_binding(
    arm, changed, monkeypatch
):
    _, _, getter, _ = make_owner(arm)
    before = getter()
    if changed == "getitem":

        def same_lookup(self, key):
            return self._modules[key]

        monkeypatch.setattr(nn.ModuleDict.__getitem__, "__code__", same_lookup.__code__)
    else:
        namespace = research_capsule if arm == "capsule" else matched_lora
        monkeypatch.setattr(namespace, "cast", lambda kind, value: value)
    try:
        after = getter()
    except CheckpointExecutionError:
        return
    assert after != before


@pytest.mark.parametrize("arm", ["capsule", "lora"])
@pytest.mark.parametrize("phase", ["preparation", "replay"])
def test_factor_lookup_drift_denied_before_side_effects(arm, phase, monkeypatch):
    owner, controller, _, operation = make_owner(arm)
    calls = []
    with pytest.raises(CheckpointExecutionError):
        with controller.session() as session:
            if phase == "replay":
                ticket = session.begin_forward(owner, {"position_ids": torch.zeros(1)})

                def block(hidden, metadata):
                    calls.append(1)
                    return operation(hidden)

                output = ticket.run(
                    0, block, torch.linspace(-1, 1, 576).reshape(1, 1, 576)
                )
                ticket.bind_output(output)

            def same_lookup(self, key):
                return self._modules[key]

            monkeypatch.setattr(
                nn.ModuleDict.__getitem__, "__code__", same_lookup.__code__
            )
            if phase == "preparation":
                session.begin_forward(owner, {"position_ids": torch.zeros(1)})
                calls.append(1)
            else:
                session.backward(output.square().sum())
    assert calls == ([] if phase == "preparation" else [1])
    assert controller._active is None
    assert all(p.grad is None for p in owner.factors.parameters())


@pytest.mark.parametrize(
    "kind,name",
    [
        (nn.ModuleDict, name)
        for name in ("__getitem__", "__len__", "__iter__", "__contains__")
    ]
    + [
        (nn.ModuleList, name)
        for name in ("__getitem__", "__len__", "__iter__", "_get_abs_string_index")
    ],
)
def test_container_same_function_code_changes_binding(kind, name, monkeypatch):
    module = kind(
        {"x": nn.Linear(2, 2)} if kind is nn.ModuleDict else [nn.Linear(2, 2)]
    )
    before = computational_state_fingerprint({"module": module})
    monkeypatch.setattr(getattr(kind, name), "__code__", (lambda *args: None).__code__)
    assert computational_state_fingerprint({"module": module}) != before


@pytest.mark.parametrize("name", ["__call__", "_call_impl"])
def test_dispatch_property_rejected_without_getter_execution(name):
    calls = []

    def getter(module):
        calls.append(1)
        return None

    cls = type("DescriptorLinear", (nn.Linear,), {name: property(getter)})
    module = cls(2, 2)
    with pytest.raises(CheckpointExecutionError, match="dispatch/lookup"):
        computational_state_fingerprint({"module": module})
    assert not calls


@pytest.mark.parametrize("arm", ["capsule", "lora"])
def test_same_cast_function_code_changes_binding(arm, monkeypatch):
    _, _, getter, _ = make_owner(arm)
    before = getter()
    namespace = research_capsule if arm == "capsule" else matched_lora
    monkeypatch.setattr(
        namespace.cast, "__code__", (lambda kind, value: value).__code__
    )
    assert getter() != before


@pytest.mark.parametrize(
    "name", ["__call__", "_call_impl", "_wrapped_call_impl", "__getattribute__"]
)
def test_same_dispatch_function_defaults_changes_binding(name, monkeypatch):
    original = attribute if name == "__getattribute__" else call
    function = types.FunctionType(original.__code__, original.__globals__)
    cls = type("DefaultLinear", (nn.Linear,), {name: function})
    module = cls(2, 2)
    before = computational_state_fingerprint({"module": module})
    monkeypatch.setattr(function, "__defaults__", (None,))
    assert computational_state_fingerprint({"module": module}) != before
