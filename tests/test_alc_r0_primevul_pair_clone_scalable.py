from __future__ import annotations

import pytest

from aluclu.alc_r0.primevul_pair_clone_graph import (
    PairCloneGraphError,
    PairCloneRecord,
    build_pair_clone_reference,
)
from aluclu.alc_r0.primevul_pair_clone_scalable import build_pair_clone_scalable


def _row(index: int, code: str, label: int) -> PairCloneRecord:
    return PairCloneRecord(f"primevul:{index}", code, label)


def _near_pair() -> tuple[str, str]:
    left = [f"v{index:03d}" for index in range(200)]
    right = left.copy()
    right[50] = "changed"
    return " ".join(left), " ".join(right)


def test_scalable_graph_matches_reference_with_cross_split_and_pair_edges() -> None:
    near_left, near_right = _near_pair()
    train = (
        _row(1, near_left, 1),
        _row(2, near_right, 0),
        _row(3, "alpha beta gamma delta epsilon", 0),
        _row(4, "alpha beta gamma delta epsilon", 0),
    )
    validation = (
        _row(5, near_right, 0),
        _row(6, "one two three four five", 1),
        _row(7, "six seven eight nine ten", 0),
    )
    edges = (("primevul:1", "primevul:3"), ("primevul:6", "primevul:7"))

    expected = build_pair_clone_reference(
        train=train, validation=validation, pair_edges=edges
    )
    actual = build_pair_clone_scalable(
        train=train, validation=validation, pair_edges=edges
    )

    assert actual == expected
    assert tuple(row.source_id for row in actual.validation) == (
        "primevul:6",
        "primevul:7",
    )


def test_scalable_graph_matches_reference_on_repeated_near_candidates() -> None:
    base = [f"v{index:03d}" for index in range(200)]
    rows = []
    for index in range(15):
        tokens = base.copy()
        tokens[20 + index] = f"changed{index}"
        rows.append(_row(index + 1, " ".join(tokens), index % 2))
    train = tuple(rows)

    expected = build_pair_clone_reference(train=train, validation=(), pair_edges=())
    actual = build_pair_clone_scalable(train=train, validation=(), pair_edges=())

    assert actual == expected
    assert actual.lsh_candidate_pairs > 0


def test_scalable_graph_rejects_exact_conflicting_labels() -> None:
    train = (_row(1, "int x = 1;", 1), _row(2, "int x = 1;", 0))

    with pytest.raises(PairCloneGraphError, match="exact normalized-code labels"):
        build_pair_clone_scalable(train=train, validation=(), pair_edges=())


def test_scalable_graph_candidate_budget_fails_closed() -> None:
    left, right = _near_pair()
    train = (_row(1, left, 1), _row(2, right, 0))

    with pytest.raises(PairCloneGraphError, match="candidate resource bound"):
        build_pair_clone_scalable(
            train=train, validation=(), pair_edges=(), max_candidate_pairs=0
        )


def test_scalable_graph_handles_more_rows_than_reference_limit() -> None:
    train = tuple(_row(index, "int x = 1;", 1) for index in range(4097))

    result = build_pair_clone_scalable(train=train, validation=(), pair_edges=())

    assert len(result.train) == 1
    assert result.exact_joins == 4096
    assert result.train_components == 1
    assert result.training_authority is False
