"""Deterministic development preprocessing for the frozen Banking77 source.

This module accepts only the official *training* rows supplied by a separate,
audited acquisition step. It neither downloads data nor touches the sealed test
split, and its output alone does not authorize an R0.0 pass.
"""

from __future__ import annotations

import hashlib
import unicodedata
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from .canonical import canonical_json_bytes

_SPLIT_SEED = b"20260916"


class BankingPreprocessError(ValueError):
    """The training source or its deterministic partition violates the plan."""


@dataclass(frozen=True)
class BankingSourceRecord:
    source_id: str
    label: str
    utterance: str


@dataclass(frozen=True)
class BankingPreparedRecord:
    source_id: str
    label: str
    utterance: str
    normalized_sha256: str


@dataclass(frozen=True)
class BankingDevelopmentSplit:
    train: tuple[BankingPreparedRecord, ...]
    dev: tuple[BankingPreparedRecord, ...]
    removed_duplicate_count: int
    duplicate_root_sha256: str
    ordered_train_ids_sha256: str
    ordered_dev_ids_sha256: str


def normalize_banking_utterance(value: str) -> str:
    """Apply exactly the R0 Banking77 NFC, CRLF-to-LF, outer-strip policy."""

    if not isinstance(value, str):
        raise BankingPreprocessError("utterance must be text")
    return unicodedata.normalize("NFC", value).replace("\r\n", "\n").strip()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _utf8(value: str, *, field: str) -> bytes:
    try:
        return value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise BankingPreprocessError(f"{field} is not valid UTF-8 text") from exc


def _ordered_id_root(records: tuple[BankingPreparedRecord, ...]) -> str:
    return _sha256(canonical_json_bytes([record.source_id for record in records]))


def preprocess_banking77_train(
    records: Iterable[BankingSourceRecord], *, labels: tuple[str, ...]
) -> BankingDevelopmentSplit:
    """Deduplicate official-train records and derive the fixed per-label split.

    The supplied label tuple is the frozen canonical vocabulary order. No
    library RNG or input iteration order participates in the partition.
    """

    if (
        not isinstance(labels, tuple)
        or len(labels) != 77
        or any(not isinstance(label, str) or not label for label in labels)
        or len(set(labels)) != 77
    ):
        raise BankingPreprocessError("exactly 77 distinct canonical labels required")
    label_set = set(labels)
    by_digest: dict[str, list[BankingPreparedRecord]] = defaultdict(list)
    seen_ids: set[str] = set()
    for record in records:
        if not isinstance(record, BankingSourceRecord):
            raise BankingPreprocessError("source row must be a BankingSourceRecord")
        if not isinstance(record.source_id, str) or not record.source_id:
            raise BankingPreprocessError("source ID must be nonempty text")
        _utf8(record.source_id, field="source ID")
        if record.source_id in seen_ids:
            raise BankingPreprocessError("duplicate source ID")
        seen_ids.add(record.source_id)
        if not isinstance(record.label, str) or record.label not in label_set:
            raise BankingPreprocessError("source row has unknown canonical label")
        normalized = normalize_banking_utterance(record.utterance)
        if not normalized:
            raise BankingPreprocessError("normalized utterance is empty")
        digest = _sha256(_utf8(normalized, field="utterance"))
        by_digest[digest].append(
            BankingPreparedRecord(record.source_id, record.label, normalized, digest)
        )

    unique: dict[str, list[BankingPreparedRecord]] = {label: [] for label in labels}
    removed: list[dict[str, str]] = []
    for digest, group in by_digest.items():
        if len({item.label for item in group}) != 1:
            raise BankingPreprocessError("conflicting labels for normalized utterance")
        if len({item.utterance for item in group}) != 1:
            raise BankingPreprocessError("normalized utterance SHA-256 collision")
        ordered = sorted(
            group, key=lambda item: _utf8(item.source_id, field="source ID")
        )
        retained = ordered[0]
        unique[retained.label].append(retained)
        removed.extend(
            {
                "removed_source_id": item.source_id,
                "retained_source_id": retained.source_id,
                "normalized_sha256": digest,
            }
            for item in ordered[1:]
        )

    if any(not unique[label] for label in labels):
        raise BankingPreprocessError("each of the 77 labels needs a training row")
    removed.sort(key=lambda item: _utf8(item["removed_source_id"], field="source ID"))
    train: list[BankingPreparedRecord] = []
    dev: list[BankingPreparedRecord] = []
    for label in labels:
        label_bytes = _utf8(label, field="label")
        per_label = sorted(
            unique[label],
            key=lambda item: _sha256(
                _SPLIT_SEED
                + b"\x00"
                + label_bytes
                + b"\x00"
                + _utf8(item.utterance, field="utterance")
            ),
        )
        dev_count = len(per_label) // 5  # floor(0.20 * label_count)
        dev.extend(per_label[:dev_count])
        train.extend(per_label[dev_count:])

    train_records = tuple(train)
    dev_records = tuple(dev)
    return BankingDevelopmentSplit(
        train=train_records,
        dev=dev_records,
        removed_duplicate_count=len(removed),
        duplicate_root_sha256=_sha256(canonical_json_bytes(removed)),
        ordered_train_ids_sha256=_ordered_id_root(train_records),
        ordered_dev_ids_sha256=_ordered_id_root(dev_records),
    )
