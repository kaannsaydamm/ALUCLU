from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import Tensor

from .state import MemorySlot


def factor_matrix(left: Tensor, right: Tensor) -> Tensor:
    """Materialize ``left.T @ right`` for diagnostics and tests."""

    if left.shape != right.shape or left.ndim != 3:
        raise ValueError("left and right must share shape [batch, rank, width]")
    return torch.einsum("brd,bre->bde", left, right)


def truncate_factors_with_error(
    left: Tensor,
    right: Tensor,
    rank: int,
) -> tuple[Tensor, Tensor, Tensor]:
    """Compress ``left.T @ right`` without constructing a dense width² matrix.

    Thin QR decompositions reduce the problem to an SVD of a matrix whose sides
    are at most the number of incoming factors. Returned tensors are padded to
    exactly ``rank`` rows, which keeps archive-state shapes static.
    """

    if left.shape != right.shape or left.ndim != 3:
        raise ValueError("left and right must share shape [batch, factors, width]")
    if rank < 1:
        raise ValueError("rank must be positive")
    _, factors, width = left.shape
    if factors < 1:
        raise ValueError("at least one factor is required")
    if rank > width:
        raise ValueError("rank cannot exceed factor width")

    original_dtype = left.dtype
    work_dtype = (
        torch.float32
        if original_dtype in (torch.float16, torch.bfloat16)
        else original_dtype
    )
    left_work = left.to(work_dtype)
    right_work = right.to(work_dtype)

    q_left, r_left = torch.linalg.qr(
        left_work.transpose(-2, -1),
        mode="reduced",
    )
    q_right, r_right = torch.linalg.qr(
        right_work.transpose(-2, -1),
        mode="reduced",
    )
    core = r_left @ r_right.transpose(-2, -1)
    u, singular, vh = torch.linalg.svd(core, full_matrices=False)
    effective_rank = min(rank, singular.shape[-1])
    sqrt_singular = singular[:, :effective_rank].clamp_min(0).sqrt()
    discarded = singular[:, effective_rank:].square().sum(dim=-1).sqrt()

    left_columns = (q_left @ u[:, :, :effective_rank]) * sqrt_singular[:, None, :]
    v = vh.transpose(-2, -1)
    right_columns = (q_right @ v[:, :, :effective_rank]) * sqrt_singular[:, None, :]
    compressed_left = left_columns.transpose(-2, -1)
    compressed_right = right_columns.transpose(-2, -1)

    padding = rank - effective_rank
    if padding:
        compressed_left = F.pad(compressed_left, (0, 0, 0, padding))
        compressed_right = F.pad(compressed_right, (0, 0, 0, padding))
    return (
        compressed_left.to(original_dtype),
        compressed_right.to(original_dtype),
        discarded.to(original_dtype),
    )


def truncate_factors(left: Tensor, right: Tensor, rank: int) -> tuple[Tensor, Tensor]:
    compressed_left, compressed_right, _ = truncate_factors_with_error(
        left,
        right,
        rank,
    )
    return compressed_left, compressed_right


def compress_slot(slot: MemorySlot, rank: int) -> MemorySlot:
    left, right, discarded = truncate_factors_with_error(
        slot.left,
        slot.right,
        rank,
    )
    return MemorySlot(
        left=left,
        right=right,
        z=slot.z,
        route_sum=slot.route_sum,
        sketch_sum=slot.sketch_sum,
        count=slot.count,
        error_bound=slot.error_bound + discarded,
    )
