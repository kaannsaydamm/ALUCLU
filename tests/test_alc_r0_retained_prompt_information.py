from __future__ import annotations

import pytest
from test_alc_r0_paired_prompt_contrast import _ByteTokenizer
from test_alc_r0_primevul_pair_clone_full import _fixture

from aluclu.alc_r0.primevul_pair_clone_graph import PairCloneRecord
from aluclu.alc_r0.retained_prompt_information import (
    RetainedPromptInformationError,
    audit_retained_prompt_information,
    run_retained_prompt_information,
)


def _rows() -> tuple[PairCloneRecord, ...]:
    return (
        PairCloneRecord("primevul:1", "AAAA" + "x" * 20 + "ZZZZ", 1),
        PairCloneRecord("primevul:2", "AAAA" + "y" * 20 + "ZZZZ", 0),
        PairCloneRecord("primevul:3", "unique", 0),
        PairCloneRecord("primevul:4", "other", 1),
    )


def test_conflicting_complete_prompt_class_gives_exact_error_floor() -> None:
    roots = {
        "primevul:1": "primevul:1",
        "primevul:2": "primevul:1",
        "primevul:3": "primevul:3",
        "primevul:4": "primevul:4",
    }

    short = audit_retained_prompt_information(
        _rows(), roots, _ByteTokenizer(), max_tokens=59
    )
    long = audit_retained_prompt_information(
        _rows(), roots, _ByteTokenizer(), max_tokens=1024
    )

    assert short["retained_observations"] == 4
    assert short["labels"] == {"safe": 2, "vulnerable": 2}
    assert short["truncated"] == {"safe": 1, "vulnerable": 1}
    assert short["prompt_classes"] == 3
    assert short["opposite_label_prompt_classes"] == 1
    assert short["conflicted_observations"] == {"safe": 1, "vulnerable": 1}
    assert short["minimum_prompt_only_errors"] == 1
    assert short["affected_components"] == 1
    assert len(short["ordered_prompt_records_sha256"]) == 64
    assert long["prompt_classes"] == 4
    assert long["opposite_label_prompt_classes"] == 0
    assert long["minimum_prompt_only_errors"] == 0
    assert long["affected_components"] == 0
    assert "AAAA" not in str(short)
    assert "primevul:" not in str(short)


def test_order_changes_commitment_not_aggregate_counts() -> None:
    roots = {row.source_id: row.source_id for row in _rows()}
    ordered = audit_retained_prompt_information(
        _rows(), roots, _ByteTokenizer(), max_tokens=59
    )
    reversed_rows = audit_retained_prompt_information(
        tuple(reversed(_rows())), roots, _ByteTokenizer(), max_tokens=59
    )

    assert (
        ordered["minimum_prompt_only_errors"]
        == reversed_rows["minimum_prompt_only_errors"]
    )
    assert (
        ordered["ordered_prompt_records_sha256"]
        != reversed_rows["ordered_prompt_records_sha256"]
    )


def test_same_label_collision_has_no_irreducible_error() -> None:
    rows = (_rows()[0], PairCloneRecord("primevul:2", _rows()[1].function, 1))
    roots = {row.source_id: row.source_id for row in rows}

    receipt = audit_retained_prompt_information(
        rows, roots, _ByteTokenizer(), max_tokens=59
    )

    assert receipt["prompt_classes"] == 1
    assert receipt["opposite_label_prompt_classes"] == 0
    assert receipt["minimum_prompt_only_errors"] == 0


def test_changed_tokenization_of_first_duplicate_fails_closed() -> None:
    class _ChangingTokenizer(_ByteTokenizer):
        def __init__(self) -> None:
            self.first_code_calls = 0

        def encode(self, text: str, *, add_special_tokens: bool) -> list[int]:
            result = super().encode(text, add_special_tokens=add_special_tokens)
            if text.startswith("AAAA") and "x" * 20 in text:
                self.first_code_calls += 1
                if self.first_code_calls == 2:
                    result[0] += 1
            return result

    rows = _rows()[:2]
    roots = {row.source_id: row.source_id for row in rows}
    with pytest.raises(RetainedPromptInformationError, match="first prompt changed"):
        audit_retained_prompt_information(
            rows, roots, _ChangingTokenizer(), max_tokens=59
        )


@pytest.mark.parametrize(
    "rows,roots",
    [
        ((), {}),
        ((_rows()[0], _rows()[0]), {"primevul:1": "primevul:1"}),
        ((_rows()[0],), {}),
        ((PairCloneRecord("primevul:1", "x", True),), {"primevul:1": "primevul:1"}),
    ],
)
def test_invalid_cohort_fails_closed(rows, roots) -> None:
    with pytest.raises(RetainedPromptInformationError):
        audit_retained_prompt_information(rows, roots, _ByteTokenizer(), max_tokens=59)


def test_fixture_runner_binds_graph_and_emits_only_aggregates(tmp_path) -> None:
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)
    receipt = run_retained_prompt_information(
        full,
        paired,
        _ByteTokenizer(),
        model_inventory_sha256="a" * 64,
        budgets=(512, 1024),
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
    )

    assert receipt["source_scope"] == "fixture"
    assert receipt["retained_train_rows"] == 2
    assert receipt["retained_validation_rows"] == 2
    assert [row["max_common_tokens"] for row in receipt["train"]] == [512, 1024]
    assert all(row["retained_observations"] == 2 for row in receipt["train"])
    assert receipt["training_authority"] is False
    assert receipt["held_out_data_present"] is False
    assert "red blue" not in str(receipt)
    assert "primevul:" not in str(receipt)


def test_runner_rejects_partial_pinned_or_non_grid_budget(tmp_path) -> None:
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)
    with pytest.raises(RetainedPromptInformationError, match="budget"):
        run_retained_prompt_information(
            full,
            paired,
            _ByteTokenizer(),
            model_inventory_sha256="a" * 64,
            budgets=(512, 1536),
            source_expectation=source_expectation,
            pair_expectation=pair_expectation,
        )


def test_runner_rejects_changed_development_bytes(tmp_path) -> None:
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)
    path = full / "primevul_train.jsonl"
    path.write_bytes(path.read_bytes().replace(b"red", b"RED", 1))
    with pytest.raises(ValueError):
        run_retained_prompt_information(
            full,
            paired,
            _ByteTokenizer(),
            model_inventory_sha256="a" * 64,
            budgets=(512,),
            source_expectation=source_expectation,
            pair_expectation=pair_expectation,
        )


def test_runner_rechecks_source_after_prompt_scan(tmp_path) -> None:
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)
    source = full / "primevul_train.jsonl"

    def change_after_scan(split: str, budget: int, processed: int, total: int) -> None:
        if split == "validation" and budget == 512 and processed == total:
            source.write_bytes(source.read_bytes().replace(b"red", b"RED", 1))

    with pytest.raises(ValueError):
        run_retained_prompt_information(
            full,
            paired,
            _ByteTokenizer(),
            model_inventory_sha256="a" * 64,
            budgets=(512,),
            source_expectation=source_expectation,
            pair_expectation=pair_expectation,
            prompt_progress=change_after_scan,
        )
