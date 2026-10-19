"""Tiny mask registry closure controls, not host parity or learning evidence."""

import types

import pytest
import torch
from test_alc_r0_attention_dependencies import make_owner
from transformers import masking_utils as masks

from aluclu.alc_r0 import checkpoint_state, host_wrapper
from aluclu.alc_r0.checkpoint_execution import CheckpointExecutionError


@pytest.mark.parametrize("route", ["eager", "sdpa"])
@pytest.mark.parametrize("phase", ["preparation", "replay"])
@pytest.mark.parametrize("changed", ["alias", "dispatch", "local_entry"])
def test_mask_registry_drift_denied_before_side_effects(
    route, phase, changed, monkeypatch
):
    owner, controller, _ = make_owner(route)
    calls = []
    with pytest.raises(CheckpointExecutionError, match="mask|fingerprint"):
        with controller.session() as session:
            if phase == "replay":
                ticket = session.begin_forward(owner, {"position_ids": torch.zeros(1)})

                def block(hidden, metadata):
                    calls.append("block")
                    return owner.factors(hidden).square()

                output = ticket.run(0, block, torch.ones(1, 2))
                ticket.bind_output(output)
            if changed == "alias":
                replacement = masks.AttentionMaskInterface()
                replacement._local_mapping[route] = lambda **kwargs: None
                monkeypatch.setattr(masks, "ALL_MASK_ATTENTION_FUNCTIONS", replacement)
            elif changed == "dispatch":

                def redirect(registry, key):
                    calls.append("resolver")
                    return masks.eager_mask if key == "eager" else masks.sdpa_mask

                monkeypatch.setattr(
                    masks.AttentionMaskInterface, "__getitem__", redirect
                )
            else:
                monkeypatch.setitem(
                    masks.ALL_MASK_ATTENTION_FUNCTIONS._local_mapping,
                    "unselected_probe",
                    lambda **kwargs: None,
                )
            for p in owner.factors.parameters():
                p.grad = torch.ones_like(p)
            if phase == "preparation":
                session.begin_forward(owner, {"position_ids": torch.zeros(1)})
                calls.append("block")
            else:
                session.backward(output.sum())
    assert calls == ([] if phase == "preparation" else ["block"])
    assert controller._active is None
    assert all(p.grad is None for p in owner.factors.parameters())


@pytest.mark.parametrize("route", ["eager", "sdpa"])
@pytest.mark.parametrize("alias", ["state", "producer"])
def test_foreign_mask_registry_rejected_without_resolver_execution(
    route, alias, monkeypatch
):
    _, _, getter = make_owner(route)
    calls = []

    class Foreign:
        def __getitem__(self, key):
            calls.append(key)
            return masks.eager_mask if key == "eager" else masks.sdpa_mask

    namespace = checkpoint_state if alias == "state" else masks
    monkeypatch.setattr(namespace, "ALL_MASK_ATTENTION_FUNCTIONS", Foreign())
    with pytest.raises(CheckpointExecutionError, match="mask registry"):
        getter()
    assert not calls


@pytest.mark.parametrize("route", ["eager", "sdpa"])
@pytest.mark.parametrize("invalid", ["unknown", "mapping", "entry", "bound", "key"])
def test_mask_registry_schema_rejected(route, invalid, monkeypatch):
    _, _, getter = make_owner(route)
    registry = masks.ALL_MASK_ATTENTION_FUNCTIONS
    if invalid == "unknown":
        monkeypatch.setitem(vars(registry), "unknown", 1)
    elif invalid == "mapping":
        monkeypatch.setattr(registry, "_local_mapping", [])
    elif invalid == "entry":
        monkeypatch.setitem(registry._local_mapping, "probe", None)
    elif invalid == "bound":
        monkeypatch.setattr(
            registry, "_local_mapping", {str(i): masks.eager_mask for i in range(129)}
        )
    else:
        monkeypatch.setitem(registry._local_mapping, "non_ascii_é", masks.eager_mask)
    with pytest.raises(CheckpointExecutionError, match="mask registry"):
        getter()


@pytest.mark.parametrize("route", ["eager", "sdpa"])
@pytest.mark.parametrize("field", ["_local_mapping", "_global_mapping"])
def test_mask_registry_descriptor_rejected_without_access(route, field, monkeypatch):
    _, _, getter = make_owner(route)
    calls = []

    def redirect(registry):
        calls.append(1)
        return {route: masks.eager_mask if route == "eager" else masks.sdpa_mask}

    monkeypatch.setattr(
        masks.AttentionMaskInterface, field, property(redirect), raising=False
    )
    with pytest.raises(CheckpointExecutionError, match="mask registry"):
        getter()
    assert not calls


@pytest.mark.parametrize("route", ["eager", "sdpa"])
def test_mask_registry_global_route_presence_required(route, monkeypatch):
    _, _, getter = make_owner(route)
    registry = masks.ALL_MASK_ATTENTION_FUNCTIONS
    monkeypatch.setitem(
        registry._local_mapping,
        route,
        masks.eager_mask if route == "eager" else masks.sdpa_mask,
    )
    monkeypatch.delitem(registry._global_mapping, route)
    with pytest.raises(CheckpointExecutionError, match="mask registry"):
        getter()


def test_negative_controls_leave_registry_schema_unchanged():
    assert set(vars(masks.ALL_MASK_ATTENTION_FUNCTIONS)) == {"_local_mapping"}
    assert not masks.ALL_MASK_ATTENTION_FUNCTIONS._local_mapping


def copy_function(function, namespace):
    copied = types.FunctionType(
        function.__code__, namespace, function.__name__, function.__defaults__,
        function.__closure__,
    )
    copied.__kwdefaults__ = function.__kwdefaults__
    return copied


@pytest.mark.parametrize("route", ["eager", "sdpa"])
@pytest.mark.parametrize("role", ["producer", "preprocess"])
def test_actual_copied_function_namespace_registry_drift(route, role, monkeypatch):
    _, _, getter = make_owner(route)
    producer_namespace = dict(masks.create_causal_mask.__globals__)
    actual = producer_namespace
    if role == "preprocess":
        original = masks._preprocess_mask_arguments
        actual = dict(original.__globals__)
        producer_namespace["_preprocess_mask_arguments"] = copy_function(original, actual)
    producer = copy_function(masks.create_causal_mask, producer_namespace)
    monkeypatch.setattr(host_wrapper, "create_causal_mask", producer)
    before = getter()
    assert getter() == before
    replacement = masks.AttentionMaskInterface()
    replacement._local_mapping[route] = lambda **kwargs: None
    actual["ALL_MASK_ATTENTION_FUNCTIONS"] = replacement
    with pytest.raises(CheckpointExecutionError, match="mask registry"):
        getter()


@pytest.mark.parametrize("route", ["eager", "sdpa"])
def test_registry_lookup_override_denied_before_attribute_access(route, monkeypatch):
    _, _, getter = make_owner(route)
    calls = []

    def lookup(registry, key):
        calls.append(key)
        return object.__getattribute__(registry, key)

    monkeypatch.setattr(masks.AttentionMaskInterface, "__getattribute__", lookup)
    with pytest.raises(CheckpointExecutionError, match="mask registry"):
        getter()
    assert not calls


@pytest.mark.parametrize("route", ["eager", "sdpa"])
def test_exact_alias_with_reviewed_selection_is_stable(route, monkeypatch):
    _, _, getter = make_owner(route)
    alternate = masks.AttentionMaskInterface()
    monkeypatch.setattr(masks, "ALL_MASK_ATTENTION_FUNCTIONS", alternate)
    before = getter()
    assert getter() == before
