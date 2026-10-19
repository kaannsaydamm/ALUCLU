from __future__ import annotations

from array import array
from itertools import product
from sys import getsizeof

import pytest

from aluclu.alc_r0.edit_token_visibility_reference import (
    MAX_DP_CELLS,
    MAX_ENDPOINT_TOKENS,
    MAX_PACKED_SCRATCH_BYTES,
    EditVisibilityError,
    EditVisibilityLimits,
    audit_edit_token_visibility,
    estimate_scratch_bytes,
)


def _oracle(a: tuple[int, ...], b: tuple[int, ...], budget: int):
    # Enumerate edit paths, then select terminal minima. No DP/memoization or
    # implementation retention/signature helpers are used.
    paths: list[tuple[int, int, int]] = []

    def retained(length: int, position: int) -> int:
        if length <= budget:
            return 1
        head = budget // 2 + budget % 2
        tail_start = length - budget // 2
        return int(position < head or position >= tail_start)

    def visit(i: int, j: int, distance: int, left: int, right: int) -> None:
        if i == len(a) and j == len(b):
            paths.append((distance, left, right))
            return
        if i < len(a) and j < len(b) and a[i] == b[j]:
            visit(i + 1, j + 1, distance, left, right)
        if i < len(a):
            visit(i + 1, j, distance + 1, left + retained(len(a), i), right)
        if j < len(b):
            visit(i, j + 1, distance + 1, left, right + retained(len(b), j))

    visit(0, 0, 0, 0, 0)
    distance = min(row[0] for row in paths)
    shortest = [row for row in paths if row[0] == distance]
    left = [row[1] for row in shortest]
    right = [row[2] for row in shortest]
    total = [row[1] + row[2] for row in shortest]
    signatures = {(2 if v else 0) + (1 if p else 0) for _, v, p in shortest}
    return (
        distance,
        (min(left), max(left)),
        (min(right), max(right)),
        (min(total), max(total)),
        sum(1 << value for value in signatures),
    )


def _values(result, index=0):
    row = result.budgets[index]
    return (
        result.edit_distance,
        (row.first_min, row.first_max),
        (row.second_min, row.second_max),
        (row.total_min, row.total_max),
        row.joint_signature_bits,
    )


@pytest.mark.parametrize(
    ("a", "b", "budget", "distance", "total"),
    [
        ((1, 2, 3), (1, 9, 3), 2, 2, (0, 0)),
        ((1, 2, 3), (9, 2, 3), 2, 2, (2, 2)),
        ((1, 2, 3), (1, 9, 2, 3), 2, 1, (0, 0)),
        ((1, 2), (1, 9, 2), 2, 1, (0, 0)),
        ((1, 1, 1), (1, 1, 1, 1), 2, 1, (0, 1)),
        ((1, 2, 3, 4, 5, 6), (9, 2, 8, 4, 5, 7), 4, 6, (4, 4)),
        ((1, 2, 3), (1, 9, 3), 3, 2, (2, 2)),
    ],
)
def test_hand_fixtures(a, b, budget, distance, total):
    result = audit_edit_token_visibility(a, b, code_budgets=(budget,))
    assert result.status == "exact-non-authorizing"
    assert result.edit_distance == distance
    assert _values(result)[3] == total
    assert _values(result) == _oracle(a, b, budget)
    assert result.training_authority is False
    assert result.held_out_data_present is False


def test_joint_existence_cannot_be_inferred_from_marginal_maxima():
    result = audit_edit_token_visibility((1, 2), (2, 1), code_budgets=(1,))
    assert _values(result) == (2, (0, 1), (0, 1), (1, 1), 0b0110)


def test_giant_positive_budget_retains_all_without_large_budget_arithmetic():
    giant_budget = 1 << 1_000_000
    result = audit_edit_token_visibility(
        (1, 2, 3), (1, 2, 9, 3), code_budgets=(giant_budget,)
    )
    assert _values(result) == (1, (0, 0), (1, 1), (1, 1), 0b0010)
    assert result.estimated_scratch_bytes == estimate_scratch_bytes(3, 4, 1)


def test_exhaustive_tiny_paths_and_nested_budget_invariants():
    tuples = [
        values for length in range(5) for values in product((0, 1), repeat=length)
    ]
    for a in tuples:
        for b in tuples:
            result = audit_edit_token_visibility(a, b, code_budgets=(1, 2, 3, 4, 5))
            previous_min = previous_max = 0
            for index, budget in enumerate((1, 2, 3, 4, 5)):
                assert _values(result, index) == _oracle(a, b, budget)
                row = result.budgets[index]
                assert (
                    previous_min
                    <= row.total_min
                    <= row.total_max
                    <= result.edit_distance
                )
                assert previous_max <= row.total_max
                assert (
                    0
                    <= row.first_min
                    <= row.first_max
                    <= (result.edit_distance + len(a) - len(b)) // 2
                )
                assert (
                    0
                    <= row.second_min
                    <= row.second_max
                    <= (result.edit_distance + len(b) - len(a)) // 2
                )
                assert row.first_min + row.second_min <= row.total_min
                assert row.total_max <= row.first_max + row.second_max
                previous_min, previous_max = row.total_min, row.total_max
            full = result.budgets[-1]
            assert full.total_min == full.total_max == result.edit_distance


def test_symmetry_identity_and_empty_boundary_states():
    for a, b in [((1, 1, 2), (1, 2)), ((), (1, 2, 3)), ((), ()), ((9,), (9,))]:
        forward = audit_edit_token_visibility(a, b, code_budgets=(1, 2, 4))
        reverse = audit_edit_token_visibility(b, a, code_budgets=(1, 2, 4))
        assert forward.edit_distance == reverse.edit_distance
        for row, swapped in zip(forward.budgets, reverse.budgets):
            assert (row.first_min, row.first_max) == (
                swapped.second_min,
                swapped.second_max,
            )
            assert (row.total_min, row.total_max) == (
                swapped.total_min,
                swapped.total_max,
            )
            swapped_bits = sum(
                1 << ((signature & 1) * 2 + (signature & 2) // 2)
                for signature in range(4)
                if row.joint_signature_bits & (1 << signature)
            )
            assert swapped.joint_signature_bits == swapped_bits
        if a == b:
            assert forward.edit_distance == 0
            assert all(
                row.total_max == 0 and row.joint_signature_bits == 1
                for row in forward.budgets
            )


@pytest.mark.parametrize(
    "a,b",
    [
        ([1], (1,)),
        ((1,), [1]),
        ((True,), (1,)),
        ((-1,), (1,)),
        ((1.0,), (1,)),
        ((1,), ("a",)),
    ],
)
def test_invalid_token_inputs_fail_closed(a, b):
    with pytest.raises(EditVisibilityError):
        audit_edit_token_visibility(a, b, code_budgets=(1,))


@pytest.mark.parametrize(
    "budgets",
    [(), [1], (True,), (0,), (-1,), (1.5,), (2, 1), (1, 1), (1, 2, 3, 4, 5, 6)],
)
def test_invalid_budgets_fail_closed(budgets):
    with pytest.raises(EditVisibilityError):
        audit_edit_token_visibility((1,), (2,), code_budgets=budgets)


def test_hard_caps_and_tightened_limits_return_structured_unresolved():
    cases = [
        (
            (1,) * (MAX_ENDPOINT_TOKENS + 1),
            (),
            EditVisibilityLimits(),
            "endpoint-token-limit",
        ),
        ((1,) * 2048, (2,) * 2048, EditVisibilityLimits(), "dp-cell-limit"),
        ((1,), (2,), EditVisibilityLimits(max_dp_cells=3), "dp-cell-limit"),
        ((1,), (2,), EditVisibilityLimits(max_scratch_bytes=1), "scratch-byte-limit"),
    ]
    for a, b, limits, reason in cases:
        result = audit_edit_token_visibility(a, b, code_budgets=(1,), limits=limits)
        assert result.status == "resource-unresolved-non-authorizing"
        assert result.reason == reason
        assert result.edit_distance is None
        assert result.budgets == ()
        assert result.dp_cells == (len(a) + 1) * (len(b) + 1)
        assert result.training_authority is False
        if len(a) > MAX_ENDPOINT_TOKENS:
            assert result.estimated_scratch_bytes is None
    exact = audit_edit_token_visibility(
        (1,),
        (2,),
        code_budgets=(1,),
        limits=EditVisibilityLimits(max_endpoint_tokens=1, max_dp_cells=4),
    )
    assert exact.edit_distance == 2


@pytest.mark.parametrize(
    "dimensions",
    [
        (-1, 0, 1),
        (0, -1, 1),
        (True, 0, 1),
        (0, 0, True),
        (0, 0, 0),
        (0, 0, 6),
        (MAX_ENDPOINT_TOKENS + 1, 0, 1),
    ],
)
def test_invalid_scratch_dimensions_fail_closed(dimensions):
    with pytest.raises(EditVisibilityError):
        estimate_scratch_bytes(*dimensions)


def test_scratch_estimate_accounts_for_headers_masks_and_cap_boundary():
    expected = (
        2 * (1 + 7 * 5) * (getsizeof(array("I")) + 4 * 8)
        + 2 * 5 * getsizeof(array("B"))
        + 5 * (9 + 7)
        + 65_536
    )
    assert estimate_scratch_bytes(9, 7, 5) == expected
    assert (
        estimate_scratch_bytes(MAX_ENDPOINT_TOKENS, MAX_ENDPOINT_TOKENS, 5)
        < MAX_PACKED_SCRATCH_BYTES
    )
    size = estimate_scratch_bytes(1, 1, 1)
    exact = audit_edit_token_visibility(
        (1,),
        (2,),
        code_budgets=(1,),
        limits=EditVisibilityLimits(max_scratch_bytes=size),
    )
    assert exact.status == "exact-non-authorizing"
    unresolved = audit_edit_token_visibility(
        (1,),
        (2,),
        code_budgets=(1,),
        limits=EditVisibilityLimits(max_scratch_bytes=size - 1),
    )
    assert unresolved.reason == "scratch-byte-limit"


@pytest.mark.parametrize(
    "limits",
    [
        None,
        EditVisibilityLimits(max_endpoint_tokens=True),
        EditVisibilityLimits(max_dp_cells=0),
        EditVisibilityLimits(max_scratch_bytes=-1),
        EditVisibilityLimits(max_endpoint_tokens=MAX_ENDPOINT_TOKENS + 1),
        EditVisibilityLimits(max_dp_cells=MAX_DP_CELLS + 1),
        EditVisibilityLimits(max_scratch_bytes=MAX_PACKED_SCRATCH_BYTES + 1),
    ],
)
def test_limits_cannot_be_invalid_or_relax_hard_ceilings(limits):
    with pytest.raises(EditVisibilityError):
        audit_edit_token_visibility((1,), (2,), code_budgets=(1,), limits=limits)


def test_byte_tokenizer_prompt_parity_without_snapshot():
    from test_alc_r0_defect_prompt import _ByteTokenizer

    from aluclu.alc_r0.defect_prompt import prepare_defect_prompt

    tokenizer = _ByteTokenizer()
    prefix = b"Labels: safe vulnerable\nInput: "
    suffix = b"\nVerdict:"
    reserve = len(b" vulnerable")
    a, b = b"ABCDE", b"AXCYE"
    for budget in (1, 2, 3, 4, 5):
        template = prepare_defect_prompt(
            tokenizer, max_tokens=len(prefix) + len(suffix) + reserve + budget
        )
        head, tail = (budget + 1) // 2, budget // 2
        for code in (a, b):
            selected = (
                code
                if len(code) <= budget
                else code[:head] + (code[-tail:] if tail else b"")
            )
            assert template.build(code).token_ids == tuple(prefix + selected + suffix)
        result = audit_edit_token_visibility(tuple(a), tuple(b), code_budgets=(budget,))
        assert _values(result) == _oracle(tuple(a), tuple(b), budget)
