"""Research-only ALC-R0 exports; plain package import loads no host dependencies.

Dependency errors propagate when an export is requested. Star imports intentionally
resolve the complete public API. Direct submodule imports use normal importlib semantics.
"""

from importlib import import_module as _import_module

_EXPORTS = {
    "CanonicalEvidenceError": ("aluclu.alc_r0.canonical", "CanonicalEvidenceError"),
    "canonical_json_bytes": ("aluclu.alc_r0.canonical", "canonical_json_bytes"),
    "canonical_jsonl_bytes": ("aluclu.alc_r0.canonical", "canonical_jsonl_bytes"),
    "normalize_evidence_path": ("aluclu.alc_r0.canonical", "normalize_evidence_path"),
    "parse_canonical_json": ("aluclu.alc_r0.canonical", "parse_canonical_json"),
    "parse_canonical_jsonl": ("aluclu.alc_r0.canonical", "parse_canonical_jsonl"),
    "sha256_bytes": ("aluclu.alc_r0.canonical", "sha256_bytes"),
    "validate_evidence_paths": ("aluclu.alc_r0.canonical", "validate_evidence_paths"),
    "SMOLLM2_135M_CONFIG": ("aluclu.alc_r0.host", "SMOLLM2_135M_CONFIG"),
    "HostLoadError": ("aluclu.alc_r0.host", "HostLoadError"),
    "PinnedHostConfig": ("aluclu.alc_r0.host", "PinnedHostConfig"),
    "VerifiedHost": ("aluclu.alc_r0.host", "VerifiedHost"),
    "load_verified_host": ("aluclu.alc_r0.host", "load_verified_host"),
    "R0SchemaValidationError": (
        "aluclu.alc_r0.schema_validation",
        "R0SchemaValidationError",
    ),
    "validate_r0_document": ("aluclu.alc_r0.schema_validation", "validate_r0_document"),
}

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


def __getattr__(name: str):
    try:
        module_name, symbol_name = _EXPORTS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    value = getattr(_import_module(module_name), symbol_name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
