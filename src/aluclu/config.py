from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EpisodicMemoryConfig:
    """Configuration for bounded episodic linear-attention memory."""

    d_model: int = 64
    segment_size: int = 16
    live_segments: int = 16
    archive_slots: int = 4
    archive_segments_per_slot: int = 4
    archive_rank: int = 8
    router_dim: int | None = None
    router_degree: int = 4
    sketch_dim: int = 128
    n_sketches: int = 3
    router_seed: int = 0
    routing: bool = True
    max_temperature: float = 4.0
    max_log_weight: float = 8.0
    conv_kernel: int = 3
    feature_floor: float = 1e-4
    feature_ceiling: float = 2.0
    eps: float = 1e-6

    def __post_init__(self) -> None:
        positive_ints = {
            "d_model": self.d_model,
            "segment_size": self.segment_size,
            "live_segments": self.live_segments,
            "archive_segments_per_slot": self.archive_segments_per_slot,
            "archive_rank": self.archive_rank,
            "router_degree": self.router_degree,
            "sketch_dim": self.sketch_dim,
            "n_sketches": self.n_sketches,
            "conv_kernel": self.conv_kernel,
        }
        for name, value in positive_ints.items():
            if value < 1:
                raise ValueError(f"{name} must be >= 1, got {value}")
        if self.archive_slots < 0:
            raise ValueError("archive_slots must be >= 0")
        if self.router_dimension < 1:
            raise ValueError("router_dim must be >= 1")
        if self.archive_rank > self.d_model:
            raise ValueError("archive_rank cannot exceed d_model")
        if self.n_sketches % 2 == 0:
            raise ValueError("n_sketches must be odd so the median is unambiguous")
        if self.max_temperature <= 0:
            raise ValueError("max_temperature must be positive")
        if self.max_log_weight <= 0:
            raise ValueError("max_log_weight must be positive")
        if not 0 < self.feature_floor < self.feature_ceiling:
            raise ValueError("feature bounds must satisfy 0 < floor < ceiling")
        if self.eps <= 0:
            raise ValueError("eps must be positive")

    @property
    def router_dimension(self) -> int:
        return self.d_model if self.router_dim is None else self.router_dim


@dataclass(frozen=True)
class GatedDeltaConfig:
    """Configuration for the recurrent Gated Delta Rule-2 reference core."""

    d_model: int = 64
    n_heads: int = 4
    head_key_dim: int = 16
    head_value_dim: int = 16
    conv_kernel: int = 3
    decay_min: float = 1e-4
    eps: float = 1e-6

    def __post_init__(self) -> None:
        for name in (
            "d_model",
            "n_heads",
            "head_key_dim",
            "head_value_dim",
            "conv_kernel",
        ):
            value = getattr(self, name)
            if value < 1:
                raise ValueError(f"{name} must be >= 1, got {value}")
        if not 0 < self.decay_min < 1:
            raise ValueError("decay_min must be in (0, 1)")
        if self.eps <= 0:
            raise ValueError("eps must be positive")


@dataclass(frozen=True)
class ExactCacheConfig:
    """Configuration for bounded exact residual-surprise memory."""

    d_model: int = 64
    n_heads: int = 4
    capacity: int = 64
    dropout: float = 0.0

    def __post_init__(self) -> None:
        for name in ("d_model", "n_heads", "capacity"):
            value = getattr(self, name)
            if value < 1:
                raise ValueError(f"{name} must be >= 1, got {value}")
        if self.d_model % self.n_heads:
            raise ValueError("d_model must be divisible by n_heads")
        if not 0 <= self.dropout < 1:
            raise ValueError("dropout must be in [0, 1)")


@dataclass(frozen=True)
class AlucluConfig:
    """Top-level ALUCLU block configuration.

    Every persistent branch is explicitly bounded by its configured window,
    matrix, cache capacity, or segment/archive budget.
    """

    d_model: int = 64
    n_layers: int = 4
    ffn_multiplier: int = 4
    dropout: float = 0.0
    local_window: int = 64
    local_heads: int = 4
    local_attention_every: int = 2
    episodic_every: int = 4
    exact_cache_every: int = 4
    gated_delta: GatedDeltaConfig | None = None
    episodic: EpisodicMemoryConfig | None = None
    exact_cache: ExactCacheConfig | None = None

    def __post_init__(self) -> None:
        for name in (
            "d_model",
            "n_layers",
            "ffn_multiplier",
            "local_window",
            "local_heads",
            "local_attention_every",
            "episodic_every",
            "exact_cache_every",
        ):
            value = getattr(self, name)
            if value < 1:
                raise ValueError(f"{name} must be >= 1, got {value}")
        if not 0 <= self.dropout < 1:
            raise ValueError("dropout must be in [0, 1)")
        if self.d_model % self.local_heads:
            raise ValueError("d_model must be divisible by local_heads")
        if (self.d_model // self.local_heads) % 2:
            raise ValueError("local attention head width must be even")
        if self.gated_delta is not None and self.gated_delta.d_model != self.d_model:
            raise ValueError("gated_delta.d_model must match d_model")
        if self.episodic is not None and self.episodic.d_model != self.d_model:
            raise ValueError("episodic.d_model must match d_model")
        if self.exact_cache is not None and self.exact_cache.d_model != self.d_model:
            raise ValueError("exact_cache.d_model must match d_model")
