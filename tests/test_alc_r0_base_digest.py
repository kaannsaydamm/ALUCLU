from __future__ import annotations

import hashlib
import struct

import pytest
import torch

from aluclu.alc_r0.base_digest import BaseStateEncodingError, encode_base_state


def _u64(value: int) -> bytes:
    return struct.pack("<Q", value)


def test_single_int16_tensor_has_hand_calculated_stream() -> None:
    tensor = torch.tensor([1, 258], dtype=torch.int16)
    expected_alias = (
        b"\x02"
        + _u64(1)
        + b"\x10"
        + _u64(1)
        + _u64(1)
        + b"\x11"
        + _u64(1)
        + b"x"
        + _u64(0)
        + _u64(4)
        + _u64(1)
        + _u64(2)
        + struct.pack("<q", 1)
    )
    expected = (
        b"ALCBASE\0"
        + struct.pack("<H", 1)
        + _u64(1)
        + b"\x01"
        + _u64(1)
        + b"x"
        + b"\x04"
        + _u64(1)
        + _u64(2)
        + _u64(4)
        + b"\x01\x00\x02\x01"
        + expected_alias
        + b"\xff"
    )

    encoded = encode_base_state({"x": tensor})

    assert encoded.data == expected
    assert encoded.sha256 == hashlib.sha256(expected).hexdigest()
    assert encoded.alias_record_sha256 == hashlib.sha256(expected_alias).hexdigest()
    assert encoded.entry_count == 1
    assert encoded.alias_group_count == 1


def test_alias_groups_are_name_ordered_and_include_disjoint_views() -> None:
    storage = torch.arange(12, dtype=torch.float32)
    state = {
        "z": storage[8:12],
        "a": storage[0:4],
        "standalone": torch.ones(1, dtype=torch.float32),
    }

    first = encode_base_state(state)
    second = encode_base_state(dict(reversed(tuple(state.items()))))

    assert first.data == second.data
    assert first.alias_group_count == 2
    assert b"a" in first.data and b"z" in first.data


def test_noncontiguous_and_zero_size_spans_are_stable() -> None:
    base = torch.arange(12, dtype=torch.float32).reshape(3, 4)
    noncontiguous = base[:, ::2]
    zero = base[:0]

    encoded = encode_base_state({"noncontiguous": noncontiguous, "zero": zero})

    # The view reaches element offsets 0..10 inclusive: 11 * 4 bytes.
    assert _u64(44) in encoded.data
    assert _u64(0) in encoded.data


def test_bfloat16_is_encoded_without_numeric_casting() -> None:
    tensor = torch.tensor([1.0, -2.0], dtype=torch.bfloat16)
    raw = tensor.contiguous().view(torch.uint8).numpy().tobytes()

    encoded = encode_base_state({"bf16": tensor})

    assert raw in encoded.data


@pytest.mark.parametrize(
    "state",
    [
        {"bad": torch.tensor([1], dtype=torch.uint16)},
        {
            "bad": torch.sparse_coo_tensor(
                torch.tensor([[0]]),
                torch.tensor([1.0]),
                (1,),
                check_invariants=True,
            )
        },
        {"bad": "not-a-tensor"},
    ],
)
def test_unsupported_entries_fail_closed(state: dict[str, object]) -> None:
    with pytest.raises(BaseStateEncodingError):
        encode_base_state(state)  # type: ignore[arg-type]
