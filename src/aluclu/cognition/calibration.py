from __future__ import annotations

import math
import re
from collections.abc import Callable
from decimal import (
    ROUND_CEILING,
    ROUND_FLOOR,
    Decimal,
    DivisionByZero,
    InvalidOperation,
    Overflow,
    Underflow,
    localcontext,
)
from functools import lru_cache

from .contracts import InputBoundaryError

_CANONICAL_OPEN_PROBABILITY = re.compile(r"0\.(?:[0-9]*[1-9])\Z")
_MAX_SELECTED_EXAMPLES = 65_536
_MAX_THRESHOLD_FAMILY = 256
_OUTPUT_DECIMAL_PLACES = 24
_SOLVER_DECIMAL_PLACES = 36
_MAX_PROBABILITY_FRACTIONAL_DIGITS = _SOLVER_DECIMAL_PLACES
_SOLVER_SCALE = 10**_SOLVER_DECIMAL_PLACES
_OUTPUT_SCALE = 10**_OUTPUT_DECIMAL_PLACES
_OUTPUT_GUARD_FACTOR = 10 ** (
    _SOLVER_DECIMAL_PLACES - _OUTPUT_DECIMAL_PLACES
)
_CDF_PRECISIONS = (80, 120, 160, 200, 240)
_DECIMAL_EMIN = -999_999_999
_DECIMAL_EMAX = 999_999_999


def clopper_pearson_upper_bound(
    *,
    error_count: int,
    selected_count: int,
    delta_decimal: str,
    family_size: int,
) -> str:
    """Return a Bonferroni-corrected one-sided upper risk bound.

    The result is the smallest canonical 24-place decimal-lattice value proven
    not to be below the continuous Clopper-Pearson root. No binary floating
    point or ambient Decimal context participates in the calculation.
    """

    _require_int(error_count, "error_count", 0, _MAX_SELECTED_EXAMPLES)
    _require_int(selected_count, "selected_count", 0, _MAX_SELECTED_EXAMPLES)
    if error_count > selected_count:
        raise InputBoundaryError("error_count cannot exceed selected_count")
    _require_int(family_size, "family_size", 1, _MAX_THRESHOLD_FAMILY)
    delta = _require_open_probability(delta_decimal, "delta_decimal")
    if selected_count == 0 or error_count == selected_count:
        return "1"
    return _solve_upper_bound(
        error_count,
        selected_count,
        delta.as_integer_ratio(),
        family_size,
    )


@lru_cache(maxsize=256)
def _solve_upper_bound(
    error_count: int,
    selected_count: int,
    delta_ratio: tuple[int, int],
    family_size: int,
) -> str:
    delta_numerator, delta_denominator = delta_ratio
    tail_numerator = delta_numerator
    tail_denominator = delta_denominator * family_size
    common = math.gcd(tail_numerator, tail_denominator)
    tail_numerator //= common
    tail_denominator //= common

    lower = 0
    upper = _SOLVER_SCALE
    while upper - lower > 1:
        midpoint = (lower + upper) // 2
        side = _classify_binomial_cdf(
            error_count=error_count,
            selected_count=selected_count,
            probability_units=midpoint,
            tail_numerator=tail_numerator,
            tail_denominator=tail_denominator,
        )
        if side > 0:
            lower = midpoint
        else:
            upper = midpoint

    output_units = (
        upper + _OUTPUT_GUARD_FACTOR - 1
    ) // _OUTPUT_GUARD_FACTOR
    return _canonical_output_probability(output_units)


def _classify_binomial_cdf(
    *,
    error_count: int,
    selected_count: int,
    probability_units: int,
    tail_numerator: int,
    tail_denominator: int,
) -> int:
    """Return 1 below the root and -1 at-or-above the root."""

    for precision in _CDF_PRECISIONS:
        lower = _binomial_cdf_directed(
            error_count=error_count,
            selected_count=selected_count,
            probability_units=probability_units,
            precision=precision,
            rounding=ROUND_FLOOR,
        )
        upper = _binomial_cdf_directed(
            error_count=error_count,
            selected_count=selected_count,
            probability_units=probability_units,
            precision=precision,
            rounding=ROUND_CEILING,
        )
        if _compare_decimal_to_ratio(lower, tail_numerator, tail_denominator) > 0:
            return 1
        if _compare_decimal_to_ratio(upper, tail_numerator, tail_denominator) <= 0:
            return -1

    return _compare_binomial_cdf_exact(
        error_count=error_count,
        selected_count=selected_count,
        probability_numerator=probability_units,
        probability_denominator=_SOLVER_SCALE,
        tail_numerator=tail_numerator,
        tail_denominator=tail_denominator,
    )


def _binomial_cdf_directed(
    *,
    error_count: int,
    selected_count: int,
    probability_units: int,
    precision: int,
    rounding: str,
) -> Decimal:
    if probability_units == 0:
        return Decimal(1)
    if probability_units == _SOLVER_SCALE:
        return Decimal(0)

    with localcontext() as context:
        context.prec = precision
        context.rounding = rounding
        context.Emin = _DECIMAL_EMIN
        context.Emax = _DECIMAL_EMAX
        for signal in (DivisionByZero, InvalidOperation, Overflow, Underflow):
            context.traps[signal] = True

        probability = context.scaleb(
            Decimal(probability_units),
            -_SOLVER_DECIMAL_PLACES,
        )
        complement = context.subtract(Decimal(1), probability)

        probability_power = _directed_power(
            probability,
            error_count,
            context.multiply,
        )
        complement_power = _directed_power(
            complement,
            selected_count - error_count,
            context.multiply,
        )
        term = context.multiply(
            Decimal(math.comb(selected_count, error_count)),
            context.multiply(probability_power, complement_power),
        )
        cumulative = term
        for index in range(error_count, 0, -1):
            numerator = context.multiply(
                context.multiply(term, Decimal(index)),
                complement,
            )
            denominator = context.multiply(
                Decimal(selected_count - index + 1),
                probability,
            )
            term = context.divide(numerator, denominator)
            cumulative = context.add(cumulative, term)

        if cumulative > 1:
            return Decimal(1)
        return cumulative


def _directed_power(
    base: Decimal,
    exponent: int,
    multiply: Callable[[Decimal, Decimal], Decimal],
) -> Decimal:
    result = Decimal(1)
    factor = base
    remaining = exponent
    while remaining:
        if remaining & 1:
            result = multiply(result, factor)
        remaining >>= 1
        if remaining:
            factor = multiply(factor, factor)
    return result


def _compare_binomial_cdf_exact(
    *,
    error_count: int,
    selected_count: int,
    probability_numerator: int,
    probability_denominator: int,
    tail_numerator: int,
    tail_denominator: int,
) -> int:
    common = math.gcd(probability_numerator, probability_denominator)
    probability_numerator //= common
    probability_denominator //= common
    complement_numerator = probability_denominator - probability_numerator
    if probability_numerator == 0:
        return 1
    if complement_numerator == 0:
        return -1

    term = complement_numerator**selected_count
    cdf_numerator = term
    for index in range(error_count):
        dividend = (
            term
            * (selected_count - index)
            * probability_numerator
        )
        divisor = (index + 1) * complement_numerator
        term, remainder = divmod(dividend, divisor)
        if remainder:
            raise AssertionError("exact binomial recurrence lost integrality")
        cdf_numerator += term

    left = cdf_numerator * tail_denominator
    right = tail_numerator * (probability_denominator**selected_count)
    return 1 if left > right else -1


def _compare_decimal_to_ratio(
    value: Decimal,
    numerator: int,
    denominator: int,
) -> int:
    value_numerator, value_denominator = value.as_integer_ratio()
    left = value_numerator * denominator
    right = numerator * value_denominator
    return (left > right) - (left < right)


def _canonical_output_probability(output_units: int) -> str:
    if output_units >= _OUTPUT_SCALE:
        return "1"
    fraction = f"{output_units:0{_OUTPUT_DECIMAL_PLACES}d}".rstrip("0")
    if not fraction:
        return "0"
    return f"0.{fraction}"


def _require_open_probability(value: object, field_name: str) -> Decimal:
    if (
        type(value) is not str
        or len(value) > 2 + _MAX_PROBABILITY_FRACTIONAL_DIGITS
        or _CANONICAL_OPEN_PROBABILITY.fullmatch(value) is None
    ):
        raise InputBoundaryError(f"{field_name} must be a canonical open probability")
    parsed = Decimal(value)
    if not Decimal(0) < parsed < Decimal(1):
        raise InputBoundaryError(f"{field_name} must be strictly between zero and one")
    return parsed


def _require_int(value: object, field_name: str, lower: int, upper: int) -> None:
    if type(value) is not int or not lower <= value <= upper:
        raise InputBoundaryError(f"{field_name} is outside its integer boundary")
