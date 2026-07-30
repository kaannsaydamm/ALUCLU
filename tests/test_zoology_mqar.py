import json
from dataclasses import replace
from importlib.resources import files

import numpy as np
import pytest
import torch

from aluclu import (
    ZOOLOGY_ICLR24_COMMIT,
    ZOOLOGY_ICLR24_RAW_PROTOCOL_ID,
    ZOOLOGY_ICLR24_REPAIRED_PROTOCOL_ID,
    ZOOLOGY_MQAR_IGNORE_INDEX,
    ZoologyMQARConfig,
    generate_mqar_batch,
    generate_zoology_mqar_batch,
    zoology_mqar_accuracy,
    zoology_mqar_loss,
)


def upstream_tagged_reference(
    config: ZoologyMQARConfig,
) -> tuple[torch.Tensor, torch.Tensor]:
    np.random.seed(config.seed)
    context_size = config.num_kv_pairs * 2
    key_vocab_size = config.vocab_size // 2
    key_choices = np.arange(1, key_vocab_size)
    value_choices = np.arange(key_vocab_size, config.vocab_size)

    keys_unshuffled = np.tile(key_choices, (config.num_examples, 1))
    keys = np.apply_along_axis(
        np.random.choice,
        1,
        keys_unshuffled,
        replace=False,
        size=config.num_kv_pairs,
    )
    values_unshuffled = np.tile(value_choices, (config.num_examples, 1))
    values = np.apply_along_axis(
        np.random.choice,
        1,
        values_unshuffled,
        replace=False,
        size=config.num_kv_pairs,
    )

    key_values = np.zeros(
        (config.num_examples, context_size),
        dtype=np.int64,
    )
    key_values[:, 0::2] = keys
    key_values[:, 1::2] = values
    space = (config.input_seq_len - context_size) // 2
    probability = config.power_a * (np.arange(1, space + 1) ** (config.power_a - 1))
    probability = probability / probability.sum()
    positions = np.stack([np.arange(space, dtype=int)] * config.num_examples)
    gaps = np.apply_along_axis(
        np.random.choice,
        axis=1,
        arr=positions,
        replace=False,
        p=probability,
        size=config.num_kv_pairs,
    )

    queries = np.zeros(
        (config.num_examples, config.input_seq_len - context_size + 1),
        dtype=np.int64,
    )
    np.put_along_axis(queries, gaps * 2, values=keys, axis=1)
    examples = np.concatenate((key_values, queries), axis=1)
    labels = np.full(
        (config.num_examples, config.input_seq_len + 1),
        ZOOLOGY_MQAR_IGNORE_INDEX,
        dtype=np.int64,
    )
    np.put_along_axis(
        labels,
        gaps * 2 + context_size + 1,
        values=values,
        axis=1,
    )
    input_ids = torch.tensor(examples[:, :-1])
    label_tensor = torch.tensor(labels[:, 1:])
    if config.random_non_queries:
        zero_mask = input_ids == 0
        input_ids[zero_mask] = torch.randint(
            config.vocab_size,
            size=input_ids.shape,
        )[zero_mask]
    return input_ids, label_tensor


def compact_config(**overrides: object) -> ZoologyMQARConfig:
    config = ZoologyMQARConfig(
        num_examples=4,
        input_seq_len=16,
        num_kv_pairs=3,
        vocab_size=64,
        seed=7,
        power_a=0.01,
        random_non_queries=False,
    )
    return replace(config, **overrides)


@pytest.mark.parametrize(
    ("input_seq_len", "num_kv_pairs"),
    [(64, 4), (128, 8), (256, 16), (512, 64)],
)
def test_generator_matches_tagged_upstream_arrays(
    input_seq_len: int,
    num_kv_pairs: int,
) -> None:
    config = ZoologyMQARConfig(
        num_examples=3,
        input_seq_len=input_seq_len,
        num_kv_pairs=num_kv_pairs,
        vocab_size=8_192,
        seed=0,
        power_a=0.01,
        random_non_queries=False,
    )
    expected_inputs, expected_labels = upstream_tagged_reference(config)
    actual = generate_zoology_mqar_batch(config)
    torch.testing.assert_close(actual.input_ids, expected_inputs, rtol=0, atol=0)
    torch.testing.assert_close(actual.labels, expected_labels, rtol=0, atol=0)


def test_labels_are_aligned_at_query_positions_without_an_extra_shift() -> None:
    config = compact_config()
    batch = generate_zoology_mqar_batch(config)
    context_keys = batch.input_ids[:, : config.context_size : 2]
    context_values = batch.input_ids[:, 1 : config.context_size : 2]

    torch.testing.assert_close(
        batch.input_ids.gather(1, batch.query_positions),
        context_keys,
    )
    torch.testing.assert_close(batch.answer_tokens, context_values)
    torch.testing.assert_close(
        batch.labels.gather(1, batch.query_positions),
        batch.answer_tokens,
    )
    assert torch.all(
        batch.labels.gather(1, batch.query_positions + 1) == ZOOLOGY_MQAR_IGNORE_INDEX
    )
    assert torch.equal(
        batch.loss_mask,
        batch.labels != ZOOLOGY_MQAR_IGNORE_INDEX,
    )
    assert torch.equal(
        batch.loss_mask.sum(dim=1),
        torch.full((config.num_examples,), config.num_kv_pairs),
    )


def test_generation_is_deterministic_and_test_seed_is_distinct() -> None:
    config = compact_config()
    first = generate_zoology_mqar_batch(config)
    second = generate_zoology_mqar_batch(config)
    test_split = generate_zoology_mqar_batch(replace(config, seed=config.seed + 10))

    assert torch.equal(first.input_ids, second.input_ids)
    assert torch.equal(first.labels, second.labels)
    assert not torch.equal(first.input_ids, test_split.input_ids)


def test_optional_random_filler_matches_upstream_torch_operation() -> None:
    config = compact_config(random_non_queries=True)
    torch.manual_seed(81)
    expected_inputs, expected_labels = upstream_tagged_reference(config)
    torch.manual_seed(81)
    actual = generate_zoology_mqar_batch(config)

    assert torch.equal(actual.input_ids, expected_inputs)
    assert torch.equal(actual.labels, expected_labels)


@pytest.mark.parametrize(
    ("field", "value", "exception"),
    [
        ("num_examples", 0, ValueError),
        ("input_seq_len", 15, ValueError),
        ("num_kv_pairs", 5, ValueError),
        ("vocab_size", 16, ValueError),
        ("seed", -1, ValueError),
        ("seed", 2**32, ValueError),
        ("power_a", 0.0, ValueError),
        ("power_a", float("nan"), ValueError),
        ("power_a", True, TypeError),
        ("random_non_queries", 1, TypeError),
    ],
)
def test_config_rejects_invalid_protocol_values(
    field: str,
    value: object,
    exception: type[Exception],
) -> None:
    with pytest.raises(exception):
        compact_config(**{field: value})


def test_raw_and_repaired_manifests_are_distinct_and_honest() -> None:
    protocol_root = files("aluclu.protocols")
    raw_path = protocol_root / "zoology_iclr24_raw.json"
    repaired_path = protocol_root / "zoology_iclr24_repaired_v1.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    repaired = json.loads(repaired_path.read_text(encoding="utf-8"))

    assert raw["protocol_id"] == ZOOLOGY_ICLR24_RAW_PROTOCOL_ID
    assert repaired["protocol_id"] == ZOOLOGY_ICLR24_REPAIRED_PROTOCOL_ID
    assert raw["protocol_id"] != repaired["protocol_id"]
    assert raw["provenance"]["commit_sha"] == ZOOLOGY_ICLR24_COMMIT
    assert raw["execution_status"] == "source_snapshot_not_uniformly_executable"
    assert raw["labels"]["alignment"] == "same_position_as_query_token"
    assert raw["labels"]["additional_causal_shift"] is False
    assert raw["training"]["seed_count"] == 1
    assert raw["data"]["data_seed"] == 0
    assert raw["data"]["test_seed_offset"] == 10
    assert raw["data"]["random_non_queries"] is False
    assert [
        (point["input_seq_len"], point["num_kv_pairs"], point["batch_size"])
        for point in raw["data"]["points"]
    ] == [
        (64, 4, 512),
        (128, 8, 512),
        (256, 16, 256),
        (512, 64, 128),
    ]
    assert len(raw["training"]["learning_rate_grid"]) == 4

    defect = raw["known_defects"][0]
    assert defect["id"] == "based_hybrid_depth_config_mismatch"
    assert raw["models"]["based_hybrid"]["requested_layers"] == 4
    assert raw["models"]["based_hybrid"]["mixer_config_count"] == 2

    assert repaired["derived_from"]["protocol_id"] == raw["protocol_id"]
    assert repaired["repair"]["before"]["requested_layers"] == 4
    assert repaired["repair"]["after"]["requested_layers"] == 2
    assert repaired["resolved_depth_policy"]["based"] == 2
    assert "must not be labeled" in repaired["repair"]["methodological_consequence"]


def test_historical_generator_is_separate_from_diagnostic_mqar() -> None:
    assert generate_zoology_mqar_batch is not generate_mqar_batch
    assert ZOOLOGY_ICLR24_RAW_PROTOCOL_ID.startswith("aluclu_")


def test_same_position_loss_and_accuracy_do_not_shift_targets() -> None:
    batch = generate_zoology_mqar_batch(compact_config())
    logits = torch.full(
        (*batch.input_ids.shape, batch.config.vocab_size),
        -20.0,
    )
    row = torch.arange(batch.input_ids.shape[0]).unsqueeze(1)
    logits[row, batch.query_positions, batch.answer_tokens] = 20.0

    assert zoology_mqar_accuracy(logits, batch).item() == 1.0
    assert zoology_mqar_loss(logits, batch).item() < 1e-6

    shifted = torch.roll(logits, shifts=1, dims=1)
    assert zoology_mqar_accuracy(shifted, batch).item() < 1.0
    assert zoology_mqar_loss(shifted, batch) > zoology_mqar_loss(logits, batch)
