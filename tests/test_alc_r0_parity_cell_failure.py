"""Small synthetic wrappers exercise failure journals, not actual-host parity."""

import importlib

import pytest
from test_alc_r0_parity_cell import factory, fixtures


def module():
    return importlib.import_module("aluclu.alc_r0.checkpoint_parity_cell")


@pytest.mark.parametrize("index", [0, 5, 6, 12, 17])
@pytest.mark.parametrize("interrupt", [False, True])
def test_failed_single_retains_prefix_key_unrun_no_retry(monkeypatch, index, interrupt):
    runner = module()
    make, created = factory()
    original = runner.observe_forward_backward
    attempts = []

    def fail(wrapper, fixture, *, checkpoint, state):
        if not checkpoint:
            attempts.append((state, len(attempts)))
            if len(attempts) == index + 1:
                raise (
                    KeyboardInterrupt("declared")
                    if interrupt
                    else RuntimeError("declared")
                )
        return original(wrapper, fixture, checkpoint=checkpoint, state=state)

    monkeypatch.setattr(runner, "observe_forward_backward", fail)
    error = runner.ParityCellInterrupted if interrupt else runner.ParityCellError
    with pytest.raises(error) as caught:
        runner.run_parity_cell(make, fixtures(), exact=True)
    failure = caught.value.failure
    assert failure.stage == "single_off"
    assert failure.current == runner.SINGLE_SCHEDULE[index]
    assert len(failure.completed) == index
    assert failure.unrun == runner.SINGLE_SCHEDULE[index + 1 :]
    assert failure.pending_losses is None
    assert len(attempts) == index + 1
    assert isinstance(
        caught.value.__cause__, KeyboardInterrupt if interrupt else RuntimeError
    )
    assert all(p.grad is None for _, _, w in created for p in w.factors.parameters())


def test_factory_failure_does_not_mark_current_row_attempted():
    runner = module()
    make, created = factory()

    def fail(state, checkpoint):
        if len(created) == 2:
            raise ValueError("factory deliberate")
        return make(state, checkpoint)

    with pytest.raises(runner.ParityCellError) as caught:
        runner.run_parity_cell(fail, fixtures(), exact=True)
    failure = caught.value.failure
    assert failure.stage == "single_factory_off"
    assert len(failure.completed) == 1
    assert failure.current == runner.SINGLE_SCHEDULE[1]
    assert failure.unrun == runner.SINGLE_SCHEDULE[1:]


@pytest.mark.parametrize(
    "stage", ["pending_off", "pending_on", "pending_compare", "accumulation"]
)
def test_later_stage_retains_all_singles(monkeypatch, stage):
    runner = module()
    make, _ = factory()
    original = runner.observe_pending_pair

    def fail(*args, **kwargs):
        raise ValueError("late deliberate")

    if stage in ("pending_off", "pending_on"):

        def observe(*args, **kwargs):
            if kwargs["checkpoint"] == (stage == "pending_on"):
                fail()
            return original(*args, **kwargs)

        monkeypatch.setattr(runner, "observe_pending_pair", observe)
    elif stage == "pending_compare":
        monkeypatch.setattr(runner, "compare_pending_observations", fail)
    else:
        monkeypatch.setattr(runner, "run_accumulation_pair", fail)
    with pytest.raises(runner.ParityCellError) as caught:
        runner.run_parity_cell(make, fixtures(), exact=True)
    failure = caught.value.failure
    assert failure.stage == stage
    assert len(failure.completed) == 18
    assert failure.current is None and failure.unrun == ()
    assert (failure.pending_losses is not None) == (stage == "accumulation")


def test_success_still_has_original_complete_result():
    runner = module()
    make, _ = factory()
    result = runner.run_parity_cell(make, fixtures(), exact=True)
    assert len(result.cases) == 18 and result.accumulation.step == 1
