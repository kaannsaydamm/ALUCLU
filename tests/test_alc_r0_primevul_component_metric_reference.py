from __future__ import annotations

from fractions import Fraction

import pytest

from aluclu.alc_r0.primevul_component_metric_reference import (
    ComponentMetricError,
    ScoredObservation,
    component_class_support,
    score_component_macro_f1,
)


def _row(root: int, code: str, truth: int, prediction: int) -> ScoredObservation:
    return ScoredObservation(
        root=f"primevul:{root}",
        normalized_sha256=code * 64,
        truth=truth,
        prediction=prediction,
    )


def _fixture() -> tuple[ScoredObservation, ...]:
    return (
        _row(1, "a", 1, 1),
        _row(1, "a", 1, 1),  # exact duplicate: zero extra vote
        _row(1, "b", 0, 0),  # mixed-label component
        _row(2, "c", 0, 1),
        _row(3, "d", 0, 0),
    )


def test_component_support_counts_mixed_root_once_in_total_and_both_classes() -> None:
    support = component_class_support(_fixture())

    assert support.total == 3
    assert support.positive_containing == 1
    assert support.negative_containing == 3
    assert support.mixed == 1
    assert support.retained_observations == 4


def test_point_macro_f1_deduplicates_exact_same_code_label() -> None:
    score = score_component_macro_f1(_fixture())

    assert score.macro_f1 == Fraction(11, 15)
    assert score.scored_observations == 4


def test_cluster_draw_repeats_all_mixed_root_observations_together() -> None:
    score = score_component_macro_f1(
        _fixture(), draw_roots=("primevul:1", "primevul:1", "primevul:3")
    )

    assert score.macro_f1 == 1
    assert score.scored_observations == 5


def test_two_distinct_same_label_observations_stay_in_one_cluster() -> None:
    rows = (
        _row(1, "a", 0, 0),
        _row(1, "b", 0, 1),
        _row(2, "c", 1, 1),
    )

    support = component_class_support(rows)
    drawn = score_component_macro_f1(rows, draw_roots=("primevul:1", "primevul:1"))

    assert support.total == 2
    assert support.negative_containing == 1
    assert support.positive_containing == 1
    assert drawn.scored_observations == 4
    assert drawn.macro_f1 == Fraction(1, 3)


def test_duplicate_prediction_disagreement_fails_closed() -> None:
    with pytest.raises(ComponentMetricError, match="duplicate prediction"):
        score_component_macro_f1((_row(1, "a", 1, 1), _row(1, "a", 1, 0)))


def test_identical_code_in_two_roots_fails_closed() -> None:
    with pytest.raises(ComponentMetricError, match="multiple roots"):
        component_class_support((_row(1, "a", 1, 1), _row(2, "a", 1, 1)))


def test_opposite_labels_for_identical_code_fail_closed() -> None:
    with pytest.raises(ComponentMetricError, match="opposite labels"):
        component_class_support((_row(1, "a", 1, 1), _row(1, "a", 0, 0)))


def test_draw_must_have_one_slot_per_unique_component() -> None:
    with pytest.raises(ComponentMetricError, match="draw length"):
        score_component_macro_f1(_fixture(), draw_roots=("primevul:1",))
