"""Complete synthetic q/v AdamW comparisons; no optimizer execution evidence."""

import pytest
import torch
from test_alc_r0_reference_qv_wrapper import fake_wrapper

from aluclu.alc_r0.checkpoint_fidelity import CheckpointFidelityError
from aluclu.alc_r0.reference_qv_artifact import make_reference_optimizer
from aluclu.alc_r0.reference_qv_optimizer import compare_reference_optimizer_states


def populated(step):
    wrapper = fake_wrapper().train()
    optimizer = make_reference_optimizer(wrapper)
    for parameter in optimizer.param_groups[0]["params"]:
        optimizer.state[parameter] = {
            "step": torch.tensor(float(step), dtype=torch.float32),
            "exp_avg": torch.full_like(parameter, 0.125),
            "exp_avg_sq": torch.full_like(parameter, 0.25),
        }
    return wrapper, optimizer


@pytest.mark.parametrize("step", [1, 2])
def test_complete_qv_synthetic_moments_compare(step):
    left, left_optimizer = populated(step)
    right, right_optimizer = populated(step)
    result = compare_reference_optimizer_states(
        left, left_optimizer, right, right_optimizer, expected_step=step, exact=True
    )
    assert result.step == step
    assert len(result.factors) == len(result.exp_avg) == len(result.exp_avg_sq) == 120
    names = {name for name, _ in result.factors}
    assert "factors.29.v.B" in names
    assert "factors.29.q.A" in names


@pytest.mark.parametrize(
    "bad", ["missing", "alias", "moment", "factor", "step", "group", "shared_arm"]
)
def test_complete_qv_optimizer_drift_rejected(bad):
    left, left_optimizer = populated(1)
    right, right_optimizer = populated(1)
    parameter = right.reference.factors["29"]["v"].B
    state = right_optimizer.state[parameter]
    if bad == "missing":
        del right_optimizer.state[parameter]
    elif bad == "alias":
        state["exp_avg"] = parameter.detach()
    elif bad == "moment":
        state["exp_avg"].add_(0.5)
    elif bad == "factor":
        with torch.no_grad():
            parameter.add_(0.5)
    elif bad == "step":
        state["step"].fill_(2)
    elif bad == "group":
        right_optimizer.param_groups[0]["lr"] = 1e-3
    else:
        right, right_optimizer = left, left_optimizer
    with pytest.raises(CheckpointFidelityError):
        compare_reference_optimizer_states(
            left, left_optimizer, right, right_optimizer, expected_step=1, exact=True
        )
