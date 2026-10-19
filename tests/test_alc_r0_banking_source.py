from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from aluclu.alc_r0.banking_source import (
    BankingDevelopmentExpectation,
    BankingSourceError,
    load_verified_banking77_development,
)
from aluclu.alc_r0.canonical import canonical_json_bytes


def _git_blob(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def _expectation(root: Path) -> BankingDevelopmentExpectation:
    categories = (root / "categories.json").read_bytes()
    train = (root / "train.csv").read_bytes()
    return BankingDevelopmentExpectation(
        revision="a" * 40,
        categories_sha256=hashlib.sha256(categories).hexdigest(),
        categories_git_blob=_git_blob(categories),
        categories_byte_length=len(categories),
        train_sha256=hashlib.sha256(train).hexdigest(),
        train_git_blob=_git_blob(train),
        train_byte_length=len(train),
    )


def _source(tmp_path: Path) -> Path:
    root = tmp_path / "banking-development"
    root.mkdir()
    labels = [f"intent_{index:02d}" for index in range(77)]
    (root / "categories.json").write_bytes(
        json.dumps(labels, ensure_ascii=False).encode("utf-8")
    )
    text = io.StringIO(newline="")
    writer = csv.writer(text, lineterminator="\n")
    writer.writerow(["text", "category"])
    for label in labels:
        for index in range(5):
            writer.writerow([f"{label} request {index}", label])
    (root / "train.csv").write_bytes(text.getvalue().encode("utf-8"))
    return root


def test_verified_source_emits_content_bound_non_authorizing_receipt(
    tmp_path: Path,
) -> None:
    root = _source(tmp_path)
    result = load_verified_banking77_development(
        root.resolve(), expectation=_expectation(root)
    )

    assert len(result.labels) == 77
    assert len(result.split.train) == 308
    assert len(result.split.dev) == 77
    assert result.split.train[0].source_id.startswith("train:000000")
    receipt = result.receipt
    assert receipt["status"] == "candidate-non-authorizing"
    assert receipt["training_authority"] is False
    assert receipt["source_rows"] == 385
    assert receipt["source_id_scheme"] == (
        "train:<zero-padded eight-digit zero-based data-row ordinal>"
    )
    assert receipt["ordered_train_ids_sha256"] == result.split.ordered_train_ids_sha256
    assert receipt["ordered_dev_ids_sha256"] == result.split.ordered_dev_ids_sha256
    assert len(receipt["ordered_train_records_sha256"]) == 64
    assert len(receipt["ordered_dev_records_sha256"]) == 64
    serialized = canonical_json_bytes(receipt)
    assert str(tmp_path).encode("utf-8") not in serialized
    assert b"intent_00 request 0" not in serialized


def test_changed_source_bytes_fail_before_csv_parse(tmp_path: Path) -> None:
    root = _source(tmp_path)
    expectation = _expectation(root)
    with (root / "train.csv").open("ab") as stream:
        stream.write(b"\n")

    with pytest.raises(BankingSourceError, match="byte length"):
        load_verified_banking77_development(root.resolve(), expectation=expectation)


def test_git_blob_identity_is_checked_independently_of_sha256(tmp_path: Path) -> None:
    root = _source(tmp_path)
    expectation = _expectation(root)
    wrong = BankingDevelopmentExpectation(
        revision=expectation.revision,
        categories_sha256=expectation.categories_sha256,
        categories_git_blob="0" * 40,
        categories_byte_length=expectation.categories_byte_length,
        train_sha256=expectation.train_sha256,
        train_git_blob=expectation.train_git_blob,
        train_byte_length=expectation.train_byte_length,
    )
    with pytest.raises(BankingSourceError, match="Git blob"):
        load_verified_banking77_development(root.resolve(), expectation=wrong)


def test_development_source_rejects_test_file_and_extras(tmp_path: Path) -> None:
    root = _source(tmp_path)
    expectation = _expectation(root)
    (root / "test.csv").write_bytes(b"sealed")

    with pytest.raises(
        BankingSourceError, match="exactly categories.json and train.csv"
    ):
        load_verified_banking77_development(root.resolve(), expectation=expectation)


def test_bad_csv_header_rejected_even_when_bytes_match_expectation(
    tmp_path: Path,
) -> None:
    root = _source(tmp_path)
    train = (root / "train.csv").read_bytes()
    (root / "train.csv").write_bytes(
        train.replace(b"text,category", b"category,text", 1)
    )

    with pytest.raises(BankingSourceError, match="CSV header"):
        load_verified_banking77_development(
            root.resolve(), expectation=_expectation(root)
        )


def test_relative_root_and_noncanonical_labels_are_rejected(tmp_path: Path) -> None:
    root = _source(tmp_path)
    expectation = _expectation(root)
    with pytest.raises(BankingSourceError, match="absolute"):
        load_verified_banking77_development(Path("relative"), expectation=expectation)

    categories = json.loads((root / "categories.json").read_text(encoding="utf-8"))
    categories[0] = "Intent 00"
    (root / "categories.json").write_bytes(json.dumps(categories).encode("utf-8"))
    with pytest.raises(BankingSourceError, match="canonical label"):
        load_verified_banking77_development(
            root.resolve(), expectation=_expectation(root)
        )


def test_unterminated_csv_quote_fails_closed(tmp_path: Path) -> None:
    root = _source(tmp_path)
    train = (root / "train.csv").read_bytes()
    (root / "train.csv").write_bytes(train + b'"unterminated,intent_00\n')
    with pytest.raises(BankingSourceError, match="CSV"):
        load_verified_banking77_development(
            root.resolve(), expectation=_expectation(root)
        )


def test_uppercase_source_label_and_terminal_question_mark_canonicalize(
    tmp_path: Path,
) -> None:
    root = _source(tmp_path)
    categories = json.loads((root / "categories.json").read_text(encoding="utf-8"))
    categories[0] = "Intent_00"
    categories[1] = "intent_01?"
    (root / "categories.json").write_bytes(json.dumps(categories).encode("utf-8"))
    train = (root / "train.csv").read_bytes()
    train = train.replace(b",intent_00\n", b",Intent_00\n")
    train = train.replace(b",intent_01\n", b",intent_01?\n")
    (root / "train.csv").write_bytes(train)

    result = load_verified_banking77_development(
        root.resolve(), expectation=_expectation(root)
    )
    assert result.labels[:2] == ("intent_00", "intent_01?")
    assert {row.label for row in result.split.train + result.split.dev} == set(
        result.labels
    )
    assert result.receipt["label_canonicalization"] == (
        "ASCII lowercase of exact source category; terminal ? retained"
    )
