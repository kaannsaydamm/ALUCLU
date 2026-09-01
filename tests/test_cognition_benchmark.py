from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

import pytest

import aluclu.cli.benchmark_cognition_ledger as benchmark_module
from aluclu.cli.benchmark_cognition_ledger import (
    local_benchmark_root,
    run_benchmark,
)
from aluclu.cognition import (
    InputBoundaryError,
    VerifiedLedgerSession,
    canonical_json_bytes,
)


def test_public_benchmark_api_does_not_expose_test_overrides() -> None:
    assert tuple(inspect.signature(run_benchmark).parameters) == (
        "turns",
        "payload_bytes",
        "output",
        "work_dir",
        "seed",
        "contention_hold_seconds",
    )


def test_benchmark_writes_machine_readable_resource_evidence(tmp_path: Path) -> None:
    output = tmp_path / "result.json"
    work_dir = tmp_path / "run"
    result = benchmark_module._run_benchmark_impl(
        turns=64,
        payload_bytes=128,
        output=output,
        work_dir=work_dir,
        seed=7,
        contention_hold_seconds=0.05,
        append_hook=None,
        benchmark_base_override=tmp_path,
    )

    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert persisted == result
    assert output.read_bytes() == canonical_json_bytes(result) + b"\n"
    assert result["turns"] == 64
    assert result["success"] is True
    assert len(result["quartile_seconds"]) == 4
    assert all(value > 0.0 for value in result["quartile_seconds"])
    assert result["full_verifications"] <= 2
    assert result["cursor_scan_records"] == 64
    assert result["cursor_scan_seconds"] > 0.0
    assert result["interfaces"] == {
        "ledger_api": "EncryptedLedger.verified_session",
        "record_key_store": "DirectoryRecordKeyStore",
    }

    disk = result["disk_bytes"]
    assert disk["total"] > 0
    assert disk["total"] == disk["database"] + disk["wal"] + disk["key_store"]
    rss = result["rss_bytes"]
    assert rss["peak"] > 0
    assert rss["peak_delta"] >= 0
    assert result["thresholds"]["fixed_gate_enforced"] is False

    contention = result["contention"]
    assert contention["attempt_signal_received"] is True
    assert contention["writer_completed_while_held"] is False
    assert contention["writer_timed_out"] is False
    assert contention["writer_exit_code"] == 0
    assert contention["session_hold_seconds"] > 0.0
    assert contention["writer_total_wait_seconds"] >= contention[
        "session_hold_seconds"
    ]
    assert 0.0 < contention["release_to_completion_seconds"] <= 10.0

    environment = result["environment"]
    assert environment["dependencies"]["packages"]
    assert environment["python"]["system_site_packages"] in {True, False}
    assert environment["cpu"]["logical_cores"]
    assert environment["ram"]["total_bytes"] > 0
    assert "gpu" in environment
    assert environment["storage"]["free_bytes"] > 0
    assert environment["git"]["commit"]
    assert Path(result["paths"]["work_dir"]).is_absolute()


def test_benchmark_atomically_replaces_existing_output(tmp_path: Path) -> None:
    output = tmp_path / "result.json"
    output.write_text('{"old":true}\n', encoding="utf-8")

    result = benchmark_module._run_benchmark_impl(
        turns=8,
        payload_bytes=32,
        output=output,
        work_dir=tmp_path / "run",
        seed=8,
        contention_hold_seconds=0.05,
        append_hook=None,
        benchmark_base_override=tmp_path,
    )

    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert persisted == result
    assert "old" not in persisted
    assert not list(tmp_path.glob("result.json*.tmp"))


@pytest.mark.parametrize(
    ("turns", "payload_bytes"),
    [
        (0, 32),
        (-1, 32),
        (True, 32),
        (1.0, 32),
        (8, 0),
        (8, -1),
        (8, True),
        (8, 1.0),
    ],
)
def test_benchmark_rejects_invalid_arguments_before_creating_ledger(
    tmp_path: Path,
    turns: Any,
    payload_bytes: Any,
) -> None:
    work_dir = tmp_path / "run"
    output = tmp_path / "result.json"

    with pytest.raises(InputBoundaryError):
        run_benchmark(
            turns=turns,
            payload_bytes=payload_bytes,
            output=output,
            work_dir=work_dir,
            seed=1,
        )

    assert not work_dir.exists()
    assert not output.exists()


def test_benchmark_append_failure_replaces_stale_success_with_failure(
    tmp_path: Path,
) -> None:
    output = tmp_path / "result.json"
    output.write_text('{"success":true,"stale":true}\n', encoding="utf-8")

    def fail_after_first(
        session: VerifiedLedgerSession,
        event_id: str,
        payload: Any,
    ) -> None:
        if event_id == "turn-00000002":
            raise RuntimeError("injected append failure")
        session.append(event_id, payload)

    with pytest.raises(RuntimeError, match="injected append failure"):
        benchmark_module._run_benchmark_impl(
            turns=4,
            payload_bytes=32,
            output=output,
            work_dir=tmp_path / "run",
            seed=2,
            contention_hold_seconds=0.05,
            append_hook=fail_after_first,
            benchmark_base_override=tmp_path,
        )

    failure = json.loads(output.read_text(encoding="utf-8"))
    assert failure["success"] is False
    assert failure["error"] == {
        "message": "injected append failure",
        "type": "RuntimeError",
    }
    assert "stale" not in failure


def test_local_benchmark_root_uses_unsynchronised_application_state() -> None:
    root = local_benchmark_root("unit-test-run")

    assert root.name == "unit-test-run"
    assert "ALUCLU" in root.parts
    assert "benchmarks" in root.parts
    assert "Temp" not in root.parts
    assert "OneDrive" not in root.parts


def test_arbitrary_work_directory_is_rejected_without_mutation(
    tmp_path: Path,
) -> None:
    work_dir = tmp_path / "temporary-run"
    output = tmp_path / "temporary-run.json"
    original = b'{"success":true,"old-run":true}\n'
    output.write_bytes(original)

    with pytest.raises(InputBoundaryError, match="benchmark work_dir"):
        run_benchmark(
            turns=4,
            payload_bytes=32,
            output=output,
            work_dir=work_dir,
            seed=10,
            contention_hold_seconds=0.05,
        )

    assert output.read_bytes() == original
    assert not work_dir.exists()


def test_cloud_synced_child_is_rejected_inside_test_boundary(
    tmp_path: Path,
) -> None:
    work_dir = tmp_path / "OneDrive" / "cloud-run"
    output = tmp_path / "cloud-run.json"
    original = b'{"success":true,"old-run":true}\n'
    output.write_bytes(original)

    with pytest.raises(InputBoundaryError, match="cloud-synchronised"):
        benchmark_module._run_benchmark_impl(
            turns=4,
            payload_bytes=32,
            output=output,
            work_dir=work_dir,
            seed=10,
            contention_hold_seconds=0.05,
            append_hook=None,
            benchmark_base_override=tmp_path,
        )

    assert output.read_bytes() == original
    assert not work_dir.exists()


def test_explicit_test_boundary_allows_a_fresh_child_run(tmp_path: Path) -> None:
    benchmark_base = tmp_path / "isolated-state"
    work_dir = benchmark_base / "allowed-run"
    output = tmp_path / "allowed.json"

    result = benchmark_module._run_benchmark_impl(
        turns=4,
        payload_bytes=32,
        output=output,
        work_dir=work_dir,
        seed=11,
        contention_hold_seconds=0.05,
        append_hook=None,
        benchmark_base_override=benchmark_base,
    )

    assert result["success"] is True
    assert Path(result["paths"]["work_dir"]) == work_dir.resolve()
    assert output.exists()


def test_payload_bytes_are_exact_and_directory_backend_is_real(tmp_path: Path) -> None:
    observed_sizes: list[int] = []

    def observe_append(
        session: VerifiedLedgerSession,
        event_id: str,
        payload: Any,
    ) -> None:
        observed_sizes.append(len(canonical_json_bytes(payload)))
        session.append(event_id, payload)

    work_dir = tmp_path / "run"
    result = benchmark_module._run_benchmark_impl(
        turns=4,
        payload_bytes=64,
        output=tmp_path / "result.json",
        work_dir=work_dir,
        seed=9,
        contention_hold_seconds=0.05,
        append_hook=observe_append,
        benchmark_base_override=tmp_path,
    )

    assert observed_sizes == [64, 64, 64, 64]
    key_store = Path(result["paths"]["record_key_store"])
    assert key_store.is_dir()
    assert key_store.is_relative_to(work_dir.resolve())


def test_existing_nonempty_work_directory_is_rejected_without_replacing_output(
    tmp_path: Path,
) -> None:
    work_dir = tmp_path / "run"
    work_dir.mkdir()
    (work_dir / "sentinel.txt").write_text("keep", encoding="utf-8")
    output = tmp_path / "result.json"
    original = b'{"success":true,"old-run":true}\n'
    output.write_bytes(original)

    with pytest.raises(InputBoundaryError):
        benchmark_module._run_benchmark_impl(
            turns=4,
            payload_bytes=64,
            output=output,
            work_dir=work_dir,
            seed=1,
            contention_hold_seconds=0.05,
            append_hook=None,
            benchmark_base_override=tmp_path,
        )

    assert output.read_bytes() == original
    assert (work_dir / "sentinel.txt").read_text(encoding="utf-8") == "keep"


def test_fixed_gate_records_and_fails_an_exceeded_raw_threshold() -> None:
    contention = {
        "writer_ready": True,
        "attempt_signal_received": True,
        "writer_completed_while_held": False,
        "writer_timed_out": False,
        "writer_exit_code": 0,
        "session_hold_seconds": 0.1,
        "writer_total_wait_seconds": 0.2,
        "release_to_completion_seconds": 0.1,
        "child_record_visible": True,
        "final_event_count": 2,
    }

    evidence = benchmark_module._threshold_evidence(
        turns=8192,
        payload_bytes=512,
        records_seen=8192,
        final_event_count=8192,
        duplicates_detected=False,
        cursor_scan_records=8192,
        full_verifications=2,
        quartile_per_append=[0.001, 0.001, 0.001, 0.0018],
        first_half_per_append=0.001,
        second_half_per_append=0.001,
        fourth_first_ratio=1.8,
        second_first_half_ratio=1.0,
        peak_rss=1,
        peak_rss_delta=0,
        disk_total=1,
        contention=contention,
    )

    assert evidence["fixed_gate_enforced"] is True
    assert evidence["passed"] is False
    assert evidence["fixed_gate_checks"]["fourth_first_ratio"] is False
    assert evidence["raw"]["fourth_first_quartile_ratio"] == 1.8
