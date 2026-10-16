"""Canonical ALCBASE v1 state encoding for the pinned ALC-R0 host."""

from __future__ import annotations

import hashlib
import struct
import sys
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass

import torch
from torch import Tensor

_DTYPE_IDS = {
    torch.bool: 1,
    torch.uint8: 2,
    torch.int8: 3,
    torch.int16: 4,
    torch.int32: 5,
    torch.int64: 6,
    torch.float16: 7,
    torch.bfloat16: 8,
    torch.float32: 9,
    torch.float64: 10,
    torch.complex64: 11,
    torch.complex128: 12,
}


class BaseStateEncodingError(ValueError):
    """Raised when a state cannot be represented by the frozen grammar."""


@dataclass(frozen=True)
class BaseStateEncoding:
    """Exact bytes and digests for one encoded state."""

    data: bytes
    sha256: str
    alias_record_sha256: str
    entry_count: int
    alias_group_count: int


def _u16(value: int) -> bytes:
    try:
        return struct.pack("<H", value)
    except struct.error as exc:
        raise BaseStateEncodingError(f"value is outside u16: {value}") from exc


def _u64(value: int) -> bytes:
    try:
        return struct.pack("<Q", value)
    except struct.error as exc:
        raise BaseStateEncodingError(f"value is outside u64: {value}") from exc


def _i64(value: int) -> bytes:
    try:
        return struct.pack("<q", value)
    except struct.error as exc:
        raise BaseStateEncodingError(f"value is outside i64: {value}") from exc


def _tensor_bytes(tensor: Tensor) -> bytes:
    contiguous = tensor.detach().to(device="cpu").contiguous()
    return contiguous.view(torch.uint8).numpy().tobytes(order="C")


def _storage_identity(tensor: Tensor) -> int:
    try:
        return int(tensor.untyped_storage()._cdata)
    except (AttributeError, RuntimeError) as exc:
        raise BaseStateEncodingError("tensor has no encodable untyped storage") from exc


def _storage_metadata(tensor: Tensor) -> tuple[int, int, tuple[int, ...]]:
    dimensions = tuple(int(value) for value in tensor.shape)
    strides = tuple(int(value) for value in tensor.stride())
    if any(dimension < 0 for dimension in dimensions):
        raise BaseStateEncodingError("negative tensor dimensions are forbidden")
    if any(stride < 0 for stride in strides):
        raise BaseStateEncodingError("negative tensor strides are unsupported")

    element_size = int(tensor.element_size())
    offset_bytes = int(tensor.storage_offset()) * element_size
    if tensor.numel() == 0:
        span_bytes = 0
    else:
        span_elements = 1 + sum(
            (dimension - 1) * stride
            for dimension, stride in zip(dimensions, strides, strict=True)
        )
        span_bytes = span_elements * element_size
    return offset_bytes, span_bytes, strides


def encode_base_state(state: Mapping[str, Tensor]) -> BaseStateEncoding:
    """Encode a state mapping as the single canonical ALCBASE v1 stream."""

    if sys.byteorder != "little":
        raise BaseStateEncodingError("ALCBASE v1 requires a little-endian host")

    entries: list[tuple[str, Tensor]] = []
    for name, tensor in state.items():
        if not isinstance(name, str):
            raise BaseStateEncodingError("state names must be strings")
        if not isinstance(tensor, Tensor):
            raise BaseStateEncodingError(f"state entry {name!r} is not a tensor")
        if tensor.layout is not torch.strided:
            raise BaseStateEncodingError(f"state entry {name!r} is not strided")
        if tensor.device.type == "meta":
            raise BaseStateEncodingError(f"state entry {name!r} is a meta tensor")
        if tensor.dtype not in _DTYPE_IDS:
            raise BaseStateEncodingError(f"state entry {name!r} has unsupported dtype")
        entries.append((name, tensor))
    entries.sort(key=lambda item: item[0])

    stream = bytearray(b"ALCBASE\0")
    stream.extend(_u16(1))
    stream.extend(_u64(len(entries)))

    storage_groups: dict[int, list[tuple[str, Tensor]]] = defaultdict(list)
    for name, tensor in entries:
        name_bytes = name.encode("utf-8", errors="strict")
        dimensions = tuple(int(value) for value in tensor.shape)
        raw = _tensor_bytes(tensor)
        stream.append(0x01)
        stream.extend(_u64(len(name_bytes)))
        stream.extend(name_bytes)
        stream.append(_DTYPE_IDS[tensor.dtype])
        stream.extend(_u64(len(dimensions)))
        for dimension in dimensions:
            stream.extend(_u64(dimension))
        stream.extend(_u64(len(raw)))
        stream.extend(raw)
        storage_groups[_storage_identity(tensor)].append((name, tensor))

    groups = sorted(
        (sorted(group, key=lambda item: item[0]) for group in storage_groups.values()),
        key=lambda group: group[0][0],
    )
    alias = bytearray([0x02])
    alias.extend(_u64(len(groups)))
    for group_index, group in enumerate(groups, start=1):
        alias.append(0x10)
        alias.extend(_u64(group_index))
        alias.extend(_u64(len(group)))
        for name, tensor in group:
            name_bytes = name.encode("utf-8", errors="strict")
            dimensions = tuple(int(value) for value in tensor.shape)
            offset_bytes, span_bytes, strides = _storage_metadata(tensor)
            alias.append(0x11)
            alias.extend(_u64(len(name_bytes)))
            alias.extend(name_bytes)
            alias.extend(_u64(offset_bytes))
            alias.extend(_u64(span_bytes))
            alias.extend(_u64(len(dimensions)))
            for dimension in dimensions:
                alias.extend(_u64(dimension))
            for stride in strides:
                alias.extend(_i64(stride))

    stream.extend(alias)
    stream.append(0xFF)
    encoded = bytes(stream)
    return BaseStateEncoding(
        data=encoded,
        sha256=hashlib.sha256(encoded).hexdigest(),
        alias_record_sha256=hashlib.sha256(alias).hexdigest(),
        entry_count=len(entries),
        alias_group_count=len(groups),
    )
