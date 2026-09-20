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
from aluclu.alc_r0.host import (
    SMOLLM2_135M_CONFIG,
    HostLoadError,
    PinnedHostConfig,
    VerifiedHost,
    load_verified_host,
)
from aluclu.alc_r0.schema_validation import (
    R0SchemaValidationError,
    validate_r0_document,
)

__all__ = [
    "SMOLLM2_135M_CONFIG",
    "CanonicalEvidenceError",
    "HostLoadError",
    "PinnedHostConfig",
    "R0SchemaValidationError",
    "VerifiedHost",
    "canonical_json_bytes",
    "canonical_jsonl_bytes",
    "load_verified_host",
    "normalize_evidence_path",
    "parse_canonical_json",
    "parse_canonical_jsonl",
    "sha256_bytes",
    "validate_evidence_paths",
    "validate_r0_document",
]
