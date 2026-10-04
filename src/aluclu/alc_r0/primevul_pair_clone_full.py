"""Verify pinned PrimeVul development files and run the pair/clone graph.

The CLI reads only author train and validation sources. It emits a metadata-
only receipt; it never opens the held-out test files or authorizes training.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .canonical import canonical_json_bytes, sha256_bytes
from .primevul_pair_clone_graph import PairCloneRecord
from .primevul_pair_clone_scalable import build_pair_clone_scalable
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


class PrimeVulFullGraphError(ValueError):
    """Pinned development source changed during a graph replay."""


def _read_source_split(
    path: Path, *, expected_sha256: str, expected_rows: int
) -> tuple[PairCloneRecord, ...]:
    if path.is_symlink() or not path.is_file():
        raise PrimeVulFullGraphError("development source is no longer a regular file")
    digest = hashlib.sha256()
    result: list[PairCloneRecord] = []
    with path.open("rb") as stream:
        for raw in stream:
            digest.update(raw)
            row = _decode_row(raw)
            result.append(
                PairCloneRecord(f"primevul:{row['idx']}", row["func"], row["target"])
            )
    if digest.hexdigest() != expected_sha256 or len(result) != expected_rows:
        raise PrimeVulFullGraphError("development source changed during graph replay")
    return tuple(result)


def _read_pair_edges(
    path: Path, *, expected_sha256: str, expected_pairs: int
) -> tuple[tuple[str, str], ...]:
    if path.is_symlink() or not path.is_file():
        raise PrimeVulFullGraphError("paired source is no longer a regular file")
    digest = hashlib.sha256()
    result: list[tuple[str, str]] = []
    with path.open("rb") as stream:
        for left_raw in stream:
            right_raw = stream.readline()
            if not right_raw:
                raise PrimeVulFullGraphError("truncated paired development source")
            digest.update(left_raw)
            digest.update(right_raw)
            left = _decode_row(left_raw)
            right = _decode_row(right_raw)
            result.append((f"primevul:{left['idx']}", f"primevul:{right['idx']}"))
    if digest.hexdigest() != expected_sha256 or len(result) != expected_pairs:
        raise PrimeVulFullGraphError("paired source changed during graph replay")
    return tuple(result)


def run_primevul_full_graph(
    source_dir: Path,
    paired_dir: Path,
    *,
    source_expectation: PrimeVulDevelopmentExpectation = PRIMEVUL_ORIGINAL_DEVELOPMENT,
    pair_expectation: PrimeVulPairExpectation = PRIMEVUL_ORIGINAL_PAIRS,
    progress: Callable[[int, int, int], None] | None = None,
) -> dict[str, Any]:
    """Verify and replay the development graph; return no raw source text."""

    if source_expectation.train_rows + source_expectation.validation_rows > 250_000:
        raise PrimeVulFullGraphError("development source exceeds graph resource bound")
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
    root_by_id = graph.root_by_id
    valid_positive = {
        root_by_id[row.source_id] for row in graph.validation if row.target == 1
    }
    valid_negative = {
        root_by_id[row.source_id] for row in graph.validation if row.target == 0
    }
    pinned_original = (
        source_expectation == PRIMEVUL_ORIGINAL_DEVELOPMENT
        and pair_expectation == PRIMEVUL_ORIGINAL_PAIRS
    )
    return {
        "receipt_version": 1,
        "status": "development-graph-non-authorizing",
        "source_scope": "pinned-original-development" if pinned_original else "fixture",
        "training_authority": False,
        "held_out_data_present": False,
        "full_corpus_graph_executed": pinned_original,
        "pair_source_receipt_sha256": sha256_bytes(canonical_json_bytes(pair_receipt)),
        "pair_edge_ledger_sha256": sha256_bytes(canonical_json_bytes(edges)),
        "component_root_ledger_sha256": sha256_bytes(
            canonical_json_bytes(sorted(root_by_id.items()))
        ),
        "retained_train_id_ledger_sha256": sha256_bytes(
            canonical_json_bytes([row.source_id for row in graph.train])
        ),
        "retained_validation_id_ledger_sha256": sha256_bytes(
            canonical_json_bytes([row.source_id for row in graph.validation])
        ),
        "input_train_rows": len(train),
        "input_validation_rows": len(validation),
        "input_pair_edges": len(edges),
        "retained_train_rows": len(graph.train),
        "retained_validation_rows": len(graph.validation),
        "train_components": graph.train_components,
        "validation_components": graph.validation_components,
        "validation_components_positive": len(valid_positive),
        "validation_components_negative": len(valid_negative),
        "validation_removed_train_overlap": graph.validation_removed_train_overlap,
        "validation_removed_roots": graph.validation_removed_roots,
        "exact_joins": graph.exact_joins,
        "lsh_candidate_pairs": graph.lsh_candidate_pairs,
        "near_joins": graph.near_joins,
        "pair_joins": graph.pair_joins,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("development_data_dir", type=Path)
    parser.add_argument("paired_development_data_dir", type=Path)
    args = parser.parse_args()

    def report(processed: int, total: int, candidates: int) -> None:
        print(
            f"graph progress {processed}/{total} candidates={candidates}",
            file=sys.stderr,
            flush=True,
        )

    print("verifying pinned development sources", file=sys.stderr, flush=True)
    receipt = run_primevul_full_graph(
        args.development_data_dir,
        args.paired_development_data_dir,
        progress=report,
    )
    sys.stdout.buffer.write(canonical_json_bytes(receipt) + b"\n")


if __name__ == "__main__":
    main()
