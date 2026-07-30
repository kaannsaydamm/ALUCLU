from __future__ import annotations

from .config import (
    AlucluConfig,
    EpisodicMemoryConfig,
    ExactCacheConfig,
    GatedDeltaConfig,
)


def build_research_config(
    *,
    d_model: int,
    n_layers: int,
    local_window: int,
    segment_size: int,
    live_segments: int,
    archive_slots: int,
    archive_segments_per_slot: int,
    archive_rank: int,
    exact_cache_capacity: int,
    sketch_dim: int = 128,
) -> AlucluConfig:
    """Build the measured four-lane research preset used by shipped CLIs."""

    if d_model % 8:
        raise ValueError("d_model must be divisible by 8")
    if n_layers < 1:
        raise ValueError("n_layers must be positive")
    scheduled_interval = min(4, n_layers)
    return AlucluConfig(
        d_model=d_model,
        n_layers=n_layers,
        ffn_multiplier=4,
        local_window=local_window,
        local_heads=4,
        local_attention_every=min(2, n_layers),
        episodic_every=scheduled_interval,
        exact_cache_every=scheduled_interval,
        gated_delta=GatedDeltaConfig(
            d_model=d_model,
            n_heads=4,
            head_key_dim=d_model // 4,
            head_value_dim=d_model // 4,
        ),
        episodic=EpisodicMemoryConfig(
            d_model=d_model,
            segment_size=segment_size,
            live_segments=live_segments,
            archive_slots=archive_slots,
            archive_segments_per_slot=archive_segments_per_slot,
            archive_rank=min(archive_rank, d_model),
            router_dim=min(32, d_model),
            router_degree=3,
            sketch_dim=sketch_dim,
            n_sketches=3,
        ),
        exact_cache=ExactCacheConfig(
            d_model=d_model,
            n_heads=4,
            capacity=exact_cache_capacity,
        ),
    )
