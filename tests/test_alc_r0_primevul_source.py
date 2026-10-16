from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from aluclu.alc_r0.primevul_source import (
    PrimeVulDevelopmentExpectation,
    PrimeVulSourceError,
    verify_primevul_development,
)


def _row(number: int, code: str, label: int) -> dict[str, object]:
    return {
        "idx": number,
        "func": code,
        "target": label,
        "project": "qemu",
        "commit_id": "0" * 40,
        "hash": number + 10,
    }


def _bytes(rows: list[dict[str, object]]) -> bytes:
    return (
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n"
    ).encode("utf-8")


def _files(
    directory: Path,
    train: bytes,
    validation: bytes,
    *,
    train_positive: int = 1,
    validation_positive: int = 0,
) -> PrimeVulDevelopmentExpectation:
    (directory / "primevul_train.jsonl").write_bytes(train)
    (directory / "primevul_valid.jsonl").write_bytes(validation)
    return PrimeVulDevelopmentExpectation(
        train_sha256=hashlib.sha256(train).hexdigest(),
        train_byte_length=len(train),
        train_rows=train.count(b"\n"),
        train_positive=train_positive,
        validation_sha256=hashlib.sha256(validation).hexdigest(),
        validation_byte_length=len(validation),
        validation_rows=validation.count(b"\n"),
        validation_positive=validation_positive,
    )


def test_verified_candidate_counts_exact_clones_without_training_authority(
    tmp_path: Path,
) -> None:
    train = _bytes(
        [
            _row(1, "int x = 1;", 1),
            _row(2, "int x = 1;", 1),
            _row(3, "int y = 2;", 0),
        ]
    )
    validation = _bytes([_row(4, "int x = 1;", 0)])
    expectation = _files(tmp_path, train, validation, train_positive=2)

    receipt = verify_primevul_development(tmp_path, expectation=expectation)

    assert receipt["status"] == "failed-exact-label-conflicts"
    assert receipt["exact_conflict_groups"] == 1
    assert receipt["exact_duplicate_groups"] == 1
    assert receipt["exact_validation_overlap_groups"] == 1
    assert receipt["training_authority"] is False
    assert receipt["held_out_data_present"] is False


def test_clean_exact_clone_candidate_is_not_an_r0_pass(tmp_path: Path) -> None:
    train = _bytes([_row(1, "int x = 1;", 1), _row(2, "int x = 1;", 1)])
    validation = _bytes([_row(3, "int y = 2;", 0)])
    expectation = _files(tmp_path, train, validation, train_positive=2)

    receipt = verify_primevul_development(tmp_path, expectation=expectation)

    assert receipt["status"] == "candidate-non-authorizing"
    assert receipt["exact_normalized_groups"] == 2
    assert receipt["exact_conflict_groups"] == 0
    assert receipt["lsh_executed"] is False
    assert receipt["training_authority"] is False


def test_test_file_and_same_size_mutation_are_rejected(tmp_path: Path) -> None:
    train = _bytes([_row(1, "int x = 1;", 1)])
    validation = _bytes([_row(2, "int y = 2;", 0)])
    expectation = _files(tmp_path, train, validation)
    (tmp_path / "primevul_test.jsonl").write_bytes(b"test stays sealed")
    with pytest.raises(PrimeVulSourceError, match="exactly train and validation"):
        verify_primevul_development(tmp_path, expectation=expectation)
    (tmp_path / "primevul_test.jsonl").unlink()
    (tmp_path / "primevul_train.jsonl").write_bytes(
        train.replace(b"int x = 1;", b"int z = 1;")
    )
    with pytest.raises(PrimeVulSourceError, match="SHA-256"):
        verify_primevul_development(tmp_path, expectation=expectation)


@pytest.mark.parametrize(
    "bad_train",
    [
        b'{"idx":1,"idx":2,"func":"int x;","target":1,"project":"qemu","commit_id":"c","hash":1}\n',
        b"\xff\n",
        _bytes([_row(1, "int x;", 2)]),
    ],
)
def test_malformed_source_fails_closed(tmp_path: Path, bad_train: bytes) -> None:
    validation = _bytes([_row(2, "int y;", 0)])
    expectation = _files(tmp_path, bad_train, validation)

    with pytest.raises(PrimeVulSourceError):
        verify_primevul_development(tmp_path, expectation=expectation)


def test_cross_split_source_id_collision_fails_closed(tmp_path: Path) -> None:
    train = _bytes([_row(1, "int x;", 1)])
    validation = _bytes([_row(1, "int y;", 0)])
    expectation = _files(tmp_path, train, validation)

    with pytest.raises(PrimeVulSourceError, match="source ID"):
        verify_primevul_development(tmp_path, expectation=expectation)
