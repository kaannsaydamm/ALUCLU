from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import aluclu.cli.benchmark_cognition_task2 as benchmark_module
from aluclu.cognition import (
    CanonicalJsonValue,
    InputBoundaryError,
)


def _passing_measurements() -> dict[str, Any]:
    return {
        "counts": [2_048, 4_096, 8_192],
        "payload_bytes": 512,
        "scan_samples_seconds": {
            "2048": [1.0, 1.1, 0.9],
            "4096": [2.0, 2.1, 1.9],
            "8192": [5.0, 5.1, 4.9],
        },
        "scan_records_by_count": {
            "2048": 2_048,
            "4096": 4_096,
            "8192": 8_192,
        },
        "rss_increment_bytes": {
            "2048": 32 * 1024 * 1024,
            "4096": 36 * 1024 * 1024,
            "8192": 40 * 1024 * 1024,
        },
        "rss_baseline_peak_bytes": 100 * 1024 * 1024,
        "peak_rss_bytes_by_count": {
            "2048": 132 * 1024 * 1024,
            "4096": 136 * 1024 * 1024,
            "8192": 140 * 1024 * 1024,
        },
        "direct_id_p95_seconds": 0.0018,
        "task1_read_p95_seconds": 0.001,
        "one_shot_result_digest": "a" * 64,
        "paged_result_digest": "a" * 64,
        "restarted_result_digest": "a" * 64,
        "logical": {
            "sensorium_state_bytes": 4_096,
            "query_bytes": 4_096,
            "current_feature_vector_bytes": 2_048,
            "retained_feature_vector_bytes": 65_536,
            "continuation_bytes": 128 * 1_024,
            "returned_payload_bytes": 262_144,
            "max_record_payload_bytes": 2 * 1024 * 1024,
            "top_k": 32,
            "candidates_returned": 32,
            "records_scanned": 8_192,
            "candidates_scored": 8_192,
        },
        "full_verification_delta": 0,
        "plaintext_sidecars": [],
        "duplicate_records": False,
        "persistent_bytes": 1,
    }


def test_fixed_thresholds_accept_exact_boundary_and_preserve_raw_samples() -> None:
    measurements = _passing_measurements()

    evidence = benchmark_module._threshold_evidence(measurements)

    assert evidence["fixed_gate_enforced"] is True
    assert evidence["passed"] is True
    assert evidence["ratios"]["scan_8192_to_4096"] == 2.5
    assert evidence["raw"]["scan_samples_seconds"] == (
        measurements["scan_samples_seconds"]
    )
    assert all(evidence["checks"].values())


@pytest.mark.parametrize(
    ("mutator", "failed_check"),
    [
        (
            lambda item: item["scan_samples_seconds"].__setitem__(
                "8192", [5.7, 5.6, 5.5]
            ),
            "scan_ratio_8192_to_4096",
        ),
        (
            lambda item: item["rss_increment_bytes"].__setitem__(
                "8192", 65 * 1024 * 1024
            ),
            "rss_8192_over_empty",
        ),
        (
            lambda item: item.__setitem__("rss_baseline_peak_bytes", 0),
            "rss_probe_available",
        ),
        (
            lambda item: item["peak_rss_bytes_by_count"].__setitem__(
                "8192", 99 * 1024 * 1024
            ),
            "rss_peaks_comparable_to_empty",
        ),
        (
            lambda item: item.__setitem__("direct_id_p95_seconds", 0.0021),
            "direct_id_p95_vs_task1_read",
        ),
        (
            lambda item: item.__setitem__("paged_result_digest", "b" * 64),
            "one_shot_equals_paged",
        ),
        (
            lambda item: item.__setitem__("restarted_result_digest", "c" * 64),
            "one_shot_equals_restarted",
        ),
        (
            lambda item: item["logical"].__setitem__(
                "returned_payload_bytes", 262_145
            ),
            "returned_payload_bytes",
        ),
        (
            lambda item: item.__setitem__("full_verification_delta", 1),
            "no_additional_full_verification",
        ),
    ],
)
def test_fixed_thresholds_fail_without_weakening_limits(
    mutator: Any,
    failed_check: str,
) -> None:
    measurements = _passing_measurements()
    mutator(measurements)

    evidence = benchmark_module._threshold_evidence(measurements)

    assert evidence["passed"] is False
    assert evidence["checks"][failed_check] is False
    assert evidence["limits"] == {
        "direct_id_p95_multiplier": 2.0,
        "max_candidates_returned": 32,
        "max_continuation_bytes": 131_072,
        "max_current_feature_vector_bytes": 2_048,
        "max_record_payload_bytes": 2_097_152,
        "max_retained_feature_vector_bytes": 65_536,
        "max_returned_payload_bytes": 262_144,
        "max_rss_8192_over_2048_bytes": 16_777_216,
        "max_rss_8192_over_empty_bytes": 67_108_864,
        "max_scan_ratio_8192_to_4096": 2.75,
        "max_sensorium_state_bytes": 4_096,
        "max_query_bytes": 4_096,
    }


def test_small_fixture_runs_actual_encrypted_records_without_fixed_gate(
    tmp_path: Path,
) -> None:
    benchmark_base = tmp_path / "local-state"
    work_dir = benchmark_base / "run"
    output = tmp_path / "result.json"

    result = benchmark_module._run_benchmark_impl(
        output=output,
        work_dir=work_dir,
        seed=17,
        counts=(4, 8, 16),
        payload_bytes=64,
        samples=1,
        benchmark_base_override=benchmark_base,
    )

    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert result == persisted
    assert result["success"] is True
    assert result["thresholds"]["fixed_gate_enforced"] is False
    assert result["counts"] == [4, 8, 16]
    assert result["payload_bytes"] == 64
    assert result["measurements"]["logical"]["records_scanned"] == 16
    assert result["measurements"]["scan_records_by_count"] == {
        "4": 4,
        "8": 8,
        "16": 16,
    }
    assert result["measurements"]["one_shot_result_digest"] == (
        result["measurements"]["paged_result_digest"]
    )
    assert result["measurements"]["one_shot_result_digest"] == (
        result["measurements"]["restarted_result_digest"]
    )
    assert result["measurements"]["content_payload_bytes"] == 64
    assert result["measurements"]["request_payload_bytes"] > 64
    assert (
        result["measurements"]["stored_observation_envelope_bytes"]
        > result["measurements"]["request_payload_bytes"]
    )
    assert result["environment"]["git"]["commit"]
    assert type(result["environment"]["git"]["dirty"]) is bool


def test_restarted_worker_full_verification_delta_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = benchmark_module._run_worker
    largest_one_shot_calls = 0

    def inject(**kwargs: Any) -> dict[str, Any]:
        nonlocal largest_one_shot_calls
        result = original(**kwargs)
        if (
            kwargs["mode"] == "scan"
            and kwargs["count"] == 16
            and kwargs["page_size"] == 16
        ):
            largest_one_shot_calls += 1
            if largest_one_shot_calls == 2:
                result = {**result, "full_verification_delta": 1}
        return result

    monkeypatch.setattr(benchmark_module, "_run_worker", inject)
    benchmark_base = tmp_path / "local-state"
    result = benchmark_module._run_benchmark_impl(
        output=tmp_path / "result.json",
        work_dir=benchmark_base / "run",
        seed=29,
        counts=(4, 8, 16),
        payload_bytes=64,
        samples=1,
        benchmark_base_override=benchmark_base,
    )

    assert largest_one_shot_calls == 2
    assert result["success"] is False
    assert result["measurements"]["full_verification_delta"] == 1
    assert result["thresholds"]["checks"]["no_additional_full_verification"] is False


def test_plaintext_sidecar_scan_detects_canonical_and_raw_content(
    tmp_path: Path,
) -> None:
    content = CanonicalJsonValue.from_value(
        benchmark_module._exact_json_string(seed=31, index=1, byte_count=64)
    )
    content_value = content.to_value()
    assert type(content_value) is str
    raw_content = content_value.encode("utf-8")
    (tmp_path / "content.txt").write_bytes(content.canonical_bytes)
    (tmp_path / "raw-content.txt").write_bytes(raw_content)

    findings = benchmark_module._plaintext_sidecars(
        tmp_path,
        sentinels=(content.canonical_bytes, raw_content),
    )

    assert findings == [
        "content.txt:plaintext-sentinel",
        "raw-content.txt:plaintext-sentinel",
    ]


def test_failure_atomically_replaces_stale_success_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    benchmark_base = tmp_path / "local-state"
    output = tmp_path / "result.json"
    output.write_text('{"success":true,"stale":true}\n', encoding="utf-8")

    def fail(*args: Any, **kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("injected scale failure")

    monkeypatch.setattr(benchmark_module, "_run_measurements", fail)

    with pytest.raises(RuntimeError, match="injected scale failure"):
        benchmark_module._run_benchmark_impl(
            output=output,
            work_dir=benchmark_base / "run",
            seed=19,
            counts=(4, 8, 16),
            payload_bytes=64,
            samples=1,
            benchmark_base_override=benchmark_base,
        )

    failure = json.loads(output.read_text(encoding="utf-8"))
    assert failure["success"] is False
    assert failure["error"] == {
        "message": "injected scale failure",
        "type": "RuntimeError",
    }
    assert "stale" not in failure


@pytest.mark.parametrize(
    ("counts", "payload_bytes", "samples"),
    [
        ((2_048, 4_096, 8_191), 512, 3),
        ((2_048, 4_096, 8_192), 511, 3),
        ((2_048, 4_096, 8_192), 512, 0),
    ],
)
def test_public_gate_rejects_non_normative_parameters_before_mutation(
    tmp_path: Path,
    counts: tuple[int, int, int],
    payload_bytes: int,
    samples: int,
) -> None:
    output = tmp_path / "result.json"
    work_dir = tmp_path / "run"

    with pytest.raises(InputBoundaryError):
        benchmark_module.run_benchmark(
            output=output,
            work_dir=work_dir,
            seed=23,
            counts=counts,
            payload_bytes=payload_bytes,
            samples=samples,
        )

    assert not output.exists()
    assert not work_dir.exists()
