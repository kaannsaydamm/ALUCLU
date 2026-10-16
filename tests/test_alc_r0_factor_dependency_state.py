"""CPU factor-global drift fixtures; no host assets, corpus or optimizer."""

from types import ModuleType, SimpleNamespace

import pytest
import torch
from torch import nn

from aluclu.alc_r0 import matched_lora, research_capsule
from aluclu.alc_r0.checkpoint_execution import (
    CheckpointController,
    CheckpointExecutionError,
)
from aluclu.alc_r0.checkpoint_state import computational_state_fingerprint


def make_owner(arm):
    owner = nn.Module()
    owner.base = nn.Linear(576, 576, bias=False).requires_grad_(False).eval()
    cls = (
        research_capsule.ResearchCapsuleV0
        if arm == "capsule"
        else matched_lora.MatchedQProjLoRA
    )
    owner.factors = cls(ports=(14,), rank=4, seed=20260916)
    with torch.no_grad():
        owner.factors.factors["14"].B.fill_(0.01)
    if arm == "capsule":
        operation = owner.factors.bind_port(14)
    else:
        operation = owner.factors.bind_q_projection(
            14, SimpleNamespace(q_proj=owner.base)
        )

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
    return owner, controller, getter, operation


def mutate_dependency(monkeypatch, arm, dependency):
    namespace = research_capsule if arm == "capsule" else matched_lora
    if dependency == "epsilon":
        monkeypatch.setattr(namespace, "NORMALIZATION_EPSILON", 1.0)
    elif dependency == "width":
        monkeypatch.setattr(namespace, "CANONICAL_WIDTH", 577)
    else:
        name = "F" if dependency == "linear" else "torch"
        original = getattr(namespace, name)
        replacement = ModuleType(original.__name__)
        replacement.__dict__.update(vars(original))
        if dependency == "linear":
            linear = original.linear

            def changed_linear(*args, **kwargs):
                return linear(*args, **kwargs) * 2

            replacement.linear = changed_linear
        else:
            autocast = original.autocast

            def changed_autocast(*args, **kwargs):
                return autocast(*args, **kwargs)

            replacement.autocast = changed_autocast
        monkeypatch.setattr(namespace, name, replacement)


CASES = [("capsule", name) for name in ("epsilon", "width", "linear", "autocast")]
CASES += [("lora", name) for name in ("linear", "autocast")]


@pytest.mark.parametrize("arm,dependency", CASES)
@pytest.mark.parametrize("phase", ["preparation", "replay"])
def test_factor_dependency_drift_denied_before_side_effect(
    arm, dependency, phase, monkeypatch
):
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
            mutate_dependency(monkeypatch, arm, dependency)
            for parameter in owner.factors.parameters():
                parameter.grad = torch.ones_like(parameter)
            if phase == "preparation":
                session.begin_forward(owner, {"position_ids": torch.zeros(1)})
                calls.append(1)
            else:
                session.backward(output.square().sum())
    assert calls == ([] if phase == "preparation" else [1])
    assert controller._active is None
    assert all(parameter.grad is None for parameter in owner.factors.parameters())


def test_epsilon_counterexample_changes_bound_math_and_fingerprint(monkeypatch):
    _, _, getter, operation = make_owner("capsule")
    hidden = torch.linspace(-1, 1, 576).reshape(1, 1, 576)
    before = getter()
    expected = operation(hidden)
    mutate_dependency(monkeypatch, "capsule", "epsilon")
    assert not torch.equal(operation(hidden), expected)
    assert getter() != before


@pytest.mark.parametrize("arm", ["capsule", "lora"])
def test_unmodified_factor_dependencies_allow_complete_session(arm):
    owner, controller, getter, operation = make_owner(arm)
    before = getter()
    with controller.session() as session:
        ticket = session.begin_forward(owner, {"position_ids": torch.zeros(1)})
        output = ticket.run(
            0,
            lambda hidden, metadata: operation(hidden),
            torch.linspace(-1, 1, 576).reshape(1, 1, 576),
        )
        ticket.bind_output(output)
        session.backward(output.square().sum())
    assert getter() == before
    assert controller._active is None
    assert all(parameter.grad is None for parameter in owner.base.parameters())
    assert all(
        parameter.grad is not None and torch.isfinite(parameter.grad).all()
        for parameter in owner.factors.parameters()
    )


@pytest.mark.parametrize("arm", ["capsule", "lora"])
@pytest.mark.parametrize("dependency", ["F", "torch", "linear", "autocast", "factory"])
def test_unsupported_factor_binding_rejected(arm, dependency, monkeypatch):
    owner, _, getter, _ = make_owner(arm)
    namespace = research_capsule if arm == "capsule" else matched_lora
    if dependency in {"F", "torch"}:
        monkeypatch.setattr(namespace, dependency, object())
    elif dependency == "factory":
        name = "bind_port" if arm == "capsule" else "bind_q_projection"
        monkeypatch.setattr(owner.factors, name, lambda *args: None)
    else:
        name = "F" if dependency == "linear" else "torch"
        original = getattr(namespace, name)
        replacement = ModuleType(original.__name__)
        replacement.__dict__.update(vars(original))
        setattr(replacement, dependency, object())
        monkeypatch.setattr(namespace, name, replacement)
    with pytest.raises(CheckpointExecutionError):
        getter()


@pytest.mark.parametrize(
    "name,value",
    [
        ("NORMALIZATION_EPSILON", True),
        ("NORMALIZATION_EPSILON", 1),
        ("NORMALIZATION_EPSILON", float("nan")),
        ("CANONICAL_WIDTH", True),
    ],
)
def test_unsupported_factor_scalar_rejected(name, value, monkeypatch):
    _, _, getter, _ = make_owner("capsule")
    monkeypatch.setattr(research_capsule, name, value)
    with pytest.raises(CheckpointExecutionError):
        getter()
