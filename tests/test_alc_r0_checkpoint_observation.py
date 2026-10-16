"""Tiny forward/backward harness tests, never real-host parity evidence."""

from dataclasses import replace
from types import SimpleNamespace

import pytest
import torch
from torch import nn

from aluclu.alc_r0.checkpoint_execution import CheckpointController
from aluclu.alc_r0.checkpoint_observation import (
    ObservationError,
    compare_observations,
    observe_forward_backward,
)
from aluclu.alc_r0.checkpoint_parity_inputs import parity_input
from aluclu.alc_r0.checkpoint_state import computational_state_fingerprint


class TinyWrapper(nn.Module):
    def __init__(self, nonzero=False):
        super().__init__()
        self.base = nn.Linear(2, 2).requires_grad_(False)
        self.base.config = SimpleNamespace(vocab_size=128)
        self.factors = nn.Module()
        self.factors.A = nn.Parameter(torch.ones(2, 2))
        self.factors.B = nn.Parameter(torch.full((2, 2), 0.01 if nonzero else 0.0))
        self.train()
        self.base.eval()
        self.controller = CheckpointController(
            self,
            base_getter=lambda: self.base,
            factor_getter=lambda: self.factors,
            layer_count=1,
            state_fingerprint_getter=lambda: computational_state_fingerprint(
                {"factors": self.factors}
            ),
        )

    def _checkpoint_factors(self):
        return self.factors

    def checkpoint_session(self):
        return self.controller.session()

    def forward(
        self,
        *,
        input_ids,
        labels,
        attention_mask,
        position_ids,
        use_cache,
        checkpoint_session=None,
    ):
        assert use_cache is False
        hidden = torch.ones((*input_ids.shape, 2))

        def block(value, metadata):
            return value @ self.factors.A.T @ self.factors.B.T

        if checkpoint_session is not None:
            ticket = checkpoint_session.begin_forward(self, {"labels": labels})
            hidden = ticket.run(0, block, hidden)
        else:
            hidden = block(hidden, None)
        logits = hidden.sum(-1, keepdim=True).expand(*input_ids.shape, 128)
        if checkpoint_session is not None:
            ticket.bind_output(logits)
        loss = logits[labels != -100].sum()
        return SimpleNamespace(loss=loss, logits=logits)


def fixture(padded=False):
    return parity_input(
        prefix_ids=(10,),
        suffix_ids=(11,),
        safe_ids=(12,),
        vulnerable_ids=(13, 14),
        eos_token_id=0,
        common_length=64 if padded else 32,
        label="safe",
        padded=padded,
    )


@pytest.mark.parametrize("nonzero", [False, True])
@pytest.mark.parametrize("padded", [False, True])
def test_off_on_complete_observation_exact_and_base_frozen(nonzero, padded):
    wrapper = TinyWrapper(nonzero)
    state = "nonzero" if nonzero else "zero"
    off = observe_forward_backward(
        wrapper, fixture(padded), checkpoint=False, state=state
    )
    on = observe_forward_backward(
        wrapper, fixture(padded), checkpoint=True, state=state
    )
    compare_observations(off, on, exact=True)
    assert set(dict(on.gradients)) == {"A", "B"}
    assert all(parameter.grad is None for parameter in wrapper.base.parameters())
    assert off.base_digest == on.base_digest
    assert all(
        not value.requires_grad and value.device.type == "cpu"
        for _, value in on.gradients
    )
    wrapper.factors.B.grad.zero_()
    assert torch.count_nonzero(dict(on.gradients)["B"]) > 0


def test_wrong_expected_factor_state_denied_before_forward():
    wrapper = TinyWrapper()
    with pytest.raises(ObservationError):
        observe_forward_backward(wrapper, fixture(), checkpoint=False, state="nonzero")


@pytest.mark.parametrize("field", ["loss", "logits", "gradients"])
def test_observation_mismatch_denied(field):
    wrapper = TinyWrapper(True)
    off = observe_forward_backward(
        wrapper, fixture(), checkpoint=False, state="nonzero"
    )
    on = observe_forward_backward(wrapper, fixture(), checkpoint=True, state="nonzero")
    if field == "gradients":
        dict(on.gradients)["B"].neg_()
    else:
        getattr(on, field).add_(1)
    with pytest.raises(ValueError):
        compare_observations(off, on, exact=True)


def test_backward_failure_clears_partial_gradients(monkeypatch):
    wrapper = TinyWrapper(True)
    original = wrapper.forward

    def broken(**kwargs):
        result = original(**kwargs)
        result.loss = result.loss.detach()
        wrapper.factors.A.grad = torch.ones_like(wrapper.factors.A)
        return result

    monkeypatch.setattr(wrapper, "forward", broken)
    with pytest.raises(ValueError):
        observe_forward_backward(wrapper, fixture(), checkpoint=False, state="nonzero")
    assert all(p.grad is None for p in wrapper.factors.parameters())


@pytest.mark.parametrize("mutation", ["base", "factors", "mode"])
def test_live_binding_replacement_during_forward_rejected(mutation, monkeypatch):
    wrapper = TinyWrapper(True)
    original = wrapper.forward

    def changed(**kwargs):
        result = original(**kwargs)
        if mutation == "base":
            new_base = nn.Linear(2, 2).requires_grad_(False).eval()
            new_base.load_state_dict(wrapper.base.state_dict())
            new_base.config = wrapper.base.config
            wrapper.base = new_base
        elif mutation == "factors":
            new_factors = nn.Module()
            new_factors.A = nn.Parameter(wrapper.factors.A.detach().clone())
            new_factors.B = nn.Parameter(wrapper.factors.B.detach().clone())
            wrapper.factors = new_factors
        else:
            wrapper.training = False
        return result

    monkeypatch.setattr(wrapper, "forward", changed)
    with pytest.raises(ObservationError):
        observe_forward_backward(wrapper, fixture(), checkpoint=False, state="nonzero")


def test_duplicate_observation_gradient_names_rejected():
    wrapper = TinyWrapper()
    off = observe_forward_backward(wrapper, fixture(), checkpoint=False, state="zero")
    on = observe_forward_backward(wrapper, fixture(), checkpoint=True, state="zero")
    duplicate = replace(
        on, gradients=on.gradients + (("A", dict(on.gradients)["A"].clone()),)
    )
    with pytest.raises(ObservationError):
        compare_observations(off, duplicate, exact=True)


@pytest.mark.parametrize(
    "mutation", ["base_parameter", "factor_parameter", "buffer", "input", "gradient"]
)
def test_state_and_input_mutations_rejected_and_gradients_cleared(
    mutation, monkeypatch
):
    wrapper = TinyWrapper(True)
    wrapper.base.register_buffer("counter", torch.zeros(1))
    original = wrapper.forward
    original_parameters = tuple(wrapper.factors.parameters())

    def changed(**kwargs):
        result = original(**kwargs)
        if mutation == "base_parameter":
            wrapper.base.weight = nn.Parameter(
                wrapper.base.weight.detach().clone(), requires_grad=False
            )
        elif mutation == "factor_parameter":
            wrapper.factors.B = nn.Parameter(wrapper.factors.B.detach().clone())
        elif mutation == "buffer":
            wrapper.base.counter.add_(1)
        elif mutation == "input":
            kwargs["input_ids"].add_(1)
        else:
            wrapper.factors.B.register_hook(lambda gradient: gradient * float("nan"))
        return result

    monkeypatch.setattr(wrapper, "forward", changed)
    with pytest.raises(ObservationError):
        observe_forward_backward(wrapper, fixture(), checkpoint=False, state="nonzero")
    assert all(parameter.grad is None for parameter in original_parameters)


def test_aliased_factor_parameter_rejected_before_forward():
    wrapper = TinyWrapper(True)
    wrapper.factors.alias = nn.Module()
    wrapper.factors.alias.A = wrapper.factors.A
    with pytest.raises(ObservationError):
        observe_forward_backward(wrapper, fixture(), checkpoint=False, state="nonzero")


@pytest.mark.parametrize("target", ["parameter", "buffer"])
def test_base_shape_drift_with_identical_bytes_rejected(target, monkeypatch):
    wrapper = TinyWrapper(True)
    wrapper.base.register_buffer("counter", torch.zeros(2, 2))
    original = wrapper.forward

    def changed(**kwargs):
        result = original(**kwargs)
        tensor = wrapper.base.weight if target == "parameter" else wrapper.base.counter
        tensor.data = tensor.data.reshape(1, 4)
        return result

    monkeypatch.setattr(wrapper, "forward", changed)
    with pytest.raises(ObservationError):
        observe_forward_backward(wrapper, fixture(), checkpoint=False, state="nonzero")
    assert all(parameter.grad is None for parameter in wrapper.factors.parameters())


@pytest.mark.parametrize(
    "field", ["labels", "attention_mask", "position_ids", "input_ids"]
)
def test_malformed_fixture_rejected_before_forward(field, monkeypatch):
    wrapper = TinyWrapper(True)
    sample = fixture()
    invalid = replace(sample, **{field: tuple(99999 for _ in getattr(sample, field))})
    called = []
    monkeypatch.setattr(wrapper, "forward", lambda **kwargs: called.append(kwargs))
    with pytest.raises(ObservationError):
        observe_forward_backward(wrapper, invalid, checkpoint=False, state="nonzero")
    assert called == []
