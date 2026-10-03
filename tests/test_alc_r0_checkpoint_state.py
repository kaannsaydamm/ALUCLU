"""Computational attribute fingerprint fixtures, no assets/model/updates."""

import pytest
import torch
from torch import nn
from transformers import LlamaConfig

from aluclu.alc_r0.checkpoint_execution import (
    CheckpointController,
    CheckpointExecutionError,
)
from aluclu.alc_r0.checkpoint_state import computational_state_fingerprint


def make_owner():
    owner = nn.Module()
    owner.base = nn.Linear(2, 2).requires_grad_(False).eval()
    owner.factors = nn.Linear(2, 2, bias=False)
    owner.base.config = LlamaConfig(hidden_size=4, num_attention_heads=2)
    owner.base.scaling = 0.5
    owner.base.variance_epsilon = 1e-5
    owner.base.private_tensor = torch.ones(2)

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


def test_fingerprint_stable_without_state_mutation():
    _, _, getter = make_owner()
    assert getter() == getter()
    assert len(getter()) == 64


@pytest.mark.parametrize(
    "mutation",
    [
        "config",
        "scaling",
        "epsilon",
        "tensor",
        "tensor_data",
        "tensor_replace",
        "new_attr",
        "forward",
        "callback",
    ],
)
def test_computational_drift_aborts_before_ticket_and_clears_gradients(mutation):
    owner, controller, _ = make_owner()
    with pytest.raises(CheckpointExecutionError):
        with controller.session() as session:
            for p in owner.factors.parameters():
                p.grad = torch.ones_like(p)
            if mutation == "config":
                owner.base.config.rope_parameters["rope_theta"] += 1
            elif mutation == "scaling":
                owner.base.scaling = 0.6
            elif mutation == "epsilon":
                owner.base.variance_epsilon = 1e-4
            elif mutation == "tensor":
                owner.base.private_tensor.add_(1)
            elif mutation == "tensor_data":
                owner.base.private_tensor.data.add_(1)
            elif mutation == "tensor_replace":
                owner.base.private_tensor = owner.base.private_tensor.clone()
            elif mutation == "new_attr":
                owner.base.other_state = True
            elif mutation == "forward":
                owner.base.forward = lambda x: x
            else:
                controller.state_fingerprint_getter = lambda: "0" * 64
            session.begin_forward(owner, {"position_ids": torch.zeros(1)})
    assert all(p.grad is None for p in owner.factors.parameters())
    assert controller._active is None


def test_drift_denied_before_recompute_side_effect():
    owner, controller, _ = make_owner()
    calls = []
    with pytest.raises(CheckpointExecutionError):
        with controller.session() as session:
            ticket = session.begin_forward(owner, {"position_ids": torch.zeros(1)})

            def block(hidden, metadata):
                calls.append(1)
                return owner.factors(hidden).square()

            output = ticket.run(0, block, torch.ones(1, 2))
            ticket.bind_output(output)
            owner.base.scaling = 0.7
            session.backward(output.sum())
    assert calls == [1]


@pytest.mark.parametrize("value", [None, "", "a" * 63, "A" * 64, "g" * 64, 123])
def test_invalid_fingerprint_result_rejected_on_entry(value):
    owner, controller, _ = make_owner()
    controller.state_fingerprint_getter = lambda: value
    with pytest.raises(CheckpointExecutionError, match="fingerprint"):
        with controller.session():
            pass
    assert controller._active is None


@pytest.mark.parametrize("bad", [object(), float("nan"), torch.ones(20000)])
def test_unsupported_or_unbounded_state_rejected(bad):
    owner, _, getter = make_owner()
    owner.base.unsupported = bad
    with pytest.raises(CheckpointExecutionError):
        getter()


def test_cycle_rejected_without_recursion_failure():
    owner, _, getter = make_owner()
    cyclic = []
    cyclic.append(cyclic)
    owner.base.cyclic = cyclic
    with pytest.raises(CheckpointExecutionError, match="cycle"):
        getter()


def test_local_hook_denied_and_cleanup_restores_inventory():
    owner, _, getter = make_owner()
    before = getter()
    handle = owner.base.register_forward_hook(lambda *args: None)
    try:
        with pytest.raises(CheckpointExecutionError, match="hook"):
            getter()
    finally:
        handle.remove()
    assert getter() == before


def test_dynamic_rope_or_implicit_hf_checkpoint_denied():
    owner, _, getter = make_owner()
    owner.base.rope_type = "dynamic"
    with pytest.raises(CheckpointExecutionError, match="RoPE"):
        getter()
    del owner.base.rope_type
    owner.base.gradient_checkpointing = True
    with pytest.raises(CheckpointExecutionError, match="checkpoint"):
        getter()


def test_many_ephemeral_bound_methods_have_stable_fingerprint():
    owner, _, getter = make_owner()
    owner.base.children_for_test = nn.ModuleList([nn.Identity() for _ in range(40)])
    expected = getter()
    for _ in range(10):
        kept_methods = [module.forward for module in owner.base.modules()]
        assert getter() == expected
        assert kept_methods


def test_foreign_bound_method_state_not_silently_accepted():
    owner, _, getter = make_owner()
    other = nn.Linear(2, 2)
    owner.base.external_operation = other.forward
    with pytest.raises(CheckpointExecutionError, match="foreign"):
        getter()


def test_guarded_fake_forward_backward_completes_and_reacquires():
    owner, controller, getter = make_owner()
    before = getter()
    for _ in range(2):
        with controller.session() as session:
            ticket = session.begin_forward(owner, {"position_ids": torch.zeros(1)})

            def block(hidden, metadata):
                return owner.factors(hidden).square()

            output = ticket.run(0, block, torch.ones(1, 2))
            ticket.bind_output(output)
            session.backward(output.sum())
            assert session.pending_count == 0
        assert getter() == before
        assert all(p.grad is not None for p in owner.factors.parameters())


def test_global_forward_hook_denied_and_removed():
    _, _, getter = make_owner()
    before = getter()
    handle = torch.nn.modules.module.register_module_forward_hook(lambda *args: None)
    try:
        with pytest.raises(CheckpointExecutionError, match="global.*hook"):
            getter()
    finally:
        handle.remove()
    assert getter() == before


@pytest.mark.parametrize("bad", [1, False, "not callable"])
def test_invalid_getter_rejected_at_controller_construction(bad):
    owner, _, _ = make_owner()
    with pytest.raises(CheckpointExecutionError):
        CheckpointController(
            owner,
            base_getter=lambda: owner.base,
            factor_getter=lambda: owner.factors,
            layer_count=1,
            state_fingerprint_getter=bad,
        )


@pytest.mark.parametrize(
    "kind", ["string", "integer", "serialized", "modules", "depth"]
)
def test_inventory_preallocation_and_serialization_bounds(kind):
    owner, _, getter = make_owner()
    if kind == "string":
        owner.base.large_value = "x" * 65537
    elif kind == "integer":
        owner.base.large_value = 1 << 256
    elif kind == "serialized":
        owner.base.large_value = ["x" * 65536] * 300
    elif kind == "modules":
        owner.base.large_value = nn.ModuleList(
            [
                nn.ModuleList([nn.Identity() for _ in range(2048)]),
                nn.ModuleList([nn.Identity() for _ in range(2048)]),
            ]
        )
    else:
        current = owner.base
        for _ in range(65):
            child = nn.Module()
            current.child = child
            current = child
    with pytest.raises(CheckpointExecutionError, match="bound"):
        getter()


_TEST_GLOBAL_SCALE = 1.0


class GlobalDependencyFixture(nn.Module):
    def forward(self, hidden):
        return hidden * _TEST_GLOBAL_SCALE


def test_function_globals_are_explicitly_outside_this_inventory():
    global _TEST_GLOBAL_SCALE
    owner, _, getter = make_owner()
    owner.base.global_operation = GlobalDependencyFixture()
    before = getter()
    hidden = torch.ones(1)
    original = _TEST_GLOBAL_SCALE
    expected = owner.base.global_operation(hidden)
    try:
        _TEST_GLOBAL_SCALE = 2.0
        assert not torch.equal(owner.base.global_operation(hidden), expected)
        # This is an explicit limitation, NOT a complete-inventory PASS.
        assert getter() == before
    finally:
        _TEST_GLOBAL_SCALE = original
