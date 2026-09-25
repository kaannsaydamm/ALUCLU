"""Non-authorizing R0 claim-ledger candidate root algorithm.

The final machine gate must supply a closed control/run/final file allowlist and
P1-P14 evidence before any ALC-0 claim can be issued. This module deliberately
cannot issue such a claim or a completion artifact.
"""

from __future__ import annotations

import codecs
import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from aluclu.alc_r0.canonical import (
    CanonicalEvidenceError,
    canonical_json_bytes,
    parse_canonical_json,
    parse_canonical_jsonl,
    validate_evidence_paths,
)

_MEDIA_BY_EXTENSION = {
    ".json": "application/json",
    ".jsonl": "application/x-ndjson",
    ".log": "text/plain;charset=utf-8",
    ".safetensors": "application/vnd.safetensors",
}
_EXCLUDED = frozenset(
    {
        "results/alc_r0/final/claim-ledger.json",
        "results/alc_r0/final/completion.json",
    }
)


class ClaimLedgerError(ValueError):
    """Candidate ledger or its closed input set is malformed or incomplete."""


def _check_paths(paths: object) -> set[str]:
    if not isinstance(paths, (dict, list, tuple, set, frozenset)):
        raise ClaimLedgerError("ledger paths must be a finite collection")
    try:
        checked = validate_evidence_paths(paths)
    except (CanonicalEvidenceError, TypeError) as exc:
        raise ClaimLedgerError("unsafe or colliding evidence path") from exc
    if not checked:
        raise ClaimLedgerError("candidate ledger requires evidence files")
    for path in checked:
        if not path.startswith("results/alc_r0/"):
            raise ClaimLedgerError("evidence is outside the R0 namespace")
        if path.casefold() in _EXCLUDED:
            raise ClaimLedgerError("ledger and completion cannot list themselves")
    return set(checked)


def _check_media(path: str, spec: object) -> tuple[str, str | None]:
    if not isinstance(spec, tuple) or len(spec) != 2:
        raise ClaimLedgerError("media/schema specification must be a pair")
    media_type, schema_type = spec
    expected = next(
        (mime for suffix, mime in _MEDIA_BY_EXTENSION.items() if path.endswith(suffix)),
        None,
    )
    if expected is None or media_type != expected:
        raise ClaimLedgerError("media type disagrees with file extension")
    if schema_type is not None and (
        not isinstance(schema_type, str) or not schema_type
    ):
        raise ClaimLedgerError("schema type must be nonempty text or null")
    return expected, schema_type


def _check_content(path: str, payload: bytes) -> None:
    try:
        if path.endswith(".json"):
            parse_canonical_json(payload)
        elif path.endswith(".jsonl"):
            parse_canonical_jsonl(payload)
        elif path.endswith(".log"):
            payload.decode("utf-8", errors="strict")
    except (CanonicalEvidenceError, UnicodeError) as exc:
        raise ClaimLedgerError(f"noncanonical evidence bytes: {path}") from exc


def _summarize_file(path: Path, relative: str) -> tuple[int, str]:
    digest = hashlib.sha256()
    byte_length = 0
    try:
        with path.open("rb") as stream:
            if relative.endswith(".json"):
                payload = stream.read()
                _check_content(relative, payload)
                digest.update(payload)
                byte_length = len(payload)
            elif relative.endswith(".jsonl"):
                count = 0
                for line in stream:
                    if not line.endswith(b"\n") or b"\r" in line or not line[:-1]:
                        raise ClaimLedgerError("JSONL requires nonblank LF records")
                    record = parse_canonical_json(line[:-1])
                    if not isinstance(record, dict):
                        raise ClaimLedgerError(
                            "JSONL evidence record must be an object"
                        )
                    digest.update(line)
                    byte_length += len(line)
                    count += 1
                if count == 0:
                    raise ClaimLedgerError("JSONL evidence must contain records")
            else:
                decoder = (
                    codecs.getincrementaldecoder("utf-8")("strict")
                    if relative.endswith(".log")
                    else None
                )
                while chunk := stream.read(1024 * 1024):
                    if decoder is not None:
                        decoder.decode(chunk)
                    digest.update(chunk)
                    byte_length += len(chunk)
                if decoder is not None:
                    decoder.decode(b"", final=True)
    except (OSError, UnicodeError, CanonicalEvidenceError) as exc:
        raise ClaimLedgerError(
            f"invalid or unreadable R0 evidence: {relative}"
        ) from exc
    return byte_length, digest.hexdigest()


def build_claim_ledger_candidate(
    evidence: Mapping[str, bytes],
    *,
    expected_media: Mapping[str, tuple[str, str | None]],
) -> bytes:
    """Hash an exact, caller-declared evidence set without granting a claim."""

    evidence_paths = _check_paths(evidence)
    expected_paths = _check_paths(expected_media)
    if evidence_paths != expected_paths:
        raise ClaimLedgerError("evidence files differ from the expected file set")

    entries: list[dict[str, Any]] = []
    for path in sorted(expected_paths, key=lambda item: item.encode("utf-8")):
        media_type, schema_type = _check_media(path, expected_media[path])
        payload = evidence[path]
        if type(payload) is not bytes:
            raise ClaimLedgerError("evidence payload must be exact bytes")
        _check_content(path, payload)
        entries.append(
            {
                "path": path,
                "byte_length": len(payload),
                "media_type": media_type,
                "schema_type": schema_type,
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )

    return _encode_candidate(entries)


def _encode_candidate(entries: list[dict[str, Any]]) -> bytes:
    unsigned: dict[str, Any] = {
        "schema_id": "https://aluclu.org/schemas/alc_r0/v1/claim-ledger-candidate.schema.json",
        "schema_version": 1,
        "experiment_id": "alc-r0-smollm2-135m-v1",
        "status": "candidate-non-authorizing",
        "claim": None,
        "training_authority": False,
        "files": entries,
    }
    root_digest = hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest()
    return canonical_json_bytes({**unsigned, "root_digest": root_digest})


def build_claim_ledger_candidate_from_tree(
    repository_root: Path,
    *,
    expected_media: Mapping[str, tuple[str, str | None]],
) -> bytes:
    """Scan one R0 evidence tree for missing/orphan/symlink files, then hash it."""

    if not repository_root.is_absolute() or repository_root.is_symlink():
        raise ClaimLedgerError("repository root must be absolute and not a symlink")
    try:
        root = repository_root.resolve(strict=True)
    except OSError as exc:
        raise ClaimLedgerError("repository root is unavailable") from exc
    if not root.is_dir():
        raise ClaimLedgerError("repository root must be a directory")
    expected_paths = _check_paths(expected_media)
    evidence_root = root / "results" / "alc_r0"
    if not evidence_root.is_dir() or evidence_root.is_symlink():
        raise ClaimLedgerError("R0 evidence root is unavailable or a symlink")

    found: set[str] = set()
    for path in evidence_root.rglob("*"):
        if path.is_symlink():
            raise ClaimLedgerError("symlink in R0 evidence tree")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ClaimLedgerError("nonregular R0 evidence entry")
        relative = path.relative_to(root).as_posix()
        if relative in _EXCLUDED:
            continue
        if relative not in expected_paths:
            raise ClaimLedgerError(f"orphan R0 evidence file: {relative}")
        found.add(relative)
    if found != expected_paths:
        raise ClaimLedgerError("R0 evidence tree is missing expected files")

    entries: list[dict[str, Any]] = []
    for relative in sorted(expected_paths, key=lambda item: item.encode("utf-8")):
        media_type, schema_type = _check_media(relative, expected_media[relative])
        path = root / Path(relative)
        byte_length, sha256 = _summarize_file(path, relative)
        entries.append(
            {
                "path": relative,
                "byte_length": byte_length,
                "media_type": media_type,
                "schema_type": schema_type,
                "sha256": sha256,
            }
        )
    return _encode_candidate(entries)


def verify_claim_ledger_candidate(
    ledger_bytes: bytes,
    evidence: Mapping[str, bytes],
    *,
    expected_media: Mapping[str, tuple[str, str | None]],
) -> dict[str, Any]:
    """Reject any byte, file-set, ordering, or root-digest discrepancy."""

    try:
        document = parse_canonical_json(ledger_bytes)
    except CanonicalEvidenceError as exc:
        raise ClaimLedgerError("ledger bytes are not canonical JSON") from exc
    if not isinstance(document, dict):
        raise ClaimLedgerError("ledger root must be an object")
    if ledger_bytes != build_claim_ledger_candidate(
        evidence, expected_media=expected_media
    ):
        raise ClaimLedgerError("ledger differs from exact evidence or root digest")
    return document
