from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any

from torch import Tensor, nn


def tensor_tree_bytes(value: Any) -> int:
    """Count unique tensor storage bytes in a nested state object."""

    seen: set[int] = set()

    def visit(item: Any) -> int:
        if isinstance(item, Tensor):
            storage_id = item.untyped_storage().data_ptr()
            if storage_id in seen:
                return 0
            seen.add(storage_id)
            return item.numel() * item.element_size()
        if is_dataclass(item):
            return sum(visit(getattr(item, field.name)) for field in fields(item))
        if isinstance(item, dict):
            return sum(visit(key) + visit(value) for key, value in item.items())
        if isinstance(item, (tuple, list)):
            return sum(visit(child) for child in item)
        return 0

    return visit(value)


def parameter_count(module: nn.Module, *, trainable_only: bool = False) -> int:
    return sum(
        parameter.numel()
        for parameter in module.parameters()
        if not trainable_only or parameter.requires_grad
    )
