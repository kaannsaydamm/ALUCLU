"""Independent structural checks on a non-authorizing PrimeVul graph result.

This checks source IDs, roots, exact groups, pair edges, split exclusion, and
retained representatives. It does not independently discover near-clone edges
or authorize source rights, held-out access, training, or evaluation.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from typing import Any

from .canonical import canonical_json_bytes, sha256_bytes
from .devign_preprocess import normalize_devign_code
from .primevul_pair_clone_graph import PairCloneRecord, PairCloneReferenceResult


class PairCloneAuditError(ValueError):
    """A graph result violates an independently checkable structural rule."""


def _expected_representatives(
    rows: Iterable[tuple[PairCloneRecord, str, bytes]],
) -> tuple[PairCloneRecord, ...]:
    selected: dict[tuple[str, bytes, int], PairCloneRecord] = {}
    for row, root, digest in rows:
        key = (root, digest, row.target)
        prior = selected.get(key)
        if prior is None or row.source_id < prior.source_id:
            selected[key] = row
    return tuple(sorted(selected.values(), key=lambda row: row.source_id))


def audit_pair_clone_result(
    *,
    train: tuple[PairCloneRecord, ...],
    validation: tuple[PairCloneRecord, ...],
    pair_edges: tuple[tuple[str, str], ...],
    result: PairCloneReferenceResult,
) -> dict[str, Any]:
    """Audit graph-output invariants without reusing its union/find procedure."""

    if (
        not isinstance(train, tuple)
        or not isinstance(validation, tuple)
        or not isinstance(pair_edges, tuple)
        or not isinstance(result, PairCloneReferenceResult)
        or not train + validation
    ):
        raise PairCloneAuditError("invalid audit input")
    if (
        result.training_authority is not False
        or result.held_out_data_present is not False
    ):
        raise PairCloneAuditError(
            "audit accepts only non-authorizing development results"
        )
    rows = train + validation
    by_id = {row.source_id: row for row in rows}
    if len(by_id) != len(rows) or set(result.root_by_id) != set(by_id):
        raise PairCloneAuditError("root ledger does not cover unique source IDs")
    if any(root not in by_id for root in result.root_by_id.values()):
        raise PairCloneAuditError("root ledger names a missing source ID")

    roots_minimum: dict[str, str] = {}
    exact_first: dict[bytes, tuple[int, str]] = {}
    normalized_digest: dict[str, bytes] = {}
    exact_duplicates = 0
    for row in rows:
        if type(row.target) is not int or row.target not in (0, 1):
            raise PairCloneAuditError("invalid source label")
        root = result.root_by_id[row.source_id]
        prior_minimum = roots_minimum.get(root)
        if prior_minimum is None or row.source_id < prior_minimum:
            roots_minimum[root] = row.source_id
        normalized = normalize_devign_code(
            row.function.encode("utf-8", errors="strict")
        )
        digest = hashlib.sha256(normalized.encode("utf-8")).digest()
        normalized_digest[row.source_id] = digest
        if digest in exact_first:
            exact_duplicates += 1
        previous = exact_first.setdefault(digest, (row.target, root))
        if previous != (row.target, root):
            raise PairCloneAuditError("exact code group crosses roots or labels")
    if any(root != minimum for root, minimum in roots_minimum.items()):
        raise PairCloneAuditError("root is not its component's minimum source ID")

    split_by_id = {row.source_id: "train" for row in train}
    split_by_id.update({row.source_id: "validation" for row in validation})
    for edge in pair_edges:
        if not isinstance(edge, tuple) or len(edge) != 2:
            raise PairCloneAuditError("invalid pair edge")
        left, right = edge
        if (
            left not in by_id
            or right not in by_id
            or left == right
            or split_by_id[left] != split_by_id[right]
            or by_id[left].target != 1
            or by_id[right].target != 0
            or result.root_by_id[left] != result.root_by_id[right]
        ):
            raise PairCloneAuditError("pair edge does not obey component contract")

    train_roots = {result.root_by_id[row.source_id] for row in train}
    validation_roots = {result.root_by_id[row.source_id] for row in validation}
    overlap_roots = train_roots & validation_roots
    safe_validation = tuple(
        row
        for row in validation
        if result.root_by_id[row.source_id] not in overlap_roots
    )
    expected_train = _expected_representatives(
        (row, result.root_by_id[row.source_id], normalized_digest[row.source_id])
        for row in train
    )
    expected_validation = _expected_representatives(
        (row, result.root_by_id[row.source_id], normalized_digest[row.source_id])
        for row in safe_validation
    )
    if result.train != expected_train or result.validation != expected_validation:
        raise PairCloneAuditError(
            "retained representative or validation exclusion mismatch"
        )
    if result.validation_removed_train_overlap != len(validation) - len(
        safe_validation
    ) or result.validation_removed_roots != len(overlap_roots):
        raise PairCloneAuditError("reported overlap count mismatch")
    if result.train_components != len(
        train_roots
    ) or result.validation_components != len(
        {result.root_by_id[row.source_id] for row in expected_validation}
    ):
        raise PairCloneAuditError("reported component count mismatch")
    if result.exact_joins != exact_duplicates:
        raise PairCloneAuditError("reported exact join count mismatch")
    return {
        "status": "structural-audit-clear-non-authorizing",
        "training_authority": False,
        "held_out_data_present": False,
        "input_rows": len(rows),
        "input_pair_edges": len(pair_edges),
        "exact_duplicate_rows": exact_duplicates,
        "retained_train_rows": len(expected_train),
        "retained_validation_rows": len(expected_validation),
        "validation_removed_train_overlap": len(validation) - len(safe_validation),
        "component_root_ledger_sha256": sha256_bytes(
            canonical_json_bytes(sorted(result.root_by_id.items()))
        ),
        "retained_train_id_ledger_sha256": sha256_bytes(
            canonical_json_bytes([row.source_id for row in expected_train])
        ),
        "retained_validation_id_ledger_sha256": sha256_bytes(
            canonical_json_bytes([row.source_id for row in expected_validation])
        ),
    }
