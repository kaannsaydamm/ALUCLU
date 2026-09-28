from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from test_alc_r0_primevul_source import _bytes, _files, _row

from aluclu.alc_r0.primevul_pairs_source import (
    PrimeVulPairExpectation,
    PrimeVulPairSourceError,
    verify_primevul_development_pairs,
)


def _paired_files(
    directory: Path, train: bytes, validation: bytes
) -> PrimeVulPairExpectation:
    directory.mkdir()
    (directory / "primevul_train_paired.jsonl").write_bytes(train)
    (directory / "primevul_valid_paired.jsonl").write_bytes(validation)
    return PrimeVulPairExpectation(
        train_sha256=hashlib.sha256(train).hexdigest(),
        train_byte_length=len(train),
        train_pairs=train.count(b"\n") // 2,
        validation_sha256=hashlib.sha256(validation).hexdigest(),
        validation_byte_length=len(validation),
        validation_pairs=validation.count(b"\n") // 2,
    )


def test_verified_pair_graph_uses_components_not_independent_edges(
    tmp_path: Path,
) -> None:
    full = tmp_path / "full"
    paired = tmp_path / "paired"
    full.mkdir()
    positive = _row(1, "int vulnerable;", 1)
    benign_a = _row(2, "int patched_a;", 0)
    benign_b = _row(4, "int patched_b;", 0)
    valid_positive = _row(5, "int valid_vulnerable;", 1)
    valid_benign = _row(6, "int valid_patched;", 0)
    full_expectation = _files(
        full,
        _bytes([positive, benign_a, benign_b]),
        _bytes([valid_positive, valid_benign]),
        validation_positive=1,
    )
    pair_expectation = _paired_files(
        paired,
        _bytes([positive, benign_a, positive, benign_b]),
        _bytes([valid_positive, valid_benign]),
    )

    receipt = verify_primevul_development_pairs(
        full,
        paired,
        source_expectation=full_expectation,
        pair_expectation=pair_expectation,
    )

    assert receipt["status"] == "paired-development-verified-non-authorizing"
    assert receipt["training_authority"] is False
    assert receipt["held_out_data_present"] is False
    assert receipt["train_pairs"] == 2
    assert receipt["train_unique_source_ids"] == 3
    assert receipt["train_pair_component_sizes"] == {"3": 1}
    assert receipt["validation_pair_component_sizes"] == {"2": 1}


@pytest.mark.parametrize("mutation", ["same-label", "wrong-code", "duplicate-key"])
def test_bad_paired_development_fails_closed(tmp_path: Path, mutation: str) -> None:
    full = tmp_path / "full"
    paired = tmp_path / "paired"
    full.mkdir()
    positive = _row(1, "int vulnerable;", 1)
    benign = _row(2, "int patched;", 0)
    extra_positive = _row(3, "int also_vulnerable;", 1)
    valid_positive = _row(5, "int valid_vulnerable;", 1)
    valid_benign = _row(6, "int valid_patched;", 0)
    full_expectation = _files(
        full,
        _bytes([positive, benign, extra_positive]),
        _bytes([valid_positive, valid_benign]),
        train_positive=2,
        validation_positive=1,
    )
    second = benign.copy()
    if mutation == "same-label":
        second = extra_positive
    elif mutation == "wrong-code":
        second["func"] = "int different;"
    train = _bytes([positive, second])
    if mutation == "duplicate-key":
        train = train.replace(b'"idx": 1,', b'"idx": 1, "idx": 1,')
    pair_expectation = _paired_files(
        paired, train, _bytes([valid_positive, valid_benign])
    )

    with pytest.raises(PrimeVulPairSourceError):
        verify_primevul_development_pairs(
            full,
            paired,
            source_expectation=full_expectation,
            pair_expectation=pair_expectation,
        )


def test_extra_test_file_and_pinned_mutation_are_rejected(tmp_path: Path) -> None:
    full = tmp_path / "full"
    paired = tmp_path / "paired"
    full.mkdir()
    positive = _row(1, "int vulnerable;", 1)
    benign = _row(2, "int patched;", 0)
    valid_positive = _row(5, "int valid_vulnerable;", 1)
    valid_benign = _row(6, "int valid_patched;", 0)
    full_expectation = _files(
        full,
        _bytes([positive, benign]),
        _bytes([valid_positive, valid_benign]),
        validation_positive=1,
    )
    train = _bytes([positive, benign])
    pair_expectation = _paired_files(
        paired, train, _bytes([valid_positive, valid_benign])
    )
    (paired / "primevul_test_paired.jsonl").write_bytes(b"sealed")
    with pytest.raises(PrimeVulPairSourceError, match="exactly"):
        verify_primevul_development_pairs(
            full,
            paired,
            source_expectation=full_expectation,
            pair_expectation=pair_expectation,
        )
    (paired / "primevul_test_paired.jsonl").unlink()
    (paired / "primevul_train_paired.jsonl").write_bytes(
        train.replace(b"patched", b"changed")
    )
    with pytest.raises(PrimeVulPairSourceError, match="SHA-256"):
        verify_primevul_development_pairs(
            full,
            paired,
            source_expectation=full_expectation,
            pair_expectation=pair_expectation,
        )


def test_reused_pair_source_id_cannot_change_content(tmp_path: Path) -> None:
    full = tmp_path / "full"
    paired = tmp_path / "paired"
    full.mkdir()
    positive = _row(1, "int vulnerable;", 1)
    changed_positive = _row(1, "int changed_vulnerable;", 1)
    benign_a = _row(2, "int patched_a;", 0)
    benign_b = _row(3, "int patched_b;", 0)
    valid_positive = _row(5, "int valid_vulnerable;", 1)
    valid_benign = _row(6, "int valid_patched;", 0)
    full_expectation = _files(
        full,
        _bytes([positive, benign_a, benign_b]),
        _bytes([valid_positive, valid_benign]),
        validation_positive=1,
    )
    pair_expectation = _paired_files(
        paired,
        _bytes([positive, benign_a, changed_positive, benign_b]),
        _bytes([valid_positive, valid_benign]),
    )

    with pytest.raises(PrimeVulPairSourceError, match="reused source ID"):
        verify_primevul_development_pairs(
            full,
            paired,
            source_expectation=full_expectation,
            pair_expectation=pair_expectation,
        )
