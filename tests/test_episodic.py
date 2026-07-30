import torch

from aluclu import (
    BoundedEpisodicMemory,
    EpisodicMemoryConfig,
    MemorySlot,
)


def config(*, routing: bool = True) -> EpisodicMemoryConfig:
    return EpisodicMemoryConfig(
        d_model=8,
        segment_size=2,
        live_segments=1,
        archive_slots=2,
        archive_segments_per_slot=2,
        archive_rank=2,
        router_dim=4,
        router_degree=3,
        sketch_dim=8,
        n_sketches=3,
        routing=routing,
        conv_kernel=3,
    )


def test_zero_temperature_matches_ungated_fixed_aggregation() -> None:
    torch.manual_seed(10)
    routed = BoundedEpisodicMemory(config(routing=True)).eval()
    ungated = BoundedEpisodicMemory(config(routing=False)).eval()
    ungated.load_state_dict(routed.state_dict())
    x = torch.randn(2, 9, 8)
    routed_output = routed(x)
    ungated_output = ungated(x)
    torch.testing.assert_close(
        routed_output,
        ungated_output,
        rtol=0,
        atol=0,
    )


def test_router_conserves_denominator_mass() -> None:
    torch.manual_seed(11)
    layer = BoundedEpisodicMemory(config())
    layer.router.temperature_raw.data.fill_(0.4)
    scores = torch.randn(3, 5)
    mass = torch.rand(3, 5) + 0.1
    weights = layer.router.weights(scores, mass)
    torch.testing.assert_close(
        (weights * mass).sum(dim=1),
        mass.sum(dim=1),
        rtol=1e-6,
        atol=1e-6,
    )
    assert torch.all(weights > 0)


def test_compressed_denominator_uses_exact_z_not_svd_factor() -> None:
    torch.manual_seed(12)
    batch, rank, width = 2, 2, 8
    slot = MemorySlot(
        left=torch.randn(batch, rank, width),
        right=-torch.rand(batch, rank, width),
        z=torch.rand(batch, width) + 0.5,
        route_sum=torch.randn(batch, 4),
        sketch_sum=torch.randn(3, batch, 8),
        count=torch.full((batch,), 4.0),
        error_bound=torch.zeros(batch),
    )
    query = torch.rand(batch, width) + 0.5
    _, denominator = BoundedEpisodicMemory._read_slot(slot, query)
    expected = torch.einsum("bd,bd->b", slot.z, query)
    wrong_svd_denominator = torch.einsum(
        "brd,bd->br",
        slot.right,
        query,
    ).sum(dim=1)
    torch.testing.assert_close(denominator, expected)
    assert torch.all(denominator > 0)
    assert not torch.allclose(denominator, wrong_svd_denominator)


def test_chunked_and_single_scan_match_through_archive_evictions() -> None:
    torch.manual_seed(13)
    layer = BoundedEpisodicMemory(config()).eval()
    layer.router.temperature_raw.data.fill_(0.25)
    x = torch.randn(2, 25, 8)
    full_output, full_state = layer(x, return_state=True)

    state = None
    parts = []
    offset = 0
    for length in (1, 4, 3, 7, 10):
        output, state = layer(
            x[:, offset : offset + length],
            state,
            return_state=True,
        )
        parts.append(output)
        offset += length
    chunked_output = torch.cat(parts, dim=1)
    torch.testing.assert_close(chunked_output, full_output, rtol=1e-5, atol=1e-6)
    assert state is not None
    assert state.tokens_seen == full_state.tokens_seen
    assert len(state.live) == len(full_state.live)
    assert len(state.archive) == len(full_state.archive)


def test_state_and_compression_depth_stay_bounded() -> None:
    torch.manual_seed(14)
    layer = BoundedEpisodicMemory(config()).eval()
    state = None
    observed = []
    with torch.no_grad():
        for _ in range(40):
            _, state = layer.step(torch.randn(2, 8), state)
            if state.tokens_seen % layer.config.segment_size == 1:
                observed.append(state.tensor_numel())
    assert state is not None
    assert len(state.live) <= layer.config.live_segments
    assert len(state.archive) <= layer.config.archive_slots
    assert state.archive_cursor_segments <= layer.config.archive_segments_per_slot
    upper = 2 * layer.saturated_state_elements_per_batch()
    assert state.tensor_numel() <= upper
    assert len(set(observed[-4:])) == 1


def test_future_tokens_do_not_change_prefix() -> None:
    torch.manual_seed(15)
    layer = BoundedEpisodicMemory(config()).eval()
    first = torch.randn(1, 12, 8)
    second = first.clone()
    second[:, 7:] = torch.randn_like(second[:, 7:])
    first_output = layer(first)
    second_output = layer(second)
    torch.testing.assert_close(
        first_output[:, :7],
        second_output[:, :7],
        rtol=0,
        atol=0,
    )


def test_router_and_memory_gradients_are_finite() -> None:
    torch.manual_seed(16)
    layer = BoundedEpisodicMemory(config())
    layer.router.temperature_raw.data.fill_(0.15)
    x = torch.randn(2, 7, 8, requires_grad=True)
    loss = layer(x).square().mean()
    loss.backward()
    assert x.grad is not None and torch.isfinite(x.grad).all()
    gradients = [
        parameter.grad
        for parameter in layer.parameters()
        if parameter.requires_grad and parameter.grad is not None
    ]
    assert gradients
    assert all(torch.isfinite(gradient).all() for gradient in gradients)
