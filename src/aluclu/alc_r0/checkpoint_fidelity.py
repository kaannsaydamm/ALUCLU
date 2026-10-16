"""Model-free fidelity checks for the prospective checkpoint implementation.

These checks confer no model execution, training or scientific authority.
"""

from __future__ import annotations

import math
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass

import torch


class CheckpointFidelityError(ValueError):
    """A tensor or fidelity comparison violates the fixed prospective contract."""


@dataclass(frozen=True)
class TensorComparison:
    reference_l2: float
    actual_l2: float
    difference_l2: float
    relative_l2: float | None
    cosine: float | None
    exact_zero: bool


def _validate_tensor(value: object) -> torch.Tensor:
    if not isinstance(value, torch.Tensor):
        raise CheckpointFidelityError("every compared value must be a tensor")
    if value.layout != torch.strided or value.device.type == "meta":
        raise CheckpointFidelityError("only materialized dense tensors are supported")
    if not value.is_floating_point() or value.is_complex() or value.numel() == 0:
        raise CheckpointFidelityError("tensors must be nonempty real floating values")
    return value


def _scaled_norm(vector: torch.Tensor) -> tuple[float, float, float]:
    scale = float(vector.abs().max().item())
    if scale == 0:
        return 0.0, 0.0, 0.0
    scaled_norm = float(torch.linalg.vector_norm(vector / scale).item())
    absolute = scale * scaled_norm
    if not math.isfinite(absolute) or absolute == 0:
        raise CheckpointFidelityError("absolute norm is not finitely representable")
    return scale, scaled_norm, absolute


def _relative_norm(
    difference_scale: float,
    difference_norm: float,
    reference_scale: float,
    reference_norm: float,
) -> float:
    if difference_scale == 0:
        return 0.0
    exponent = (
        math.log(difference_scale)
        - math.log(reference_scale)
        + math.log(difference_norm)
        - math.log(reference_norm)
    )
    try:
        result = math.exp(exponent)
    except OverflowError as exc:
        raise CheckpointFidelityError("relative norm is not representable") from exc
    if result == 0 or not math.isfinite(result):
        raise CheckpointFidelityError("nonzero relative norm is not representable")
    return result


def compare_tensor(
    reference: torch.Tensor, actual: torch.Tensor, *, exact: bool = False
) -> TensorComparison:
    """Validate one complete tensor without mutating it or recording autograd."""

    if type(exact) is not bool:
        raise CheckpointFidelityError("exact mode must be an actual boolean")
    ref = _validate_tensor(reference)
    act = _validate_tensor(actual)
    if ref.shape != act.shape or ref.dtype != act.dtype or ref.device != act.device:
        raise CheckpointFidelityError("shape, dtype and device must match")
    left = ref.detach().to(device="cpu", dtype=torch.float64).reshape(-1)
    right = act.detach().to(device="cpu", dtype=torch.float64).reshape(-1)
    if not torch.isfinite(left).all().item() or not torch.isfinite(right).all().item():
        raise CheckpointFidelityError("tensor contains a nonfinite value")
    if exact:
        left_bytes = ref.detach().cpu().contiguous().reshape(-1).view(torch.uint8)
        right_bytes = act.detach().cpu().contiguous().reshape(-1).view(torch.uint8)
        if not torch.equal(left_bytes, right_bytes):
            raise CheckpointFidelityError("original logical tensor bytes differ")

    reference_scale, reference_norm, reference_l2 = _scaled_norm(left)
    actual_scale, actual_norm, actual_l2 = _scaled_norm(right)
    difference = right - left
    if not torch.isfinite(difference).all().item():
        raise CheckpointFidelityError("difference is not finitely representable")
    difference_scale, difference_norm, difference_l2 = _scaled_norm(difference)
    if reference_scale == 0:
        if actual_scale != 0:
            raise CheckpointFidelityError("zero reference requires exactly zero actual")
        return TensorComparison(0.0, 0.0, 0.0, None, None, True)
    if actual_scale == 0:
        raise CheckpointFidelityError("nonzero reference cannot have zero actual")

    relative = _relative_norm(
        difference_scale, difference_norm, reference_scale, reference_norm
    )
    cosine = float(
        torch.dot(
            (left / reference_scale) / reference_norm,
            (right / actual_scale) / actual_norm,
        ).item()
    )
    if not math.isfinite(cosine):
        raise CheckpointFidelityError("cosine is not finitely representable")
    # Normalize harmless endpoint roundoff from the float64 dot product.
    cosine = min(1.0, max(-1.0, cosine))
    if (
        not torch.allclose(left, right, rtol=1e-3, atol=1e-3)
        or relative > 1e-5
        or cosine < 1 - 1e-6
    ):
        raise CheckpointFidelityError("fixed scale-sensitive fidelity checks failed")
    return TensorComparison(
        reference_l2, actual_l2, difference_l2, relative, cosine, False
    )


def _canonical_keys(values: Mapping[str, torch.Tensor]) -> tuple[str, ...]:
    for name in values:
        if (
            not isinstance(name, str)
            or not name
            or name != name.strip()
            or unicodedata.normalize("NFC", name) != name
            or any(ord(char) < 32 or ord(char) == 127 for char in name)
        ):
            raise CheckpointFidelityError(
                "tensor names must be canonical nonempty text"
            )
        try:
            name.encode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise CheckpointFidelityError("tensor name is not valid UTF-8") from exc
    return tuple(sorted(values, key=lambda name: name.encode("utf-8")))


def compare_named_tensors(
    reference: Mapping[str, torch.Tensor],
    actual: Mapping[str, torch.Tensor],
    *,
    exact: bool = False,
) -> tuple[tuple[str, TensorComparison], ...]:
    """Check every named value; never silently compare only intersecting keys."""

    if not isinstance(reference, Mapping) or not isinstance(actual, Mapping):
        raise CheckpointFidelityError("named comparisons require mappings")
    keys = _canonical_keys(reference)
    if not keys or keys != _canonical_keys(actual):
        raise CheckpointFidelityError("identical nonempty tensor name sets required")
    return tuple(
        (name, compare_tensor(reference[name], actual[name], exact=exact))
        for name in keys
    )
