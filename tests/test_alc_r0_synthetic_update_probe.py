from __future__ import annotations

from types import SimpleNamespace

import pytest
import torch
from torch import nn

from aluclu.alc_r0.synthetic_update_probe import (
    SyntheticUpdateProbeError,
    optimizer_update_loop,
    validate_update_request,
)


class _TinyWrapper(nn.Module):
    def __init__(self, factors: nn.Module) -> None:
        super().__init__()
        self.base = nn.Parameter(torch.tensor([0.25]), requires_grad=False)
        self.factors = factors

    def forward(self, *, input_ids, use_cache, logits_to_keep):
        assert use_cache is False
        assert logits_to_keep == 1
        signal = input_ids.float().mean() * self.factors.weight
        return SimpleNamespace(logits=torch.stack((self.base, signal)).view(1, 1, 2))


class _TinyFactors(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.tensor([0.0], dtype=torch.float32))


def test_synthetic_update_loop_changes_only_factors_and_improves_target() -> None:
    factors = _TinyFactors()
    wrapper = _TinyWrapper(factors)
    base_before = wrapper.base.detach().clone()

    result = optimizer_update_loop(
        wrapper,
        factors,
        torch.tensor([[1, 1]], dtype=torch.long),
        target_token_id=1,
        updates=16,
    )

    assert result["optimizer_updates"] == 16
    assert len(result["losses"]) == 16
    assert result["post_target_log_probability"] > result["pre_target_log_probability"]
    assert all(torch.isfinite(torch.tensor(result["losses"])))
    assert torch.equal(wrapper.base, base_before)
    assert wrapper.base.grad is None


def test_nonfinite_loss_fails_closed_before_update() -> None:
    factors = _TinyFactors()
    with torch.no_grad():
        factors.weight.fill_(float("nan"))
    with pytest.raises(SyntheticUpdateProbeError, match="nonfinite"):
        optimizer_update_loop(
            _TinyWrapper(factors),
            factors,
            torch.tensor([[1, 1]], dtype=torch.long),
            target_token_id=1,
            updates=16,
        )


@pytest.mark.parametrize(
    ("arm", "updates"),
    [("capsule", 15), ("capsule", True), ("other", 16)],
)
def test_undeclared_cell_fails_closed(arm, updates) -> None:
    with pytest.raises(SyntheticUpdateProbeError):
        validate_update_request(arm, updates)
