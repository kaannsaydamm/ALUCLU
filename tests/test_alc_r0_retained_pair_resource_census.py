from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from test_alc_r0_acquisition import _snapshot
from test_alc_r0_paired_prompt_contrast import _ByteTokenizer
from test_alc_r0_primevul_pair_clone_full import _fixture
from test_alc_r0_source_checkout import _git

from aluclu.alc_r0.acquisition import verify_model_snapshot
from aluclu.alc_r0.canonical import canonical_json_bytes
from aluclu.alc_r0.edit_token_visibility_reference import (
    EditVisibilityLimits,
    estimate_scratch_bytes,
)
from aluclu.alc_r0.retained_pair_resource_census import (
    PairResourceCensusError,
    audit_retained_pair_resource_census,
    pair_resource_cost,
    run_retained_pair_resource_census,
    verify_census_module_origin,
    verify_terminal_census_state,
)
from aluclu.alc_r0.source_checkout import inspect_clean_source_checkout


class _LengthTokenizer(_ByteTokenizer):
    def encode(self, text: str, *, add_special_tokens: bool) -> list[int]:
        if text.startswith("tokens_"):
            assert add_special_tokens is False
            return [7] * int(text.removeprefix("tokens_"))
        return super().encode(text, add_special_tokens=add_special_tokens)


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    root = tmp_path / "checkout"
    root.mkdir()
    _git(root, "init", "--quiet")
    _git(root, "config", "user.name", "ALC-R0 Census Fixture")
    _git(root, "config", "user.email", "census@example.invalid")
    _git(root, "config", "core.autocrlf", "false")
    (root / "source.py").write_bytes(b"print('frozen')\n")
    _git(root, "add", "source.py")
    _git(root, "commit", "--quiet", "-m", "freeze census fixture")
    return root


def _pair(index: int, n: int, m: int) -> tuple[str, str, str, str]:
    return (f"primevul:{index}", f"primevul:{index + 1}", f"tokens_{n}", f"tokens_{m}")


def _audit(train=(), validation=(), *, retained=None, roots=None, **kwargs):
    train_ids = {source_id for row in train for source_id in row[:2]}
    validation_ids = {source_id for row in validation for source_id in row[:2]}
    if roots is None:
        roots = {
            source_id: row[0] for row in train + validation for source_id in row[:2]
        }
    return audit_retained_pair_resource_census(
        train,
        validation,
        train_ids if retained is None else retained,
        validation_ids,
        roots,
        _LengthTokenizer(),
        **kwargs,
    )


def test_exact_local_cell_cap_boundary_without_dp() -> None:
    inside = pair_resource_cost(2047, 2047)
    outside = pair_resource_cost(2048, 2048)
    assert inside == {
        "first_tokens": 2047,
        "second_tokens": 2047,
        "dp_cells": 4_194_304,
        "estimated_scratch_bytes": estimate_scratch_bytes(2047, 2047, 5),
        "local_reason": None,
    }
    assert outside["dp_cells"] == 4_198_401
    assert outside["local_reason"] == "dp-cell-limit"


def test_endpoint_cell_scratch_reason_precedence_and_null_estimate() -> None:
    limits = EditVisibilityLimits(10, 10, 1)
    assert (
        pair_resource_cost(11, 11, limits=limits)["local_reason"]
        == "endpoint-token-limit"
    )
    assert pair_resource_cost(3, 3, limits=limits)["local_reason"] == "dp-cell-limit"
    assert (
        pair_resource_cost(1, 1, limits=limits)["local_reason"] == "scratch-byte-limit"
    )
    oversized = pair_resource_cost(32_769, 32_769)
    assert oversized["local_reason"] == "endpoint-token-limit"
    assert oversized["estimated_scratch_bytes"] is None
    # Tightened endpoint limit does not suppress estimates within the absolute ceiling.
    assert (
        pair_resource_cost(11, 11, limits=limits)["estimated_scratch_bytes"] is not None
    )


def test_total_cap_equal_fit_then_first_nonfit_exhausts_across_splits() -> None:
    receipt = _audit(
        (_pair(1, 2, 2), _pair(3, 3, 3), _pair(5, 1, 1), _pair(7, 2048, 2048)),
        (_pair(9, 1, 1), _pair(11, 32_769, 1)),
        total_cell_cap=10,
    )
    assert receipt["admission"]["admitted_dp_cells"] == 9
    assert receipt["admission"]["remaining_dp_cells"] == 1
    assert receipt["admission"]["exhausted"] is True
    train, validation = receipt["train"], receipt["validation"]
    assert train["universe"]["pairs"] == 4
    assert train["locally_eligible"]["pairs"] == 3
    assert train["admitted"]["pairs"] == 1
    assert train["unresolved"]["pairs"] == 3
    assert train["unresolved_reasons"] == {
        "endpoint-token-limit": 0,
        "dp-cell-limit": 1,
        "scratch-byte-limit": 0,
        "total-cell-budget-exhausted": 2,
    }
    assert validation["admitted"]["pairs"] == 0
    assert validation["unresolved_reasons"]["total-cell-budget-exhausted"] == 1
    assert validation["unresolved_reasons"]["endpoint-token-limit"] == 1
    equal = _audit((_pair(1, 2, 2),), total_cell_cap=9)
    assert equal["admission"]["admitted_dp_cells"] == 9
    assert equal["admission"]["exhausted"] is False


def test_nonfit_stops_later_small_pair_even_when_it_would_fit_remaining() -> None:
    receipt = _audit(
        (_pair(1, 2, 2), _pair(3, 3, 3), _pair(5, 1, 1)), total_cell_cap=14
    )
    assert receipt["admission"]["remaining_dp_cells"] == 5
    assert receipt["train"]["admitted"]["pairs"] == 1
    assert receipt["train"]["unresolved_reasons"]["total-cell-budget-exhausted"] == 2


def test_four_survival_categories_keep_original_endpoints() -> None:
    train = tuple(_pair(index, 1, 1) for index in (1, 3, 5, 7))
    receipt = _audit(
        train, retained={"primevul:1", "primevul:2", "primevul:3", "primevul:6"}
    )
    assert receipt["train"]["survival"] == {
        "author_pairs": 4,
        "both_retained": 1,
        "vulnerable_only_retained": 1,
        "safe_only_retained": 1,
        "neither_retained": 1,
    }
    assert receipt["train"]["universe"]["pairs"] == 1


def test_shared_endpoint_component_counts_use_union_and_can_overlap_strata() -> None:
    train = (_pair(1, 1, 1), ("primevul:1", "primevul:3", "tokens_1", "tokens_2"))
    receipt = _audit(
        train,
        roots={f"primevul:{i}": "primevul:1" for i in (1, 2, 3)},
        total_cell_cap=4,
    )
    assert receipt["train"]["universe"]["pairs"] == 2
    assert receipt["train"]["components"] == {
        "universe": 1,
        "locally_eligible": 1,
        "admitted": 1,
        "unresolved": 1,
        "unresolved_reasons": {
            "endpoint-token-limit": 0,
            "dp-cell-limit": 0,
            "scratch-byte-limit": 0,
            "total-cell-budget-exhausted": 1,
        },
    }
    assert receipt["train"]["endpoint_length_histogram"]["le_512"] == 4


def test_empty_universe_is_explicit_with_null_coverage_fractions() -> None:
    receipt = _audit()
    for split in ("train", "validation"):
        assert receipt[split]["universe"] == {
            "pairs": 0,
            "dp_cells_sum": 0,
            "dp_cells_max": 0,
        }
        assert receipt[split]["eligible_fraction_of_universe"] is None
        assert receipt[split]["admitted_fraction_of_universe"] is None
        assert (
            receipt[split]["ordered_internal_records_sha256"]
            == hashlib.sha256(b"").hexdigest()
        )
    assert receipt["admission"]["exhausted"] is False


@pytest.mark.parametrize("boundary", [512, 1024, 2048, 4096, 8192, 16384, 32768])
def test_endpoint_histogram_uses_disjoint_inclusive_boundaries(boundary: int) -> None:
    receipt = _audit((_pair(1, boundary, boundary + 1),))
    histogram = receipt["train"]["endpoint_length_histogram"]
    edges = [512, 1024, 2048, 4096, 8192, 16384, 32768]
    expected = {f"le_{edge}": 0 for edge in edges} | {"overflow": 0}
    expected[f"le_{boundary}"] = 1
    next_index = edges.index(boundary) + 1
    expected[f"le_{edges[next_index]}" if next_index < len(edges) else "overflow"] = 1
    assert histogram == expected


@pytest.mark.parametrize(
    "length,bin_name",
    [
        (127, "le_16384"),
        (255, "le_65536"),
        (511, "le_262144"),
        (1023, "le_1048576"),
        (2047, "le_4194304"),
    ],
)
def test_cell_histogram_uses_full_pair_cost_and_inclusive_boundaries(
    length, bin_name
) -> None:
    receipt = _audit((_pair(1, length, length), _pair(3, length + 1, length + 1)))
    histogram = receipt["train"]["pair_cell_histogram"]
    assert histogram[bin_name] == 1
    assert sum(histogram.values()) == 2
    if length == 2047:
        assert histogram["overflow"] == 1


def test_hash_is_exact_ordered_internal_commitment_without_raw_leakage() -> None:
    train = (_pair(1, 1, 2), _pair(3, 2, 1))
    receipt = _audit(train)
    ordered = hashlib.sha256()
    for row in train:
        n, m = (int(text.removeprefix("tokens_")) for text in row[2:])
        ordered.update(
            canonical_json_bytes(
                {
                    "split": "train",
                    "vulnerable_id": row[0],
                    "safe_id": row[1],
                    "component_root": row[0],
                    "first_token_ids_sha256": hashlib.sha256(
                        canonical_json_bytes([7] * n)
                    ).hexdigest(),
                    "second_token_ids_sha256": hashlib.sha256(
                        canonical_json_bytes([7] * m)
                    ).hexdigest(),
                    **pair_resource_cost(n, m),
                    "classification": "admitted",
                    "reason": None,
                }
            )
            + b"\n"
        )
    assert receipt["ordered_internal_records_sha256"] == ordered.hexdigest()
    reversed_receipt = _audit(tuple(reversed(train)))
    assert receipt["train"]["universe"] == reversed_receipt["train"]["universe"]
    assert (
        receipt["ordered_internal_records_sha256"]
        != reversed_receipt["ordered_internal_records_sha256"]
    )
    encoded = canonical_json_bytes(receipt)
    for forbidden in (
        b"primevul:",
        b"tokens_1",
        b"tokens_2",
        b"[7,7",
        b"edit_distance",
        b"zero_distance",
        b"collapsed_pairs",
    ):
        assert forbidden not in encoded
    assert receipt["training_authority"] is False
    assert receipt["held_out_data_present"] is False
    assert [
        row["max_common_tokens"] for row in receipt["policy"]["template_budgets"]
    ] == [512, 1024, 2048, 4096, 8192]


@pytest.mark.parametrize("n,m", [(True, 1), (-1, 1), (1.0, 1), (1, False), (1, "1")])
def test_invalid_dimensions_fail_closed(n, m) -> None:
    with pytest.raises(PairResourceCensusError):
        pair_resource_cost(n, m)


@pytest.mark.parametrize(
    "limits",
    [
        None,
        EditVisibilityLimits(True, 1, 1),
        EditVisibilityLimits(-1, 1, 1),
        EditVisibilityLimits(32_769, 1, 1),
        EditVisibilityLimits(1, 4_194_305, 1),
        EditVisibilityLimits(1, 1, 64 * 1024 * 1024 + 1),
    ],
)
def test_limits_never_relax_helper_ceilings(limits) -> None:
    with pytest.raises(PairResourceCensusError):
        _audit(limits=limits)


@pytest.mark.parametrize("cap", [True, 0, -1, 1.0, "1", 100_000_001])
def test_total_cap_is_positive_exact_integer_and_cannot_relax(cap) -> None:
    with pytest.raises(PairResourceCensusError):
        _audit(total_cell_cap=cap)


@pytest.mark.parametrize("bad_ids", [[True], [-1], [1.0], [], [99]])
def test_full_endpoint_token_validation_is_frozen(bad_ids) -> None:
    class _BadTokenizer(_LengthTokenizer):
        bos_token_id = 99

        def encode(self, text: str, *, add_special_tokens: bool) -> list[int]:
            if text.startswith("tokens_"):
                return bad_ids
            return super().encode(text, add_special_tokens=add_special_tokens)

    with pytest.raises(PairResourceCensusError):
        audit_retained_pair_resource_census(
            (_pair(1, 1, 1),),
            (),
            {"primevul:1", "primevul:2"},
            set(),
            {"primevul:1": "primevul:1", "primevul:2": "primevul:1"},
            _BadTokenizer(),
        )


def test_inconsistent_shared_endpoint_missing_root_and_duplicates_fail_closed() -> None:
    train = (_pair(1, 1, 1), ("primevul:1", "primevul:3", "tokens_2", "tokens_1"))
    with pytest.raises(PairResourceCensusError, match="shared endpoint"):
        _audit(train, roots={f"primevul:{i}": "primevul:1" for i in (1, 2, 3)})
    with pytest.raises(PairResourceCensusError, match="root"):
        _audit((_pair(1, 1, 1),), roots={})
    with pytest.raises(PairResourceCensusError, match="root"):
        _audit(
            (_pair(1, 1, 1),),
            roots={"primevul:1": "primevul:1", "primevul:2": "primevul:2"},
        )
    with pytest.raises(PairResourceCensusError, match="duplicate"):
        _audit((_pair(1, 1, 1), _pair(1, 1, 1)))


def test_fixture_runner_binds_all_roots_and_source_reverification(
    tmp_path: Path,
) -> None:
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)
    receipt = run_retained_pair_resource_census(
        full,
        paired,
        _ByteTokenizer(),
        model_inventory_sha256="a" * 64,
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
    )
    assert receipt["source_scope"] == "fixture"
    assert receipt["source_expectation"] == source_expectation.__dict__
    assert receipt["pair_expectation"] == pair_expectation.__dict__
    assert len(receipt["graph_ledgers"]) == 4
    assert receipt["retained_train_rows"] == 2
    assert receipt["retained_validation_rows"] == 2
    assert receipt["train"]["universe"]["pairs"] == 1
    assert receipt["validation"]["universe"]["pairs"] == 1
    assert "primevul:" not in str(receipt)
    assert "red blue" not in str(receipt)


@pytest.mark.parametrize("kind", ["source", "paired"])
def test_runner_rechecks_source_and_pair_bytes_after_scan(
    tmp_path: Path, kind: str
) -> None:
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)
    target = (
        (full / "primevul_train.jsonl")
        if kind == "source"
        else (paired / "primevul_train_paired.jsonl")
    )

    def change_after_scan(split: str, processed: int, total: int) -> None:
        if split == "validation" and processed == total:
            target.write_bytes(target.read_bytes().replace(b"red", b"RED", 1))

    with pytest.raises(ValueError):
        run_retained_pair_resource_census(
            full,
            paired,
            _ByteTokenizer(),
            model_inventory_sha256="a" * 64,
            source_expectation=source_expectation,
            pair_expectation=pair_expectation,
            census_progress=change_after_scan,
        )


@pytest.mark.parametrize(
    "kwargs",
    [{"total_cell_cap": 99_999_999}, {"limits": EditVisibilityLimits(1, 1, 1)}],
)
def test_pinned_runner_rejects_any_changed_production_limits_before_io(
    tmp_path: Path, kwargs
) -> None:
    with pytest.raises(PairResourceCensusError, match="pinned"):
        run_retained_pair_resource_census(
            tmp_path,
            tmp_path,
            _ByteTokenizer(),
            model_inventory_sha256="a" * 64,
            **kwargs,
        )


def test_census_rejects_empty_endpoint_dimensions_and_tokens() -> None:
    for n, m in ((0, 0), (0, 1), (1, 0)):
        with pytest.raises(PairResourceCensusError, match="positive"):
            pair_resource_cost(n, m)
    with pytest.raises(PairResourceCensusError):
        _audit((_pair(1, 0, 1),))


def test_normalized_whitespace_produces_same_full_token_commitments() -> None:
    roots = {"primevul:1": "primevul:1", "primevul:2": "primevul:1"}
    args = ((), {"primevul:1", "primevul:2"}, set(), roots, _ByteTokenizer())
    first = audit_retained_pair_resource_census(
        (("primevul:1", "primevul:2", "\r\nalpha  \r\nbeta\t\r\n", "safe \r\n"),), *args
    )
    second = audit_retained_pair_resource_census(
        (("primevul:1", "primevul:2", "alpha\nbeta", "safe"),), *args
    )
    assert (
        first["ordered_internal_records_sha256"]
        == second["ordered_internal_records_sha256"]
    )


@pytest.mark.parametrize("bad_code", ["\n\r\n\t", "\ud800"])
def test_unselected_malformed_author_endpoint_fails_closed(bad_code) -> None:
    with pytest.raises(PairResourceCensusError):
        _audit((("primevul:1", "primevul:2", bad_code, "safe"),), retained=set())


@pytest.mark.parametrize(
    "change", ["required-model", "extra-model", "tracked-code", "new-commit", "none"]
)
def test_terminal_model_and_clean_checkout_reverification_after_scan(
    tmp_path: Path, repository: Path, change: str
) -> None:
    snapshot, expectation = _snapshot(tmp_path)
    model_inventory = verify_model_snapshot(snapshot, expectation=expectation)[
        "inventory_sha256"
    ]
    checkout = inspect_clean_source_checkout(repository)
    _audit((_pair(1, 1, 1),))
    if change == "required-model":
        (snapshot / "tokenizer.json").write_bytes(b"changed")
    elif change == "extra-model":
        (snapshot / "README.md").write_bytes(b"new metadata")
    elif change == "tracked-code":
        (repository / "source.py").write_bytes(b"print('changed')\n")
    elif change == "new-commit":
        _git(repository, "commit", "--allow-empty", "--quiet", "-m", "changed HEAD")
    if change == "none":
        verify_terminal_census_state(
            snapshot,
            repository,
            model_inventory_sha256=model_inventory,
            source_checkout=checkout,
            snapshot_expectation=expectation,
        )
    else:
        with pytest.raises(ValueError):
            verify_terminal_census_state(
                snapshot,
                repository,
                model_inventory_sha256=model_inventory,
                source_checkout=checkout,
                snapshot_expectation=expectation,
            )


def test_imported_module_must_originate_in_recorded_checkout(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    expected = (
        checkout / "src" / "aluclu" / "alc_r0" / "retained_pair_resource_census.py"
    )
    expected.parent.mkdir(parents=True)
    expected.write_bytes(b"# fixture census module\n")
    verify_census_module_origin(checkout, expected)
    wrong = tmp_path / "other_module.py"
    wrong.write_bytes(expected.read_bytes())
    with pytest.raises(PairResourceCensusError, match="originate"):
        verify_census_module_origin(checkout, wrong)
    with pytest.raises(PairResourceCensusError, match="originate"):
        verify_census_module_origin(tmp_path, expected)
