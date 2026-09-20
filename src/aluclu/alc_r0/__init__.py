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
from aluclu.alc_r0.schema_validation import (
    R0SchemaValidationError,
    validate_r0_document,
)

__all__ = [
    "CanonicalEvidenceError",
    "R0SchemaValidationError",
    "canonical_json_bytes",
    "canonical_jsonl_bytes",
    "normalize_evidence_path",
    "parse_canonical_json",
    "parse_canonical_jsonl",
    "sha256_bytes",
    "validate_evidence_paths",
    "validate_r0_document",
]
