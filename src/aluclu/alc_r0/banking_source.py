"""Pinned Banking77 development-source verification and split receipt.

Only ``categories.json`` and official ``train.csv`` belong in this source
directory. The official test split is handled by a separate sealed evaluator.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .banking_preprocess import (
    BankingDevelopmentSplit,
    BankingPreparedRecord,
    BankingPreprocessError,
    BankingSourceRecord,
    preprocess_banking77_train,
)
from .canonical import canonical_json_bytes

_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_LABEL = re.compile(r"[a-z0-9_]+\??\Z")
_EXPECTED_NAMES = {"categories.json", "train.csv"}
_SOURCE_ID_SCHEME = "train:<zero-padded eight-digit zero-based data-row ordinal>"


class BankingSourceError(ValueError):
    """Pinned source bytes, schema, or development split are invalid."""


@dataclass(frozen=True)
class BankingDevelopmentExpectation:
    revision: str
    categories_sha256: str
    categories_git_blob: str
    categories_byte_length: int
    train_sha256: str
    train_git_blob: str
    train_byte_length: int

    def __post_init__(self) -> None:
        if not _HEX40.fullmatch(self.revision):
            raise BankingSourceError("revision must be a full lowercase Git commit")
        for value in (self.categories_sha256, self.train_sha256):
            if not _HEX64.fullmatch(value):
                raise BankingSourceError("expected SHA-256 must be lowercase 64-hex")
        for value in (self.categories_git_blob, self.train_git_blob):
            if not _HEX40.fullmatch(value):
                raise BankingSourceError("expected Git blob must be lowercase 40-hex")
        for value in (self.categories_byte_length, self.train_byte_length):
            if type(value) is not int or value <= 0:
                raise BankingSourceError("expected byte length must be positive")


BANKING77_DEVELOPMENT = BankingDevelopmentExpectation(
    revision="9d081458ff52e53cf7e848f414e6e9344e4e6696",
    categories_sha256="53261da888122daf2d120d925458631d9619e15d82e56052e7a42e535ce32b63",
    categories_git_blob="cdd2a5c77a4079a455f8fb7e751d1ecee0e2a5a4",
    categories_byte_length=2036,
    train_sha256="b06e26ac675513959a63135f11b94ea7786ed02da65db93a5650d8838cbc664b",
    train_git_blob="98e2543cf482d0dca7bfb175ebe35d98efad95be",
    train_byte_length=839073,
)


@dataclass(frozen=True)
class VerifiedBankingDevelopment:
    labels: tuple[str, ...]
    split: BankingDevelopmentSplit
    receipt: dict[str, Any]


def _git_blob(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _verified_bytes(path: Path, *, length: int, sha256: str, git_blob: str) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise BankingSourceError(f"required regular file missing: {path.name}")
    if path.stat().st_size != length:
        raise BankingSourceError(f"byte length mismatch: {path.name}")
    data = path.read_bytes()
    if len(data) != length:
        raise BankingSourceError(f"byte length changed during read: {path.name}")
    if hashlib.sha256(data).hexdigest() != sha256:
        raise BankingSourceError(f"SHA-256 mismatch: {path.name}")
    if _git_blob(data) != git_blob:
        raise BankingSourceError(f"Git blob mismatch: {path.name}")
    return data


def _decode_utf8(data: bytes, name: str) -> str:
    if data.startswith(b"\xef\xbb\xbf"):
        raise BankingSourceError(f"UTF-8 BOM forbidden: {name}")
    try:
        return data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise BankingSourceError(f"invalid UTF-8: {name}") from exc


def _parse_labels(data: bytes) -> tuple[tuple[str, ...], dict[str, str]]:
    try:
        value = json.loads(_decode_utf8(data, "categories.json"))
    except json.JSONDecodeError as exc:
        raise BankingSourceError("invalid categories JSON") from exc
    if not isinstance(value, list) or len(value) != 77:
        raise BankingSourceError("categories must contain 77 distinct canonical labels")
    if any(not isinstance(label, str) or not label.isascii() for label in value):
        raise BankingSourceError("categories must contain 77 distinct canonical labels")
    canonical = tuple(label.lower() for label in value)
    if (
        any(not _LABEL.fullmatch(label) for label in canonical)
        or len(set(value)) != 77
        or len(set(canonical)) != 77
    ):
        raise BankingSourceError("categories must contain 77 distinct canonical labels")
    return canonical, dict(zip(value, canonical, strict=True))


def _parse_train(
    data: bytes, raw_to_canonical: dict[str, str]
) -> tuple[BankingSourceRecord, ...]:
    text = _decode_utf8(data, "train.csv")
    rows: list[BankingSourceRecord] = []
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        if reader.fieldnames != ["text", "category"]:
            raise BankingSourceError("CSV header must be text,category")
        for ordinal, row in enumerate(reader):
            if (
                set(row) != {"text", "category"}
                or not isinstance(row["text"], str)
                or not isinstance(row["category"], str)
            ):
                raise BankingSourceError("CSV row has wrong column count")
            if row["category"] not in raw_to_canonical:
                raise BankingSourceError("CSV category is not in pinned categories")
            rows.append(
                BankingSourceRecord(
                    source_id=f"train:{ordinal:08d}",
                    label=raw_to_canonical[row["category"]],
                    utterance=row["text"],
                )
            )
    except csv.Error as exc:
        raise BankingSourceError("invalid CSV syntax") from exc
    if not rows:
        raise BankingSourceError("CSV has no training rows")
    return tuple(rows)


def _record_root(records: tuple[BankingPreparedRecord, ...]) -> str:
    leaves = [
        {
            "source_id": row.source_id,
            "label": row.label,
            "normalized_sha256": row.normalized_sha256,
        }
        for row in records
    ]
    return hashlib.sha256(canonical_json_bytes(leaves)).hexdigest()


def load_verified_banking77_development(
    root: Path,
    *,
    expectation: BankingDevelopmentExpectation = BANKING77_DEVELOPMENT,
) -> VerifiedBankingDevelopment:
    """Verify pinned raw bytes before parsing; never access an official test file."""

    if not root.is_absolute():
        raise BankingSourceError("development source root must be absolute")
    if root.is_symlink() or not root.is_dir():
        raise BankingSourceError("development source root must be a real directory")
    names = {entry.name for entry in root.iterdir()}
    if names != _EXPECTED_NAMES:
        raise BankingSourceError(
            "development directory must contain exactly categories.json and train.csv"
        )
    categories = _verified_bytes(
        root / "categories.json",
        length=expectation.categories_byte_length,
        sha256=expectation.categories_sha256,
        git_blob=expectation.categories_git_blob,
    )
    train = _verified_bytes(
        root / "train.csv",
        length=expectation.train_byte_length,
        sha256=expectation.train_sha256,
        git_blob=expectation.train_git_blob,
    )
    labels, raw_to_canonical = _parse_labels(categories)
    rows = _parse_train(train, raw_to_canonical)
    try:
        split = preprocess_banking77_train(rows, labels=labels)
    except BankingPreprocessError as exc:
        raise BankingSourceError(f"invalid development split: {exc}") from exc
    receipt: dict[str, Any] = {
        "receipt_version": 1,
        "status": "candidate-non-authorizing",
        "training_authority": False,
        "source_repository": "PolyAI-LDN/task-specific-datasets",
        "source_subtree": "banking_data/",
        "source_revision": expectation.revision,
        "upstream_license_declaration": "CC-BY-4.0",
        "files": [
            {
                "path": "banking_data/categories.json",
                "byte_length": len(categories),
                "sha256": expectation.categories_sha256,
                "git_blob": expectation.categories_git_blob,
            },
            {
                "path": "banking_data/train.csv",
                "byte_length": len(train),
                "sha256": expectation.train_sha256,
                "git_blob": expectation.train_git_blob,
            },
        ],
        "label_count": len(labels),
        "ordered_labels_sha256": hashlib.sha256(
            canonical_json_bytes(labels)
        ).hexdigest(),
        "label_canonicalization": (
            "ASCII lowercase of exact source category; terminal ? retained"
        ),
        "source_id_scheme": _SOURCE_ID_SCHEME,
        "source_rows": len(rows),
        "removed_duplicate_count": split.removed_duplicate_count,
        "duplicate_root_sha256": split.duplicate_root_sha256,
        "train_rows": len(split.train),
        "dev_rows": len(split.dev),
        "ordered_train_ids_sha256": split.ordered_train_ids_sha256,
        "ordered_dev_ids_sha256": split.ordered_dev_ids_sha256,
        "ordered_train_records_sha256": _record_root(split.train),
        "ordered_dev_records_sha256": _record_root(split.dev),
    }
    return VerifiedBankingDevelopment(labels, split, receipt)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("development_source_dir", type=Path)
    args = parser.parse_args()
    result = load_verified_banking77_development(args.development_source_dir)
    sys.stdout.buffer.write(canonical_json_bytes(result.receipt) + b"\n")


if __name__ == "__main__":
    main()
