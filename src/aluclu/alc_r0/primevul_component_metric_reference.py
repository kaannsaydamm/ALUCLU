"""Non-authorizing exact reference for PrimeVul component-vote mechanics.

This does not choose bootstrap random vectors, compute confidence intervals,
access sealed data, or replace the frozen ALC-R0 evaluator. It tests the unit
of observation and the unit of resampling proposed in the v2 draft.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction

_ROOT = re.compile(r"primevul:(?:0|[1-9][0-9]*)\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class ComponentMetricError(ValueError):
    """The component scoring input violates the candidate graph contract."""


@dataclass(frozen=True)
class ScoredObservation:
    root: str
    normalized_sha256: str
    truth: int
    prediction: int


@dataclass(frozen=True)
class ComponentClassSupport:
    total: int
    positive_containing: int
    negative_containing: int
    mixed: int
    retained_observations: int


@dataclass(frozen=True)
class ComponentMacroF1:
    macro_f1: Fraction
    scored_observations: int


def _canonical_observations(
    observations: tuple[ScoredObservation, ...],
) -> dict[str, tuple[ScoredObservation, ...]]:
    if not isinstance(observations, tuple) or not observations:
        raise ComponentMetricError("nonempty tuple of scored observations required")
    by_code: dict[str, ScoredObservation] = {}
    by_root: dict[str, list[ScoredObservation]] = {}
    for row in observations:
        if not isinstance(row, ScoredObservation) or (
            not isinstance(row.root, str)
            or not _ROOT.fullmatch(row.root)
            or not isinstance(row.normalized_sha256, str)
            or not _SHA256.fullmatch(row.normalized_sha256)
            or type(row.truth) is not int
            or row.truth not in (0, 1)
            or type(row.prediction) is not int
            or row.prediction not in (0, 1)
        ):
            raise ComponentMetricError("invalid scored observation")
        previous = by_code.get(row.normalized_sha256)
        if previous is not None:
            if previous.root != row.root:
                raise ComponentMetricError("identical code occurs in multiple roots")
            if previous.truth != row.truth:
                raise ComponentMetricError("identical code has opposite labels")
            if previous.prediction != row.prediction:
                raise ComponentMetricError("duplicate prediction disagreement")
            continue
        by_code[row.normalized_sha256] = row
        by_root.setdefault(row.root, []).append(row)
    return {root: tuple(by_root[root]) for root in sorted(by_root)}


def component_class_support(
    observations: tuple[ScoredObservation, ...],
) -> ComponentClassSupport:
    """Count distinct components once, and mixed components in both classes."""

    by_root = _canonical_observations(observations)
    positive = sum(any(row.truth == 1 for row in rows) for rows in by_root.values())
    negative = sum(any(row.truth == 0 for row in rows) for rows in by_root.values())
    return ComponentClassSupport(
        total=len(by_root),
        positive_containing=positive,
        negative_containing=negative,
        mixed=positive + negative - len(by_root),
        retained_observations=sum(len(rows) for rows in by_root.values()),
    )


def score_component_macro_f1(
    observations: tuple[ScoredObservation, ...],
    *,
    draw_roots: tuple[str, ...] | None = None,
) -> ComponentMacroF1:
    """Score distinct observations; repeated sampled roots copy all their rows."""

    by_root = _canonical_observations(observations)
    if draw_roots is None:
        draw_roots = tuple(by_root)
    if not isinstance(draw_roots, tuple) or len(draw_roots) != len(by_root):
        raise ComponentMetricError("component draw length must match root count")
    if any(not isinstance(root, str) or root not in by_root for root in draw_roots):
        raise ComponentMetricError("component draw has an unknown root")
    confusion = [[0, 0], [0, 0]]
    for root in draw_roots:
        for row in by_root[root]:
            confusion[row.truth][row.prediction] += 1
    f1: list[Fraction] = []
    for label in (0, 1):
        tp = confusion[label][label]
        fp = confusion[1 - label][label]
        fn = confusion[label][1 - label]
        denominator = 2 * tp + fp + fn
        f1.append(Fraction(2 * tp, denominator) if denominator else Fraction(0))
    return ComponentMacroF1(
        macro_f1=sum(f1, Fraction(0)) / 2,
        scored_observations=sum(sum(row) for row in confusion),
    )
