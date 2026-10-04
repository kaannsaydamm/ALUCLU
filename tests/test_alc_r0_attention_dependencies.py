"""Tiny CPU helper drift fixtures, not loaded-host forward or learning."""

import pytest
import torch
from torch import nn
from transformers import LlamaConfig
from transformers.integrations import sdpa_attention as sdpa
from transformers.models.llama import modeling_llama as llama

from aluclu.alc_r0 import matched_lora
from aluclu.alc_r0.checkpoint_execution import (
    CheckpointController,
    CheckpointExecutionError,
)
from aluclu.alc_r0.checkpoint_state import computational_state_fingerprint

CASES = [
    (route, namespace, name)
    for route in ("eager", "sdpa")
    for namespace, name in (
        (llama, "rotate_half"),
        (llama, "apply_rotary_pos_emb"),
        (matched_lora, "apply_rotary_pos_emb"),
    )
] + [
    ("eager", llama, "repeat_kv"),
    ("sdpa", sdpa, "repeat_kv"),
    ("sdpa", sdpa, "use_gqa_in_sdpa"),
    ("sdpa", sdpa, "create_position_bias_mask"),
    ("sdpa", sdpa, "_is_torch_xpu_available"),
    ("sdpa", sdpa, "_is_torch_npu_available"),
    ("sdpa", sdpa, "_is_torch_greater_or_equal_than_2_8"),
]


def make_owner(route):
    owner = nn.Module()
    owner.base = nn.Module()
    config = LlamaConfig(
        hidden_size=4,
        num_attention_heads=2,
        num_key_value_heads=2,
        intermediate_size=8,
    )
    config._attn_implementation = route
    owner.base.attention = llama.LlamaAttention(config, layer_idx=0)
    owner.base.requires_grad_(False).eval()
    owner.factors = nn.Linear(2, 2, bias=False)

    def getter():
        return computational_state_fingerprint(
            {"base": owner.base, "factors": owner.factors}
        )

    controller = CheckpointController(
        owner,
        base_getter=lambda: owner.base,
        factor_getter=lambda: owner.factors,
        layer_count=1,
        state_fingerprint_getter=getter,
    )
    return owner, controller, getter


@pytest.mark.parametrize("route,namespace,name", CASES)
@pytest.mark.parametrize("phase", ["preparation", "replay"])
def test_attention_helper_drift_denied_before_side_effects(
    route,
    namespace,
    name,
    phase,
    monkeypatch,
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


def test_rotate_half_numeric_change_must_change_binding(monkeypatch):
    _, _, getter = make_owner("eager")
    before = getter()
    query = torch.arange(8, dtype=torch.float32).reshape(1, 1, 2, 4)
    cos = torch.zeros(1, 2, 4)
    sin = torch.ones(1, 2, 4)
    original, _ = llama.apply_rotary_pos_emb(query, query, cos, sin)
    monkeypatch.setattr(llama, "rotate_half", lambda value: value)
    changed, _ = llama.apply_rotary_pos_emb(query, query, cos, sin)
    assert not torch.equal(original, changed)
    assert getter() != before


@pytest.mark.parametrize("route", ["eager", "sdpa"])
def test_unchanged_attention_inventory_completes_factor_gradient_session(route):
    owner, controller, getter = make_owner(route)
    before = getter()
    with controller.session() as session:
        ticket = session.begin_forward(owner, {"position_ids": torch.zeros(1)})
        output = ticket.run(
            0, lambda hidden, metadata: owner.factors(hidden).square(), torch.ones(1, 2)
        )
        ticket.bind_output(output)
        session.backward(output.sum())
    assert getter() == before
    assert controller._active is None
    assert all(
        p.grad is not None and torch.isfinite(p.grad).all()
        for p in owner.factors.parameters()
    )
    assert all(p.grad is None for p in owner.base.parameters())


@pytest.mark.parametrize(
    "namespace,name",
    [
        (llama, "rotate_half"),
        (matched_lora, "apply_rotary_pos_emb"),
        (sdpa, "repeat_kv"),
    ],
)
def test_noncallable_helper_schema_rejected(namespace, name, monkeypatch):
    _, _, getter = make_owner("sdpa")
    monkeypatch.setattr(namespace, name, 1)
    with pytest.raises(CheckpointExecutionError, match="attention helper"):
        getter()


@pytest.mark.parametrize(
    "name",
    [
        "_is_torch_xpu_available",
        "_is_torch_npu_available",
        "_is_torch_greater_or_equal_than_2_8",
    ],
)
def test_nonboolean_route_flag_rejected(name, monkeypatch):
    _, _, getter = make_owner("sdpa")
    monkeypatch.setattr(sdpa, name, 1)
    with pytest.raises(CheckpointExecutionError, match="route flag"):
        getter()


def test_same_function_default_mutation_changes_binding(monkeypatch):
    _, _, getter = make_owner("sdpa")
    before = getter()
    monkeypatch.setattr(sdpa.repeat_kv, "__defaults__", (1,))
    assert getter() != before


def test_gqa_flag_changes_actual_route_and_binding(monkeypatch):
    _, _, getter = make_owner("sdpa")
    monkeypatch.setattr(sdpa, "_is_torch_xpu_available", False)
    monkeypatch.setattr(sdpa, "_is_torch_greater_or_equal_than_2_8", False)
    before = getter()
    key = torch.ones(1, 1, 2, 4)
    assert sdpa.use_gqa_in_sdpa(None, key, key) is True
    monkeypatch.setattr(sdpa, "_is_torch_xpu_available", True)
    assert sdpa.use_gqa_in_sdpa(None, key, key) is False
    assert getter() != before
