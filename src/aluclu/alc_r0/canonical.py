"""Canonical byte and evidence-path rules for ALC-R0.

This module is intentionally separate from :mod:`aluclu.cognition.codec`.
Task 2 has an existing deterministic JSON contract; ALC-R0 requires RFC 8785.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from pathlib import PurePosixPath
from typing import Any, NoReturn

import rfc8785

_DRIVE_PREFIX = re.compile(r"^[A-Za-z]:")
_WINDOWS_DEVICE = re.compile(r"^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)", re.I)


class CanonicalEvidenceError(ValueError):
    """Raised when evidence bytes or paths violate the frozen R0 contract."""


def _reject_constant(value: str) -> NoReturn:
    raise CanonicalEvidenceError(f"non-finite JSON number is forbidden: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CanonicalEvidenceError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _decode_json(data: bytes) -> Any:
    if data.startswith(b"\xef\xbb\xbf"):
        raise CanonicalEvidenceError("UTF-8 BOM is forbidden")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise CanonicalEvidenceError("evidence is not strict UTF-8") from exc
    try:
        return json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except CanonicalEvidenceError:
        raise
    except (json.JSONDecodeError, UnicodeError, ValueError) as exc:
        raise CanonicalEvidenceError("invalid JSON evidence") from exc


def canonical_json_bytes(value: Any) -> bytes:
    """Return RFC 8785 canonical JSON bytes or fail closed."""

    try:
        return rfc8785.dumps(value)
    except (rfc8785.CanonicalizationError, TypeError, ValueError) as exc:
        raise CanonicalEvidenceError("value cannot be RFC-8785 canonicalized") from exc


def parse_canonical_json(data: bytes) -> Any:
    """Parse JSON only when its supplied bytes are already canonical."""

    value = _decode_json(data)
    if canonical_json_bytes(value) != data:
        raise CanonicalEvidenceError("JSON bytes are valid but not RFC-8785 canonical")
    return value


def canonical_jsonl_bytes(records: Iterable[Mapping[str, Any]]) -> bytes:
    """Serialize object records as canonical JSONL with a mandatory final LF."""

    encoded: list[bytes] = []
    for record in records:
        if not isinstance(record, Mapping):
            raise CanonicalEvidenceError("every JSONL record must be an object")
        encoded.append(canonical_json_bytes(dict(record)) + b"\n")
    if not encoded:
        raise CanonicalEvidenceError("canonical JSONL must contain at least one record")
    return b"".join(encoded)


def parse_canonical_jsonl(data: bytes) -> tuple[dict[str, Any], ...]:
    """Parse canonical JSONL and enforce LF-only, no blank records, final LF."""

    if not data:
        raise CanonicalEvidenceError("canonical JSONL is empty")
    if b"\r" in data:
        raise CanonicalEvidenceError("canonical JSONL permits LF only")
    if not data.endswith(b"\n"):
        raise CanonicalEvidenceError("canonical JSONL requires a final LF")

    records: list[dict[str, Any]] = []
    for line in data[:-1].split(b"\n"):
        if not line:
            raise CanonicalEvidenceError("blank JSONL records are forbidden")
        value = parse_canonical_json(line)
        if not isinstance(value, dict):
            raise CanonicalEvidenceError("every JSONL record must be an object")
        records.append(value)
    return tuple(records)


def sha256_bytes(data: bytes) -> str:
    """Return the lowercase SHA-256 hex digest of exact bytes."""

    return hashlib.sha256(data).hexdigest()


def normalize_evidence_path(path: str) -> str:
    """Validate one normalized repository-relative evidence path."""

    if not isinstance(path, str) or not path:
        raise CanonicalEvidenceError("evidence path must be a nonempty string")
    if "\x00" in path:
        raise CanonicalEvidenceError("evidence path contains NUL")
    if "\\" in path:
        raise CanonicalEvidenceError("evidence path must use forward slashes")
    if ":" in path or any(ord(character) < 0x20 for character in path):
        raise CanonicalEvidenceError("evidence path contains a forbidden character")
    if path.startswith("/") or _DRIVE_PREFIX.match(path):
        raise CanonicalEvidenceError("evidence path must be relative")

    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise CanonicalEvidenceError("evidence path contains an empty or dot segment")
    if any(part.endswith((" ", ".")) or _WINDOWS_DEVICE.match(part) for part in parts):
        raise CanonicalEvidenceError("evidence path is unsafe on Windows")
    normalized = PurePosixPath(*parts).as_posix()
    if normalized != path:
        raise CanonicalEvidenceError("evidence path is not normalized")
    return normalized


def validate_evidence_paths(paths: Iterable[str]) -> tuple[str, ...]:
    """Validate paths and reject exact or Windows-casefold collisions."""

    normalized: list[str] = []
    exact: set[str] = set()
    folded: set[str] = set()
    for raw_path in paths:
        path = normalize_evidence_path(raw_path)
        if path in exact:
            raise CanonicalEvidenceError(f"duplicate evidence path: {path}")
        casefolded = path.casefold()
        if casefolded in folded:
            raise CanonicalEvidenceError(f"Windows-casefold path collision: {path}")
        exact.add(path)
        folded.add(casefolded)
        normalized.append(path)
    return tuple(normalized)
