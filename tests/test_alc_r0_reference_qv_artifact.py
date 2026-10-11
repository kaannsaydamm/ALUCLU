"""Synthetic CPU q/v records and optimizer bindings, never learning evidence."""

import hashlib
import json

import pytest
import torch
from test_alc_r0_reference_qv_wrapper import fake_wrapper

from aluclu.alc_r0.canonical import canonical_json_bytes, parse_canonical_json
from aluclu.alc_r0.reference_qv_artifact import (
    ReferenceArtifactError,
    deserialize_reference,
    make_reference_optimizer,
    reference_bindings,
    serialize_reference,
)
from aluclu.alc_r0.reference_qv_lora import ReferenceQVLoRA


def test_reference_roundtrip_exact_bytes_and_separate_identity():
    reference = ReferenceQVLoRA(seed=17)
    with torch.no_grad():
        reference.factors["29"]["v"].B.fill_(0.125)
    manifest, payload = serialize_reference(reference)
    restored = deserialize_reference(manifest, payload)
    assert serialize_reference(restored) == (manifest, payload)
    assert len(payload) > 256 * 1024
    assert len(manifest) + len(payload) <= 2 * 1024 * 1024
    document = parse_canonical_json(manifest)
    assert document["reference_kind"] == "standard_qv_reference"
    assert document["parameter_count"] == 460800
    assert document["parameter_matched"] is False
    assert document["training_authority"] is False
    assert document["tensor_sha256"] == hashlib.sha256(payload).hexdigest()
    for name, parameter in reference.named_parameters():
        other = dict(restored.named_parameters())[name]
        assert torch.equal(parameter, other)
        assert parameter.data_ptr() != other.data_ptr()


@pytest.mark.parametrize(
    "field,value",
    [
        ("rank", 4),
        ("parameter_count", 460799),
        ("parameter_matched", True),
        ("training_authority", True),
        ("initialization_seed", "017"),
        ("model_revision", "wrong"),
        ("schema_version", True),
    ],
)
def test_manifest_drift_rejected(field, value):
    manifest, payload = serialize_reference(ReferenceQVLoRA(seed=17))
    document = parse_canonical_json(manifest)
    document[field] = value
    with pytest.raises(ReferenceArtifactError):
        deserialize_reference(canonical_json_bytes(document), payload)


@pytest.mark.parametrize(
    "bad", ["shape", "dtype", "offset", "missing", "extra", "duplicate", "deep"]
)
def test_header_rejected_before_tensor_loader(bad, monkeypatch):
    from aluclu.alc_r0 import reference_qv_artifact as module

    manifest, payload = serialize_reference(ReferenceQVLoRA(seed=17))
    length = int.from_bytes(payload[:8], "little")
    header = json.loads(payload[8 : 8 + length])
    name = next(iter(header))
    if bad == "shape":
        header[name]["shape"] = [2**60, 576]
    elif bad == "dtype":
        header[name]["dtype"] = "F64"
    elif bad == "offset":
        header[name]["data_offsets"] = [0, 2**60]
    elif bad == "missing":
        del header[name]
    elif bad == "extra":
        header["__metadata__"] = {"foreign": "payload"}
    encoded = json.dumps(header, separators=(",", ":")).encode()
    if bad == "duplicate":
        encoded = encoded[:-1] + b"," + json.dumps(name).encode() + b":{} }"
    elif bad == "deep":
        encoded = b"[" * 2000 + b"0" + b"]" * 2000
    changed = len(encoded).to_bytes(8, "little") + encoded + payload[8 + length :]
    document = parse_canonical_json(manifest)
    document["tensor_sha256"] = hashlib.sha256(changed).hexdigest()
    document["tensor_byte_length"] = len(changed)
    calls = []
    monkeypatch.setattr(module, "load_safetensors", lambda data: calls.append(data))
    with pytest.raises(ReferenceArtifactError):
        deserialize_reference(canonical_json_bytes(document), changed)
    assert calls == []


@pytest.mark.parametrize("bad", ["nonfinite", "alias", "missing", "buffer", "dtype"])
def test_invalid_live_factors_rejected(bad):
    reference = ReferenceQVLoRA(seed=17)
    factors = reference.factors["0"]["q"]
    if bad == "nonfinite":
        with torch.no_grad():
            factors.B.fill_(float("nan"))
    elif bad == "alias":
        factors.B = torch.nn.Parameter(factors.A.T)
    elif bad == "missing":
        del reference.factors["29"]
    elif bad == "buffer":
        reference.register_buffer("foreign", torch.zeros(1))
    else:
        reference.to(dtype=torch.float64)
    with pytest.raises(ReferenceArtifactError):
        serialize_reference(reference)


@pytest.mark.parametrize(
    "bad", ["prefix", "header_bound", "truncated", "overlap", "gap", "trailing"]
)
def test_record_boundaries_rejected_before_loader(bad, monkeypatch):
    from aluclu.alc_r0 import reference_qv_artifact as module

    manifest, payload = serialize_reference(ReferenceQVLoRA(seed=17))
    length = int.from_bytes(payload[:8], "little")
    header = json.loads(payload[8 : 8 + length])
    if bad == "prefix":
        changed = payload[:7]
    elif bad == "header_bound":
        changed = (module.MAX_HEADER_BYTES + 1).to_bytes(8, "little") + payload[8:]
    elif bad == "truncated":
        changed = payload[: 8 + length - 1]
    elif bad == "trailing":
        changed = payload + b"x"
    else:
        entries = sorted(header.values(), key=lambda entry: entry["data_offsets"][0])
        start, end = entries[1]["data_offsets"]
        shift = -4 if bad == "overlap" else 4
        entries[1]["data_offsets"] = [start + shift, end + shift]
        encoded = json.dumps(header, separators=(",", ":")).encode()
        changed = len(encoded).to_bytes(8, "little") + encoded + payload[8 + length :]
    document = parse_canonical_json(manifest)
    document["tensor_sha256"] = hashlib.sha256(changed).hexdigest()
    document["tensor_byte_length"] = len(changed)
    calls = []
    monkeypatch.setattr(module, "load_safetensors", lambda data: calls.append(data))
    with pytest.raises(ReferenceArtifactError):
        deserialize_reference(canonical_json_bytes(document), changed)
    assert calls == []


def test_base_buffer_alias_rejected():
    wrapper = fake_wrapper().train()
    factor = wrapper.reference.factors["0"]["q"].A
    wrapper.base.register_buffer("foreign_alias", factor.detach())
    with pytest.raises(ReferenceArtifactError):
        reference_bindings(wrapper)


def test_optimizer_owns_exact_reference_parameters_not_base():
    wrapper = fake_wrapper().train()
    mapping, base = reference_bindings(wrapper)
    optimizer = make_reference_optimizer(wrapper)
    assert len(mapping) == 120
    assert sum(parameter.numel() for parameter in mapping.values()) == 460800
    assert [id(p) for p in optimizer.param_groups[0]["params"]] == [
        id(mapping[name]) for name in sorted(mapping)
    ]
    assert {id(p) for p in base}.isdisjoint(id(p) for p in mapping.values())
    assert optimizer.state == {}
    with wrapper.checkpoint_session():
        with pytest.raises(ReferenceArtifactError):
            make_reference_optimizer(wrapper)


def test_base_storage_alias_and_extra_wrapper_parameters_rejected():
    wrapper = fake_wrapper().train()
    factor = wrapper.reference.factors["0"]["q"].A
    wrapper.base.weight = torch.nn.Parameter(factor.detach(), requires_grad=False)
    with pytest.raises(ReferenceArtifactError):
        reference_bindings(wrapper)
    wrapper = fake_wrapper().train()
    wrapper.register_parameter("foreign", torch.nn.Parameter(torch.ones(1)))
    with pytest.raises(ReferenceArtifactError):
        make_reference_optimizer(wrapper)
