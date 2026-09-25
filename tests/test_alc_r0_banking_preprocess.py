from __future__ import annotations

import hashlib

import pytest

from aluclu.alc_r0.banking_preprocess import (
    BankingPreprocessError,
    BankingSourceRecord,
    normalize_banking_utterance,
    preprocess_banking77_train,
)
from aluclu.alc_r0.canonical import canonical_json_bytes

LABELS = tuple(f"intent_{index:02d}" for index in range(77))


def _source() -> list[BankingSourceRecord]:
    return [
        BankingSourceRecord(
            source_id=f"{label}-{index}",
            label=label,
            utterance=f"{label} request {index}",
        )
        for label in LABELS
        for index in range(5)
    ]


def test_normalization_is_nfc_crlf_to_lf_and_outer_strip_only() -> None:
    assert normalize_banking_utterance("  cafe\u0301\r\n next  ") == "café\n next"
    assert normalize_banking_utterance("a  b") == "a  b"
    assert normalize_banking_utterance("x\ry") == "x\ry"


def test_exact_77_label_split_is_deterministic_and_keeps_source_order_out() -> None:
    records = _source()
    first = preprocess_banking77_train(records, labels=LABELS)
    reversed_input = preprocess_banking77_train(list(reversed(records)), labels=LABELS)

    assert first == reversed_input
    assert len(first.train) == 308
    assert len(first.dev) == 77
    assert first.removed_duplicate_count == 0
    assert {record.label for record in first.dev} == set(LABELS)
    assert all(
        record.normalized_sha256
        == hashlib.sha256(record.utterance.encode("utf-8")).hexdigest()
        for record in first.train + first.dev
    )
    assert first.dev[0].source_id == "intent_00-3"  # frozen hash-order fixture
    assert [record.source_id for record in first.train[:4]] == [
        "intent_00-2",
        "intent_00-0",
        "intent_00-4",
        "intent_00-1",
    ]
    assert first.ordered_train_ids_sha256 == (
        "33fba07c9c9f0e48180dce76045bda2c50278320ffe8c7aead7635f078246f7e"
    )
    assert first.ordered_dev_ids_sha256 == (
        "254cffa60eade366ec3bc533f696e47c66609a43ba11509f0d9151f7e68b2b80"
    )
    assert (
        first.duplicate_root_sha256
        == hashlib.sha256(canonical_json_bytes([])).hexdigest()
    )
    assert (
        first.ordered_train_ids_sha256
        == hashlib.sha256(
            canonical_json_bytes([record.source_id for record in first.train])
        ).hexdigest()
    )


def test_same_label_duplicate_keeps_lexicographically_smallest_id() -> None:
    records = _source()
    records.extend(
        [
            BankingSourceRecord("zzz", "intent_00", " cafe\u0301\r\n "),
            BankingSourceRecord("aaa", "intent_00", "café"),
        ]
    )
    result = preprocess_banking77_train(records, labels=LABELS)

    assert result.removed_duplicate_count == 1
    assert "aaa" in {record.source_id for record in result.train + result.dev}
    assert "zzz" not in {record.source_id for record in result.train + result.dev}
    expected_removed = [
        {
            "removed_source_id": "zzz",
            "retained_source_id": "aaa",
            "normalized_sha256": hashlib.sha256("café".encode()).hexdigest(),
        }
    ]
    assert (
        result.duplicate_root_sha256
        == hashlib.sha256(canonical_json_bytes(expected_removed)).hexdigest()
    )


def test_conflicting_labels_for_same_normalized_utterance_fail_closed() -> None:
    records = _source()
    records.extend(
        [
            BankingSourceRecord("a", "intent_00", "cafe\u0301"),
            BankingSourceRecord("b", "intent_01", "café"),
        ]
    )
    with pytest.raises(BankingPreprocessError, match="conflicting labels"):
        preprocess_banking77_train(records, labels=LABELS)


@pytest.mark.parametrize(
    "bad",
    [
        BankingSourceRecord("", "intent_00", "hello"),
        BankingSourceRecord("new", "unknown", "hello"),
        BankingSourceRecord("new", "intent_00", "   "),
        BankingSourceRecord("new", "intent_00", "\ud800"),
    ],
)
def test_invalid_source_record_is_rejected(bad: BankingSourceRecord) -> None:
    with pytest.raises(BankingPreprocessError):
        preprocess_banking77_train([*_source(), bad], labels=LABELS)


def test_duplicate_source_id_and_incomplete_label_vocabulary_fail_closed() -> None:
    records = _source()
    with pytest.raises(BankingPreprocessError, match="duplicate source ID"):
        preprocess_banking77_train([*records, records[0]], labels=LABELS)
    with pytest.raises(BankingPreprocessError, match="77"):
        preprocess_banking77_train(records, labels=LABELS[:-1])
