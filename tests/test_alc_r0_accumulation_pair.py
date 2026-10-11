"""Cooperating factory/phase integration, not real-host or learning evidence."""

import pytest
import torch
from test_alc_r0_accumulation_observation import fixtures
from test_alc_r0_checkpoint_observation import TinyWrapper

import aluclu.alc_r0.checkpoint_accumulation_pair as pair_module
from aluclu.alc_r0.checkpoint_accumulation_pair import run_accumulation_pair


def factory():
    base = TinyWrapper(True).base
    created = []

    def make(checkpoint):
        wrapper = TinyWrapper(True)
        wrapper.base = base
        created.append((checkpoint, wrapper))
        return wrapper

    return make, created


def test_shared_base_independent_factors_full_pair():
    make, created = factory()
    result = run_accumulation_pair(make, fixtures(), exact=True)
    assert [flag for flag, _ in created] == [False, True]
    assert created[0][1].base is created[1][1].base
    assert result.comparison.step == 1
    assert result.reference.optimizer is not result.actual.optimizer
    assert all(p.grad is None for p in created[0][1].base.parameters())


def test_factor_registration_order_is_not_state_drift():
    make, _ = factory()

    def reversed_roster(checkpoint):
        wrapper = make(checkpoint)
        a, b = wrapper.factors.A, wrapper.factors.B
        del wrapper.factors.A
        del wrapper.factors.B
        wrapper.factors.B = b
        wrapper.factors.A = a
        return wrapper

    result = run_accumulation_pair(reversed_roster, fixtures(), exact=True)
    assert result.comparison.step == 1


def test_actual_phase_order_compare_before_both_steps(monkeypatch):
    make, _ = factory()
    events = []
    for name in (
        "observe_accumulation",
        "compare_accumulations",
        "step_accumulation",
        "compare_accumulation_steps",
    ):
        original = getattr(pair_module, name)

        def recorded(*args, _original=original, _name=name, **kwargs):
            events.append(_name)
            return _original(*args, **kwargs)

        monkeypatch.setattr(pair_module, name, recorded)
    run_accumulation_pair(make, fixtures(), exact=True)
    assert events == [
        "observe_accumulation",
        "observe_accumulation",
        "compare_accumulations",
        "step_accumulation",
        "step_accumulation",
        "compare_accumulation_steps",
    ]


@pytest.mark.parametrize("bad", ["base", "wrapper", "factors", "initial_state"])
def test_bad_factory_denied_before_on_forward(bad, monkeypatch):
    make, created = factory()
    on_calls = []

    def broken(checkpoint):
        if not checkpoint:
            return make(False)
        off = created[0][1]
        on = make(True)
        if bad == "base":
            on.base = TinyWrapper(True).base
        elif bad == "wrapper":
            on = off
        elif bad == "factors":
            on.factors = off.factors
        else:
            with torch.no_grad():
                on.factors.B.add_(0.01)
        original = on.forward

        def counted(**kwargs):
            on_calls.append(1)
            return original(**kwargs)

        monkeypatch.setattr(on, "forward", counted)
        return on

    with pytest.raises(ValueError):
        run_accumulation_pair(broken, fixtures(), exact=True)
    assert not on_calls
    assert all(
        p.grad is None for _, wrapper in created for p in wrapper.factors.parameters()
    )


def test_parity_failure_never_steps_either_arm(monkeypatch):
    make, created = factory()
    steps = []
    original_step = pair_module.step_accumulation

    def recorded(*args, **kwargs):
        steps.append(1)
        return original_step(*args, **kwargs)

    monkeypatch.setattr(pair_module, "step_accumulation", recorded)

    def drift(checkpoint):
        wrapper = make(checkpoint)
        if checkpoint:
            original = wrapper.forward

            def changed(**kwargs):
                result = original(**kwargs)
                result.loss = result.loss * 2
                return result

            monkeypatch.setattr(wrapper, "forward", changed)
        return wrapper

    with pytest.raises(ValueError):
        run_accumulation_pair(drift, fixtures(), exact=True)
    assert not steps
    assert all(
        p.grad is None for _, wrapper in created for p in wrapper.factors.parameters()
    )


def test_on_factory_failure_clears_off_gradients():
    make, created = factory()
    primary = RuntimeError("factory failed")

    def broken(checkpoint):
        if checkpoint:
            raise primary
        return make(False)

    with pytest.raises(pair_module.AccumulationError, match="factory failed") as caught:
        run_accumulation_pair(broken, fixtures(), exact=True)
    assert caught.value.__cause__ is primary
    assert caught.value.failure.phase == "on_factory"
    assert caught.value.failure.completed_pair == 3
    assert caught.value.failure.off.forwards == 16
    assert caught.value.failure.off.backwards == 16
    assert caught.value.failure.on.forwards == 0
    assert len(created) == 1
    assert all(p.grad is None for p in created[0][1].factors.parameters())


def test_cross_arm_gradient_alias_denied_before_either_step(monkeypatch):
    make, created = factory()
    original = pair_module.observe_accumulation
    steps = []

    def alias(wrapper, *args, **kwargs):
        observation = original(wrapper, *args, **kwargs)
        if kwargs["checkpoint"]:
            wrapper.factors.B.grad = created[0][1].factors.B.grad
        return observation

    monkeypatch.setattr(pair_module, "observe_accumulation", alias)
    monkeypatch.setattr(pair_module, "step_accumulation", lambda *args: steps.append(1))
    with pytest.raises(ValueError):
        run_accumulation_pair(make, fixtures(), exact=True)
    assert not steps


def test_cpu_tolerant_mode_denied_before_forward(monkeypatch):
    make, created = factory()
    calls = []
    monkeypatch.setattr(
        pair_module, "observe_accumulation", lambda *args, **kwargs: calls.append(1)
    )
    with pytest.raises(ValueError):
        run_accumulation_pair(make, fixtures(), exact=False)
    assert not calls


@pytest.mark.parametrize("exact", [1, None, "true"])
def test_invalid_exact_denied_before_factory(exact):
    calls = []
    with pytest.raises(ValueError):
        run_accumulation_pair(lambda flag: calls.append(flag), fixtures(), exact=exact)
    assert not calls
