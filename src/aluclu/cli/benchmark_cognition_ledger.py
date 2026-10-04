from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import math
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import uuid
from collections.abc import Callable, Mapping
from functools import lru_cache
from importlib import metadata
from pathlib import Path
from typing import Any, cast

from cryptography import __version__ as cryptography_version

from aluclu.cognition import (
    EncryptedLedger,
    FileKeyProvider,
    InputBoundaryError,
    VerifiedLedgerSession,
    atomic_write_bytes,
    canonical_json_bytes,
)
from aluclu.cognition.codec import MAX_PAYLOAD_BYTES
from aluclu.cognition.contracts import JsonValue

_PROTOCOL_ID = "aluclu_cognition_ledger_scale_v1"
_FIXED_GATE_TURNS = 8192
_FIXED_GATE_PAYLOAD_BYTES = 512
_DEFAULT_CONTENTION_HOLD_SECONDS = 0.25
_CONTENTTION_TIMEOUT_SECONDS = 10.0
_MAX_CONTENTION_HOLD_SECONDS = 5.0
_RSS_LIMIT_BYTES = 256 * 1024 * 1024
_DISK_LIMIT_BYTES = 128 * 1024 * 1024
_RATIO_LIMIT = 1.75
_POLL_SECONDS = 0.005

AppendHook = Callable[[VerifiedLedgerSession, str, JsonValue], None]


def local_benchmark_root(run_id: str | None = None) -> Path:
    """Return an unsynchronised application-state path without creating it."""

    suffix = run_id or (
        f"task1d-{time.strftime('%Y%m%d-%H%M%S')}-{os.getpid()}-"
        f"{uuid.uuid4().hex[:8]}"
    )
    if type(suffix) is not str or not suffix or suffix in {".", ".."}:
        raise InputBoundaryError("benchmark run id is invalid")
    if "/" in suffix or "\\" in suffix:
        raise InputBoundaryError("benchmark run id must be one path component")
    return _benchmark_base() / suffix


def run_benchmark(
    *,
    turns: int,
    payload_bytes: int,
    output: str | Path,
    work_dir: str | Path,
    seed: int,
    contention_hold_seconds: float = _DEFAULT_CONTENTION_HOLD_SECONDS,
) -> dict[str, Any]:
    """Run one fresh production-directory ledger benchmark and persist evidence."""

    return _run_benchmark_impl(
        turns=turns,
        payload_bytes=payload_bytes,
        output=output,
        work_dir=work_dir,
        seed=seed,
        contention_hold_seconds=contention_hold_seconds,
        append_hook=None,
        benchmark_base_override=None,
    )


def _run_benchmark_impl(
    *,
    turns: int,
    payload_bytes: int,
    output: str | Path,
    work_dir: str | Path,
    seed: int,
    contention_hold_seconds: float,
    append_hook: AppendHook | None,
    benchmark_base_override: Path | None,
) -> dict[str, Any]:
    safe_turns = _validated_turns(turns)
    safe_payload_bytes = _validated_payload_bytes(payload_bytes)
    safe_seed = _exact_int(seed, label="seed")
    safe_hold = _validated_hold_seconds(contention_hold_seconds)
    output_path = Path(output).expanduser().resolve(strict=False)
    work_root = Path(work_dir).expanduser().resolve(strict=False)
    _require_work_root_boundary(
        work_root,
        test_only_benchmark_base=benchmark_base_override,
    )
    _require_fresh_work_root(work_root)

    try:
        work_root.mkdir(parents=True, exist_ok=True)
        result = _run_validated_benchmark(
            turns=safe_turns,
            payload_bytes=safe_payload_bytes,
            output=output_path,
            work_root=work_root,
            seed=safe_seed,
            append_hook=append_hook,
            contention_hold_seconds=safe_hold,
        )
        _write_json(output_path, result)
        return result
    except Exception as primary:
        failure = {
            "protocol_id": _PROTOCOL_ID,
            "success": False,
            "turns": safe_turns,
            "payload_bytes": safe_payload_bytes,
            "seed": safe_seed,
            "paths": {
                "work_dir": str(work_root),
                "output": str(output_path),
            },
            "error": {
                "type": type(primary).__name__,
                "message": str(primary),
            },
        }
        try:
            _write_json(output_path, failure)
        except Exception as cleanup:
            if cleanup.__context__ is primary:
                cleanup.__context__ = primary.__cause__
            raise primary.with_traceback(primary.__traceback__) from cleanup
        raise


def _run_validated_benchmark(
    *,
    turns: int,
    payload_bytes: int,
    output: Path,
    work_root: Path,
    seed: int,
    append_hook: AppendHook | None,
    contention_hold_seconds: float,
) -> dict[str, Any]:
    ledger_path = work_root / "cognition.sqlite3"
    key_path = work_root / "cognition.master.key"
    record_key_store = ledger_path.with_suffix(
        ledger_path.suffix + ".record-keys"
    )
    memory_before = _process_memory_bytes()
    quartile_seconds: list[float] = []
    quartile_counts: list[int] = []
    records_seen = 0
    duplicates_detected = False
    final_event_count = 0
    cursor_scan_records = 0
    cursor_scan_seconds = 0.0
    full_verifications = 0
    delta_verifications = 0
    disk_bytes: dict[str, int] = {}

    with EncryptedLedger(
        ledger_path,
        FileKeyProvider(key_path, create=True),
    ) as ledger:
        with ledger.verified_session() as session:
            for start, end in _bucket_ranges(turns, 4):
                payloads = [
                    _deterministic_payload(
                        seed=seed,
                        index=index,
                        payload_bytes=payload_bytes,
                    )
                    for index in range(start, end)
                ]
                started_ns = time.perf_counter_ns()
                for offset, payload in enumerate(payloads):
                    index = start + offset
                    event_id = f"turn-{index + 1:08d}"
                    if append_hook is None:
                        outcome = session.append(event_id, payload)
                        if not outcome.created:
                            duplicates_detected = True
                    else:
                        append_hook(session, event_id, payload)
                    records_seen += 1
                elapsed_ns = time.perf_counter_ns() - started_ns
                quartile_seconds.append(_positive_seconds(elapsed_ns))
                quartile_counts.append(end - start)
            final_event_count = session.event_count()

        ledger.verify_integrity()
        cursor_started_ns = time.perf_counter_ns()
        with ledger.verified_session() as session:
            cursor_scan_records = sum(1 for _ in session.cursor(batch_size=64))
        cursor_scan_seconds = _positive_seconds(
            time.perf_counter_ns() - cursor_started_ns
        )
        stats = ledger.verification_stats
        full_verifications = stats.full_verifications
        delta_verifications = stats.delta_verifications
        disk_bytes = _main_disk_bytes(ledger_path, record_key_store)

    contention = _measure_contention(
        work_root / "contention",
        hold_seconds=contention_hold_seconds,
    )
    environment = _environment(work_root)
    memory_after = _process_memory_bytes()

    per_append = [
        seconds / count
        for seconds, count in zip(quartile_seconds, quartile_counts, strict=True)
    ]
    first_half_seconds = sum(quartile_seconds[:2])
    second_half_seconds = sum(quartile_seconds[2:])
    first_half_count = sum(quartile_counts[:2])
    second_half_count = sum(quartile_counts[2:])
    first_half_per_append = first_half_seconds / first_half_count
    second_half_per_append = second_half_seconds / second_half_count
    fourth_first_ratio = _finite_ratio(per_append[3], per_append[0])
    second_first_half_ratio = _finite_ratio(
        second_half_per_append,
        first_half_per_append,
    )
    peak_delta = max(0, memory_after["peak"] - memory_before["peak"])

    thresholds = _threshold_evidence(
        turns=turns,
        payload_bytes=payload_bytes,
        records_seen=records_seen,
        final_event_count=final_event_count,
        duplicates_detected=duplicates_detected,
        cursor_scan_records=cursor_scan_records,
        full_verifications=full_verifications,
        quartile_per_append=per_append,
        first_half_per_append=first_half_per_append,
        second_half_per_append=second_half_per_append,
        fourth_first_ratio=fourth_first_ratio,
        second_first_half_ratio=second_first_half_ratio,
        peak_rss=memory_after["peak"],
        peak_rss_delta=peak_delta,
        disk_total=disk_bytes["total"],
        contention=contention,
    )
    result: dict[str, Any] = {
        "protocol_id": _PROTOCOL_ID,
        "success": thresholds["passed"],
        "turns": turns,
        "payload_bytes": payload_bytes,
        "seed": seed,
        "records_seen": records_seen,
        "final_event_count": final_event_count,
        "duplicates_detected": duplicates_detected,
        "append_total_seconds": sum(quartile_seconds),
        "quartile_seconds": quartile_seconds,
        "quartile_counts": quartile_counts,
        "quartile_per_append_seconds": per_append,
        "half_seconds": [first_half_seconds, second_half_seconds],
        "half_per_append_seconds": [
            first_half_per_append,
            second_half_per_append,
        ],
        "fourth_first_quartile_ratio": fourth_first_ratio,
        "second_first_half_ratio": second_first_half_ratio,
        "full_verifications": full_verifications,
        "delta_verifications": delta_verifications,
        "cursor_scan_seconds": cursor_scan_seconds,
        "cursor_scan_records": cursor_scan_records,
        "rss_bytes": {
            "before_current": memory_before["current"],
            "before_peak": memory_before["peak"],
            "after_current": memory_after["current"],
            "peak": memory_after["peak"],
            "peak_delta": peak_delta,
            "limit": _RSS_LIMIT_BYTES,
        },
        "disk_bytes": {
            **disk_bytes,
            "limit": _DISK_LIMIT_BYTES,
        },
        "contention": contention,
        "thresholds": thresholds,
        "interfaces": {
            "ledger_api": "EncryptedLedger.verified_session",
            "record_key_store": "DirectoryRecordKeyStore",
        },
        "paths": {
            "work_dir": str(work_root),
            "ledger": str(ledger_path),
            "record_key_store": str(record_key_store),
            "master_key": str(key_path),
            "output": str(output),
            "local_benchmark_root": str(local_benchmark_root("<run-id>")),
        },
        "environment": environment,
        "note": (
            "Deterministic exact-size payload generation is outside timed "
            "quartiles. Torch and GPU are inventory only; the persistence loop "
            "uses the production directory record-key backend."
        ),
    }
    return result


def _threshold_evidence(
    *,
    turns: int,
    payload_bytes: int,
    records_seen: int,
    final_event_count: int,
    duplicates_detected: bool,
    cursor_scan_records: int,
    full_verifications: int,
    quartile_per_append: list[float],
    first_half_per_append: float,
    second_half_per_append: float,
    fourth_first_ratio: float | None,
    second_first_half_ratio: float | None,
    peak_rss: int,
    peak_rss_delta: int,
    disk_total: int,
    contention: Mapping[str, Any],
) -> dict[str, Any]:
    fixed_gate = (
        turns == _FIXED_GATE_TURNS
        and payload_bytes == _FIXED_GATE_PAYLOAD_BYTES
    )
    base_checks = {
        "append_count": records_seen == turns,
        "event_count": final_event_count == turns,
        "no_duplicates": not duplicates_detected,
        "cursor_count": cursor_scan_records == turns,
        "full_verifications": full_verifications <= 2,
        "positive_quartiles": all(value > 0.0 for value in quartile_per_append),
        "positive_rss": peak_rss > 0,
        "positive_disk": disk_total > 0,
        "contention_ready": contention["attempt_signal_received"] is True,
        "contention_writer_ready": contention["writer_ready"] is True,
        "contention_blocked": (
            contention["writer_completed_while_held"] is False
        ),
        "contention_exit": contention["writer_exit_code"] == 0,
        "contention_timeout": contention["writer_timed_out"] is False,
        "contention_visible": contention["child_record_visible"] is True,
        "contention_count": contention["final_event_count"] == 2,
        "contention_hold": (
            type(contention["session_hold_seconds"]) is float
            and contention["session_hold_seconds"] > 0.0
        ),
        "contention_total_wait": (
            type(contention["writer_total_wait_seconds"]) is float
            and contention["writer_total_wait_seconds"]
            >= contention["session_hold_seconds"]
        ),
        "contention_release": (
            type(contention["release_to_completion_seconds"]) is float
            and 0.0 < contention["release_to_completion_seconds"]
            <= _CONTENTTION_TIMEOUT_SECONDS
        ),
    }
    fixed_checks = {
        "fixed_turns": turns == _FIXED_GATE_TURNS,
        "fixed_payload_bytes": payload_bytes == _FIXED_GATE_PAYLOAD_BYTES,
        "fourth_first_ratio": (
            fourth_first_ratio is not None
            and fourth_first_ratio <= _RATIO_LIMIT
        ),
        "second_first_half_ratio": (
            second_first_half_ratio is not None
            and second_first_half_ratio <= _RATIO_LIMIT
        ),
        "peak_rss_delta": peak_rss_delta <= _RSS_LIMIT_BYTES,
        "disk_total": disk_total <= _DISK_LIMIT_BYTES,
    }
    passed = all(base_checks.values()) and (
        not fixed_gate or all(fixed_checks.values())
    )
    return {
        "passed": passed,
        "fixed_gate_enforced": fixed_gate,
        "limits": {
            "max_full_verifications": 2,
            "max_fourth_first_quartile_ratio": _RATIO_LIMIT,
            "max_second_first_half_ratio": _RATIO_LIMIT,
            "max_peak_rss_delta_bytes": _RSS_LIMIT_BYTES,
            "max_disk_bytes": _DISK_LIMIT_BYTES,
            "contention_release_timeout_seconds": _CONTENTTION_TIMEOUT_SECONDS,
        },
        "raw": {
            "turns": turns,
            "payload_bytes": payload_bytes,
            "records_seen": records_seen,
            "final_event_count": final_event_count,
            "full_verifications": full_verifications,
            "quartile_per_append_seconds": quartile_per_append,
            "first_half_per_append_seconds": first_half_per_append,
            "second_half_per_append_seconds": second_half_per_append,
            "fourth_first_quartile_ratio": fourth_first_ratio,
            "second_first_half_ratio": second_first_half_ratio,
            "peak_rss_bytes": peak_rss,
            "peak_rss_delta_bytes": peak_rss_delta,
            "disk_total_bytes": disk_total,
        },
        "base_checks": base_checks,
        "fixed_gate_checks": fixed_checks,
    }


def _measure_contention(root: Path, *, hold_seconds: float) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=False)
    ledger_path = root / "contention.sqlite3"
    key_path = root / "contention.master.key"
    ready_path = root / "writer-ready.json"
    start_path = root / "writer-start.json"
    attempt_path = root / "writer-attempt.json"
    done_path = root / "writer-done.json"

    process: subprocess.Popen[str] | None = None
    ready_received = False
    attempt_received = False
    completed_while_held = False
    writer_timed_out = False
    held_event_count = 0
    release_ns = 0
    completion_ns = 0
    stdout = ""
    stderr = ""

    with EncryptedLedger(
        ledger_path,
        FileKeyProvider(key_path, create=True),
    ) as ledger:
        with ledger.verified_session() as session:
            session.append("contention-parent", "parent")

        process = _start_contention_child(
            ledger_path=ledger_path,
            key_path=key_path,
            ready_path=ready_path,
            start_path=start_path,
            attempt_path=attempt_path,
            done_path=done_path,
        )
        ready_received = _wait_for_file(
            ready_path,
            process=process,
            timeout=_CONTENTTION_TIMEOUT_SECONDS,
        )

        hold_started_ns = time.perf_counter_ns()
        if ready_received:
            with ledger.verified_session() as session:
                _write_json(start_path, {"start": True})
                attempt_received = _wait_for_file(
                    attempt_path,
                    process=process,
                    timeout=_CONTENTTION_TIMEOUT_SECONDS,
                )
                hold_started_ns = time.perf_counter_ns()
                if attempt_received:
                    time.sleep(hold_seconds)
                completed_while_held = (
                    done_path.exists() or process.poll() is not None
                )
                held_event_count = session.event_count()
            release_ns = time.perf_counter_ns()
        else:
            release_ns = time.perf_counter_ns()

        try:
            stdout, stderr = process.communicate(
                timeout=_CONTENTTION_TIMEOUT_SECONDS
            )
        except subprocess.TimeoutExpired:
            writer_timed_out = True
            process.kill()
            stdout, stderr = process.communicate(timeout=5.0)
        completion_ns = time.perf_counter_ns()

        child_record_visible = False
        final_event_count = 0
        if process.returncode == 0:
            child_record_visible = ledger.read("contention-child") is not None
            final_event_count = ledger.event_count()

    done = _read_json(done_path)
    writer_total_wait = _child_elapsed_seconds(done)
    release_to_completion = _positive_seconds(completion_ns - release_ns)
    session_hold = _positive_seconds(release_ns - hold_started_ns)
    return {
        "writer_ready": ready_received,
        "attempt_signal_received": attempt_received,
        "writer_completed_while_held": completed_while_held,
        "writer_timed_out": writer_timed_out,
        "writer_exit_code": process.returncode if process is not None else None,
        "session_hold_seconds": session_hold,
        "requested_hold_seconds": hold_seconds,
        "writer_total_wait_seconds": writer_total_wait,
        "release_to_completion_seconds": release_to_completion,
        "session_event_count_while_held": held_event_count,
        "child_record_visible": child_record_visible,
        "final_event_count": final_event_count,
        "stdout": stdout.strip(),
        "stderr": stderr.strip(),
    }


def _start_contention_child(
    *,
    ledger_path: Path,
    key_path: Path,
    ready_path: Path,
    start_path: Path,
    attempt_path: Path,
    done_path: Path,
) -> subprocess.Popen[str]:
    command = [
        sys.executable,
        "-m",
        "aluclu.cli.benchmark_cognition_ledger",
        "--contention-child",
        "--ledger-path",
        str(ledger_path),
        "--key-path",
        str(key_path),
        "--ready-path",
        str(ready_path),
        "--start-path",
        str(start_path),
        "--attempt-path",
        str(attempt_path),
        "--done-path",
        str(done_path),
    ]
    return subprocess.Popen(
        command,
        cwd=_repository_root(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _run_contention_child(args: argparse.Namespace) -> None:
    required = {
        "ledger_path": args.ledger_path,
        "key_path": args.key_path,
        "ready_path": args.ready_path,
        "start_path": args.start_path,
        "attempt_path": args.attempt_path,
        "done_path": args.done_path,
    }
    if any(value is None for value in required.values()):
        raise InputBoundaryError("contention child paths are required")
    ledger_path = cast(Path, args.ledger_path)
    key_path = cast(Path, args.key_path)
    ready_path = cast(Path, args.ready_path)
    start_path = cast(Path, args.start_path)
    attempt_path = cast(Path, args.attempt_path)
    done_path = cast(Path, args.done_path)

    with EncryptedLedger(
        ledger_path,
        FileKeyProvider(key_path, create=False),
    ) as ledger:
        _write_json(ready_path, {"ready": True})
        deadline = time.monotonic() + _CONTENTTION_TIMEOUT_SECONDS
        while not start_path.exists() and time.monotonic() < deadline:
            time.sleep(_POLL_SECONDS)
        if not start_path.exists():
            raise TimeoutError("contention parent did not release writer start")
        signal_ns = time.perf_counter_ns()
        _write_json(attempt_path, {"signal_ns": signal_ns})
        attempt_ns = time.perf_counter_ns()
        with ledger.verified_session() as session:
            session.append("contention-child", "child")
        completed_ns = time.perf_counter_ns()
        _write_json(
            done_path,
            {
                "attempt_ns": attempt_ns,
                "completed_ns": completed_ns,
            },
        )


def _wait_for_file(
    path: Path,
    *,
    process: subprocess.Popen[str],
    timeout: float,
) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return True
        if process.poll() is not None:
            return path.exists()
        time.sleep(_POLL_SECONDS)
    return path.exists()


def _child_elapsed_seconds(
    done: Mapping[str, Any] | None,
) -> float:
    if done is None:
        return 0.0
    started = done.get("attempt_ns")
    completed = done.get("completed_ns")
    if type(started) is not int or type(completed) is not int:
        return 0.0
    return _positive_seconds(completed - started)


def _deterministic_payload(
    *,
    seed: int,
    index: int,
    payload_bytes: int,
) -> str:
    text_bytes = payload_bytes - 2
    digest = hashlib.sha256(f"{seed}:{index}".encode("ascii")).hexdigest()
    repeats = (text_bytes + len(digest) - 1) // len(digest)
    payload = (digest * repeats)[:text_bytes]
    if len(canonical_json_bytes(payload)) != payload_bytes:
        raise RuntimeError("deterministic payload size is not exact")
    return payload


def _bucket_ranges(count: int, buckets: int) -> list[tuple[int, int]]:
    return [
        ((index * count) // buckets, ((index + 1) * count) // buckets)
        for index in range(buckets)
    ]


def _validated_turns(value: int) -> int:
    turns = _exact_int(value, label="turns")
    if turns < 4:
        raise InputBoundaryError("turns must be at least four")
    return turns


def _validated_payload_bytes(value: int) -> int:
    payload_bytes = _exact_int(value, label="payload_bytes")
    if not 2 <= payload_bytes <= MAX_PAYLOAD_BYTES:
        raise InputBoundaryError(
            f"payload_bytes must be between 2 and {MAX_PAYLOAD_BYTES}"
        )
    return payload_bytes


def _exact_int(value: int, *, label: str) -> int:
    if type(value) is not int:
        raise InputBoundaryError(f"{label} must be an integer")
    return value


def _validated_hold_seconds(value: float) -> float:
    if type(value) not in {int, float} or isinstance(value, bool):
        raise InputBoundaryError("contention_hold_seconds must be numeric")
    hold = float(value)
    if not math.isfinite(hold) or not 0.0 < hold <= _MAX_CONTENTION_HOLD_SECONDS:
        raise InputBoundaryError("contention_hold_seconds is out of range")
    return hold


def _benchmark_base() -> Path:
    if os.name == "nt":
        state_home = os.environ.get("LOCALAPPDATA")
        if not state_home:
            raise InputBoundaryError("LOCALAPPDATA is required for the benchmark")
    else:
        state_home = os.environ.get("XDG_STATE_HOME")
        if not state_home:
            state_home = str(Path.home() / ".local" / "state")
    state_path = Path(state_home).expanduser()
    if not state_path.is_absolute():
        raise InputBoundaryError("benchmark application-state path must be absolute")
    return (state_path / "ALUCLU" / "benchmarks").resolve(strict=False)


def _require_work_root_boundary(
    path: Path,
    *,
    test_only_benchmark_base: Path | None,
) -> None:
    production_boundary = test_only_benchmark_base is None
    base = (
        _benchmark_base()
        if production_boundary
        else test_only_benchmark_base.expanduser().resolve(strict=False)
    )
    if path == base or not path.is_relative_to(base):
        raise InputBoundaryError(
            "benchmark work_dir must be a run directory under the benchmark base"
        )
    if _looks_synced(base) or _looks_synced(path):
        raise InputBoundaryError(
            "benchmark work_dir must not use a cloud-synchronised path"
        )
    if production_boundary:
        temporary_root = Path(tempfile.gettempdir()).resolve(strict=False)
        if base == temporary_root or base.is_relative_to(temporary_root):
            raise InputBoundaryError(
                "benchmark base must not use the temporary directory"
            )
        if path == temporary_root or path.is_relative_to(temporary_root):
            raise InputBoundaryError(
                "benchmark work_dir must not use the temporary directory"
            )


def _require_fresh_work_root(path: Path) -> None:
    if not path.exists():
        return
    if not path.is_dir():
        raise InputBoundaryError("benchmark work_dir must be a directory")
    try:
        nonempty = next(path.iterdir(), None) is not None
    except OSError as exc:
        raise InputBoundaryError("benchmark work_dir cannot be inspected") from exc
    if nonempty:
        raise InputBoundaryError("benchmark work_dir must be empty")


def _positive_seconds(elapsed_ns: int) -> float:
    return max(1, elapsed_ns) / 1_000_000_000


def _finite_ratio(numerator: float, denominator: float) -> float | None:
    if (
        not math.isfinite(numerator)
        or not math.isfinite(denominator)
        or denominator <= 0.0
    ):
        return None
    return numerator / denominator


def _main_disk_bytes(ledger_path: Path, key_store: Path) -> dict[str, int]:
    database = _file_size(ledger_path)
    wal = _file_size(Path(f"{ledger_path}-wal"))
    key_store_bytes = _tree_bytes(key_store)
    return {
        "database": database,
        "wal": wal,
        "key_store": key_store_bytes,
        "total": database + wal + key_store_bytes,
    }


def _file_size(path: Path) -> int:
    try:
        return path.stat().st_size if path.is_file() else 0
    except OSError:
        return 0


def _tree_bytes(root: Path) -> int:
    total = 0
    if not root.exists():
        return total
    for path in root.rglob("*"):
        if path.is_file():
            total += _file_size(path)
    return total


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    atomic_write_bytes(
        path,
        canonical_json_bytes(cast(JsonValue, dict(payload))) + b"\n",
    )


def _read_json(path: Path) -> Mapping[str, Any] | None:
    try:
        decoded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return decoded if isinstance(decoded, dict) else None


def _process_memory_bytes() -> dict[str, int]:
    if os.name == "nt":
        return _windows_process_memory_bytes()
    try:
        import resource
    except ImportError:
        return {"current": 0, "peak": 0}
    peak_raw = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    peak = peak_raw if sys.platform == "darwin" else peak_raw * 1024
    current = peak
    statm = Path("/proc/self/statm")
    try:
        resident_pages = int(statm.read_text(encoding="ascii").split()[1])
        current = resident_pages * int(os.sysconf("SC_PAGE_SIZE"))
    except (OSError, ValueError, IndexError):
        pass
    return {"current": current, "peak": peak}


def _windows_process_memory_bytes() -> dict[str, int]:
    import ctypes
    from ctypes import wintypes

    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    counters = ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(ProcessMemoryCounters)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(ProcessMemoryCounters),
        wintypes.DWORD,
    ]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    handle = kernel32.GetCurrentProcess()
    if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
        return {"current": 0, "peak": 0}
    return {
        "current": int(counters.WorkingSetSize),
        "peak": int(counters.PeakWorkingSetSize),
    }


def _environment(work_root: Path) -> dict[str, Any]:
    environment = copy.deepcopy(_static_environment())
    environment["storage"] = _storage_info(work_root)
    return environment


@lru_cache(maxsize=1)
def _static_environment() -> dict[str, Any]:
    return {
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
            "prefix": sys.prefix,
            "base_prefix": sys.base_prefix,
            "system_site_packages": _uses_system_site_packages(),
        },
        "sqlite": sqlite3.sqlite_version,
        "cryptography": cryptography_version,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "description": platform.platform(),
        },
        "cpu": _cpu_info(),
        "ram": {"total_bytes": _total_ram_bytes()},
        "gpu": _gpu_info(),
        "git": _git_info(),
        "dependencies": _installed_dependency_report(),
    }


def _uses_system_site_packages() -> bool:
    config = Path(sys.prefix) / "pyvenv.cfg"
    try:
        lines = config.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    for line in lines:
        key, separator, value = line.partition("=")
        if separator and key.strip().casefold() == "include-system-site-packages":
            return value.strip().casefold() == "true"
    return False


def _installed_dependency_report() -> dict[str, Any]:
    requirements = _declared_dependencies()
    packages = [_dependency_status(text) for text in requirements]
    return {
        "declared": requirements,
        "packages": packages,
        "all_satisfied": all(item["satisfied"] is True for item in packages),
        "mismatches": [
            item["requirement"]
            for item in packages
            if item["satisfied"] is not True
        ],
        "torch_inventory_only": True,
    }


def _declared_dependencies() -> list[str]:
    pyproject = _repository_root() / "pyproject.toml"
    try:
        import tomllib
    except ImportError:
        return _fallback_dependencies(pyproject)
    try:
        body = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return _fallback_dependencies(pyproject)
    values = body.get("project", {}).get("dependencies", [])
    return [value for value in values if type(value) is str]


def _fallback_dependencies(pyproject: Path) -> list[str]:
    try:
        lines = pyproject.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    collecting = False
    fragments: list[str] = []
    balance = 0
    for line in lines:
        stripped = line.strip()
        if not collecting and stripped.startswith("dependencies"):
            _, _, remainder = stripped.partition("=")
            fragments.append(remainder.strip())
            balance += remainder.count("[") - remainder.count("]")
            collecting = balance > 0
            if not collecting:
                break
        elif collecting:
            fragments.append(stripped)
            balance += stripped.count("[") - stripped.count("]")
            if balance <= 0:
                break
    try:
        decoded = ast.literal_eval(" ".join(fragments))
    except (SyntaxError, ValueError):
        return []
    return [value for value in decoded if type(value) is str]


def _dependency_status(requirement_text: str) -> dict[str, Any]:
    try:
        from packaging.requirements import Requirement
    except ImportError:
        name = requirement_text.split(">=", 1)[0].strip()
        return {
            "requirement": requirement_text,
            "name": name,
            "installed": _metadata_version(name),
            "satisfied": None,
            "checker": "unavailable",
        }
    requirement = Requirement(requirement_text)
    installed = _metadata_version(requirement.name)
    satisfied = installed is not None and requirement.specifier.contains(
        installed,
        prereleases=True,
    )
    return {
        "requirement": requirement_text,
        "name": requirement.name,
        "installed": installed,
        "satisfied": satisfied,
        "checker": "packaging",
    }


def _metadata_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _cpu_info() -> dict[str, Any]:
    info: dict[str, Any] = {
        "model": platform.processor() or platform.machine(),
        "physical_cores": None,
        "logical_cores": os.cpu_count(),
    }
    if os.name == "nt":
        detected = _powershell_json(
            "Get-CimInstance Win32_Processor | "
            "Select-Object -First 1 Name,NumberOfCores,"
            "NumberOfLogicalProcessors | ConvertTo-Json -Compress"
        )
        if isinstance(detected, dict):
            info["model"] = detected.get("Name") or info["model"]
            info["physical_cores"] = detected.get("NumberOfCores")
            info["logical_cores"] = (
                detected.get("NumberOfLogicalProcessors")
                or info["logical_cores"]
            )
    else:
        info["physical_cores"] = _linux_physical_cores()
        info["model"] = _linux_cpu_model() or info["model"]
    return info


def _linux_cpu_model() -> str | None:
    cpuinfo = Path("/proc/cpuinfo")
    try:
        for line in cpuinfo.read_text(
            encoding="utf-8",
            errors="ignore",
        ).splitlines():
            key, separator, value = line.partition(":")
            if separator and key.strip() in {"model name", "Hardware"}:
                return value.strip()
    except OSError:
        return None
    return None


def _linux_physical_cores() -> int | None:
    cpuinfo = Path("/proc/cpuinfo")
    try:
        blocks = cpuinfo.read_text(
            encoding="utf-8",
            errors="ignore",
        ).split("\n\n")
    except OSError:
        return None
    cores: set[tuple[str, str]] = set()
    for block in blocks:
        values: dict[str, str] = {}
        for line in block.splitlines():
            key, separator, value = line.partition(":")
            if separator:
                values[key.strip()] = value.strip()
        if "physical id" in values and "core id" in values:
            cores.add((values["physical id"], values["core id"]))
    return len(cores) or None


def _total_ram_bytes() -> int:
    if os.name == "nt":
        return _windows_total_ram_bytes()
    if not hasattr(os, "sysconf"):
        return 0
    try:
        return int(os.sysconf("SC_PAGE_SIZE")) * int(os.sysconf("SC_PHYS_PAGES"))
    except (OSError, ValueError):
        return 0


def _windows_total_ram_bytes() -> int:
    import ctypes

    class MemoryStatusEx(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = MemoryStatusEx()
    status.dwLength = ctypes.sizeof(MemoryStatusEx)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(MemoryStatusEx)]
    kernel32.GlobalMemoryStatusEx.restype = ctypes.c_int
    if not kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return 0
    return int(status.ullTotalPhys)


def _gpu_info() -> dict[str, Any]:
    nvidia = _run_command(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader,nounits",
        ],
        timeout=5.0,
    )
    devices: list[dict[str, Any]] = []
    if nvidia["returncode"] == 0:
        for line in nvidia["stdout"].splitlines():
            fields = [field.strip() for field in line.split(",")]
            if len(fields) == 3:
                devices.append(
                    {
                        "name": fields[0],
                        "memory_total_mib": _optional_int(fields[1]),
                        "driver_version": fields[2],
                        "source": "nvidia-smi",
                    }
                )
    if not devices and os.name == "nt":
        fallback = _powershell_json(
            "Get-CimInstance Win32_VideoController | "
            "Select-Object Name,AdapterRAM,DriverVersion | "
            "ConvertTo-Json -Compress"
        )
        values = fallback if isinstance(fallback, list) else [fallback]
        devices = [
            {**value, "source": "Win32_VideoController"}
            for value in values
            if isinstance(value, dict)
        ]
    return {
        "cuda_available": nvidia["returncode"] == 0,
        "nvidia_smi_available": nvidia["returncode"] == 0,
        "devices": devices,
        "inventory_only": True,
        "persistence_loop_uses_gpu": False,
    }


def _storage_info(work_root: Path) -> dict[str, Any]:
    usage = shutil.disk_usage(work_root)
    synced = _looks_synced(work_root)
    info: dict[str, Any] = {
        "path": str(work_root),
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "filesystem": None,
        "path_type": "cloud-synchronised" if synced else "local",
        "synced_path": synced,
        "physical_disk": None,
    }
    if os.name == "nt":
        escaped = str(work_root).replace("'", "''")
        detected = _powershell_json(
            f"$item=Get-Item -LiteralPath '{escaped}'; "
            "$letter=$item.PSDrive.Name; "
            "$volume=Get-Volume -DriveLetter $letter; "
            "$disk=Get-Partition -DriveLetter $letter | Get-Disk; "
            "[pscustomobject]@{FileSystem=$volume.FileSystem;"
            "FriendlyName=$disk.FriendlyName;MediaType=[string]$disk.MediaType;"
            "BusType=[string]$disk.BusType} | ConvertTo-Json -Compress"
        )
        if isinstance(detected, dict):
            info["filesystem"] = detected.get("FileSystem")
            info["physical_disk"] = {
                "friendly_name": detected.get("FriendlyName"),
                "media_type": detected.get("MediaType"),
                "bus_type": detected.get("BusType"),
            }
    else:
        filesystem, source = _posix_mount_info(work_root)
        info["filesystem"] = filesystem
        if filesystem in {"nfs", "nfs4", "cifs", "smbfs", "sshfs"}:
            info["path_type"] = "network"
        info["physical_disk"] = _posix_storage_device(source)
    return info


def _posix_mount_info(path: Path) -> tuple[str | None, str | None]:
    if sys.platform == "darwin":
        detected = _run_command(["stat", "-f", "%T", str(path)], timeout=5.0)
        filesystem = (
            detected["stdout"].strip() if detected["returncode"] == 0 else None
        )
        return filesystem, None
    mountinfo = Path("/proc/self/mountinfo")
    try:
        lines = mountinfo.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None, None
    resolved = str(path.resolve())
    best: tuple[int, str, str] | None = None
    for line in lines:
        fields = line.split()
        try:
            separator = fields.index("-")
            mount_point = fields[4].replace("\\040", " ")
            filesystem = fields[separator + 1]
            source = fields[separator + 2].replace("\\040", " ")
        except (ValueError, IndexError):
            continue
        prefix = mount_point.rstrip("/") or "/"
        if resolved == prefix or resolved.startswith(prefix.rstrip("/") + "/"):
            candidate = (len(prefix), filesystem, source)
            if best is None or candidate[0] > best[0]:
                best = candidate
    if best is None:
        return None, None
    return best[1], best[2]


def _posix_storage_device(source: str | None) -> dict[str, Any] | None:
    if source is None or not source.startswith("/dev/"):
        return {"source": source, "media_type": None, "bus_type": None}
    name = Path(source).name
    if name.startswith("nvme"):
        base = name.split("p", 1)[0]
        bus_type = "nvme"
    else:
        base = name.rstrip("0123456789")
        bus_type = None
    rotational_path = Path("/sys/class/block") / base / "queue" / "rotational"
    try:
        rotational = rotational_path.read_text(encoding="ascii").strip()
    except OSError:
        rotational = None
    media_type = (
        {"0": "solid-state", "1": "rotational"}.get(rotational)
        if rotational is not None
        else None
    )
    return {
        "source": source,
        "media_type": media_type,
        "bus_type": bus_type,
    }


def _looks_synced(path: Path) -> bool:
    markers = {"onedrive", "dropbox", "google drive", "iclouddrive"}
    return any(part.casefold() in markers for part in path.parts)


def _git_info() -> dict[str, Any]:
    root = _repository_root()
    head = _run_command(["git", "rev-parse", "HEAD"], cwd=root, timeout=5.0)
    dirty = _run_command(["git", "status", "--short"], cwd=root, timeout=5.0)
    return {
        "commit": head["stdout"].strip() if head["returncode"] == 0 else None,
        "dirty": bool(dirty["stdout"].strip())
        if dirty["returncode"] == 0
        else None,
    }


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _powershell_json(command: str) -> Any:
    executable = shutil.which("powershell") or shutil.which("pwsh")
    if executable is None:
        return None
    completed = _run_command(
        [executable, "-NoProfile", "-Command", command],
        timeout=8.0,
    )
    if completed["returncode"] != 0 or not completed["stdout"].strip():
        return None
    try:
        return json.loads(completed["stdout"])
    except json.JSONDecodeError:
        return None


def _run_command(
    command: list[str],
    *,
    timeout: float,
    cwd: Path | None = None,
) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
        }
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def _optional_int(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Measure encrypted cognition-ledger scale behavior."
    )
    parser.add_argument("--turns", type=int, default=_FIXED_GATE_TURNS)
    parser.add_argument(
        "--payload-bytes",
        type=int,
        default=_FIXED_GATE_PAYLOAD_BYTES,
    )
    parser.add_argument("--seed", type=int, default=20260822)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/cognition_ledger_scale.json"),
    )
    parser.add_argument(
        "--contention-hold-seconds",
        type=float,
        default=_DEFAULT_CONTENTION_HOLD_SECONDS,
    )
    parser.add_argument("--contention-child", action="store_true", help=argparse.SUPPRESS)
    for name in (
        "ledger-path",
        "key-path",
        "ready-path",
        "start-path",
        "attempt-path",
        "done-path",
    ):
        parser.add_argument(f"--{name}", type=Path, help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)
    if args.contention_child:
        _run_contention_child(args)
        return
    work_dir = args.work_dir or local_benchmark_root()
    result = run_benchmark(
        turns=args.turns,
        payload_bytes=args.payload_bytes,
        output=args.output,
        work_dir=work_dir,
        seed=args.seed,
        contention_hold_seconds=args.contention_hold_seconds,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["success"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
