from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest
from test_alc_r0_paired_prompt_contrast import _ByteTokenizer
from test_alc_r0_primevul_pair_clone_full import _fixture
from test_alc_r0_retained_pair_resource_census import _LengthTokenizer, _pair

from aluclu.alc_r0.banded_edit_token_visibility_reference import (
    BandedEditVisibilityLimits,
    audit_banded_edit_token_visibility,
)
from aluclu.alc_r0.banded_pair_resource_census import (
    audit_banded_pair_resource_census,
    banded_pair_resource_cost,
    run_banded_pair_resource_census,
    verify_banded_census_module_origin,
    verify_geometry_dependencies,
)
from aluclu.alc_r0.canonical import canonical_json_bytes
from aluclu.alc_r0.retained_pair_resource_census import PairResourceCensusError


def _audit(train=(), validation=(), *, retained=None, roots=None, **kwargs):
    train_ids = {value for row in train for value in row[:2]}
    validation_ids = {value for row in validation for value in row[:2]}
    roots = (
        roots
        if roots is not None
        else {value: row[0] for row in train + validation for value in row[:2]}
    )
    return audit_banded_pair_resource_census(
        train,
        validation,
        train_ids if retained is None else retained,
        validation_ids,
        roots,
        _LengthTokenizer(),
        **kwargs,
    )


def test_independent_geometric_enumeration_and_frozen_reference_metadata():
    for n in range(1, 5):
        for m in range(1, 5):
            for threshold in range(8):
                cost = banded_pair_resource_cost(n, m, distance_threshold=threshold)
                reference = audit_banded_edit_token_visibility(
                    (7,) * n,
                    (7,) * m,
                    code_budgets=(1, 2, 3, 4, 5),
                    distance_threshold=threshold,
                )
                if abs(n - m) > threshold:
                    assert cost["scheduled_band_cells"] == 0
                    assert cost["local_reason"] == "distance-threshold-exceeded"
                    continue
                widths = [
                    sum(
                        abs(i - j) + abs((n - m) - (i - j)) <= threshold
                        for j in range(m + 1)
                    )
                    for i in range(n + 1)
                ]
                assert cost["scheduled_band_cells"] == sum(widths)
                assert cost["max_row_width"] == max(widths)
                assert cost["band_lower_diagonal"] == reference.band_lower_diagonal
                assert cost["band_upper_diagonal"] == reference.band_upper_diagonal
                assert cost["scheduled_band_cells"] == reference.scheduled_band_cells
                assert (
                    cost["estimated_scratch_bytes"] == reference.estimated_scratch_bytes
                )
                assert (
                    cost["planned_packed_payload_bytes"]
                    == reference.allocated_packed_payload_bytes
                )


def test_unknown_endpoint_geometry_is_not_known_empty_band():
    unknown = banded_pair_resource_cost(32769, 1)
    empty = banded_pair_resource_cost(1, 514)
    for key in (
        "band_lower_diagonal",
        "band_upper_diagonal",
        "scheduled_band_cells",
        "max_row_width",
        "planned_packed_payload_bytes",
        "estimated_scratch_bytes",
    ):
        assert unknown[key] is None
    assert unknown["local_reason"] == "endpoint-token-limit"
    assert empty["scheduled_band_cells"] == empty["max_row_width"] == 0
    assert empty["planned_packed_payload_bytes"] == 0
    assert empty["estimated_scratch_bytes"] is None
    assert empty["local_reason"] == "distance-threshold-exceeded"


def test_exact_endpoint_K_and_tightened_cell_scratch_boundaries():
    boundary = banded_pair_resource_cost(32768, 32768, distance_threshold=0)
    assert boundary["scheduled_band_cells"] == 32769
    assert boundary["local_reason"] is None
    cost = banded_pair_resource_cost(6, 6, distance_threshold=512)
    assert cost["scheduled_band_cells"] == 49
    limits = BandedEditVisibilityLimits(
        max_band_cells=49, max_scratch_bytes=cost["estimated_scratch_bytes"]
    )
    assert banded_pair_resource_cost(6, 6, limits=limits)["local_reason"] is None
    rejected = banded_pair_resource_cost(
        6, 6, limits=replace(limits, max_band_cells=48)
    )
    assert rejected["local_reason"] == "band-cell-limit"
    assert (
        rejected["planned_packed_payload_bytes"] == cost["planned_packed_payload_bytes"]
    )
    assert (
        banded_pair_resource_cost(
            6, 6, limits=replace(limits, max_scratch_bytes=limits.max_scratch_bytes - 1)
        )["local_reason"]
        == "scratch-byte-limit"
    )
    assert (
        banded_pair_resource_cost(
            1, 514, limits=replace(limits, max_band_cells=1, max_scratch_bytes=1)
        )["local_reason"]
        == "distance-threshold-exceeded"
    )
    assert banded_pair_resource_cost(32768, 32768)["local_reason"] == "band-cell-limit"


@pytest.mark.parametrize(
    "n,m", [(0, 1), (1, 0), (True, 1), (-1, 1), (1.0, 1), (1, "1")]
)
def test_strict_positive_endpoint_dimensions(n, m):
    with pytest.raises(PairResourceCensusError):
        banded_pair_resource_cost(n, m)


@pytest.mark.parametrize("K", [True, -1, 513, 1.0, "1"])
def test_strict_bounded_threshold(K):
    with pytest.raises(PairResourceCensusError):
        banded_pair_resource_cost(1, 1, distance_threshold=K)


@pytest.mark.parametrize(
    "limits",
    [
        None,
        BandedEditVisibilityLimits(max_endpoint_tokens=True),
        BandedEditVisibilityLimits(max_endpoint_tokens=32769),
        BandedEditVisibilityLimits(max_band_cells=4194305),
        BandedEditVisibilityLimits(max_scratch_bytes=67108865),
        BandedEditVisibilityLimits(max_distance_threshold=513),
    ],
)
def test_limits_cannot_relax_original_band_policy(limits):
    with pytest.raises(PairResourceCensusError):
        _audit(limits=limits)


@pytest.mark.parametrize("cap", [True, 0, -1, 1.0, "1", 100000001])
def test_total_prospective_cap_is_fixed_or_tightened(cap):
    with pytest.raises(PairResourceCensusError):
        _audit(total_cell_cap=cap)


def test_first_nonfit_permanently_exhausts_across_splits():
    receipt = _audit(
        (
            _pair(1, 2, 2),
            _pair(3, 3, 3),
            _pair(5, 1, 1),
            _pair(7, 32769, 1),
            _pair(9, 1, 514),
        ),
        (_pair(11, 1, 1),),
        total_cell_cap=9,
    )
    assert receipt["admission"] == {
        "admitted_band_cells": 9,
        "remaining_band_cells": 0,
        "exhausted": True,
    }
    assert receipt["train"]["prospective_admitted"]["pairs"] == 1
    assert receipt["train"]["prospectively_unresolved"]["pairs"] == 4
    assert receipt["validation"]["prospective_admitted"]["pairs"] == 0
    assert (
        receipt["validation"]["unresolved_reasons"]["total-cell-budget-exhausted"] == 1
    )
    assert receipt["train"]["universe"]["known_geometry_pairs"] == 4
    assert receipt["train"]["universe"]["unknown_geometry_pairs"] == 1
    assert receipt["train"]["pair_band_cell_histogram"]["unknown"] == 1
    assert receipt["train"]["unresolved_reasons"]["distance-threshold-exceeded"] == 1
    assert receipt["train"]["unresolved_reasons"]["endpoint-token-limit"] == 1


def test_survival_partition_root_union_and_full_population_fractions():
    train = (_pair(1, 1, 1), _pair(3, 1, 1), _pair(5, 1, 1), _pair(7, 1, 1))
    roots = {value: "primevul:1" for row in train for value in row[:2]}
    receipt = _audit(
        train,
        retained={"primevul:1", "primevul:2", "primevul:3", "primevul:6"},
        roots=roots,
    )
    assert receipt["train"]["survival"] == {
        "author_pairs": 4,
        "both_retained": 1,
        "vulnerable_only_retained": 1,
        "safe_only_retained": 1,
        "neither_retained": 1,
    }
    assert receipt["train"]["components"]["universe"] == 1
    assert receipt["train"]["eligible_fraction_of_universe"] == 1
    assert receipt["validation"]["eligible_fraction_of_universe"] is None
    assert (
        receipt["validation"]["ordered_internal_records_sha256"]
        == hashlib.sha256(b"").hexdigest()
    )


def test_ordered_digest_template_grid_no_raw_or_edit_leakage():
    pairs = (_pair(1, 1, 1), _pair(3, 2, 2))
    receipt = _audit(pairs)
    assert (
        receipt["ordered_internal_records_sha256"]
        != _audit(tuple(reversed(pairs)))["ordered_internal_records_sha256"]
    )
    encoded = canonical_json_bytes(receipt)
    for forbidden in (
        b"primevul:",
        b'"tokens_',
        b"edit_distance",
        b"exposures",
        b"[7,7",
    ):
        assert forbidden not in encoded
    assert (
        receipt["training_authority"] is False
        and receipt["held_out_data_present"] is False
    )
    assert [
        row["max_common_tokens"] for row in receipt["policy"]["template_budgets"]
    ] == [512, 1024, 2048, 4096, 8192]
    assert (
        receipt["policy"]["operation"] == "banded-geometry-prospective-admission-only"
    )


@pytest.mark.parametrize("changed_source", ["source", "paired"])
def test_fixture_reader_graph_roots_and_terminal_source_recheck(
    tmp_path, changed_source
):
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)
    kwargs = dict(
        model_inventory_sha256="a" * 64,
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
    )
    receipt = run_banded_pair_resource_census(full, paired, _ByteTokenizer(), **kwargs)
    assert len(receipt["graph_ledgers"]) == 4
    assert receipt["source_scope"] == "fixture"
    assert (
        receipt["train"]["universe"]["pairs"]
        == receipt["validation"]["universe"]["pairs"]
        == 1
    )

    def mutate(split, processed, total):
        if split == "validation" and processed == total:
            target = (
                full / "primevul_train.jsonl"
                if changed_source == "source"
                else paired / "primevul_train_paired.jsonl"
            )
            target.write_bytes(target.read_bytes().replace(b"red", b"RED", 1))

    with pytest.raises(ValueError):
        run_banded_pair_resource_census(
            full, paired, _ByteTokenizer(), census_progress=mutate, **kwargs
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"distance_threshold": 511},
        {"total_cell_cap": 99999999},
        {"limits": BandedEditVisibilityLimits(max_band_cells=1)},
    ],
)
def test_pinned_policy_override_rejected_before_io(tmp_path, kwargs):
    with pytest.raises(PairResourceCensusError, match="pinned"):
        run_banded_pair_resource_census(
            tmp_path,
            tmp_path,
            _ByteTokenizer(),
            model_inventory_sha256="a" * 64,
            **kwargs,
        )


def test_exact_module_origin_and_dependency_pins(tmp_path):
    root = Path(__file__).resolve().parents[1]
    module = root / "src/aluclu/alc_r0/banded_pair_resource_census.py"
    verify_banded_census_module_origin(root, module)
    verify_geometry_dependencies(root)
    with pytest.raises(PairResourceCensusError):
        verify_banded_census_module_origin(tmp_path, module)
    with pytest.raises(PairResourceCensusError):
        verify_geometry_dependencies(tmp_path)


def test_hypothetical_payload_is_not_actual_reference_allocation_on_rejection():
    limits = BandedEditVisibilityLimits(max_band_cells=1)
    cost = banded_pair_resource_cost(2, 2, limits=limits)
    reference = audit_banded_edit_token_visibility(
        (7, 7),
        (7, 7),
        code_budgets=(1, 2, 3, 4, 5),
        distance_threshold=512,
        limits=limits,
    )
    assert cost["planned_packed_payload_bytes"] > 0
    assert reference.allocated_packed_payload_bytes == 0
    assert cost["estimated_scratch_bytes"] == reference.estimated_scratch_bytes
    assert reference.visited_band_cells == 0


def test_histogram_boundaries_known_zero_and_unknown_have_distinct_accounting():
    receipt = _audit(
        (
            _pair(1, 16383, 16383),
            _pair(3, 16384, 16384),
            _pair(5, 32769, 1),
            _pair(7, 1, 2),
        ),
        distance_threshold=0,
    )
    histogram = receipt["train"]["pair_band_cell_histogram"]
    assert histogram["le_16384"] == 2  # exact cell boundary and known C0
    assert histogram["le_65536"] == 1
    assert histogram["unknown"] == 1
    assert sum(histogram.values()) == 4
    assert sum(receipt["train"]["endpoint_length_histogram"].values()) == 8


def test_shared_root_component_union_and_metadata_callback_snapshot():
    train = (_pair(1, 1, 1), _pair(3, 1, 1))
    validation = (_pair(5, 1, 1),)
    train_ids = {value for row in train for value in row[:2]}
    validation_ids = {value for row in validation for value in row[:2]}
    roots = {value: "primevul:1" for row in train for value in row[:2]}
    roots.update({value: "primevul:5" for value in validation[0][:2]})

    def clear_metadata(*args):
        train_ids.clear()
        validation_ids.clear()
        roots.clear()

    receipt = audit_banded_pair_resource_census(
        train,
        validation,
        train_ids,
        validation_ids,
        roots,
        _LengthTokenizer(),
        progress=clear_metadata,
    )
    assert receipt["train"]["components"]["universe"] == 1
    assert receipt["validation"]["universe"]["pairs"] == 1


@pytest.mark.parametrize("bad_ids", [[], [True], [-1], [1.0], [99]])
def test_reused_full_token_validation_rejects_invalid_and_special_ids(bad_ids):
    class BadTokenizer(_LengthTokenizer):
        bos_token_id = 99

        def encode(self, text, *, add_special_tokens):
            if text.startswith("tokens_"):
                return bad_ids
            return super().encode(text, add_special_tokens=add_special_tokens)

    with pytest.raises(PairResourceCensusError):
        audit_banded_pair_resource_census(
            (_pair(1, 1, 1),),
            (),
            {"primevul:1", "primevul:2"},
            set(),
            {"primevul:1": "primevul:1", "primevul:2": "primevul:1"},
            BadTokenizer(),
        )


def test_dependency_change_is_rejected(tmp_path):
    root = Path(__file__).resolve().parents[1]
    for relative in (
        "src/aluclu/alc_r0/retained_pair_resource_census.py",
        "src/aluclu/alc_r0/banded_edit_token_visibility_reference.py",
    ):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((root / relative).read_bytes())
    verify_geometry_dependencies(tmp_path)
    target.write_bytes(b"changed")
    with pytest.raises(PairResourceCensusError, match="changed"):
        verify_geometry_dependencies(tmp_path)
