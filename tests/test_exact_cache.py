import torch

from aluclu import (
    ExactCacheConfig,
    ExactCacheState,
    ResidualSurpriseCache,
)


def cache() -> ResidualSurpriseCache:
    return ResidualSurpriseCache(
        ExactCacheConfig(
            d_model=8,
            n_heads=2,
            capacity=3,
        )
    )


def test_cache_keeps_highest_residual_priorities() -> None:
    torch.manual_seed(40)
    layer = cache().eval()
    x = torch.randn(1, 6, 8)
    priority = torch.tensor([[0.2, 0.8, 0.1, 0.7, 0.3, 0.9]])
    _, state = layer(x, priority, return_state=True)
    expected = torch.tensor([0.7, 0.8, 0.9])
    torch.testing.assert_close(state.priority.sort(dim=1).values[0], expected)
    assert state.valid.all()


def test_replacement_is_batch_local_and_requires_strictly_higher_priority() -> None:
    torch.manual_seed(44)
    layer = ResidualSurpriseCache(
        ExactCacheConfig(d_model=8, n_heads=2, capacity=2)
    ).eval()
    x = torch.randn(2, 3, 8)
    priority = torch.tensor(
        [
            [0.2, 0.8, 0.2],
            [0.4, 0.3, 0.5],
        ]
    )
    projected_key = layer._reshape(layer.key_projection(x))

    _, state = layer(x, priority, return_state=True)

    torch.testing.assert_close(
        state.priority,
        torch.tensor([[0.2, 0.8], [0.4, 0.5]]),
    )
    torch.testing.assert_close(state.key[0, :, 0], projected_key[0, 0])
    torch.testing.assert_close(state.key[0, :, 1], projected_key[0, 1])
    torch.testing.assert_close(state.key[1, :, 0], projected_key[1, 0])
    torch.testing.assert_close(state.key[1, :, 1], projected_key[1, 2])
    assert state.tokens_seen == 3


def test_cache_step_matches_full_scan() -> None:
    torch.manual_seed(41)
    layer = cache().eval()
    x = torch.randn(2, 9, 8)
    priority = torch.rand(2, 9)
    full_output, full_state = layer(x, priority, return_state=True)

    state = None
    outputs = []
    for index in range(x.shape[1]):
        output, state = layer.step(x[:, index], priority[:, index], state)
        outputs.append(output)
    torch.testing.assert_close(
        torch.stack(outputs, dim=1),
        full_output,
        rtol=1e-5,
        atol=1e-6,
    )
    assert state is not None
    torch.testing.assert_close(state.key, full_state.key)
    torch.testing.assert_close(state.value, full_state.value)
    torch.testing.assert_close(state.priority, full_state.priority)
    assert torch.equal(state.valid, full_state.valid)


def test_cache_state_size_is_constant_after_initialization() -> None:
    torch.manual_seed(42)
    layer = cache().eval()
    state = layer.initial_state(
        2,
        device=torch.device("cpu"),
        dtype=torch.float32,
    )
    initial_elements = state.tensor_numel()
    for _ in range(20):
        _, state = layer.step(
            torch.randn(2, 8),
            torch.rand(2),
            state,
        )
        assert state.tensor_numel() == initial_elements
    assert initial_elements == 2 * layer.state_elements_per_batch()


def test_cache_is_causal_and_gradients_are_finite() -> None:
    torch.manual_seed(43)
    layer = cache()
    first = torch.randn(2, 7, 8, requires_grad=True)
    second = first.detach().clone()
    second[:, 4:] = torch.randn_like(second[:, 4:])
    priority = torch.rand(2, 7)

    first_output = layer(first, priority)
    second_output = layer(second, priority)
    torch.testing.assert_close(
        first_output[:, :4],
        second_output[:, :4],
        rtol=0,
        atol=0,
    )
    first_output.square().mean().backward()
    assert first.grad is not None and torch.isfinite(first.grad).all()
    assert all(
        parameter.grad is None or torch.isfinite(parameter.grad).all()
        for parameter in layer.parameters()
    )
    for projection in (
        layer.query_projection,
        layer.key_projection,
        layer.value_projection,
        layer.output_projection,
    ):
        assert projection.weight.grad is not None
        assert torch.isfinite(projection.weight.grad).all()
        assert projection.weight.grad.abs().sum() > 0


def test_float64_read_preserves_float64_softmax_precision() -> None:
    torch.manual_seed(45)
    layer = cache().double().eval()
    initial = layer.initial_state(
        1,
        device=torch.device("cpu"),
        dtype=torch.float64,
    )
    state = ExactCacheState(
        key=torch.randn_like(initial.key),
        value=torch.randn_like(initial.value),
        priority=torch.ones_like(initial.priority),
        valid=torch.ones_like(initial.valid),
        tokens_seen=3,
    )
    query = torch.randn(1, 2, 4, dtype=torch.float64)

    actual = layer._read(query, state)
    scores = torch.einsum(
        "bhd,bhcd->bhc",
        query,
        state.key,
    ) / (4**0.5)
    expected = torch.einsum(
        "bhc,bhcd->bhd",
        scores.softmax(dim=-1),
        state.value,
    )

    assert actual.dtype == torch.float64
    torch.testing.assert_close(actual, expected, rtol=1e-12, atol=1e-12)


def test_float64_priority_does_not_lose_replacement_ordering() -> None:
    torch.manual_seed(46)
    layer = (
        ResidualSurpriseCache(ExactCacheConfig(d_model=8, n_heads=2, capacity=1))
        .double()
        .eval()
    )
    x = torch.randn(1, 2, 8, dtype=torch.float64)
    priority = torch.tensor([[1.0, 1.0 + 1e-10]], dtype=torch.float64)
    projected_key = layer._reshape(layer.key_projection(x))

    _, state = layer(x, priority, return_state=True)

    assert state.priority.dtype == torch.float64
    torch.testing.assert_close(state.priority[:, 0], priority[:, 1])
    torch.testing.assert_close(state.key[:, :, 0], projected_key[:, 1])


def test_malformed_state_shape_is_rejected_instead_of_broadcast() -> None:
    layer = cache().eval()
    initial = layer.initial_state(
        2,
        device=torch.device("cpu"),
        dtype=torch.float32,
    )
    malformed = ExactCacheState(
        key=initial.key[:, :, :1],
        value=initial.value,
        priority=initial.priority,
        valid=initial.valid,
        tokens_seen=initial.tokens_seen,
    )

    try:
        layer(
            torch.randn(2, 1, 8),
            torch.rand(2, 1),
            malformed,
        )
    except ValueError as error:
        assert "state.key must have shape" in str(error)
    else:
        raise AssertionError("malformed cache state was silently accepted")


def test_cpu_autocast_preserves_device_and_finite_state() -> None:
    torch.manual_seed(47)
    layer = cache().eval()
    x = torch.randn(2, 4, 8)
    priority = torch.rand(2, 4)

    with torch.autocast("cpu", dtype=torch.bfloat16):
        output, state = layer(x, priority, return_state=True)
        step_output, next_state = layer.step(
            torch.randn(2, 8),
            torch.rand(2),
            state,
        )

    assert output.dtype == torch.bfloat16
    assert step_output.dtype == torch.bfloat16
    assert state.key.device == x.device
    assert state.value.device == x.device
    assert state.priority.device == x.device
    assert state.valid.device == x.device
    assert state.key.dtype == x.dtype
    assert state.value.dtype == x.dtype
    assert state.priority.dtype == torch.float32
    assert state.valid.dtype == torch.bool
    assert torch.isfinite(output).all()
    assert torch.isfinite(step_output).all()
    assert torch.isfinite(next_state.key).all()
