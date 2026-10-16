"""Manual CPU moment fixtures only: no updates/host/resume capability proof."""

import hashlib
import importlib
import json
from dataclasses import replace

import pytest
import torch
from safetensors.torch import load, save
from test_alc_r0_reference_qv_optimizer import populated
from test_alc_r0_reference_qv_wrapper import fake_wrapper

from aluclu.alc_r0.canonical import canonical_json_bytes, parse_canonical_json
from aluclu.alc_r0.reference_qv_artifact import (
    deserialize_reference,
    serialize_reference,
)
from aluclu.alc_r0.reference_qv_optimizer import compare_reference_optimizer_states
from aluclu.alc_r0.reference_qv_resume import (
    ReferenceResumeError,
    restore_reference_optimizer,
    serialize_reference_resume,
)


def target(source, record):
    wrapper = fake_wrapper().train()
    wrapper.base.load_state_dict(source.base.state_dict())
    wrapper.reference = deserialize_reference(
        record.factor_manifest, record.factor_payload
    )
    return wrapper


def with_payload(record, payload):
    manifest = parse_canonical_json(record.optimizer_manifest)
    manifest["optimizer_payload_sha256"] = hashlib.sha256(payload).hexdigest()
    manifest["optimizer_payload_length"] = len(payload)
    return replace(
        record,
        optimizer_payload=payload,
        optimizer_manifest=canonical_json_bytes(manifest),
    )


def test_complete_manual_moments_roundtrip_and_independent_storage():
    source, optimizer = populated(1)
    record = serialize_reference_resume(source, optimizer)
    restored = target(source, record)
    other = restore_reference_optimizer(restored, record)
    result = compare_reference_optimizer_states(
        source, optimizer, restored, other, expected_step=1, exact=True
    )
    assert len(result.factors) == len(result.exp_avg) == len(result.exp_avg_sq) == 120
    assert serialize_reference_resume(restored, other) == record
    for left, right in zip(
        optimizer.param_groups[0]["params"],
        other.param_groups[0]["params"],
        strict=True,
    ):
        for key in ("step", "exp_avg", "exp_avg_sq"):
            assert (
                optimizer.state[left][key].data_ptr()
                != other.state[right][key].data_ptr()
            )


@pytest.mark.parametrize(
    "bad",
    [
        "missing",
        "foreign",
        "alias",
        "buffer_alias",
        "nonfinite",
        "negative",
        "step",
        "group",
        "gradient",
        "base_dtype",
    ],
)
def test_invalid_live_export_rejected_without_caller_mutation(bad):
    wrapper, optimizer = populated(1)
    parameter = wrapper.reference.factors["29"]["v"].B
    state = optimizer.state[parameter]
    if bad == "missing":
        del optimizer.state[parameter]
    elif bad == "foreign":
        optimizer.state[parameter]["foreign"] = torch.tensor(1.0)
    elif bad == "alias":
        state["exp_avg"] = parameter.detach()
    elif bad == "buffer_alias":
        wrapper.base.register_buffer("moment_alias", state["exp_avg"])
    elif bad == "nonfinite":
        state["exp_avg"].fill_(float("nan"))
    elif bad == "negative":
        state["exp_avg_sq"].fill_(-1)
    elif bad == "step":
        state["step"].fill_(2)
    elif bad == "group":
        optimizer.param_groups[0]["lr"] = 1e-3
    elif bad == "gradient":
        parameter.grad = torch.ones_like(parameter)
    else:
        wrapper.base.double()
    before = serialize_reference(wrapper.reference)
    with pytest.raises(ReferenceResumeError):
        serialize_reference_resume(wrapper, optimizer)
    assert serialize_reference(wrapper.reference) == before
    if bad == "gradient":
        assert torch.equal(parameter.grad, torch.ones_like(parameter))


@pytest.mark.parametrize(
    "hook",
    [
        "step_pre",
        "step_post",
        "state_dict_pre",
        "state_dict_post",
        "load_state_dict_pre",
        "load_state_dict_post",
        "global_pre",
        "global_post",
    ],
)
def test_registered_optimizer_hooks_rejected_without_execution(hook):
    wrapper, optimizer = populated(1)
    calls = []

    def callback(*args, **kwargs):
        calls.append(True)

    if hook.startswith("global_"):
        module = importlib.import_module("torch.optim.optimizer")
        register = getattr(module, f"register_optimizer_step_{hook[7:]}_hook")
    else:
        register = getattr(optimizer, f"register_{hook}_hook")
    handle = register(callback)
    try:
        with pytest.raises(ReferenceResumeError):
            serialize_reference_resume(wrapper, optimizer)
        assert calls == []
    finally:
        handle.remove()


@pytest.mark.parametrize(
    "bad",
    [
        "shape",
        "dtype",
        "bool_shape",
        "offset",
        "overlap",
        "gap",
        "missing",
        "extra",
        "duplicate",
        "deep",
        "prefix",
        "truncated",
        "trailing",
        "header_bound",
    ],
)
def test_bad_header_rejected_before_loader_and_constructor(bad, monkeypatch):
    from aluclu.alc_r0 import reference_qv_resume as module

    source, optimizer = populated(1)
    record = serialize_reference_resume(source, optimizer)
    wrapper = target(source, record)
    payload = record.optimizer_payload
    size = int.from_bytes(payload[:8], "little")
    header = json.loads(payload[8 : 8 + size])
    name = next(name for name in header if name.startswith("exp_avg/"))
    if bad == "shape":
        header[name]["shape"] = [2**60, 576]
    elif bad == "dtype":
        header[name]["dtype"] = "F64"
    elif bad == "bool_shape":
        header[name]["shape"] = [True, 576]
    elif bad == "offset":
        header[name]["data_offsets"] = [0, 2**60]
    elif bad in ("overlap", "gap"):
        delta = -4 if bad == "overlap" else 4
        header[name]["data_offsets"] = [v + delta for v in header[name]["data_offsets"]]
    elif bad == "missing":
        del header[name]
    elif bad == "extra":
        header["__metadata__"] = {"foreign": "value"}
    encoded = json.dumps(header, separators=(",", ":")).encode()
    if bad == "duplicate":
        encoded = encoded[:-1] + b"," + json.dumps(name).encode() + b":{}}"
    elif bad == "deep":
        encoded = b"[" * 2000 + b"0" + b"]" * 2000
    changed = len(encoded).to_bytes(8, "little") + encoded + payload[8 + size :]
    if bad == "prefix":
        changed = b"short"
    elif bad == "truncated":
        changed = changed[:-4]
    elif bad == "trailing":
        changed += b"tail"
    elif bad == "header_bound":
        changed = (131073).to_bytes(8, "little") + changed[8:]
    calls = []
    monkeypatch.setattr(module, "load_safetensors", lambda *args: calls.append("load"))
    monkeypatch.setattr(
        module, "make_reference_optimizer", lambda *args: calls.append("construct")
    )
    before = serialize_reference(wrapper.reference)
    with pytest.raises(ReferenceResumeError):
        restore_reference_optimizer(wrapper, with_payload(record, changed))
    assert calls == []
    assert serialize_reference(wrapper.reference) == before


@pytest.mark.parametrize(
    "bad", ["factor", "base", "gradient", "mode", "lease", "record_type", "field_type"]
)
def test_restore_ownership_preconditions_preserve_caller(bad):
    source, optimizer = populated(1)
    record = serialize_reference_resume(source, optimizer)
    wrapper = target(source, record)
    parameter = wrapper.reference.factors["29"]["v"].B
    if bad == "factor":
        with torch.no_grad():
            parameter.add_(0.5)
    elif bad == "base":
        with torch.no_grad():
            next(wrapper.base.parameters()).add_(0.5)
    elif bad == "gradient":
        parameter.grad = torch.ones_like(parameter)
    elif bad == "mode":
        wrapper.eval()
    elif bad == "record_type":
        record = object()
    elif bad == "field_type":
        record = replace(record, optimizer_payload=bytearray(record.optimizer_payload))
    before = serialize_reference(wrapper.reference)
    if bad == "lease":
        with wrapper.checkpoint_session():
            with pytest.raises(ReferenceResumeError):
                restore_reference_optimizer(wrapper, record)
            with pytest.raises(ReferenceResumeError):
                serialize_reference_resume(wrapper, optimizer)
    else:
        with pytest.raises(ReferenceResumeError):
            restore_reference_optimizer(wrapper, record)
    assert serialize_reference(wrapper.reference) == before


@pytest.mark.parametrize("mutation", ["factor", "base", "mount"])
def test_loader_time_binding_drift_prevents_publication(mutation, monkeypatch):
    from aluclu.alc_r0 import reference_qv_resume as module

    source, optimizer = populated(1)
    record = serialize_reference_resume(source, optimizer)
    wrapper = target(source, record)
    calls = []

    def drifting_loader(payload):
        result = load(payload)
        if mutation == "mount":
            wrapper.reference = deserialize_reference(
                record.factor_manifest, record.factor_payload
            )
        else:
            value = next(
                (
                    wrapper.reference if mutation == "factor" else wrapper.base
                ).parameters()
            )
            value.data.add_(0.5)
        return result

    monkeypatch.setattr(module, "load_safetensors", drifting_loader)
    monkeypatch.setattr(
        module, "make_reference_optimizer", lambda *args: calls.append(True)
    )
    with pytest.raises(ReferenceResumeError):
        restore_reference_optimizer(wrapper, record)
    assert calls == []  # External mutation detected, not falsely rolled back.


def test_source_state_drift_during_export_is_rejected(monkeypatch):
    from aluclu.alc_r0 import reference_qv_resume as module

    wrapper, optimizer = populated(1)
    parameter = wrapper.reference.factors["29"]["v"].B

    def drifting_writer(tensors):
        payload = save(tensors)
        optimizer.state[parameter]["exp_avg"].data.add_(0.5)
        return payload

    monkeypatch.setattr(module, "save_safetensors", drifting_writer)
    with pytest.raises(ReferenceResumeError):
        serialize_reference_resume(wrapper, optimizer)


def test_loader_error_is_typed_and_does_not_construct(monkeypatch):
    from aluclu.alc_r0 import reference_qv_resume as module

    source, optimizer = populated(1)
    record = serialize_reference_resume(source, optimizer)
    wrapper = target(source, record)
    before = serialize_reference(wrapper.reference)
    calls = []

    def bad_loader(payload):
        raise RuntimeError("injected loader failure")

    monkeypatch.setattr(module, "load_safetensors", bad_loader)
    monkeypatch.setattr(
        module, "make_reference_optimizer", lambda *args: calls.append(True)
    )
    with pytest.raises(ReferenceResumeError):
        restore_reference_optimizer(wrapper, record)
    assert calls == []
    assert serialize_reference(wrapper.reference) == before


@pytest.mark.parametrize("bad", ["step", "negative", "nonfinite"])
def test_invalid_loaded_values_rejected_before_optimizer_construction(bad, monkeypatch):
    from aluclu.alc_r0 import reference_qv_resume as module

    source, optimizer = populated(1)
    record = serialize_reference_resume(source, optimizer)
    wrapper = target(source, record)
    tensors = load(record.optimizer_payload)
    role, value = {
        "step": ("step/", 2),
        "negative": ("exp_avg_sq/", -1),
        "nonfinite": ("exp_avg/", float("nan")),
    }[bad]
    tensors[next(name for name in tensors if name.startswith(role))].fill_(value)
    calls = []
    monkeypatch.setattr(
        module, "make_reference_optimizer", lambda *args: calls.append("construct")
    )
    with pytest.raises(ReferenceResumeError):
        restore_reference_optimizer(wrapper, with_payload(record, save(tensors)))
    assert calls == []


@pytest.mark.parametrize(
    "bad",
    [
        "runtime",
        "authority",
        "group",
        "base_digest",
        "factor_digest",
        "payload_digest",
        "extra",
        "manifest_bound",
        "payload_bound",
    ],
)
def test_manifest_and_size_drift_rejected_before_loading(bad, monkeypatch):
    from aluclu.alc_r0 import reference_qv_resume as module

    source, optimizer = populated(1)
    record = serialize_reference_resume(source, optimizer)
    wrapper = target(source, record)
    document = parse_canonical_json(record.optimizer_manifest)
    if bad == "runtime":
        document["torch_version"] = "wrong"
    elif bad == "authority":
        document["training_authority"] = True
    elif bad == "group":
        document["optimizer_group"]["lr"] = 1e-3
    elif bad in ("base_digest", "factor_digest", "payload_digest"):
        key = {
            "base_digest": "base_sha256",
            "factor_digest": "factor_payload_sha256",
            "payload_digest": "optimizer_payload_sha256",
        }[bad]
        document[key] = "0" * 64
    else:
        document["foreign"] = "field"
    changed = replace(record, optimizer_manifest=canonical_json_bytes(document))
    if bad == "manifest_bound":
        changed = replace(record, optimizer_manifest=b"x" * 16385)
    elif bad == "payload_bound":
        changed = replace(record, optimizer_payload=b"x" * (4 * 1024 * 1024 + 1))
    calls = []
    monkeypatch.setattr(module, "load_safetensors", lambda *args: calls.append("load"))
    monkeypatch.setattr(
        module, "make_reference_optimizer", lambda *args: calls.append("construct")
    )
    with pytest.raises(ReferenceResumeError):
        restore_reference_optimizer(wrapper, changed)
    assert calls == []
