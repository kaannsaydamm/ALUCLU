"""Synthetic 16-microbatch/one-step controls, no host learning evidence."""

from dataclasses import replace

import pytest
import torch
from test_alc_r0_checkpoint_observation import TinyWrapper

from aluclu.alc_r0.checkpoint_accumulation_step import (
    compare_accumulation_steps,
    step_accumulation,
)
from aluclu.alc_r0.checkpoint_observation import (
    ObservationError,
    compare_accumulations,
    observe_accumulation,
    observe_forward_backward,
)
from aluclu.alc_r0.checkpoint_parity_inputs import parity_input


def fixtures():
    pair = tuple(
        parity_input(
            prefix_ids=(10,),
            suffix_ids=(11,),
            safe_ids=(12,),
            vulnerable_ids=(13, 14),
            eos_token_id=0,
            common_length=64,
            label=label,
            padded=False,
        )
        for label in ("safe", "vulnerable")
    )
    return pair * 8


def test_accumulation_off_on_then_fixed_adamw_matches():
    off_wrapper, on_wrapper = TinyWrapper(True), TinyWrapper(True)
    on_wrapper.base.load_state_dict(off_wrapper.base.state_dict())
    off = observe_accumulation(off_wrapper, fixtures(), checkpoint=False)
    on = observe_accumulation(on_wrapper, fixtures(), checkpoint=True)
    compare_accumulations(off, on, exact=True)
    assert len(off.forwards) == 16
    off_step = step_accumulation(off_wrapper, off)
    on_step = step_accumulation(on_wrapper, on)
    comparison = compare_accumulation_steps(off_step, on_step, exact=True)
    assert comparison.step == 1
    assert all(float(state["step"]) == 1 for state in off_step.optimizer.state.values())
    assert all(p.grad is None for p in off_wrapper.base.parameters())


def test_loss_division_once_and_gradients_accumulate_without_reset():
    wrapper = TinyWrapper(True)
    singles = tuple(
        observe_forward_backward(wrapper, f, checkpoint=False, state="nonzero")
        for f in fixtures()[:2]
    )
    accumulated = observe_accumulation(wrapper, fixtures(), checkpoint=False)
    expected_loss = (singles[0].loss + singles[1].loss) / 2
    torch.testing.assert_close(accumulated.averaged_loss, expected_loss)
    for name, gradient in accumulated.forwards[0].gradients:
        expected = (
            dict(singles[0].gradients)[name] + dict(singles[1].gradients)[name]
        ) / 2
        torch.testing.assert_close(gradient, expected)


@pytest.mark.parametrize("checkpoint", [False, True])
def test_each_microbatch_backward_precedes_next_forward(checkpoint, monkeypatch):
    wrapper = TinyWrapper(True)
    events = []
    original = wrapper.forward
    wrapper.factors.B.register_hook(lambda g: events.append("backward") or g)

    def forward(**kwargs):
        events.append("forward")
        return original(**kwargs)

    monkeypatch.setattr(wrapper, "forward", forward)
    observe_accumulation(wrapper, fixtures(), checkpoint=checkpoint)
    assert events == ["forward", "backward"] * 16


@pytest.mark.parametrize("bad", [(), (None,) * 15, (None,) * 17, [None] * 16])
def test_bad_count_denied_before_execution(bad, monkeypatch):
    wrapper = TinyWrapper(True)
    calls = []
    monkeypatch.setattr(wrapper, "forward", lambda **kwargs: calls.append(kwargs))
    with pytest.raises(ObservationError):
        observe_accumulation(wrapper, bad, checkpoint=False)
    assert not calls


def test_invalid_last_fixture_denied_before_first_forward(monkeypatch):
    wrapper = TinyWrapper(True)
    sample = fixtures()
    bad = sample[:-1] + (replace(sample[-1], labels=()),)
    calls = []
    monkeypatch.setattr(wrapper, "forward", lambda **kwargs: calls.append(kwargs))
    with pytest.raises(ObservationError):
        observe_accumulation(wrapper, bad, checkpoint=False)
    assert not calls


def test_non_alternating_fixture_denied():
    with pytest.raises(ObservationError):
        observe_accumulation(TinyWrapper(True), (fixtures()[0],) * 16, checkpoint=False)


@pytest.mark.parametrize("checkpoint", [False, True])
def test_mid_accumulation_failure_clears_grads(checkpoint, monkeypatch):
    wrapper = TinyWrapper(True)
    original = wrapper.forward
    calls = []

    def broken(**kwargs):
        calls.append(1)
        if len(calls) == 9:
            raise RuntimeError("ninth microbatch")
        return original(**kwargs)

    monkeypatch.setattr(wrapper, "forward", broken)
    with pytest.raises(RuntimeError, match="ninth"):
        observe_accumulation(wrapper, fixtures(), checkpoint=checkpoint)
    assert all(p.grad is None for p in wrapper.factors.parameters())


def test_changed_gradients_denied_before_optimizer_step():
    wrapper = TinyWrapper(True)
    observation = observe_accumulation(wrapper, fixtures(), checkpoint=False)
    before = wrapper.factors.B.detach().clone()
    wrapper.factors.B.grad.add_(1)
    with pytest.raises(ValueError):
        step_accumulation(wrapper, observation)
    assert torch.equal(wrapper.factors.B, before)


def test_second_step_on_same_observation_rejected():
    wrapper = TinyWrapper(True)
    observation = observe_accumulation(wrapper, fixtures(), checkpoint=False)
    step_accumulation(wrapper, observation)
    with pytest.raises(ValueError):
        step_accumulation(wrapper, observation)


def test_active_checkpoint_lease_denies_step():
    wrapper = TinyWrapper(True)
    observation = observe_accumulation(wrapper, fixtures(), checkpoint=False)
    before = wrapper.factors.B.detach().clone()
    with wrapper.checkpoint_session():
        with pytest.raises(ValueError):
            step_accumulation(wrapper, observation)
    assert torch.equal(wrapper.factors.B, before)


def test_step_detects_frozen_base_mutation_and_clears_grads(monkeypatch):
    wrapper = TinyWrapper(True)
    observation = observe_accumulation(wrapper, fixtures(), checkpoint=False)
    original = torch.optim.AdamW.step

    def changed(optimizer, *args, **kwargs):
        result = original(optimizer, *args, **kwargs)
        wrapper.base.weight.data = wrapper.base.weight.data.reshape(1, 4)
        return result

    monkeypatch.setattr(torch.optim.AdamW, "step", changed)
    with pytest.raises(ObservationError):
        step_accumulation(wrapper, observation)
    assert all(p.grad is None for p in wrapper.factors.parameters())


def test_step_full_state_matches_independent_fixed_reference():
    wrapper = TinyWrapper(True)
    observation = observe_accumulation(wrapper, fixtures(), checkpoint=False)
    reference = {
        name: torch.nn.Parameter(p.detach().clone())
        for name, p in wrapper.factors.named_parameters()
    }
    for name, p in reference.items():
        p.grad = dict(observation.forwards[0].gradients)[name].clone()
    optimizer = torch.optim.AdamW(
        list(reference.values()),
        lr=3e-4,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0,
        foreach=False,
        fused=False,
    )
    torch.nn.utils.clip_grad_norm_(
        list(reference.values()), 1.0, error_if_nonfinite=True, foreach=False
    )
    optimizer.step()
    actual = step_accumulation(wrapper, observation)
    for name, parameter in actual.factors.items():
        assert torch.equal(parameter, reference[name])
        for key in ("step", "exp_avg", "exp_avg_sq"):
            assert torch.equal(
                actual.optimizer.state[parameter][key],
                optimizer.state[reference[name]][key],
            )
