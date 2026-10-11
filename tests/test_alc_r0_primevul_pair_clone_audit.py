from __future__ import annotations

from dataclasses import replace

import pytest

from aluclu.alc_r0.primevul_pair_clone_audit import (
    PairCloneAuditError,
    audit_pair_clone_result,
)
from aluclu.alc_r0.primevul_pair_clone_graph import (
    PairCloneRecord,
    build_pair_clone_reference,
)
from aluclu.alc_r0.primevul_pair_clone_scalable import build_pair_clone_scalable


def _fixture():
    train = (
        PairCloneRecord("primevul:1", "a b c d e", 1),
        PairCloneRecord("primevul:2", "f g h i j", 0),
    )
    validation = (
        PairCloneRecord("primevul:3", "a b c d e", 1),
        PairCloneRecord("primevul:4", "k l m n o", 0),
        PairCloneRecord("primevul:5", "k l m n o", 0),
    )
    edges = (("primevul:1", "primevul:2"),)
    result = build_pair_clone_reference(
        train=train, validation=validation, pair_edges=edges
    )
    return train, validation, edges, result


@pytest.mark.parametrize(
    "builder", [build_pair_clone_reference, build_pair_clone_scalable]
)
def test_audit_accepts_graph_and_reports_no_validation_leak(builder) -> None:
    train, validation, edges, result = _fixture()
    result = builder(train=train, validation=validation, pair_edges=edges)

    audit = audit_pair_clone_result(
        train=train, validation=validation, pair_edges=edges, result=result
    )

    assert audit["status"] == "structural-audit-clear-non-authorizing"
    assert audit["input_rows"] == 5
    assert audit["retained_train_rows"] == 2
    assert audit["retained_validation_rows"] == 1
    assert audit["validation_removed_train_overlap"] == 1
    assert audit["exact_duplicate_rows"] == 2
    assert audit["training_authority"] is False


def test_audit_rejects_nonminimal_or_inconsistent_root_mapping() -> None:
    train, validation, edges, result = _fixture()
    root_by_id = dict(result.root_by_id)
    root_by_id["primevul:1"] = "primevul:2"

    with pytest.raises(PairCloneAuditError, match="root"):
        audit_pair_clone_result(
            train=train,
            validation=validation,
            pair_edges=edges,
            result=replace(result, root_by_id=root_by_id),
        )


def test_audit_rejects_wrong_representative() -> None:
    train, validation, edges, result = _fixture()

    with pytest.raises(PairCloneAuditError, match="representative"):
        audit_pair_clone_result(
            train=train,
            validation=validation,
            pair_edges=edges,
            result=replace(result, validation=(validation[2],)),
        )


def test_audit_rejects_pair_edge_outside_its_component() -> None:
    train, validation, _, result = _fixture()

    with pytest.raises(PairCloneAuditError, match="pair edge"):
        audit_pair_clone_result(
            train=train,
            validation=validation,
            pair_edges=(("primevul:1", "primevul:4"),),
            result=result,
        )


def test_audit_rejects_wrong_reported_overlap_count() -> None:
    train, validation, edges, result = _fixture()

    with pytest.raises(PairCloneAuditError, match="overlap"):
        audit_pair_clone_result(
            train=train,
            validation=validation,
            pair_edges=edges,
            result=replace(result, validation_removed_train_overlap=0),
        )


def test_audit_rejects_wrong_exact_join_count() -> None:
    train, validation, edges, result = _fixture()

    with pytest.raises(PairCloneAuditError, match="exact join"):
        audit_pair_clone_result(
            train=train,
            validation=validation,
            pair_edges=edges,
            result=replace(result, exact_joins=0),
        )
