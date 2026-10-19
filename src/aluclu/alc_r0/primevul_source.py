"""Development-only PrimeVul original-source qualification candidate.

Only the authors' train and validation JSONL files are accepted. This module
does not inspect the test split, run LSH, or authorize training.
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
from .devign_preprocess import DevignPreprocessError, normalize_devign_code

_TRAIN_NAME = "primevul_train.jsonl"
_VALIDATION_NAME = "primevul_valid.jsonl"
_EXPECTED_NAMES = {_TRAIN_NAME, _VALIDATION_NAME}
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_REQUIRED_KEYS = {"idx", "func", "target", "project", "commit_id", "hash"}
_FOLDER_ID = "19iLaNDS0z99N8kB_jBRTmDLehwZBolMY"
_TRAIN_ID = "1qRO_Qdy7KXcZbJJAu5J3VZWkRVvT4Kbu"
_VALIDATION_ID = "1CMQ185Ww_bsBWGbJe4sZW0vzceWnmNE7"


class PrimeVulSourceError(ValueError):
    """Pinned development bytes or source rows violate the candidate contract."""


@dataclass(frozen=True)
class PrimeVulDevelopmentExpectation:
    train_sha256: str
    train_byte_length: int
    train_rows: int
    train_positive: int
    validation_sha256: str
    validation_byte_length: int
    validation_rows: int
    validation_positive: int

    def __post_init__(self) -> None:
        if not _HEX64.fullmatch(self.train_sha256) or not _HEX64.fullmatch(
            self.validation_sha256
        ):
            raise PrimeVulSourceError("expected SHA-256 must be lowercase 64-hex")
        for size, rows, positive in (
            (self.train_byte_length, self.train_rows, self.train_positive),
            (
                self.validation_byte_length,
                self.validation_rows,
                self.validation_positive,
            ),
        ):
            if (
                type(size) is not int
                or size < 1
                or type(rows) is not int
                or rows < 1
                or type(positive) is not int
                or not 0 <= positive <= rows
            ):
                raise PrimeVulSourceError("invalid source expectation")


PRIMEVUL_ORIGINAL_DEVELOPMENT = PrimeVulDevelopmentExpectation(
    train_sha256="9fea452f1b7c7ffafb28d6131789f722ad820c1032d3bcd90b7fc17da3d9b117",
    train_byte_length=343487568,
    train_rows=184427,
    train_positive=5574,
    validation_sha256="56b91474fb7d75b313013766e0f5d1d8150c98e70961cf2b26df93875e87fb27",
    validation_byte_length=52185805,
    validation_rows=25430,
    validation_positive=699,
)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PrimeVulSourceError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise PrimeVulSourceError(f"nonfinite JSON constant: {value}")


def _read_split(
    path: Path,
    *,
    expected_sha256: str,
    expected_bytes: int,
    expected_rows: int,
    expected_positive: int,
    split_bit: int,
    ids: set[int],
    groups: dict[str, tuple[int, int, int]],
    conflict_digests: set[str],
) -> tuple[int, int, int, int, int]:
    if path.is_symlink() or not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
        raise PrimeVulSourceError(f"required regular source file missing: {path.name}")
    if path.stat().st_size != expected_bytes:
        raise PrimeVulSourceError(f"byte length mismatch: {path.name}")
    digest = hashlib.sha256()
    bytes_read = 0
    rows = 0
    positive = 0
    new_duplicate_groups = 0
    validation_overlap_groups = 0
    with path.open("rb") as stream:
        for raw in stream:
            digest.update(raw)
            bytes_read += len(raw)
            rows += 1
            if not raw.endswith(b"\n"):
                raise PrimeVulSourceError("JSONL line must end with LF")
            try:
                record = json.loads(
                    raw.decode("utf-8", errors="strict"),
                    object_pairs_hook=_unique_object,
                    parse_constant=_reject_constant,
                )
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise PrimeVulSourceError("invalid UTF-8 JSONL source row") from exc
            if not isinstance(record, dict) or not _REQUIRED_KEYS <= record.keys():
                raise PrimeVulSourceError("missing required PrimeVul source fields")
            source_id = record["idx"]
            label = record["target"]
            code = record["func"]
            if (
                type(source_id) is not int
                or source_id < 0
                or type(label) is not int
                or label not in (0, 1)
                or not isinstance(code, str)
                or not code.strip()
                or not isinstance(record["project"], str)
                or not record["project"]
                or not isinstance(record["commit_id"], str)
                or not record["commit_id"]
                or type(record["hash"]) is not int
            ):
                raise PrimeVulSourceError("invalid PrimeVul source row")
            if source_id in ids:
                raise PrimeVulSourceError(
                    "duplicate source ID across development splits"
                )
            ids.add(source_id)
            positive += label
            try:
                normalized = normalize_devign_code(
                    code.encode("utf-8", errors="strict")
                )
            except (UnicodeEncodeError, DevignPreprocessError) as exc:
                raise PrimeVulSourceError("invalid code normalization") from exc
            normalized_sha256 = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            existing = groups.get(normalized_sha256)
            if existing is None:
                groups[normalized_sha256] = (label, 1, split_bit)
            else:
                first_label, member_count, split_mask = existing
                new_duplicate_groups += member_count == 1
                validation_overlap_groups += split_mask != 3 and split_mask != split_bit
                if first_label != label:
                    conflict_digests.add(normalized_sha256)
                groups[normalized_sha256] = (
                    first_label,
                    member_count + 1,
                    split_mask | split_bit,
                )
    if bytes_read != expected_bytes or path.stat().st_size != expected_bytes:
        raise PrimeVulSourceError(f"byte length changed during read: {path.name}")
    if digest.hexdigest() != expected_sha256:
        raise PrimeVulSourceError(f"SHA-256 mismatch: {path.name}")
    if rows != expected_rows or positive != expected_positive:
        raise PrimeVulSourceError(f"row or label count mismatch: {path.name}")
    return rows, positive, bytes_read, new_duplicate_groups, validation_overlap_groups


def verify_primevul_development(
    source_dir: Path,
    *,
    expectation: PrimeVulDevelopmentExpectation = PRIMEVUL_ORIGINAL_DEVELOPMENT,
) -> dict[str, Any]:
    """Verify only author-hosted development files and exact-label preflight."""

    if (
        not source_dir.is_absolute()
        or source_dir.is_symlink()
        or not source_dir.is_dir()
    ):
        raise PrimeVulSourceError(
            "development source must be an absolute real directory"
        )
    if {entry.name for entry in source_dir.iterdir()} != _EXPECTED_NAMES:
        raise PrimeVulSourceError(
            "development directory must contain exactly train and validation"
        )
    ids: set[int] = set()
    groups: dict[str, tuple[int, int, int]] = {}
    conflicts: set[str] = set()
    train = _read_split(
        source_dir / _TRAIN_NAME,
        expected_sha256=expectation.train_sha256,
        expected_bytes=expectation.train_byte_length,
        expected_rows=expectation.train_rows,
        expected_positive=expectation.train_positive,
        split_bit=1,
        ids=ids,
        groups=groups,
        conflict_digests=conflicts,
    )
    validation = _read_split(
        source_dir / _VALIDATION_NAME,
        expected_sha256=expectation.validation_sha256,
        expected_bytes=expectation.validation_byte_length,
        expected_rows=expectation.validation_rows,
        expected_positive=expectation.validation_positive,
        split_bit=2,
        ids=ids,
        groups=groups,
        conflict_digests=conflicts,
    )
    if len(ids) != train[0] + validation[0]:
        raise PrimeVulSourceError("source ID count mismatch")
    return {
        "receipt_version": 1,
        "status": "failed-exact-label-conflicts"
        if conflicts
        else "candidate-non-authorizing",
        "training_authority": False,
        "held_out_data_present": False,
        "lsh_executed": False,
        "source_repository": "DLVulDet/PrimeVul",
        "source_folder_id": _FOLDER_ID,
        "source_license_note": "repository declares MIT; dataset-specific scope not yet independently resolved",
        "train_file_id": _TRAIN_ID,
        "train_sha256": expectation.train_sha256,
        "train_byte_length": train[2],
        "train_rows": train[0],
        "train_positive": train[1],
        "validation_file_id": _VALIDATION_ID,
        "validation_sha256": expectation.validation_sha256,
        "validation_byte_length": validation[2],
        "validation_rows": validation[0],
        "validation_positive": validation[1],
        "normalization_policy": "strict-utf8-nfc-lf-trailing-ascii-outer-blank",
        "source_id_scheme": "primevul:idx",
        "exact_normalized_groups": len(groups),
        "exact_duplicate_groups": train[3] + validation[3],
        "exact_validation_overlap_groups": validation[4],
        "exact_conflict_groups": len(conflicts),
        "conflict_digest_sha256": sha256_bytes(canonical_json_bytes(sorted(conflicts))),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("development_data_dir", type=Path)
    args = parser.parse_args()
    receipt = verify_primevul_development(args.development_data_dir)
    sys.stdout.buffer.write(canonical_json_bytes(receipt) + b"\n")


if __name__ == "__main__":
    main()
