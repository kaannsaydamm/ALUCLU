"""Closed-world run-artifact contract for the preregistered ALC-R0 matrix."""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from typing import Any

from aluclu.alc_r0.canonical import parse_canonical_json
from aluclu.alc_r0.run_matrix import (
    SOURCE_PLAN_PATH,
    SOURCE_PLAN_SHA256,
    build_expected_run_matrix,
)

EXPERIMENT_ID = "alc-r0-smollm2-135m-v1"
MATRIX_PATH = "experiments/alc_r0/v1/logical-run-matrix.json"

_JSONL_LOGICAL_IDS = {
    "likelihoods.jsonl": "example_id",
    "predictions.jsonl": "example_id",
    "resource-samples.jsonl": "sample_id",
    "run-events.jsonl": "event_id",
}
_MEDIA_TYPES = {
    ".json": "application/json",
    ".jsonl": "application/x-ndjson",
    ".log": "text/plain;charset=utf-8",
    ".safetensors": "application/vnd.safetensors",
}


class ArtifactContractError(ValueError):
    """Raised when the logical matrix cannot support a closed artifact contract."""


def _extension(filename: str) -> str:
    for extension in sorted(_MEDIA_TYPES, key=len, reverse=True):
        if filename.endswith(extension):
            return extension
    raise ArtifactContractError(f"unsupported run artifact extension: {filename}")


def _logical_id_contract(filename: str, extension: str) -> dict[str, str]:
    field = _JSONL_LOGICAL_IDS.get(filename)
    if field is not None:
        return {"field": field, "mode": "record-field"}
    if extension == ".jsonl":
        raise ArtifactContractError(f"JSONL logical-ID rule is missing: {filename}")
    if extension == ".safetensors":
        return {"mode": "constant", "value": "selected"}
    if extension == ".log":
        return {"mode": "constant", "value": "stream"}
    return {"mode": "constant", "value": "document"}


def _validated_rows(matrix_bytes: bytes) -> list[dict[str, Any]]:
    matrix = parse_canonical_json(matrix_bytes)
    if not isinstance(matrix, dict):
        raise ArtifactContractError("logical matrix root must be an object")
    expected_rows = [row.to_json() for row in build_expected_run_matrix()]
    if matrix.get("experiment_id") != EXPERIMENT_ID:
        raise ArtifactContractError("logical matrix experiment mismatch")
    if matrix.get("source_plan_path") != SOURCE_PLAN_PATH:
        raise ArtifactContractError("logical matrix source-plan path mismatch")
    if matrix.get("source_plan_sha256") != SOURCE_PLAN_SHA256:
        raise ArtifactContractError("logical matrix source-plan digest mismatch")
    if matrix.get("training_authority") is not False:
        raise ArtifactContractError("logical matrix must remain non-authorizing")
    if matrix.get("logical_run_count") != len(expected_rows):
        raise ArtifactContractError("logical matrix count mismatch")
    rows = matrix.get("runs")
    if rows != expected_rows:
        raise ArtifactContractError("logical matrix rows differ from preregistration")
    return expected_rows


def build_run_artifact_contract(matrix_bytes: bytes) -> dict[str, object]:
    """Derive the exact allowed run-file namespace from the frozen run matrix."""

    rows = _validated_rows(matrix_bytes)
    counts: Counter[str] = Counter()
    kinds: defaultdict[str, set[str]] = defaultdict(set)
    for row in rows:
        kind = row["kind"]
        artifacts = row["expected_artifacts"]
        if not isinstance(kind, str) or not isinstance(artifacts, list):
            raise ArtifactContractError("logical matrix row shape mismatch")
        for filename in artifacts:
            if not isinstance(filename, str):
                raise ArtifactContractError("artifact filename must be a string")
            counts[filename] += 1
            kinds[filename].add(kind)

    artifacts: list[dict[str, object]] = []
    for filename in sorted(counts, key=lambda item: item.encode("utf-8")):
        extension = _extension(filename)
        artifacts.append(
            {
                "artifact_type": filename[: -len(extension)],
                "cardinality_per_run": 1,
                "expected_run_count": counts[filename],
                "extension": extension,
                "filename": filename,
                "logical_id": _logical_id_contract(filename, extension),
                "media_type": _MEDIA_TYPES[extension],
                "required_for_kinds": sorted(
                    kinds[filename], key=lambda item: item.encode("utf-8")
                ),
            }
        )

    return {
        "allowed_extensions": sorted(
            _MEDIA_TYPES, key=lambda item: item.encode("utf-8")
        ),
        "artifacts": artifacts,
        "contract_version": 1,
        "experiment_id": EXPERIMENT_ID,
        "logical_run_count": len(rows),
        "matrix": {
            "byte_length": len(matrix_bytes),
            "relative_path": MATRIX_PATH,
            "sha256": hashlib.sha256(matrix_bytes).hexdigest(),
        },
        "namespace": "run",
        "primary_key": ["run_id", "artifact_type", "logical_id"],
        "run_path_template": (
            "results/alc_r0/{phase}/{run_id}/{artifact_type}.{extension}"
        ),
        "schema_id": (
            "https://aluclu.org/schemas/alc_r0/v1/run-artifact-contract.schema.json"
        ),
        "schema_version": 1,
        "source_plan_path": SOURCE_PLAN_PATH,
        "source_plan_sha256": SOURCE_PLAN_SHA256,
        "status": "run-namespace-frozen-non-authorizing",
        "total_expected_file_count": sum(counts.values()),
        "training_authority": False,
    }
