"""Development-only qualification of PrimeVul's author-provided pair files.

The paired test file is neither needed nor permitted. Verified pairs are
metadata for protocol design, not a preregistration amendment or training gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canonical import canonical_json_bytes, sha256_bytes
from .primevul_source import (
    PRIMEVUL_ORIGINAL_DEVELOPMENT,
    PrimeVulDevelopmentExpectation,
    PrimeVulSourceError,
    _reject_constant,
    _unique_object,
    verify_primevul_development,
)

_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_PAIR_NAMES = {"primevul_train_paired.jsonl", "primevul_valid_paired.jsonl"}
_FOLDER_ID = "19iLaNDS0z99N8kB_jBRTmDLehwZBolMY"
_TRAIN_ID = "1CYE_AZdZTIHPepOIxmPNZtMPdwB6cEt1"
_VALIDATION_ID = "1UBoDzBD9tXAieRlXYjjB-2HpPf9I83mg"


class PrimeVulPairSourceError(ValueError):
    """A paired development file violates its pinned source contract."""


@dataclass(frozen=True)
class PrimeVulPairExpectation:
    train_sha256: str
    train_byte_length: int
    train_pairs: int
    validation_sha256: str
    validation_byte_length: int
    validation_pairs: int

    def __post_init__(self) -> None:
        if not _HEX64.fullmatch(self.train_sha256) or not _HEX64.fullmatch(
            self.validation_sha256
        ):
            raise PrimeVulPairSourceError("expected SHA-256 must be lowercase 64-hex")
        for size, pairs in (
            (self.train_byte_length, self.train_pairs),
            (self.validation_byte_length, self.validation_pairs),
        ):
            if type(size) is not int or size < 1 or type(pairs) is not int or pairs < 1:
                raise PrimeVulPairSourceError("invalid paired source expectation")


PRIMEVUL_ORIGINAL_PAIRS = PrimeVulPairExpectation(
    train_sha256="22d2f27ffda164d7de81f870f6a4907c66df2338f6a9fd01ee2300d7fb34f965",
    train_byte_length=52076348,
    train_pairs=4354,
    validation_sha256="33b18631d7b5c075ee143527176fddf2180648901ed40952553d99f744c6c74f",
    validation_byte_length=5867872,
    validation_pairs=562,
)


def _decode_row(raw: bytes) -> dict[str, Any]:
    if not raw.endswith(b"\n"):
        raise PrimeVulPairSourceError("paired JSONL line must end with LF")
    try:
        row = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, PrimeVulSourceError) as exc:
        raise PrimeVulPairSourceError("invalid paired UTF-8 JSONL row") from exc
    if (
        not isinstance(row, dict)
        or not {
            "idx",
            "func",
            "target",
            "project",
            "commit_id",
            "hash",
        }
        <= row.keys()
    ):
        raise PrimeVulPairSourceError("missing paired source fields")
    if (
        type(row["idx"]) is not int
        or row["idx"] < 0
        or type(row["target"]) is not int
        or row["target"] not in (0, 1)
        or not isinstance(row["func"], str)
        or not row["func"].strip()
        or not isinstance(row["project"], str)
        or not row["project"]
        or not isinstance(row["commit_id"], str)
        or not row["commit_id"]
        or type(row["hash"]) is not int
    ):
        raise PrimeVulPairSourceError("invalid paired source row")
    return row


def _read_pair_split(
    path: Path, *, expected_sha256: str, expected_bytes: int, expected_pairs: int
) -> tuple[dict[int, dict[str, Any]], dict[str, int]]:
    if path.is_symlink() or not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
        raise PrimeVulPairSourceError(
            f"required regular pair file missing: {path.name}"
        )
    if path.stat().st_size != expected_bytes:
        raise PrimeVulPairSourceError(f"byte length mismatch: {path.name}")
    digest = hashlib.sha256()
    rows: list[dict[str, Any]] = []
    byte_length = 0
    with path.open("rb") as stream:
        for raw in stream:
            digest.update(raw)
            byte_length += len(raw)
            rows.append(_decode_row(raw))
    if byte_length != expected_bytes or path.stat().st_size != expected_bytes:
        raise PrimeVulPairSourceError(f"byte length changed during read: {path.name}")
    if digest.hexdigest() != expected_sha256:
        raise PrimeVulPairSourceError(f"SHA-256 mismatch: {path.name}")
    if len(rows) != 2 * expected_pairs:
        raise PrimeVulPairSourceError(f"pair row count mismatch: {path.name}")
    by_id: dict[int, dict[str, Any]] = {}
    parent: dict[int, int] = {}
    seen_edges: set[tuple[int, int]] = set()

    def find(source_id: int) -> int:
        while parent[source_id] != source_id:
            parent[source_id] = parent[parent[source_id]]
            source_id = parent[source_id]
        return source_id

    for left, right in zip(rows[::2], rows[1::2], strict=True):
        if left["target"] != 1 or right["target"] != 0:
            raise PrimeVulPairSourceError("paired row labels must be ordered 1,0")
        if (
            left["project"] != right["project"]
            or left["commit_id"] != right["commit_id"]
        ):
            raise PrimeVulPairSourceError("paired rows must share project and commit")
        edge = (left["idx"], right["idx"])
        if edge[0] == edge[1] or edge in seen_edges:
            raise PrimeVulPairSourceError("duplicate or self pair")
        seen_edges.add(edge)
        for row in (left, right):
            source_id = row["idx"]
            prior = by_id.setdefault(source_id, row)
            if prior != row:
                raise PrimeVulPairSourceError("reused source ID has different content")
            parent.setdefault(source_id, source_id)
        a, b = find(edge[0]), find(edge[1])
        if a != b:
            parent[max(a, b)] = min(a, b)
    component_sizes: dict[int, int] = {}
    for source_id in by_id:
        root = find(source_id)
        component_sizes[root] = component_sizes.get(root, 0) + 1
    size_histogram: dict[str, int] = {}
    for size in component_sizes.values():
        key = str(size)
        size_histogram[key] = size_histogram.get(key, 0) + 1
    return by_id, size_histogram


def _match_full_source(
    path: Path, paired_by_id: dict[int, dict[str, Any]], expected_sha256: str
) -> None:
    digest = hashlib.sha256()
    seen: set[int] = set()
    with path.open("rb") as stream:
        for raw in stream:
            digest.update(raw)
            row = _decode_row(raw)
            source_id = row["idx"]
            if source_id in paired_by_id:
                seen.add(source_id)
                if row != paired_by_id[source_id]:
                    raise PrimeVulPairSourceError("paired row differs from full source")
    if digest.hexdigest() != expected_sha256:
        raise PrimeVulPairSourceError("full source SHA-256 changed during pair match")
    if seen != paired_by_id.keys():
        raise PrimeVulPairSourceError("paired source ID missing from full source")


def verify_primevul_development_pairs(
    source_dir: Path,
    paired_dir: Path,
    *,
    source_expectation: PrimeVulDevelopmentExpectation = PRIMEVUL_ORIGINAL_DEVELOPMENT,
    pair_expectation: PrimeVulPairExpectation = PRIMEVUL_ORIGINAL_PAIRS,
) -> dict[str, Any]:
    """Bind author-provided development pairs to the original full records."""

    source_receipt = verify_primevul_development(
        source_dir, expectation=source_expectation
    )
    if source_receipt["exact_conflict_groups"]:
        raise PrimeVulPairSourceError("full source exact conflict preflight failed")
    if (
        not paired_dir.is_absolute()
        or paired_dir.is_symlink()
        or not paired_dir.is_dir()
    ):
        raise PrimeVulPairSourceError(
            "paired source must be an absolute real directory"
        )
    if {entry.name for entry in paired_dir.iterdir()} != _PAIR_NAMES:
        raise PrimeVulPairSourceError(
            "paired directory must contain exactly train and validation"
        )
    train, train_components = _read_pair_split(
        paired_dir / "primevul_train_paired.jsonl",
        expected_sha256=pair_expectation.train_sha256,
        expected_bytes=pair_expectation.train_byte_length,
        expected_pairs=pair_expectation.train_pairs,
    )
    validation, validation_components = _read_pair_split(
        paired_dir / "primevul_valid_paired.jsonl",
        expected_sha256=pair_expectation.validation_sha256,
        expected_bytes=pair_expectation.validation_byte_length,
        expected_pairs=pair_expectation.validation_pairs,
    )
    if train.keys() & validation.keys():
        raise PrimeVulPairSourceError("paired source ID spans development splits")
    _match_full_source(
        source_dir / "primevul_train.jsonl", train, source_expectation.train_sha256
    )
    _match_full_source(
        source_dir / "primevul_valid.jsonl",
        validation,
        source_expectation.validation_sha256,
    )
    return {
        "receipt_version": 1,
        "status": "paired-development-verified-non-authorizing",
        "training_authority": False,
        "held_out_data_present": False,
        "source_folder_id": _FOLDER_ID,
        "source_receipt_sha256": sha256_bytes(canonical_json_bytes(source_receipt)),
        "train_paired_file_id": _TRAIN_ID,
        "train_paired_sha256": pair_expectation.train_sha256,
        "train_paired_byte_length": pair_expectation.train_byte_length,
        "train_pairs": pair_expectation.train_pairs,
        "train_unique_source_ids": len(train),
        "train_pair_component_sizes": train_components,
        "validation_paired_file_id": _VALIDATION_ID,
        "validation_paired_sha256": pair_expectation.validation_sha256,
        "validation_paired_byte_length": pair_expectation.validation_byte_length,
        "validation_pairs": pair_expectation.validation_pairs,
        "validation_unique_source_ids": len(validation),
        "validation_pair_component_sizes": validation_components,
        "pair_rows_match_full_source": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("development_data_dir", type=Path)
    parser.add_argument("paired_development_data_dir", type=Path)
    args = parser.parse_args()
    receipt = verify_primevul_development_pairs(
        args.development_data_dir, args.paired_development_data_dir
    )
    sys.stdout.buffer.write(canonical_json_bytes(receipt) + b"\n")


if __name__ == "__main__":
    main()
