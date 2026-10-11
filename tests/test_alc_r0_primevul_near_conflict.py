from __future__ import annotations

from pathlib import Path

import pytest
from test_alc_r0_primevul_source import _bytes, _files, _row

from aluclu.alc_r0.canonical import canonical_json_bytes
from aluclu.alc_r0.primevul_near_conflict import (
    PrimeVulNearConflictError,
    build_primevul_near_conflict_receipt,
)


def _near_pair() -> tuple[str, str]:
    left = [f"v{index:03d}" for index in range(200)]
    right = left.copy()
    right[50] = "changed"
    return " ".join(left), " ".join(right)


def test_opposite_label_near_pair_is_non_authorizing_failure(tmp_path: Path) -> None:
    left, right = _near_pair()
    train = _bytes([_row(7, left, 1), _row(11213, right, 0)])
    validation = _bytes([_row(19, "int unrelated;", 0)])
    expectation = _files(tmp_path, train, validation)

    receipt = build_primevul_near_conflict_receipt(
        tmp_path, left_id=7, right_id=11213, expectation=expectation
    )

    assert receipt["status"] == "failed-near-clone-label-conflict"
    assert receipt["training_authority"] is False
    assert receipt["held_out_data_present"] is False
    assert receipt["full_development_lsh_executed"] is False
    assert receipt["exact_conflict_groups"] == 0
    assert receipt["witness"]["left"]["label"] == 1
    assert receipt["witness"]["right"]["label"] == 0
    assert receipt["witness"]["common_lsh_bands"] >= 1
    assert (
        10 * receipt["witness"]["jaccard_intersection"]
        >= 9 * receipt["witness"]["jaccard_union"]
    )
    assert left not in canonical_json_bytes(receipt).decode("utf-8")


@pytest.mark.parametrize(
    ("right_code", "right_label", "match"),
    [
        ("same", 1, "opposite labels"),
        ("int unrelated;", 0, "Jaccard"),
    ],
)
def test_unqualified_pair_is_rejected(
    tmp_path: Path, right_code: str, right_label: int, match: str
) -> None:
    left, near = _near_pair()
    if right_code == "same":
        right_code = near
    train = _bytes([_row(7, left, 1), _row(11213, right_code, right_label)])
    validation = _bytes([_row(19, "int other;", 0)])
    expectation = _files(tmp_path, train, validation, train_positive=1 + right_label)

    with pytest.raises(PrimeVulNearConflictError, match=match):
        build_primevul_near_conflict_receipt(
            tmp_path, left_id=7, right_id=11213, expectation=expectation
        )


def test_missing_or_exact_conflict_witness_fails_closed(tmp_path: Path) -> None:
    left, _ = _near_pair()
    train = _bytes([_row(7, left, 1), _row(11213, left, 0)])
    validation = _bytes([_row(19, "int other;", 0)])
    expectation = _files(tmp_path, train, validation)

    with pytest.raises(PrimeVulNearConflictError, match="exact preflight"):
        build_primevul_near_conflict_receipt(
            tmp_path, left_id=7, right_id=11213, expectation=expectation
        )

    train = _bytes([_row(7, left, 1)])
    expectation = _files(tmp_path, train, validation)
    with pytest.raises(PrimeVulNearConflictError, match="missing"):
        build_primevul_near_conflict_receipt(
            tmp_path, left_id=7, right_id=11213, expectation=expectation
        )


def test_same_length_source_mutation_fails_before_witness(tmp_path: Path) -> None:
    left, right = _near_pair()
    train = _bytes([_row(7, left, 1), _row(11213, right, 0)])
    validation = _bytes([_row(19, "int unrelated;", 0)])
    expectation = _files(tmp_path, train, validation)
    (tmp_path / "primevul_train.jsonl").write_bytes(
        train.replace(b"changed", b"other__")
    )

    with pytest.raises(ValueError, match="SHA-256"):
        build_primevul_near_conflict_receipt(
            tmp_path, left_id=7, right_id=11213, expectation=expectation
        )
