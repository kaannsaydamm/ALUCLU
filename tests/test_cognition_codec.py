import math

import pytest

from aluclu.cognition import (
    InputBoundaryError,
    SafeStateCodec,
    StateIntegrityError,
    canonical_json_bytes,
    strict_json_loads,
)


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


@pytest.mark.parametrize("name", ["../state", "a/b", "a\\b", "", "."])
def test_safe_state_codec_rejects_path_escape(tmp_path, name: str) -> None:
    codec = SafeStateCodec(tmp_path, integrity_key=b"k" * 32)
    with pytest.raises(InputBoundaryError):
        codec.save(name, {"step": 1}, {})
