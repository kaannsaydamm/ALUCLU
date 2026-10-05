"""Mocked CPU orchestration, not host/full4096 attention or E3 qualification.

Start/binding/inventory and microbatch are explicit substitutions. Real fixed
AdamW and snapshot checks execute on two small factors. Full schedule/counts
stay4096/16/2; this proves loop accounting only, not model behavior/resource fit.
"""

from contextlib import contextmanager
from types import SimpleNamespace

import pytest
import torch
from torch import nn

from aluclu.alc_r0 import reference_stress_execution as run
from aluclu.alc_r0.checkpoint_observation import _base_digest
from aluclu.alc_r0.reference_stress_inputs import (
    build_stress_schedule,
    stress_schedule_sha256,
)


@pytest.fixture
def logic(monkeypatch):
    wrapper = nn.Module()
    wrapper.base = nn.Linear(2, 2, bias=False).requires_grad_(False).eval()
    wrapper.reference = nn.Module()
    wrapper.reference.A = nn.Parameter(torch.ones(2, 2))
    wrapper.reference.B = nn.Parameter(torch.zeros(2, 2))
    wrapper.active = False
    factors = dict(wrapper.reference.named_parameters())
    events, optimizers = [], []
    schedule = build_stress_schedule(
        prefix_ids=(7,), suffix_ids=(8,), safe_ids=(9,), vulnerable_ids=(10, 11)
    )

    @contextmanager
    def lease():
        assert not wrapper.active
        wrapper.active = True
        events.append("enter")
        try:
            yield None
        finally:
            wrapper.active = False
            events.append("exit")

    def guard():
        assert not wrapper.active

    def optimizer(owner):
        assert owner is wrapper and not wrapper.active
        value = torch.optim.AdamW(
            list(factors.values()),
            lr=3e-4,
            betas=(0.9, 0.999),
            eps=1e-8,
            weight_decay=0,
            foreach=False,
            fused=False,
        )
        original = value.step

        def step():
            assert not wrapper.active
            events.append("step")
            return original()

        value.step = step
        optimizers.append(value)
        return value

    def microbatch(owner, item, device):
        assert owner is wrapper and not wrapper.active
        with lease():
            assert len(item.input_ids) in (4095, 4096)
            loss = (wrapper.reference.A * wrapper.reference.B).sum() + 2
            (loss / 16).backward()
            events.append(item.label)
            return float(loss.detach().item()) / 16

    wrapper._assert_checkpoint_mutation_allowed = guard
    monkeypatch.setattr(
        run,
        "inspect_reference_stress_start",
        lambda w, s: SimpleNamespace(
            base_digest=_base_digest(wrapper.base),
            schedule_digest=stress_schedule_sha256(s),
        ),
    )
    monkeypatch.setattr(
        run, "reference_bindings", lambda w: (factors, tuple(wrapper.base.parameters()))
    )
    monkeypatch.setattr(run, "_inventory", lambda w: guard())
    monkeypatch.setattr(run, "make_reference_optimizer", optimizer)
    monkeypatch.setattr(run, "_microbatch", microbatch)
    return wrapper, schedule, events, optimizers


def test_two_updates_one_optimizer_exact_schedule_and_quiescent_steps(logic):
    wrapper, schedule, events, optimizers = logic
    result = run.execute_reference_stress(wrapper, schedule)
    assert len(optimizers) == 1
    assert result.progress.stage == "complete"
    assert result.progress.attempted_updates == result.progress.completed_updates == 2
    assert (
        result.progress.attempted_microbatches
        == result.progress.completed_microbatches
        == 32
    )
    assert result.progress.attempted_steps == result.progress.returned_steps == 2
    assert [e for e in events if e in ("safe", "vulnerable")] == [
        "safe",
        "vulnerable",
    ] * 16
    assert events.count("enter") == events.count("exit") == 32
    assert events.count("step") == 2
    for index, event in enumerate(events):
        if event == "step":
            assert events[index - 1] == "exit"
    assert all(
        float(state["step"].item()) == 2 for state in optimizers[0].state.values()
    )
    assert all(p.grad is None for p in wrapper.reference.parameters())
    assert len(result.updates) == 2


def test_microbatch_failure_preserves_partial_counts_no_retry(logic, monkeypatch):
    wrapper, schedule, events, optimizers = logic
    original = run._microbatch
    calls = 0

    def fail(owner, item, device):
        nonlocal calls
        calls += 1
        if calls == 19:
            raise RuntimeError("injected failure")
        return original(owner, item, device)

    monkeypatch.setattr(run, "_microbatch", fail)
    with pytest.raises(run.StressExecutionError) as caught:
        run.execute_reference_stress(wrapper, schedule)
    p = caught.value.progress
    assert (p.attempted_updates, p.completed_updates) == (2, 1)
    assert (p.attempted_microbatches, p.completed_microbatches) == (19, 18)
    assert (p.attempted_steps, p.returned_steps) == (1, 1)
    assert p.stage == "microbatch"
    assert len(optimizers) == 1 and events.count("step") == 1
    assert isinstance(caught.value.__cause__, RuntimeError)


def test_step_returned_but_invalid_state_not_completed(logic, monkeypatch):
    wrapper, schedule, _, _ = logic
    original = run._snapshot

    def fail(*args):
        if args[-1] == 2:
            raise ValueError("state verification fails")
        return original(*args)

    monkeypatch.setattr(run, "_snapshot", fail)
    with pytest.raises(run.StressExecutionError) as caught:
        run.execute_reference_stress(wrapper, schedule)
    p = caught.value.progress
    assert p.stage == "optimizer_state"
    assert (p.attempted_steps, p.returned_steps, p.completed_updates) == (2, 2, 1)


def test_preflight_failure_zero_attempts(logic, monkeypatch):
    wrapper, schedule, _, optimizers = logic

    def fail(*args):
        raise ValueError("no admission")

    monkeypatch.setattr(run, "inspect_reference_stress_start", fail)
    with pytest.raises(run.StressExecutionError) as caught:
        run.execute_reference_stress(wrapper, schedule)
    assert caught.value.progress.stage == "preflight"
    assert caught.value.progress.attempted_updates == 0 and not optimizers


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_gradient",
        "infinite_gradient",
        "factor_bytes",
        "base_bytes",
        "mode",
        "remount",
    ],
)
def test_mid_microbatch_invariant_failure_never_steps(logic, monkeypatch, mutation):
    wrapper, schedule, _, optimizers = logic
    original = run._microbatch

    def corrupt(owner, item, device):
        value = original(owner, item, device)
        if mutation == "missing_gradient":
            wrapper.reference.A.grad = None
        elif mutation == "infinite_gradient":
            wrapper.reference.A.grad.fill_(float("inf"))
        elif mutation == "factor_bytes":
            wrapper.reference.A.data.add_(1)
        elif mutation == "base_bytes":
            next(wrapper.base.parameters()).data.add_(1)
        elif mutation == "mode":
            wrapper.base.train()
        elif mutation == "remount":
            replacement = nn.Module()
            replacement.A, replacement.B = wrapper.reference.A, wrapper.reference.B
            wrapper.reference = replacement
        return value

    monkeypatch.setattr(run, "_microbatch", corrupt)
    with pytest.raises(run.StressExecutionError) as caught:
        run.execute_reference_stress(wrapper, schedule)
    assert caught.value.progress.attempted_steps == 0
    assert caught.value.progress.completed_updates == 0
    assert not optimizers[0].state


def test_step_mutates_then_raises_is_not_rolled_back(logic, monkeypatch):
    wrapper, schedule, _, optimizers = logic
    factory = run.make_reference_optimizer

    def injected(owner):
        value = factory(owner)
        original = value.step

        def step():
            original()
            raise RuntimeError("after mutation")

        value.step = step
        return value

    monkeypatch.setattr(run, "make_reference_optimizer", injected)
    with pytest.raises(run.StressExecutionError) as caught:
        run.execute_reference_stress(wrapper, schedule)
    p = caught.value.progress
    assert (p.attempted_steps, p.returned_steps, p.completed_updates) == (1, 0, 0)
    assert p.stage == "optimizer_step"
    assert any(torch.count_nonzero(p).item() for p in [wrapper.reference.B])
    assert optimizers[0].state


def test_clipping_is_quiescent_and_fixed(logic, monkeypatch):
    wrapper, schedule, _, _ = logic
    original = torch.nn.utils.clip_grad_norm_
    calls = []

    def clip(parameters, max_norm, *, error_if_nonfinite, foreach):
        assert not wrapper.active
        assert max_norm == 1.0 and error_if_nonfinite is True and foreach is False
        calls.append(1)
        return original(
            parameters, max_norm, error_if_nonfinite=error_if_nonfinite, foreach=foreach
        )

    monkeypatch.setattr(torch.nn.utils, "clip_grad_norm_", clip)
    run.execute_reference_stress(wrapper, schedule)
    assert len(calls) == 2


@pytest.mark.parametrize(
    "case", ["finite", "nan", "shape", "detached_loss", "vector_loss"]
)
def test_output_validation_on_small_vocab_not_host(case):
    result = SimpleNamespace(
        loss=torch.tensor(2.0, requires_grad=True), logits=torch.zeros(1, 65, 2)
    )
    if case == "nan":
        result.logits[0, 64, 1] = float("nan")
    elif case == "shape":
        result.logits = torch.zeros(1, 64, 2)
    elif case == "detached_loss":
        result.loss = result.loss.detach()
    elif case == "vector_loss":
        result.loss = result.loss.unsqueeze(0)
    if case == "finite":
        run._output(result, 65, 2, torch.device("cpu"))
    else:
        with pytest.raises(ValueError):
            run._output(result, 65, 2, torch.device("cpu"))


def test_real_microbatch_helper_full_inputs_with_fake_loss_and_lease():
    # Executes helper tensor/backward flow, not real checkpoint replay/attention.
    schedule = build_stress_schedule(
        prefix_ids=(7,), suffix_ids=(8,), safe_ids=(9,), vulnerable_ids=(10, 11)
    )
    item = schedule.inputs[1]
    weight = nn.Parameter(torch.tensor(3.0))
    events = []

    class Session:
        pending_count = 0

        def backward(self, loss):
            events.append("backward")
            loss.backward()

    class Fake:
        base = SimpleNamespace(config=SimpleNamespace(vocab_size=2))

        @contextmanager
        def checkpoint_session(self):
            events.append("enter")
            yield Session()
            events.append("exit")

        def __call__(self, **arguments):
            assert arguments["use_cache"] is False
            for name in ("input_ids", "labels", "position_ids", "attention_mask"):
                assert arguments[name].tolist() == [list(getattr(item, name))]
            return SimpleNamespace(loss=weight * 2, logits=torch.zeros(1, 4096, 2))

    value = run._microbatch(Fake(), item, torch.device("cpu"))
    assert value == 6 / 16 and weight.grad.item() == 2 / 16
    assert events == ["enter", "backward", "exit"]


def test_clipping_cannot_mutate_factor_bytes_before_step(logic, monkeypatch):
    wrapper, schedule, _, optimizers = logic
    original = torch.nn.utils.clip_grad_norm_

    def corrupt(parameters, max_norm, **kwargs):
        norm = original(parameters, max_norm, **kwargs)
        wrapper.reference.A.data.add_(1)
        return norm

    monkeypatch.setattr(torch.nn.utils, "clip_grad_norm_", corrupt)
    with pytest.raises(run.StressExecutionError) as caught:
        run.execute_reference_stress(wrapper, schedule)
    assert caught.value.progress.stage == "preclip"
    assert caught.value.progress.attempted_steps == 0
    assert not optimizers[0].state


def test_gradient_storage_cannot_alias_factors(logic, monkeypatch):
    wrapper, schedule, _, _ = logic
    original = run._microbatch

    def alias(owner, item, device):
        value = original(owner, item, device)
        wrapper.reference.A.grad = wrapper.reference.A.detach()
        return value

    monkeypatch.setattr(run, "_microbatch", alias)
    with pytest.raises(run.StressExecutionError) as caught:
        run.execute_reference_stress(wrapper, schedule)
    assert caught.value.progress.stage == "microbatch"
    assert caught.value.progress.attempted_steps == 0
