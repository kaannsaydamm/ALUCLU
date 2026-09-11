from __future__ import annotations

from decimal import Decimal, localcontext
from typing import Any, cast

import pytest

import aluclu.cognition.calibration as calibration_module
from aluclu.cognition import InputBoundaryError
from aluclu.cognition.calibration import clopper_pearson_upper_bound

# Independently generated at 160 decimal digits by regularized-beta inversion,
# then cross-checked with a separate arbitrary-precision binomial recurrence.
# Expected values are upper-rounded to the frozen 24-place output lattice.
_BOUND_FIXTURES = (
    (0, 0, "0.05", 10, "1"),
    (0, 1, "0.01", 1, "0.99"),
    (1, 1, "0.01", 1, "1"),
    (7, 7, "0.01", 8, "1"),
    (0, 100, "0.05", 10, "0.051604029624104003416529"),
    (3, 20, "0.05", 10, "0.449465406739485979638068"),
    (2, 100, "0.01", 20, "0.114628478227106434215945"),
    (0, 8_192, "0.01", 20, "0.000927414223873145725855"),
    (41, 8_192, "0.01", 20, "0.008122492527907508061789"),
    (8_191, 8_192, "0.01", 20, "0.999999938949581736343229"),
)

_REFERENCE_BRACKETS = (
    (
        0,
        100,
        "0.05",
        10,
        "0.051604029624104003416528549011825019770120768102135988378746",
        "0.051604029624104003416528549011825019770120768102135988378747",
    ),
    (
        3,
        20,
        "0.05",
        10,
        "0.449465406739485979638067610044323945311094092586512976964716",
        "0.449465406739485979638067610044323945311094092586512976964717",
    ),
    (
        2,
        100,
        "0.01",
        20,
        "0.114628478227106434215944787848433887325401418530863489815916",
        "0.114628478227106434215944787848433887325401418530863489815917",
    ),
    (
        0,
        8_192,
        "0.01",
        20,
        "0.000927414223873145725854448067561957565569046658234555190542",
        "0.000927414223873145725854448067561957565569046658234555190543",
    ),
    (
        41,
        8_192,
        "0.01",
        20,
        "0.008122492527907508061788090989821658758303277727626238650759",
        "0.008122492527907508061788090989821658758303277727626238650760",
    ),
    (
        8_191,
        8_192,
        "0.01",
        20,
        "0.999999938949581736343228208189735343252037573678027376928347",
        "0.999999938949581736343228208189735343252037573678027376928348",
    ),
)


@pytest.mark.parametrize(
    ("error_count", "selected_count", "delta_decimal", "family_size", "expected"),
    _BOUND_FIXTURES,
)
def test_clopper_pearson_upper_bound_matches_independent_fixtures(
    error_count: int,
    selected_count: int,
    delta_decimal: str,
    family_size: int,
    expected: str,
) -> None:
    assert (
        clopper_pearson_upper_bound(
            error_count=error_count,
            selected_count=selected_count,
            delta_decimal=delta_decimal,
            family_size=family_size,
        )
        == expected
    )


@pytest.mark.parametrize(
    (
        "error_count",
        "selected_count",
        "delta_decimal",
        "family_size",
        "reference_lower",
        "reference_upper",
    ),
    _REFERENCE_BRACKETS,
)
def test_clopper_pearson_result_is_conservatively_upper_rounded(
    error_count: int,
    selected_count: int,
    delta_decimal: str,
    family_size: int,
    reference_lower: str,
    reference_upper: str,
) -> None:
    actual = Decimal(
        clopper_pearson_upper_bound(
            error_count=error_count,
            selected_count=selected_count,
            delta_decimal=delta_decimal,
            family_size=family_size,
        )
    )

    assert actual >= Decimal(reference_upper)
    assert actual - Decimal(reference_lower) <= Decimal("1e-24")


def test_clopper_pearson_uses_bonferroni_tail_for_the_full_family() -> None:
    corrected = clopper_pearson_upper_bound(
        error_count=0,
        selected_count=100,
        delta_decimal="0.05",
        family_size=10,
    )
    uncorrected = clopper_pearson_upper_bound(
        error_count=0,
        selected_count=100,
        delta_decimal="0.05",
        family_size=1,
    )

    assert corrected == "0.051604029624104003416529"
    assert uncorrected == "0.029513049607039934500476"
    assert Decimal(corrected) > Decimal(uncorrected)


def test_clopper_pearson_ignores_the_ambient_decimal_context() -> None:
    baseline = clopper_pearson_upper_bound(
        error_count=0,
        selected_count=100,
        delta_decimal="0.05",
        family_size=1,
    )

    with localcontext() as hostile_context:
        hostile_context.prec = 6
        hostile_context.Emin = -9
        hostile_context.Emax = 9
        equivalent_tail = clopper_pearson_upper_bound(
            error_count=0,
            selected_count=100,
            delta_decimal="0.1",
            family_size=2,
        )

    assert baseline == "0.029513049607039934500476"
    assert equivalent_tail == baseline


def test_exact_fallback_reduces_the_probability_ratio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gcd_calls: list[tuple[int, int]] = []
    original_gcd = calibration_module.math.gcd

    def recording_gcd(left: int, right: int) -> int:
        gcd_calls.append((left, right))
        return original_gcd(left, right)

    monkeypatch.setattr(calibration_module.math, "gcd", recording_gcd)

    assert (
        clopper_pearson_upper_bound(
            error_count=250,
            selected_count=501,
            delta_decimal="0.5",
            family_size=1,
        )
        == "0.5"
    )
    assert (5 * 10**35, 10**36) in gcd_calls


def test_clopper_pearson_accepts_the_frozen_decimal_precision_boundary() -> None:
    assert (
        clopper_pearson_upper_bound(
            error_count=0,
            selected_count=0,
            delta_decimal=f"0.{'0' * 35}1",
            family_size=256,
        )
        == "1"
    )


@pytest.mark.parametrize(
    "overrides",
    (
        {"error_count": True},
        {"error_count": -1},
        {"error_count": 65_537},
        {"error_count": 2, "selected_count": 1},
        {"selected_count": True},
        {"selected_count": -1},
        {"selected_count": 65_537},
        {"family_size": True},
        {"family_size": 0},
        {"family_size": 257},
        {"delta_decimal": 0.05},
        {"delta_decimal": ""},
        {"delta_decimal": "0"},
        {"delta_decimal": "1"},
        {"delta_decimal": ".05"},
        {"delta_decimal": "0.050"},
        {"delta_decimal": "5e-2"},
        {"delta_decimal": "-0.05"},
        {"delta_decimal": "NaN"},
        {"delta_decimal": f"0.{'0' * 36}1"},
    ),
)
def test_clopper_pearson_rejects_noncanonical_or_invalid_inputs(
    overrides: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "error_count": 0,
        "selected_count": 10,
        "delta_decimal": "0.05",
        "family_size": 4,
    }
    arguments.update(overrides)

    untyped_boundary_call = cast(Any, clopper_pearson_upper_bound)
    with pytest.raises(InputBoundaryError):
        untyped_boundary_call(**arguments)
