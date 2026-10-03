"""Development-only exposure with explicit pinned paths; no import-time native load.

The fixture core is not a production execution entry point. A separately
reviewed pinned-source CLI is required before any real development execution.
"""

import argparse
import hashlib
import json
import platform
import re
import sys
from dataclasses import asdict
from pathlib import Path

from .acquisition import verify_model_snapshot
from .banded_edit_token_visibility_reference import (
    BandedEditVisibilityLimits,
    BandedEditVisibilityResult,
    _validate,
)
from .banded_pair_resource_census import (
    _add,
    _summary,
    audit_banded_pair_resource_census,
    banded_pair_resource_cost,
    verify_geometry_dependencies,
)
from .canonical import canonical_json_bytes, sha256_bytes
from .edit_token_visibility_reference import BudgetExposure
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
from .retained_pair_resource_census import _full_code_ids, verify_terminal_census_state
from .retained_paired_prompt_contrast import _PINNED_GRAPH_LEDGERS, _read_pair_rows
from .source_checkout import inspect_clean_source_checkout

MAX_EXPOSURE_CELLS = 3_000_000_000
GEOMETRY_RECEIPT_SHA256 = (
    "6ffd5f601d2aef5df092307b24dc21a7aefc12b211e849fadd4042d87e28adc7"
)
NATIVE_RECEIPT_SHA256 = (
    "ec5463427664884af4c2315031733fe3eb9a496abc84322b5fefba46db4e8d61"
)
NATIVE_DLL_SHA256 = "d8d680420698a30d863748943d5b000d38facafc56b7081eb1dbfe004af0161a"
_FIELDS = (
    "first_min",
    "first_max",
    "second_min",
    "second_max",
    "total_min",
    "total_max",
)
_STRATA = (
    "universe",
    "locally_eligible",
    "dp_attempted",
    "exact_zero_distance",
    "exact_positive_distance",
    "preflight_unresolved",
    "global_cap_unresolved",
    "terminal_threshold_unresolved",
)
_REASONS = (
    "endpoint-token-limit",
    "distance-threshold-exceeded",
    "band-cell-limit",
    "scratch-byte-limit",
)


class EditExposureError(ValueError):
    """Invalid cohort, commitment, policy or completed backend result."""


def _require(condition, message="invalid completed backend result"):
    if not condition:
        raise EditExposureError(message)


def validate_completed_result(result, first, second, budgets, threshold, limits):
    """Fail-closed validation, not an independent proof of corpus DP outputs."""
    _require(type(result) is BandedEditVisibilityResult)
    _require(
        result.training_authority is False and result.held_out_data_present is False
    )
    _require(type(result.requested_code_budgets) is tuple)
    cost = banded_pair_resource_cost(
        len(first), len(second), limits=limits, distance_threshold=threshold
    )
    _require(cost["local_reason"] is None)
    expected = {
        key: cost[key]
        for key in (
            "first_tokens",
            "second_tokens",
            "distance_threshold",
            "band_lower_diagonal",
            "band_upper_diagonal",
            "scheduled_band_cells",
            "max_row_width",
            "estimated_scratch_bytes",
        )
    }
    expected.update(
        requested_code_budgets=budgets,
        limits=asdict(limits),
        visited_band_cells=cost["scheduled_band_cells"],
        allocated_packed_payload_bytes=cost["planned_packed_payload_bytes"],
    )
    actual = asdict(result)
    # Canonical bytes preserve integer/bool distinction that Python equality loses.
    _require(
        canonical_json_bytes({key: actual[key] for key in expected})
        == canonical_json_bytes(expected)
    )
    if result.status == "resource-unresolved-non-authorizing":
        _require(
            result.reason == "distance-threshold-exceeded"
            and result.edit_distance is None
            and type(result.budgets) is tuple
            and result.budgets == ()
        )
        _require(first != second and len(first) + len(second) > threshold)
        return
    _require(result.status == "exact-non-authorizing" and result.reason is None)
    d = result.edit_distance
    n, m = len(first), len(second)
    _require(
        type(d) is int
        and abs(n - m) <= d <= min(threshold, n + m)
        and (d - n + m) % 2 == 0
    )
    _require((d == 0) == (first == second))
    _require(
        type(result.requested_code_budgets) is tuple
        and type(result.budgets) is tuple
        and len(result.budgets) == len(budgets)
    )
    deletions, insertions = (d + n - m) // 2, (d - n + m) // 2
    previous = None
    for budget, row in zip(budgets, result.budgets, strict=True):
        _require(type(row) is BudgetExposure)
        _require(type(row.code_budget) is int and row.code_budget == budget)
        _require(all(type(getattr(row, key)) is int for key in _FIELDS))
        a, b, c, e, t, u = (getattr(row, key) for key in _FIELDS)
        _require(
            0 <= a <= b <= deletions and 0 <= c <= e <= insertions and 0 <= t <= u <= d
        )
        first_retained, second_retained = min(budget, n), min(budget, m)
        _require(max(0, deletions - (n - first_retained)) <= a <= b <= first_retained)
        _require(
            max(0, insertions - (m - second_retained)) <= c <= e <= second_retained
        )
        _require(a + c <= t <= min(a + e, b + c) and max(a + e, b + c) <= u <= b + e)
        bits = row.joint_signature_bits
        _require(type(bits) is int and 1 <= bits <= 15)
        signatures = [v for v in range(4) if bits & (1 << v)]
        _require(
            any(v & 2 for v in signatures) == (b > 0)
            and all(v & 2 for v in signatures) == (a > 0)
        )
        _require(
            any(v & 1 for v in signatures) == (e > 0)
            and all(v & 1 for v in signatures) == (c > 0)
        )
        _require((0 in signatures) == (t == 0) and (bits == 1) == (u == 0))
        if d == 0:
            _require(all(getattr(row, key) == 0 for key in _FIELDS) and bits == 1)
        if budget >= max(n, m):
            signature = (2 if deletions else 0) + (1 if insertions else 0)
            _require(
                (a, b, c, e, t, u)
                == (deletions, deletions, insertions, insertions, d, d)
                and bits == 1 << signature
            )
        if previous is not None:
            _require(
                all(getattr(previous, key) <= getattr(row, key) for key in _FIELDS)
            )
        previous = row


def _budget_bucket(budget):
    return dict(
        code_budget=budget,
        pairs=0,
        sums={key: 0 for key in _FIELDS},
        pair_total_min_fraction_sum=0.0,
        pair_total_max_fraction_sum=0.0,
        joint_signature_histogram={str(v): 0 for v in range(1, 16)},
        some_optimum_hides_all=0,
        all_optima_hide_all=0,
        every_optimum_exposes=0,
        some_optimum_exposes=0,
        every_optimum_exposes_all=0,
        some_optimum_exposes_all=0,
    )


def _accumulate(bucket, row, d):
    bucket["pairs"] += 1
    for key in _FIELDS:
        bucket["sums"][key] += getattr(row, key)
    bucket["pair_total_min_fraction_sum"] += row.total_min / d
    bucket["pair_total_max_fraction_sum"] += row.total_max / d
    bucket["joint_signature_histogram"][str(row.joint_signature_bits)] += 1
    for key, condition in (
        ("some_optimum_hides_all", row.total_min == 0),
        ("all_optima_hide_all", row.total_max == 0),
        ("every_optimum_exposes", row.total_min > 0),
        ("some_optimum_exposes", row.total_max > 0),
        ("every_optimum_exposes_all", row.total_min == d),
        ("some_optimum_exposes_all", row.total_max == d),
    ):
        bucket[key] += int(condition)


def audit_full_development_banded_edit_exposure(
    train_pairs,
    validation_pairs,
    retained_train_ids,
    retained_validation_ids,
    root_by_id,
    tokenizer,
    *,
    expected_geometry,
    backend_factory,
    limits=BandedEditVisibilityLimits(),
    distance_threshold=512,
    total_cell_cap=MAX_EXPOSURE_CELLS,
    code_budgets=None,
    progress=None,
):
    """Explicit synthetic seams; no source/DLL/model acquisition or fallback."""
    _require(
        type(total_cell_cap) is int and 0 < total_cell_cap <= MAX_EXPOSURE_CELLS,
        "invalid new exposure workload cap",
    )
    _require(callable(backend_factory), "explicit backend factory required")
    # Snapshot caller-owned metadata before callbacks. Frozen census validates it.
    splits = (tuple(train_pairs), tuple(validation_pairs))
    retained = (set(retained_train_ids), set(retained_validation_ids))
    roots = dict(root_by_id)
    prepass = audit_banded_pair_resource_census(
        *splits,
        *retained,
        roots,
        tokenizer,
        limits=limits,
        distance_threshold=distance_threshold,
    )
    _require(
        canonical_json_bytes(prepass) == canonical_json_bytes(expected_geometry),
        "geometry prepass commitment mismatch",
    )
    production_budgets = tuple(
        row["code_budget"] for row in prepass["policy"]["template_budgets"]
    )
    budgets = production_budgets if code_budgets is None else code_budgets
    _validate((), (), budgets, distance_threshold, limits)
    _require(
        len(budgets) == 5
        and all(b <= p for b, p in zip(budgets, production_budgets, strict=True)),
        "five fixture budgets may only tighten template budgets",
    )
    policy = dict(
        operation="bounded-band-edit-exposure-development-only",
        version=1,
        geometry_policy_sha256=prepass["policy_sha256"],
        geometry_prepass_records_sha256=prepass["ordered_internal_records_sha256"],
        total_cell_cap=total_cell_cap,
        limits=asdict(limits),
        distance_threshold=distance_threshold,
        code_budgets=list(budgets),
        order="train-then-validation-author-file-order",
        exhaustion="permanent-at-first-locally-eligible-nonfitting-pair",
    )
    policy_hash = sha256_bytes(canonical_json_bytes(policy))
    out = dict(
        status="retained-development-banded-edit-exposure-non-authorizing",
        training_authority=False,
        held_out_data_present=False,
        policy=policy,
        policy_sha256=policy_hash,
    )
    ordered = hashlib.sha256()
    geometry_ordered = hashlib.sha256()
    old_used = used = 0
    old_exhausted = exhausted = False
    backend = None
    for name, rows, ids in zip(("train", "validation"), splits, retained, strict=True):
        summaries = {key: _summary() for key in _STRATA}
        components = {key: set() for key in _STRATA}
        reason_counts = {key: 0 for key in _REASONS}
        reason_roots = {key: set() for key in _REASONS}
        reason_geometry = {key: _summary() for key in _REASONS}
        exposure = [_budget_bucket(budget) for budget in budgets]
        split_hash = hashlib.sha256()
        split_geometry = hashlib.sha256()
        visited = 0
        selected = [row for row in rows if row[0] in ids and row[1] in ids]
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
            old_reason = reason = cost["local_reason"]
            token_commitments = dict(
                first_token_ids_sha256=sha256_bytes(canonical_json_bytes(list(first))),
                second_token_ids_sha256=sha256_bytes(
                    canonical_json_bytes(list(second))
                ),
            )
            if old_reason is None:
                if (
                    old_exhausted
                    or cells > prepass["policy"]["total_cell_cap"] - old_used
                ):
                    old_exhausted = True
                    old_reason = "total-cell-budget-exhausted"
                else:
                    old_used += cells
            geometry_record = dict(
                split=name,
                vulnerable_id=row[0],
                safe_id=row[1],
                component_root=root,
                policy_sha256=prepass["policy_sha256"],
                **token_commitments,
                **cost,
                classification="prospective_admitted"
                if old_reason is None
                else "prospectively_unresolved",
                reason=old_reason,
            )
            encoded = canonical_json_bytes(geometry_record) + b"\n"
            geometry_ordered.update(encoded)
            split_geometry.update(encoded)
            result = None
            classifications = ["universe"]
            if reason is not None:
                classification = "preflight_unresolved"
                reason_counts[reason] += 1
                reason_roots[reason].add(root)
                _add(reason_geometry[reason], cells)
            else:
                classifications.append("locally_eligible")
                if exhausted or cells > total_cell_cap - used:
                    exhausted = True
                    classification = "global_cap_unresolved"
                    reason = "total-cell-budget-exhausted"
                else:
                    used += cells
                    if backend is None:
                        backend = backend_factory()
                    result = backend.audit(
                        first,
                        second,
                        code_budgets=budgets,
                        distance_threshold=distance_threshold,
                        limits=limits,
                    )
                    validate_completed_result(
                        result, first, second, budgets, distance_threshold, limits
                    )
                    classifications.append("dp_attempted")
                    visited += result.visited_band_cells
                    if result.edit_distance is None:
                        classification = "terminal_threshold_unresolved"
                        reason = result.reason
                    elif result.edit_distance == 0:
                        classification = "exact_zero_distance"
                    else:
                        classification = "exact_positive_distance"
                        for bucket, state in zip(exposure, result.budgets, strict=True):
                            _accumulate(bucket, state, result.edit_distance)
            classifications.append(classification)
            for key in classifications:
                _add(summaries[key], cells)
                components[key].add(root)
            record = dict(
                split=name,
                vulnerable_id=row[0],
                safe_id=row[1],
                component_root=root,
                **token_commitments,
                policy_sha256=policy_hash,
                geometry=cost,
                classification=classification,
                reason=reason,
                result=None if result is None else asdict(result),
                visited_band_cells=0 if result is None else result.visited_band_cells,
                allocated_packed_payload_bytes=0
                if result is None
                else result.allocated_packed_payload_bytes,
            )
            encoded = canonical_json_bytes(record) + b"\n"
            ordered.update(encoded)
            split_hash.update(encoded)
            if progress is not None:
                progress(name, index, len(selected))
        _require(
            split_geometry.hexdigest()
            == prepass[name]["ordered_internal_records_sha256"],
            "second-pass geometry/token commitment mismatch",
        )
        for bucket in exposure:
            count = bucket["pairs"]
            bucket["mean_pair_total_min_fraction"] = (
                bucket["pair_total_min_fraction_sum"] / count if count else None
            )
            bucket["mean_pair_total_max_fraction"] = (
                bucket["pair_total_max_fraction_sum"] / count if count else None
            )
        out[name] = dict(
            survival=prepass[name]["survival"],
            strata=summaries,
            components={key: len(value) for key, value in components.items()},
            preflight_unresolved_reasons=reason_counts,
            preflight_reason_geometry=reason_geometry,
            preflight_reason_components={
                key: len(value) for key, value in reason_roots.items()
            },
            visited_band_cells=visited,
            budget_exposure=exposure,
            ordered_internal_records_sha256=split_hash.hexdigest(),
            second_pass_geometry_records_sha256=split_geometry.hexdigest(),
        )
    _require(
        geometry_ordered.hexdigest() == prepass["ordered_internal_records_sha256"],
        "second-pass global geometry/token commitment mismatch",
    )
    if backend is not None:
        backend.verify_terminal()
    out["admission"] = dict(
        scheduled_band_cells=used,
        remaining_band_cells=total_cell_cap - used,
        exhausted=exhausted,
    )
    out["ordered_internal_records_sha256"] = ordered.hexdigest()
    out["geometry_prepass"] = prepass
    return out


def run_verified_development_edit_exposure(
    source_dir,
    paired_dir,
    tokenizer,
    *,
    geometry_receipt,
    backend_factory,
    model_inventory_sha256,
    source_expectation=PRIMEVUL_ORIGINAL_DEVELOPMENT,
    pair_expectation=PRIMEVUL_ORIGINAL_PAIRS,
    limits=BandedEditVisibilityLimits(),
    distance_threshold=512,
    total_cell_cap=MAX_EXPOSURE_CELLS,
    graph_progress=None,
    progress=None,
):
    """Verified development readers and one graph; explicit fixture backend seam.

    Production CLI must supply a pinned native factory and independently bind
    receipt bytes, model inventory and clean source before/after this call.
    """
    _require(
        type(total_cell_cap) is int and 0 < total_cell_cap <= MAX_EXPOSURE_CELLS,
        "invalid new exposure workload cap",
    )
    _validate((), (), (1, 2, 3, 4, 5), distance_threshold, limits)
    _require(callable(backend_factory), "explicit backend factory required")
    _require(
        type(source_expectation) is PrimeVulDevelopmentExpectation
        and type(pair_expectation) is PrimeVulPairExpectation,
        "source expectations required",
    )
    pinned = source_expectation == PRIMEVUL_ORIGINAL_DEVELOPMENT
    _require(
        pinned == (pair_expectation == PRIMEVUL_ORIGINAL_PAIRS),
        "mixed source expectations",
    )
    if pinned:
        _require(
            limits == BandedEditVisibilityLimits()
            and distance_threshold == 512
            and total_cell_cap == MAX_EXPOSURE_CELLS,
            "pinned exposure policy changed",
        )
        verify_geometry_dependencies(Path(__file__).resolve().parents[3])
    _require(
        type(model_inventory_sha256) is str
        and re.fullmatch("[a-f0-9]{64}", model_inventory_sha256) is not None,
        "model inventory hash required",
    )
    _require(type(geometry_receipt) is dict, "geometry provenance receipt required")
    # Snapshot external receipt before graph/tokenizer/backend callbacks.
    prior = json.loads(canonical_json_bytes(geometry_receipt))
    _require(
        source_expectation.train_rows + source_expectation.validation_rows <= 250000
        and pair_expectation.train_pairs + pair_expectation.validation_pairs <= 250000,
        "development graph/census bound exceeded",
    )
    source_dir, paired_dir = Path(source_dir), Path(paired_dir)
    original = verify_primevul_development_pairs(
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
    ledgers = dict(
        pair_edge_ledger_sha256=sha256_bytes(canonical_json_bytes(edges)),
        component_root_ledger_sha256=sha256_bytes(
            canonical_json_bytes(sorted(graph.root_by_id.items()))
        ),
        retained_train_id_ledger_sha256=sha256_bytes(
            canonical_json_bytes([r.source_id for r in graph.train])
        ),
        retained_validation_id_ledger_sha256=sha256_bytes(
            canonical_json_bytes([r.source_id for r in graph.validation])
        ),
    )
    if pinned:
        _require(ledgers == _PINNED_GRAPH_LEDGERS, "pinned graph provenance changed")
    provenance = dict(
        source_scope="pinned-original-development" if pinned else "fixture",
        source_expectation=asdict(source_expectation),
        pair_expectation=asdict(pair_expectation),
        pair_source_receipt_sha256=sha256_bytes(canonical_json_bytes(original)),
        model_inventory_sha256=model_inventory_sha256,
        graph_ledgers=ledgers,
        retained_train_rows=len(graph.train),
        retained_validation_rows=len(graph.validation),
    )
    _require(
        canonical_json_bytes({key: prior.get(key) for key in provenance})
        == canonical_json_bytes(provenance),
        "geometry provenance mismatch",
    )
    core_keys = (
        "receipt_version",
        "status",
        "training_authority",
        "held_out_data_present",
        "policy",
        "policy_sha256",
        "train",
        "validation",
        "ordered_internal_records_sha256",
        "admission",
    )
    _require(
        all(key in prior for key in core_keys), "geometry provenance core incomplete"
    )
    retained_train = {r.source_id for r in graph.train}
    retained_validation = {r.source_id for r in graph.validation}
    if pinned:
        _require(
            (len(graph.train), len(graph.validation)) == (177291, 22772),
            "pinned retained row counts changed",
        )
        _require(
            (len(train_pairs), len(validation_pairs)) == (4354, 562),
            "pinned author counts changed",
        )
        _require(
            tuple(
                sum(row[0] in ids and row[1] in ids for row in rows)
                for rows, ids in (
                    (train_pairs, retained_train),
                    (validation_pairs, retained_validation),
                )
            )
            == (4344, 482),
            "pinned both-retained universe changed",
        )
    out = audit_full_development_banded_edit_exposure(
        train_pairs,
        validation_pairs,
        retained_train,
        retained_validation,
        graph.root_by_id,
        tokenizer,
        expected_geometry={key: prior[key] for key in core_keys},
        backend_factory=backend_factory,
        limits=limits,
        distance_threshold=distance_threshold,
        total_cell_cap=total_cell_cap,
        progress=progress,
    )
    final = verify_primevul_development_pairs(
        source_dir,
        paired_dir,
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
    )
    _require(
        canonical_json_bytes(final) == canonical_json_bytes(original),
        "development sources changed during exposure",
    )
    if pinned:
        verify_geometry_dependencies(Path(__file__).resolve().parents[3])
    out.update(provenance)
    return out


def verify_edit_exposure_module_origin(repo_root, module_path):
    root = Path(repo_root).resolve(strict=True)
    expected = root / "src/aluclu/alc_r0/full_development_banded_edit_exposure.py"
    _require(
        expected.is_file()
        and expected.resolve(strict=True) == expected
        and Path(module_path).resolve(strict=True) == expected,
        "edit exposure module does not originate in source checkout",
    )


def load_pinned_geometry_receipt(receipt_path):
    """Data-only exact committed geometry receipt; no source/model/DLL access."""
    raw = Path(receipt_path).read_bytes()
    _require(
        sha256_bytes(raw) == GEOMETRY_RECEIPT_SHA256, "geometry receipt bytes changed"
    )
    receipt = json.loads(raw)
    _require(
        canonical_json_bytes(receipt) + b"\n" == raw, "noncanonical geometry receipt"
    )
    _require(
        receipt["source_checkout"]
        == {
            "source_commit": "f7af51351cd66017a3c438af473b9eb17b0b7839",
            "source_tree_sha256": "cae2990a5ac4c73bc7af7c5351a7b2f27b9298e01536e77a8725bceea629f17e",
            "tracked_file_count": 721,
        },
        "geometry receipt source freeze changed",
    )
    return receipt


def verify_pinned_native_build(receipt_path):
    """Data-only original build validation; never loads or compiles a DLL."""
    path = Path(receipt_path).resolve(strict=True)
    _require(
        sha256_bytes(path.read_bytes()) == NATIVE_RECEIPT_SHA256,
        "native receipt bytes changed",
    )
    from .banded_edit_token_visibility_native import read_build_receipt

    receipt = read_build_receipt(path)
    _require(receipt["dll_sha256"] == NATIVE_DLL_SHA256, "native artifact changed")
    # Re-read after metadata/source/toolchain validation to reject receipt races.
    _require(
        sha256_bytes(path.read_bytes()) == NATIVE_RECEIPT_SHA256,
        "native receipt changed during verification",
    )
    return receipt


class PinnedDevelopmentNativeBackend:
    """One named original native owner, constructed only after the full prepass."""

    def __init__(self, receipt_path):
        self.receipt_path = Path(receipt_path).resolve(strict=True)
        self.receipt = verify_pinned_native_build(self.receipt_path)
        from .banded_edit_token_visibility_native import NativeBandedBackend

        self.owner = NativeBandedBackend(self.receipt_path)
        _require(
            canonical_json_bytes(self.owner.receipt)
            == canonical_json_bytes(self.receipt),
            "native owner receipt mismatch",
        )

    def audit(self, first, second, **kwargs):
        return self.owner.audit(first, second, **kwargs)

    def verify_terminal(self):
        import ctypes

        self.owner._verify_artifact()
        identifier = (ctypes.c_uint8 * 32)()
        _require(
            self.owner.dll.aluclu_banded_abi_v1() == 1
            and self.owner.dll.aluclu_banded_build_id_v1(identifier, 32) == 0
            and bytes(identifier).hex() == self.receipt["native_source_sha256"],
            "native terminal ABI/build identifier changed",
        )
        _require(
            canonical_json_bytes(verify_pinned_native_build(self.receipt_path))
            == canonical_json_bytes(self.receipt),
            "native terminal provenance changed",
        )


def _argument_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "development_data_dir",
        "paired_development_data_dir",
        "tokenizer_snapshot",
        "native_build_receipt",
        "geometry_receipt",
    ):
        parser.add_argument(name, type=Path)
    return parser


def main():
    args = _argument_parser().parse_args()
    root = Path.cwd().resolve(strict=True)
    verify_edit_exposure_module_origin(root, Path(__file__))
    verify_geometry_dependencies(root)
    checkout = inspect_clean_source_checkout(root)
    geometry = load_pinned_geometry_receipt(args.geometry_receipt)
    native = verify_pinned_native_build(args.native_build_receipt)
    snapshot = verify_model_snapshot(args.tokenizer_snapshot)
    _require(
        snapshot["inventory_sha256"] == geometry["model_inventory_sha256"],
        "geometry tokenizer inventory mismatch",
    )
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

    def progress(split, processed, total):
        print(
            f"edit exposure progress {split} {processed}/{total}",
            file=sys.stderr,
            flush=True,
        )

    result = run_verified_development_edit_exposure(
        args.development_data_dir,
        args.paired_development_data_dir,
        tokenizer,
        geometry_receipt=geometry,
        backend_factory=lambda: PinnedDevelopmentNativeBackend(
            args.native_build_receipt
        ),
        model_inventory_sha256=snapshot["inventory_sha256"],
        graph_progress=graph_progress,
        progress=progress,
    )
    verify_terminal_census_state(
        args.tokenizer_snapshot,
        root,
        model_inventory_sha256=snapshot["inventory_sha256"],
        source_checkout=checkout,
    )
    verify_edit_exposure_module_origin(root, Path(__file__))
    verify_geometry_dependencies(root)
    _require(
        canonical_json_bytes(load_pinned_geometry_receipt(args.geometry_receipt))
        == canonical_json_bytes(geometry),
        "terminal geometry provenance changed",
    )
    _require(
        canonical_json_bytes(verify_pinned_native_build(args.native_build_receipt))
        == canonical_json_bytes(native),
        "terminal native provenance changed",
    )
    result.update(
        source_checkout=asdict(checkout),
        geometry_receipt_sha256=GEOMETRY_RECEIPT_SHA256,
        geometry_source_checkout=geometry["source_checkout"],
        native_build_receipt_sha256=NATIVE_RECEIPT_SHA256,
        native_dll_sha256=native["dll_sha256"],
        native_build_identifier=native["native_source_sha256"],
        native_source_hashes=native["source_hashes"],
        model_repository=snapshot["repository"],
        model_revision=snapshot["revision"],
        model_snapshot_receipt_sha256=sha256_bytes(canonical_json_bytes(snapshot)),
        invocation={
            "module": "aluclu.alc_r0.full_development_banded_edit_exposure",
            **{
                name: str(value.resolve(strict=True))
                for name, value in vars(args).items()
            },
            "python_executable": str(Path(sys.executable).resolve(strict=True)),
            "python_version": sys.version,
            "platform": platform.platform(),
        },
    )
    sys.stdout.buffer.write(canonical_json_bytes(result) + b"\n")


if __name__ == "__main__":
    main()
