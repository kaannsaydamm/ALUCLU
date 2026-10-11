"""Tiny disabled-HF dispatch inventory; no model assets or numerical run."""

import types

import pytest
from torch import nn
from transformers import modeling_layers
from transformers.modeling_layers import GradientCheckpointingLayer

from aluclu.alc_r0.checkpoint_execution import CheckpointExecutionError
from aluclu.alc_r0.checkpoint_state import computational_state_fingerprint


class TinyLayer(GradientCheckpointingLayer):
    def forward(self, value):
        return value


def fingerprint(module):
    return computational_state_fingerprint({"layer": module})


def test_real_disabled_hf_class_cell_has_stable_binding():
    module = TinyLayer()
    assert fingerprint(module) == fingerprint(module)


@pytest.mark.parametrize("value", [True, 0, None, "false"])
def test_only_exact_disabled_boolean_route_is_admitted(value):
    module = TinyLayer()
    module.gradient_checkpointing = value
    with pytest.raises(CheckpointExecutionError):
        fingerprint(module)


def test_class_is_not_admitted_as_arbitrary_attribute():
    module = nn.Module()
    module.arbitrary = GradientCheckpointingLayer
    with pytest.raises(CheckpointExecutionError):
        fingerprint(module)


@pytest.mark.parametrize(
    "changed", ["namespace", "super", "code", "closure", "method", "mro"]
)
def test_disabled_dispatch_mutations_are_rejected(changed, monkeypatch):
    module = TinyLayer()
    fingerprint(module)
    operation = GradientCheckpointingLayer.__call__
    if changed == "namespace":
        monkeypatch.setattr(modeling_layers, "GradientCheckpointingLayer", nn.Module)
    elif changed == "super":
        monkeypatch.setitem(operation.__globals__, "super", lambda: None)
    elif changed == "code":

        class Donor(nn.Module):
            def __call__(self, *args, **kwargs):
                return super().__call__(*args, **kwargs)

        monkeypatch.setattr(operation, "__code__", Donor.__call__.__code__)
    elif changed == "closure":

        def cell(value):
            return (lambda: value).__closure__[0]

        replacement = types.FunctionType(
            operation.__code__, operation.__globals__, closure=(cell(nn.Module),)
        )
        monkeypatch.setattr(GradientCheckpointingLayer, "__call__", replacement)
    elif changed == "method":
        monkeypatch.setattr(GradientCheckpointingLayer, "__call__", lambda *args: None)
    else:

        class Other(nn.Module):
            def __call__(self, *args, **kwargs):
                return None

        class Changed(GradientCheckpointingLayer, Other):
            def forward(self, value):
                return value

        module = Changed()
    with pytest.raises(CheckpointExecutionError):
        fingerprint(module)


@pytest.mark.parametrize("name", ["__call__", "_wrapped_call_impl", "_call_impl"])
def test_downstream_module_dispatch_mutation_is_bound(name, monkeypatch):
    module = TinyLayer()
    before = fingerprint(module)
    monkeypatch.setattr(nn.Module, name, lambda *args, **kwargs: None)
    assert fingerprint(module) != before


def test_builtin_super_shadow_is_denied(monkeypatch):
    module = TinyLayer()
    operation = GradientCheckpointingLayer.__call__
    original = operation.__globals__["__builtins__"]
    namespace = dict(original if type(original) is dict else vars(original))
    namespace["super"] = lambda: None
    monkeypatch.setitem(operation.__globals__, "__builtins__", namespace)
    with pytest.raises(CheckpointExecutionError):
        fingerprint(module)


def test_function_builtin_cache_and_global_alias_must_agree(monkeypatch):
    operation = GradientCheckpointingLayer.__call__
    monkeypatch.setitem(
        operation.__globals__, "__builtins__", dict(operation.__builtins__)
    )
    with pytest.raises(CheckpointExecutionError):
        fingerprint(TinyLayer())


def test_actual_function_builtin_super_mutation_is_denied():
    from aluclu.alc_r0.checkpoint_hf_dispatch import disabled_hf_dispatch

    module = TinyLayer()
    operation = GradientCheckpointingLayer.__call__
    namespace = operation.__builtins__
    original = namespace["super"]
    failure = None
    # Restore before pytest/framework machinery runs: this is the real shared
    # builtins mapping, not a substitute globals dictionary.
    try:
        namespace["super"] = lambda: None
        try:
            disabled_hf_dispatch(module, operation, lambda value: value)
        except CheckpointExecutionError as error:
            failure = error
    finally:
        namespace["super"] = original
    assert failure is not None


def test_unrelated_class_closure_is_still_denied():
    class Foreign(nn.Module):
        def __call__(self, *args, **kwargs):
            return super().__call__(*args, **kwargs)

    with pytest.raises(CheckpointExecutionError):
        fingerprint(Foreign())


def test_checkpoint_descriptor_is_not_invoked():
    calls = []

    class Descriptor(TinyLayer):
        @property
        def gradient_checkpointing(self):
            calls.append(1)
            return False

    with pytest.raises(CheckpointExecutionError):
        from aluclu.alc_r0.checkpoint_hf_dispatch import disabled_hf_dispatch

        disabled_hf_dispatch(
            Descriptor(), GradientCheckpointingLayer.__call__, lambda x: x
        )
    assert not calls


@pytest.mark.parametrize("name", ["__defaults__", "__kwdefaults__"])
def test_dispatch_defaults_are_bound(name, monkeypatch):
    module = TinyLayer()
    before = fingerprint(module)
    monkeypatch.setattr(
        GradientCheckpointingLayer.__call__,
        name,
        (None,) if name == "__defaults__" else {"flag": False},
    )
    assert fingerprint(module) != before
