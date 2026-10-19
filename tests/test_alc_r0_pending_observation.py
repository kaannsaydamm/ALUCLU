"""Two pending synthetic graphs, not actual-host/learning evidence."""

from dataclasses import replace

import pytest
import torch
from test_alc_r0_checkpoint_observation import TinyWrapper

from aluclu.alc_r0.checkpoint_observation import (
    ObservationError,
    compare_pending_observations,
    observe_forward_backward,
    observe_pending_pair,
)
from aluclu.alc_r0.checkpoint_parity_inputs import parity_input


def pair():
    return tuple(
        parity_input(
            prefix_ids=(10,),
            suffix_ids=(11,),
            safe_ids=(12,),
            vulnerable_ids=(13, 14),
            eos_token_id=0,
            common_length=32,
            label=label,
            padded=False,
        )
        for label in ("safe", "vulnerable")
    )


@pytest.mark.parametrize("reverse", [False, True])
def test_pending_pair_matches_summed_single_gradients_and_off_on(reverse):
    wrapper = TinyWrapper(True)
    fixtures = pair()[::-1] if reverse else pair()
    singles = tuple(
        observe_forward_backward(wrapper, f, checkpoint=False, state="nonzero")
        for f in fixtures
    )
    off = observe_pending_pair(wrapper, fixtures, checkpoint=False)
    on = observe_pending_pair(wrapper, fixtures, checkpoint=True)
    compare_pending_observations(off, on, exact=True)
    assert len(on.forwards) == 2
    assert torch.equal(on.summed_loss, sum(item.loss for item in singles))
    for name, gradient in on.forwards[0].gradients:
        torch.testing.assert_close(
            gradient, sum(dict(item.gradients)[name] for item in singles)
        )
    assert all(p.grad is None for p in wrapper.base.parameters())


@pytest.mark.parametrize("checkpoint", [False, True])
def test_both_forwards_precede_single_backward(checkpoint, monkeypatch):
    wrapper = TinyWrapper(True)
    events = []
    original = wrapper.forward
    wrapper.factors.B.register_hook(lambda g: events.append("backward") or g)

    def forward(**kwargs):
        events.append("forward")
        return original(**kwargs)

    monkeypatch.setattr(wrapper, "forward", forward)
    observe_pending_pair(wrapper, pair(), checkpoint=checkpoint)
    assert events == ["forward", "forward", "backward"]


@pytest.mark.parametrize("bad", [(), (None,), (None, None, None), [None, None]])
def test_invalid_pair_count_denied_before_execution(bad, monkeypatch):
    wrapper = TinyWrapper(True)
    calls = []
    monkeypatch.setattr(wrapper, "forward", lambda **kwargs: calls.append(kwargs))
    with pytest.raises(ObservationError):
        observe_pending_pair(wrapper, bad, checkpoint=False)
    assert not calls


def test_invalid_second_fixture_denied_before_first_forward(monkeypatch):
    wrapper = TinyWrapper(True)
    fixtures = pair()
    calls = []
    monkeypatch.setattr(wrapper, "forward", lambda **kwargs: calls.append(kwargs))
    with pytest.raises(ObservationError):
        observe_pending_pair(
            wrapper, (fixtures[0], replace(fixtures[1], labels=())), checkpoint=False
        )
    assert not calls


@pytest.mark.parametrize("checkpoint", [False, True])
def test_second_forward_failure_clears_original_gradients(checkpoint, monkeypatch):
    wrapper = TinyWrapper(True)
    original = wrapper.forward
    calls = []

    def broken(**kwargs):
        calls.append(1)
        if len(calls) == 2:
            wrapper.factors.B.grad = torch.ones_like(wrapper.factors.B)
            raise RuntimeError("second forward")
        return original(**kwargs)

    monkeypatch.setattr(wrapper, "forward", broken)
    with pytest.raises(RuntimeError, match="second forward"):
        observe_pending_pair(wrapper, pair(), checkpoint=checkpoint)
    assert all(p.grad is None for p in wrapper.factors.parameters())


def test_summed_loss_mismatch_denied():
    wrapper = TinyWrapper(True)
    off = observe_pending_pair(wrapper, pair(), checkpoint=False)
    on = observe_pending_pair(wrapper, pair(), checkpoint=True)
    with pytest.raises(ValueError):
        compare_pending_observations(
            off, replace(on, summed_loss=on.summed_loss + 1), exact=True
        )


def test_duplicate_candidate_pair_denied():
    wrapper = TinyWrapper(True)
    with pytest.raises(ObservationError):
        observe_pending_pair(wrapper, (pair()[0], pair()[0]), checkpoint=False)


def test_omitted_second_graph_rejected_and_gradients_cleared(monkeypatch):
    wrapper = TinyWrapper(True)
    original = wrapper.forward
    results = []

    def omit(**kwargs):
        results.append(original(**kwargs))
        return results[0]

    monkeypatch.setattr(wrapper, "forward", omit)
    with pytest.raises(ValueError):
        observe_pending_pair(wrapper, pair(), checkpoint=True)
    assert all(p.grad is None for p in wrapper.factors.parameters())


@pytest.mark.parametrize("checkpoint", [False, True])
def test_nonfinite_second_loss_rejected(checkpoint, monkeypatch):
    wrapper = TinyWrapper(True)
    original = wrapper.forward
    calls = []

    def invalid(**kwargs):
        result = original(**kwargs)
        calls.append(1)
        if len(calls) == 2:
            result.loss = result.loss * float("nan")
        return result

    monkeypatch.setattr(wrapper, "forward", invalid)
    with pytest.raises(ValueError):
        observe_pending_pair(wrapper, pair(), checkpoint=checkpoint)
    assert all(p.grad is None for p in wrapper.factors.parameters())


def test_zero_factor_state_not_admitted_for_pending_fixture():
    with pytest.raises(ObservationError):
        observe_pending_pair(TinyWrapper(), pair(), checkpoint=False)
