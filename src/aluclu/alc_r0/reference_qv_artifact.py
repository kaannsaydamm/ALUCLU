"""Bounded, non-authorizing records for the larger same-host q/v reference.

Cooperating callers must exclusively own quiescent factors/base. This is not a
signed .alc container, optimizer-state checkpoint, host attestation, or training
permission. No filesystem access or executable deserialization occurs here.
"""

from __future__ import annotations

import hashlib
import json
import re

import torch
from safetensors.torch import load as load_safetensors
from safetensors.torch import save as save_safetensors

from .acquisition import SMOLLM2_135M
from .canonical import (
    CanonicalEvidenceError,
    canonical_json_bytes,
    parse_canonical_json,
)
from .checkpoint_execution import CheckpointExecutionError
from .checkpoint_optimizer import _group
from .reference_qv_lora import ReferenceQVLoRA
from .reference_qv_wrapper import PinnedLlamaQVReferenceWrapper

MAX_ARTIFACT_BYTES = 2 * 1024 * 1024
MAX_MANIFEST_BYTES = 4096
MAX_HEADER_BYTES = 65536
_SHAPES = {
    f"factors.{layer}.{target}.{factor}": shape
    for layer in range(30)
    for target, width in (("q", 576), ("v", 192))
    for factor, shape in (("A", (8, 576)), ("B", (width, 8)))
}


class ReferenceArtifactError(ValueError):
    """The same-host reference record or ownership bindings are invalid."""


def _seed(value):
    if type(value) is not int or not 0 <= value < 2**63:
        raise ReferenceArtifactError("invalid reference initialization seed")
    return value


def _storage(tensor):
    if tensor.layout != torch.strided or tensor.device.type not in {"cpu", "cuda"}:
        raise ReferenceArtifactError("materialized CPU/CUDA dense tensors required")
    return tensor.device, tensor.untyped_storage().data_ptr()


def _live_factors(reference):
    if type(reference) is not ReferenceQVLoRA:
        raise ReferenceArtifactError("exact ReferenceQVLoRA required")
    _seed(reference.initialization_seed)
    named = tuple(reference.named_parameters(remove_duplicate=False))
    if len(named) != 120 or {name for name, _ in named} != set(_SHAPES):
        raise ReferenceArtifactError("exact all-layer q/v factor roster required")
    if tuple(reference.named_buffers()):
        raise ReferenceArtifactError("reference buffers are not part of this format")
    result, used = {}, set()
    for name, parameter in sorted(named):
        if (
            type(parameter) is not torch.nn.Parameter
            or not parameter.is_leaf
            or not parameter.requires_grad
            or parameter.dtype != torch.float32
            or tuple(parameter.shape) != _SHAPES[name]
        ):
            raise ReferenceArtifactError("reference parameter contract differs")
        storage = _storage(parameter)
        if storage in used or not torch.isfinite(parameter).all().item():
            raise ReferenceArtifactError("nonfinite or aliased reference factors")
        used.add(storage)
        result[name] = parameter
    return result


def _manifest(seed, payload):
    return {
        "schema_id": "aluclu/alc-r0/qv-reference-artifact/v1",
        "schema_version": 1,
        "experiment_id": "alc-r0-smollm2-135m-v1",
        "reference_kind": "standard_qv_reference",
        "model_repository": SMOLLM2_135M.repository,
        "model_revision": SMOLLM2_135M.revision,
        "model_weight_sha256": SMOLLM2_135M.required_sha256["model.safetensors"],
        "layers": list(range(30)),
        "projection_widths": {"q": 576, "v": 192},
        "rank": 8,
        "alpha": 8,
        "initialization_seed": str(seed),
        "parameter_count": 460800,
        "parameter_matched": False,
        "tensor_byte_length": len(payload),
        "tensor_sha256": hashlib.sha256(payload).hexdigest(),
        "training_authority": False,
    }


def serialize_reference(reference):
    """Clone only validated factors into deterministic JSON/SafeTensors bytes."""
    factors = _live_factors(reference)
    tensors = {
        name: value.detach().to(device="cpu").contiguous().clone()
        for name, value in factors.items()
    }
    payload = save_safetensors(tensors)
    manifest = canonical_json_bytes(_manifest(reference.initialization_seed, payload))
    if (
        len(manifest) > MAX_MANIFEST_BYTES
        or len(manifest) + len(payload) > MAX_ARTIFACT_BYTES
    ):
        raise ReferenceArtifactError("reference artifact exceeds its separate bound")
    return manifest, payload


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ReferenceArtifactError("duplicate SafeTensors header key")
        result[key] = value
    return result


def _reject_constant(value):
    raise ReferenceArtifactError("nonfinite header JSON constant")


def _header_before_allocation(payload):
    if len(payload) < 8:
        raise ReferenceArtifactError("truncated SafeTensors prefix")
    size = int.from_bytes(payload[:8], "little")
    if not 0 < size <= MAX_HEADER_BYTES or 8 + size > len(payload):
        raise ReferenceArtifactError("SafeTensors header bound/truncation")
    try:
        header = json.loads(
            payload[8 : 8 + size].decode("utf-8"),
            object_pairs_hook=_unique,
            parse_constant=_reject_constant,
        )
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ReferenceArtifactError("invalid bounded SafeTensors header") from exc
    if type(header) is not dict or set(header) != set(_SHAPES):
        raise ReferenceArtifactError("exact tensor header names required")
    offsets = []
    for name, shape in _SHAPES.items():
        entry = header[name]
        if (
            type(entry) is not dict
            or set(entry) != {"dtype", "shape", "data_offsets"}
            or entry["dtype"] != "F32"
            or type(entry["shape"]) is not list
            or any(type(value) is not int for value in entry["shape"])
            or entry["shape"] != list(shape)
        ):
            raise ReferenceArtifactError("tensor header dtype/shape differs")
        interval = entry["data_offsets"]
        if (
            type(interval) is not list
            or len(interval) != 2
            or any(type(value) is not int for value in interval)
            or interval[0] < 0
            or interval[1] - interval[0] != shape[0] * shape[1] * 4
        ):
            raise ReferenceArtifactError("tensor header offset/length differs")
        offsets.append(tuple(interval))
    cursor = 0
    for start, end in sorted(offsets):
        if start != cursor:
            raise ReferenceArtifactError("overlapping or gapped tensor offsets")
        cursor = end
    if cursor != 460800 * 4 or len(payload) != 8 + size + cursor:
        raise ReferenceArtifactError("tensor data length/trailing bytes differ")


def deserialize_reference(manifest_bytes, payload):
    """Preflight exact geometry/offsets before loading bounded CPU tensors."""
    if (
        type(manifest_bytes) is not bytes
        or type(payload) is not bytes
        or len(manifest_bytes) > MAX_MANIFEST_BYTES
        or len(manifest_bytes) + len(payload) > MAX_ARTIFACT_BYTES
    ):
        raise ReferenceArtifactError("reference bytes exceed type/size bound")
    try:
        manifest = parse_canonical_json(manifest_bytes)
    except (CanonicalEvidenceError, RecursionError) as exc:
        raise ReferenceArtifactError("invalid canonical reference manifest") from exc
    if type(manifest) is not dict:
        raise ReferenceArtifactError("reference manifest must be an object")
    seed = manifest.get("initialization_seed")
    if (
        type(seed) is not str
        or len(seed) > 19
        or not re.fullmatch(r"0|[1-9][0-9]*", seed)
    ):
        raise ReferenceArtifactError("seed must be canonical decimal text")
    seed = _seed(int(seed))
    if manifest_bytes != canonical_json_bytes(_manifest(seed, payload)):
        raise ReferenceArtifactError("reference manifest/host/tensor digest differs")
    _header_before_allocation(payload)
    try:
        tensors = load_safetensors(payload)
    except Exception as exc:
        raise ReferenceArtifactError("invalid SafeTensors payload") from exc
    if (
        set(tensors) != set(_SHAPES)
        or any(
            value.dtype != torch.float32
            or tuple(value.shape) != _SHAPES[name]
            or not torch.isfinite(value).all().item()
            for name, value in tensors.items()
        )
        or save_safetensors(tensors) != payload
    ):
        raise ReferenceArtifactError("nonfinite or noncanonical reference tensors")
    reference = ReferenceQVLoRA(seed=seed)
    reference.load_state_dict(tensors, strict=True)
    return reference


def reference_bindings(wrapper):
    """Return quiescent complete factor/base bindings; no actual host certificate."""
    if type(wrapper) is not PinnedLlamaQVReferenceWrapper:
        raise ReferenceArtifactError("exact q/v wrapper required")
    try:
        wrapper._assert_checkpoint_mutation_allowed()
    except CheckpointExecutionError as exc:
        raise ReferenceArtifactError(
            "optimizer preparation forbidden during lease"
        ) from exc
    factors = _live_factors(wrapper.reference)
    base = tuple(wrapper.base.parameters())
    if (
        not base
        or not wrapper.training
        or not wrapper.reference.training
        or any(module.training for module in wrapper.base.modules())
        or any(
            parameter.requires_grad or parameter.grad is not None for parameter in base
        )
        or {id(p) for p in wrapper.parameters()}
        != {id(p) for p in (*base, *factors.values())}
    ):
        raise ReferenceArtifactError("wrapper/base/factor ownership differs")
    base_storage = {_storage(value) for value in (*base, *wrapper.base.buffers())}
    if any(_storage(value) in base_storage for value in factors.values()):
        raise ReferenceArtifactError("reference storage aliases frozen base")
    return factors, base


def make_reference_optimizer(wrapper):
    """Construct fixed AdamW over exact factors only; do not step or authorize."""
    factors, _ = reference_bindings(wrapper)
    optimizer = torch.optim.AdamW(
        list(factors.values()),
        lr=3e-4,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0,
        foreach=False,
        fused=False,
    )
    _group(optimizer)
    return optimizer
