"""Additional mask route/endpoint drift, not host parity or learning."""

import pytest
import torch
from test_alc_r0_attention_dependencies import make_owner
from transformers import masking_utils as masks

from aluclu.alc_r0.checkpoint_execution import CheckpointExecutionError

CASES = [
    (masks, name)
    for name in (
        "find_packed_sequence_indices",
        "packed_sequence_mask_function",
        "or_masks",
        "blockwise_overlay",
        "maybe_pad_block_sequence_ids",
        "_can_skip_bidirectional_mask_xpu",
        "bidirectional_mask_function",
        "create_bidirectional_mask",
        "_vmap_expansion_sdpa",
    )
] + [(torch, "arange"), (torch, "diff"), (torch, "where"), (masks.F, "pad")]


@pytest.mark.parametrize("route", ["eager", "sdpa"])
@pytest.mark.parametrize("namespace,name", CASES)
@pytest.mark.parametrize("phase", ["preparation", "replay"])
def test_mask_subdependency_drift_denied(route, namespace, name, phase, monkeypatch):
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
            monkeypatch.setattr(namespace, name, lambda *args, **kwargs: None)
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
def test_actual_packed_mask_change_changes_binding(route, monkeypatch):
    owner, _, getter = make_owner(route)
    before = getter()
    kwargs = dict(
        config=owner.base.attention.config,
        inputs_embeds=torch.zeros(1, 4, 4),
        attention_mask=None,
        past_key_values=None,
        position_ids=torch.tensor([[0, 1, 0, 1]]),
        allow_is_causal_skip=False,
    )
    original = masks.create_causal_mask(**kwargs)
    monkeypatch.setattr(masks, "find_packed_sequence_indices", lambda value: None)
    changed = masks.create_causal_mask(**kwargs)
    assert not torch.equal(original, changed)
    assert getter() != before


@pytest.mark.parametrize("route", ["eager", "sdpa"])
@pytest.mark.parametrize(
    "namespace,name",
    [
        (masks, "find_packed_sequence_indices"),
        (torch, "diff"),
        (masks, "F"),
    ],
)
def test_unknown_subroute_schema_rejected(route, namespace, name, monkeypatch):
    _, _, getter = make_owner(route)
    monkeypatch.setattr(namespace, name, None)
    with pytest.raises(CheckpointExecutionError, match="unsupported mask"):
        getter()


def test_actual_block_padding_endpoint_change_changes_binding(monkeypatch):
    _, _, getter = make_owner("eager")
    before = getter()
    block_ids = torch.tensor([[0, 0]])
    original = masks.maybe_pad_block_sequence_ids(block_ids, None, 4, 0)
    monkeypatch.setattr(
        masks.F,
        "pad",
        lambda input_tensor, *args, **kwargs: torch.zeros(
            (1, 4), dtype=input_tensor.dtype
        ),
    )
    changed = masks.maybe_pad_block_sequence_ids(block_ids, None, 4, 0)
    assert not torch.equal(original, changed)
    assert getter() != before
