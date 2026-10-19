from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import torch
from safetensors.torch import save

from aluclu.alc_r0.canonical import canonical_json_bytes, parse_canonical_json
from aluclu.alc_r0.capsule_artifact import (
    CapsuleArtifactError,
    deserialize_capsule,
    serialize_capsule,
)
from aluclu.alc_r0.research_capsule import ResearchCapsuleV0
from aluclu.alc_r0.schema_validation import validate_r0_document

SCHEMA_ROOT = Path(__file__).parents[1] / "schemas" / "alc_r0" / "v1"


def _changed_manifest(manifest_bytes: bytes, **changes: object) -> bytes:
    manifest = parse_canonical_json(manifest_bytes)
    assert isinstance(manifest, dict)
    manifest.update(changes)
    return canonical_json_bytes(manifest)


@pytest.mark.parametrize("ports,rank", [((14,), 4), ((29,), 8), ((14, 29), 16)])
def test_canonical_capsule_round_trip_and_size_bound(
    ports: tuple[int, ...], rank: int
) -> None:
    first = ResearchCapsuleV0(ports=ports, rank=rank, seed=20260921)
    with torch.no_grad():
        for name, parameter in first.named_parameters():
            if name.endswith(".B"):
                parameter.fill_(0.125)
    same = ResearchCapsuleV0(ports=ports, rank=rank, seed=20260921)
    same.load_state_dict(first.state_dict())

    manifest_bytes, tensor_bytes = serialize_capsule(first)
    same_manifest, same_tensors = serialize_capsule(same)
    restored = deserialize_capsule(manifest_bytes, tensor_bytes)
    manifest = parse_canonical_json(manifest_bytes)
    assert (
        validate_r0_document(
            manifest_bytes,
            schema_name="research-capsule-artifact",
            schema_root=SCHEMA_ROOT,
        )
        == manifest
    )

    assert (manifest_bytes, tensor_bytes) == (same_manifest, same_tensors)
    assert len(manifest_bytes) + len(tensor_bytes) <= 256 * 1024
    assert manifest["tensor_sha256"] == hashlib.sha256(tensor_bytes).hexdigest()
    assert manifest["tensor_byte_length"] == len(tensor_bytes)
    assert manifest["parameter_count"] == 1152 * rank * len(ports)
    assert manifest["training_authority"] is False
    assert restored.ports == ports
    assert restored.rank == rank
    assert restored.initialization_seed == 20260921
    assert all(
        torch.equal(restored.state_dict()[name], first.state_dict()[name])
        for name in first.state_dict()
    )


def test_zero_control_round_trip_is_never_trainable_and_all_positive_zero() -> None:
    zero = ResearchCapsuleV0.zero_control(ports=(14, 29), rank=16)
    manifest_bytes, tensor_bytes = serialize_capsule(zero)

    restored = deserialize_capsule(manifest_bytes, tensor_bytes)
    manifest = parse_canonical_json(manifest_bytes)

    assert manifest["control_kind"] == "all_factors_zero"
    assert len(manifest_bytes) == 674
    assert len(tensor_bytes) == 147776
    assert hashlib.sha256(manifest_bytes).hexdigest() == (
        "c2dfcb53668db046195eda97a721cd43a49ebf5fbbd3ef6f3fa150d357d02084"
    )
    assert hashlib.sha256(tensor_bytes).hexdigest() == (
        "f251ab9a14f995dc446b90dc1873c3fa7745f5df5f29994c09dca9c124125800"
    )
    assert restored.control_kind == "all_factors_zero"
    assert all(not parameter.requires_grad for parameter in restored.parameters())
    assert all(
        torch.count_nonzero(parameter) == 0 for parameter in restored.parameters()
    )
    assert all(
        not torch.signbit(parameter).any() for parameter in restored.parameters()
    )


def test_wrong_host_or_noncanonical_manifest_is_rejected() -> None:
    manifest_bytes, tensor_bytes = serialize_capsule(
        ResearchCapsuleV0(ports=(14,), rank=4, seed=1)
    )
    manifest = parse_canonical_json(manifest_bytes)
    assert isinstance(manifest, dict)

    with pytest.raises(CapsuleArtifactError):
        deserialize_capsule(
            _changed_manifest(manifest_bytes, model_revision="0" * 40), tensor_bytes
        )
    with pytest.raises(CapsuleArtifactError):
        deserialize_capsule(
            _changed_manifest(manifest_bytes, unexpected=True), tensor_bytes
        )
    with pytest.raises(CapsuleArtifactError):
        deserialize_capsule(b" " + manifest_bytes, tensor_bytes)
    with pytest.raises(CapsuleArtifactError):
        deserialize_capsule(
            _changed_manifest(manifest_bytes, training_authority=0), tensor_bytes
        )
    with pytest.raises(CapsuleArtifactError):
        deserialize_capsule(
            _changed_manifest(manifest_bytes, schema_version=True), tensor_bytes
        )


def test_tampered_or_wrong_shape_tensors_are_rejected() -> None:
    manifest_bytes, tensor_bytes = serialize_capsule(
        ResearchCapsuleV0(ports=(14,), rank=4, seed=1)
    )
    with pytest.raises(CapsuleArtifactError):
        deserialize_capsule(
            manifest_bytes, tensor_bytes[:-1] + bytes([tensor_bytes[-1] ^ 1])
        )
    with pytest.raises(CapsuleArtifactError):
        deserialize_capsule(manifest_bytes, b"not safetensors")

    wrong_shape = save(
        {
            "factors.14.A": torch.zeros(4, 575),
            "factors.14.B": torch.zeros(576, 4),
        }
    )
    with pytest.raises(CapsuleArtifactError):
        deserialize_capsule(
            _changed_manifest(
                manifest_bytes,
                tensor_sha256=hashlib.sha256(wrong_shape).hexdigest(),
                tensor_byte_length=len(wrong_shape),
            ),
            wrong_shape,
        )


def test_zero_control_rejects_negative_zero_and_nonzero_tensor() -> None:
    manifest_bytes, _ = serialize_capsule(
        ResearchCapsuleV0.zero_control(ports=(14,), rank=4)
    )
    for value in (-0.0, 0.125):
        factors = {
            "factors.14.A": torch.zeros(4, 576),
            "factors.14.B": torch.zeros(576, 4),
        }
        factors["factors.14.B"][0, 0] = value
        tensor_bytes = save(factors)
        altered = _changed_manifest(
            manifest_bytes,
            tensor_sha256=hashlib.sha256(tensor_bytes).hexdigest(),
            tensor_byte_length=len(tensor_bytes),
        )
        with pytest.raises(CapsuleArtifactError):
            deserialize_capsule(altered, tensor_bytes)


def test_serializer_rejects_nonfinite_or_non_fp32_factors() -> None:
    capsule = ResearchCapsuleV0(ports=(14,), rank=4, seed=1)
    with torch.no_grad():
        dict(capsule.named_parameters())["factors.14.A"][0, 0] = float("nan")
    with pytest.raises(CapsuleArtifactError):
        serialize_capsule(capsule)

    capsule = ResearchCapsuleV0(ports=(14,), rank=4, seed=1).to(torch.bfloat16)
    with pytest.raises(CapsuleArtifactError):
        serialize_capsule(capsule)


def test_full_signed_63_bit_seed_round_trips_as_decimal_text() -> None:
    seed = 2**63 - 1
    manifest_bytes, tensor_bytes = serialize_capsule(
        ResearchCapsuleV0(ports=(14,), rank=4, seed=seed)
    )
    manifest = parse_canonical_json(manifest_bytes)

    assert manifest["initialization_seed"] == str(seed)
    assert deserialize_capsule(manifest_bytes, tensor_bytes).initialization_seed == seed
