"""Bounded, fixture-only edit-token exposure across all shortest alignments.

No data reader, tokenizer, model, prompt policy, or scientific gate lives here.
Replacement means deletion plus insertion; exposure counts token positions,
not semantic changes or vulnerability-bearing edits.
"""

from __future__ import annotations

from array import array
from dataclasses import dataclass
from sys import getsizeof

MAX_ENDPOINT_TOKENS = 32_768
MAX_DP_CELLS = 4_194_304
MAX_BUDGETS = 5
MAX_PACKED_SCRATCH_BYTES = 64 * 1024 * 1024
_BOOKKEEPING_BYTES = 65_536


class EditVisibilityError(ValueError):
    """Inputs do not satisfy the mathematical reference contract."""


@dataclass(frozen=True)
class EditVisibilityLimits:
    """Per-call limits may tighten, but never relax, the hard ceilings."""

    max_endpoint_tokens: int = MAX_ENDPOINT_TOKENS
    max_dp_cells: int = MAX_DP_CELLS
    max_scratch_bytes: int = MAX_PACKED_SCRATCH_BYTES


@dataclass(frozen=True)
class BudgetExposure:
    code_budget: int
    first_min: int
    first_max: int
    second_min: int
    second_max: int
    total_min: int
    total_max: int
    # Bit (1 << signature) represents a reachable signature. Within that
    # signature, mask value 2 means first exposed, mask value 1 second exposed.
    joint_signature_bits: int


@dataclass(frozen=True)
class EditVisibilityResult:
    status: str
    reason: str | None
    first_tokens: int
    second_tokens: int
    requested_code_budgets: tuple[int, ...]
    dp_cells: int
    estimated_scratch_bytes: int | None
    edit_distance: int | None
    budgets: tuple[BudgetExposure, ...]
    limits: EditVisibilityLimits
    training_authority: bool = False
    held_out_data_present: bool = False


def estimate_scratch_bytes(first_tokens: int, second_tokens: int, budgets: int) -> int:
    """Conservative packed storage preflight; inputs and process RSS excluded.

    Includes two uint32 rows (distance plus seven states per budget), byte
    retention masks, their array headers and fixed transient bookkeeping.
    Allocates only two empty arrays to inspect platform representation.
    """

    if (
        type(first_tokens) is not int
        or not 0 <= first_tokens <= MAX_ENDPOINT_TOKENS
        or type(second_tokens) is not int
        or not 0 <= second_tokens <= MAX_ENDPOINT_TOKENS
        or type(budgets) is not int
        or not 1 <= budgets <= MAX_BUDGETS
    ):
        raise EditVisibilityError("invalid scratch dimensions")
    words, flags = array("I"), array("B")
    if words.itemsize != 4 or flags.itemsize != 1:
        raise EditVisibilityError("four-byte uint32 and one-byte masks required")
    rows = (
        2
        * (1 + 7 * budgets)
        * (getsizeof(words) + words.itemsize * (second_tokens + 1))
    )
    masks = 2 * budgets * getsizeof(flags) + budgets * (first_tokens + second_tokens)
    return rows + masks + _BOOKKEEPING_BYTES


def _validate_limits(limits: EditVisibilityLimits) -> None:
    if not isinstance(limits, EditVisibilityLimits):
        raise EditVisibilityError("reference resource limits required")
    for value, ceiling in (
        (limits.max_endpoint_tokens, MAX_ENDPOINT_TOKENS),
        (limits.max_dp_cells, MAX_DP_CELLS),
        (limits.max_scratch_bytes, MAX_PACKED_SCRATCH_BYTES),
    ):
        if type(value) is not int or not 0 < value <= ceiling:
            raise EditVisibilityError(
                "limits must be positive and cannot relax ceilings"
            )


def _retention_mask(length: int, budget: int) -> array:
    # Fixed-size multiplication avoids generator append over-allocation; this
    # makes the packed scratch preflight account for the complete buffer.
    if length <= budget:
        # Avoid arithmetic on arbitrarily large caller-owned positive budgets.
        return array("B", [1]) * length
    mask = array("B", [0]) * length
    head, tail = (budget + 1) // 2, budget // 2
    for position in range(length):
        mask[position] = int(position < head or position >= length - tail)
    return mask


def _signature_after_exposure(bits: int, flag: int) -> int:
    if flag == 2:
        return (4 if bits & 0b0101 else 0) | (8 if bits & 0b1010 else 0)
    if flag == 1:
        return (2 if bits & 0b0011 else 0) | (8 if bits & 0b1100 else 0)
    return bits


def audit_edit_token_visibility(
    first: tuple[int, ...],
    second: tuple[int, ...],
    *,
    code_budgets: tuple[int, ...],
    limits: EditVisibilityLimits = EditVisibilityLimits(),
) -> EditVisibilityResult:
    """Compute exact marginal/direct-total bounds and joint reachability.

    All minimum insertion/deletion paths remain eligible, including paths
    skipping equal tokens. Each reported extremum is optimized independently;
    joint existence is represented by signature sets, not marginal arithmetic.
    Empty endpoints are valid mathematical fixtures. Resource-unresolved
    results contain no distance or partial bounds and preserve the denominator.
    """

    _validate_limits(limits)
    if not isinstance(first, tuple) or not isinstance(second, tuple):
        raise EditVisibilityError("token endpoints must be tuples")
    if any(type(token) is not int or token < 0 for token in first) or any(
        type(token) is not int or token < 0 for token in second
    ):
        raise EditVisibilityError("token IDs must be exact nonnegative integers")
    if (
        not isinstance(code_budgets, tuple)
        or not 1 <= len(code_budgets) <= MAX_BUDGETS
        or any(type(budget) is not int or budget < 1 for budget in code_budgets)
        or any(left >= right for left, right in zip(code_budgets, code_budgets[1:]))
    ):
        raise EditVisibilityError(
            "one to five increasing positive code budgets required"
        )
    n, m = len(first), len(second)
    cells = (n + 1) * (m + 1)
    # Oversized endpoints have no admissible allocation estimate. Null avoids
    # suggesting that an unattempted allocation needs zero bytes.
    scratch = (
        estimate_scratch_bytes(n, m, len(code_budgets))
        if max(n, m) <= MAX_ENDPOINT_TOKENS
        else None
    )
    reason = None
    if max(n, m) > limits.max_endpoint_tokens:
        reason = "endpoint-token-limit"
    elif cells > limits.max_dp_cells:
        reason = "dp-cell-limit"
    elif scratch is not None and scratch > limits.max_scratch_bytes:
        reason = "scratch-byte-limit"
    if reason is not None:
        return EditVisibilityResult(
            "resource-unresolved-non-authorizing",
            reason,
            n,
            m,
            code_budgets,
            cells,
            scratch,
            None,
            (),
            limits,
        )

    first_masks = tuple(_retention_mask(n, budget) for budget in code_budgets)
    second_masks = tuple(_retention_mask(m, budget) for budget in code_budgets)
    states = 1 + 7 * len(code_budgets)
    previous = tuple(array("I", [0]) * (m + 1) for _ in range(states))
    current = tuple(array("I", [0]) * (m + 1) for _ in range(states))
    for j in range(m + 1):
        previous[0][j] = j
    for k, mask in enumerate(second_masks):
        offset, exposed = 1 + 7 * k, 0
        for j in range(m + 1):
            if j:
                exposed += mask[j - 1]
            for state in (2, 3, 4, 5):
                previous[offset + state][j] = exposed
            previous[offset + 6][j] = 2 if exposed else 1

    boundary_exposed = [0] * len(code_budgets)
    for i in range(1, n + 1):
        current[0][0] = i
        for k, mask in enumerate(first_masks):
            offset = 1 + 7 * k
            boundary_exposed[k] += mask[i - 1]
            for state in (0, 1, 4, 5):
                current[offset + state][0] = boundary_exposed[k]
            current[offset + 2][0] = current[offset + 3][0] = 0
            current[offset + 6][0] = 4 if boundary_exposed[k] else 1
        for j in range(1, m + 1):
            delete_distance = previous[0][j] + 1
            insert_distance = current[0][j - 1] + 1
            match_distance = (
                previous[0][j - 1] if first[i - 1] == second[j - 1] else n + m + 1
            )
            distance = min(delete_distance, insert_distance, match_distance)
            current[0][j] = distance
            # Keep every primary-optimal edge, even when equal IDs match.
            predecessors = []
            if delete_distance == distance:
                predecessors.append((previous, j, 2))
            if insert_distance == distance:
                predecessors.append((current, j - 1, 1))
            if match_distance == distance:
                predecessors.append((previous, j - 1, 0))
            for k in range(len(code_budgets)):
                offset = 1 + 7 * k
                lows = [n + m + 1] * 3
                highs = [0] * 3
                signatures = 0
                for row, column, operation in predecessors:
                    left = first_masks[k][i - 1] if operation == 2 else 0
                    right = second_masks[k][j - 1] if operation == 1 else 0
                    for objective, added in enumerate((left, right, left + right)):
                        state = offset + 2 * objective
                        lows[objective] = min(
                            lows[objective], row[state][column] + added
                        )
                        highs[objective] = max(
                            highs[objective], row[state + 1][column] + added
                        )
                    flag = 2 if left else 1 if right else 0
                    signatures |= _signature_after_exposure(
                        row[offset + 6][column], flag
                    )
                for objective in range(3):
                    current[offset + 2 * objective][j] = lows[objective]
                    current[offset + 2 * objective + 1][j] = highs[objective]
                current[offset + 6][j] = signatures
        previous, current = current, previous

    exposures = tuple(
        BudgetExposure(budget, *(previous[1 + 7 * k + state][m] for state in range(7)))
        for k, budget in enumerate(code_budgets)
    )
    return EditVisibilityResult(
        "exact-non-authorizing",
        None,
        n,
        m,
        code_budgets,
        cells,
        scratch,
        previous[0][m],
        exposures,
        limits,
    )
