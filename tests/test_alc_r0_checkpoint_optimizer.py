from __future__ import annotations

import pytest
import torch

from aluclu.alc_r0.checkpoint_fidelity import CheckpointFidelityError
from aluclu.alc_r0.checkpoint_optimizer import compare_adamw_states


def fixture():
    # Construct and populate synthetic state only: never optimizer.step/model.
    factors = {
        "port.29.B": torch.nn.Parameter(torch.tensor([1.0, -2.0])),
        "port.14.A": torch.nn.Parameter(torch.tensor([[3.0, 4.0]])),
    }
    base = [torch.nn.Parameter(torch.ones(3), requires_grad=False)]
    optimizer = torch.optim.AdamW(
        list(factors.values()), lr=3e-4, weight_decay=0, foreach=False, fused=False
    )
    for parameter in factors.values():
        optimizer.state[parameter] = {
            "step": torch.tensor(1.0),
            "exp_avg": torch.full_like(parameter, 1e-6),
            "exp_avg_sq": torch.full_like(parameter, 1e-12),
        }
    return optimizer, factors, base


def compare(left, right, **kwargs):
    return compare_adamw_states(
        left[0],
        right[0],
        left[1],
        right[1],
        reference_base_parameters=left[2],
        actual_base_parameters=right[2],
        expected_step=kwargs.pop("expected_step", 1),
        **kwargs,
    )


def test_complete_identity_and_canonical_order_without_mutation():
    left, right = fixture(), fixture()
    versions = [p._version for p in left[1].values()]
    result = compare(left, right, exact=True)
    assert [name for name, _ in result.factors] == ["port.14.A", "port.29.B"]
    assert [name for name, _ in result.exp_avg] == ["port.14.A", "port.29.B"]
    assert len(result.exp_avg_sq) == 2 and result.step == 1
    assert versions == [p._version for p in left[1].values()]
    assert all(p.grad is None for p in left[1].values())
    assert all(not p.requires_grad for p in left[2])


def test_step_two_and_reordered_optimizer_parameters():
    left, right = fixture(), fixture()
    right[0].param_groups[0]["params"].reverse()
    for side in (left, right):
        for state in side[0].state.values():
            state["step"].fill_(2)
    assert compare(left, right, expected_step=2).step == 2


@pytest.mark.parametrize("field", ["factor", "exp_avg", "exp_avg_sq"])
def test_each_value_compared_with_scale_sensitive_criteria(field):
    left, right = fixture(), fixture()
    parameter = right[1]["port.29.B"]
    with torch.no_grad():
        if field == "factor":
            parameter.mul_(1.01)
        else:
            value = right[0].state[parameter][field]
            before = value.clone()
            value.mul_(1.01)
            assert torch.allclose(before, value, atol=1e-3, rtol=1e-3)
    with pytest.raises(CheckpointFidelityError):
        compare(left, right)


@pytest.mark.parametrize("side", [0, 1])
@pytest.mark.parametrize(
    "mutation",
    [
        "missing_state",
        "extra_state",
        "missing_parameter",
        "duplicate_parameter",
        "base_parameter",
        "missing_binding",
        "duplicate_binding",
        "bad_name",
        "empty_base",
        "trainable_base",
        "duplicate_base",
        "factor_is_base",
        "wrong_dtype",
        "frozen_factor",
        "non_parameter",
        "two_groups",
        "extra_group_key",
        "missing_group_key",
        "wrong_optimizer",
    ],
)
def test_membership_and_binding_fail_closed(side, mutation):
    arms = [fixture(), fixture()]
    optimizer, factors, base = arms[side]
    parameter = factors["port.29.B"]
    group = optimizer.param_groups[0]
    if mutation == "missing_state":
        del optimizer.state[parameter]
    elif mutation == "extra_state":
        optimizer.state[base[0]] = {}
    elif mutation == "missing_parameter":
        group["params"].pop()
    elif mutation == "duplicate_parameter":
        group["params"].append(parameter)
    elif mutation == "base_parameter":
        group["params"].append(base[0])
    elif mutation == "missing_binding":
        factors.pop("port.29.B")
    elif mutation == "duplicate_binding":
        factors["alias"] = parameter
    elif mutation == "bad_name":
        factors[" bad "] = factors.pop("port.29.B")
    elif mutation == "empty_base":
        base.clear()
    elif mutation == "trainable_base":
        base[0].requires_grad_(True)
    elif mutation == "duplicate_base":
        base.append(base[0])
    elif mutation == "factor_is_base":
        base.append(parameter)
    elif mutation == "wrong_dtype":
        parameter.data = parameter.data.double()
    elif mutation == "frozen_factor":
        parameter.requires_grad_(False)
    elif mutation == "non_parameter":
        factors["port.29.B"] = parameter.detach()
    elif mutation == "two_groups":
        optimizer.param_groups.append(dict(group))
    elif mutation == "extra_group_key":
        group["unreviewed"] = False
    elif mutation == "missing_group_key":
        del group["fused"]
    elif mutation == "wrong_optimizer":
        arms[side] = (torch.optim.SGD(list(factors.values()), lr=3e-4), factors, base)
    with pytest.raises(CheckpointFidelityError):
        compare(*arms)


@pytest.mark.parametrize(
    "key,value",
    [
        ("lr", 1e-3),
        ("lr", True),
        ("lr", torch.tensor(3e-4)),
        ("betas", (0.8, 0.999)),
        ("betas", [0.9, 0.999]),
        ("eps", 1e-6),
        ("weight_decay", 0.01),
        ("weight_decay", False),
        ("amsgrad", True),
        ("maximize", True),
        ("foreach", None),
        ("capturable", True),
        ("differentiable", True),
        ("fused", None),
        ("decoupled_weight_decay", False),
        ("maximize", 0),
    ],
)
def test_fixed_hyperparameters_even_when_both_arms_drift(key, value):
    left, right = fixture(), fixture()
    for arm in (left, right):
        arm[0].param_groups[0][key] = value
    with pytest.raises(CheckpointFidelityError):
        compare(left, right)


@pytest.mark.parametrize(
    "mutation",
    [
        "empty",
        "missing_moment",
        "extra_key",
        "step_zero",
        "step_two",
        "step_bool",
        "step_int",
        "step_vector",
        "step_nan",
        "step_grad",
        "moment_shape",
        "moment_dtype",
        "moment_none",
        "moment_nan",
        "moment_sparse",
        "moment_grad",
        "negative_square",
        "moment_meta",
    ],
)
@pytest.mark.parametrize("side", [0, 1])
def test_state_validation(side, mutation):
    arms = [fixture(), fixture()]
    optimizer, factors, _ = arms[side]
    parameter = factors["port.29.B"]
    state = optimizer.state[parameter]
    if mutation == "empty":
        state.clear()
    elif mutation == "missing_moment":
        del state["exp_avg"]
    elif mutation == "extra_key":
        state["max_exp_avg_sq"] = torch.ones_like(parameter)
    elif mutation.startswith("step_"):
        state["step"] = {
            "step_zero": torch.tensor(0.0),
            "step_two": torch.tensor(2.0),
            "step_bool": True,
            "step_int": torch.tensor(1),
            "step_vector": torch.tensor([1.0]),
            "step_nan": torch.tensor(float("nan")),
            "step_grad": torch.tensor(1.0, requires_grad=True),
        }[mutation]
    elif mutation == "moment_shape":
        state["exp_avg"] = torch.ones(3)
    elif mutation == "moment_dtype":
        state["exp_avg"] = torch.ones(2, dtype=torch.float64)
    elif mutation == "moment_none":
        state["exp_avg"] = None
    elif mutation == "moment_nan":
        state["exp_avg"][0] = float("nan")
    elif mutation == "moment_sparse":
        state["exp_avg"] = state["exp_avg"].to_sparse()
    elif mutation == "moment_grad":
        state["exp_avg"].requires_grad_(True)
    elif mutation == "negative_square":
        state["exp_avg_sq"][0] = -1e-12
    elif mutation == "moment_meta":
        state["exp_avg"] = torch.empty(2, device="meta")
    with pytest.raises(CheckpointFidelityError):
        compare(*arms)


@pytest.mark.parametrize("step", [True, 0, 3, 1.0, None])
def test_required_step_contract(step):
    with pytest.raises(CheckpointFidelityError):
        compare(fixture(), fixture(), expected_step=step)


def test_shared_factor_arms_are_not_independent_evidence():
    arm = fixture()
    with pytest.raises(CheckpointFidelityError):
        compare(arm, arm)


def test_mismatched_complete_names_fail():
    left, right = fixture(), fixture()
    right[1]["port.29.C"] = right[1].pop("port.29.B")
    with pytest.raises(CheckpointFidelityError):
        compare(left, right)


def test_exact_mode_checks_moment_original_bytes():
    left, right = fixture(), fixture()
    for arm in (left, right):
        arm[0].state[arm[1]["port.29.B"]]["exp_avg"].zero_()
    right[0].state[right[1]["port.29.B"]]["exp_avg"][0] = -0.0
    compare(left, right)
    with pytest.raises(CheckpointFidelityError):
        compare(left, right, exact=True)


@pytest.mark.parametrize(
    "mutation",
    [
        "factor_alias",
        "base_alias",
        "moment_factor",
        "moment_moment",
        "shared_step",
        "cross_arm_moment",
        "cross_arm_factor",
    ],
)
def test_distinct_objects_cannot_hide_shared_storage(mutation):
    left, right = fixture(), fixture()
    optimizer, factors, base = right
    parameter = factors["port.29.B"]
    state = optimizer.state[parameter]
    if mutation == "factor_alias":
        factors["port.14.A"].data = parameter.data
    elif mutation == "base_alias":
        base[0].data = parameter.data
    elif mutation == "moment_factor":
        state["exp_avg"] = parameter.detach()
    elif mutation == "moment_moment":
        state["exp_avg_sq"] = state["exp_avg"]
    elif mutation == "shared_step":
        optimizer.state[factors["port.14.A"]]["step"] = state["step"]
    elif mutation == "cross_arm_moment":
        state["exp_avg"] = left[0].state[left[1]["port.29.B"]]["exp_avg"]
    elif mutation == "cross_arm_factor":
        parameter.data = left[1]["port.29.B"].data
    with pytest.raises(CheckpointFidelityError):
        compare(left, right)


def test_frozen_base_may_be_shared_without_sharing_comparison_state():
    left, right = fixture(), fixture()
    compare(left, (right[0], right[1], left[2]), exact=True)


@pytest.mark.parametrize("side", [0, 1])
@pytest.mark.parametrize("field", ["factor", "exp_avg", "exp_avg_sq", "step"])
def test_cross_arm_base_storage_must_remain_frozen(side, field):
    arms = [fixture(), fixture()]
    optimizer, factors, _ = arms[side]
    parameter = factors["port.29.B"]
    value = parameter if field == "factor" else optimizer.state[parameter][field]
    arms[1 - side][2][0].data = value.detach()
    with pytest.raises(CheckpointFidelityError):
        compare(*arms, exact=True)


@pytest.mark.parametrize("field", ["exp_avg", "exp_avg_sq"])
def test_explicit_zero_moments_not_missing_state(field):
    left, right = fixture(), fixture()
    for arm in (left, right):
        for state in arm[0].state.values():
            state[field].zero_()
    result = compare(left, right, exact=True)
    assert all(metrics.exact_zero for _, metrics in getattr(result, field))
    right[0].state[right[1]["port.29.B"]][field][0] = 1e-12
    with pytest.raises(CheckpointFidelityError):
        compare(left, right)


@pytest.mark.parametrize("exact", [0, 1, None, "true"])
def test_invalid_exact_flags(exact):
    with pytest.raises(CheckpointFidelityError):
        compare(fixture(), fixture(), exact=exact)


@pytest.mark.parametrize(
    "kind",
    ["factors_none", "factors_empty", "base_none", "state_none", "state_not_mapping"],
)
def test_invalid_containers(kind):
    left, right = fixture(), fixture()
    optimizer, factors, base = right
    if kind == "factors_none":
        factors = None
    elif kind == "factors_empty":
        factors = {}
    elif kind == "base_none":
        base = None
    elif kind == "state_none":
        optimizer.state = None
    elif kind == "state_not_mapping":
        optimizer.state[factors["port.29.B"]] = []
    with pytest.raises(CheckpointFidelityError):
        compare(left, (optimizer, factors, base))


def test_matching_wrong_state_cannot_pass_against_itself():
    left, right = fixture(), fixture()
    for arm in (left, right):
        arm[0].state[arm[1]["port.29.B"]]["step"].fill_(2)
    with pytest.raises(CheckpointFidelityError):
        compare(left, right, expected_step=1)


def test_factor_shape_mismatch_between_arms():
    left, right = fixture(), fixture()
    parameter = right[1]["port.29.B"]
    parameter.data = torch.tensor([[1.0, -2.0]])
    for key in ("exp_avg", "exp_avg_sq"):
        right[0].state[parameter][key] = right[0].state[parameter][key].reshape(1, 2)
    with pytest.raises(CheckpointFidelityError):
        compare(left, right)
