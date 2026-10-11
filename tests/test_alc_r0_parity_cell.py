"""Full cell orchestration on tiny cooperating wrappers, not real-host evidence."""

import importlib

import pytest
import torch
from test_alc_r0_checkpoint_observation import TinyWrapper

from aluclu.alc_r0.checkpoint_parity_inputs import parity_input


def fixtures():
    return tuple(
        parity_input(
            prefix_ids=(10,),
            suffix_ids=(11,),
            safe_ids=(12,),
            vulnerable_ids=(13, 14),
            eos_token_id=0,
            common_length=length,
            label=label,
            padded=padded,
        )
        for length, padded in ((32, False), (64, False), (64, True))
        for label in ("safe", "vulnerable")
    )


def factory():
    base = TinyWrapper(True).base
    created = []

    def make(state, checkpoint):
        wrapper = TinyWrapper(state == "nonzero")
        if state == "nonzero":
            with torch.no_grad():
                wrapper.factors.B.copy_(
                    (torch.arange(4) % 17 - 8).float().reshape(2, 2) * 1e-4
                )
        wrapper.base = base
        created.append((state, checkpoint, wrapper))
        return wrapper

    return make, created


def runner():
    return importlib.import_module("aluclu.alc_r0.checkpoint_parity_cell")


def test_complete_cell_schedule_and_fixed_step():
    make, created = factory()
    result = runner().run_parity_cell(make, fixtures(), exact=True)
    assert len(result.cases) == 18
    assert [(c.state, c.repeat) for c in result.cases] == (
        [("zero", 0)] * 6 + [("nonzero", 0)] * 6 + [("nonzero", 1)] * 6
    )
    assert [flag for _, flag, _ in created] == [False, True] * 20
    assert len({id(w.base) for _, _, w in created}) == 1
    assert len({id(w.factors) for _, _, w in created}) == 40
    assert result.accumulation.step == 1
    assert result.parameter_count == 8
    assert result.parameter_names == ("A", "B")
    assert all(p.grad is None for p in created[0][2].base.parameters())


@pytest.mark.parametrize("bad", [None, (), [], (1,) * 6])
def test_invalid_fixture_schedule_denied_before_factory(bad):
    make, created = factory()
    with pytest.raises(ValueError):
        runner().run_parity_cell(make, bad, exact=True)
    assert not created


@pytest.mark.parametrize("bad", ["reorder", "padding", "candidate", "prompt"])
def test_incomplete_or_mismatched_schedule_denied_before_factory(bad):
    from dataclasses import replace

    schedule = list(fixtures())
    if bad == "reorder":
        schedule[0], schedule[2] = schedule[2], schedule[0]
    elif bad == "padding":
        schedule[4] = schedule[2]
    elif bad == "candidate":
        schedule[1] = schedule[0]
    else:
        schedule[1] = replace(schedule[1], input_ids=(15,) + schedule[1].input_ids[1:])
    make, created = factory()
    with pytest.raises(ValueError):
        runner().run_parity_cell(make, tuple(schedule), exact=True)
    assert not created


@pytest.mark.parametrize("bad", ["base", "wrapper", "factors", "initial"])
def test_factory_drift_denied_and_gradients_cleared(bad):
    make, created = factory()

    def broken(state, checkpoint):
        wrapper = make(state, checkpoint)
        if checkpoint:
            off = created[-2][2]
            if bad == "base":
                wrapper.base = TinyWrapper().base
            elif bad == "wrapper":
                return off
            elif bad == "factors":
                wrapper.factors = off.factors
            else:
                wrapper.factors.A.data.add_(1)
        return wrapper

    with pytest.raises(ValueError):
        runner().run_parity_cell(broken, fixtures(), exact=True)
    assert len(created) == 2
    assert all(p.grad is None for _, _, w in created for p in w.factors.parameters())


def test_repeat_initial_state_drift_is_not_hidden_by_pair_parity():
    make, created = factory()

    def changed(state, checkpoint):
        wrapper = make(state, checkpoint)
        if len(created) > 24:
            wrapper.factors.A.data.add_(1)
        return wrapper

    with pytest.raises(ValueError):
        runner().run_parity_cell(changed, fixtures(), exact=True)
    assert len(created) < 40


def test_cpu_cannot_select_tolerant_mode():
    make, _ = factory()
    with pytest.raises(ValueError):
        runner().run_parity_cell(make, fixtures(), exact=False)


@pytest.mark.parametrize("bad", ["storage", "parameter"])
@pytest.mark.parametrize("phase", ["single", "pending"])
def test_fresh_modules_cannot_share_live_factor_storage(bad, phase):
    make, created = factory()

    def aliased(state, checkpoint):
        wrapper = make(state, checkpoint)
        if checkpoint and len(created) == (2 if phase == "single" else 38):
            off = created[-2][2]
            for name in ("A", "B"):
                source = getattr(off.factors, name)
                source.grad = None
                setattr(
                    wrapper.factors,
                    name,
                    source
                    if bad == "parameter"
                    else torch.nn.Parameter(source.detach()),
                )
        return wrapper

    with pytest.raises(ValueError):
        runner().run_parity_cell(aliased, fixtures(), exact=True)
    assert len(created) == (2 if phase == "single" else 38)


def test_nonzero_state_must_keep_zero_state_A():
    make, created = factory()

    def changed(state, checkpoint):
        wrapper = make(state, checkpoint)
        if state == "nonzero":
            wrapper.factors.A.data.add_(1)
        return wrapper

    with pytest.raises(ValueError):
        runner().run_parity_cell(changed, fixtures(), exact=True)
    assert len(created) == 13


def test_nonzero_B_requires_prescribed_pattern():
    make, _ = factory()

    def wrong_pattern(state, checkpoint):
        wrapper = make(state, checkpoint)
        if state == "nonzero":
            wrapper.factors.B.data.fill_(0.01)
        return wrapper

    with pytest.raises(ValueError, match="pattern"):
        runner().run_parity_cell(wrong_pattern, fixtures(), exact=True)


@pytest.mark.parametrize("mutation", ["order", "repeat"])
def test_matching_pairs_cannot_hide_order_or_repeat_drift(mutation, monkeypatch):
    from dataclasses import replace

    module = runner()
    original = module.observe_forward_backward
    calls = []
    if mutation == "order":
        compare = module.compare_observations
        # Isolate the order guard using the unchanged tolerant comparator on
        # CPU fixtures. No production mode/threshold or GPU claim is changed.
        monkeypatch.setattr(
            module,
            "compare_observations",
            lambda left, right, **kwargs: compare(left, right, exact=False),
        )

    def changed(*args, **kwargs):
        observation = original(*args, **kwargs)
        calls.append(1)
        if mutation == "order":
            # Individually within fixed GPU scalar tolerance; order still flips.
            score = (-1.0, -1.0 + 5e-7, -1.0 + 5e-7, -1.0)[len(calls) - 1]
            return replace(observation, candidate_score=score)
        if len(calls) > 24:
            return replace(observation, logits=observation.logits + 1e-6)
        return observation

    monkeypatch.setattr(module, "observe_forward_backward", changed)
    make, created = factory()
    with pytest.raises(ValueError):
        module.run_parity_cell(make, fixtures(), exact=True)
    assert len(created) == (4 if mutation == "order" else 26)
    assert all(p.grad is None for _, _, w in created for p in w.factors.parameters())


def test_interruption_clears_owned_gradients_without_retry(monkeypatch):
    module = runner()
    original = module.observe_forward_backward

    def interrupted(*args, **kwargs):
        original(*args, **kwargs)
        raise KeyboardInterrupt("owned synthetic attempt interrupted")

    monkeypatch.setattr(module, "observe_forward_backward", interrupted)
    make, created = factory()
    with pytest.raises(KeyboardInterrupt):
        module.run_parity_cell(make, fixtures(), exact=True)
    assert len(created) == 1
    assert all(p.grad is None for p in created[0][2].factors.parameters())
