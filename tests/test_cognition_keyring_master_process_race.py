from __future__ import annotations

import base64
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

MASTER_SERVICE = "aluclu-race"
MASTER_USERNAME = "owner"
MASTER_READ_BARRIER_TIMEOUT_SECONDS = 15
WORKER_COMPLETION_TIMEOUT_SECONDS = 120


def _worker() -> Path:
    return Path(__file__).with_name("_keyring_master_race_worker.py")


def _run_worker(
    workspace_python: Path,
    tmp_path: Path,
    worker_id: str,
) -> subprocess.Popen[str]:
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    src_path = str(root / "src")
    env["PYTHONPATH"] = (
        src_path
        if not env.get("PYTHONPATH")
        else src_path + os.pathsep + env["PYTHONPATH"]
    )
    return subprocess.Popen(
        [
            str(workspace_python),
            str(_worker()),
            "--ledger",
            str(tmp_path / "memory.sqlite3"),
            "--vault",
            str(tmp_path / "persistent-keyring.sqlite3"),
            "--worker-id",
            worker_id,
            "--service",
            MASTER_SERVICE,
            "--username",
            MASTER_USERNAME,
            "--participants",
            "2",
            "--timeout-seconds",
            str(MASTER_READ_BARRIER_TIMEOUT_SECONDS),
        ],
        cwd=root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _communicate(
    process: subprocess.Popen[str],
) -> subprocess.CompletedProcess[str]:
    try:
        stdout, stderr = process.communicate(timeout=WORKER_COMPLETION_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(
            f"keyring race worker {process.pid} timed out; "
            f"stdout={exc.output!r}; stderr={exc.stderr!r}"
        ) from exc
    return subprocess.CompletedProcess(
        process.args,
        process.returncode,
        stdout,
        stderr,
    )


def _kill_and_reap(processes: list[subprocess.Popen[str]]) -> None:
    for process in processes:
        if process.poll() is None:
            process.kill()
    for process in processes:
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=5)


def _communicate_workers(
    processes: list[subprocess.Popen[str]],
) -> list[subprocess.CompletedProcess[str]]:
    try:
        return [_communicate(process) for process in processes]
    except BaseException:
        _kill_and_reap(processes)
        raise


def _operation_rows(vault_path: Path) -> list[dict[str, str | int | None]]:
    with sqlite3.connect(vault_path) as connection:
        rows = connection.execute(
            """
            SELECT pid, operation, service, username, password, observed
            FROM operations
            ORDER BY id
            """
        ).fetchall()
    return [
        {
            "pid": int(pid),
            "operation": str(operation),
            "service": str(service),
            "username": str(username),
            "password": None if password is None else str(password),
            "observed": None if observed is None else str(observed),
        }
        for pid, operation, service, username, password, observed in rows
    ]


def _master_sets(rows: list[dict[str, str | int | None]]) -> list[str]:
    return [
        str(row["password"])
        for row in rows
        if row["operation"] == "set"
        and row["service"] == MASTER_SERVICE
        and row["username"] == MASTER_USERNAME
    ]


def _vault_artifact_paths(vault_path: Path) -> set[Path]:
    return {
        vault_path,
        Path(f"{vault_path}-wal"),
        Path(f"{vault_path}-shm"),
        Path(f"{vault_path}-journal"),
    }


def _assert_no_master_secret_or_file_fallback_on_disk(
    tmp_path: Path,
    master_passwords: list[str],
) -> None:
    vault_artifacts = _vault_artifact_paths(tmp_path / "persistent-keyring.sqlite3")
    forbidden_payloads = set()
    for password in master_passwords:
        forbidden_payloads.add(password.encode("ascii"))
        forbidden_payloads.add(
            base64.b64decode(password.encode("ascii"), validate=True)
        )

    assert not (tmp_path / "memory.sqlite3.key").exists()
    assert not (tmp_path / "memory.sqlite3.record-keys.json").exists()

    for path in tmp_path.rglob("*"):
        if not path.is_file() or path in vault_artifacts:
            continue
        payload = path.read_bytes()
        for forbidden in forbidden_payloads:
            assert forbidden not in payload


def test_keyring_master_key_is_created_once_across_real_process_unlock_race(
    tmp_path: Path,
) -> None:
    first = _run_worker(Path(sys.executable), tmp_path, "one")
    second = _run_worker(Path(sys.executable), tmp_path, "two")

    completed = _communicate_workers([first, second])
    errors = "\n\n".join(
        f"command={result.args!r}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        for result in completed
        if result.returncode != 0
    )
    assert [result.returncode for result in completed] == [0, 0], errors

    rows = _operation_rows(tmp_path / "persistent-keyring.sqlite3")
    master_sets = _master_sets(rows)
    _assert_no_master_secret_or_file_fallback_on_disk(tmp_path, master_sets)

    assert len(master_sets) == 1, rows
    assert (tmp_path / "memory.sqlite3.record-keys").is_dir()
