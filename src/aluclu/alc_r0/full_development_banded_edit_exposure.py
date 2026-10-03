"""Development exposure aggregation. No implicit corpus reader or native load.

The fixture core is not a production execution entry point. A separately
reviewed pinned-source CLI is required before any real development execution.
"""

import hashlib
from dataclasses import asdict

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
)
from .canonical import canonical_json_bytes, sha256_bytes
from .edit_token_visibility_reference import BudgetExposure
from .retained_pair_resource_census import _full_code_ids

MAX_EXPOSURE_CELLS = 3_000_000_000
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
