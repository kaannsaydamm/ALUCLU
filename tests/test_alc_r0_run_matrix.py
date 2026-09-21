from __future__ import annotations

import re
from collections import Counter

from aluclu.alc_r0.run_matrix import build_expected_run_matrix

RUN_ID = re.compile(r"^alc-r0-v1-(pilot|dev|confirm|eval)-[a-z0-9-]+-s[0-9]{8}$")


def test_expected_run_matrix_has_exact_normative_cardinalities() -> None:
    matrix = build_expected_run_matrix()

    assert len(matrix) == 280
    assert Counter(row.kind for row in matrix) == {
        "attach-detach": 10,
        "base-digest": 40,
        "capsule-size": 10,
        "confirm-train": 40,
        "dev-train": 76,
        "fresh-remount": 10,
        "pilot-train": 4,
        "resource": 10,
        "retention-score": 22,
        "target-score": 58,
    }


def test_development_matrix_is_the_full_frozen_cartesian_product() -> None:
    matrix = build_expected_run_matrix()
    primary = [
        row
        for row in matrix
        if row.kind == "dev-train" and row.arm in {"capsule", "q-only-lora"}
    ]
    reference = [
        row for row in matrix if row.kind == "dev-train" and row.arm == "q-v-lora"
    ]

    assert len(primary) == 72
    assert {(row.family, row.arm, row.grid_id, row.seed) for row in primary} == {
        (family, arm, grid, seed)
        for family in ("banking77", "devign")
        for arm in ("capsule", "q-only-lora")
        for grid in (
            "l-r4",
            "l-r8",
            "l-r16",
            "m-r4",
            "m-r8",
            "m-r16",
            "ml-r4",
            "ml-r8",
            "ml-r16",
        )
        for seed in (20260917, 20260918)
    }
    assert len(reference) == 4
    assert all(row.grid_id == "all-r8" for row in reference)


def test_confirmatory_and_scoring_matrix_matches_preregistered_rows() -> None:
    matrix = build_expected_run_matrix()
    confirm = [row for row in matrix if row.kind == "confirm-train"]
    target = [row for row in matrix if row.kind == "target-score"]
    retention = [row for row in matrix if row.kind == "retention-score"]

    assert Counter(row.arm for row in confirm) == {
        "capsule": 10,
        "label-shuffled": 10,
        "q-only-lora": 10,
        "q-v-lora": 10,
    }
    assert Counter(row.arm for row in target) == {
        "base": 2,
        "capsule": 10,
        "label-shuffled": 10,
        "profile": 2,
        "q-only-lora": 10,
        "q-v-lora": 10,
        "rag": 2,
        "wrong-family": 10,
        "zero": 2,
    }
    assert Counter(row.arm for row in retention) == {"base": 2, "capsule": 20}
    assert all(row.grid_id == "selected" for row in confirm if row.arm != "q-v-lora")
    assert all(row.grid_id == "all-r8" for row in confirm if row.arm == "q-v-lora")


def test_run_ids_and_artifact_contracts_are_closed_and_deterministic() -> None:
    first = build_expected_run_matrix()
    second = build_expected_run_matrix()
    ids = [row.run_id for row in first]

    assert first == second
    assert ids == sorted(ids, key=lambda value: value.encode("utf-8"))
    assert len(ids) == len(set(ids))
    assert all(RUN_ID.fullmatch(run_id) for run_id in ids)
    assert all(row.expected_artifacts for row in first)
    assert all(
        tuple(sorted(row.expected_artifacts)) == row.expected_artifacts for row in first
    )
