"""Versioned, fail-closed JSON Schema validation for ALC-R0 evidence."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

from aluclu.alc_r0.acquisition import SMOLLM2_135M
from aluclu.alc_r0.canonical import (
    CanonicalEvidenceError,
    canonical_json_bytes,
    parse_canonical_json,
    validate_evidence_paths,
)

_SCHEMA_BASE = "https://aluclu.org/schemas/alc_r0/v1/"
_SCHEMAS = {
    "acquisition-receipt": "acquisition-receipt.schema.json",
    "lock-manifest": "lock-manifest.schema.json",
}


class R0SchemaValidationError(ValueError):
    """Raised when a schema or evidence document is invalid."""


def _load_schema(schema_root: Path, schema_name: str) -> dict[str, Any]:
    filename = _SCHEMAS.get(schema_name)
    if filename is None:
        raise R0SchemaValidationError(f"unknown schema: {schema_name}")
    if not schema_root.is_absolute():
        raise R0SchemaValidationError("schema root must be absolute")
    if schema_root.is_symlink():
        raise R0SchemaValidationError("schema root must not be a symlink")
    try:
        resolved_root = schema_root.resolve(strict=True)
    except OSError as exc:
        raise R0SchemaValidationError("schema root is unavailable") from exc
    if resolved_root != schema_root:
        raise R0SchemaValidationError("schema root must be normalized and symlink-free")

    schema_path = resolved_root / filename
    if schema_path.is_symlink():
        raise R0SchemaValidationError("schema file must not be a symlink")
    try:
        data = schema_path.read_bytes()
    except OSError as exc:
        raise R0SchemaValidationError(
            f"schema file is unavailable: {filename}"
        ) from exc
    try:
        schema = parse_canonical_json(data)
    except CanonicalEvidenceError as exc:
        raise R0SchemaValidationError(f"schema is not canonical: {filename}") from exc
    if not isinstance(schema, dict):
        raise R0SchemaValidationError(f"schema root is not an object: {filename}")
    if schema.get("$id") != _SCHEMA_BASE + filename:
        raise R0SchemaValidationError(f"schema ID mismatch: {filename}")
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise R0SchemaValidationError(
            f"invalid Draft 2020-12 schema: {filename}"
        ) from exc
    return schema


def _validate_acquisition_semantics(document: Mapping[str, Any]) -> None:
    raw_files = document.get("files")
    if not isinstance(raw_files, list):
        raise R0SchemaValidationError("acquisition files must be a list")
    files = [item for item in raw_files if isinstance(item, dict)]
    if len(files) != len(raw_files):
        raise R0SchemaValidationError("acquisition file record must be an object")
    try:
        paths = validate_evidence_paths(str(item["path"]) for item in files)
    except (CanonicalEvidenceError, KeyError) as exc:
        raise R0SchemaValidationError("acquisition inventory path violation") from exc
    by_path = {path: item for path, item in zip(paths, files, strict=True)}
    for path, expected_sha256 in SMOLLM2_135M.required_sha256.items():
        item = by_path.get(path)
        if item is None or item.get("sha256") != expected_sha256:
            raise R0SchemaValidationError(f"pinned acquisition file mismatch: {path}")
    expected_inventory = hashlib.sha256(canonical_json_bytes(files)).hexdigest()
    if document.get("inventory_sha256") != expected_inventory:
        raise R0SchemaValidationError("acquisition inventory digest mismatch")


def _validate_lock_semantics(document: Mapping[str, Any]) -> None:
    raw_locks = document.get("locks")
    if not isinstance(raw_locks, list):
        raise R0SchemaValidationError("locks must be a list")
    locks = [item for item in raw_locks if isinstance(item, dict)]
    if len(locks) != len(raw_locks):
        raise R0SchemaValidationError("lock record must be an object")
    try:
        validate_evidence_paths(str(item["relative_path"]) for item in locks)
    except (CanonicalEvidenceError, KeyError) as exc:
        raise R0SchemaValidationError("lock path violation") from exc


def validate_r0_document(
    data: bytes,
    *,
    schema_name: str,
    schema_root: Path,
) -> dict[str, Any]:
    """Validate exact canonical bytes against one frozen R0 schema and semantics."""

    schema = _load_schema(schema_root, schema_name)
    try:
        document = parse_canonical_json(data)
    except CanonicalEvidenceError as exc:
        raise R0SchemaValidationError("evidence document is not canonical") from exc
    if not isinstance(document, dict):
        raise R0SchemaValidationError("evidence document root must be an object")

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        first = errors[0]
        location = "/".join(str(part) for part in first.absolute_path) or "<root>"
        raise R0SchemaValidationError(
            f"schema violation at {location}: {first.message}"
        )

    if schema_name == "acquisition-receipt":
        _validate_acquisition_semantics(document)
    elif schema_name == "lock-manifest":
        _validate_lock_semantics(document)
    return document
