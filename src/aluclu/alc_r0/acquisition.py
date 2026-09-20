"""Fail-closed local snapshot verification for ALC-R0 acquisition."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aluclu.alc_r0.canonical import canonical_json_bytes, validate_evidence_paths

_REVISION = re.compile(r"^[0-9a-f]{40}$")
_FORBIDDEN_WEIGHT_SUFFIXES = {
    ".bin",
    ".ckpt",
    ".pickle",
    ".pkl",
    ".pt",
    ".pth",
}


class AcquisitionError(ValueError):
    """Raised when acquired source bytes violate the preregistration."""


@dataclass(frozen=True)
class SnapshotExpectation:
    repository: str
    revision: str
    required_sha256: Mapping[str, str]

    def __post_init__(self) -> None:
        if not self.repository or self.repository.strip() != self.repository:
            raise AcquisitionError("repository must be a normalized nonempty ID")
        if not _REVISION.fullmatch(self.revision):
            raise AcquisitionError("revision must be a full lowercase 40-hex commit")
        validate_evidence_paths(self.required_sha256)
        for digest in self.required_sha256.values():
            if not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise AcquisitionError("expected SHA-256 must be lowercase 64-hex")


SMOLLM2_135M = SnapshotExpectation(
    repository="HuggingFaceTB/SmolLM2-135M",
    revision="93efa2f097d58c2a74874c7e644dbc9b0cee75a2",
    required_sha256={
        "config.json": "1d556eab73b69c7f11f64c557a2f9c6f440bd4c6b89bb2584a6b498c92603843",
        "model.safetensors": "80521b40281d6ce74e35c9282c22539e75aa0ac8578892b2a59955ef78d55da1",
        "tokenizer.json": "9ca9acddb6525a194ec8ac7a87f24fbba7232a9a15ffa1af0c1224fcd888e47c",
        "tokenizer_config.json": "4bb9af56a342753d39374f4016a16574cab299fe088e896f425ce3c433f61424",
    },
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def verify_model_snapshot(
    snapshot_root: Path,
    *,
    expectation: SnapshotExpectation = SMOLLM2_135M,
) -> dict[str, Any]:
    """Inventory and verify one already-downloaded local model snapshot."""

    if not snapshot_root.is_absolute():
        raise AcquisitionError("snapshot root must be absolute")
    if not snapshot_root.is_dir():
        raise AcquisitionError("snapshot root is not a directory")
    root = snapshot_root.resolve(strict=True)

    inventory: list[dict[str, Any]] = []
    for path in sorted(snapshot_root.rglob("*"), key=lambda value: value.as_posix()):
        if path.is_symlink():
            raise AcquisitionError(f"snapshot symlink is forbidden: {path}")
        if not path.is_file():
            continue
        resolved = path.resolve(strict=True)
        try:
            relative = resolved.relative_to(root).as_posix()
        except ValueError as exc:
            raise AcquisitionError(f"snapshot path escapes root: {path}") from exc
        if path.suffix.casefold() in _FORBIDDEN_WEIGHT_SUFFIXES:
            raise AcquisitionError(f"unsafe weight format is forbidden: {relative}")
        inventory.append(
            {
                "path": relative,
                "byte_length": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
        )

    paths = validate_evidence_paths(item["path"] for item in inventory)
    by_path = {item["path"]: item for item in inventory}
    if len(by_path) != len(paths):
        raise AcquisitionError("snapshot contains colliding paths")
    for relative, expected_digest in expectation.required_sha256.items():
        item = by_path.get(relative)
        if item is None:
            raise AcquisitionError(f"required snapshot file is missing: {relative}")
        if item["sha256"] != expected_digest:
            raise AcquisitionError(f"snapshot hash mismatch: {relative}")

    receipt: dict[str, Any] = {
        "schema_id": "https://aluclu.org/schemas/alc_r0/v1/acquisition-receipt.schema.json",
        "schema_version": 1,
        "experiment_id": "alc-r0-smollm2-135m-v1",
        "repository": expectation.repository,
        "revision": expectation.revision,
        "trust_remote_code": False,
        "safetensors_only": True,
        "files": inventory,
    }
    receipt["inventory_sha256"] = hashlib.sha256(
        canonical_json_bytes(inventory)
    ).hexdigest()
    return receipt
