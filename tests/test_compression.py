import torch

from aluclu import (
    MemorySlot,
    compress_slot,
    factor_matrix,
    truncate_factors_with_error,
)


def make_slot(left: torch.Tensor, right: torch.Tensor) -> MemorySlot:
    batch, _, width = left.shape
    return MemorySlot(
        left=left,
        right=right,
        z=torch.rand(batch, width, dtype=left.dtype) + 0.1,
        route_sum=torch.randn(batch, 3, dtype=left.dtype),
        sketch_sum=torch.randn(3, batch, 5, dtype=left.dtype),
        count=torch.ones(batch, dtype=left.dtype),
        error_bound=torch.zeros(batch, dtype=left.dtype),
    )


def test_small_core_compression_is_exact_when_rank_is_sufficient() -> None:
    torch.manual_seed(1)
    left = torch.randn(2, 3, 8, dtype=torch.float64)
    right = torch.randn(2, 3, 8, dtype=torch.float64)
    compressed_left, compressed_right, discarded = truncate_factors_with_error(
        left,
        right,
        rank=3,
    )
    torch.testing.assert_close(
        factor_matrix(compressed_left, compressed_right),
        factor_matrix(left, right),
        rtol=1e-10,
        atol=1e-10,
    )
    torch.testing.assert_close(discarded, torch.zeros_like(discarded))


def test_reported_tail_matches_dense_best_rank_error() -> None:
    torch.manual_seed(2)
    left = torch.randn(2, 6, 8, dtype=torch.float64)
    right = torch.randn(2, 6, 8, dtype=torch.float64)
    compressed_left, compressed_right, discarded = truncate_factors_with_error(
        left,
        right,
        rank=2,
    )
    dense = factor_matrix(left, right)
    approximation = factor_matrix(compressed_left, compressed_right)
    actual = (dense - approximation).square().sum(dim=(-2, -1)).sqrt()
    torch.testing.assert_close(actual, discarded, rtol=1e-9, atol=1e-9)


def test_slot_error_ledger_accumulates_new_discarded_tail() -> None:
    torch.manual_seed(3)
    slot = make_slot(
        torch.randn(2, 5, 8, dtype=torch.float64),
        torch.randn(2, 5, 8, dtype=torch.float64),
    )
    slot = MemorySlot(
        left=slot.left,
        right=slot.right,
        z=slot.z,
        route_sum=slot.route_sum,
        sketch_sum=slot.sketch_sum,
        count=slot.count,
        error_bound=torch.full((2,), 0.25, dtype=torch.float64),
    )
    compressed = compress_slot(slot, rank=2)
    actual = (
        (
            factor_matrix(slot.left, slot.right)
            - factor_matrix(compressed.left, compressed.right)
        )
        .square()
        .sum(dim=(-2, -1))
        .sqrt()
    )
    torch.testing.assert_close(
        compressed.error_bound,
        actual + 0.25,
        rtol=1e-9,
        atol=1e-9,
    )
