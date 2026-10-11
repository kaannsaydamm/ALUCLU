from __future__ import annotations

import pytest

from aluclu.alc_r0.primevul_pair_clone_graph import (
    PairCloneGraphError,
    PairCloneRecord,
    build_pair_clone_reference,
)


def _row(number: int, code: str, label: int) -> PairCloneRecord:
    return PairCloneRecord(f"primevul:{number}", code, label)


def _near_pair() -> tuple[str, str]:
    left = [f"v{index:03d}" for index in range(200)]
    right = left.copy()
    right[50] = "changed"
    return " ".join(left), " ".join(right)


def test_opposite_label_near_clones_are_one_unit_but_both_rows_remain() -> None:
    left, right = _near_pair()

    result = build_pair_clone_reference(
        train=(_row(1, left, 1), _row(2, right, 0)),
        validation=(),
        pair_edges=(),
    )

    assert result.root_by_id == {
        "primevul:1": "primevul:1",
        "primevul:2": "primevul:1",
    }
    assert tuple((row.source_id, row.target) for row in result.train) == (
        ("primevul:1", 1),
        ("primevul:2", 0),
    )
    assert result.train_components == 1
    assert result.near_joins == 1
    assert result.training_authority is False
    assert result.held_out_data_present is False


def test_identical_normalized_code_with_opposite_labels_still_fails() -> None:
    with pytest.raises(PairCloneGraphError, match="exact normalized-code labels"):
        build_pair_clone_reference(
            train=(_row(1, "int x = 1;", 1), _row(2, "int x = 1;", 0)),
            validation=(),
            pair_edges=(),
        )


def test_repeated_pair_endpoint_connects_dissimilar_codes_transitively() -> None:
    result = build_pair_clone_reference(
        train=(
            _row(1, "red blue green yellow orange", 1),
            _row(2, "alpha beta gamma delta epsilon", 0),
            _row(3, "one two three four five", 0),
        ),
        validation=(),
        pair_edges=(("primevul:1", "primevul:2"), ("primevul:1", "primevul:3")),
    )

    assert set(result.root_by_id.values()) == {"primevul:1"}
    assert result.train_components == 1
    assert result.pair_joins == 2
    assert len(result.train) == 3


def test_train_overlap_removes_whole_validation_dependency_component() -> None:
    left, right = _near_pair()
    result = build_pair_clone_reference(
        train=(_row(1, left, 0),),
        validation=(
            _row(2, right, 1),
            _row(3, "int totally_different;", 0),
            _row(4, "int isolated;", 0),
        ),
        pair_edges=(("primevul:2", "primevul:3"),),
    )

    assert result.root_by_id["primevul:2"] == "primevul:1"
    assert result.root_by_id["primevul:3"] == "primevul:1"
    assert tuple(row.source_id for row in result.validation) == ("primevul:4",)
    assert result.validation_removed_train_overlap == 2
    assert result.validation_removed_roots == 1


def test_same_label_exact_duplicates_keep_one_representative() -> None:
    result = build_pair_clone_reference(
        train=(_row(2, "int x = 1;", 1), _row(1, "int x = 1;", 1)),
        validation=(),
        pair_edges=(),
    )

    assert tuple(row.source_id for row in result.train) == ("primevul:1",)
    assert result.exact_joins == 1
    assert result.train_components == 1


def test_exact_train_validation_overlap_removes_validation_row() -> None:
    result = build_pair_clone_reference(
        train=(_row(1, "int x = 1;", 1),),
        validation=(_row(2, "int x = 1;", 1),),
        pair_edges=(),
    )

    assert result.validation == ()
    assert result.validation_removed_train_overlap == 1
    assert result.validation_removed_roots == 1


@pytest.mark.parametrize(
    "train,validation,edges,match",
    [
        ((PairCloneRecord("primevul:01", "int x;", 1),), (), (), "invalid"),
        ((_row(1, "int x;", 1), _row(1, "int y;", 0)), (), (), "source IDs"),
        ((_row(1, "int x;", 1),), (), (("primevul:1", "primevul:2"),), "unknown"),
        (
            (_row(1, "int x;", 1), _row(2, "int y;", 1)),
            (),
            (("primevul:1", "primevul:2"),),
            "opposite",
        ),
        (
            (_row(1, "int x;", 1), _row(2, "int y;", 0)),
            (),
            (("primevul:1", "primevul:2"), ("primevul:1", "primevul:2")),
            "duplicate",
        ),
        (
            (_row(1, "int x;", 1),),
            (_row(2, "int y;", 0),),
            (("primevul:1", "primevul:2"),),
            "crosses development splits",
        ),
    ],
)
def test_invalid_graph_inputs_fail_closed(
    train: tuple[PairCloneRecord, ...],
    validation: tuple[PairCloneRecord, ...],
    edges: tuple[tuple[str, str], ...],
    match: str,
) -> None:
    with pytest.raises(PairCloneGraphError, match=match):
        build_pair_clone_reference(train=train, validation=validation, pair_edges=edges)


def test_reference_resource_bound_rejects_large_input() -> None:
    rows = tuple(_row(index, "int x;", 0) for index in range(4097))

    with pytest.raises(PairCloneGraphError, match="resource bound"):
        build_pair_clone_reference(train=rows, validation=(), pair_edges=())
