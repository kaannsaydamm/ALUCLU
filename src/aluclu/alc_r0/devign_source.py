"""Pinned Devign train/validation acquisition without touching official test.

This verifier binds exact Parquet bytes to source IDs and development metadata.
Clone filtering and the independently sealed test split are separate gates.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from .canonical import canonical_json_bytes

_REVISION = "69bd48c03223c2104342acd9a807caf61ac3efb8"
_TRAIN_NAME = "train-00000-of-00001.parquet"
_VALIDATION_NAME = "validation-00000-of-00001.parquet"
_EXPECTED_NAMES = {_TRAIN_NAME, _VALIDATION_NAME}
_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_SCHEMA = pa.schema(
    [
        pa.field("id", pa.int32()),
        pa.field("func", pa.string()),
        pa.field("target", pa.bool_()),
        pa.field("project", pa.string()),
        pa.field("commit_id", pa.string()),
    ]
)


class DevignSourceError(ValueError):
    """Pinned development bytes or rows violate the Devign source contract."""


@dataclass(frozen=True)
class DevignDevelopmentExpectation:
    revision: str
    train_sha256: str
    train_byte_length: int
    train_rows: int
    validation_sha256: str
    validation_byte_length: int
    validation_rows: int

    def __post_init__(self) -> None:
        if not _HEX40.fullmatch(self.revision):
            raise DevignSourceError("revision must be a full lowercase Git commit")
        if not _HEX64.fullmatch(self.train_sha256) or not _HEX64.fullmatch(
            self.validation_sha256
        ):
            raise DevignSourceError("expected SHA-256 must be lowercase 64-hex")
        if any(
            type(value) is not int or value < 1
            for value in (
                self.train_byte_length,
                self.train_rows,
                self.validation_byte_length,
                self.validation_rows,
            )
        ):
            raise DevignSourceError(
                "expected byte lengths and row counts must be positive"
            )


DEVIGN_DEVELOPMENT = DevignDevelopmentExpectation(
    revision=_REVISION,
    train_sha256="e319c83e2e816a10aeeebe78668aa95b757b04e555700bf5f826766b0e80bb06",
    train_byte_length=17847670,
    train_rows=21854,
    validation_sha256="a17a76ed040d7f8657d1ff741f967b44704c008101ac958e2990ad468203cfa4",
    validation_byte_length=2214315,
    validation_rows=2732,
)


@dataclass(frozen=True)
class DevignSourceRecord:
    source_id: str
    function: str
    target: bool
    project: str
    commit_id: str


@dataclass(frozen=True)
class VerifiedDevignDevelopment:
    train: tuple[DevignSourceRecord, ...]
    validation: tuple[DevignSourceRecord, ...]
    receipt: dict[str, Any]


def _read_exact_file(path: Path, *, size: int, sha256: str) -> bytes:
    if path.is_symlink() or not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
        raise DevignSourceError(f"required regular file missing: {path.name}")
    if path.stat().st_size != size:
        raise DevignSourceError(f"byte length mismatch: {path.name}")
    data = path.read_bytes()
    if len(data) != size:
        raise DevignSourceError(f"byte length changed during read: {path.name}")
    if hashlib.sha256(data).hexdigest() != sha256:
        raise DevignSourceError(f"SHA-256 mismatch: {path.name}")
    return data


def _parse_parquet(
    data: bytes, *, expected_rows: int
) -> tuple[DevignSourceRecord, ...]:
    try:
        reader = pq.ParquetFile(pa.BufferReader(data))
        schema = reader.schema_arrow.remove_metadata()
        if not schema.equals(_SCHEMA, check_metadata=False):
            raise DevignSourceError("Devign Parquet schema mismatch")
        if reader.metadata.num_rows != expected_rows:
            raise DevignSourceError("Devign Parquet row count mismatch")
        table = reader.read()
    except DevignSourceError:
        raise
    except (pa.ArrowException, OSError, ValueError) as exc:
        raise DevignSourceError("invalid Devign Parquet bytes") from exc
    if table.num_rows != expected_rows or any(
        column.null_count for column in table.columns
    ):
        raise DevignSourceError("Devign rows or null fields are invalid")
    records: list[DevignSourceRecord] = []
    for row in table.to_pylist():
        source_number = row["id"]
        function = row["func"]
        project = row["project"]
        commit_id = row["commit_id"]
        if (
            type(source_number) is not int
            or source_number < 0
            or not isinstance(function, str)
            or not function.strip()
            or project not in ("FFmpeg", "qemu")
            or not isinstance(commit_id, str)
            or not _HEX40.fullmatch(commit_id)
        ):
            raise DevignSourceError("invalid Devign source row")
        records.append(
            DevignSourceRecord(
                f"devign:{source_number:08d}",
                function,
                row["target"],
                project,
                commit_id,
            )
        )
    return tuple(records)


def load_verified_devign_development(
    source_dir: Path,
    *,
    expectation: DevignDevelopmentExpectation = DEVIGN_DEVELOPMENT,
) -> VerifiedDevignDevelopment:
    """Read only exact pinned development files, never the official test split."""

    if not source_dir.is_absolute():
        raise DevignSourceError("development source directory must be absolute")
    if source_dir.is_symlink() or not source_dir.is_dir():
        raise DevignSourceError("development source must be a real directory")
    if {path.name for path in source_dir.iterdir()} != _EXPECTED_NAMES:
        raise DevignSourceError(
            "development directory must contain exactly train and validation"
        )
    train_data = _read_exact_file(
        source_dir / _TRAIN_NAME,
        size=expectation.train_byte_length,
        sha256=expectation.train_sha256,
    )
    validation_data = _read_exact_file(
        source_dir / _VALIDATION_NAME,
        size=expectation.validation_byte_length,
        sha256=expectation.validation_sha256,
    )
    train = _parse_parquet(train_data, expected_rows=expectation.train_rows)
    validation = _parse_parquet(
        validation_data, expected_rows=expectation.validation_rows
    )
    train_ids = [row.source_id for row in train]
    validation_ids = [row.source_id for row in validation]
    if (
        len(set(train_ids)) != len(train_ids)
        or len(set(validation_ids)) != len(validation_ids)
        or set(train_ids) & set(validation_ids)
    ):
        raise DevignSourceError("duplicate or cross-split source ID")
    receipt: dict[str, Any] = {
        "receipt_version": 1,
        "status": "candidate-non-authorizing",
        "training_authority": False,
        "held_out_data_present": False,
        "source_repository": "google/code_x_glue_cc_defect_detection",
        "source_revision": expectation.revision,
        "upstream_license_declaration": "C-UDA",
        "source_id_scheme": "devign:<zero-padded eight-digit official id>",
        "train_file": f"data/{_TRAIN_NAME}",
        "train_byte_length": expectation.train_byte_length,
        "train_sha256": expectation.train_sha256,
        "train_rows": len(train),
        "train_target_true": sum(row.target for row in train),
        "ordered_train_ids_sha256": hashlib.sha256(
            canonical_json_bytes(train_ids)
        ).hexdigest(),
        "validation_file": f"data/{_VALIDATION_NAME}",
        "validation_byte_length": expectation.validation_byte_length,
        "validation_sha256": expectation.validation_sha256,
        "validation_rows": len(validation),
        "validation_target_true": sum(row.target for row in validation),
        "ordered_validation_ids_sha256": hashlib.sha256(
            canonical_json_bytes(validation_ids)
        ).hexdigest(),
    }
    return VerifiedDevignDevelopment(train, validation, receipt)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("development_data_dir", type=Path)
    args = parser.parse_args()
    result = load_verified_devign_development(args.development_data_dir)
    sys.stdout.buffer.write(canonical_json_bytes(result.receipt) + b"\n")


if __name__ == "__main__":
    main()
