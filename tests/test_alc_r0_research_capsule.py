from __future__ import annotations

import math
from typing import cast

import pytest
import torch

from aluclu.alc_r0.research_capsule import ResearchCapsuleV0, _PortFactors


def _factors(capsule: ResearchCapsuleV0, port: int) -> _PortFactors:
    return cast(_PortFactors, capsule.factors[str(port)])


@pytest.mark.parametrize(
    "ports,rank,expected_parameters",
    [
        ((14,), 4, 4608),
        ((29,), 8, 9216),
        ((14, 29), 16, 36864),
    ],
)
def test_capsule_has_exact_preregistered_factor_shapes_and_count(
    ports: tuple[int, ...], rank: int, expected_parameters: int
) -> None:
    capsule = ResearchCapsuleV0(ports=ports, rank=rank, seed=20260921)

    assert capsule.ports == ports
    assert capsule.rank == rank
    assert sum(parameter.numel() for parameter in capsule.parameters()) == expected_parameters
    assert set(capsule.state_dict()) == {
        f"factors.{port}.{factor}" for port in ports for factor in ("A", "B")
    }
    for port in ports:
        assert _factors(capsule, port).A.shape == (rank, 576)
        assert _factors(capsule, port).B.shape == (576, rank)
        assert _factors(capsule, port).A.dtype == torch.float32
        assert _factors(capsule, port).B.dtype == torch.float32
        assert torch.count_nonzero(_factors(capsule, port).B) == 0


def test_capsule_initialization_is_seeded_and_forward_noop() -> None:
    first = ResearchCapsuleV0(ports=(14, 29), rank=8, seed=7)
    same = ResearchCapsuleV0(ports=(14, 29), rank=8, seed=7)
    different = ResearchCapsuleV0(ports=(14, 29), rank=8, seed=8)
    hidden = torch.tensor([[[1.0] * 576, [2.0] * 576]], dtype=torch.float32)

    assert all(
        torch.equal(first.state_dict()[name], same.state_dict()[name])
        for name in first.state_dict()
    )
    assert not torch.equal(_factors(first, 14).A, _factors(different, 14).A)
    assert torch.equal(first.apply_port(14, hidden), hidden)
    assert torch.equal(first.apply_port(29, hidden), hidden)


def test_capsule_initialization_does_not_mutate_global_torch_rng() -> None:
    before = torch.random.get_rng_state().clone()

    ResearchCapsuleV0(ports=(14, 29), rank=8, seed=7)

    assert torch.equal(torch.random.get_rng_state(), before)


def test_capsule_uses_fp32_normalized_residual_math_and_casts_delta_back() -> None:
    capsule = ResearchCapsuleV0(ports=(14,), rank=4, seed=1)
    with torch.no_grad():
        _factors(capsule, 14).A.fill_(0.125)
        _factors(capsule, 14).B.fill_(0.125)
    hidden = torch.arange(576, dtype=torch.float32).reshape(1, 1, 576).to(torch.bfloat16)

    actual = capsule.apply_port(14, hidden)
    fp32 = hidden.float()
    normalized = fp32 / torch.sqrt(fp32.square().mean(dim=-1, keepdim=True) + 1e-5)
    low_rank = torch.nn.functional.linear(normalized, _factors(capsule, 14).A)
    expected_delta = torch.nn.functional.linear(low_rank, _factors(capsule, 14).B)
    expected = hidden + expected_delta.to(dtype=hidden.dtype)

    assert actual.dtype == torch.bfloat16
    assert torch.equal(actual, expected)
    assert not torch.equal(actual, hidden)


def test_capsule_fp32_math_is_unchanged_by_host_bf16_autocast() -> None:
    capsule = ResearchCapsuleV0(ports=(14,), rank=4, seed=1)
    with torch.no_grad():
        _factors(capsule, 14).B.fill_(0.25)
    hidden = torch.linspace(-1, 1, steps=1152, dtype=torch.float32).reshape(1, 2, 576)

    expected = capsule.apply_port(14, hidden)
    with torch.autocast(device_type="cpu", dtype=torch.bfloat16):
        actual = capsule.apply_port(14, hidden)

    assert torch.equal(actual, expected)


@pytest.mark.skipif(
    not torch.cuda.is_available() or not torch.cuda.is_bf16_supported(),
    reason="CUDA BF16 device is unavailable",
)
def test_capsule_executes_bf16_host_path_on_cuda_with_fp32_factors() -> None:
    capsule = ResearchCapsuleV0(ports=(14,), rank=4, seed=1).to("cuda")
    with torch.no_grad():
        _factors(capsule, 14).B.fill_(0.125)
    hidden = torch.linspace(-1, 1, steps=576).reshape(1, 1, 576).to(
        device="cuda", dtype=torch.bfloat16
    )

    with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
        actual = capsule.apply_port(14, hidden)

    assert actual.dtype == torch.bfloat16
    assert actual.device.type == "cuda"
    assert _factors(capsule, 14).A.dtype == torch.float32
    assert _factors(capsule, 14).B.dtype == torch.float32
    assert torch.isfinite(actual).all()
    assert not torch.equal(actual, hidden)


def test_capsule_zero_control_has_positive_zero_for_both_factors() -> None:
    zero = ResearchCapsuleV0.zero_control(ports=(14, 29), rank=16)

    assert sum(parameter.numel() for parameter in zero.parameters()) == 36864
    for parameter in zero.parameters():
        assert torch.count_nonzero(parameter) == 0
        assert not torch.signbit(parameter).any()
        assert parameter.requires_grad is False


@pytest.mark.parametrize(
    "ports,rank,seed",
    [((14, 14), 4, 1), ((29, 14), 4, 1), ((13,), 4, 1), ((14,), 2, 1), ((14,), 4, -1)],
)
def test_capsule_rejects_unregistered_grid_or_seed(
    ports: tuple[int, ...], rank: int, seed: int
) -> None:
    with pytest.raises(ValueError):
        ResearchCapsuleV0(ports=ports, rank=rank, seed=seed)


def test_capsule_rejects_unknown_port_and_invalid_hidden_state() -> None:
    capsule = ResearchCapsuleV0(ports=(14,), rank=4, seed=1)
    with pytest.raises(ValueError):
        capsule.apply_port(29, torch.zeros(1, 576))
    with pytest.raises(ValueError):
        capsule.apply_port(14, torch.zeros(1, 575))
    with pytest.raises(ValueError):
        capsule.apply_port(14, torch.zeros(1, 576, dtype=torch.int64))


def test_capsule_gradients_remain_on_fp32_factors() -> None:
    capsule = ResearchCapsuleV0(ports=(14,), rank=4, seed=1)
    hidden = torch.full((1, 2, 576), math.sqrt(2), dtype=torch.float32)
    capsule.apply_port(14, hidden).sum().backward()

    a_grad = _factors(capsule, 14).A.grad
    b_grad = _factors(capsule, 14).B.grad
    assert a_grad is not None
    assert b_grad is not None
    assert a_grad.dtype == torch.float32
    assert b_grad.dtype == torch.float32
