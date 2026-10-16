"""Synthesized receipts only: no forward/backward/optimizer execution evidence."""

from dataclasses import replace

import pytest

from aluclu.alc_r0.checkpoint_fidelity import TensorComparison
from aluclu.alc_r0.checkpoint_optimizer import AdamWComparison
from aluclu.alc_r0.checkpoint_parity_cell import CaseComparison, ParityCell
from aluclu.alc_r0.reference_parity_receipt import (
    REFERENCE_NAMES,
    ReferenceParityIdentity,
    ReferenceParityReceipt,
    validate_reference_parity_receipt,
)


def receipt(device="cpu"):
    identity = ReferenceParityIdentity(
        device,
        "torch.float32" if device == "cpu" else "torch.bfloat16",
        "a" * 64,
        "b" * 64,
        "c" * 64,
        "d" * 64,
    )
    cases = tuple(
        CaseComparison(
            state,
            repeat,
            index,
            (1.0, 1.0),
            (-1.0, -1.0),
            identity.base_digest,
            ("e" if state == "zero" else "f") * 64,
        )
        for state, repeat in (("zero", 0), ("nonzero", 0), ("nonzero", 1))
        for index in range(6)
    )
    metrics = tuple(
        (name, TensorComparison(1.0, 1.0, 0.0, 0.0, 1.0, False))
        for name in REFERENCE_NAMES
    )
    cell = ParityCell(
        cases,
        (2.0, 2.0),
        AdamWComparison(1, metrics, metrics, metrics),
        REFERENCE_NAMES,
        460800,
        identity.base_digest,
    )
    return ReferenceParityReceipt(identity, 20260916, cell)


def validate(result):
    validate_reference_parity_receipt(result, expected_identity=receipt().identity)


def test_complete_cpu_and_gpu_receipts():
    for device in ("cpu", "cuda:0"):
        result = receipt(device)
        validate_reference_parity_receipt(result, expected_identity=result.identity)
    assert len(REFERENCE_NAMES) == 120
    assert REFERENCE_NAMES.index("factors.10.q.A") < REFERENCE_NAMES.index(
        "factors.2.q.A"
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_device", "cuda:1"),
        ("source_dtype", "torch.float16"),
        ("base_digest", "z" * 64),
        ("configuration_digest", "B" * 64),
        ("host_identity_digest", None),
        ("fixture_digest", "0" * 63),
    ],
)
def test_bad_identity(field, value):
    result = receipt()
    with pytest.raises(ValueError):
        validate(replace(result, identity=replace(result.identity, **{field: value})))


def test_valid_but_foreign_identity():
    result = receipt()
    with pytest.raises(ValueError):
        validate(
            replace(result, identity=replace(result.identity, fixture_digest="0" * 64))
        )


@pytest.mark.parametrize("seed", [True, 0, 20260917, "20260916"])
def test_wrong_seed(seed):
    with pytest.raises(ValueError):
        validate(replace(receipt(), seed=seed))


@pytest.mark.parametrize(
    "mode",
    ["count", "bool_count", "names", "reverse", "duplicate", "base", "partial", "list"],
)
def test_incomplete_or_foreign_cell(mode):
    result = receipt()
    cell = result.cell
    changes = {
        "count": {"parameter_count": 1},
        "bool_count": {"parameter_count": True},
        "names": {"parameter_names": REFERENCE_NAMES[:-1]},
        "reverse": {"parameter_names": REFERENCE_NAMES[::-1]},
        "duplicate": {"parameter_names": (REFERENCE_NAMES[0],) * 120},
        "base": {"base_digest": "0" * 64},
        "partial": {"cases": cell.cases[:-1]},
        "list": {"cases": list(cell.cases)},
    }
    with pytest.raises(ValueError):
        validate(replace(result, cell=replace(cell, **changes[mode])))


@pytest.mark.parametrize(
    "field,value",
    [
        ("state", "other"),
        ("repeat", True),
        ("fixture_index", 1),
        ("losses", (float("nan"), 1.0)),
        ("scores", (-1.0, float("inf"))),
        ("losses", (1, 1.0)),
        ("losses", (1.0, 1.01)),
        ("base_digest", "0" * 64),
        ("factor_digest", "bad"),
    ],
)
def test_bad_single_row(field, value):
    result = receipt()
    cases = (replace(result.cell.cases[0], **{field: value}),) + result.cell.cases[1:]
    with pytest.raises(ValueError):
        validate(replace(result, cell=replace(result.cell, cases=cases)))


def test_factor_state_and_repetition_corruption():
    result = receipt()
    for index, digest in ((1, "0" * 64), (12, "0" * 64), (6, "e" * 64)):
        cases = list(result.cell.cases)
        cases[index] = replace(cases[index], factor_digest=digest)
        with pytest.raises(ValueError):
            validate(replace(result, cell=replace(result.cell, cases=tuple(cases))))


@pytest.mark.parametrize(
    "pending", [(), [2.0, 2.0], (True, 2.0), (float("inf"), 2.0), (2.0, 2.01)]
)
def test_bad_pending(pending):
    result = receipt()
    with pytest.raises(ValueError):
        validate(replace(result, cell=replace(result.cell, pending_losses=pending)))


@pytest.mark.parametrize("field", ["factors", "exp_avg", "exp_avg_sq"])
@pytest.mark.parametrize(
    "mode",
    [
        "partial",
        "reverse",
        "duplicate",
        "malformed",
        "nan",
        "bound",
        "zero",
        "cpu_difference",
    ],
)
def test_complete_optimizer_metrics_required(field, mode):
    result = receipt()
    optimizer = result.cell.accumulation
    mapping = getattr(optimizer, field)
    metric = mapping[0][1]
    changed = {
        "partial": mapping[:-1],
        "reverse": mapping[::-1],
        "duplicate": (mapping[0],) * 120,
        "malformed": (("bad",),) + mapping[1:],
        "nan": ((mapping[0][0], replace(metric, actual_l2=float("nan"))),)
        + mapping[1:],
        "bound": ((mapping[0][0], replace(metric, relative_l2=1e-4)),) + mapping[1:],
        "zero": ((mapping[0][0], replace(metric, exact_zero=True)),) + mapping[1:],
        "cpu_difference": (
            (mapping[0][0], replace(metric, difference_l2=1e-7, relative_l2=1e-7)),
        )
        + mapping[1:],
    }[mode]
    with pytest.raises(ValueError):
        validate(
            replace(
                result,
                cell=replace(
                    result.cell, accumulation=replace(optimizer, **{field: changed})
                ),
            )
        )


@pytest.mark.parametrize("step", [0, 2, True, 1.0])
def test_fixed_step1(step):
    result = receipt()
    with pytest.raises(ValueError):
        validate(
            replace(
                result,
                cell=replace(
                    result.cell,
                    accumulation=replace(result.cell.accumulation, step=step),
                ),
            )
        )


def test_exact_zero_metric_allowed_and_bad_receipt_type_denied():
    result = receipt()
    mapping = tuple(
        (name, TensorComparison(0.0, 0.0, 0.0, None, None, True))
        for name in REFERENCE_NAMES
    )
    validate(
        replace(
            result,
            cell=replace(
                result.cell,
                accumulation=replace(result.cell.accumulation, exp_avg=mapping),
            ),
        )
    )
    for bad in (None, {}, result.cell):
        with pytest.raises(ValueError):
            validate(bad)
