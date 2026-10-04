"""Development-only prompt contrast among author pairs surviving graph cleanup.

This conditional diagnostic neither authorizes training nor inspects held-out data.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import stat
import sys
from collections.abc import Callable, Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .acquisition import verify_model_snapshot
from .banking_scoring import CandidateTokenizer
from .canonical import canonical_json_bytes, sha256_bytes
from .paired_prompt_contrast import audit_paired_prompt_contrast
from .primevul_pair_clone_full import _read_pair_edges, _read_source_split
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
from .source_checkout import inspect_clean_source_checkout

_BUDGETS = (512, 1024, 2048, 4096, 8192)
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_PINNED_GRAPH_LEDGERS = {
    "pair_edge_ledger_sha256": "4ed968d05b79bcb826f5d4e6756df0cac9b4f5a53d392c31e4b3e0291a87fe9a",
    "component_root_ledger_sha256": "7a39cd3ce27002838ae3aef73a8caa7902651401b272b76ead3fb636bd239059",
    "retained_train_id_ledger_sha256": "4589f0acfcc69edf743733ef7ebb069c987c9b30ccd30c72b5827e0dd5388d61",
    "retained_validation_id_ledger_sha256": "0d3db4ae9bba39c231c14129662181feb367f113feaa7b01400580529b297c4c",
}


class RetainedPairedPromptError(ValueError):
    """The pinned cohort or survivor-pair diagnostic changed unexpectedly."""


def classify_retained_pairs(
    pairs: Sequence[tuple[str, str, str, str]], retained_ids: set[str]
) -> tuple[dict[str, int], tuple[tuple[str, str], ...]]:
    """Partition ordered author pairs; return only both-retained function pairs."""

    if not isinstance(retained_ids, set) or not isinstance(pairs, (tuple, list)):
        raise RetainedPairedPromptError("invalid survivor classification input")
    counts = {
        "author_pairs": len(pairs),
        "both_retained": 0,
        "vulnerable_only_retained": 0,
        "safe_only_retained": 0,
        "neither_retained": 0,
    }
    survivors: list[tuple[str, str]] = []
    for pair in pairs:
        if not isinstance(pair, tuple) or len(pair) != 4:
            raise RetainedPairedPromptError("invalid ordered source pair")
        vulnerable_id, safe_id, vulnerable_code, safe_code = pair
        if any(not isinstance(value, str) or not value for value in pair):
            raise RetainedPairedPromptError("invalid ordered source pair")
        vulnerable_in = vulnerable_id in retained_ids
        safe_in = safe_id in retained_ids
        if vulnerable_in and safe_in:
            counts["both_retained"] += 1
            survivors.append((vulnerable_code, safe_code))
        elif vulnerable_in:
            counts["vulnerable_only_retained"] += 1
        elif safe_in:
            counts["safe_only_retained"] += 1
        else:
            counts["neither_retained"] += 1
    if sum(value for key, value in counts.items() if key != "author_pairs") != len(
        pairs
    ):
        raise RetainedPairedPromptError("non-exhaustive pair partition")
    return counts, tuple(survivors)


def _read_pair_rows(
    path: Path, *, expected_sha256: str, expected_pairs: int
) -> tuple[tuple[str, str, str, str], ...]:
    if path.is_symlink() or not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
        raise RetainedPairedPromptError("paired development file is not regular")
    digest = hashlib.sha256()
    rows: list[tuple[str, str, str, str]] = []
    with path.open("rb") as stream:
        for left_raw in stream:
            right_raw = stream.readline()
            if not right_raw:
                raise RetainedPairedPromptError("truncated paired source")
            digest.update(left_raw)
            digest.update(right_raw)
            left, right = _decode_row(left_raw), _decode_row(right_raw)
            if left["target"] != 1 or right["target"] != 0:
                raise RetainedPairedPromptError("pair labels must be ordered 1,0")
            rows.append(
                (
                    f"primevul:{left['idx']}",
                    f"primevul:{right['idx']}",
                    left["func"],
                    right["func"],
                )
            )
    if digest.hexdigest() != expected_sha256 or len(rows) != expected_pairs:
        raise RetainedPairedPromptError("paired development file changed during read")
    return tuple(rows)


def _audit_survivors(
    pairs: tuple[tuple[str, str], ...],
    tokenizer: CandidateTokenizer,
    budget: int,
) -> dict[str, Any]:
    if pairs:
        return audit_paired_prompt_contrast(pairs, tokenizer, max_tokens=budget)
    return {
        "status": "development-pair-prompt-contrast-non-authorizing",
        "training_authority": False,
        "held_out_data_present": False,
        "pairs": 0,
        "collapsed_pairs": 0,
        "both_truncated_pairs": 0,
        "one_truncated_pairs": 0,
        "neither_truncated_pairs": 0,
        "ordered_pair_prompt_ids_sha256": hashlib.sha256(b"").hexdigest(),
    }


def run_retained_paired_prompt_contrast(
    source_dir: Path,
    paired_dir: Path,
    tokenizer: CandidateTokenizer,
    *,
    model_inventory_sha256: str,
    budgets: tuple[int, ...] = _BUDGETS,
    source_expectation: PrimeVulDevelopmentExpectation = PRIMEVUL_ORIGINAL_DEVELOPMENT,
    pair_expectation: PrimeVulPairExpectation = PRIMEVUL_ORIGINAL_PAIRS,
    progress: Callable[[int, int, int], None] | None = None,
) -> dict[str, Any]:
    """Rebuild graph, bind ledgers, then audit only both-retained author pairs."""

    pinned = (
        source_expectation == PRIMEVUL_ORIGINAL_DEVELOPMENT
        and pair_expectation == PRIMEVUL_ORIGINAL_PAIRS
    )
    if not isinstance(model_inventory_sha256, str) or not _HEX64.fullmatch(
        model_inventory_sha256
    ):
        raise RetainedPairedPromptError("invalid model inventory SHA-256")
    if (
        not isinstance(budgets, tuple)
        or any(type(budget) is not int or budget not in _BUDGETS for budget in budgets)
        or not budgets
        or (pinned and budgets != _BUDGETS)
    ):
        raise RetainedPairedPromptError("budget grid changed or invalid")
    if source_expectation.train_rows + source_expectation.validation_rows > 250_000:
        raise RetainedPairedPromptError("development source exceeds graph bound")
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
    train_pairs = _read_pair_rows(
        paired_dir / "primevul_train_paired.jsonl",
        expected_sha256=pair_expectation.train_sha256,
        expected_pairs=pair_expectation.train_pairs,
    )
    validation_pairs = _read_pair_rows(
        paired_dir / "primevul_valid_paired.jsonl",
        expected_sha256=pair_expectation.validation_sha256,
        expected_pairs=pair_expectation.validation_pairs,
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
    if edges != tuple((row[0], row[1]) for row in train_pairs + validation_pairs):
        raise RetainedPairedPromptError("pair rows and graph edges disagree")
    graph = build_pair_clone_scalable(
        train=train, validation=validation, pair_edges=edges, progress=progress
    )
    graph_ledgers = {
        "pair_edge_ledger_sha256": sha256_bytes(canonical_json_bytes(edges)),
        "component_root_ledger_sha256": sha256_bytes(
            canonical_json_bytes(sorted(graph.root_by_id.items()))
        ),
        "retained_train_id_ledger_sha256": sha256_bytes(
            canonical_json_bytes([row.source_id for row in graph.train])
        ),
        "retained_validation_id_ledger_sha256": sha256_bytes(
            canonical_json_bytes([row.source_id for row in graph.validation])
        ),
    }
    if pinned and graph_ledgers != _PINNED_GRAPH_LEDGERS:
        raise RetainedPairedPromptError("pinned graph ledgers changed")

    result: dict[str, Any] = {
        "receipt_version": 1,
        "status": "retained-development-author-pair-prompt-contrast-non-authorizing",
        "source_scope": "pinned-original-development" if pinned else "fixture",
        "training_authority": False,
        "held_out_data_present": False,
        "pair_source_receipt_sha256": sha256_bytes(canonical_json_bytes(pair_receipt)),
        "model_inventory_sha256": model_inventory_sha256,
        "graph_ledgers": graph_ledgers,
        "retained_train_rows": len(graph.train),
        "retained_validation_rows": len(graph.validation),
    }
    for name, paired_rows, retained_rows in (
        ("train", train_pairs, graph.train),
        ("validation", validation_pairs, graph.validation),
    ):
        partition, survivors = classify_retained_pairs(
            paired_rows, {row.source_id for row in retained_rows}
        )
        result[name] = {
            "survival": partition,
            "budgets": [
                {
                    "max_common_tokens": budget,
                    **_audit_survivors(survivors, tokenizer, budget),
                }
                for budget in budgets
            ],
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("development_data_dir", type=Path)
    parser.add_argument("paired_development_data_dir", type=Path)
    parser.add_argument("tokenizer_snapshot", type=Path)
    args = parser.parse_args()
    checkout = inspect_clean_source_checkout(Path.cwd().resolve(strict=True))
    snapshot = verify_model_snapshot(args.tokenizer_snapshot)
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        str(args.tokenizer_snapshot), local_files_only=True, trust_remote_code=False
    )

    def report(processed: int, total: int, candidates: int) -> None:
        print(
            f"graph progress {processed}/{total} candidates={candidates}",
            file=sys.stderr,
            flush=True,
        )

    receipt = run_retained_paired_prompt_contrast(
        args.development_data_dir,
        args.paired_development_data_dir,
        tokenizer,
        model_inventory_sha256=snapshot["inventory_sha256"],
        progress=report,
    )
    if (
        verify_model_snapshot(args.tokenizer_snapshot)["inventory_sha256"]
        != snapshot["inventory_sha256"]
    ):
        raise RetainedPairedPromptError("tokenizer snapshot changed during run")
    if inspect_clean_source_checkout(Path.cwd().resolve(strict=True)) != checkout:
        raise RetainedPairedPromptError("source checkout changed during run")
    receipt["source_checkout"] = asdict(checkout)
    receipt["invocation"] = {
        "module": "aluclu.alc_r0.retained_paired_prompt_contrast",
        "source_dir": str(args.development_data_dir.resolve(strict=True)),
        "paired_dir": str(args.paired_development_data_dir.resolve(strict=True)),
        "tokenizer_snapshot": str(args.tokenizer_snapshot.resolve(strict=True)),
        "python_executable": str(Path(sys.executable).resolve(strict=True)),
        "python_version": sys.version.split()[0],
    }
    sys.stdout.buffer.write(canonical_json_bytes(receipt) + b"\n")


if __name__ == "__main__":
    main()
