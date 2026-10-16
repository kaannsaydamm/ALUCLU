"""Aggregate prospective resource coverage of retained development author pairs.

No dynamic program, edit distance, prompt outcome, model forward or training is
executed. Admission is a fixed-order simulation, never resolved edit evidence.
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

from .acquisition import SMOLLM2_135M, SnapshotExpectation, verify_model_snapshot
from .banking_scoring import CandidateTokenizer
from .canonical import canonical_json_bytes, sha256_bytes
from .defect_prompt import DefectPromptError, _ids, prepare_defect_prompt
from .devign_preprocess import DevignPreprocessError, normalize_devign_code
from .edit_token_visibility_reference import (
    MAX_ENDPOINT_TOKENS,
    EditVisibilityError,
    EditVisibilityLimits,
    _validate_limits,
    estimate_scratch_bytes,
)
from .primevul_pair_clone_full import _read_source_split
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
from .retained_paired_prompt_contrast import (
    _BUDGETS,
    _PINNED_GRAPH_LEDGERS,
    _read_pair_rows,
)
from .source_checkout import SourceCheckoutEvidence, inspect_clean_source_checkout

MAX_TOTAL_DP_CELLS = 100_000_000
_MAX_ROWS = 250_000
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_SOURCE_ID = re.compile(r"primevul:(?:0|[1-9][0-9]*)\Z")
_ENDPOINT_BINS = (512, 1024, 2048, 4096, 8192, 16384, 32768)
_CELL_BINS = (16384, 65536, 262144, 1048576, 4194304)
_REASONS = (
    "endpoint-token-limit",
    "dp-cell-limit",
    "scratch-byte-limit",
    "total-cell-budget-exhausted",
)
_PAIR = tuple[str, str, str, str]


class PairResourceCensusError(ValueError):
    """The cohort, fixed prospective policy, or source commitment is invalid."""


def _resource_policy(limits: EditVisibilityLimits, total_cell_cap: int) -> None:
    try:
        _validate_limits(limits)
    except EditVisibilityError as exc:
        raise PairResourceCensusError("invalid helper resource limits") from exc
    if type(total_cell_cap) is not int or not 0 < total_cell_cap <= MAX_TOTAL_DP_CELLS:
        raise PairResourceCensusError("total cell cap cannot relax production ceiling")


def pair_resource_cost(
    first_tokens: int,
    second_tokens: int,
    *,
    limits: EditVisibilityLimits = EditVisibilityLimits(),
) -> dict[str, Any]:
    """Preflight the full endpoints with the exact helper reason precedence."""

    _resource_policy(limits, MAX_TOTAL_DP_CELLS)
    if any(
        type(length) is not int or length <= 0
        for length in (first_tokens, second_tokens)
    ):
        raise PairResourceCensusError(
            "endpoint lengths must be exact positive integers"
        )
    cells = (first_tokens + 1) * (second_tokens + 1)
    scratch = (
        estimate_scratch_bytes(first_tokens, second_tokens, len(_BUDGETS))
        if max(first_tokens, second_tokens) <= MAX_ENDPOINT_TOKENS
        else None
    )
    reason = None
    if max(first_tokens, second_tokens) > limits.max_endpoint_tokens:
        reason = "endpoint-token-limit"
    elif cells > limits.max_dp_cells:
        reason = "dp-cell-limit"
    elif scratch is not None and scratch > limits.max_scratch_bytes:
        reason = "scratch-byte-limit"
    return {
        "first_tokens": first_tokens,
        "second_tokens": second_tokens,
        "dp_cells": cells,
        "estimated_scratch_bytes": scratch,
        "local_reason": reason,
    }


def _template_policy(
    tokenizer: CandidateTokenizer, limits: EditVisibilityLimits, total_cell_cap: int
) -> dict[str, Any]:
    templates = []
    try:
        for budget in _BUDGETS:
            template = prepare_defect_prompt(tokenizer, max_tokens=budget)
            templates.append(
                {
                    "max_common_tokens": budget,
                    "code_budget": template.code_budget,
                    "max_candidate_tokens": template.max_candidate_tokens,
                    **{
                        f"{field}_sha256": sha256_bytes(
                            canonical_json_bytes(list(getattr(template, field)))
                        )
                        for field in (
                            "prefix_ids",
                            "suffix_ids",
                            "safe_candidate_ids",
                            "vulnerable_candidate_ids",
                        )
                    },
                }
            )
    except (DefectPromptError, TypeError, AttributeError) as exc:
        raise PairResourceCensusError(
            "invalid frozen prompt template provenance"
        ) from exc
    # All budgets must share the same template and label-reserve commitments.
    commitments = [
        {
            key: value
            for key, value in row.items()
            if key not in {"max_common_tokens", "code_budget"}
        }
        for row in templates
    ]
    if any(row != commitments[0] for row in commitments[1:]):
        raise PairResourceCensusError("template commitments changed across budget grid")
    return {
        "version": 1,
        "operation": "prospective-admission-simulation-only",
        "order": "train-then-validation-author-file-order",
        "exhaustion": "permanent-at-first-locally-eligible-nonfitting-pair",
        "limits": asdict(limits),
        "total_cell_cap": total_cell_cap,
        "scratch_budget_count": len(_BUDGETS),
        "scratch_estimate_scope": "packed-helper-storage-excluding-inputs-and-process-rss",
        "template_budgets": templates,
        "endpoint_length_bin_upper_bounds": list(_ENDPOINT_BINS),
        "pair_cell_bin_upper_bounds": list(_CELL_BINS),
        "histogram_semantics": "disjoint-inclusive-upper-bounds-plus-overflow",
        "endpoint_counting_unit": "author-pair-endpoint-appearances",
        "component_counting_unit": "distinct-root-union-with-overlapping-strata",
        "local_reason_precedence": list(_REASONS[:-1]),
        "internal_record_encoding": "canonical-json-object-plus-LF-in-selected-pair-order",
    }


def _source_id(value: object) -> bool:
    return isinstance(value, str) and _SOURCE_ID.fullmatch(value) is not None


def _validate_cohort(
    splits: tuple[tuple[_PAIR, ...], tuple[_PAIR, ...]],
    retained: tuple[set[str], set[str]],
    roots: Mapping[str, str],
) -> None:
    if (
        any(not isinstance(rows, tuple) for rows in splits)
        or sum(map(len, splits)) > _MAX_ROWS
    ):
        raise PairResourceCensusError("bounded ordered author-pair tuples required")
    if any(
        not isinstance(ids, set) or any(not _source_id(value) for value in ids)
        for ids in retained
    ):
        raise PairResourceCensusError("retained source ID sets required")
    if retained[0] & retained[1]:
        raise PairResourceCensusError("retained splits overlap")
    if not isinstance(roots, Mapping):
        raise PairResourceCensusError("component root mapping required")
    seen_ids: dict[str, tuple[str, int, int]] = {}
    for split_index, rows in enumerate(splits):
        seen_pairs: set[tuple[str, str]] = set()
        for row in rows:
            if (
                not isinstance(row, tuple)
                or len(row) != 4
                or not all(_source_id(value) for value in row[:2])
                or row[0] == row[1]
                or any(
                    not isinstance(code, str) or not code.strip() for code in row[2:]
                )
            ):
                raise PairResourceCensusError("invalid ordered author pair")
            edge = row[:2]
            if edge in seen_pairs:
                raise PairResourceCensusError("duplicate author pair")
            seen_pairs.add(edge)
            root = roots.get(row[0])
            if not _source_id(root) or roots.get(row[1]) != root:
                raise PairResourceCensusError(
                    "missing or inconsistent pair component root"
                )
            for source_id, code, label in ((row[0], row[2], 1), (row[1], row[3], 0)):
                prior = seen_ids.setdefault(source_id, (code, label, split_index))
                if prior != (code, label, split_index):
                    raise PairResourceCensusError("inconsistent shared endpoint")
                try:
                    normalize_devign_code(code.encode("utf-8", errors="strict"))
                except (UnicodeEncodeError, DevignPreprocessError) as exc:
                    raise PairResourceCensusError(
                        "invalid author endpoint normalization"
                    ) from exc


def _histogram(bounds: tuple[int, ...]) -> dict[str, int]:
    return {f"le_{bound}": 0 for bound in bounds} | {"overflow": 0}


def _increment_histogram(
    histogram: dict[str, int], bounds: tuple[int, ...], value: int
) -> None:
    histogram[
        next((f"le_{bound}" for bound in bounds if value <= bound), "overflow")
    ] += 1


def _summary() -> dict[str, int]:
    return {"pairs": 0, "dp_cells_sum": 0, "dp_cells_max": 0}


def _add_cost(summary: dict[str, int], cells: int) -> None:
    summary["pairs"] += 1
    summary["dp_cells_sum"] += cells
    summary["dp_cells_max"] = max(summary["dp_cells_max"], cells)


def _full_code_ids(code: str, tokenizer: CandidateTokenizer) -> tuple[int, ...]:
    try:
        normalized = normalize_devign_code(code.encode("utf-8", errors="strict"))
        return _ids(tokenizer, normalized, field="code")
    except (
        UnicodeEncodeError,
        DevignPreprocessError,
        DefectPromptError,
        TypeError,
        AttributeError,
    ) as exc:
        raise PairResourceCensusError(
            "invalid full normalized endpoint tokenization"
        ) from exc


def audit_retained_pair_resource_census(
    train_pairs: tuple[_PAIR, ...],
    validation_pairs: tuple[_PAIR, ...],
    retained_train_ids: set[str],
    retained_validation_ids: set[str],
    root_by_id: Mapping[str, str],
    tokenizer: CandidateTokenizer,
    *,
    limits: EditVisibilityLimits = EditVisibilityLimits(),
    total_cell_cap: int = MAX_TOTAL_DP_CELLS,
    progress: Callable[[str, int, int], None] | None = None,
) -> dict[str, Any]:
    """Return aggregates only; fixtures may tighten but never relax resource caps."""

    _resource_policy(limits, total_cell_cap)
    splits = (train_pairs, validation_pairs)
    retained = (retained_train_ids, retained_validation_ids)
    _validate_cohort(splits, retained, root_by_id)
    # Own metadata snapshots so callbacks cannot alter the in-progress universe.
    retained = (retained_train_ids.copy(), retained_validation_ids.copy())
    roots = dict(root_by_id)
    policy = _template_policy(tokenizer, limits, total_cell_cap)
    result: dict[str, Any] = {
        "receipt_version": 1,
        "status": "retained-development-author-pair-resource-census-non-authorizing",
        "training_authority": False,
        "held_out_data_present": False,
        "policy": policy,
        "policy_sha256": sha256_bytes(canonical_json_bytes(policy)),
    }
    ordered = hashlib.sha256()
    admitted_cells, exhausted = 0, False
    for name, rows, ids in zip(("train", "validation"), splits, retained, strict=True):
        survival = {
            "author_pairs": len(rows),
            "both_retained": 0,
            "vulnerable_only_retained": 0,
            "safe_only_retained": 0,
            "neither_retained": 0,
        }
        selected = []
        for row in rows:
            left, right = row[0] in ids, row[1] in ids
            category = (
                "both_retained"
                if left and right
                else "vulnerable_only_retained"
                if left
                else "safe_only_retained"
                if right
                else "neither_retained"
            )
            survival[category] += 1
            if left and right:
                selected.append(row)
        summaries = {
            key: _summary()
            for key in ("universe", "locally_eligible", "admitted", "unresolved")
        }
        component_sets: dict[str, set[str]] = {key: set() for key in summaries}
        reasons = {key: 0 for key in _REASONS}
        reason_components: dict[str, set[str]] = {key: set() for key in _REASONS}
        reason_cells = {key: 0 for key in _REASONS}
        endpoint_histogram, cell_histogram = (
            _histogram(_ENDPOINT_BINS),
            _histogram(_CELL_BINS),
        )
        split_ordered = hashlib.sha256()
        endpoint_sum = endpoint_max = scratch_max = scratch_available = 0
        for index, row in enumerate(selected, start=1):
            first, second = (
                _full_code_ids(row[2], tokenizer),
                _full_code_ids(row[3], tokenizer),
            )
            cost = pair_resource_cost(len(first), len(second), limits=limits)
            cells, root = cost["dp_cells"], roots[row[0]]
            _add_cost(summaries["universe"], cells)
            component_sets["universe"].add(root)
            for length in (len(first), len(second)):
                endpoint_sum += length
                endpoint_max = max(endpoint_max, length)
                _increment_histogram(endpoint_histogram, _ENDPOINT_BINS, length)
            _increment_histogram(cell_histogram, _CELL_BINS, cells)
            scratch = cost["estimated_scratch_bytes"]
            if scratch is not None:
                scratch_available += 1
                scratch_max = max(scratch_max, scratch)
            reason = cost["local_reason"]
            if reason is None:
                _add_cost(summaries["locally_eligible"], cells)
                component_sets["locally_eligible"].add(root)
                if exhausted or cells > total_cell_cap - admitted_cells:
                    exhausted = True
                    reason = "total-cell-budget-exhausted"
                else:
                    admitted_cells += cells
            classification = "admitted" if reason is None else "unresolved"
            _add_cost(summaries[classification], cells)
            component_sets[classification].add(root)
            if reason is not None:
                reasons[reason] += 1
                reason_cells[reason] += cells
                reason_components[reason].add(root)
            record = {
                "split": name,
                "vulnerable_id": row[0],
                "safe_id": row[1],
                "component_root": root,
                "first_token_ids_sha256": sha256_bytes(
                    canonical_json_bytes(list(first))
                ),
                "second_token_ids_sha256": sha256_bytes(
                    canonical_json_bytes(list(second))
                ),
                **cost,
                "classification": classification,
                "reason": reason,
            }
            encoded = canonical_json_bytes(record) + b"\n"
            ordered.update(encoded)
            split_ordered.update(encoded)
            if progress is not None and (index % 500 == 0 or index == len(selected)):
                progress(name, index, len(selected))
        if not selected and progress is not None:
            progress(name, 0, 0)
        universe = len(selected)
        result[name] = {
            "survival": survival,
            **summaries,
            "unresolved_reasons": reasons,
            "unresolved_reason_dp_cells": reason_cells,
            "components": {
                **{key: len(value) for key, value in component_sets.items()},
                "unresolved_reasons": {
                    key: len(value) for key, value in reason_components.items()
                },
            },
            "eligible_fraction_of_universe": summaries["locally_eligible"]["pairs"]
            / universe
            if universe
            else None,
            "admitted_fraction_of_universe": summaries["admitted"]["pairs"] / universe
            if universe
            else None,
            "endpoint_tokens_sum": endpoint_sum,
            "endpoint_tokens_max": endpoint_max,
            "estimated_scratch_pairs": scratch_available,
            "estimated_scratch_bytes_max": scratch_max if scratch_available else None,
            "endpoint_length_histogram": endpoint_histogram,
            "pair_cell_histogram": cell_histogram,
            "ordered_internal_records_sha256": split_ordered.hexdigest(),
        }
    result["ordered_internal_records_sha256"] = ordered.hexdigest()
    result["admission"] = {
        "admitted_dp_cells": admitted_cells,
        "remaining_dp_cells": total_cell_cap - admitted_cells,
        "exhausted": exhausted,
    }
    return result


def run_retained_pair_resource_census(
    source_dir: Path,
    paired_dir: Path,
    tokenizer: CandidateTokenizer,
    *,
    model_inventory_sha256: str,
    source_expectation: PrimeVulDevelopmentExpectation = PRIMEVUL_ORIGINAL_DEVELOPMENT,
    pair_expectation: PrimeVulPairExpectation = PRIMEVUL_ORIGINAL_PAIRS,
    limits: EditVisibilityLimits = EditVisibilityLimits(),
    total_cell_cap: int = MAX_TOTAL_DP_CELLS,
    graph_progress: Callable[[int, int, int], None] | None = None,
    census_progress: Callable[[str, int, int], None] | None = None,
) -> dict[str, Any]:
    """Bind development bytes/graph; production policy is fixed before data access."""

    _resource_policy(limits, total_cell_cap)
    if not isinstance(
        source_expectation, PrimeVulDevelopmentExpectation
    ) or not isinstance(pair_expectation, PrimeVulPairExpectation):
        raise PairResourceCensusError("source and pair expectations required")
    pinned = (
        source_expectation == PRIMEVUL_ORIGINAL_DEVELOPMENT
        and pair_expectation == PRIMEVUL_ORIGINAL_PAIRS
    )
    if (source_expectation == PRIMEVUL_ORIGINAL_DEVELOPMENT) != (
        pair_expectation == PRIMEVUL_ORIGINAL_PAIRS
    ):
        raise PairResourceCensusError("pinned and fixture expectations cannot mix")
    if pinned and (
        limits != EditVisibilityLimits() or total_cell_cap != MAX_TOTAL_DP_CELLS
    ):
        raise PairResourceCensusError("pinned production resource policy changed")
    if not isinstance(model_inventory_sha256, str) or not _HEX64.fullmatch(
        model_inventory_sha256
    ):
        raise PairResourceCensusError("invalid model inventory SHA-256")
    if (
        source_expectation.train_rows + source_expectation.validation_rows > _MAX_ROWS
        or pair_expectation.train_pairs + pair_expectation.validation_pairs > _MAX_ROWS
    ):
        raise PairResourceCensusError("development inputs exceed graph/census bound")
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
    edges = tuple(row[:2] for row in train_pairs + validation_pairs)
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
        raise PairResourceCensusError("pinned graph ledgers changed")
    result = audit_retained_pair_resource_census(
        train_pairs,
        validation_pairs,
        {row.source_id for row in graph.train},
        {row.source_id for row in graph.validation},
        graph.root_by_id,
        tokenizer,
        limits=limits,
        total_cell_cap=total_cell_cap,
        progress=census_progress,
    )
    result.update(
        {
            "source_scope": "pinned-original-development" if pinned else "fixture",
            "source_expectation": asdict(source_expectation),
            "pair_expectation": asdict(pair_expectation),
            "pair_source_receipt_sha256": sha256_bytes(
                canonical_json_bytes(pair_receipt)
            ),
            "model_inventory_sha256": model_inventory_sha256,
            "graph_ledgers": graph_ledgers,
            "retained_train_rows": len(graph.train),
            "retained_validation_rows": len(graph.validation),
        }
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
        raise PairResourceCensusError("development source changed during run")
    return result


def verify_terminal_census_state(
    tokenizer_snapshot: Path,
    repo_root: Path,
    *,
    model_inventory_sha256: str,
    source_checkout: SourceCheckoutEvidence,
    snapshot_expectation: SnapshotExpectation = SMOLLM2_135M,
) -> None:
    """Recheck real model bytes and clean Git state; explicit fixture seam only."""

    if not isinstance(model_inventory_sha256, str) or not _HEX64.fullmatch(
        model_inventory_sha256
    ):
        raise PairResourceCensusError("invalid initial model inventory SHA-256")
    if not isinstance(source_checkout, SourceCheckoutEvidence):
        raise PairResourceCensusError("initial clean source checkout evidence required")
    if (
        verify_model_snapshot(tokenizer_snapshot, expectation=snapshot_expectation)[
            "inventory_sha256"
        ]
        != model_inventory_sha256
    ):
        raise PairResourceCensusError("tokenizer snapshot changed during run")
    if inspect_clean_source_checkout(repo_root) != source_checkout:
        raise PairResourceCensusError("source checkout changed during run")


def verify_census_module_origin(repo_root: Path, module_path: Path) -> None:
    """Require the executed source file to belong to the recorded checkout."""

    root = repo_root.resolve(strict=True)
    expected = root / "src" / "aluclu" / "alc_r0" / "retained_pair_resource_census.py"
    try:
        if (
            not expected.is_file()
            or expected.resolve(strict=True) != expected
            or module_path.resolve(strict=True) != expected
        ):
            raise PairResourceCensusError(
                "census module does not originate in source checkout"
            )
    except OSError as exc:
        raise PairResourceCensusError("census module origin unavailable") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("development_data_dir", type=Path)
    parser.add_argument("paired_development_data_dir", type=Path)
    parser.add_argument("tokenizer_snapshot", type=Path)
    args = parser.parse_args()
    root = Path.cwd().resolve(strict=True)
    verify_census_module_origin(root, Path(__file__))
    checkout = inspect_clean_source_checkout(root)
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

    def census_progress(split: str, processed: int, total: int) -> None:
        print(
            f"resource census progress {split} {processed}/{total}",
            file=sys.stderr,
            flush=True,
        )

    receipt = run_retained_pair_resource_census(
        args.development_data_dir,
        args.paired_development_data_dir,
        tokenizer,
        model_inventory_sha256=snapshot["inventory_sha256"],
        graph_progress=graph_progress,
        census_progress=census_progress,
    )
    verify_terminal_census_state(
        args.tokenizer_snapshot,
        root,
        model_inventory_sha256=snapshot["inventory_sha256"],
        source_checkout=checkout,
    )
    verify_census_module_origin(root, Path(__file__))
    receipt["source_checkout"] = asdict(checkout)
    receipt["model_repository"] = snapshot["repository"]
    receipt["model_revision"] = snapshot["revision"]
    receipt["model_snapshot_receipt_sha256"] = sha256_bytes(
        canonical_json_bytes(snapshot)
    )
    receipt["invocation"] = {
        "module": "aluclu.alc_r0.retained_pair_resource_census",
        "source_dir": str(args.development_data_dir.resolve(strict=True)),
        "paired_dir": str(args.paired_development_data_dir.resolve(strict=True)),
        "tokenizer_snapshot": str(args.tokenizer_snapshot.resolve(strict=True)),
        "python_executable": str(Path(sys.executable).resolve(strict=True)),
        "python_version": sys.version.split()[0],
    }
    sys.stdout.buffer.write(canonical_json_bytes(receipt) + b"\n")


if __name__ == "__main__":
    main()
