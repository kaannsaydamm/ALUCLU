"""Bounded CPU step1 factor/moment records, not training or resume acceptance.

Cooperating callers exclusively own quiescent state and do not monkeypatch
runtime behavior. No disk, assets, optimizer step or executable deserialization.
Byte digests bind consistency, not host computation, authenticity or authority.
Peak RAM exceeds serialized bounds; stochastic/cursor state is not captured.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import re
from dataclasses import dataclass

import torch
from safetensors.torch import load as load_safetensors
from safetensors.torch import save as save_safetensors

from .canonical import (
    CanonicalEvidenceError,
    canonical_json_bytes,
    parse_canonical_json,
)
from .checkpoint_execution import _digest, _tensor_stamp
from .checkpoint_fidelity import CheckpointFidelityError
from .checkpoint_observation import _base_digest
from .checkpoint_optimizer import _BOOLEAN, _NUMERIC, _snapshot
from .reference_qv_artifact import (
    _SHAPES,
    MAX_ARTIFACT_BYTES,
    ReferenceArtifactError,
    _reject_constant,
    _storage,
    _unique,
    make_reference_optimizer,
    reference_bindings,
    serialize_reference,
)

MAX_MANIFEST_BYTES = 16 * 1024
MAX_HEADER_BYTES = 128 * 1024
MAX_PAYLOAD_BYTES = 4 * 1024 * 1024
MAX_RECORD_BYTES = 8 * 1024 * 1024
_ROLES = ("step", "exp_avg", "exp_avg_sq")
_STATE_SHAPES = {
    f"{role}/{name}": (() if role == "step" else shape)
    for name, shape in _SHAPES.items()
    for role in _ROLES
}
_LOCAL_HOOKS = (
    "_optimizer_step_pre_hooks",
    "_optimizer_step_post_hooks",
    "_optimizer_state_dict_pre_hooks",
    "_optimizer_state_dict_post_hooks",
    "_optimizer_load_state_dict_pre_hooks",
    "_optimizer_load_state_dict_post_hooks",
)


class ReferenceResumeError(ValueError):
    """A bounded resume record or live ownership contract differs."""


@dataclass(frozen=True)
class ReferenceResumeRecord:
    factor_manifest: bytes
    factor_payload: bytes
    optimizer_manifest: bytes
    optimizer_payload: bytes


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _runtime():
    version = str(torch.__version__)
    if not re.fullmatch(r"2\.14\.\d+(?:\+[^ ]+)?", version):
        raise ReferenceResumeError("fixed Torch2.14 runtime required")
    return version


def _hooks(optimizer=None):
    module = importlib.import_module("torch.optim.optimizer")
    for name in ("_global_optimizer_pre_hooks", "_global_optimizer_post_hooks"):
        hooks = getattr(module, name, None)
        if hooks is None or len(hooks):
            raise ReferenceResumeError("global optimizer hooks/schema forbidden")
    if optimizer is not None:
        for name in _LOCAL_HOOKS:
            hooks = getattr(optimizer, name, None)
            if hooks is None or len(hooks):
                raise ReferenceResumeError("local optimizer hooks/schema forbidden")


def _live(wrapper):
    _runtime()
    _hooks()
    factors, base = reference_bindings(wrapper)
    if (
        any(p.device.type != "cpu" or p.dtype != torch.float32 for p in base)
        or any(p.device.type != "cpu" or p.grad is not None for p in factors.values())
        or any(
            b.device.type != "cpu" or b.requires_grad for b in wrapper.base.buffers()
        )
    ):
        raise ReferenceResumeError("quiescent CPU FP32 base/factors required")
    named = tuple(wrapper.base.named_parameters()) + tuple(wrapper.base.named_buffers())
    stamps = tuple((name, _tensor_stamp(value)) for name, value in named)
    factor_stamps = tuple(
        (name, _tensor_stamp(value)) for name, value in factors.items()
    )
    modules = tuple((name, id(m), m.training) for name, m in wrapper.named_modules())
    identity = (
        id(wrapper.base),
        id(wrapper.reference),
        id(wrapper._checkpoint_controller),
    )
    evidence = (
        identity,
        modules,
        stamps,
        factor_stamps,
        _base_digest(wrapper.base),
        _digest(tuple(factors.items())),
    )
    return factors, base, evidence


def _state(wrapper, optimizer):
    _hooks(optimizer)
    factors, base, binding = _live(wrapper)
    _snapshot(optimizer, factors, base, 1)
    buffers = {_storage(value) for value in wrapper.base.buffers()}
    named = tuple(
        (f"{role}/{name}", optimizer.state[p][role])
        for name, p in sorted(factors.items())
        for role in _ROLES
    )
    if any(_storage(value) in buffers for _, value in named):
        raise ReferenceResumeError("optimizer buffers alias frozen base buffer")
    stamps = tuple((name, _tensor_stamp(value)) for name, value in named)
    group_ids = tuple(id(p) for p in optimizer.param_groups[0]["params"])
    evidence = (binding, id(optimizer), group_ids, stamps, _digest(named))
    return named, evidence


def _manifest(factor_manifest, factor_payload, payload, base_digest):
    return {
        "schema_id": "aluclu/alc-r0/qv-reference-resume/v1",
        "schema_version": 1,
        "torch_version": _runtime(),
        "device": "cpu",
        "dtype": "F32",
        "step": 1,
        "optimizer_group": {**_NUMERIC, **_BOOLEAN, "betas": [0.9, 0.999]},
        "factor_manifest_length": len(factor_manifest),
        "factor_manifest_sha256": _sha(factor_manifest),
        "factor_payload_length": len(factor_payload),
        "factor_payload_sha256": _sha(factor_payload),
        "base_sha256": base_digest,
        "optimizer_payload_length": len(payload),
        "optimizer_payload_sha256": _sha(payload),
        "training_authority": False,
    }


def _bounds(record):
    if type(record) is not ReferenceResumeRecord:
        raise ReferenceResumeError("exact immutable resume record required")
    fields = (
        record.factor_manifest,
        record.factor_payload,
        record.optimizer_manifest,
        record.optimizer_payload,
    )
    if (
        any(type(value) is not bytes for value in fields)
        or len(record.factor_manifest) > 4096
        or len(record.factor_manifest) + len(record.factor_payload) > MAX_ARTIFACT_BYTES
        or len(record.optimizer_manifest) > MAX_MANIFEST_BYTES
        or len(record.optimizer_payload) > MAX_PAYLOAD_BYTES
        or sum(map(len, fields)) > MAX_RECORD_BYTES
    ):
        raise ReferenceResumeError("record type/serialized size bounds differ")


def _header(payload):
    if len(payload) < 8:
        raise ReferenceResumeError("truncated optimizer prefix")
    size = int.from_bytes(payload[:8], "little")
    if not 0 < size <= MAX_HEADER_BYTES or 8 + size > len(payload):
        raise ReferenceResumeError("optimizer header bound/truncation")
    try:
        header = json.loads(
            payload[8 : 8 + size].decode("utf-8"),
            object_pairs_hook=_unique,
            parse_constant=_reject_constant,
        )
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ReferenceResumeError("invalid optimizer header JSON") from exc
    if type(header) is not dict or set(header) != set(_STATE_SHAPES):
        raise ReferenceResumeError("exact optimizer tensor names required")
    offsets = []
    for name, shape in _STATE_SHAPES.items():
        entry = header[name]
        if (
            type(entry) is not dict
            or set(entry) != {"dtype", "shape", "data_offsets"}
            or entry["dtype"] != "F32"
            or type(entry["shape"]) is not list
            or any(type(v) is not int for v in entry["shape"])
            or entry["shape"] != list(shape)
        ):
            raise ReferenceResumeError("optimizer tensor shape/dtype differs")
        interval = entry["data_offsets"]
        if (
            type(interval) is not list
            or len(interval) != 2
            or any(type(v) is not int for v in interval)
            or interval[0] < 0
            or interval[1] - interval[0] != math.prod(shape) * 4
        ):
            raise ReferenceResumeError("optimizer offset/length differs")
        offsets.append(tuple(interval))
    cursor = 0
    for start, end in sorted(offsets):
        if start != cursor:
            raise ReferenceResumeError("optimizer overlapping/gapped offsets")
        cursor = end
    if cursor != 3686880 or len(payload) != 8 + size + cursor:
        raise ReferenceResumeError("optimizer data length/trailing bytes differ")


def _values(tensors):
    if type(tensors) is not dict or set(tensors) != set(_STATE_SHAPES):
        raise ReferenceResumeError("complete optimizer tensors required")
    for name, shape in _STATE_SHAPES.items():
        value = tensors[name]
        if (
            not isinstance(value, torch.Tensor)
            or value.device.type != "cpu"
            or value.dtype != torch.float32
            or tuple(value.shape) != shape
            or value.requires_grad
            or not torch.isfinite(value).all().item()
            or (name.startswith("step/") and float(value.item()) != 1)
            or (name.startswith("exp_avg_sq/") and (value < 0).any().item())
        ):
            raise ReferenceResumeError("optimizer finite/step/moment values differ")


def serialize_reference_resume(wrapper, optimizer):
    """Read-only step1 export; no callbacks, steps or execution authority."""
    try:
        named, before = _state(wrapper, optimizer)
        factor_manifest, factor_payload = serialize_reference(wrapper.reference)
        tensors = {name: value.detach().contiguous().clone() for name, value in named}
        _values(tensors)
        payload = save_safetensors(tensors)
        record = ReferenceResumeRecord(
            factor_manifest,
            factor_payload,
            canonical_json_bytes(
                _manifest(
                    factor_manifest, factor_payload, payload, _base_digest(wrapper.base)
                )
            ),
            payload,
        )
        _bounds(record)
        _header(payload)
        if _state(wrapper, optimizer)[1] != before:
            raise ReferenceResumeError("source binding/state changed during export")
        return record
    except (
        ReferenceArtifactError,
        CheckpointFidelityError,
        CanonicalEvidenceError,
        RecursionError,
    ) as exc:
        raise ReferenceResumeError("invalid live resume export") from exc


def restore_reference_optimizer(wrapper, record):
    """Validate then publish fresh optimizer; never alter wrapper/mount/factors."""
    try:
        _bounds(record)
        factors, _, before = _live(wrapper)
        factor_manifest, factor_payload = serialize_reference(wrapper.reference)
        if (record.factor_manifest, record.factor_payload) != (
            factor_manifest,
            factor_payload,
        ):
            raise ReferenceResumeError("mounted factor bytes differ from record")
        parse_canonical_json(record.optimizer_manifest)
        expected = canonical_json_bytes(
            _manifest(
                factor_manifest,
                factor_payload,
                record.optimizer_payload,
                _base_digest(wrapper.base),
            )
        )
        if record.optimizer_manifest != expected:
            raise ReferenceResumeError("resume manifest/binding/runtime/digest differs")
        _header(record.optimizer_payload)
        try:
            tensors = load_safetensors(record.optimizer_payload)
        except Exception as exc:
            raise ReferenceResumeError("invalid bounded optimizer SafeTensors") from exc
        _values(tensors)
        if save_safetensors(tensors) != record.optimizer_payload:
            raise ReferenceResumeError("optimizer payload is not canonical")
        if _live(wrapper)[2] != before:
            raise ReferenceResumeError("live binding changed while parsing")
        optimizer = make_reference_optimizer(wrapper)
        for name, parameter in factors.items():
            optimizer.state[parameter] = {
                role: tensors[f"{role}/{name}"].clone() for role in _ROLES
            }
        _state(wrapper, optimizer)
        if _live(wrapper)[2] != before:
            raise ReferenceResumeError("live binding changed before publication")
        return optimizer
    except (
        ReferenceArtifactError,
        CheckpointFidelityError,
        CanonicalEvidenceError,
        RecursionError,
    ) as exc:
        raise ReferenceResumeError("invalid resume restore") from exc
