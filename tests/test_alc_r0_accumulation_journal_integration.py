"""Tiny synthetic numerical error boundaries, never actual-host/learning proof."""

from dataclasses import replace

import pytest
import torch
from test_alc_r0_accumulation_observation import fixtures as accumulation_inputs
from test_alc_r0_accumulation_pair import factory as pair_factory
from test_alc_r0_parity_cell import factory as cell_factory
from test_alc_r0_parity_cell import fixtures as cell_inputs
from test_alc_r0_reference_parity_suite import run as reference_run
from test_alc_r0_reference_parity_suite import wiring

import aluclu.alc_r0.checkpoint_accumulation_pair as pair
import aluclu.alc_r0.checkpoint_accumulation_step as step
import aluclu.alc_r0.checkpoint_observation as observation
import aluclu.alc_r0.checkpoint_parity_cell as cell
from aluclu.alc_r0.checkpoint_accumulation_progress import (
    _AccumulationOwner,
    validate_accumulation_failure,
)


def assert_cleared(wrappers):
    assert all(
        p.grad is None for wrapper in wrappers for p in wrapper.factors.parameters()
    )
    assert all(
        p.grad is None for wrapper in wrappers for p in wrapper.base.parameters()
    )


@pytest.fixture
def reference_wiring(monkeypatch):
    return wiring.__wrapped__(monkeypatch)


@pytest.mark.parametrize("interrupt", [False, True])
@pytest.mark.parametrize("timing", ["before_cache", "after_cache"])
@pytest.mark.parametrize("extra", ["tensor", "object"])
def test_late_reference_failure_rejects_extra_row_fields(
    reference_wiring, monkeypatch, interrupt, timing, extra
):
    """Stubbed cell framing; reject graph/object retention, not numerical proof."""
    module, _, created = reference_wiring
    original_cell = module.run_parity_cell
    original_unchanged = module._ReferenceFactory.unchanged
    primary = (
        KeyboardInterrupt("late framing") if interrupt else RuntimeError("late framing")
    )
    injected = torch.ones(2, requires_grad=True) * 2 if extra == "tensor" else object()
    returned = []

    def complete(*args, **kwargs):
        result = original_cell(*args, **kwargs)
        if timing == "before_cache":
            object.__setattr__(result.cases[5], "extra", injected)
        returned.append(result)
        return result

    def fail_after_cell(factory):
        if returned:
            if timing == "after_cache":
                object.__setattr__(returned[0].cases[5], "extra", injected)
            for wrapper in created:
                for parameter in wrapper.reference.parameters():
                    parameter.grad = torch.ones_like(parameter)
            raise primary
        return original_unchanged(factory)

    monkeypatch.setattr(module, "run_parity_cell", complete)
    monkeypatch.setattr(module._ReferenceFactory, "unchanged", fail_after_cell)
    expected = (
        module.ReferenceParityInterrupted if interrupt else module.ReferenceParityError
    )
    with pytest.raises(expected) as caught:
        reference_run(reference_wiring)
    error = caught.value
    assert error.__cause__ is primary
    assert error.journal_fault
    assert error.failure.stage == "final_base"
    failure = error.failure.cell_failure
    assert failure.completed == returned[0].cases[:5]
    assert all(len(vars(row)) == 7 for row in failure.completed)
    assert failure.pending_losses == returned[0].pending_losses
    assert failure.accumulation is None
    assert all(
        p.grad is None for wrapper in created for p in wrapper.reference.parameters()
    )


@pytest.mark.parametrize("extra", ["tensor", "object"])
@pytest.mark.parametrize("timing", ["before_cache", "after_cache"])
def test_reference_cannot_return_success_after_detecting_bad_row_framing(
    reference_wiring, monkeypatch, extra, timing
):
    """Malformed synthesized receipt cannot bypass a detected framing failure."""
    module, _, _ = reference_wiring
    original = module.run_parity_cell
    original_unchanged = module._ReferenceFactory.unchanged
    returned = []
    injected = torch.ones(2, requires_grad=True) * 2 if extra == "tensor" else object()

    def malformed(*args, **kwargs):
        result = original(*args, **kwargs)
        if timing == "before_cache":
            object.__setattr__(result.cases[5], "extra", injected)
        returned.append(result)
        return result

    def mutate_after_cache(factory):
        if returned and timing == "after_cache":
            object.__setattr__(returned[0].cases[5], "extra", injected)
        return original_unchanged(factory)

    monkeypatch.setattr(module, "run_parity_cell", malformed)
    monkeypatch.setattr(module._ReferenceFactory, "unchanged", mutate_after_cache)
    with pytest.raises(module.ReferenceParityError) as caught:
        reference_run(reference_wiring)
    assert type(caught.value.__cause__) is ValueError
    assert caught.value.journal_fault
    failure = caught.value.failure.cell_failure
    assert failure.completed == returned[0].cases[:5]
    assert all(len(vars(row)) == 7 for row in failure.completed)
    assert failure.pending_losses == returned[0].pending_losses


@pytest.mark.parametrize("interrupt", [False, True])
@pytest.mark.parametrize(
    "bad",
    [
        "stage",
        "completed_list",
        "oversized",
        "row",
        "row_metric",
        "current",
        "unrun",
        "pending",
    ],
)
def test_reference_sanitizes_all_inner_fields_without_losing_valid_evidence(
    reference_wiring, monkeypatch, interrupt, bad
):
    """Stubbed reference framing; never numerical parity evidence."""
    module, _, _ = reference_wiring
    original = module.run_parity_cell
    primary = KeyboardInterrupt("framing") if interrupt else RuntimeError("framing")
    observed = []

    def corrupt(factory, inputs, *, exact, _accumulation_owner):
        result = original(factory, inputs, exact=exact)
        good = module._completed_progress(result)
        changes = {
            "stage": {"stage": object()},
            "completed_list": {"completed": list(good.completed)},
            "oversized": {"completed": good.completed + good.completed[:1]},
            "row": {"completed": good.completed[:5] + (object(),) + good.completed[6:]},
            "row_metric": {
                "completed": good.completed[:5]
                + (replace(good.completed[5], losses=(float("inf"), 1.0)),)
                + good.completed[6:]
            },
            "current": {"current": torch.tensor(1)},
            "unrun": {"unrun": [object()]},
            "pending": {"pending_losses": (float("nan"), 1.0)},
        }
        failure = replace(good, **changes[bad])
        observed.append(good)
        kind = cell.ParityCellInterrupted if interrupt else cell.ParityCellError
        raise kind("framing", failure, cleanup_fault=True) from primary

    monkeypatch.setattr(module, "run_parity_cell", corrupt)
    expected = (
        module.ReferenceParityInterrupted if interrupt else module.ReferenceParityError
    )
    with pytest.raises(expected) as caught:
        reference_run(reference_wiring)
    error = caught.value
    failure = error.failure.cell_failure
    assert error.__cause__.__cause__ is primary
    assert error.journal_fault and error.cleanup_fault
    assert type(failure) is cell.ParityCellFailure and failure.stage == "invalid_inner"
    expected_prefix = (
        ()
        if bad in ("completed_list", "oversized")
        else observed[0].completed[:5]
        if bad in ("row", "row_metric")
        else observed[0].completed
    )
    assert failure.completed == expected_prefix
    assert failure.current is None and failure.unrun == ()
    assert failure.pending_losses == (
        None if bad == "pending" else observed[0].pending_losses
    )
    assert failure.accumulation is None


def test_real_tiny_pair_drives_complete_owned_journal_without_receipt_changes():
    owner = _AccumulationOwner()
    make, created = pair_factory()
    result = pair.run_accumulation_pair(
        make, accumulation_inputs(), exact=True, _accumulation_owner=owner
    )
    record = owner.snapshot()
    assert validate_accumulation_failure(record) is record
    assert record.completed_pair == 12
    assert (record.off.forwards, record.on.forwards) == (16, 16)
    assert (record.off.backwards, record.on.backwards) == (16, 16)
    assert (record.off.completed_step, record.on.completed_step) == (11, 11)
    assert result.comparison.step == 1
    assert not hasattr(result, "journal") and not hasattr(result, "failure")
    assert len(created) == 2


BOUNDARIES = (
    ("off", "micro_forward", 0),
    ("off", "micro_backward", 7),
    ("off", "micro_capture", 15),
    ("off", "observe_capture", None),
    ("off", "observe_record", None),
    ("on", "micro_forward", 0),
    ("on", "micro_backward", 7),
    ("on", "micro_capture", 15),
    ("on", "observe_record", None),
    ("off", "step_admit", None),
    ("off", "step_optimizer_create", None),
    ("off", "step_clip", None),
    ("off", "step_clipped_capture", None),
    ("off", "step_optimizer_call", None),
    ("off", "step_postconditions", None),
    ("off", "step_snapshot", None),
    ("off", "step_record", None),
    ("on", "step_optimizer_call", None),
    ("on", "step_postconditions", None),
    ("on", "step_record", None),
)


@pytest.mark.parametrize("interrupt", [False, True])
@pytest.mark.parametrize("arm", ["off", "on"])
@pytest.mark.parametrize(
    "phase,index,counters,observation_count,step_count",
    [
        ("micro_forward", 3, (4, 3, 3), 4, 0),
        ("micro_backward", 3, (4, 4, 3), 6, 0),
        ("micro_capture", 15, (16, 16, 16), 7, 0),
        ("observe_record", None, (16, 16, 16), 15, 0),
        ("step_optimizer_call", None, (16, 16, 16), 15, 8),
        ("step_record", None, (16, 16, 16), 15, 11),
    ],
)
def test_returned_operation_is_retained_without_inventing_enclosing_return(
    monkeypatch, interrupt, arm, phase, index, counters, observation_count, step_count
):
    """Actual tiny operations; injected fault follows a recorded inner return."""
    primary = (
        KeyboardInterrupt("after return") if interrupt else RuntimeError("after return")
    )
    original = _AccumulationOwner.finish_arm
    hits = []

    def inject(owner, ticket, returned, returned_index=None):
        original(owner, ticket, returned, returned_index)
        if (ticket.arm, returned, returned_index) == (arm, phase, index):
            hits.append(1)
            raise primary

    monkeypatch.setattr(_AccumulationOwner, "finish_arm", inject)
    make, created = pair_factory()
    expected = pair.AccumulationInterrupted if interrupt else pair.AccumulationError
    with pytest.raises(expected) as caught:
        pair.run_accumulation_pair(make, accumulation_inputs(), exact=True)
    record = caught.value.failure
    assert validate_accumulation_failure(record) is record
    assert (record.arm, record.phase, record.index) == (arm, phase, index)
    progress = getattr(record, arm)
    assert (progress.forwards, progress.backwards, progress.captured) == counters
    assert progress.completed_observation == observation_count
    assert progress.completed_step == step_count
    assert record.completed_pair == (
        (8 if arm == "off" else 9)
        if phase.startswith("step_")
        else (2 if arm == "off" else 5)
    )
    assert caught.value.__cause__ is primary
    assert str(caught.value) == "after return"
    assert hits == [1]
    assert_cleared([wrapper for _, wrapper in created])


@pytest.mark.parametrize("interrupt", [False, True])
@pytest.mark.parametrize("arm,phase,index", BOUNDARIES)
def test_entered_error_or_interrupt_retains_exact_stage_and_cause(
    monkeypatch, arm, phase, index, interrupt
):
    primary = KeyboardInterrupt("primary") if interrupt else RuntimeError("primary")
    original = _AccumulationOwner.begin_arm
    hits = []

    def inject(owner, ticket, entered, entered_index=None):
        original(owner, ticket, entered, entered_index)
        if (ticket.arm, entered, entered_index) == (arm, phase, index):
            hits.append(1)
            raise primary

    monkeypatch.setattr(_AccumulationOwner, "begin_arm", inject)
    make, created = pair_factory()
    expected = pair.AccumulationInterrupted if interrupt else pair.AccumulationError
    with pytest.raises(expected) as caught:
        pair.run_accumulation_pair(make, accumulation_inputs(), exact=True)
    record = caught.value.failure
    validate_accumulation_failure(record)
    assert (record.arm, record.phase, record.index) == (arm, phase, index)
    assert caught.value.__cause__ is primary
    assert str(caught.value) == "primary"
    assert hits == [1]
    if phase == "micro_backward":
        progress = getattr(record, arm)
        assert (progress.forwards, progress.backwards, progress.captured) == (
            index + 1,
            index,
            index,
        )
    if phase == "step_postconditions":
        assert getattr(record, arm).completed_step == 8
        assert record.completed_pair == (8 if arm == "off" else 9)
    assert_cleared([wrapper for _, wrapper in created])


@pytest.mark.parametrize("interrupt", [False, True])
def test_late_cell_failure_retains_real_completed_accumulation(monkeypatch, interrupt):
    primary = KeyboardInterrupt("late base") if interrupt else RuntimeError("late base")
    original_pair = cell.run_accumulation_pair
    original_digest = cell._base_digest
    returned = []

    def complete(*args, **kwargs):
        result = original_pair(*args, **kwargs)
        returned.append(1)
        return result

    def fail_after_pair(base):
        if returned:
            raise primary
        return original_digest(base)

    monkeypatch.setattr(cell, "run_accumulation_pair", complete)
    monkeypatch.setattr(cell, "_base_digest", fail_after_pair)
    make, created = cell_factory()
    expected = cell.ParityCellInterrupted if interrupt else cell.ParityCellError
    with pytest.raises(expected) as caught:
        cell.run_parity_cell(make, cell_inputs(), exact=True)
    failure = caught.value.failure
    assert caught.value.__cause__ is primary
    assert failure.stage == "final_base"
    assert len(failure.completed) == 18
    assert failure.pending_losses is not None
    record = failure.accumulation
    assert validate_accumulation_failure(record) is record
    assert record.completed_pair == 12
    assert record.off.completed_step == record.on.completed_step == 11
    assert returned == [1]
    assert_cleared([wrapper for _, _, wrapper in created])


@pytest.mark.parametrize("engine", ["pair", "cell"])
def test_rejected_factor_alias_does_not_clear_caller_owned_base_gradient(engine):
    make, created = pair_factory() if engine == "pair" else cell_factory()
    protected = []

    def malformed(*args):
        wrapper = make(*args)
        base_parameter = wrapper.base.weight
        base_gradient = torch.ones_like(base_parameter)
        base_parameter.grad = base_gradient
        wrapper.factors.A = base_parameter
        wrapper.factors.B.grad = torch.ones_like(wrapper.factors.B)
        protected.append((base_parameter, base_gradient, wrapper.factors.B))
        return wrapper

    if engine == "pair":
        with pytest.raises(pair.AccumulationError):
            pair.run_accumulation_pair(malformed, accumulation_inputs(), exact=True)
    else:
        with pytest.raises(cell.ParityCellError):
            cell.run_parity_cell(malformed, cell_inputs(), exact=True)
    assert len(created) == len(protected) == 1
    base_parameter, base_gradient, owned_factor = protected[0]
    assert base_parameter.grad is base_gradient
    assert torch.equal(base_gradient, torch.ones_like(base_gradient))
    assert owned_factor.grad is None


@pytest.mark.parametrize("interrupt", [False, True])
def test_combined_cleanup_and_snapshot_failure_preserves_both_markers(
    monkeypatch, interrupt
):
    primary = KeyboardInterrupt("combined") if interrupt else RuntimeError("combined")
    original_setattr = torch.nn.Parameter.__setattr__
    armed, cleanup_hits = [], []
    entered = []
    original_observe = pair.observe_accumulation
    original_score = observation.score_banking_candidate

    def observe(*args, **kwargs):
        entered.append(1)
        return original_observe(*args, **kwargs)

    def fail(*args, **kwargs):
        if not entered:
            return original_score(*args, **kwargs)
        armed.append(1)
        raise primary

    def setattr_once(parameter, name, value):
        if armed and name == "grad" and value is None and not cleanup_hits:
            cleanup_hits.append(1)
            raise RuntimeError("cleanup")
        return original_setattr(parameter, name, value)

    monkeypatch.setattr(observation, "score_banking_candidate", fail)
    monkeypatch.setattr(pair, "observe_accumulation", observe)
    monkeypatch.setattr(torch.nn.Parameter, "__setattr__", setattr_once)
    monkeypatch.setattr(pair, "_safe_snapshot", lambda owner: (None, True))
    make, created = cell_factory()
    expected = cell.ParityCellInterrupted if interrupt else cell.ParityCellError
    with pytest.raises(expected) as caught:
        cell.run_parity_cell(make, cell_inputs(), exact=True)
    error = caught.value
    assert error.__cause__.__cause__ is primary
    assert error.failure.accumulation is None
    assert error.journal_fault and error.cleanup_fault
    assert_cleared([wrapper for _, _, wrapper in created])


@pytest.mark.parametrize("interrupt", [False, True])
def test_malformed_inner_snapshot_does_not_erase_valid_cleanup_marker(
    monkeypatch, interrupt
):
    primary = KeyboardInterrupt("malformed") if interrupt else RuntimeError("malformed")
    expected_inner = (
        pair.AccumulationInterrupted if interrupt else pair.AccumulationError
    )

    def fail(*args, **kwargs):
        raise expected_inner("malformed", object(), cleanup_fault=True) from primary

    monkeypatch.setattr(cell, "run_accumulation_pair", fail)
    make, created = cell_factory()
    expected = cell.ParityCellInterrupted if interrupt else cell.ParityCellError
    with pytest.raises(expected) as caught:
        cell.run_parity_cell(make, cell_inputs(), exact=True)
    error = caught.value
    assert error.__cause__.__cause__ is primary
    assert error.failure.accumulation is None
    assert error.journal_fault and error.cleanup_fault
    assert (
        len(error.failure.completed) == 18 and error.failure.pending_losses is not None
    )
    assert_cleared([wrapper for _, _, wrapper in created])


@pytest.mark.parametrize("interrupt", [False, True])
@pytest.mark.parametrize("stage", ["inner", "late"])
@pytest.mark.parametrize("fault", ["snapshot", "cleanup"])
def test_stubbed_reference_fault_transport_preserves_primary_and_prefix(
    reference_wiring, monkeypatch, interrupt, stage, fault
):
    """Reference framing/cleanup only: fixture deliberately stubs cell computation."""
    module, _, _ = reference_wiring
    original_cell, original_clear = (
        module.run_parity_cell,
        module._ReferenceFactory.clear,
    )
    primary = KeyboardInterrupt("reference") if interrupt else RuntimeError("reference")

    def framed_cell(factory, inputs, *, exact, _accumulation_owner):
        result = original_cell(factory, inputs, exact=exact)
        if stage == "inner":
            kind = cell.ParityCellInterrupted if interrupt else cell.ParityCellError
            raise kind(
                "reference",
                module._completed_progress(result),
                journal_fault=fault == "snapshot",
                cleanup_fault=fault == "cleanup",
            ) from primary
        return result

    def fail(*args, **kwargs):
        raise primary

    def clear(factory):
        original_clear(factory)
        raise RuntimeError("reference cleanup")

    monkeypatch.setattr(module, "run_parity_cell", framed_cell)
    if stage == "late":
        monkeypatch.setattr(module, "validate_reference_parity_receipt", fail)
    if fault == "cleanup":
        monkeypatch.setattr(module._ReferenceFactory, "clear", clear)
    elif stage == "late":
        monkeypatch.setattr(module, "_safe_snapshot", lambda owner: (None, True))
    expected = (
        module.ReferenceParityInterrupted if interrupt else module.ReferenceParityError
    )
    with pytest.raises(expected) as caught:
        reference_run(reference_wiring)
    error = caught.value
    if stage == "inner":
        assert error.__cause__.__cause__ is primary
    else:
        assert error.__cause__ is primary
    assert getattr(
        error, "journal_fault" if fault == "snapshot" else "cleanup_fault", False
    )
    assert len(error.failure.cell_failure.completed) == 18
    assert error.failure.cell_failure.pending_losses is not None


@pytest.mark.parametrize("interrupt", [False, True])
def test_on_factory_failure_retains_completed_off_observation(monkeypatch, interrupt):
    make, created = pair_factory()
    primary = KeyboardInterrupt("factory") if interrupt else RuntimeError("factory")

    def broken(checkpoint):
        if checkpoint:
            raise primary
        return make(checkpoint)

    expected = pair.AccumulationInterrupted if interrupt else pair.AccumulationError
    with pytest.raises(expected) as caught:
        pair.run_accumulation_pair(broken, accumulation_inputs(), exact=True)
    record = caught.value.failure
    assert record.phase == "on_factory" and record.completed_pair == 3
    assert record.off.completed_observation == 15 and record.off.captured == 16
    assert record.on.forwards == record.on.completed_step == 0
    assert caught.value.__cause__ is primary
    assert len(created) == 1
    assert_cleared([wrapper for _, wrapper in created])


def test_preclip_failure_prevents_either_optimizer_step(monkeypatch):
    primary = RuntimeError("preclip")
    steps = []

    def fail(*args, **kwargs):
        raise primary

    monkeypatch.setattr(pair, "compare_accumulations", fail)
    monkeypatch.setattr(pair, "step_accumulation", lambda *a, **kw: steps.append(1))
    make, created = pair_factory()
    with pytest.raises(pair.AccumulationError) as caught:
        pair.run_accumulation_pair(make, accumulation_inputs(), exact=True)
    record = caught.value.failure
    assert record.phase == "preclip_compare" and record.completed_pair == 6
    assert record.off.completed_step == record.on.completed_step == 0
    assert not steps
    assert caught.value.__cause__ is primary
    assert_cleared([wrapper for _, wrapper in created])


def test_actual_forward_failure_does_not_increment_completed_forward(monkeypatch):
    make, created = pair_factory()
    primary = RuntimeError("forward")

    def broken(checkpoint):
        wrapper = make(checkpoint)
        original = wrapper.forward
        calls = []

        def forward(**kwargs):
            calls.append(1)
            if not checkpoint and len(calls) == 4:
                raise primary
            return original(**kwargs)

        monkeypatch.setattr(wrapper, "forward", forward)
        return wrapper

    with pytest.raises(pair.AccumulationError) as caught:
        pair.run_accumulation_pair(broken, accumulation_inputs(), exact=True)
    record = caught.value.failure
    assert (record.phase, record.arm, record.index) == ("micro_forward", "off", 3)
    assert (record.off.forwards, record.off.backwards, record.off.captured) == (3, 3, 3)
    assert caught.value.__cause__ is primary
    assert_cleared([wrapper for _, wrapper in created])


def test_actual_backward_failure_does_not_increment_completed_backward(monkeypatch):
    make, created = pair_factory()
    primary = RuntimeError("backward")
    original = torch.Tensor.backward
    calls = []

    def backward(value, *args, **kwargs):
        calls.append(1)
        if len(calls) == 4:
            raise primary
        return original(value, *args, **kwargs)

    monkeypatch.setattr(torch.Tensor, "backward", backward)
    with pytest.raises(pair.AccumulationError) as caught:
        pair.run_accumulation_pair(make, accumulation_inputs(), exact=True)
    record = caught.value.failure
    assert (record.phase, record.arm, record.index) == ("micro_backward", "off", 3)
    assert (record.off.forwards, record.off.backwards, record.off.captured) == (4, 3, 3)
    assert calls == [1] * 4 and caught.value.__cause__ is primary
    assert_cleared([wrapper for _, wrapper in created])


@pytest.mark.parametrize("interrupt", [False, True])
def test_cell_preserves_singles_pending_and_inner_accumulation_failure(
    monkeypatch, interrupt
):
    original = _AccumulationOwner.begin_arm
    primary = KeyboardInterrupt("cell") if interrupt else RuntimeError("cell")

    def inject(owner, ticket, phase, index=None):
        original(owner, ticket, phase, index)
        if ticket.arm == "on" and phase == "step_record":
            raise primary

    monkeypatch.setattr(_AccumulationOwner, "begin_arm", inject)
    make, created = cell_factory()
    expected = cell.ParityCellInterrupted if interrupt else cell.ParityCellError
    with pytest.raises(expected) as caught:
        cell.run_parity_cell(make, cell_inputs(), exact=True)
    failure = caught.value.failure
    assert len(failure.completed) == 18 and failure.unrun == ()
    assert failure.pending_losses is not None
    assert failure.accumulation.phase == "step_record"
    assert failure.accumulation.arm == "on"
    assert failure.accumulation.completed_pair == 9
    assert_cleared([wrapper for _, _, wrapper in created])


@pytest.mark.parametrize("interrupt", [False, True])
@pytest.mark.parametrize("fault", ["snapshot", "cleanup"])
def test_cell_preserves_pair_secondary_fault_markers(monkeypatch, interrupt, fault):
    primary = KeyboardInterrupt("original") if interrupt else RuntimeError("original")

    def fail(*args, **kwargs):
        raise primary

    monkeypatch.setattr(pair, "compare_accumulations", fail)
    if fault == "snapshot":
        monkeypatch.setattr(pair, "_safe_snapshot", lambda owner: (None, True))
    else:
        original = pair._clear_owned

        def clear(parameters):
            original(parameters)
            return True

        monkeypatch.setattr(pair, "_clear_owned", clear)
    make, created = cell_factory()
    expected = cell.ParityCellInterrupted if interrupt else cell.ParityCellError
    with pytest.raises(expected) as caught:
        cell.run_parity_cell(make, cell_inputs(), exact=True)
    error = caught.value
    assert error.__cause__.__cause__ is primary
    assert (
        len(error.failure.completed) == 18 and error.failure.pending_losses is not None
    )
    assert getattr(error, "journal_fault" if fault == "snapshot" else "cleanup_fault")
    if fault == "snapshot":
        assert error.failure.accumulation is None
    else:
        assert error.failure.accumulation.cleanup_fault
    assert_cleared([wrapper for _, _, wrapper in created])


@pytest.mark.parametrize("interrupt", [False, True])
@pytest.mark.parametrize("layer", ["observation", "step"])
def test_secondary_factor_cleanup_does_not_replace_computation_error(
    monkeypatch, interrupt, layer
):
    primary = KeyboardInterrupt("compute") if interrupt else RuntimeError("compute")
    original_setattr = torch.nn.Parameter.__setattr__
    make, created = pair_factory()
    armed = []
    failed_cleanup = []

    def broken_setattr(parameter, name, value):
        if armed and name == "grad" and value is None and not failed_cleanup:
            failed_cleanup.append(id(parameter))
            raise RuntimeError("secondary cleanup")
        return original_setattr(parameter, name, value)

    def fail(*args, **kwargs):
        armed.append(1)
        raise primary

    monkeypatch.setattr(torch.nn.Parameter, "__setattr__", broken_setattr)
    if layer == "observation":
        monkeypatch.setattr(observation, "score_banking_candidate", fail)
    else:
        monkeypatch.setattr(step, "_snapshot", fail)
    expected = pair.AccumulationInterrupted if interrupt else pair.AccumulationError
    with pytest.raises(expected) as caught:
        pair.run_accumulation_pair(make, accumulation_inputs(), exact=True)
    assert failed_cleanup and caught.value.__cause__ is primary
    assert caught.value.cleanup_fault and caught.value.failure.cleanup_fault
    assert_cleared([wrapper for _, wrapper in created])
