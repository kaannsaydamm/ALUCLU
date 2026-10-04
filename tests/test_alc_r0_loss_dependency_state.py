"""Pinned loss-dispatch fixtures, no host weights/corpus/optimizer/model forward."""

from types import ModuleType

import pytest
import torch
from torch import nn
from transformers import LlamaConfig, PreTrainedModel
from transformers.loss import loss_utils
from transformers.models.llama.modeling_llama import LlamaForCausalLM

from aluclu.alc_r0.checkpoint_execution import (
    CheckpointController,
    CheckpointExecutionError,
)
from aluclu.alc_r0.checkpoint_state import computational_state_fingerprint


def make_owner():
    class LossDispatchFixture(LlamaForCausalLM):
        def __init__(self):
            nn.Module.__init__(self)
            self.weight = nn.Parameter(torch.ones(2, 2), requires_grad=False)
            self.loss_type = "ForCausalLM"
            self.config = LlamaConfig(
                vocab_size=4, hidden_size=4, num_attention_heads=2
            )

        def forward(self, hidden):
            raise AssertionError("model forward is outside these fixtures")

    owner = nn.Module()
    owner.base = LossDispatchFixture().eval()
    owner.factors = nn.Linear(2, 4, bias=False)

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


def replace_dependency(owner, monkeypatch, dependency):
    if dependency == "property":
        monkeypatch.setattr(
            type(owner.base),
            "loss_function",
            property(lambda self: loss_utils.ForCausalLMLoss),
        )
    elif dependency == "mapping":
        mapping = PreTrainedModel.loss_function.fget.__globals__["LOSS_MAPPING"]
        original = mapping["ForCausalLM"]
        monkeypatch.setitem(
            mapping,
            "ForCausalLM",
            lambda *args, **kwargs: original(*args, **kwargs) * 2,
        )
    elif dependency == "fixed":
        original = loss_utils.fixed_cross_entropy
        monkeypatch.setattr(
            loss_utils,
            "fixed_cross_entropy",
            lambda *args, **kwargs: original(*args, **kwargs) * 2,
        )
    else:
        original_nn = loss_utils.nn
        replacement_nn = ModuleType(original_nn.__name__)
        replacement_nn.__dict__.update(vars(original_nn))
        original_functional = original_nn.functional
        replacement_functional = ModuleType(original_functional.__name__)
        replacement_functional.__dict__.update(vars(original_functional))
        original = getattr(original_functional, dependency)
        replacement_functional.__dict__[dependency] = lambda *args, **kwargs: original(
            *args, **kwargs
        )
        replacement_nn.functional = replacement_functional
        monkeypatch.setattr(loss_utils, "nn", replacement_nn)


@pytest.mark.parametrize(
    "dependency", ["property", "mapping", "fixed", "cross_entropy", "pad"]
)
@pytest.mark.parametrize("phase", ["preparation", "replay"])
def test_loss_dependency_drift_denied_before_side_effect(
    dependency, phase, monkeypatch
):
    owner, controller, _ = make_owner()
    calls = []
    with pytest.raises(CheckpointExecutionError):
        with controller.session() as session:
            if phase == "replay":
                ticket = session.begin_forward(owner, {"position_ids": torch.zeros(1)})

                def block(hidden, metadata):
                    calls.append(1)
                    return owner.factors(hidden)

                output = ticket.run(0, block, torch.ones(1, 2, 2))
                ticket.bind_output(output)
                loss = owner.base.loss_function(
                    logits=output, labels=torch.tensor([[0, 1]]), vocab_size=4
                )
            replace_dependency(owner, monkeypatch, dependency)
            for parameter in owner.factors.parameters():
                parameter.grad = torch.ones_like(parameter)
            if phase == "preparation":
                session.begin_forward(owner, {"position_ids": torch.zeros(1)})
                calls.append(1)
            else:
                session.backward(loss)
    assert calls == ([] if phase == "preparation" else [1])
    assert controller._active is None
    assert all(parameter.grad is None for parameter in owner.factors.parameters())


def test_loss_helper_counterexample_changes_numeric_loss_and_is_detected(monkeypatch):
    owner, _, getter = make_owner()
    logits, labels = torch.ones(1, 2, 4), torch.tensor([[0, 1]])
    before = getter()
    expected = owner.base.loss_function(logits=logits, labels=labels, vocab_size=4)
    replace_dependency(owner, monkeypatch, "fixed")
    actual = owner.base.loss_function(logits=logits, labels=labels, vocab_size=4)
    assert torch.equal(actual, expected * 2)
    try:
        changed = getter()
    except CheckpointExecutionError:
        return
    assert changed != before


@pytest.mark.parametrize("explicit_override", [False, True])
def test_unmodified_causal_loss_allows_complete_gradient_session(explicit_override):
    owner, controller, getter = make_owner()
    if explicit_override:
        owner.base.loss_function = loss_utils.ForCausalLMLoss
    before = getter()
    with controller.session() as session:
        ticket = session.begin_forward(owner, {"position_ids": torch.zeros(1)})
        output = ticket.run(
            0, lambda hidden, metadata: owner.factors(hidden), torch.ones(1, 2, 2)
        )
        ticket.bind_output(output)
        loss = owner.base.loss_function(
            logits=output, labels=torch.tensor([[0, 1]]), vocab_size=4
        )
        session.backward(loss)
    assert getter() == before
    assert controller._active is None
    assert all(parameter.grad is None for parameter in owner.base.parameters())
    assert all(
        parameter.grad is not None and torch.isfinite(parameter.grad).all()
        for parameter in owner.factors.parameters()
    )


@pytest.mark.parametrize("loss_type", [None, False, "ForMaskedLM", "unregistered"])
def test_unreviewed_loss_type_does_not_use_implicit_fallback(loss_type):
    owner, _, getter = make_owner()
    owner.base.loss_type = loss_type
    with pytest.raises(CheckpointExecutionError, match="loss route"):
        getter()


@pytest.mark.parametrize("kind", ["missing", "type", "bound"])
def test_unsupported_loss_registry_rejected(kind, monkeypatch):
    _, _, getter = make_owner()
    namespace = PreTrainedModel.loss_function.fget.__globals__
    mapping = namespace["LOSS_MAPPING"]
    if kind == "missing":
        monkeypatch.delitem(mapping, "ForCausalLM")
    elif kind == "type":
        monkeypatch.setitem(namespace, "LOSS_MAPPING", None)
    else:
        monkeypatch.setitem(
            namespace, "LOSS_MAPPING", {str(index): None for index in range(2049)}
        )
    with pytest.raises(CheckpointExecutionError):
        getter()


@pytest.mark.parametrize("override", [None, lambda *args, **kwargs: None])
def test_unreviewed_loss_override_rejected(override):
    owner, _, getter = make_owner()
    owner.base.loss_function = override
    with pytest.raises(CheckpointExecutionError, match="selected causal loss"):
        getter()


@pytest.mark.parametrize(
    "mutation", ["loss_defaults", "helper_defaults", "property_code"]
)
def test_same_loss_function_mutation_changes_fingerprint(mutation, monkeypatch):
    _, _, getter = make_owner()
    before = getter()
    if mutation == "loss_defaults":
        monkeypatch.setattr(
            loss_utils.ForCausalLMLoss, "__defaults__", (None, -101, None)
        )
    elif mutation == "helper_defaults":
        monkeypatch.setattr(
            loss_utils.fixed_cross_entropy, "__defaults__", (None, -101)
        )
    else:

        def altered(self):
            return None

        monkeypatch.setattr(
            PreTrainedModel.loss_function.fget, "__code__", altered.__code__
        )
    assert getter() != before
