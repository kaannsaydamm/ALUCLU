from __future__ import annotations

from dataclasses import dataclass

from torch import Tensor


@dataclass(frozen=True)
class MemorySlot:
    """A factorized associative-memory slot.

    ``left.T @ right`` is the value-key numerator matrix. ``z`` is stored
    independently and is the only valid source for the positive denominator.
    """

    left: Tensor
    right: Tensor
    z: Tensor
    route_sum: Tensor
    sketch_sum: Tensor
    count: Tensor
    error_bound: Tensor

    def detach(self) -> MemorySlot:
        return MemorySlot(*(tensor.detach() for tensor in self.tensors()))

    def tensors(self) -> tuple[Tensor, ...]:
        return (
            self.left,
            self.right,
            self.z,
            self.route_sum,
            self.sketch_sum,
            self.count,
            self.error_bound,
        )


@dataclass(frozen=True)
class EpisodicState:
    conv_history: Tensor
    current: MemorySlot | None
    live: tuple[MemorySlot, ...]
    archive: tuple[MemorySlot, ...]
    archive_cursor: int
    archive_cursor_segments: int
    tokens_seen: int

    def detach(self) -> EpisodicState:
        return EpisodicState(
            conv_history=self.conv_history.detach(),
            current=None if self.current is None else self.current.detach(),
            live=tuple(slot.detach() for slot in self.live),
            archive=tuple(slot.detach() for slot in self.archive),
            archive_cursor=self.archive_cursor,
            archive_cursor_segments=self.archive_cursor_segments,
            tokens_seen=self.tokens_seen,
        )

    def tensor_numel(self) -> int:
        total = self.conv_history.numel()
        slots = self.live + self.archive
        if self.current is not None:
            slots = slots + (self.current,)
        for slot in slots:
            total += sum(tensor.numel() for tensor in slot.tensors())
        return total


@dataclass(frozen=True)
class GatedDeltaState:
    conv_history: Tensor
    fast_weight: Tensor
    tokens_seen: int

    def detach(self) -> GatedDeltaState:
        return GatedDeltaState(
            conv_history=self.conv_history.detach(),
            fast_weight=self.fast_weight.detach(),
            tokens_seen=self.tokens_seen,
        )

    def tensor_numel(self) -> int:
        return self.conv_history.numel() + self.fast_weight.numel()


@dataclass(frozen=True)
class LocalAttentionState:
    key: Tensor
    value: Tensor
    tokens_seen: int

    def detach(self) -> LocalAttentionState:
        return LocalAttentionState(
            key=self.key.detach(),
            value=self.value.detach(),
            tokens_seen=self.tokens_seen,
        )

    def tensor_numel(self) -> int:
        return self.key.numel() + self.value.numel()


@dataclass(frozen=True)
class ExactCacheState:
    key: Tensor
    value: Tensor
    priority: Tensor
    valid: Tensor
    tokens_seen: int

    def detach(self) -> ExactCacheState:
        return ExactCacheState(
            key=self.key.detach(),
            value=self.value.detach(),
            priority=self.priority.detach(),
            valid=self.valid.detach(),
            tokens_seen=self.tokens_seen,
        )

    def tensor_numel(self) -> int:
        return (
            self.key.numel()
            + self.value.numel()
            + self.priority.numel()
            + self.valid.numel()
        )


@dataclass(frozen=True)
class AlucluBlockState:
    gated_delta: GatedDeltaState
    local_attention: LocalAttentionState | None
    episodic: EpisodicState | None
    exact_cache: ExactCacheState | None

    def detach(self) -> AlucluBlockState:
        return AlucluBlockState(
            gated_delta=self.gated_delta.detach(),
            local_attention=(
                None if self.local_attention is None else self.local_attention.detach()
            ),
            episodic=None if self.episodic is None else self.episodic.detach(),
            exact_cache=(
                None if self.exact_cache is None else self.exact_cache.detach()
            ),
        )

    def tensor_numel(self) -> int:
        total = self.gated_delta.tensor_numel()
        if self.local_attention is not None:
            total += self.local_attention.tensor_numel()
        if self.episodic is not None:
            total += self.episodic.tensor_numel()
        if self.exact_cache is not None:
            total += self.exact_cache.tensor_numel()
        return total


@dataclass(frozen=True)
class AlucluModelState:
    blocks: tuple[AlucluBlockState, ...]
    tokens_seen: int

    def detach(self) -> AlucluModelState:
        return AlucluModelState(
            blocks=tuple(block.detach() for block in self.blocks),
            tokens_seen=self.tokens_seen,
        )

    def tensor_numel(self) -> int:
        return sum(block.tensor_numel() for block in self.blocks)
