"""Versioned, fail-closed JSON Schema validation for ALC-R0 evidence."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Registry
from referencing.exceptions import NoSuchResource

from aluclu.alc_r0.acquisition import SMOLLM2_135M
from aluclu.alc_r0.artifact_contract import build_run_artifact_contract
from aluclu.alc_r0.canonical import (
    CanonicalEvidenceError,
    canonical_json_bytes,
    parse_canonical_json,
    validate_evidence_paths,
)
from aluclu.alc_r0.run_matrix import (
    SOURCE_PLAN_PATH,
    SOURCE_PLAN_SHA256,
    build_expected_run_matrix,
)

_SCHEMA_BASE = "https://aluclu.org/schemas/alc_r0/v1/"
_SCHEMAS = {
    "acquisition-receipt": "acquisition-receipt.schema.json",
    "base-digest-receipt": "base-digest-receipt.schema.json",
    "logical-run-matrix": "logical-run-matrix.schema.json",
    "lock-manifest": "lock-manifest.schema.json",
    "linux-evaluator-bootstrap-receipt": (
        "linux-evaluator-bootstrap-receipt.schema.json"
    ),
    "run-artifact-contract": "run-artifact-contract.schema.json",
    "research-capsule-artifact": "research-capsule-artifact.schema.json",
}


def _reject_schema_retrieval(uri: str):
    raise NoSuchResource(ref=uri)


_LOCAL_ONLY_REGISTRY = Registry(retrieve=_reject_schema_retrieval)


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
    _assert_local_schema_references(schema)
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
    if paths != tuple(sorted(paths, key=lambda path: path.encode("utf-8"))):
        raise R0SchemaValidationError(
            "acquisition inventory paths are not UTF-8 sorted"
        )
    by_path = {path: item for path, item in zip(paths, files, strict=True)}
    if set(by_path) != set(SMOLLM2_135M.required_sha256):
        raise R0SchemaValidationError("acquisition inventory file set mismatch")
    for path, expected_sha256 in SMOLLM2_135M.required_sha256.items():
        item = by_path.get(path)
        if item is None or item.get("sha256") != expected_sha256:
            raise R0SchemaValidationError(f"pinned acquisition file mismatch: {path}")
        expected_byte_lengths = SMOLLM2_135M.required_byte_length
        if (
            expected_byte_lengths is None
            or item.get("byte_length") != expected_byte_lengths[path]
        ):
            raise R0SchemaValidationError(
                f"pinned acquisition byte length mismatch: {path}"
            )
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


def _validate_logical_run_matrix_semantics(document: Mapping[str, Any]) -> None:
    expected_runs = [row.to_json() for row in build_expected_run_matrix()]
    if document.get("source_plan_path") != SOURCE_PLAN_PATH:
        raise R0SchemaValidationError("logical run matrix source-plan path mismatch")
    if document.get("source_plan_sha256") != SOURCE_PLAN_SHA256:
        raise R0SchemaValidationError("logical run matrix source-plan digest mismatch")
    if document.get("logical_run_count") != len(expected_runs):
        raise R0SchemaValidationError("logical run matrix count mismatch")
    if document.get("runs") != expected_runs:
        raise R0SchemaValidationError("logical run matrix differs from preregistration")


def _validate_package_inventory(raw_inventory: object, *, label: str) -> None:
    if not isinstance(raw_inventory, Mapping):
        raise R0SchemaValidationError(f"{label} inventory must be an object")
    raw_items = raw_inventory.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise R0SchemaValidationError(f"{label} inventory must contain packages")
    items = [item for item in raw_items if isinstance(item, dict)]
    if len(items) != len(raw_items):
        raise R0SchemaValidationError(f"{label} package must be an object")
    names: list[str] = []
    for item in items:
        name = item.get("name")
        if not isinstance(name, str):
            raise R0SchemaValidationError(f"{label} package name must be a string")
        names.append(name)
    if names != sorted(names, key=lambda item: item.encode("utf-8")):
        raise R0SchemaValidationError(f"{label} packages are not UTF-8 sorted")
    if len(set(names)) != len(names):
        raise R0SchemaValidationError(f"{label} packages contain duplicates")
    if raw_inventory.get("count") != len(items):
        raise R0SchemaValidationError(f"{label} package count mismatch")
    digest = hashlib.sha256(canonical_json_bytes(items)).hexdigest()
    if raw_inventory.get("sha256") != digest:
        raise R0SchemaValidationError(f"{label} package inventory digest mismatch")


def _validate_linux_bootstrap_semantics(document: Mapping[str, Any]) -> None:
    _validate_package_inventory(document.get("distro_packages"), label="distro")
    python = document.get("python")
    if not isinstance(python, Mapping):
        raise R0SchemaValidationError("Python environment must be an object")
    _validate_package_inventory(python.get("packages"), label="Python")


def _validate_run_artifact_contract_semantics(document: Mapping[str, Any]) -> None:
    project_root = Path(__file__).parents[3]
    matrix_path = project_root / "experiments/alc_r0/v1/logical-run-matrix.json"
    try:
        matrix_bytes = matrix_path.read_bytes()
    except OSError as exc:
        raise R0SchemaValidationError("logical matrix is unavailable") from exc
    expected = build_run_artifact_contract(matrix_bytes)
    if document != expected:
        raise R0SchemaValidationError(
            "run artifact contract differs from the frozen logical matrix"
        )


def _assert_local_schema_references(value: Any) -> None:
    if isinstance(value, dict):
        for keyword in ("$ref", "$dynamicRef"):
            reference = value.get(keyword)
            if reference is not None and (
                not isinstance(reference, str) or not reference.startswith("#")
            ):
                raise R0SchemaValidationError(
                    f"remote or nonlocal schema {keyword} is forbidden"
                )
        for child in value.values():
            _assert_local_schema_references(child)
    elif isinstance(value, list):
        for child in value:
            _assert_local_schema_references(child)


def _validate_base_digest_semantics(document: Mapping[str, Any]) -> None:
    observations = document.get("observations")
    if not isinstance(observations, list) or len(observations) != 2:
        raise R0SchemaValidationError("base digest requires two observations")
    if canonical_json_bytes(observations[0]) != canonical_json_bytes(observations[1]):
        raise R0SchemaValidationError("fresh-process base observations differ")


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

    validator = Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
        registry=_LOCAL_ONLY_REGISTRY,
    )
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
    elif schema_name == "base-digest-receipt":
        _validate_base_digest_semantics(document)
    elif schema_name == "lock-manifest":
        _validate_lock_semantics(document)
    elif schema_name == "logical-run-matrix":
        _validate_logical_run_matrix_semantics(document)
    elif schema_name == "linux-evaluator-bootstrap-receipt":
        _validate_linux_bootstrap_semantics(document)
    elif schema_name == "run-artifact-contract":
        _validate_run_artifact_contract_semantics(document)
    return document
