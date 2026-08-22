import math
from pathlib import Path
from typing import Any

import pytest

from aluclu.cognition import (
    InputBoundaryError,
    SafeStateCodec,
    StateIntegrityError,
    canonical_json_bytes,
    strict_json_loads,
)
from aluclu.cognition import codec as codec_module
from aluclu.cognition.codec import MAX_JSON_NODES, MAX_PAYLOAD_BYTES


def test_canonical_json_has_literal_stable_bytes() -> None:
    assert canonical_json_bytes({"z": 1, "a": [True, None, "ı"]}) == (
        b'{"a":[true,null,"\xc4\xb1"],"z":1}'
    )


@pytest.mark.parametrize("value", [(1, 2), {1: "x"}, {"x": math.nan}, {"x": math.inf}])
def test_canonical_json_rejects_non_json_or_non_finite_values(value: object) -> None:
    with pytest.raises(InputBoundaryError):
        canonical_json_bytes(value)


def test_strict_json_rejects_duplicate_object_keys() -> None:
    with pytest.raises(InputBoundaryError):
        strict_json_loads(b'{"x":1,"x":2}')


@pytest.mark.parametrize("constant", [b'{"x":NaN}', b'{"x":Infinity}', b'{"x":-Infinity}'])
def test_strict_json_rejects_stored_non_finite_constants(constant: bytes) -> None:
    with pytest.raises(InputBoundaryError):
        strict_json_loads(constant)


def test_canonical_json_accepts_depth_32_and_rejects_depth_33() -> None:
    assert canonical_json_bytes(_nested_json(32))
    with pytest.raises(InputBoundaryError):
        canonical_json_bytes(_nested_json(33))


def test_canonical_json_accepts_node_limit_and_rejects_one_extra_node() -> None:
    assert canonical_json_bytes([None] * (MAX_JSON_NODES - 1))
    with pytest.raises(InputBoundaryError):
        canonical_json_bytes([None] * MAX_JSON_NODES)


def test_canonical_json_accepts_payload_byte_limit_and_rejects_one_extra_byte() -> None:
    assert len(canonical_json_bytes("x" * (MAX_PAYLOAD_BYTES - 2))) == MAX_PAYLOAD_BYTES
    with pytest.raises(InputBoundaryError):
        canonical_json_bytes("x" * (MAX_PAYLOAD_BYTES - 1))


def test_canonical_json_rejects_cycles() -> None:
    value: list[Any] = []
    value.append(value)
    with pytest.raises(InputBoundaryError):
        canonical_json_bytes(value)


def test_canonical_json_rejects_exact_type_subclasses() -> None:
    class CustomString(str):
        pass

    with pytest.raises(InputBoundaryError):
        canonical_json_bytes(CustomString("x"))


@pytest.mark.parametrize("value", ["\ud800", {"\ud800": "x"}, {"x": "\ud800"}])
def test_canonical_json_rejects_lone_surrogates_in_keys_and_values(value: object) -> None:
    with pytest.raises(InputBoundaryError):
        canonical_json_bytes(value)


def test_safe_state_codec_round_trips_state_and_metadata(tmp_path) -> None:
    codec = SafeStateCodec(tmp_path, integrity_key=b"k" * 32)
    generation = codec.save("state", {"step": 1}, {"source": "test"})

    assert generation == 1
    assert codec.load("state") == ({"step": 1}, {"source": "test"})


def test_safe_state_codec_rejects_manifest_and_pointer_rewrite(tmp_path) -> None:
    codec = SafeStateCodec(tmp_path, integrity_key=b"k" * 32)
    codec.save("state", {"step": 1}, {"source": "test"})
    pointer = tmp_path / "state.json"
    pointer.write_bytes(pointer.read_bytes().replace(b'"generation":1', b'"generation":9'))
    with pytest.raises(StateIntegrityError):
        codec.load("state")


def test_safe_state_codec_rejects_cross_name_pointer_before_save(tmp_path) -> None:
    codec = SafeStateCodec(tmp_path, integrity_key=b"k" * 32)
    codec.save("state", {"step": 1}, {"source": "state"})
    codec.save("other", {"step": 1}, {"source": "other"})
    (tmp_path / "state.json").write_bytes((tmp_path / "other.json").read_bytes())

    with pytest.raises(StateIntegrityError):
        codec.save("state", {"step": 2}, {"source": "state"})


def test_safe_state_codec_durably_replaces_manifest_before_pointer(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def fake_durable_replace(path: Path, data: bytes) -> None:
        calls.append(path.name)
        path.write_bytes(data)

    monkeypatch.setattr(codec_module, "_durable_replace", fake_durable_replace, raising=False)

    SafeStateCodec(tmp_path, integrity_key=b"k" * 32).save("state", {"step": 1}, {})

    assert calls == ["state.00000000000000000001.manifest.json", "state.json"]


def test_safe_state_codec_does_not_advance_pointer_when_manifest_replace_fails(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    codec = SafeStateCodec(tmp_path, integrity_key=b"k" * 32)
    codec.save("state", {"step": 1}, {})

    def fail_second_manifest(path: Path, data: bytes) -> None:
        if path.name == "state.00000000000000000002.manifest.json":
            raise OSError("manifest durable replace failed")
        path.write_bytes(data)

    monkeypatch.setattr(codec_module, "_durable_replace", fail_second_manifest, raising=False)

    with pytest.raises(OSError, match="manifest durable replace failed"):
        codec.save("state", {"step": 2}, {})

    assert codec.load("state") == ({"step": 1}, {})


@pytest.mark.parametrize("name", ["../state", "a/b", "a\\b", "", "."])
def test_safe_state_codec_rejects_path_escape(tmp_path, name: str) -> None:
    codec = SafeStateCodec(tmp_path, integrity_key=b"k" * 32)
    with pytest.raises(InputBoundaryError):
        codec.save(name, {"step": 1}, {})


def _nested_json(depth: int) -> object:
    value: object = None
    for _ in range(depth - 1):
        value = [value]
    return value
