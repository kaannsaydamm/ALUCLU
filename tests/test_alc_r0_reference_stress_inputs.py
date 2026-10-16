"""Pure synthetic token checks; no tokenizer/host/GPU or E3 acceptance."""

from dataclasses import FrozenInstanceError, replace

import pytest

from aluclu.alc_r0.reference_stress_inputs import (
    StressInputError,
    build_stress_schedule,
    stress_schedule_sha256,
    validate_stress_schedule,
)


def build(**changes):
    arguments = dict(
        prefix_ids=(7, 8), suffix_ids=(9,), safe_ids=(10,), vulnerable_ids=(11, 12)
    )
    return build_stress_schedule(**(arguments | changes))


def test_fixed_schedule_complete_supervision_and_unequal_lengths():
    schedule = build()
    validate_stress_schedule(schedule)
    assert len(schedule.inputs) == 16
    assert [item.label for item in schedule.inputs] == ["safe", "vulnerable"] * 8
    for index, item in enumerate(schedule.inputs):
        candidate = (10,) if index % 2 == 0 else (11, 12)
        assert len(item.input_ids) == 4095 + index % 2
        assert item.prompt_length == 4094
        assert item.candidate_ids == candidate
        assert item.labels == (-100,) * 4094 + candidate
        assert item.attention_mask == (1,) * len(item.input_ids)
        assert item.position_ids == tuple(range(len(item.input_ids)))
        assert item.input_ids[:2] == (7, 8)
        assert item.input_ids[2:4093] == tuple((i + 1) % 49151 + 1 for i in range(4091))
        assert item.input_ids[4093:4094] == (9,)
        assert item.input_ids[4094:] == candidate
    assert schedule.inputs[0].input_ids[:4094] == schedule.inputs[1].input_ids[:4094]
    assert stress_schedule_sha256(schedule) == stress_schedule_sha256(build())
    assert stress_schedule_sha256(schedule) != stress_schedule_sha256(
        build(safe_ids=(13,))
    )
    with pytest.raises(FrozenInstanceError):
        schedule.inputs = ()
    with pytest.raises(FrozenInstanceError):
        schedule.inputs[0].label = "vulnerable"


@pytest.mark.parametrize(
    "field", ["prefix_ids", "suffix_ids", "safe_ids", "vulnerable_ids"]
)
@pytest.mark.parametrize(
    "bad", [(), [], (True,), (0,), (-1,), (49152,), (1.0,), ("1",), (1,) * 65]
)
def test_bad_supplied_tokens_rejected(field, bad):
    with pytest.raises(StressInputError):
        build(**{field: bad})


def test_equal_candidates_rejected_and_maximum_bounded_inputs_complete():
    with pytest.raises(StressInputError):
        build(safe_ids=(1,), vulnerable_ids=(1,))
    schedule = build(
        prefix_ids=(1,) * 64,
        suffix_ids=(2,) * 64,
        safe_ids=(3,) * 64,
        vulnerable_ids=(4,) * 64,
    )
    validate_stress_schedule(schedule)
    assert all(len(item.input_ids) == 4096 for item in schedule.inputs)
    assert all(item.prompt_length == 4032 for item in schedule.inputs)


@pytest.mark.parametrize(
    "bad",
    [
        "count",
        "list",
        "foreign",
        "order",
        "label",
        "bool_prompt",
        "ids",
        "labels",
        "mask",
        "position",
        "candidate",
        "oversized",
        "mutable",
        "bool_id",
        "framing",
    ],
)
def test_forged_schedules_rejected_before_digest(bad):
    schedule = build()
    first = schedule.inputs[0]
    if bad == "count":
        schedule = replace(schedule, inputs=schedule.inputs[:-1])
    elif bad == "list":
        schedule = replace(schedule, inputs=list(schedule.inputs))
    elif bad == "foreign":
        schedule = object()
    elif bad == "order":
        schedule = replace(schedule, inputs=tuple(reversed(schedule.inputs)))
    elif bad == "framing":
        schedule = replace(schedule, prefix_ids=(15,))
    else:
        changes = {
            "label": {"label": "vulnerable"},
            "bool_prompt": {"prompt_length": True},
            "ids": {"input_ids": (13,) + first.input_ids[1:]},
            "labels": {"labels": first.labels[:-1] + (-100,)},
            "mask": {"attention_mask": (0,) + first.attention_mask[1:]},
            "position": {"position_ids": tuple(reversed(first.position_ids))},
            "candidate": {"candidate_ids": (14,)},
            "oversized": {"input_ids": (1,) * 4097},
            "mutable": {"labels": list(first.labels)},
            "bool_id": {"input_ids": (True,) + first.input_ids[1:]},
        }[bad]
        schedule = replace(
            schedule, inputs=(replace(first, **changes),) + schedule.inputs[1:]
        )
    with pytest.raises(StressInputError):
        validate_stress_schedule(schedule)
    with pytest.raises(StressInputError):
        stress_schedule_sha256(schedule)
