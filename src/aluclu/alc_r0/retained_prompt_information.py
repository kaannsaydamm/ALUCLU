"""Non-authorizing prompt-information bound on graph-retained development rows.

The estimator concerns a deterministic classifier seeing only the complete
single-function prompt token IDs. It is not a macro-F1 bound or training result.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from collections.abc import Callable, Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .acquisition import verify_model_snapshot
from .banking_scoring import CandidateTokenizer
from .canonical import canonical_json_bytes, sha256_bytes
from .defect_prompt import DefectPromptError, prepare_defect_prompt
from .primevul_pair_clone_full import _read_pair_edges, _read_source_split
from .primevul_pair_clone_graph import PairCloneRecord
from .primevul_pair_clone_scalable import build_pair_clone_scalable
from .primevul_pairs_source import (
    PRIMEVUL_ORIGINAL_PAIRS,
    PrimeVulPairExpectation,
    verify_primevul_development_pairs,
)
from .primevul_source import (
    PRIMEVUL_ORIGINAL_DEVELOPMENT,
    PrimeVulDevelopmentExpectation,
)
from .retained_paired_prompt_contrast import _BUDGETS, _PINNED_GRAPH_LEDGERS
from .source_checkout import inspect_clean_source_checkout

_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_SOURCE_ID = re.compile(r"primevul:(?:0|[1-9][0-9]*)\Z")
_MAX_ROWS = 250_000


class RetainedPromptInformationError(ValueError):
    """The retained cohort or exact prompt-information audit is invalid."""


def audit_retained_prompt_information(
    rows: tuple[PairCloneRecord, ...],
    root_by_id: Mapping[str, str],
    tokenizer: CandidateTokenizer,
    *,
    max_tokens: int,
    progress: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    """Count identical-input conflicts with one vote per retained observation."""

    if not isinstance(rows, tuple) or not 0 < len(rows) <= _MAX_ROWS:
        raise RetainedPromptInformationError("bounded nonempty retained tuple required")
    if not isinstance(root_by_id, Mapping):
        raise RetainedPromptInformationError("component root mapping required")
    try:
        template = prepare_defect_prompt(tokenizer, max_tokens=max_tokens)
    except DefectPromptError as exc:
        raise RetainedPromptInformationError("invalid prompt template") from exc

    by_id: dict[str, PairCloneRecord] = {}
    for row in rows:
        if (
            not isinstance(row, PairCloneRecord)
            or not isinstance(row.source_id, str)
            or not _SOURCE_ID.fullmatch(row.source_id)
            or not isinstance(row.function, str)
            or not row.function.strip()
            or type(row.target) is not int
            or row.target not in (0, 1)
            or row.source_id in by_id
        ):
            raise RetainedPromptInformationError("invalid retained observation")
        root = root_by_id.get(row.source_id)
        if not isinstance(root, str) or not _SOURCE_ID.fullmatch(root):
            raise RetainedPromptInformationError("missing or invalid component root")
        by_id[row.source_id] = row

    labels = [0, 0]
    truncated = [0, 0]
    # A unique digest retains no prompt tokens. On a repeated digest, rebuild
    # its first prompt and compare every complete tuple, failing on SHA collision.
    classes: dict[bytes, list[int | str]] = {}
    repeated_prompts: dict[bytes, tuple[int, ...]] = {}
    repeated_roots: dict[bytes, set[str]] = {}
    ordered = hashlib.sha256()
    for index, row in enumerate(rows, start=1):
        try:
            prompt = template.build(row.function.encode("utf-8", errors="strict"))
        except (UnicodeEncodeError, DefectPromptError) as exc:
            raise RetainedPromptInformationError("invalid retained prompt") from exc
        root = root_by_id[row.source_id]
        ordered.update(
            canonical_json_bytes(
                [row.source_id, root, row.target, list(prompt.token_ids)]
            )
            + b"\n"
        )
        prompt_digest = hashlib.sha256(
            canonical_json_bytes(list(prompt.token_ids))
        ).digest()
        labels[row.target] += 1
        truncated[row.target] += (
            prompt.original_code_tokens > prompt.retained_code_tokens
        )
        entry = classes.get(prompt_digest)
        if entry is None:
            entry = [0, 0, row.source_id]
            classes[prompt_digest] = entry
        else:
            first_prompt = repeated_prompts.get(prompt_digest)
            if first_prompt is None:
                first = by_id[entry[2]]
                first_prompt = template.build(
                    first.function.encode("utf-8", errors="strict")
                ).token_ids
                if (
                    hashlib.sha256(canonical_json_bytes(list(first_prompt))).digest()
                    != prompt_digest
                ):
                    raise RetainedPromptInformationError(
                        "first prompt changed during collision verification"
                    )
                repeated_prompts[prompt_digest] = first_prompt
                repeated_roots[prompt_digest] = {root_by_id[first.source_id]}
            if prompt.token_ids != first_prompt:
                raise RetainedPromptInformationError("complete prompt digest collision")
            repeated_roots[prompt_digest].add(root)
        entry[row.target] += 1
        if progress is not None and (index % 10_000 == 0 or index == len(rows)):
            progress(index, len(rows))

    conflicts = [
        (digest, entry) for digest, entry in classes.items() if entry[0] and entry[1]
    ]
    affected = set().union(*(repeated_roots[digest] for digest, _ in conflicts))
    return {
        "status": "retained-development-prompt-information-non-authorizing",
        "training_authority": False,
        "held_out_data_present": False,
        "max_common_tokens": max_tokens,
        "retained_observations": len(rows),
        "labels": {"safe": labels[0], "vulnerable": labels[1]},
        "truncated": {"safe": truncated[0], "vulnerable": truncated[1]},
        "prompt_classes": len(classes),
        "opposite_label_prompt_classes": len(conflicts),
        "conflicted_observations": {
            "safe": sum(entry[0] for _, entry in conflicts),
            "vulnerable": sum(entry[1] for _, entry in conflicts),
        },
        "minimum_prompt_only_errors": sum(
            min(entry[0], entry[1]) for _, entry in conflicts
        ),
        "affected_components": len(affected),
        "ordered_prompt_records_sha256": ordered.hexdigest(),
    }


def run_retained_prompt_information(
    source_dir: Path,
    paired_dir: Path,
    tokenizer: CandidateTokenizer,
    *,
    model_inventory_sha256: str,
    budgets: tuple[int, ...] = _BUDGETS,
    source_expectation: PrimeVulDevelopmentExpectation = PRIMEVUL_ORIGINAL_DEVELOPMENT,
    pair_expectation: PrimeVulPairExpectation = PRIMEVUL_ORIGINAL_PAIRS,
    graph_progress: Callable[[int, int, int], None] | None = None,
    prompt_progress: Callable[[str, int, int, int], None] | None = None,
) -> dict[str, Any]:
    """Verify development bytes, rebuild pinned graph, then audit full cohorts."""

    pinned = (
        source_expectation == PRIMEVUL_ORIGINAL_DEVELOPMENT
        and pair_expectation == PRIMEVUL_ORIGINAL_PAIRS
    )
    if not isinstance(model_inventory_sha256, str) or not _HEX64.fullmatch(
        model_inventory_sha256
    ):
        raise RetainedPromptInformationError("invalid model inventory SHA-256")
    if (
        not isinstance(budgets, tuple)
        or not budgets
        or any(type(budget) is not int or budget not in _BUDGETS for budget in budgets)
        or len(set(budgets)) != len(budgets)
        or (pinned and budgets != _BUDGETS)
    ):
        raise RetainedPromptInformationError("budget grid changed or invalid")
    if source_expectation.train_rows + source_expectation.validation_rows > _MAX_ROWS:
        raise RetainedPromptInformationError("development source exceeds graph bound")

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
        train=train, validation=validation, pair_edges=edges, progress=graph_progress
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
        raise RetainedPromptInformationError("pinned graph ledgers changed")

    result: dict[str, Any] = {
        "receipt_version": 1,
        "status": "retained-development-prompt-information-non-authorizing",
        "source_scope": "pinned-original-development" if pinned else "fixture",
        "training_authority": False,
        "held_out_data_present": False,
        "pair_source_receipt_sha256": sha256_bytes(canonical_json_bytes(pair_receipt)),
        "model_inventory_sha256": model_inventory_sha256,
        "graph_ledgers": graph_ledgers,
        "retained_train_rows": len(graph.train),
        "retained_validation_rows": len(graph.validation),
    }
    for name, rows in (("train", graph.train), ("validation", graph.validation)):
        result[name] = []
        for budget in budgets:

            def report(processed: int, total: int) -> None:
                if prompt_progress is not None:
                    prompt_progress(name, budget, processed, total)

            result[name].append(
                audit_retained_prompt_information(
                    rows,
                    graph.root_by_id,
                    tokenizer,
                    max_tokens=budget,
                    progress=report,
                )
            )
    final_source_receipt = verify_primevul_development_pairs(
        source_dir,
        paired_dir,
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
    )
    if (
        sha256_bytes(canonical_json_bytes(final_source_receipt))
        != result["pair_source_receipt_sha256"]
    ):
        raise RetainedPromptInformationError("development source changed during run")
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

    def graph_progress(processed: int, total: int, candidates: int) -> None:
        print(
            f"graph progress {processed}/{total} candidates={candidates}",
            file=sys.stderr,
            flush=True,
        )

    def prompt_progress(split: str, budget: int, processed: int, total: int) -> None:
        print(
            f"prompt progress {split} {budget} {processed}/{total}",
            file=sys.stderr,
            flush=True,
        )

    receipt = run_retained_prompt_information(
        args.development_data_dir,
        args.paired_development_data_dir,
        tokenizer,
        model_inventory_sha256=snapshot["inventory_sha256"],
        graph_progress=graph_progress,
        prompt_progress=prompt_progress,
    )
    if (
        verify_model_snapshot(args.tokenizer_snapshot)["inventory_sha256"]
        != snapshot["inventory_sha256"]
    ):
        raise RetainedPromptInformationError("tokenizer snapshot changed during run")
    if inspect_clean_source_checkout(Path.cwd().resolve(strict=True)) != checkout:
        raise RetainedPromptInformationError("source checkout changed during run")
    receipt["source_checkout"] = asdict(checkout)
    receipt["invocation"] = {
        "module": "aluclu.alc_r0.retained_prompt_information",
        "source_dir": str(args.development_data_dir.resolve(strict=True)),
        "paired_dir": str(args.paired_development_data_dir.resolve(strict=True)),
        "tokenizer_snapshot": str(args.tokenizer_snapshot.resolve(strict=True)),
        "python_executable": str(Path(sys.executable).resolve(strict=True)),
        "python_version": sys.version.split()[0],
    }
    sys.stdout.buffer.write(canonical_json_bytes(receipt) + b"\n")


if __name__ == "__main__":
    main()
