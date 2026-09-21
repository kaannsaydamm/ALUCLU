from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

from aluclu.alc_r0.artifact_contract import build_run_artifact_contract
from aluclu.alc_r0.canonical import canonical_json_bytes, parse_canonical_json
from aluclu.alc_r0.schema_validation import (
    R0SchemaValidationError,
    validate_r0_document,
)

PROJECT_ROOT = Path(__file__).parents[1]
SCHEMA_ROOT = PROJECT_ROOT / "schemas" / "alc_r0" / "v1"
MATRIX_PATH = PROJECT_ROOT / "experiments" / "alc_r0" / "v1" / "logical-run-matrix.json"
CONTRACT_PATH = (
    PROJECT_ROOT / "experiments" / "alc_r0" / "v1" / "run-artifact-contract.json"
)


def _artifacts(contract: dict[str, object]) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], contract["artifacts"])


def test_run_artifact_contract_is_closed_over_every_matrix_filename() -> None:
    contract = build_run_artifact_contract(MATRIX_PATH.read_bytes())
    matrix = parse_canonical_json(MATRIX_PATH.read_bytes())
    matrix_filenames = {
        filename for row in matrix["runs"] for filename in row["expected_artifacts"]
    }
    declared_filenames = {item["filename"] for item in _artifacts(contract)}

    assert declared_filenames == matrix_filenames
    assert len(declared_filenames) == 20
    assert contract["logical_run_count"] == 280
    assert contract["training_authority"] is False
    assert contract["status"] == "run-namespace-frozen-non-authorizing"


def test_learned_artifact_is_safe_closed_and_required_for_all_training_runs() -> None:
    contract = build_run_artifact_contract(MATRIX_PATH.read_bytes())
    by_filename = {item["filename"]: item for item in _artifacts(contract)}
    learned = by_filename["learned-artifact.safetensors"]

    assert learned == {
        "artifact_type": "learned-artifact",
        "cardinality_per_run": 1,
        "expected_run_count": 120,
        "extension": ".safetensors",
        "filename": "learned-artifact.safetensors",
        "logical_id": {"mode": "constant", "value": "selected"},
        "media_type": "application/vnd.safetensors",
        "required_for_kinds": ["confirm-train", "dev-train", "pilot-train"],
    }


@pytest.mark.parametrize(
    "filename,field",
    [
        ("predictions.jsonl", "example_id"),
        ("likelihoods.jsonl", "example_id"),
        ("resource-samples.jsonl", "sample_id"),
        ("run-events.jsonl", "event_id"),
    ],
)
def test_jsonl_artifacts_require_explicit_record_logical_ids(
    filename: str, field: str
) -> None:
    contract = build_run_artifact_contract(MATRIX_PATH.read_bytes())
    by_filename = {item["filename"]: item for item in _artifacts(contract)}

    assert by_filename[filename]["logical_id"] == {
        "field": field,
        "mode": "record-field",
    }


def test_tracked_run_artifact_contract_is_reproducible_and_valid() -> None:
    expected = canonical_json_bytes(
        build_run_artifact_contract(MATRIX_PATH.read_bytes())
    )
    tracked = CONTRACT_PATH.read_bytes()

    assert tracked == expected
    assert validate_r0_document(
        tracked,
        schema_name="run-artifact-contract",
        schema_root=SCHEMA_ROOT,
    ) == parse_canonical_json(tracked)


@pytest.mark.parametrize("mutation", ["drop", "rename", "authority", "count"])
def test_run_artifact_contract_rejects_closed_world_mutations(mutation: str) -> None:
    contract = build_run_artifact_contract(MATRIX_PATH.read_bytes())
    if mutation == "drop":
        _artifacts(contract).pop()
    elif mutation == "rename":
        _artifacts(contract)[0]["filename"] = "undeclared.json"
    elif mutation == "authority":
        contract["training_authority"] = True
    else:
        contract["total_expected_file_count"] = 1

    with pytest.raises(R0SchemaValidationError):
        validate_r0_document(
            canonical_json_bytes(contract),
            schema_name="run-artifact-contract",
            schema_root=SCHEMA_ROOT,
        )
