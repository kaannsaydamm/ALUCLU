"""Reproducible, development-only PrimeVul pair/clone reference pilot.

The first N original train-pair edges are selected by file order, not model
performance. This bounded pilot cannot qualify the full source or training.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Any

from .canonical import canonical_json_bytes, sha256_bytes
from .primevul_pair_clone_graph import PairCloneRecord, build_pair_clone_reference
from .primevul_pairs_source import (
    PRIMEVUL_ORIGINAL_PAIRS,
    PrimeVulPairExpectation,
    _decode_row,
    verify_primevul_development_pairs,
)
from .primevul_source import (
    PRIMEVUL_ORIGINAL_DEVELOPMENT,
    PrimeVulDevelopmentExpectation,
)

_MAX_PILOT_PAIRS = 2048


class PairClonePilotError(ValueError):
    """A pilot selection or pinned source mutation is invalid."""


def build_primevul_pair_clone_pilot(
    source_dir: Path,
    paired_dir: Path,
    *,
    pair_count: int = 50,
    source_expectation: PrimeVulDevelopmentExpectation = PRIMEVUL_ORIGINAL_DEVELOPMENT,
    pair_expectation: PrimeVulPairExpectation = PRIMEVUL_ORIGINAL_PAIRS,
) -> dict[str, Any]:
    """Verify both development sources, then graph only first N train pairs."""

    if (
        type(pair_count) is not int
        or pair_count < 1
        or pair_count > _MAX_PILOT_PAIRS
        or pair_count > pair_expectation.train_pairs
    ):
        raise PairClonePilotError("pilot pair count is outside pinned reference bounds")
    pair_receipt = verify_primevul_development_pairs(
        source_dir,
        paired_dir,
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
    )
    selected_rows: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    with (paired_dir / "primevul_train_paired.jsonl").open("rb") as stream:
        for index, raw in enumerate(stream):
            digest.update(raw)
            if index < 2 * pair_count:
                selected_rows.append(_decode_row(raw))
    if digest.hexdigest() != pair_expectation.train_sha256:
        raise PairClonePilotError("paired train SHA-256 changed during pilot read")
    if len(selected_rows) != 2 * pair_count:
        raise PairClonePilotError("pilot pair rows missing")
    records: dict[str, PairCloneRecord] = {}
    edges: list[tuple[str, str]] = []
    for left, right in zip(selected_rows[::2], selected_rows[1::2], strict=True):
        for row in (left, right):
            source_id = f"primevul:{row['idx']}"
            record = PairCloneRecord(source_id, row["func"], row["target"])
            prior = records.setdefault(source_id, record)
            if prior != record:
                raise PairClonePilotError("pilot source ID changed across pairs")
        edges.append((f"primevul:{left['idx']}", f"primevul:{right['idx']}"))
    result = build_pair_clone_reference(
        train=tuple(records.values()), validation=(), pair_edges=tuple(edges)
    )
    return {
        "receipt_version": 1,
        "status": "development-reference-pilot-non-authorizing",
        "training_authority": False,
        "held_out_data_present": False,
        "full_corpus_graph_executed": False,
        "pair_source_receipt_sha256": sha256_bytes(canonical_json_bytes(pair_receipt)),
        "selection_rule": "first-N-train-pair-edges-in-author-file-order",
        "selected_edge_ledger_sha256": sha256_bytes(canonical_json_bytes(edges)),
        "component_root_ledger_sha256": sha256_bytes(
            canonical_json_bytes(sorted(result.root_by_id.items()))
        ),
        "input_pair_edges": len(edges),
        "input_unique_source_ids": len(records),
        "train_components": result.train_components,
        "retained_train_rows": len(result.train),
        "exact_joins": result.exact_joins,
        "near_joins": result.near_joins,
        "pair_joins": result.pair_joins,
        "lsh_candidate_pairs": result.lsh_candidate_pairs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("development_data_dir", type=Path)
    parser.add_argument("paired_development_data_dir", type=Path)
    parser.add_argument("--pair-count", type=int, default=50)
    args = parser.parse_args()
    receipt = build_primevul_pair_clone_pilot(
        args.development_data_dir,
        args.paired_development_data_dir,
        pair_count=args.pair_count,
    )
    sys.stdout.buffer.write(canonical_json_bytes(receipt) + b"\n")


if __name__ == "__main__":
    main()
