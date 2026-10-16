"""Primitive-only journal protocol; no Torch/model/assets/execution authority."""

import importlib
from dataclasses import FrozenInstanceError, fields, replace

import pytest


def module():
    return importlib.import_module("aluclu.alc_r0.checkpoint_accumulation_progress")


OBSERVE_START = ("observe_admit", "observe_prepare", "observe_session_enter")
OBSERVE_END = (
    "observe_total",
    "observe_session_exit",
    "observe_bindings",
    "observe_frozen",
    "observe_outputs",
    "observe_gradients",
    "observe_capture",
    "observe_record",
)
MICRO = ("micro_forward", "micro_loss", "micro_backward", "micro_capture")
STEP = (
    "step_admit",
    "step_live_gradients",
    "step_guard",
    "step_optimizer_create",
    "step_optimizer_group",
    "step_clip",
    "step_clipped_capture",
    "step_optimizer_call",
    "step_postconditions",
    "step_snapshot",
    "step_record",
)


def pair(owner, phase):
    owner.begin_pair(phase)
    module().validate_accumulation_failure(owner.snapshot())
    owner.finish_pair(phase)
    module().validate_accumulation_failure(owner.snapshot())


def nested(owner, ticket, phase, index=None):
    owner.begin_arm(ticket, phase, index)
    module().validate_accumulation_failure(owner.snapshot())
    owner.finish_arm(ticket, phase, index)
    module().validate_accumulation_failure(owner.snapshot())


def observation(owner, arm):
    ticket = owner.ticket(arm)
    owner.begin_pair(arm + "_observation")
    for phase in OBSERVE_START:
        nested(owner, ticket, phase)
    for index in range(16):
        for phase in MICRO:
            nested(owner, ticket, phase, index)
    for phase in OBSERVE_END:
        nested(owner, ticket, phase)
    owner.finish_pair(arm + "_observation")


def through_observations(owner):
    for arm in ("off", "on"):
        pair(owner, arm + "_factory")
        pair(owner, arm + "_bindings")
        observation(owner, arm)


def through_steps(owner):
    through_observations(owner)
    pair(owner, "preclip_compare")
    pair(owner, "cross_arm_storage")
    for arm in ("off", "on"):
        owner.begin_pair(arm + "_step")
        for phase in STEP:
            nested(owner, owner.ticket(arm), phase)
        owner.finish_pair(arm + "_step")


def test_complete_trace_has_bounded_immutable_primitive_records():
    journal = module()
    owner = journal._AccumulationOwner()
    assert owner.snapshot() is None
    through_steps(owner)
    pair(owner, "full_step_compare")
    pair(owner, "pair_record")
    record = owner.snapshot()
    assert record.completed_pair == 12
    assert record.phase == "pair_record" and record.arm is record.index is None
    for arm in (record.off, record.on):
        assert (arm.forwards, arm.backwards, arm.captured) == (16, 16, 16)
        assert (arm.completed_observation, arm.completed_step) == (15, 11)
        assert len(fields(arm)) == 5
        assert all(type(getattr(arm, field.name)) is int for field in fields(arm))
    assert len(fields(record)) == 8
    assert journal.validate_accumulation_failure(record) is record
    with pytest.raises(FrozenInstanceError):
        record.completed_pair = 0
    with pytest.raises(journal.JournalError):
        owner.begin_pair("off_factory")


@pytest.mark.parametrize("arm", ["off", "on"])
@pytest.mark.parametrize("index", [0, 7, 15])
def test_before_backward_counts_do_not_claim_observation_return(arm, index):
    owner = module()._AccumulationOwner()
    if arm == "on":
        pair(owner, "off_factory")
        pair(owner, "off_bindings")
        observation(owner, "off")
    pair(owner, arm + "_factory")
    pair(owner, arm + "_bindings")
    owner.begin_pair(arm + "_observation")
    ticket = owner.ticket(arm)
    for phase in OBSERVE_START:
        nested(owner, ticket, phase)
    for completed in range(index):
        for phase in MICRO:
            nested(owner, ticket, phase, completed)
    nested(owner, ticket, "micro_forward", index)
    nested(owner, ticket, "micro_loss", index)
    owner.begin_arm(ticket, "micro_backward", index)
    record = owner.snapshot()
    progress = getattr(record, arm)
    assert (progress.forwards, progress.backwards, progress.captured) == (
        index + 1,
        index,
        index,
    )
    assert progress.completed_observation == 5
    assert record.phase == "micro_backward" and record.index == index
    assert record.completed_pair == (2 if arm == "off" else 5)


def test_optimizer_return_does_not_claim_step_record_or_pair_return():
    owner = module()._AccumulationOwner()
    through_observations(owner)
    pair(owner, "preclip_compare")
    pair(owner, "cross_arm_storage")
    owner.begin_pair("off_step")
    for phase in STEP[:8]:
        nested(owner, owner.ticket("off"), phase)
    owner.begin_arm(owner.ticket("off"), "step_postconditions")
    record = owner.snapshot()
    assert record.off.completed_step == 8 and record.completed_pair == 8
    assert record.on.completed_step == 0
    before = record
    with pytest.raises(module().JournalError):
        owner.begin_pair("on_step")
    assert owner.snapshot() == before


def test_skipped_return_and_foreign_or_forged_ticket_are_rejected():
    journal = module()
    owner, foreign = journal._AccumulationOwner(), journal._AccumulationOwner()
    pair(owner, "off_factory")
    pair(owner, "off_bindings")
    owner.begin_pair("off_observation")
    before = owner.snapshot()
    with pytest.raises(journal.JournalError):
        owner.finish_pair("off_observation")
    for ticket in (foreign.ticket("off"), owner.ticket("on"), object()):
        with pytest.raises(journal.JournalError):
            owner.begin_arm(ticket, "observe_admit")
    assert owner.snapshot() == before
    owner.begin_arm(owner.ticket("off"), "observe_admit")
    with pytest.raises(journal.JournalError):
        owner.begin_arm(owner.ticket("off"), "observe_prepare")


@pytest.mark.parametrize(
    "changes",
    [
        {"completed_pair": True},
        {"completed_pair": 12},
        {"phase": "unknown"},
        {"arm": "on"},
        {"index": 0},
        {"journal_fault": 1},
        {"cleanup_fault": None},
    ],
)
def test_forged_snapshot_cannot_overstate_progress(changes):
    journal = module()
    owner = journal._AccumulationOwner()
    owner.begin_pair("off_factory")
    with pytest.raises(journal.JournalError):
        journal.validate_accumulation_failure(replace(owner.snapshot(), **changes))


def test_bad_nested_counts_subclasses_and_extra_fields_are_rejected():
    journal = module()
    owner = journal._AccumulationOwner()
    owner.begin_pair("off_factory")
    record = owner.snapshot()
    for changes in ({"forwards": True}, {"backwards": 1}, {"completed_step": 11}):
        with pytest.raises(journal.JournalError):
            journal.validate_accumulation_failure(
                replace(record, off=replace(record.off, **changes))
            )
    with pytest.raises(journal.JournalError):
        journal.validate_accumulation_failure(object())
    with pytest.raises(TypeError):
        replace(record, arbitrary_payload=object())


def test_closed_owner_retains_snapshot_but_cannot_continue():
    journal = module()
    owner = journal._AccumulationOwner()
    owner.begin_pair("off_factory")
    record = owner.snapshot()
    owner.close()
    assert owner.snapshot() == record
    with pytest.raises(journal.JournalError):
        owner.finish_pair("off_factory")


def test_copied_exact_ticket_is_foreign_even_with_same_owner_token_arm():
    journal = module()
    owner = journal._AccumulationOwner()
    pair(owner, "off_factory")
    pair(owner, "off_bindings")
    owner.begin_pair("off_observation")
    before = owner.snapshot()
    with pytest.raises(journal.JournalError):
        owner.begin_arm(replace(owner.ticket("off")), "observe_admit")
    assert owner.snapshot() == before


def test_owner_and_snapshot_subclasses_are_not_admitted():
    journal = module()

    class ForeignOwner(journal._AccumulationOwner):
        pass

    class ForeignRecord(journal.AccumulationFailure):
        pass

    with pytest.raises(journal.JournalError):
        ForeignOwner().begin_pair("off_factory")
    owner = journal._AccumulationOwner()
    owner.begin_pair("off_factory")
    record = owner.snapshot()
    foreign = ForeignRecord(
        **{field.name: getattr(record, field.name) for field in fields(record)}
    )
    with pytest.raises(journal.JournalError):
        journal.validate_accumulation_failure(foreign)


def test_external_snapshot_mutation_cannot_corrupt_owner_or_other_snapshots():
    journal = module()
    owner = journal._AccumulationOwner()
    owner.begin_pair("off_factory")
    original, exposed = owner.snapshot(), owner.snapshot()
    assert original is not exposed and original.off is not exposed.off
    object.__setattr__(exposed.off, "forwards", 16)
    object.__setattr__(exposed, "completed_pair", 12)
    with pytest.raises(journal.JournalError):
        journal.validate_accumulation_failure(exposed)
    assert owner.snapshot() == original
    owner.finish_pair("off_factory")
    assert owner.snapshot().completed_pair == 1


@pytest.mark.parametrize("index", [True, -1, 16, "0"])
def test_invalid_micro_index_is_rejected_without_advancing(index):
    journal = module()
    owner = journal._AccumulationOwner()
    pair(owner, "off_factory")
    pair(owner, "off_bindings")
    owner.begin_pair("off_observation")
    for phase in OBSERVE_START:
        nested(owner, owner.ticket("off"), phase)
    before = owner.snapshot()
    with pytest.raises(journal.JournalError):
        owner.begin_arm(owner.ticket("off"), "micro_forward", index)
    assert owner.snapshot() == before


def test_fault_markers_are_primitive_diagnostics_not_completion():
    journal = module()
    owner = journal._AccumulationOwner()
    owner.begin_pair("off_factory")
    record = replace(owner.snapshot(), journal_fault=True, cleanup_fault=True)
    assert journal.validate_accumulation_failure(record) is record
    assert record.completed_pair == 0
