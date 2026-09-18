from __future__ import annotations

import base64
import subprocess
import sys
from pathlib import Path

import pytest

CRASH_EXIT_CODE = 73
EVENT_KEY = b"d" * 32
INIT_BOUNDARIES = [
    "after_keyring_initialize_identity",
    "after_keyring_initialize_head",
    "after_keyring_initialize_intent",
    "after_keyring_initialize_publish",
    "after_keyring_initialize_witness",
    "after_keyring_initialize_cleanup",
]
OPERATION_BOUNDARIES = [
    "after_keyring_staging_credential",
    "after_keyring_staged_metadata",
    "after_keyring_prepare",
    "after_keyring_final_credential",
    "after_keyring_event_state",
    "after_keyring_disk_head",
    "after_keyring_keyring_head",
    "after_keyring_cleanup",
]
OPERATIONS = ["put_pending", "mark_committed", "discard_pending", "shred"]
PREPARE_COMMITTED_BOUNDARIES = frozenset(OPERATION_BOUNDARIES[2:])


@pytest.fixture(scope="module")
def workspace_python() -> Path:
    return Path(sys.executable)


def _worker() -> Path:
    return Path(__file__).with_name("_keyring_process_worker.py")


def _run_worker(
    workspace_python: Path,
    tmp_path: Path,
    action: str,
    *,
    operation: str = "",
    boundary: str = "",
    expected: str = "",
    timeout: int = 30,
) -> subprocess.CompletedProcess[str]:
    command = [
        str(workspace_python),
        str(_worker()),
        action,
        "--root",
        str(tmp_path / "keys"),
        "--vault",
        str(tmp_path / "persistent-vault.sqlite3"),
    ]
    if operation:
        command.extend(["--operation", operation])
    if boundary:
        command.extend(["--boundary", boundary])
    if expected:
        command.extend(["--expected", expected])
    return subprocess.run(
        command,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _assert_worker_ok(completed: subprocess.CompletedProcess[str]) -> None:
    assert completed.returncode == 0, completed.stderr


def _vault_artifact_paths(tmp_path: Path) -> set[Path]:
    vault = tmp_path / "persistent-vault.sqlite3"
    return {
        vault,
        Path(f"{vault}-wal"),
        Path(f"{vault}-shm"),
        Path(f"{vault}-journal"),
    }


def _assert_no_dek_outside_vault(tmp_path: Path) -> None:
    vault_artifacts = _vault_artifact_paths(tmp_path)
    encoded = base64.b64encode(EVENT_KEY)
    for path in tmp_path.rglob("*"):
        if not path.is_file() or path in vault_artifacts:
            continue
        payload = path.read_bytes()
        assert EVENT_KEY not in payload
        assert encoded not in payload


@pytest.mark.parametrize("boundary", INIT_BOUNDARIES)
def test_keyring_real_process_initialization_crash_recovers_with_persistent_vault(
    tmp_path: Path,
    workspace_python: Path,
    boundary: str,
) -> None:
    crashed = _run_worker(
        workspace_python,
        tmp_path,
        "crash-init",
        boundary=boundary,
    )
    assert crashed.returncode == CRASH_EXIT_CODE, crashed.stderr

    _assert_worker_ok(_run_worker(workspace_python, tmp_path, "verify-init"))
    _assert_worker_ok(_run_worker(workspace_python, tmp_path, "verify-init"))


@pytest.mark.parametrize("operation", OPERATIONS)
@pytest.mark.parametrize("boundary", OPERATION_BOUNDARIES)
def test_keyring_real_process_operation_crash_recovers_to_exact_old_or_new_state(
    tmp_path: Path,
    workspace_python: Path,
    operation: str,
    boundary: str,
) -> None:
    _assert_worker_ok(
        _run_worker(
            workspace_python,
            tmp_path,
            "setup-operation",
            operation=operation,
        )
    )

    crashed = _run_worker(
        workspace_python,
        tmp_path,
        "crash-operation",
        operation=operation,
        boundary=boundary,
    )
    assert crashed.returncode == CRASH_EXIT_CODE, crashed.stderr
    _assert_no_dek_outside_vault(tmp_path)

    expected = "new" if boundary in PREPARE_COMMITTED_BOUNDARIES else "old"
    _assert_worker_ok(
        _run_worker(
            workspace_python,
            tmp_path,
            "verify-operation",
            operation=operation,
            expected=expected,
        )
    )
    _assert_worker_ok(
        _run_worker(
            workspace_python,
            tmp_path,
            "verify-operation",
            operation=operation,
            expected=expected,
        )
    )


def test_keyring_real_process_prepared_append_missing_staged_credential_fails_closed(
    tmp_path: Path,
    workspace_python: Path,
) -> None:
    _assert_worker_ok(
        _run_worker(
            workspace_python,
            tmp_path,
            "setup-operation",
            operation="put_pending",
        )
    )
    crashed = _run_worker(
        workspace_python,
        tmp_path,
        "crash-operation",
        operation="put_pending",
        boundary="after_keyring_prepare",
    )
    assert crashed.returncode == CRASH_EXIT_CODE, crashed.stderr
    _assert_worker_ok(
        _run_worker(workspace_python, tmp_path, "delete-staging-credential")
    )

    _assert_worker_ok(_run_worker(workspace_python, tmp_path, "verify-fails-closed"))
    _assert_worker_ok(_run_worker(workspace_python, tmp_path, "verify-fails-closed"))
