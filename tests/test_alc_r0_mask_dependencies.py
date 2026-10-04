"""Mask helper drift fixtures; no loaded host or learning acceptance."""

import pytest
import torch
from test_alc_r0_attention_dependencies import make_owner
from transformers import masking_utils as masks
from transformers.models.llama import modeling_llama as llama

from aluclu.alc_r0 import host_wrapper
from aluclu.alc_r0.checkpoint_execution import CheckpointExecutionError

CASES = [
    (masks, name)
    for name in (
        "prepare_padding_mask",
        "_ignore_causal_mask_sdpa",
        "_ignore_bidirectional_mask_sdpa",
        "_non_vmap_expansion_sdpa",
        "padding_mask_function",
        "and_masks",
        "causal_mask_function",
        "_preprocess_mask_arguments",
        "fast_all",
        "is_tracing",
        "_is_torch_greater_or_equal_than_2_6",
        "_is_torch_xpu_available",
    )
] + [(host_wrapper, "create_causal_mask"), (llama, "create_causal_mask")]


@pytest.mark.parametrize("route", ["eager", "sdpa"])
@pytest.mark.parametrize("namespace,name", CASES)
@pytest.mark.parametrize("phase", ["preparation", "replay"])
def test_mask_helper_drift_denied_before_side_effects(
    route, namespace, name, phase, monkeypatch
):
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
            original = getattr(namespace, name)
            replacement = not original if type(original) is bool else lambda *args: None
            monkeypatch.setattr(namespace, name, replacement)
            for parameter in owner.factors.parameters():
                parameter.grad = torch.ones_like(parameter)
            if phase == "preparation":
                session.begin_forward(owner, {"position_ids": torch.zeros(1)})
                calls.append(1)
            else:
                session.backward(output.sum())
    assert calls == ([] if phase == "preparation" else [1])
    assert controller._active is None
    assert all(p.grad is None for p in owner.factors.parameters())


@pytest.mark.parametrize("route", ["eager", "sdpa"])
def test_padding_helper_numeric_change_changes_binding(route, monkeypatch):
    _, _, getter = make_owner(route)
    before = getter()
    kwargs = dict(
        batch_size=1,
        q_length=2,
        kv_length=2,
        attention_mask=torch.tensor([[True, False]]),
        allow_is_causal_skip=False,
        dtype=torch.float32,
    )
    interface = masks.ALL_MASK_ATTENTION_FUNCTIONS[route]
    original = interface(**kwargs)
    monkeypatch.setattr(
        masks,
        "prepare_padding_mask",
        lambda attention_mask, kv_length, kv_offset: torch.ones_like(attention_mask),
    )
    changed = interface(**kwargs)
    assert not torch.equal(original, changed)
    assert getter() != before


@pytest.mark.parametrize("route", ["eager", "sdpa"])
@pytest.mark.parametrize(
    "name,value",
    [
        ("prepare_padding_mask", None),
        ("create_causal_mask", 1),
        ("_is_torch_greater_or_equal_than_2_6", 1),
        ("_is_torch_xpu_available", None),
    ],
)
def test_unknown_mask_schema_rejected(route, name, value, monkeypatch):
    _, _, getter = make_owner(route)
    monkeypatch.setattr(masks, name, value)
    with pytest.raises(CheckpointExecutionError, match="unsupported mask"):
        getter()


def test_same_mask_helper_default_mutation_changes_binding(monkeypatch):
    _, _, getter = make_owner("sdpa")
    before = getter()
    function = masks._ignore_causal_mask_sdpa
    monkeypatch.setattr(function, "__defaults__", (7,))
    assert getter() != before
