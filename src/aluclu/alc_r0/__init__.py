"""Research-only support for the preregistered ALC-R0 experiment."""

from aluclu.alc_r0.canonical import (
    CanonicalEvidenceError,
    canonical_json_bytes,
    canonical_jsonl_bytes,
    normalize_evidence_path,
    parse_canonical_json,
    parse_canonical_jsonl,
    sha256_bytes,
    validate_evidence_paths,
)

__all__ = [
    "CanonicalEvidenceError",
    "canonical_json_bytes",
    "canonical_jsonl_bytes",
    "normalize_evidence_path",
    "parse_canonical_json",
    "parse_canonical_jsonl",
    "sha256_bytes",
    "validate_evidence_paths",
]
