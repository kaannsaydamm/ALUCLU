"""Token-only prospective parity fixtures; no tokenizer/model/data execution."""

import pytest

from aluclu.alc_r0.checkpoint_parity_inputs import ParityInputError, parity_input


def build(**changes):
    arguments = dict(
        prefix_ids=(10, 11),
        suffix_ids=(12,),
        safe_ids=(13,),
        vulnerable_ids=(14, 15),
        eos_token_id=0,
        common_length=32,
        label="safe",
        padded=False,
    )
    return parity_input(**(arguments | changes))


@pytest.mark.parametrize("length", [32, 64])
@pytest.mark.parametrize("label,candidate", [("safe", (13,)), ("vulnerable", (14, 15))])
def test_complete_candidate_and_reserved_common_prompt(length, label, candidate):
    result = build(common_length=length, label=label)
    code = tuple((index + 1) % 49151 + 1 for index in range(length - 5))
    prompt = (10, 11) + code + (12,)
    assert result.input_ids == prompt + candidate
    assert result.prompt_length == len(prompt)
    assert result.candidate_ids == candidate
    assert result.labels == (-100,) * len(prompt) + candidate
    assert result.attention_mask == (1,) * len(result.input_ids)
    assert result.position_ids == tuple(range(len(result.input_ids)))
    assert len(prompt) + 2 == length
    assert result.labels[result.prompt_length] == candidate[0]


@pytest.mark.parametrize("label", ["safe", "vulnerable"])
def test_right_padding_only_on_64_masks_every_padding_target(label):
    plain = build(common_length=64, label=label)
    padded = build(common_length=64, label=label, padded=True)
    assert padded.input_ids == plain.input_ids + (0,) * 7
    assert padded.labels == plain.labels + (-100,) * 7
    assert padded.attention_mask == plain.attention_mask + (0,) * 7
    assert padded.position_ids == tuple(range(len(padded.input_ids)))
    assert padded.prompt_length == plain.prompt_length
    assert padded.candidate_ids == plain.candidate_ids


@pytest.mark.parametrize(
    "changes",
    [
        {"common_length": True},
        {"common_length": 33},
        {"padded": 1},
        {"padded": True},
        {"label": "SAFE"},
        {"label": None},
        {"prefix_ids": ()},
        {"suffix_ids": []},
        {"safe_ids": (True,)},
        {"vulnerable_ids": (49152,)},
        {"eos_token_id": None},
        {"eos_token_id": True},
        {"safe_ids": (0,)},
        {"prefix_ids": tuple(range(1, 65))},
        {"safe_ids": (14, 15)},
        {"safe_ids": (float("nan"),)},
    ],
)
def test_invalid_or_infeasible_fixture_rejected(changes):
    with pytest.raises(ParityInputError):
        build(**changes)


def test_shared_framing_immutable_snapshot_and_frozen_result():
    result = build()
    with pytest.raises(AttributeError):
        result.input_ids = ()
    assert isinstance(result.input_ids, tuple)
    assert isinstance(result.labels, tuple)
