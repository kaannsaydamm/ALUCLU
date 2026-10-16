import tracemalloc
from itertools import product

import pytest

from aluclu.alc_r0.banded_edit_token_visibility_reference import (
    BandedEditVisibilityLimits,
    audit_banded_edit_token_visibility,
)
from aluclu.alc_r0.edit_token_visibility_reference import audit_edit_token_visibility


def test_crossed_joint_and_direct_total():
    result = audit_banded_edit_token_visibility(
        (1, 2), (2, 1), code_budgets=(1,), distance_threshold=2
    )
    assert result.status == "exact-non-authorizing"
    exposure = result.budgets[0]
    assert (exposure.first_min, exposure.first_max) == (0, 1)
    assert (exposure.second_min, exposure.second_max) == (0, 1)
    assert (exposure.total_min, exposure.total_max) == (1, 1)
    assert exposure.joint_signature_bits == 6


def test_binary_full_reference_parity_all_thresholds():
    sequences = [s for n in range(5) for s in product((0, 1), repeat=n)]
    for first in sequences:
        for second in sequences:
            expected = audit_edit_token_visibility(
                first, second, code_budgets=(1, 2, 3, 4, 5)
            )
            for threshold in range(len(first) + len(second) + 2):
                actual = audit_banded_edit_token_visibility(
                    first,
                    second,
                    code_budgets=(1, 2, 3, 4, 5),
                    distance_threshold=threshold,
                )
                if expected.edit_distance <= threshold:
                    assert actual.edit_distance == expected.edit_distance
                    assert actual.budgets == expected.budgets
                    assert actual.status == "exact-non-authorizing"
                else:
                    assert actual.reason == "distance-threshold-exceeded"
                    assert actual.edit_distance is None and actual.budgets == ()
                assert actual.training_authority is False
                assert actual.held_out_data_present is False


def test_geometry_and_preflight():
    for n in range(6):
        for m in range(6):
            for threshold in range(7):
                result = audit_banded_edit_token_visibility(
                    tuple(range(n)),
                    tuple(range(m)),
                    code_budgets=(1,),
                    distance_threshold=threshold,
                )
                cells = [
                    (i, j)
                    for i in range(n + 1)
                    for j in range(m + 1)
                    if abs(i - j) + abs(n - m - (i - j)) <= threshold
                ]
                if threshold < abs(n - m):
                    assert result.band_lower_diagonal is None
                    assert result.scheduled_band_cells == result.visited_band_cells == 0
                    assert result.estimated_scratch_bytes is None
                else:
                    assert (
                        result.scheduled_band_cells
                        == result.visited_band_cells
                        == len(cells)
                    )
                    assert result.max_row_width == max(
                        sum(i == row for i, _ in cells) for row in range(n + 1)
                    )


def test_resource_exact_fit_and_one_under():
    args = ((1, 2), (2, 1))
    baseline = audit_banded_edit_token_visibility(
        *args, code_budgets=(1,), distance_threshold=2
    )
    for limits, reason in (
        (
            BandedEditVisibilityLimits(
                max_band_cells=baseline.scheduled_band_cells - 1
            ),
            "band-cell-limit",
        ),
        (
            BandedEditVisibilityLimits(
                max_scratch_bytes=baseline.estimated_scratch_bytes - 1
            ),
            "scratch-byte-limit",
        ),
        (BandedEditVisibilityLimits(max_endpoint_tokens=1), "endpoint-token-limit"),
    ):
        result = audit_banded_edit_token_visibility(
            *args, code_budgets=(1,), distance_threshold=2, limits=limits
        )
        assert result.reason == reason
        assert result.visited_band_cells == result.allocated_packed_payload_bytes == 0
        assert result.edit_distance is None and result.budgets == ()
    exact = audit_banded_edit_token_visibility(
        *args,
        code_budgets=(1,),
        distance_threshold=2,
        limits=BandedEditVisibilityLimits(
            max_band_cells=baseline.scheduled_band_cells,
            max_scratch_bytes=baseline.estimated_scratch_bytes,
        ),
    )
    assert exact.budgets == baseline.budgets


def test_long_identity_and_repeated_insertion():
    first = tuple(range(10000))
    result = audit_banded_edit_token_visibility(
        first, first, code_budgets=(1,), distance_threshold=0
    )
    assert result.edit_distance == 0
    assert result.scheduled_band_cells == 10001 and result.max_row_width == 1
    repeat = audit_banded_edit_token_visibility(
        (7,) * 10000, (7,) * 10001, code_budgets=(1,), distance_threshold=1
    )
    assert repeat.edit_distance == 1 and repeat.scheduled_band_cells == 20002
    row = repeat.budgets[0]
    assert (
        row.first_min,
        row.first_max,
        row.second_min,
        row.second_max,
        row.total_min,
        row.total_max,
        row.joint_signature_bits,
    ) == (0, 0, 0, 1, 0, 1, 3)


@pytest.mark.parametrize("threshold", [-1, True, 513, 1.0])
def test_invalid_threshold(threshold):
    with pytest.raises(ValueError):
        audit_banded_edit_token_visibility(
            (), (), code_budgets=(1,), distance_threshold=threshold
        )


def test_giant_budget():
    result = audit_banded_edit_token_visibility(
        (1,), (1, 2), code_budgets=(1 << 1000000,), distance_threshold=1
    )
    assert result.edit_distance == 1
    assert result.budgets[0].joint_signature_bits == 2


def _independent_oracle(first, second, budget):
    paths = []

    def retained(length, position):
        return int(
            length <= budget
            or position < (budget + 1) // 2
            or position >= length - budget // 2
        )

    def visit(i, j, distance, left, right):
        if i == len(first) and j == len(second):
            paths.append((distance, left, right))
            return
        if i < len(first) and j < len(second) and first[i] == second[j]:
            visit(i + 1, j + 1, distance, left, right)
        if i < len(first):
            visit(i + 1, j, distance + 1, left + retained(len(first), i), right)
        if j < len(second):
            visit(i, j + 1, distance + 1, left, right + retained(len(second), j))

    visit(0, 0, 0, 0, 0)
    distance = min(p[0] for p in paths)
    selected = [p for p in paths if p[0] == distance]
    left, right = [p[1] for p in selected], [p[2] for p in selected]
    totals = [p[1] + p[2] for p in selected]
    signatures = {(2 if p[1] else 0) | (1 if p[2] else 0) for p in selected}
    return distance, (
        min(left),
        max(left),
        min(right),
        max(right),
        min(totals),
        max(totals),
        sum(1 << s for s in signatures),
    )


def test_independent_all_paths_oracle():
    sequences = [s for n in range(5) for s in product((0, 1), repeat=n)]
    for first in sequences:
        for second in sequences:
            expected = [
                _independent_oracle(first, second, budget) for budget in range(1, 6)
            ]
            for threshold in range(len(first) + len(second) + 2):
                actual = audit_banded_edit_token_visibility(
                    first,
                    second,
                    code_budgets=(1, 2, 3, 4, 5),
                    distance_threshold=threshold,
                )
                if expected[0][0] > threshold:
                    assert actual.edit_distance is None and actual.budgets == ()
                else:
                    assert actual.edit_distance == expected[0][0]
                    for row, (_, values) in zip(actual.budgets, expected):
                        assert (
                            row.first_min,
                            row.first_max,
                            row.second_min,
                            row.second_max,
                            row.total_min,
                            row.total_max,
                            row.joint_signature_bits,
                        ) == values


def test_long_unique_insertion_and_helper_allocation_bound():
    first = tuple(range(10000))
    second = first[:5000] + (10000,) + first[5000:]
    budgets = (1, 2, 3, 4, 5)
    tracemalloc.start()
    try:
        result = audit_banded_edit_token_visibility(
            first, second, code_budgets=budgets, distance_threshold=1
        )
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert result.edit_distance == 1 and result.scheduled_band_cells == 20002
    assert all(
        row.total_max == 0 and row.joint_signature_bits == 1 for row in result.budgets
    )
    assert peak <= result.estimated_scratch_bytes


@pytest.mark.parametrize(
    "first,second,budgets",
    [
        ([1], (1,), (1,)),
        ((True,), (), (1,)),
        ((-1,), (), (1,)),
        ((), (), ()),
        ((), (), (1, 1)),
        ((), (), (True,)),
    ],
)
def test_invalid_inputs(first, second, budgets):
    with pytest.raises(ValueError):
        audit_banded_edit_token_visibility(
            first, second, code_budgets=budgets, distance_threshold=0
        )


def test_ternary_swap_nested_and_all_retained():
    sequences = [s for n in range(3) for s in product((0, 1, 2), repeat=n)]
    for first in sequences:
        for second in sequences:
            result = audit_banded_edit_token_visibility(
                first, second, code_budgets=(1, 2, 3), distance_threshold=4
            )
            swapped = audit_banded_edit_token_visibility(
                second, first, code_budgets=(1, 2, 3), distance_threshold=4
            )
            for row, other in zip(result.budgets, swapped.budgets):
                _, expected = _independent_oracle(first, second, row.code_budget)
                assert (
                    row.first_min,
                    row.first_max,
                    row.second_min,
                    row.second_max,
                    row.total_min,
                    row.total_max,
                    row.joint_signature_bits,
                ) == expected
                assert (row.first_min, row.first_max) == (
                    other.second_min,
                    other.second_max,
                )
                remapped = sum(
                    1 << (((signature & 1) << 1) | ((signature & 2) >> 1))
                    for signature in range(4)
                    if row.joint_signature_bits & (1 << signature)
                )
                assert other.joint_signature_bits == remapped
            assert all(
                a.total_min <= b.total_min and a.total_max <= b.total_max
                for a, b in zip(result.budgets, result.budgets[1:])
            )
            assert (
                result.budgets[-1].total_min
                == result.budgets[-1].total_max
                == result.edit_distance
            )


@pytest.mark.parametrize(
    "limits",
    [
        BandedEditVisibilityLimits(max_endpoint_tokens=32769),
        BandedEditVisibilityLimits(max_band_cells=0),
        BandedEditVisibilityLimits(max_scratch_bytes=67108865),
        BandedEditVisibilityLimits(max_distance_threshold=513),
        BandedEditVisibilityLimits(max_distance_threshold=True),
    ],
)
def test_invalid_limits(limits):
    with pytest.raises(ValueError):
        audit_banded_edit_token_visibility(
            (), (), code_budgets=(1,), distance_threshold=0, limits=limits
        )


def test_threshold_and_endpoint_hard_boundaries():
    identity = (3,) * 32768
    result = audit_banded_edit_token_visibility(
        identity,
        identity,
        code_budgets=(1,),
        distance_threshold=0,
        limits=BandedEditVisibilityLimits(max_distance_threshold=0),
    )
    assert result.edit_distance == 0 and result.visited_band_cells == 32769
    rejected = audit_banded_edit_token_visibility(
        identity + (3,), (), code_budgets=(1,), distance_threshold=0
    )
    assert (
        rejected.reason == "endpoint-token-limit"
        and rejected.scheduled_band_cells is None
    )
    maximal = audit_banded_edit_token_visibility(
        (), (), code_budgets=(1,), distance_threshold=512
    )
    assert maximal.edit_distance == 0


@pytest.mark.parametrize(
    "first,second,budgets,threshold",
    [
        ((), (), (1,), 0),
        ((1, 2), (1, 3, 2), (1 << 1000000,), 1),
        (tuple(range(600)), tuple(range(600)), (1, 2, 3, 4, 5), 512),
    ],
)
def test_allocation_payload_and_corner_bounds(first, second, budgets, threshold):
    tracemalloc.start()
    try:
        result = audit_banded_edit_token_visibility(
            first, second, code_budgets=budgets, distance_threshold=threshold
        )
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert result.max_row_width <= 513
    assert result.allocated_packed_payload_bytes == 2 * (
        1 + 7 * len(budgets)
    ) * 4 * result.max_row_width + len(budgets) * (len(first) + len(second))
    assert peak <= result.estimated_scratch_bytes
