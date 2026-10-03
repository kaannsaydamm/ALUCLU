from dataclasses import replace
from itertools import product

import pytest
from test_alc_r0_edit_token_visibility_reference import _oracle
from test_alc_r0_paired_prompt_contrast import _ByteTokenizer

from aluclu.alc_r0.banded_edit_token_visibility_reference import (
    BandedEditVisibilityLimits,
    audit_banded_edit_token_visibility,
)
from aluclu.alc_r0.banded_pair_resource_census import audit_banded_pair_resource_census
from aluclu.alc_r0.canonical import canonical_json_bytes
from aluclu.alc_r0.full_development_banded_edit_exposure import (
    EditExposureError,
    audit_full_development_banded_edit_exposure,
    validate_completed_result,
)


class Tokenizer(_ByteTokenizer):
    def encode(self, text, *, add_special_tokens):
        if text.startswith("ids:"):
            return [int(v) for v in text[4:].split(",")]
        return super().encode(text, add_special_tokens=add_special_tokens)


class Backend:
    def __init__(self, transform=lambda value: value):
        self.calls = 0
        self.verified = False
        self.transform = transform

    def audit(self, first, second, **kwargs):
        self.calls += 1
        return self.transform(
            audit_banded_edit_token_visibility(first, second, **kwargs)
        )

    def verify_terminal(self):
        self.verified = True


def pair(index, a, b):
    return (
        f"primevul:{index}",
        f"primevul:{index + 1}",
        "ids:" + ",".join(map(str, a)),
        "ids:" + ",".join(map(str, b)),
    )


def audit(
    train=(),
    validation=(),
    *,
    tokenizer=None,
    backend=None,
    expected=None,
    retained=None,
    roots=None,
    **kwargs,
):
    tok = tokenizer or Tokenizer()
    ids = tuple({v for row in rows for v in row[:2]} for rows in (train, validation))
    if retained is not None:
        ids = retained
    roots = roots or {v: row[0] for row in train + validation for v in row[:2]}
    policy = {
        key: kwargs[key] for key in ("distance_threshold", "limits") if key in kwargs
    }
    geometry = audit_banded_pair_resource_census(
        train, validation, *ids, roots, Tokenizer(), **policy
    )
    backend = backend or Backend()
    loaded = []

    def factory():
        loaded.append(True)
        return backend

    result = audit_full_development_banded_edit_exposure(
        train,
        validation,
        *ids,
        roots,
        tok,
        expected_geometry=geometry if expected is None else expected,
        backend_factory=factory,
        **kwargs,
    )
    return result, backend, loaded


def test_zero_positive_and_unresolved_denominators_direct_joint():
    rows = (pair(0, (1, 2), (2, 1)), pair(2, (7,), (7,)), pair(4, (1, 2), (8, 9)))
    out, backend, loaded = audit(
        rows, distance_threshold=2, code_budgets=(1, 2, 3, 4, 5)
    )
    s = out["train"]
    assert s["strata"]["universe"]["pairs"] == 3
    assert s["strata"]["exact_positive_distance"]["pairs"] == 1
    assert s["strata"]["exact_zero_distance"]["pairs"] == 1
    assert s["strata"]["terminal_threshold_unresolved"]["pairs"] == 1
    budget = s["budget_exposure"][0]
    assert budget["pairs"] == 1
    assert budget["sums"]["total_min"] == budget["sums"]["total_max"] == 1
    assert budget["joint_signature_histogram"]["6"] == 1
    assert budget["mean_pair_total_min_fraction"] == 0.5
    assert backend.calls == 3 and backend.verified and len(loaded) == 1
    assert out["training_authority"] is False and out["held_out_data_present"] is False


def test_empty_all_zero_and_all_unresolved_have_null_ratios():
    for rows, threshold in [
        ((), 0),
        ((pair(0, (7,), (7,)),), 0),
        ((pair(0, (1,), (2,)),), 0),
    ]:
        out, _, _ = audit(rows, distance_threshold=threshold)
        for budget in out["train"]["budget_exposure"]:
            assert budget["pairs"] == 0
            assert budget["mean_pair_total_min_fraction"] is None
            assert sum(budget["joint_signature_histogram"].values()) == 0


def test_permanent_first_nonfit_no_skip_across_splits():
    out, backend, _ = audit(
        (pair(0, (7,), (7,)), pair(2, (7, 7), (7, 7))),
        (pair(4, (7,), (7,)),),
        distance_threshold=0,
        total_cell_cap=3,
    )
    assert backend.calls == 1
    assert out["admission"] == dict(
        scheduled_band_cells=2, remaining_band_cells=1, exhausted=True
    )
    assert out["train"]["strata"]["global_cap_unresolved"]["pairs"] == 1
    assert out["validation"]["strata"]["global_cap_unresolved"]["pairs"] == 1


def test_geometry_mismatch_fails_before_factory():
    with pytest.raises(EditExposureError, match="prepass"):
        audit((pair(0, (7,), (7,)),), expected={})


def test_second_pass_same_length_token_change_rejects_digest():
    class Changing(Tokenizer):
        def __init__(self):
            self.calls = 0

        def encode(self, text, **kwargs):
            value = super().encode(text, **kwargs)
            if text.startswith("ids:"):
                self.calls += 1
                if self.calls > 2:
                    value = [v + 1 for v in value]
            return value

    with pytest.raises(EditExposureError, match="second-pass"):
        audit((pair(0, (1, 2), (2, 1)),), tokenizer=Changing())


@pytest.mark.parametrize(
    "field,value",
    [
        ("first_tokens", True),
        ("distance_threshold", False),
        ("visited_band_cells", 0),
        ("training_authority", True),
        ("held_out_data_present", 0),
        ("edit_distance", True),
        ("allocated_packed_payload_bytes", 0),
        ("status", "success"),
        ("reason", "bad"),
        ("requested_code_budgets", (1, 2, 3, 4, 5)),
        ("scheduled_band_cells", 999),
    ],
)
def test_malformed_backend_result_rejected(field, value):
    backend = Backend(lambda r: replace(r, **{field: value}))
    with pytest.raises(EditExposureError):
        audit((pair(0, (1,), (2,)),), backend=backend)


def test_budget_corruption_and_infrastructure_not_unresolved():
    def corruption(r):
        return replace(r, budgets=(replace(r.budgets[0], total_min=0),) + r.budgets[1:])

    with pytest.raises(EditExposureError):
        audit((pair(0, (1,), (2,)),), backend=Backend(corruption))

    class Broken(Backend):
        def audit(self, *args, **kwargs):
            raise RuntimeError("transport")

    with pytest.raises(RuntimeError, match="transport"):
        audit((pair(0, (1,), (2,)),), backend=Broken())


def test_tiny_oracle_all_five_slots_and_completed_validation():
    for a in product((1, 2), repeat=2):
        for b in product((1, 2), repeat=2):
            budgets = (1, 2, 3, 4, 5)
            result = audit_banded_edit_token_visibility(
                a, b, code_budgets=budgets, distance_threshold=4
            )
            validate_completed_result(
                result, a, b, budgets, 4, BandedEditVisibilityLimits()
            )
            for budget, row in zip(budgets, result.budgets, strict=True):
                d, x, y, t, j = _oracle(a, b, budget)
                assert (
                    result.edit_distance,
                    row.first_min,
                    row.first_max,
                    row.second_min,
                    row.second_max,
                    row.total_min,
                    row.total_max,
                    row.joint_signature_bits,
                ) == (d, *x, *y, *t, j)


def test_local_unknown_zero_and_survival_root_unions_no_raw_leak():
    rows = (pair(0, (7,) * 4, (7,)), pair(2, (7,), (7, 7)), pair(4, (7,), (7,)))
    limits = BandedEditVisibilityLimits(max_endpoint_tokens=3)
    out, backend, _ = audit(rows, limits=limits, distance_threshold=0)
    assert backend.calls == 1
    assert out["train"]["preflight_unresolved_reasons"] == {
        "endpoint-token-limit": 1,
        "distance-threshold-exceeded": 1,
        "band-cell-limit": 0,
        "scratch-byte-limit": 0,
    }
    assert out["train"]["strata"]["universe"]["unknown_geometry_pairs"] == 1
    raw = canonical_json_bytes(out)
    assert b"primevul:" not in raw and b"ids:" not in raw


@pytest.mark.parametrize("cap", [True, 0, -1, 3000000001])
def test_cannot_relax_new_workload_cap(cap):
    with pytest.raises(EditExposureError):
        audit(total_cell_cap=cap)


def test_unresolved_result_requires_tuple_budget_contract():
    backend = Backend(
        lambda r: replace(r, requested_code_budgets=list(r.requested_code_budgets))
    )
    with pytest.raises(EditExposureError):
        audit((pair(0, (1,), (2,)),), distance_threshold=0, backend=backend)


def test_backend_cannot_claim_identical_pair_exceeds_threshold():
    def false_unresolved(r):
        return replace(
            r,
            status="resource-unresolved-non-authorizing",
            reason="distance-threshold-exceeded",
            edit_distance=None,
            budgets=(),
        )

    with pytest.raises(EditExposureError):
        audit(
            (pair(0, (7,), (7,)),),
            distance_threshold=0,
            backend=Backend(false_unresolved),
        )


def test_terminal_backend_failure_prevents_returning_receipt():
    class Changed(Backend):
        def verify_terminal(self):
            raise RuntimeError("artifact changed")

    with pytest.raises(RuntimeError, match="artifact changed"):
        audit((pair(0, (7,), (7,)),), backend=Changed())


def test_snapshot_survival_all_categories_and_overlapping_roots():
    rows = tuple(pair(i, (7,), (7,)) for i in (0, 2, 4, 6))
    retained = ({"primevul:0", "primevul:1", "primevul:2", "primevul:5"}, set())
    roots = {v: "primevul:0" for row in rows for v in row[:2]}
    out, backend, _ = audit(rows, retained=retained, roots=roots)
    assert out["train"]["survival"] == dict(
        author_pairs=4,
        both_retained=1,
        vulnerable_only_retained=1,
        safe_only_retained=1,
        neither_retained=1,
    )
    assert out["train"]["components"]["universe"] == 1 and backend.calls == 1


@pytest.mark.parametrize("exposed", [0, 2])
def test_impossible_retained_mask_capacity_rejected(exposed):
    def corruption(result):
        first = replace(
            result.budgets[0],
            first_min=exposed,
            first_max=exposed,
            second_min=exposed,
            second_max=exposed,
            total_min=2 * exposed,
            total_max=2 * exposed,
            joint_signature_bits=8 if exposed else 1,
        )
        return replace(result, budgets=(first,) + result.budgets[1:])

    with pytest.raises(EditExposureError):
        audit(
            (pair(0, (1, 2, 3), (8, 9, 10)),),
            backend=Backend(corruption),
            code_budgets=(1, 2, 3, 4, 5),
        )
