"""Canonical, non-authorizing R0 capsule factor artifact.

This is an in-memory reference serializer. It does not grant training,
activation, or held-out evaluation authority.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

import torch
from safetensors.torch import load as load_safetensors
from safetensors.torch import save as save_safetensors

from aluclu.alc_r0.acquisition import SMOLLM2_135M
from aluclu.alc_r0.canonical import (
    CanonicalEvidenceError,
    canonical_json_bytes,
    parse_canonical_json,
)
from aluclu.alc_r0.research_capsule import (
    ALLOWED_PORTS,
    ALLOWED_RANKS,
    CANONICAL_WIDTH,
    NORMALIZATION_EPSILON,
    ResearchCapsuleV0,
)

MAX_ARTIFACT_BYTES = 256 * 1024
_SCHEMA_ID = (
    "https://aluclu.org/schemas/alc_r0/v1/research-capsule-artifact.schema.json"
)
_MANIFEST_KEYS = frozenset(
    {
        "schema_id",
        "schema_version",
        "experiment_id",
        "model_repository",
        "model_revision",
        "model_weight_sha256",
        "bridge",
        "width",
        "ports",
        "rank",
        "alpha",
        "normalization_epsilon",
        "initialization_seed",
        "control_kind",
        "parameter_count",
        "tensor_byte_length",
        "tensor_sha256",
        "training_authority",
    }
)


class CapsuleArtifactError(ValueError):
    """The supplied factors or canonical artifact violate the frozen R0 grid."""


def _expected_shapes(ports: tuple[int, ...], rank: int) -> dict[str, tuple[int, int]]:
    return {
        f"factors.{port}.{factor}": shape
        for port in ports
        for factor, shape in (
            ("A", (rank, CANONICAL_WIDTH)),
            ("B", (CANONICAL_WIDTH, rank)),
        )
    }


def _validated_tensors(
    tensors: dict[str, torch.Tensor], ports: tuple[int, ...], rank: int
) -> dict[str, torch.Tensor]:
    shapes = _expected_shapes(ports, rank)
    if set(tensors) != set(shapes):
        raise CapsuleArtifactError("capsule factor names differ from the grid")
    result: dict[str, torch.Tensor] = {}
    for name in sorted(shapes):
        tensor = tensors[name]
        if tensor.dtype != torch.float32 or tuple(tensor.shape) != shapes[name]:
            raise CapsuleArtifactError(f"capsule factor dtype or shape drift: {name}")
        if not torch.isfinite(tensor).all().item():
            raise CapsuleArtifactError(f"capsule factor is nonfinite: {name}")
        result[name] = tensor.detach().to(device="cpu").contiguous()
    return result


def _positive_zero_only(tensors: dict[str, torch.Tensor]) -> bool:
    return all(
        not torch.count_nonzero(tensor).item()
        and not torch.signbit(tensor).any().item()
        for tensor in tensors.values()
    )


def _grid(
    ports: object, rank: object, seed: object
) -> tuple[tuple[int, ...], int, int]:
    if not isinstance(ports, (list, tuple)) or any(type(p) is not int for p in ports):
        raise CapsuleArtifactError("capsule ports must be integer IDs")
    selected = tuple(ports)
    if selected not in ALLOWED_PORTS:
        raise CapsuleArtifactError("capsule ports are outside the frozen grid")
    if type(rank) is not int or rank not in ALLOWED_RANKS:
        raise CapsuleArtifactError("capsule rank is outside the frozen grid")
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise CapsuleArtifactError("initialization seed is outside the frozen range")
    return selected, rank, seed


def _manifest(
    *,
    ports: tuple[int, ...],
    rank: int,
    seed: int,
    control_kind: str,
    tensor_bytes: bytes,
) -> dict[str, Any]:
    return {
        "schema_id": _SCHEMA_ID,
        "schema_version": 1,
        "experiment_id": "alc-r0-smollm2-135m-v1",
        "model_repository": SMOLLM2_135M.repository,
        "model_revision": SMOLLM2_135M.revision,
        "model_weight_sha256": SMOLLM2_135M.required_sha256["model.safetensors"],
        "bridge": "identity_576",
        "width": CANONICAL_WIDTH,
        "ports": list(ports),
        "rank": rank,
        "alpha": rank,
        "normalization_epsilon": NORMALIZATION_EPSILON,
        "initialization_seed": str(seed),
        "control_kind": control_kind,
        "parameter_count": 2 * CANONICAL_WIDTH * rank * len(ports),
        "tensor_byte_length": len(tensor_bytes),
        "tensor_sha256": hashlib.sha256(tensor_bytes).hexdigest(),
        "training_authority": False,
    }


def serialize_capsule(capsule: ResearchCapsuleV0) -> tuple[bytes, bytes]:
    """Return canonical JSON manifest and SafeTensors factor bytes."""

    if not isinstance(capsule, ResearchCapsuleV0):
        raise CapsuleArtifactError("ResearchCapsuleV0 is required")
    ports, rank, seed = _grid(capsule.ports, capsule.rank, capsule.initialization_seed)
    kind = capsule.control_kind
    if kind not in ("trainable_init", "all_factors_zero"):
        raise CapsuleArtifactError("unknown R0 capsule control kind")
    tensors = _validated_tensors(dict(capsule.state_dict()), ports, rank)
    if kind == "all_factors_zero":
        if seed != 0 or not _positive_zero_only(tensors):
            raise CapsuleArtifactError("zero control contains nonzero factor bits")
        if any(parameter.requires_grad for parameter in capsule.parameters()):
            raise CapsuleArtifactError("zero control factors must remain frozen")
    tensor_bytes = save_safetensors(tensors)
    manifest_bytes = canonical_json_bytes(
        _manifest(
            ports=ports,
            rank=rank,
            seed=seed,
            control_kind=kind,
            tensor_bytes=tensor_bytes,
        )
    )
    if len(manifest_bytes) + len(tensor_bytes) > MAX_ARTIFACT_BYTES:
        raise CapsuleArtifactError("canonical capsule exceeds the 256 KiB cap")
    return manifest_bytes, tensor_bytes


def deserialize_capsule(
    manifest_bytes: bytes, tensor_bytes: bytes
) -> ResearchCapsuleV0:
    """Load only a complete, exact, pinned-host canonical factor artifact."""

    if len(manifest_bytes) + len(tensor_bytes) > MAX_ARTIFACT_BYTES:
        raise CapsuleArtifactError("canonical capsule exceeds the 256 KiB cap")
    try:
        manifest = parse_canonical_json(manifest_bytes)
    except CanonicalEvidenceError as exc:
        raise CapsuleArtifactError("manifest is not canonical JSON") from exc
    if not isinstance(manifest, dict) or set(manifest) != _MANIFEST_KEYS:
        raise CapsuleArtifactError("capsule manifest field set is not exact")
    seed_text = manifest["initialization_seed"]
    if (
        not isinstance(seed_text, str)
        or len(seed_text) > 19
        or not re.fullmatch(r"0|[1-9][0-9]*", seed_text)
    ):
        raise CapsuleArtifactError("initialization seed must be canonical decimal text")
    ports, rank, seed = _grid(manifest["ports"], manifest["rank"], int(seed_text))
    kind = manifest["control_kind"]
    if kind not in ("trainable_init", "all_factors_zero"):
        raise CapsuleArtifactError("unknown R0 capsule control kind")
    if kind == "all_factors_zero" and seed != 0:
        raise CapsuleArtifactError("zero control seed must be zero")
    expected = _manifest(
        ports=ports,
        rank=rank,
        seed=seed,
        control_kind=kind,
        tensor_bytes=tensor_bytes,
    )
    if manifest_bytes != canonical_json_bytes(expected):
        raise CapsuleArtifactError("capsule manifest, host, or tensor digest mismatch")
    try:
        loaded = load_safetensors(tensor_bytes)
    except Exception as exc:
        raise CapsuleArtifactError("invalid SafeTensors factor payload") from exc
    tensors = _validated_tensors(loaded, ports, rank)
    if save_safetensors(tensors) != tensor_bytes:
        raise CapsuleArtifactError("noncanonical SafeTensors factor payload")
    if kind == "all_factors_zero" and not _positive_zero_only(tensors):
        raise CapsuleArtifactError("zero control contains nonzero factor bits")

    capsule = (
        ResearchCapsuleV0.zero_control(ports=ports, rank=rank)
        if kind == "all_factors_zero"
        else ResearchCapsuleV0(ports=ports, rank=rank, seed=seed)
    )
    capsule.load_state_dict(tensors, strict=True)
    return capsule
