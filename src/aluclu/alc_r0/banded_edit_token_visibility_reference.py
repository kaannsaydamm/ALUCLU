"""Fixture-only all-optimal-path exposure within an exact threshold-safe band.

No data/model access, adaptive threshold, fallback, or scientific authority.
"""

from array import array
from dataclasses import dataclass
from sys import getsizeof

from .edit_token_visibility_reference import BudgetExposure

MAX_ENDPOINT_TOKENS = 32768
MAX_BAND_CELLS = 4194304
MAX_DISTANCE_THRESHOLD = 512
MAX_SCRATCH_BYTES = 64 * 1024 * 1024


class BandedEditVisibilityError(ValueError):
    """Malformed fixture input or resource policy."""


@dataclass(frozen=True)
class BandedEditVisibilityLimits:
    max_endpoint_tokens: int = MAX_ENDPOINT_TOKENS
    max_band_cells: int = MAX_BAND_CELLS
    max_scratch_bytes: int = MAX_SCRATCH_BYTES
    max_distance_threshold: int = MAX_DISTANCE_THRESHOLD


@dataclass(frozen=True)
class BandedEditVisibilityResult:
    status: str
    reason: str | None
    first_tokens: int
    second_tokens: int
    requested_code_budgets: tuple[int, ...]
    distance_threshold: int
    band_lower_diagonal: int | None
    band_upper_diagonal: int | None
    scheduled_band_cells: int | None
    visited_band_cells: int
    max_row_width: int | None
    estimated_scratch_bytes: int | None
    allocated_packed_payload_bytes: int
    edit_distance: int | None
    budgets: tuple[BudgetExposure, ...]
    limits: BandedEditVisibilityLimits
    training_authority: bool = False
    held_out_data_present: bool = False


def _validate(first, second, budgets, threshold, limits):
    if not isinstance(limits, BandedEditVisibilityLimits):
        raise BandedEditVisibilityError("banded limits required")
    for value, ceiling in (
        (limits.max_endpoint_tokens, MAX_ENDPOINT_TOKENS),
        (limits.max_band_cells, MAX_BAND_CELLS),
        (limits.max_scratch_bytes, MAX_SCRATCH_BYTES),
    ):
        if type(value) is not int or not 0 < value <= ceiling:
            raise BandedEditVisibilityError("positive limits cannot relax ceilings")
    if (
        type(limits.max_distance_threshold) is not int
        or not 0 <= limits.max_distance_threshold <= MAX_DISTANCE_THRESHOLD
    ):
        raise BandedEditVisibilityError("invalid distance ceiling")
    if (
        type(threshold) is not int
        or not 0 <= threshold <= limits.max_distance_threshold
    ):
        raise BandedEditVisibilityError("invalid distance threshold")
    if not isinstance(first, tuple) or not isinstance(second, tuple):
        raise BandedEditVisibilityError("token endpoints must be tuples")
    if any(
        type(token) is not int or token < 0
        for endpoint in (first, second)
        for token in endpoint
    ):
        raise BandedEditVisibilityError("exact nonnegative integer tokens required")
    if (
        not isinstance(budgets, tuple)
        or not 1 <= len(budgets) <= 5
        or any(type(b) is not int or b <= 0 for b in budgets)
        or any(a >= b for a, b in zip(budgets, budgets[1:]))
    ):
        raise BandedEditVisibilityError("increasing positive code budgets required")


def _mask(length, budget):
    if budget >= length:
        return array("B", [1]) * length
    result = array("B", [0]) * length
    head, tail = (budget + 1) // 2, budget // 2
    for pos in range(length):
        result[pos] = int(pos < head or pos >= length - tail)
    return result


def _signature(bits, flag):
    if flag == 2:
        return (4 if bits & 5 else 0) | (8 if bits & 10 else 0)
    if flag == 1:
        return (2 if bits & 3 else 0) | (8 if bits & 12 else 0)
    return bits


def audit_banded_edit_token_visibility(
    first: tuple[int, ...],
    second: tuple[int, ...],
    *,
    code_budgets: tuple[int, ...],
    distance_threshold: int,
    limits: BandedEditVisibilityLimits = BandedEditVisibilityLimits(),
) -> BandedEditVisibilityResult:
    """Exact accepted results; unresolved results contain no partial metrics."""
    _validate(first, second, code_budgets, distance_threshold, limits)
    n, m, threshold = len(first), len(second), distance_threshold
    lower = upper = cells = width = scratch = None
    visited = payload = 0

    def result(reason, distance=None, exposures=()):
        return BandedEditVisibilityResult(
            "resource-unresolved-non-authorizing"
            if reason
            else "exact-non-authorizing",
            reason,
            n,
            m,
            code_budgets,
            threshold,
            lower,
            upper,
            cells,
            visited,
            width,
            scratch,
            payload,
            distance,
            exposures,
            limits,
        )

    if max(n, m) > limits.max_endpoint_tokens:
        return result("endpoint-token-limit")
    delta = n - m
    if abs(delta) > threshold:
        cells = width = 0
        return result("distance-threshold-exceeded")
    lower, upper = -((threshold - delta) // 2), (delta + threshold) // 2
    cells = width = 0
    for i in range(n + 1):
        row_width = max(0, min(m, i - lower) - max(0, i - upper) + 1)
        cells += row_width
        width = max(width, row_width)
    words, flags = array("I"), array("B")
    if words.itemsize != 4 or flags.itemsize != 1:
        raise BandedEditVisibilityError("uint32 and byte storage required")
    states, count = 1 + 7 * len(code_budgets), len(code_budgets)
    planned_payload = 2 * states * 4 * width + count * (n + m)
    scratch = (
        planned_payload
        + 2 * states * getsizeof(words)
        + 2 * count * getsizeof(flags)
        + 65536
    )
    if cells > limits.max_band_cells:
        return result("band-cell-limit")
    if scratch > limits.max_scratch_bytes:
        return result("scratch-byte-limit")
    first_masks = tuple(_mask(n, budget) for budget in code_budgets)
    second_masks = tuple(_mask(m, budget) for budget in code_budgets)
    infinity = n + m + 1
    previous = tuple(array("I", [0]) * width for _ in range(states))
    current = tuple(array("I", [0]) * width for _ in range(states))
    payload = planned_payload
    prev_low, prev_high = 0, -1
    for i in range(n + 1):
        low, high = max(0, i - upper), min(m, i - lower)
        for j in range(low, high + 1):
            column = j - low
            visited += 1
            current[0][column] = infinity
            for budget_index in range(count):
                offset = 1 + 7 * budget_index
                for objective in range(3):
                    current[offset + 2 * objective][column] = infinity
                    current[offset + 2 * objective + 1][column] = 0
                current[offset + 6][column] = 0
            if i == j == 0:
                current[0][column] = 0
                for budget_index in range(count):
                    offset = 1 + 7 * budget_index
                    for state in range(6):
                        current[offset + state][column] = 0
                    current[offset + 6][column] = 1
                continue
            candidates = []
            if i and prev_low <= j <= prev_high:
                index = j - prev_low
                if previous[0][index] < infinity:
                    candidates.append((previous[0][index] + 1, previous, index, 2))
            if j > low and current[0][column - 1] < infinity:
                candidates.append((current[0][column - 1] + 1, current, column - 1, 1))
            if (
                i
                and j
                and prev_low <= j - 1 <= prev_high
                and first[i - 1] == second[j - 1]
            ):
                index = j - 1 - prev_low
                if previous[0][index] < infinity:
                    candidates.append((previous[0][index], previous, index, 0))
            distance = min((item[0] for item in candidates), default=infinity)
            current[0][column] = distance
            for budget_index in range(count):
                offset = 1 + 7 * budget_index
                for cost, row, index, operation in candidates:
                    if cost != distance:
                        continue
                    left = first_masks[budget_index][i - 1] if operation == 2 else 0
                    right = second_masks[budget_index][j - 1] if operation == 1 else 0
                    for objective, added in enumerate((left, right, left + right)):
                        state = offset + 2 * objective
                        current[state][column] = min(
                            current[state][column], row[state][index] + added
                        )
                        current[state + 1][column] = max(
                            current[state + 1][column], row[state + 1][index] + added
                        )
                    current[offset + 6][column] |= _signature(
                        row[offset + 6][index], 2 if left else 1 if right else 0
                    )
        previous, current = current, previous
        prev_low, prev_high = low, high
    terminal = m - prev_low
    distance = previous[0][terminal]
    if distance > threshold:
        return result("distance-threshold-exceeded")
    exposures = tuple(
        BudgetExposure(
            budget, *(previous[1 + 7 * index + state][terminal] for state in range(7))
        )
        for index, budget in enumerate(code_budgets)
    )
    return result(None, distance, exposures)
