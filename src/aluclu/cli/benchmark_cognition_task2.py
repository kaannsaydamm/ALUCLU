from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
import time
import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import aluclu.cognition.recollection as recollection_module
from aluclu.cli.benchmark_cognition_ledger import (
    _environment,
    _main_disk_bytes,
    _process_memory_bytes,
    _repository_root,
    _require_fresh_work_root,
    _require_work_root_boundary,
    _write_json,
)
from aluclu.cli.benchmark_cognition_ledger import (
    local_benchmark_root as _task1_local_benchmark_root,
)
from aluclu.cognition import (
    ApproximateCandidates,
    CanonicalJsonValue,
    ConflictedRecollection,
    EncryptedLedger,
    EventIdRecallQuery,
    ExactRecollection,
    FileKeyProvider,
    IncompleteRecollection,
    IngestStatus,
    InputBoundaryError,
    ObservationAcceptedV1,
    ObservationRequestV1,
    ProvenanceV1,
    RecallExecutionPolicyV1,
    SensoriumStateV1,
    SourceKind,
    TextRecallQuery,
    active_feature_spec_id,
    active_normalizer_id,
    baseline_boundary_profile,
    canonical_json_bytes,
    encode_canonical_observation,
    encode_retrieval_text,
    encode_sensorium_state,
    ingest_observation,
    initialize_empty_sensorium_state,
    observation_request_to_json_value,
    recall,
)
from aluclu.cognition.contracts import JsonValue
from aluclu.cognition.ledger import VerifiedLedgerSession
from aluclu.cognition.recollection import RecollectionWorkV1

_PROTOCOL_ID = "aluclu.cognition.task2.scale.v1"
_FIXED_COUNTS = (2_048, 4_096, 8_192)
_FIXED_PAYLOAD_BYTES = 512
_DEFAULT_SAMPLES = 3
_MAX_SCAN_RATIO = 2.75
_MAX_RSS_OVER_EMPTY = 64 * 1024 * 1024
_MAX_RSS_OVER_2048 = 16 * 1024 * 1024
_MAX_SENSORIUM_STATE_BYTES = 4_096
_MAX_QUERY_BYTES = 4_096
_MAX_CURRENT_FEATURE_VECTOR_BYTES = 2_048
_MAX_RETAINED_FEATURE_VECTOR_BYTES = 64 * 1_024
_MAX_CONTINUATION_BYTES = 128 * 1_024
_MAX_RETURNED_PAYLOAD_BYTES = 262_144
_MAX_RECORD_PAYLOAD_BYTES = 2 * 1024 * 1024
_MAX_TOP_K = 32
_DIRECT_P95_MULTIPLIER = 2.0
_WORKER_TIMEOUT_SECONDS = 3_600.0
_BENCHMARK_MARKER = "task2-scale-private-marker"


def local_benchmark_root(run_id: str | None = None) -> Path:
    """Return a fresh-run path below the unsynchronised benchmark state root."""

    suffix = run_id or (
        f"task2-{time.strftime('%Y%m%d-%H%M%S')}-{os.getpid()}-"
        f"{uuid.uuid4().hex[:8]}"
    )
    return _task1_local_benchmark_root(suffix)


def run_benchmark(
    *,
    output: str | Path,
    work_dir: str | Path,
    seed: int,
    counts: tuple[int, int, int] = _FIXED_COUNTS,
    payload_bytes: int = _FIXED_PAYLOAD_BYTES,
    samples: int = _DEFAULT_SAMPLES,
) -> dict[str, Any]:
    """Run the fixed Task 2 scale gate and atomically persist canonical JSON."""

    _require_public_gate(counts, payload_bytes, samples)
    return _run_benchmark_impl(
        output=output,
        work_dir=work_dir,
        seed=seed,
        counts=counts,
        payload_bytes=payload_bytes,
        samples=samples,
        benchmark_base_override=None,
    )


def _run_benchmark_impl(
    *,
    output: str | Path,
    work_dir: str | Path,
    seed: int,
    counts: tuple[int, int, int],
    payload_bytes: int,
    samples: int,
    benchmark_base_override: Path | None,
) -> dict[str, Any]:
    safe_counts = _validated_counts(counts)
    safe_payload_bytes = _validated_payload_bytes(payload_bytes)
    safe_samples = _validated_samples(samples)
    safe_seed = _exact_int(seed, "seed")
    output_path = Path(output).expanduser().resolve(strict=False)
    work_root = Path(work_dir).expanduser().resolve(strict=False)
    _require_work_root_boundary(
        work_root,
        test_only_benchmark_base=benchmark_base_override,
    )
    _require_fresh_work_root(work_root)

    try:
        work_root.mkdir(parents=True, exist_ok=True)
        measurements = _run_measurements(
            work_root=work_root,
            seed=safe_seed,
            counts=safe_counts,
            payload_bytes=safe_payload_bytes,
            samples=safe_samples,
        )
        thresholds = _threshold_evidence(measurements)
        result: dict[str, Any] = {
            "protocol_id": _PROTOCOL_ID,
            "success": thresholds["passed"],
            "counts": list(safe_counts),
            "payload_bytes": safe_payload_bytes,
            "samples": safe_samples,
            "seed": safe_seed,
            "measurements": measurements,
            "thresholds": thresholds,
            "environment": _environment(work_root),
            "paths": {
                "work_dir": str(work_root),
                "output": str(output_path),
                "local_benchmark_root": str(local_benchmark_root("<run-id>")),
            },
            "algorithm": {
                "ledger_api": "VerifiedLedgerSession.cursor",
                "recall_api": "aluclu.cognition.recall",
                "materializes_full_ledger": False,
                "persistent_plaintext_index": False,
                "one_process_per_measured_scan": True,
            },
        }
        _write_json(output_path, result)
        return result
    except Exception as primary:
        failure = {
            "protocol_id": _PROTOCOL_ID,
            "success": False,
            "counts": list(safe_counts),
            "payload_bytes": safe_payload_bytes,
            "samples": safe_samples,
            "seed": safe_seed,
            "paths": {"work_dir": str(work_root), "output": str(output_path)},
            "error": {"type": type(primary).__name__, "message": str(primary)},
        }
        try:
            _write_json(output_path, failure)
        except Exception as cleanup:
            raise primary.with_traceback(primary.__traceback__) from cleanup
        raise


def _run_measurements(
    *,
    work_root: Path,
    seed: int,
    counts: tuple[int, int, int],
    payload_bytes: int,
    samples: int,
) -> dict[str, Any]:
    ledger_path = work_root / "cognition.sqlite3"
    key_path = work_root / "cognition.master.key"
    empty_ledger_path = work_root / "empty.sqlite3"
    empty_key_path = work_root / "empty.master.key"
    profile = baseline_boundary_profile()
    largest = counts[-1]
    largest_envelope_bytes = 0
    largest_request_bytes = 0
    final_state_bytes = 0
    duplicate_records = False
    plaintext_sentinels: set[bytes] = {_BENCHMARK_MARKER.encode("ascii")}

    state: SensoriumStateV1 | None = None
    previous_count = 0

    with EncryptedLedger(
        empty_ledger_path,
        FileKeyProvider(empty_key_path, create=True),
    ):
        pass

    empty = _run_worker(
        mode="baseline",
        ledger_path=empty_ledger_path,
        key_path=empty_key_path,
        count=0,
        page_size=0,
        samples=1,
        seed=seed,
    )
    baseline_peak = _required_int(empty, "peak_rss_bytes")
    scan_samples: dict[str, list[float]] = {}
    scan_records: dict[str, int] = {}
    scan_peaks: dict[str, int] = {}
    rss_increments: dict[str, int] = {}
    one_shot_digest = ""
    paged_digest = ""
    restarted_digest = ""
    direct_p95 = 0.0
    read_p95 = 0.0
    maximum_work: Mapping[str, Any] = {}
    maximum_continuation_bytes = 0
    maximum_full_verification_delta = 0

    for count in counts:
        # Grow one physical encrypted ledger only as far as this checkpoint.
        # The isolated worker below consequently observes an exact-N head.
        with EncryptedLedger(
            ledger_path, FileKeyProvider(key_path, create=True)
        ) as ledger:
            with ledger.verified_session() as session:
                if state is None:
                    initialized = initialize_empty_sensorium_state(session, profile)
                    if type(initialized) is not SensoriumStateV1:
                        raise RuntimeError("empty sensorium state was not initialized")
                    state = initialized
                if session.event_count() != previous_count:
                    raise RuntimeError("ledger checkpoint count changed unexpectedly")
                for index in range(previous_count + 1, count + 1):
                    request = _observation_request(
                        index=index,
                        seed=seed,
                        payload_bytes=payload_bytes,
                    )
                    if index in {1, count, largest}:
                        plaintext_sentinels.add(request.content.canonical_bytes)
                        content_value = request.content.to_value()
                        if type(content_value) is not str:
                            raise RuntimeError("benchmark content is not a string")
                        plaintext_sentinels.add(content_value.encode("utf-8"))
                    largest_request_bytes = max(
                        largest_request_bytes,
                        len(
                            canonical_json_bytes(
                                cast(
                                    JsonValue,
                                    observation_request_to_json_value(request),
                                )
                            )
                        ),
                    )
                    accepted = ingest_observation(
                        session,
                        request,
                        profile,
                        state,
                    )
                    if type(accepted) is not ObservationAcceptedV1:
                        raise RuntimeError(f"observation {index} was not accepted")
                    duplicate_records = (
                        duplicate_records
                        or accepted.status is not IngestStatus.APPLIED
                    )
                    state = accepted.next_state
                    largest_envelope_bytes = max(
                        largest_envelope_bytes,
                        len(
                            encode_canonical_observation(
                                accepted.stored_observation
                            )
                        ),
                    )
                if session.event_count() != count:
                    raise RuntimeError(
                        "observation count does not match ledger event count"
                    )
                final_state_bytes = len(encode_sensorium_state(state))

        scan = _run_worker(
            mode="scan",
            ledger_path=ledger_path,
            key_path=key_path,
            count=count,
            page_size=count,
            samples=samples,
            seed=seed,
        )
        scan_samples[str(count)] = _required_float_list(scan, "samples_seconds")
        scan_work = _required_mapping(scan, "work")
        scan_records[str(count)] = _required_int(scan_work, "records_scanned")
        scan_peak = _required_int(scan, "peak_rss_bytes")
        scan_peaks[str(count)] = scan_peak
        rss_increments[str(count)] = max(0, scan_peak - baseline_peak)
        maximum_full_verification_delta = max(
            maximum_full_verification_delta,
            _required_int(scan, "full_verification_delta"),
        )
        if count == largest:
            one_shot_digest = _required_str(scan, "result_digest")
            direct_p95 = _required_float(scan, "direct_id_p95_seconds")
            read_p95 = _required_float(scan, "task1_read_p95_seconds")
            maximum_work = scan_work
        previous_count = count

    paged = _run_worker(
        mode="scan",
        ledger_path=ledger_path,
        key_path=key_path,
        count=largest,
        page_size=max(1, counts[0]),
        samples=1,
        seed=seed,
    )
    paged_digest = _required_str(paged, "result_digest")
    maximum_continuation_bytes = _required_int(paged, "max_continuation_bytes")
    maximum_full_verification_delta = max(
        maximum_full_verification_delta,
        _required_int(paged, "full_verification_delta"),
    )
    # This is a separate fresh process. It does not receive or serialize a
    # RecallContinuationV1; it starts at sequence zero and independently
    # reproduces the one-shot result at the same frozen ledger head.
    restarted = _run_worker(
        mode="scan",
        ledger_path=ledger_path,
        key_path=key_path,
        count=largest,
        page_size=largest,
        samples=1,
        seed=seed,
    )
    restarted_digest = _required_str(restarted, "result_digest")
    maximum_full_verification_delta = max(
        maximum_full_verification_delta,
        _required_int(restarted, "full_verification_delta"),
    )

    key_store = ledger_path.with_suffix(ledger_path.suffix + ".record-keys")
    disk = _main_disk_bytes(ledger_path, key_store)
    plaintext_sidecars = _plaintext_sidecars(
        work_root,
        sentinels=tuple(sorted(plaintext_sentinels)),
    )
    return {
        "counts": list(counts),
        "payload_bytes": payload_bytes,
        "content_payload_bytes": payload_bytes,
        "request_payload_bytes": largest_request_bytes,
        "stored_observation_envelope_bytes": largest_envelope_bytes,
        "scan_samples_seconds": scan_samples,
        "scan_records_by_count": scan_records,
        "rss_baseline_peak_bytes": baseline_peak,
        "peak_rss_bytes_by_count": scan_peaks,
        "rss_increment_bytes": rss_increments,
        "direct_id_p95_seconds": direct_p95,
        "task1_read_p95_seconds": read_p95,
        "one_shot_result_digest": one_shot_digest,
        "paged_result_digest": paged_digest,
        "restarted_result_digest": restarted_digest,
        "logical": {
            "sensorium_state_bytes": final_state_bytes,
            "query_bytes": len(canonical_json_bytes(_query_text(largest))),
            "current_feature_vector_bytes": len(
                encode_retrieval_text(
                    _query_text(largest),
                    feature_spec_id=active_feature_spec_id(),
                ).bins_i16be
            ),
            "retained_feature_vector_bytes": 0,
            "continuation_bytes": maximum_continuation_bytes,
            "returned_payload_bytes": _required_int(
                maximum_work, "output_bytes"
            ),
            "max_record_payload_bytes": largest_envelope_bytes,
            "top_k": _MAX_TOP_K,
            "candidates_returned": _required_int(
                maximum_work, "candidates_returned"
            ),
            "records_scanned": _required_int(maximum_work, "records_scanned"),
            "candidates_scored": _required_int(
                maximum_work, "candidates_scored"
            ),
        },
        "full_verification_delta": maximum_full_verification_delta,
        "plaintext_sidecars": plaintext_sidecars,
        "duplicate_records": duplicate_records,
        "persistent_bytes": disk["total"],
        "persistent_breakdown_bytes": disk,
    }


def _threshold_evidence(measurements: Mapping[str, Any]) -> dict[str, Any]:
    counts = measurements.get("counts")
    payload_bytes = measurements.get("payload_bytes")
    fixed_gate = counts == list(_FIXED_COUNTS) and payload_bytes == 512
    if type(counts) is not list or len(counts) != 3:
        raise RuntimeError("benchmark measurement counts are invalid")
    low_key, middle_key, high_key = (str(item) for item in counts)
    samples = _required_mapping(measurements, "scan_samples_seconds")
    medians = {
        name: statistics.median(_float_sequence(value, f"scan samples {name}"))
        for name, value in samples.items()
    }
    scan_ratio = _ratio(medians.get(high_key), medians.get(middle_key))
    rss = _required_mapping(measurements, "rss_increment_bytes")
    rss_baseline = _required_int(measurements, "rss_baseline_peak_bytes")
    rss_peaks = _required_mapping(measurements, "peak_rss_bytes_by_count")
    rss_low = _mapping_int(rss, low_key)
    rss_high = _mapping_int(rss, high_key)
    direct_p95 = _required_float(measurements, "direct_id_p95_seconds")
    read_p95 = _required_float(measurements, "task1_read_p95_seconds")
    logical = _required_mapping(measurements, "logical")
    scan_records = _required_mapping(measurements, "scan_records_by_count")
    limits = {
        "direct_id_p95_multiplier": _DIRECT_P95_MULTIPLIER,
        "max_candidates_returned": _MAX_TOP_K,
        "max_continuation_bytes": _MAX_CONTINUATION_BYTES,
        "max_current_feature_vector_bytes": _MAX_CURRENT_FEATURE_VECTOR_BYTES,
        "max_record_payload_bytes": _MAX_RECORD_PAYLOAD_BYTES,
        "max_retained_feature_vector_bytes": _MAX_RETAINED_FEATURE_VECTOR_BYTES,
        "max_returned_payload_bytes": _MAX_RETURNED_PAYLOAD_BYTES,
        "max_rss_8192_over_2048_bytes": _MAX_RSS_OVER_2048,
        "max_rss_8192_over_empty_bytes": _MAX_RSS_OVER_EMPTY,
        "max_scan_ratio_8192_to_4096": _MAX_SCAN_RATIO,
        "max_sensorium_state_bytes": _MAX_SENSORIUM_STATE_BYTES,
        "max_query_bytes": _MAX_QUERY_BYTES,
    }
    base_checks = {
        "counts_strictly_increasing": (
            type(counts) is list
            and all(type(item) is int for item in counts)
            and all(left < right for left, right in zip(counts, counts[1:]))
        ),
        "positive_samples": bool(medians)
        and all(math.isfinite(item) and item > 0 for item in medians.values()),
        "positive_persistent_bytes": (
            _required_int(measurements, "persistent_bytes") > 0
        ),
        "rss_probe_available": rss_baseline > 0
        and all(
            _mapping_int(rss_peaks, str(count)) > 0 for count in counts
        ),
        "rss_peaks_comparable_to_empty": all(
            _mapping_int(rss_peaks, str(count)) >= rss_baseline
            for count in counts
        ),
        "no_duplicate_records": measurements.get("duplicate_records") is False,
        "no_plaintext_sidecars": measurements.get("plaintext_sidecars") == [],
        "no_additional_full_verification": (
            _required_int(measurements, "full_verification_delta") == 0
        ),
        "exact_checkpoint_scan_counts": all(
            _mapping_int(scan_records, str(count)) == count for count in counts
        ),
    }
    fixed_checks = {
        "fixed_counts": counts == list(_FIXED_COUNTS),
        "fixed_payload_bytes": payload_bytes == _FIXED_PAYLOAD_BYTES,
        "scan_ratio_8192_to_4096": (
            scan_ratio is not None and scan_ratio <= _MAX_SCAN_RATIO
        ),
        "rss_8192_over_empty": rss_high <= _MAX_RSS_OVER_EMPTY,
        "rss_8192_over_2048": rss_high <= rss_low + _MAX_RSS_OVER_2048,
        "direct_id_p95_vs_task1_read": (
            read_p95 > 0 and direct_p95 <= _DIRECT_P95_MULTIPLIER * read_p95
        ),
        "one_shot_equals_paged": (
            measurements.get("one_shot_result_digest")
            == measurements.get("paged_result_digest")
        ),
        "one_shot_equals_restarted": (
            measurements.get("one_shot_result_digest")
            == measurements.get("restarted_result_digest")
        ),
        "sensorium_state_bytes": (
            _mapping_int(logical, "sensorium_state_bytes")
            <= _MAX_SENSORIUM_STATE_BYTES
        ),
        "query_bytes": _mapping_int(logical, "query_bytes") <= _MAX_QUERY_BYTES,
        "current_feature_vector_bytes": (
            _mapping_int(logical, "current_feature_vector_bytes")
            <= _MAX_CURRENT_FEATURE_VECTOR_BYTES
        ),
        "retained_feature_vector_bytes": (
            _mapping_int(logical, "retained_feature_vector_bytes")
            <= _MAX_RETAINED_FEATURE_VECTOR_BYTES
        ),
        "continuation_bytes": (
            _mapping_int(logical, "continuation_bytes") <= _MAX_CONTINUATION_BYTES
        ),
        "returned_payload_bytes": (
            _mapping_int(logical, "returned_payload_bytes")
            <= _MAX_RETURNED_PAYLOAD_BYTES
        ),
        "record_payload_bytes": (
            _mapping_int(logical, "max_record_payload_bytes")
            <= _MAX_RECORD_PAYLOAD_BYTES
        ),
        "top_k": _mapping_int(logical, "top_k") <= _MAX_TOP_K,
        "candidates_returned": (
            _mapping_int(logical, "candidates_returned") <= _MAX_TOP_K
        ),
        "records_scanned": _mapping_int(logical, "records_scanned") == 8_192,
        "candidates_scored": (
            _mapping_int(logical, "candidates_scored") == 8_192
        ),
    }
    checks = {**base_checks, **fixed_checks}
    passed = all(base_checks.values()) and (
        not fixed_gate or all(fixed_checks.values())
    )
    return {
        "passed": passed,
        "fixed_gate_enforced": fixed_gate,
        "limits": limits,
        "ratios": {"scan_8192_to_4096": scan_ratio},
        "medians_seconds": medians,
        "checks": checks,
        "raw": {
            "scan_samples_seconds": samples,
            "rss_baseline_peak_bytes": rss_baseline,
            "peak_rss_bytes_by_count": rss_peaks,
            "rss_increment_bytes": rss,
            "direct_id_p95_seconds": direct_p95,
            "task1_read_p95_seconds": read_p95,
        },
    }


def _observation_request(
    *, index: int, seed: int, payload_bytes: int
) -> ObservationRequestV1:
    return ObservationRequestV1(
        observation_id=f"obs:task2-scale-{index:08d}",
        session_id="session:task2-scale",
        turn_id=f"turn:task2-scale-{index:08d}",
        provenance=ProvenanceV1(
            source_kind=SourceKind.USER,
            source_instance_id="user:task2-scale",
            origin_id=f"fixture:task2-scale-{seed}-{index:08d}",
            observed_at_ns=1_725_000_000_000_000_000 + index,
            parent_observation_ids=(),
            capture_method="task2-scale-benchmark",
            capture_version="1.0.0",
        ),
        content=CanonicalJsonValue.from_value(
            _exact_json_string(seed=seed, index=index, byte_count=payload_bytes)
        ),
        retrieval_text=_query_text(index),
        topic_key="topic:task2-scale",
        goal_ids=(),
        participant_ids=("participant:user",),
        tool_invocation_id=None,
        tool_phase=None,
        force_boundary=False,
    )


def _exact_json_string(*, seed: int, index: int, byte_count: int) -> str:
    text_bytes = byte_count - 2
    digest = hashlib.sha256(f"{seed}:{index}".encode("ascii")).hexdigest()
    value = (digest * ((text_bytes + len(digest) - 1) // len(digest)))[:text_bytes]
    if len(canonical_json_bytes(value)) != byte_count:
        raise RuntimeError("benchmark content payload is not exact size")
    return value


def _query_text(index: int) -> str:
    return f"{_BENCHMARK_MARKER} {index:08d}"


def _run_worker(
    *,
    mode: str,
    ledger_path: Path,
    key_path: Path,
    count: int,
    page_size: int,
    samples: int,
    seed: int,
) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "aluclu.cli.benchmark_cognition_task2",
            "--worker",
            mode,
            "--ledger-path",
            str(ledger_path),
            "--key-path",
            str(key_path),
            "--worker-count",
            str(count),
            "--page-size",
            str(page_size),
            "--samples",
            str(samples),
            "--seed",
            str(seed),
        ],
        cwd=_repository_root(),
        capture_output=True,
        text=True,
        timeout=_WORKER_TIMEOUT_SECONDS,
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "Task 2 benchmark worker failed: "
            f"exit={completed.returncode}; stderr={completed.stderr.strip()}"
        )
    try:
        decoded = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Task 2 benchmark worker returned invalid JSON") from exc
    if type(decoded) is not dict:
        raise RuntimeError("Task 2 benchmark worker result is not an object")
    return cast(dict[str, Any], decoded)


def _worker_baseline(ledger_path: Path, key_path: Path) -> dict[str, Any]:
    with EncryptedLedger(
        ledger_path, FileKeyProvider(key_path, create=False)
    ) as ledger:
        with ledger.verified_session() as session:
            if session.event_count() != 0:
                raise RuntimeError("baseline ledger is not empty")
            peak = _process_memory_bytes()["peak"]
    return {"peak_rss_bytes": peak}


def _worker_scan(
    ledger_path: Path,
    key_path: Path,
    *,
    count: int,
    page_size: int,
    samples: int,
    seed: int,
) -> dict[str, Any]:
    del seed
    policy = _recall_policy(page_size)
    query = TextRecallQuery(text=_query_text(count))
    sample_seconds: list[float] = []
    result: ApproximateCandidates | ConflictedRecollection | None = None
    max_continuation_bytes = 0
    direct_samples: list[float] = []
    read_samples: list[float] = []
    with EncryptedLedger(
        ledger_path, FileKeyProvider(key_path, create=False)
    ) as ledger:
        with ledger.verified_session() as session:
            if session.event_count() != count:
                raise RuntimeError("scan worker ledger head does not equal count")
            before_verifications = ledger.verification_stats.full_verifications
            for _ in range(samples):
                started = time.perf_counter_ns()
                measured, continuation_bytes = _complete_recall(
                    session, query, policy=policy
                )
                sample_seconds.append(_seconds(time.perf_counter_ns() - started))
                max_continuation_bytes = max(
                    max_continuation_bytes, continuation_bytes
                )
                result = measured
            if count == session.event_count():
                direct_samples, read_samples = _direct_read_samples(session, count)
            after_verifications = ledger.verification_stats.full_verifications
        peak = _process_memory_bytes()["peak"]
    if result is None:
        raise RuntimeError("scan produced no result")
    work = result.work
    return {
        "samples_seconds": sample_seconds,
        "peak_rss_bytes": peak,
        "result_digest": _result_digest(result),
        "max_continuation_bytes": max_continuation_bytes,
        "full_verification_delta": after_verifications - before_verifications,
        "direct_id_p95_seconds": _p95(direct_samples),
        "task1_read_p95_seconds": _p95(read_samples),
        "work": _work_json(work),
    }


def _complete_recall(
    session: VerifiedLedgerSession,
    query: TextRecallQuery,
    *,
    policy: RecallExecutionPolicyV1,
) -> tuple[ApproximateCandidates | ConflictedRecollection, int]:
    current = recall(session, query, policy=policy)
    max_continuation_bytes = 0
    while type(current) is IncompleteRecollection:
        continuation = current.continuation
        continuation_bytes = len(
            canonical_json_bytes(
                cast(
                    JsonValue,
                    recollection_module._continuation_payload(continuation),
                )
            )
        )
        max_continuation_bytes = max(max_continuation_bytes, continuation_bytes)
        current = recall(
            session,
            query,
            policy=policy,
            continuation=continuation,
        )
    if not isinstance(current, (ApproximateCandidates, ConflictedRecollection)):
        raise RuntimeError(f"unexpected scale recollection: {type(current).__name__}")
    return current, max_continuation_bytes


def _direct_read_samples(
    session: VerifiedLedgerSession, count: int
) -> tuple[list[float], list[float]]:
    sample_count = min(64, count)
    indices = [1 + (offset * max(1, count - 1)) // max(1, sample_count - 1) for offset in range(sample_count)]
    direct: list[float] = []
    reads: list[float] = []
    for offset, index in enumerate(indices):
        observation_id = f"obs:task2-scale-{index:08d}"
        if offset % 2 == 0:
            direct_elapsed, exact = _measure_direct(session, observation_id)
            read_elapsed, record = _measure_read(session, observation_id)
        else:
            read_elapsed, record = _measure_read(session, observation_id)
            direct_elapsed, exact = _measure_direct(session, observation_id)
        direct.append(direct_elapsed)
        reads.append(read_elapsed)
        if type(exact) is not ExactRecollection:
            raise RuntimeError("direct-ID benchmark did not return exact recollection")
        if record is None:
            raise RuntimeError("Task 1 read baseline did not find observation")
    return direct, reads


def _measure_direct(
    session: VerifiedLedgerSession, observation_id: str
) -> tuple[float, ExactRecollection | object]:
    started = time.perf_counter_ns()
    result = recall(session, EventIdRecallQuery(observation_id=observation_id))
    return _seconds(time.perf_counter_ns() - started), result


def _measure_read(
    session: VerifiedLedgerSession, observation_id: str
) -> tuple[float, object | None]:
    started = time.perf_counter_ns()
    result = session.read(observation_id)
    return _seconds(time.perf_counter_ns() - started), result


def _recall_policy(max_records: int) -> RecallExecutionPolicyV1:
    return RecallExecutionPolicyV1(
        max_records=max_records,
        top_k=_MAX_TOP_K,
        max_returned_payload_bytes=_MAX_RETURNED_PAYLOAD_BYTES,
        active_normalizer_id=active_normalizer_id(),
        active_feature_spec_id=active_feature_spec_id(),
        minimum_score_q32=0,
        minimum_margin_q32=0,
        allow_approximate=True,
        allow_incomplete=True,
    )


def _result_digest(result: ApproximateCandidates | ConflictedRecollection) -> str:
    payload = {
        "type": type(result).__name__,
        "margin_q32": result.margin_q32,
        "candidates": [
            {
                "observation_id": item.observation_id,
                "episode_id": item.episode_id,
                "sequence": item.sequence,
                "record_hash": item.record_hash,
                "content_digest": item.content_digest,
                "score_q32": item.score_q32,
                "content_omitted": item.content_omitted,
            }
            for item in result.candidates
        ],
        "work": _work_json(result.work),
    }
    return hashlib.sha256(canonical_json_bytes(cast(JsonValue, payload))).hexdigest()


def _work_json(work: RecollectionWorkV1) -> dict[str, JsonValue]:
    return {
        "records_scanned": work.records_scanned,
        "canonical_payload_bytes_decoded": work.canonical_payload_bytes_decoded,
        "candidates_scored": work.candidates_scored,
        "candidates_returned": work.candidates_returned,
        "output_bytes": work.output_bytes,
        "exhaustive": work.exhaustive,
    }


def _plaintext_sidecars(
    root: Path, *, sentinels: Sequence[bytes]
) -> list[str]:
    if not sentinels or any(type(item) is not bytes or not item for item in sentinels):
        raise RuntimeError("plaintext sentinels must be non-empty bytes")
    findings: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            body = path.read_bytes()
            if any(sentinel in body for sentinel in sentinels):
                findings.append(f"{path.relative_to(root)}:plaintext-sentinel")
        except OSError:
            findings.append(f"{path.relative_to(root)}:unreadable")
    return sorted(findings)


def _require_public_gate(
    counts: tuple[int, int, int], payload_bytes: int, samples: int
) -> None:
    if counts != _FIXED_COUNTS:
        raise InputBoundaryError("public Task 2 benchmark counts are fixed")
    if payload_bytes != _FIXED_PAYLOAD_BYTES:
        raise InputBoundaryError("public Task 2 benchmark payload size is fixed")
    _validated_samples(samples)


def _validated_counts(value: tuple[int, int, int]) -> tuple[int, int, int]:
    if type(value) is not tuple or len(value) != 3:
        raise InputBoundaryError("counts must contain exactly three integers")
    if any(type(item) is not int or item < 1 or item > 8_192 for item in value):
        raise InputBoundaryError("counts are outside the supported range")
    if not value[0] < value[1] < value[2]:
        raise InputBoundaryError("counts must be strictly increasing")
    return value


def _validated_payload_bytes(value: int) -> int:
    result = _exact_int(value, "payload_bytes")
    if not 2 <= result <= _FIXED_PAYLOAD_BYTES:
        raise InputBoundaryError("payload_bytes is outside the supported range")
    return result


def _validated_samples(value: int) -> int:
    result = _exact_int(value, "samples")
    if not 1 <= result <= 10:
        raise InputBoundaryError("samples must be between one and ten")
    return result


def _exact_int(value: int, label: str) -> int:
    if type(value) is not int:
        raise InputBoundaryError(f"{label} must be an integer")
    return value


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def _seconds(nanoseconds: int) -> float:
    return max(1, nanoseconds) / 1_000_000_000


def _p95(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[math.ceil(0.95 * len(ordered)) - 1]


def _required_mapping(value: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    item = value.get(key)
    if not isinstance(item, Mapping):
        raise RuntimeError(f"benchmark measurement {key} is not an object")
    return item


def _required_int(value: Mapping[str, Any], key: str) -> int:
    item = value.get(key)
    if type(item) is not int:
        raise RuntimeError(f"benchmark measurement {key} is not an integer")
    return item


def _mapping_int(value: Mapping[str, Any], key: str) -> int:
    return _required_int(value, key)


def _required_float(value: Mapping[str, Any], key: str) -> float:
    item = value.get(key)
    if not isinstance(item, (int, float)) or isinstance(item, bool):
        raise RuntimeError(f"benchmark measurement {key} is not numeric")
    result = float(item)
    if not math.isfinite(result) or result < 0:
        raise RuntimeError(f"benchmark measurement {key} is invalid")
    return result


def _required_str(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if type(item) is not str or not item:
        raise RuntimeError(f"benchmark measurement {key} is not a string")
    return item


def _float_sequence(value: Any, label: str) -> list[float]:
    if type(value) is not list or not value:
        raise RuntimeError(f"{label} must be a nonempty array")
    return [_coerce_float(item, label) for item in value]


def _required_float_list(value: Mapping[str, Any], key: str) -> list[float]:
    return _float_sequence(value.get(key), key)


def _coerce_float(value: Any, label: str) -> float:
    if type(value) not in {int, float} or isinstance(value, bool):
        raise RuntimeError(f"{label} contains a nonnumeric value")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise RuntimeError(f"{label} contains an invalid value")
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the fixed ALUCLU Task 2 cognition scale gate."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/cognition_task2_scale.json"),
    )
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--seed", type=int, default=20260916)
    parser.add_argument("--samples", type=int, default=_DEFAULT_SAMPLES)
    parser.add_argument("--worker", choices=("baseline", "scan"), help=argparse.SUPPRESS)
    parser.add_argument("--ledger-path", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--key-path", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--worker-count", type=int, default=0, help=argparse.SUPPRESS)
    parser.add_argument("--page-size", type=int, default=0, help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)
    if args.worker is not None:
        if args.ledger_path is None or args.key_path is None:
            raise InputBoundaryError("worker ledger and key paths are required")
        if args.worker == "baseline":
            result = _worker_baseline(args.ledger_path, args.key_path)
        else:
            result = _worker_scan(
                args.ledger_path,
                args.key_path,
                count=args.worker_count,
                page_size=args.page_size,
                samples=args.samples,
                seed=args.seed,
            )
        sys.stdout.buffer.write(canonical_json_bytes(cast(JsonValue, result)) + b"\n")
        return
    work_dir = args.work_dir or local_benchmark_root()
    result = run_benchmark(
        output=args.output,
        work_dir=work_dir,
        seed=args.seed,
        samples=args.samples,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["success"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
