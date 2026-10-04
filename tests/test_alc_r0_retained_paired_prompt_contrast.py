from __future__ import annotations

import pytest
from test_alc_r0_paired_prompt_contrast import _ByteTokenizer
from test_alc_r0_primevul_pair_clone_full import _fixture

from aluclu.alc_r0.retained_paired_prompt_contrast import (
    classify_retained_pairs,
    run_retained_paired_prompt_contrast,
)


def test_pair_survival_partition_is_exhaustive_and_ordered() -> None:
    pairs = (
        ("primevul:1", "primevul:2", "v1", "s2"),
        ("primevul:3", "primevul:4", "v3", "s4"),
        ("primevul:5", "primevul:6", "v5", "s6"),
        ("primevul:7", "primevul:8", "v7", "s8"),
    )
    partition, survivors = classify_retained_pairs(
        pairs, {"primevul:1", "primevul:2", "primevul:3", "primevul:6"}
    )

    assert partition == {
        "author_pairs": 4,
        "both_retained": 1,
        "vulnerable_only_retained": 1,
        "safe_only_retained": 1,
        "neither_retained": 1,
    }
    assert survivors == (("v1", "s2"),)


def test_empty_survivor_cohort_is_explicit() -> None:
    partition, survivors = classify_retained_pairs(
        (("primevul:1", "primevul:2", "v", "s"),), set()
    )
    assert partition["both_retained"] == 0
    assert partition["neither_retained"] == 1
    assert survivors == ()


def test_fixture_runner_binds_graph_and_reports_only_aggregates(tmp_path) -> None:
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)
    receipt = run_retained_paired_prompt_contrast(
        full,
        paired,
        _ByteTokenizer(),
        model_inventory_sha256="a" * 64,
        budgets=(512, 1024),
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
    )

    assert receipt["source_scope"] == "fixture"
    assert receipt["train"]["survival"]["both_retained"] == 1
    assert receipt["validation"]["survival"]["both_retained"] == 1
    assert [row["max_common_tokens"] for row in receipt["train"]["budgets"]] == [
        512,
        1024,
    ]
    assert all(row["pairs"] == 1 for row in receipt["train"]["budgets"])
    assert receipt["training_authority"] is False
    assert receipt["held_out_data_present"] is False
    assert "red blue" not in str(receipt)
    assert "primevul:" not in str(receipt)


def test_runner_rejects_non_grid_or_partial_pinned_budget(tmp_path) -> None:
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)
    with pytest.raises(ValueError, match="budget"):
        run_retained_paired_prompt_contrast(
            full,
            paired,
            _ByteTokenizer(),
            model_inventory_sha256="a" * 64,
            budgets=(512, 1536),
            source_expectation=source_expectation,
            pair_expectation=pair_expectation,
        )


def test_runner_rejects_changed_pair_bytes(tmp_path) -> None:
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)
    path = paired / "primevul_train_paired.jsonl"
    path.write_bytes(path.read_bytes().replace(b"red", b"RED", 1))
    with pytest.raises(ValueError):
        run_retained_paired_prompt_contrast(
            full,
            paired,
            _ByteTokenizer(),
            model_inventory_sha256="a" * 64,
            budgets=(512,),
            source_expectation=source_expectation,
            pair_expectation=pair_expectation,
        )
