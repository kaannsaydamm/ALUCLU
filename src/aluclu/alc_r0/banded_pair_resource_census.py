"""Prospective full-token band geometry only; no edit DP or native execution."""

from __future__ import annotations

import argparse
import hashlib
import platform
import re
import sys
from array import array
from dataclasses import asdict
from pathlib import Path

from .acquisition import verify_model_snapshot
from .banded_edit_token_visibility_reference import (
    BandedEditVisibilityError,
    BandedEditVisibilityLimits,
    _validate,
)
from .canonical import canonical_json_bytes, sha256_bytes
from .edit_token_visibility_reference import EditVisibilityLimits
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
from .retained_pair_resource_census import (
    MAX_TOTAL_DP_CELLS,
    PairResourceCensusError,
    _full_code_ids,
    _histogram,
    _increment_histogram,
    _template_policy,
    _validate_cohort,
    verify_terminal_census_state,
)
from .retained_paired_prompt_contrast import _PINNED_GRAPH_LEDGERS, _read_pair_rows
from .source_checkout import inspect_clean_source_checkout

_ENDPOINT_BINS = (512, 1024, 2048, 4096, 8192, 16384, 32768)
_CELL_BINS = (16384, 65536, 262144, 1048576, 4194304)
_REASONS = (
    "endpoint-token-limit",
    "distance-threshold-exceeded",
    "band-cell-limit",
    "scratch-byte-limit",
    "total-cell-budget-exhausted",
)
_STRATA = (
    "universe",
    "preflight_eligible",
    "prospective_admitted",
    "prospectively_unresolved",
)
_DEPENDENCIES = {
    "src/aluclu/alc_r0/retained_pair_resource_census.py": "31c6bea82c5599f397e75351bb6cd845d6075f5fd960fdff7a5a587951308df5",
    "src/aluclu/alc_r0/banded_edit_token_visibility_reference.py": "dff2a30af16daa97dd0acd1ab39fe89403b35b6a4b181c95f7bf5db21f707f8d",
}


def _policy(limits, distance_threshold, total_cell_cap):
    try:
        # Validation only, never invokes the reference dynamic program.
        _validate((), (), (1, 2, 3, 4, 5), distance_threshold, limits)
    except BandedEditVisibilityError as exc:
        raise PairResourceCensusError("invalid band geometry resource policy") from exc
    if type(total_cell_cap) is not int or not 0 < total_cell_cap <= MAX_TOTAL_DP_CELLS:
        raise PairResourceCensusError("total prospective cap cannot relax ceiling")


def _headers():
    words, flags = array("I"), array("B")
    if words.itemsize != 4 or flags.itemsize != 1:
        raise PairResourceCensusError("uint32/byte geometry storage metadata required")
    return {
        "uint32_array_header_bytes": sys.getsizeof(words),
        "byte_array_header_bytes": sys.getsizeof(flags),
    }


def banded_pair_resource_cost(
    first_tokens,
    second_tokens,
    *,
    limits=BandedEditVisibilityLimits(),
    distance_threshold=512,
):
    """Hypothetical preflight geometry; eligibility is not resolved distance."""
    _policy(limits, distance_threshold, MAX_TOTAL_DP_CELLS)
    if any(type(n) is not int or n <= 0 for n in (first_tokens, second_tokens)):
        raise PairResourceCensusError(
            "endpoint lengths must be exact positive integers"
        )
    n, m, K = first_tokens, second_tokens, distance_threshold
    lower = upper = cells = width = payload = scratch = None
    if max(n, m) > limits.max_endpoint_tokens:
        reason = "endpoint-token-limit"
    elif abs(n - m) > K:
        cells = width = payload = 0
        reason = "distance-threshold-exceeded"
    else:
        delta = n - m
        lower, upper = -((K - delta) // 2), (delta + K) // 2
        cells = width = 0
        for i in range(n + 1):
            row_width = max(0, min(m, i - lower) - max(0, i - upper) + 1)
            cells += row_width
            width = max(width, row_width)
        headers = _headers()
        payload = 2 * 36 * 4 * width + 5 * (n + m)
        scratch = (
            payload
            + 72 * headers["uint32_array_header_bytes"]
            + 10 * headers["byte_array_header_bytes"]
            + 65536
        )
        reason = (
            "band-cell-limit"
            if cells > limits.max_band_cells
            else "scratch-byte-limit"
            if scratch > limits.max_scratch_bytes
            else None
        )
    return {
        "first_tokens": n,
        "second_tokens": m,
        "distance_threshold": K,
        "band_lower_diagonal": lower,
        "band_upper_diagonal": upper,
        "scheduled_band_cells": cells,
        "max_row_width": width,
        "planned_packed_payload_bytes": payload,
        "estimated_scratch_bytes": scratch,
        "local_reason": reason,
    }


def _summary():
    return {
        "pairs": 0,
        "known_geometry_pairs": 0,
        "unknown_geometry_pairs": 0,
        "known_band_cells_sum": 0,
        "known_band_cells_max": 0,
    }


def _add(summary, cells):
    summary["pairs"] += 1
    if cells is None:
        summary["unknown_geometry_pairs"] += 1
    else:
        summary["known_geometry_pairs"] += 1
        summary["known_band_cells_sum"] += cells
        summary["known_band_cells_max"] = max(summary["known_band_cells_max"], cells)


def audit_banded_pair_resource_census(
    train_pairs,
    validation_pairs,
    retained_train_ids,
    retained_validation_ids,
    root_by_id,
    tokenizer,
    *,
    limits=BandedEditVisibilityLimits(),
    distance_threshold=512,
    total_cell_cap=MAX_TOTAL_DP_CELLS,
    progress=None,
):
    """Aggregate all retained author pairs; no pair-level output or edit DP."""
    _policy(limits, distance_threshold, total_cell_cap)
    splits = (train_pairs, validation_pairs)
    _validate_cohort(splits, (retained_train_ids, retained_validation_ids), root_by_id)
    retained = (retained_train_ids.copy(), retained_validation_ids.copy())
    roots = dict(root_by_id)
    # Reuse only frozen template commitments, not rectangular admission semantics.
    templates = _template_policy(tokenizer, EditVisibilityLimits(), MAX_TOTAL_DP_CELLS)[
        "template_budgets"
    ]
    policy = {
        "version": 1,
        "operation": "banded-geometry-prospective-admission-only",
        "order": "train-then-validation-author-file-order",
        "exhaustion": "permanent-at-first-locally-eligible-nonfitting-pair",
        "limits": asdict(limits),
        "distance_threshold": distance_threshold,
        "total_cell_cap": total_cell_cap,
        "scratch_budget_count": 5,
        "template_budgets": templates,
        "geometry_headers": _headers(),
        "scratch_estimate_scope": "hypothetical-helper-storage-excluding-inputs-and-process-rss",
        "endpoint_length_bin_upper_bounds": list(_ENDPOINT_BINS),
        "band_cell_bin_upper_bounds": list(_CELL_BINS),
        "histogram_semantics": "disjoint-inclusive-upper-bounds-plus-overflow-and-unknown",
        "local_reason_precedence": list(_REASONS[:-1]),
        "component_counting_unit": "distinct-root-union-with-overlapping-strata",
        "endpoint_counting_unit": "author-pair-endpoint-appearances",
        "internal_record_encoding": "canonical-json-object-plus-LF-in-selected-pair-order",
    }
    policy_hash = sha256_bytes(canonical_json_bytes(policy))
    result = {
        "receipt_version": 1,
        "status": "retained-development-banded-geometry-census-non-authorizing",
        "training_authority": False,
        "held_out_data_present": False,
        "policy": policy,
        "policy_sha256": policy_hash,
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
        summaries = {key: _summary() for key in _STRATA}
        components = {key: set() for key in _STRATA}
        reasons = {key: 0 for key in _REASONS}
        reason_components = {key: set() for key in _REASONS}
        reason_costs = {key: _summary() for key in _REASONS}
        endpoint_histogram = _histogram(_ENDPOINT_BINS)
        cell_histogram = _histogram(_CELL_BINS) | {"unknown": 0}
        split_ordered = hashlib.sha256()
        endpoint_sum = endpoint_max = scratch_max = scratch_pairs = 0
        for index, row in enumerate(selected, start=1):
            first, second = (
                _full_code_ids(row[2], tokenizer),
                _full_code_ids(row[3], tokenizer),
            )
            cost = banded_pair_resource_cost(
                len(first),
                len(second),
                limits=limits,
                distance_threshold=distance_threshold,
            )
            cells, root = cost["scheduled_band_cells"], roots[row[0]]
            _add(summaries["universe"], cells)
            components["universe"].add(root)
            for length in (len(first), len(second)):
                endpoint_sum += length
                endpoint_max = max(endpoint_max, length)
                _increment_histogram(endpoint_histogram, _ENDPOINT_BINS, length)
            if cells is None:
                cell_histogram["unknown"] += 1
            else:
                _increment_histogram(cell_histogram, _CELL_BINS, cells)
            scratch = cost["estimated_scratch_bytes"]
            if scratch is not None:
                scratch_pairs += 1
                scratch_max = max(scratch_max, scratch)
            reason = cost["local_reason"]
            if reason is None:
                _add(summaries["preflight_eligible"], cells)
                components["preflight_eligible"].add(root)
                if exhausted or cells > total_cell_cap - admitted_cells:
                    exhausted, reason = True, "total-cell-budget-exhausted"
                else:
                    admitted_cells += cells
            classification = (
                "prospective_admitted" if reason is None else "prospectively_unresolved"
            )
            _add(summaries[classification], cells)
            components[classification].add(root)
            if reason is not None:
                reasons[reason] += 1
                _add(reason_costs[reason], cells)
                reason_components[reason].add(root)
            record = {
                "split": name,
                "vulnerable_id": row[0],
                "safe_id": row[1],
                "component_root": root,
                "policy_sha256": policy_hash,
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
            "unresolved_reason_geometry": reason_costs,
            "components": {
                **{key: len(value) for key, value in components.items()},
                "unresolved_reasons": {
                    key: len(value) for key, value in reason_components.items()
                },
            },
            "eligible_fraction_of_universe": summaries["preflight_eligible"]["pairs"]
            / universe
            if universe
            else None,
            "admitted_fraction_of_universe": summaries["prospective_admitted"]["pairs"]
            / universe
            if universe
            else None,
            "endpoint_tokens_sum": endpoint_sum,
            "endpoint_tokens_max": endpoint_max,
            "estimated_scratch_pairs": scratch_pairs,
            "estimated_scratch_bytes_max": scratch_max if scratch_pairs else None,
            "endpoint_length_histogram": endpoint_histogram,
            "pair_band_cell_histogram": cell_histogram,
            "ordered_internal_records_sha256": split_ordered.hexdigest(),
        }
    result["ordered_internal_records_sha256"] = ordered.hexdigest()
    result["admission"] = {
        "admitted_band_cells": admitted_cells,
        "remaining_band_cells": total_cell_cap - admitted_cells,
        "exhausted": exhausted,
    }
    return result


def verify_banded_census_module_origin(repo_root, module_path):
    root = Path(repo_root).resolve(strict=True)
    expected = root / "src/aluclu/alc_r0/banded_pair_resource_census.py"
    try:
        if (
            not expected.is_file()
            or expected.resolve(strict=True) != expected
            or Path(module_path).resolve(strict=True) != expected
        ):
            raise PairResourceCensusError("band census module origin mismatch")
    except OSError as exc:
        raise PairResourceCensusError("band census module origin unavailable") from exc


def verify_geometry_dependencies(repo_root):
    for relative, digest in _DEPENDENCIES.items():
        path = Path(repo_root) / relative
        try:
            if (
                path.resolve(strict=True) != path
                or sha256_bytes(path.read_bytes()) != digest
            ):
                raise PairResourceCensusError("frozen geometry dependency changed")
        except OSError as exc:
            raise PairResourceCensusError(
                "frozen geometry dependency unavailable"
            ) from exc


def run_banded_pair_resource_census(
    source_dir,
    paired_dir,
    tokenizer,
    *,
    model_inventory_sha256,
    source_expectation=PRIMEVUL_ORIGINAL_DEVELOPMENT,
    pair_expectation=PRIMEVUL_ORIGINAL_PAIRS,
    limits=BandedEditVisibilityLimits(),
    distance_threshold=512,
    total_cell_cap=MAX_TOTAL_DP_CELLS,
    graph_progress=None,
    census_progress=None,
):
    """Verified development readers; synthetic expectations are fixture-only."""
    _policy(limits, distance_threshold, total_cell_cap)
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
        limits != BandedEditVisibilityLimits()
        or distance_threshold != 512
        or total_cell_cap != MAX_TOTAL_DP_CELLS
    ):
        raise PairResourceCensusError("pinned production band geometry policy changed")
    if not isinstance(model_inventory_sha256, str) or not re.fullmatch(
        r"[0-9a-f]{64}", model_inventory_sha256
    ):
        raise PairResourceCensusError("invalid model inventory SHA-256")
    if (
        source_expectation.train_rows + source_expectation.validation_rows > 250000
        or pair_expectation.train_pairs + pair_expectation.validation_pairs > 250000
    ):
        raise PairResourceCensusError("development inputs exceed graph/census bound")
    root = Path(__file__).resolve().parents[3]
    if pinned:
        verify_geometry_dependencies(root)
    source_dir, paired_dir = Path(source_dir), Path(paired_dir)
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
    ledgers = {
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
    if pinned and ledgers != _PINNED_GRAPH_LEDGERS:
        raise PairResourceCensusError("pinned graph ledgers changed")
    result = audit_banded_pair_resource_census(
        train_pairs,
        validation_pairs,
        {row.source_id for row in graph.train},
        {row.source_id for row in graph.validation},
        graph.root_by_id,
        tokenizer,
        limits=limits,
        distance_threshold=distance_threshold,
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
            "graph_ledgers": ledgers,
            "retained_train_rows": len(graph.train),
            "retained_validation_rows": len(graph.validation),
        }
    )
    final_receipt = verify_primevul_development_pairs(
        source_dir,
        paired_dir,
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
    )
    if (
        sha256_bytes(canonical_json_bytes(final_receipt))
        != result["pair_source_receipt_sha256"]
    ):
        raise PairResourceCensusError("development source changed during census")
    if pinned:
        verify_geometry_dependencies(root)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("development_data_dir", type=Path)
    parser.add_argument("paired_development_data_dir", type=Path)
    parser.add_argument("tokenizer_snapshot", type=Path)
    args = parser.parse_args()
    root = Path.cwd().resolve(strict=True)
    verify_banded_census_module_origin(root, Path(__file__))
    verify_geometry_dependencies(root)
    checkout = inspect_clean_source_checkout(root)
    snapshot = verify_model_snapshot(args.tokenizer_snapshot)
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        str(args.tokenizer_snapshot), local_files_only=True, trust_remote_code=False
    )

    def graph_progress(processed, total, candidates):
        print(
            f"graph progress {processed}/{total} candidates={candidates}",
            file=sys.stderr,
            flush=True,
        )

    def census_progress(split, processed, total):
        print(
            f"band geometry census progress {split} {processed}/{total}",
            file=sys.stderr,
            flush=True,
        )

    result = run_banded_pair_resource_census(
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
    verify_banded_census_module_origin(root, Path(__file__))
    verify_geometry_dependencies(root)
    result.update(
        {
            "source_checkout": asdict(checkout),
            "model_repository": snapshot["repository"],
            "model_revision": snapshot["revision"],
            "model_snapshot_receipt_sha256": sha256_bytes(
                canonical_json_bytes(snapshot)
            ),
            "dependency_source_hashes": dict(_DEPENDENCIES),
            "invocation": {
                "module": "aluclu.alc_r0.banded_pair_resource_census",
                "source_dir": str(args.development_data_dir.resolve(strict=True)),
                "paired_dir": str(
                    args.paired_development_data_dir.resolve(strict=True)
                ),
                "tokenizer_snapshot": str(args.tokenizer_snapshot.resolve(strict=True)),
                "python_executable": str(Path(sys.executable).resolve(strict=True)),
                "python_version": sys.version,
                "platform": platform.platform(),
            },
        }
    )
    sys.stdout.buffer.write(canonical_json_bytes(result) + b"\n")


if __name__ == "__main__":
    main()
