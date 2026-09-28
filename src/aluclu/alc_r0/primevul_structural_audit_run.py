"""Rebuild the pinned development graph and structurally audit its receipt.

This is a separate, non-authorizing replay. Its checker does not independently
discover near-clone edges, and it never reads held-out test files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .canonical import canonical_json_bytes, sha256_bytes
from .primevul_near_edge_audit import audit_near_edges
from .primevul_pair_clone_audit import audit_pair_clone_result
from .primevul_pair_clone_full import _read_pair_edges, _read_source_split
from .primevul_pair_clone_scalable import build_pair_clone_scalable
from .primevul_pairs_source import (
    PRIMEVUL_ORIGINAL_PAIRS,
    PrimeVulPairExpectation,
    verify_primevul_development_pairs,
)
from .primevul_source import (
    PRIMEVUL_ORIGINAL_DEVELOPMENT,
    PrimeVulDevelopmentExpectation,
    _reject_constant,
    _unique_object,
)


class PrimeVulStructuralAuditError(ValueError):
    """The replay and the prior development receipt disagree."""


def run_primevul_structural_audit(
    source_dir: Path,
    paired_dir: Path,
    *,
    expected_receipt: dict[str, Any],
    source_expectation: PrimeVulDevelopmentExpectation = PRIMEVUL_ORIGINAL_DEVELOPMENT,
    pair_expectation: PrimeVulPairExpectation = PRIMEVUL_ORIGINAL_PAIRS,
    progress: Callable[[int, int, int], None] | None = None,
    include_near_edges: bool = False,
    near_progress: Callable[[int, int, int], None] | None = None,
) -> dict[str, Any]:
    """Verify sources, rebuild the graph, audit structure, and bind old ledgers."""

    if type(include_near_edges) is not bool or (
        near_progress is not None
        and (not include_near_edges or not callable(near_progress))
    ):
        raise PrimeVulStructuralAuditError(
            "invalid independent near-edge audit options"
        )
    if (
        not isinstance(expected_receipt, dict)
        or expected_receipt.get("status") != "development-graph-non-authorizing"
        or expected_receipt.get("training_authority") is not False
        or expected_receipt.get("held_out_data_present") is not False
    ):
        raise PrimeVulStructuralAuditError("non-authorizing prior receipt required")
    pair_receipt = verify_primevul_development_pairs(
        source_dir,
        paired_dir,
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
    )
    train = _read_source_split(
        source_dir / "primevul_train.jsonl",
        expected_sha256=source_expectation.train_sha256,
        expected_rows=source_expectation.train_rows,
    )
    validation = _read_source_split(
        source_dir / "primevul_valid.jsonl",
        expected_sha256=source_expectation.validation_sha256,
        expected_rows=source_expectation.validation_rows,
    )
    edges = _read_pair_edges(
        paired_dir / "primevul_train_paired.jsonl",
        expected_sha256=pair_expectation.train_sha256,
        expected_pairs=pair_expectation.train_pairs,
    ) + _read_pair_edges(
        paired_dir / "primevul_valid_paired.jsonl",
        expected_sha256=pair_expectation.validation_sha256,
        expected_pairs=pair_expectation.validation_pairs,
    )
    graph = build_pair_clone_scalable(
        train=train, validation=validation, pair_edges=edges, progress=progress
    )
    audit = audit_pair_clone_result(
        train=train, validation=validation, pair_edges=edges, result=graph
    )
    positive_roots = {
        graph.root_by_id[row.source_id] for row in graph.validation if row.target == 1
    }
    negative_roots = {
        graph.root_by_id[row.source_id] for row in graph.validation if row.target == 0
    }
    pinned_original = (
        source_expectation == PRIMEVUL_ORIGINAL_DEVELOPMENT
        and pair_expectation == PRIMEVUL_ORIGINAL_PAIRS
    )
    checks = {
        "source_scope": "pinned-original-development" if pinned_original else "fixture",
        "full_corpus_graph_executed": pinned_original,
        "pair_source_receipt_sha256": sha256_bytes(canonical_json_bytes(pair_receipt)),
        "pair_edge_ledger_sha256": sha256_bytes(canonical_json_bytes(edges)),
        "component_root_ledger_sha256": audit["component_root_ledger_sha256"],
        "retained_train_id_ledger_sha256": audit["retained_train_id_ledger_sha256"],
        "retained_validation_id_ledger_sha256": audit[
            "retained_validation_id_ledger_sha256"
        ],
        "input_train_rows": len(train),
        "input_validation_rows": len(validation),
        "input_pair_edges": len(edges),
        "retained_train_rows": len(graph.train),
        "retained_validation_rows": len(graph.validation),
        "train_components": graph.train_components,
        "validation_components": graph.validation_components,
        "validation_components_positive": len(positive_roots),
        "validation_components_negative": len(negative_roots),
        "validation_removed_train_overlap": graph.validation_removed_train_overlap,
        "validation_removed_roots": graph.validation_removed_roots,
        "exact_joins": graph.exact_joins,
        "lsh_candidate_pairs": graph.lsh_candidate_pairs,
        "near_joins": graph.near_joins,
        "pair_joins": graph.pair_joins,
    }
    mismatches = sorted(
        key for key, value in checks.items() if expected_receipt.get(key) != value
    )
    if mismatches:
        raise PrimeVulStructuralAuditError(
            "prior receipt mismatch: " + ", ".join(mismatches)
        )
    near_audit = (
        audit_near_edges(
            train=train,
            validation=validation,
            result=graph,
            progress=near_progress,
        )
        if include_near_edges
        else None
    )
    receipt = {
        **audit,
        "status": (
            "full-graph-structural-and-near-edge-audit-clear-non-authorizing"
            if include_near_edges
            else "full-graph-structural-audit-clear-non-authorizing"
        ),
        "source_scope": checks["source_scope"],
        "training_authority": False,
        "held_out_data_present": False,
        "previous_receipt_sha256": sha256_bytes(
            canonical_json_bytes(expected_receipt) + b"\n"
        ),
        "pair_source_receipt_sha256": checks["pair_source_receipt_sha256"],
    }
    if near_audit is not None:
        receipt["near_edge_audit"] = near_audit
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("development_data_dir", type=Path)
    parser.add_argument("paired_development_data_dir", type=Path)
    parser.add_argument("prior_receipt_file", type=Path)
    parser.add_argument("--expected-receipt-sha256", required=True)
    parser.add_argument("--include-near-edges", action="store_true")
    args = parser.parse_args()
    raw = args.prior_receipt_file.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.expected_receipt_sha256:
        raise PrimeVulStructuralAuditError("prior receipt file SHA-256 mismatch")
    expected_receipt = json.loads(
        raw.decode("utf-8", errors="strict"),
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
    )
    if raw != canonical_json_bytes(expected_receipt) + b"\n":
        raise PrimeVulStructuralAuditError(
            "prior receipt must be canonical JSON plus LF"
        )

    def report(processed: int, total: int, candidates: int) -> None:
        print(
            f"structural audit graph progress {processed}/{total} candidates={candidates}",
            file=sys.stderr,
            flush=True,
        )

    def report_near(processed: int, total: int, candidates: int) -> None:
        print(
            f"independent near audit progress {processed}/{total} candidates={candidates}",
            file=sys.stderr,
            flush=True,
        )

    audit = run_primevul_structural_audit(
        args.development_data_dir,
        args.paired_development_data_dir,
        expected_receipt=expected_receipt,
        progress=report,
        include_near_edges=args.include_near_edges,
        near_progress=report_near if args.include_near_edges else None,
    )
    sys.stdout.buffer.write(canonical_json_bytes(audit) + b"\n")


if __name__ == "__main__":
    main()
