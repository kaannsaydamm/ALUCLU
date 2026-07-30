import torch

from aluclu import (
    BoundedLocalAttention,
    GatedDeltaConfig,
    GatedDeltaRule2,
)


def delta_config() -> GatedDeltaConfig:
    return GatedDeltaConfig(
        d_model=8,
        n_heads=2,
        head_key_dim=4,
        head_value_dim=4,
        conv_kernel=3,
    )


def test_gated_delta_scan_matches_token_steps() -> None:
    torch.manual_seed(20)
    layer = GatedDeltaRule2(delta_config()).eval()
    x = torch.randn(2, 11, 8)
    full, full_state = layer(x, return_state=True)
    state = None
    outputs = []
    for index in range(x.shape[1]):
        output, state = layer.step(x[:, index], state)
        outputs.append(output)
    stepped = torch.stack(outputs, dim=1)
    torch.testing.assert_close(stepped, full, rtol=1e-5, atol=1e-6)
    assert state is not None
    torch.testing.assert_close(state.fast_weight, full_state.fast_weight)


def test_gated_delta_state_size_is_context_independent() -> None:
    torch.manual_seed(21)
    layer = GatedDeltaRule2(delta_config()).eval()
    short_state = layer(torch.randn(1, 4, 8), return_state=True)[1]
    long_state = layer(torch.randn(1, 40, 8), return_state=True)[1]
    assert short_state.tensor_numel() == long_state.tensor_numel()


def test_gated_delta_gradients_are_finite() -> None:
    torch.manual_seed(22)
    layer = GatedDeltaRule2(delta_config())
    x = torch.randn(2, 8, 8, requires_grad=True)
    layer(x).square().mean().backward()
    assert x.grad is not None and torch.isfinite(x.grad).all()
    assert all(
        parameter.grad is None or torch.isfinite(parameter.grad).all()
        for parameter in layer.parameters()
    )


def test_zero_write_surprise_has_finite_gradients() -> None:
    torch.manual_seed(25)
    layer = GatedDeltaRule2(delta_config())
    with torch.no_grad():
        layer.value_projection.weight.zero_()
    x = torch.randn(2, 5, 8, requires_grad=True)

    _, surprise = layer(x, return_write_surprise=True)
    torch.testing.assert_close(surprise, torch.zeros_like(surprise))
    surprise.sum().backward()

    assert x.grad is not None and torch.isfinite(x.grad).all()
    assert all(
        parameter.grad is None or torch.isfinite(parameter.grad).all()
        for parameter in layer.parameters()
    )


def test_local_attention_scan_matches_token_steps_and_caps_cache() -> None:
    torch.manual_seed(23)
    layer = BoundedLocalAttention(
        d_model=8,
        n_heads=2,
        window_size=5,
    ).eval()
    x = torch.randn(2, 13, 8)
    full, full_state = layer(x, return_state=True)
    state = None
    outputs = []
    for index in range(x.shape[1]):
        output, state = layer.step(x[:, index], state)
        outputs.append(output)
    stepped = torch.stack(outputs, dim=1)
    torch.testing.assert_close(stepped, full, rtol=1e-6, atol=1e-6)
    assert state is not None
    assert state.key.shape[2] == 5
    assert state.tensor_numel() == full_state.tensor_numel()


def test_local_attention_is_causal() -> None:
    torch.manual_seed(24)
    layer = BoundedLocalAttention(8, 2, 5).eval()
    first = torch.randn(1, 9, 8)
    second = first.clone()
    second[:, 6:] = torch.randn_like(second[:, 6:])
    torch.testing.assert_close(
        layer(first)[:, :6],
        layer(second)[:, :6],
        rtol=0,
        atol=0,
    )
