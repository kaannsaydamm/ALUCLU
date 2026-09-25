from __future__ import annotations

import argparse
import base64
import json
import os
import sqlite3
import sys
import types
from pathlib import Path
from typing import Any

CRASH_EXIT_CODE = 73
INTEGRITY_KEY = b"i" * 32
LEDGER_ID = "ledger-1"
RECORD_HASH = "ab" * 32
EVENT_ID = "evt-1"
EVENT_KEY = b"d" * 32


class PersistentFakeKeyringBackend:
    priority = 1

    def __init__(self, vault_path: Path) -> None:
        self._vault_path = vault_path
        self._vault_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS credentials (
                    service TEXT NOT NULL,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    PRIMARY KEY (service, username)
                )
                """
            )

    def get_password(self, service: str, username: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT password FROM credentials WHERE service = ? AND username = ?",
                (service, username),
            ).fetchone()
        return None if row is None else str(row[0])

    def set_password(self, service: str, username: str, password: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO credentials(service, username, password)
                VALUES (?, ?, ?)
                ON CONFLICT(service, username) DO UPDATE SET password = excluded.password
                """,
                (service, username, password),
            )

    def delete_password(self, service: str, username: str) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM credentials WHERE service = ? AND username = ?",
                (service, username),
            )
        if cursor.rowcount == 0:
            raise RuntimeError("credential is missing")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._vault_path)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        return connection


PersistentFakeKeyringBackend.__module__ = "keyring.backends.Windows"


def _install_fake_keyring(vault_path: Path) -> PersistentFakeKeyringBackend:
    backend = PersistentFakeKeyringBackend(vault_path)
    module = types.ModuleType("keyring")
    module.get_keyring = lambda: backend  # type: ignore[attr-defined]
    module.get_password = backend.get_password  # type: ignore[attr-defined]
    module.set_password = backend.set_password  # type: ignore[attr-defined]
    module.delete_password = backend.delete_password  # type: ignore[attr-defined]
    sys.modules["keyring"] = module
    return backend


def _store(root: Path, vault_path: Path, *, create: bool = True, boundary: str | None = None):
    _install_fake_keyring(vault_path)
    from aluclu.cognition import KeyringRecordKeyStore

    def fault(observed: str) -> None:
        if observed == boundary:
            os._exit(CRASH_EXIT_CODE)

    return KeyringRecordKeyStore(
        root,
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        service="aluclu-test",
        username_prefix="owner",
        database_path=root.parent / "ledger.sqlite3",
        create=create,
        _fault_injector=fault if boundary is not None else None,
    )


def _apply_old_state(store: Any, operation: str) -> None:
    if operation == "put_pending":
        return
    store.put_pending(EVENT_ID, EVENT_KEY)
    if operation == "shred":
        store.mark_committed(EVENT_ID, RECORD_HASH)


def _run_operation(store: Any, operation: str) -> None:
    if operation == "put_pending":
        store.put_pending(EVENT_ID, EVENT_KEY)
    elif operation == "mark_committed":
        store.mark_committed(EVENT_ID, RECORD_HASH)
    elif operation == "discard_pending":
        store.discard_pending(EVENT_ID)
    elif operation == "shred":
        store.shred(EVENT_ID, RECORD_HASH)
    else:
        raise AssertionError(f"unknown operation: {operation}")


def _credential_rows(vault_path: Path) -> list[dict[str, str]]:
    if not vault_path.exists():
        return []
    with sqlite3.connect(vault_path) as connection:
        rows = connection.execute(
            "SELECT service, username, password FROM credentials ORDER BY service, username"
        ).fetchall()
    return [
        {"service": str(service), "username": str(username), "password": str(password)}
        for service, username, password in rows
    ]


def _root_file_payloads(root: Path) -> list[bytes]:
    if not root.exists():
        return []
    return [path.read_bytes() for path in root.rglob("*") if path.is_file()]


def _vault_artifact_paths(vault_path: Path) -> set[Path]:
    return {
        vault_path,
        Path(f"{vault_path}-wal"),
        Path(f"{vault_path}-shm"),
        Path(f"{vault_path}-journal"),
    }


def _non_vault_file_state(root: Path, vault_path: Path) -> dict[str, bytes]:
    workspace = root.parent
    if not workspace.exists():
        return {}
    vault_artifacts = _vault_artifact_paths(vault_path)
    return {
        path.relative_to(workspace).as_posix(): path.read_bytes()
        for path in workspace.rglob("*")
        if path.is_file() and path not in vault_artifacts
    }


def _verify_no_dek_under_root(root: Path) -> None:
    raw = EVENT_KEY
    encoded = base64.b64encode(EVENT_KEY)
    for payload in _root_file_payloads(root):
        if raw in payload or encoded in payload:
            raise AssertionError("record DEK leaked under key store root")


def _snapshot(root: Path, vault_path: Path, operation: str) -> dict[str, Any]:
    from aluclu.cognition import RecordKeyState

    store = _store(root, vault_path, create=False)
    store.verify_integrity()
    reference = store.reference(EVENT_ID)
    _verify_no_dek_under_root(root)
    value = store.get(EVENT_ID)
    rows = _credential_rows(vault_path)
    return {
        "get": None if value is None else value.hex(),
        "has_reference": reference is not None,
        "state": None if reference is None else reference.state.value,
        "record_hash": None if reference is None else reference.record_hash,
        "revision": store.revision,
        "tombstone_hash": store.tombstone_hash(EVENT_ID),
        "tombstoned": store.is_tombstoned(EVENT_ID),
        "event_credentials": sum(":event:" in row["username"] for row in rows),
        "head_credentials": sum(":head:" in row["username"] for row in rows),
        "staging_credentials": sum(":staging:" in row["username"] for row in rows),
        "profile": store.profile.value,
        "operation": operation,
        "states_available": [state.value for state in RecordKeyState],
    }


def _expect_state(snapshot: dict[str, Any], operation: str, expected: str) -> None:
    new = expected == "new"
    key_hex = EVENT_KEY.hex()
    if operation == "put_pending":
        assert snapshot["get"] == (key_hex if new else None)
        assert snapshot["has_reference"] is new
        assert snapshot["state"] == ("pending" if new else None)
        assert snapshot["record_hash"] is None
        assert snapshot["revision"] == (1 if new else 0)
        assert snapshot["tombstoned"] is False
        assert snapshot["tombstone_hash"] is None
        assert snapshot["event_credentials"] == (1 if new else 0)
    elif operation == "mark_committed":
        assert snapshot["get"] == key_hex
        assert snapshot["has_reference"] is True
        assert snapshot["state"] == ("committed" if new else "pending")
        assert snapshot["record_hash"] == (RECORD_HASH if new else None)
        assert snapshot["revision"] == (2 if new else 1)
        assert snapshot["tombstoned"] is False
        assert snapshot["tombstone_hash"] is None
        assert snapshot["event_credentials"] == 1
    elif operation == "discard_pending":
        assert snapshot["get"] == (None if new else key_hex)
        assert snapshot["has_reference"] is not new
        assert snapshot["state"] == (None if new else "pending")
        assert snapshot["record_hash"] is None
        assert snapshot["tombstoned"] is False
        assert snapshot["tombstone_hash"] is None
        assert snapshot["revision"] == (2 if new else 1)
        assert snapshot["event_credentials"] == (0 if new else 1)
    elif operation == "shred":
        assert snapshot["get"] == (None if new else key_hex)
        assert snapshot["has_reference"] is not new
        assert snapshot["state"] == (None if new else "committed")
        assert snapshot["record_hash"] == (None if new else RECORD_HASH)
        assert snapshot["tombstoned"] is new
        assert snapshot["tombstone_hash"] == (RECORD_HASH if new else None)
        assert snapshot["revision"] == (3 if new else 2)
        assert snapshot["event_credentials"] == (0 if new else 1)
    else:
        raise AssertionError(f"unknown operation: {operation}")
    assert snapshot["profile"] == "os-keyring"
    assert snapshot["head_credentials"] == 1
    assert snapshot["staging_credentials"] == 0


def setup_operation(root: Path, vault_path: Path, operation: str) -> None:
    store = _store(root, vault_path)
    _apply_old_state(store, operation)
    _verify_no_dek_under_root(root)


def crash_init(root: Path, vault_path: Path, boundary: str) -> None:
    _store(root, vault_path, boundary=boundary)
    raise AssertionError(f"boundary did not fire: {boundary}")


def crash_operation(root: Path, vault_path: Path, operation: str, boundary: str) -> None:
    store = _store(root, vault_path, create=False, boundary=boundary)
    _run_operation(store, operation)
    raise AssertionError(f"boundary did not fire: {boundary}")


def verify_init(root: Path, vault_path: Path) -> None:
    store = _store(root, vault_path, create=True)
    store.verify_integrity()
    assert store.revision == 0
    assert tuple(store.iter_references()) == ()
    assert not (root / "init.json").exists()
    assert not any(
        path.name.startswith(f".{root.name}.") and path.name.endswith(".init.tmp")
        for path in root.parent.iterdir()
    )
    rows = _credential_rows(vault_path)
    assert sum(":head:" in row["username"] for row in rows) == 1
    assert not any(":probe:" in row["username"] for row in rows)
    _verify_no_dek_under_root(root)


def verify_operation(root: Path, vault_path: Path, operation: str, expected: str) -> None:
    snapshot = _snapshot(root, vault_path, operation)
    _expect_state(snapshot, operation, expected)
    print(json.dumps(snapshot, sort_keys=True))


def delete_staging_credential(vault_path: Path) -> None:
    with sqlite3.connect(vault_path) as connection:
        cursor = connection.execute(
            "DELETE FROM credentials WHERE username LIKE ?",
            ("%:staging:%",),
        )
    assert cursor.rowcount == 1


def verify_fails_closed(root: Path, vault_path: Path) -> None:
    before_files = _non_vault_file_state(root, vault_path)
    before_rows = _credential_rows(vault_path)
    assert (root / "prepare.json").is_file()
    assert (root / "staged.bin").is_file()
    assert sum(":event:" in row["username"] for row in before_rows) == 0
    assert sum(":staging:" in row["username"] for row in before_rows) == 0
    _install_fake_keyring(vault_path)
    from aluclu.cognition import KeyringRecordKeyStore, LedgerIntegrityError

    try:
        KeyringRecordKeyStore(
            root,
            INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
            service="aluclu-test",
            username_prefix="owner",
            database_path=root.parent / "ledger.sqlite3",
            create=False,
        )
    except LedgerIntegrityError as exc:
        assert str(exc) == "prepared keyring credential is unavailable"
    else:
        raise AssertionError("missing staged credential did not fail closed")

    after_rows = _credential_rows(vault_path)
    assert _non_vault_file_state(root, vault_path) == before_files
    assert after_rows == before_rows
    assert (root / "prepare.json").is_file()
    assert (root / "staged.bin").is_file()
    assert sum(":event:" in row["username"] for row in after_rows) == 0
    assert sum(":staging:" in row["username"] for row in after_rows) == 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action")
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--vault", required=True, type=Path)
    parser.add_argument("--operation", default="")
    parser.add_argument("--boundary", default="")
    parser.add_argument("--expected", default="")
    args = parser.parse_args()

    if args.action == "setup-operation":
        setup_operation(args.root, args.vault, args.operation)
    elif args.action == "crash-init":
        crash_init(args.root, args.vault, args.boundary)
    elif args.action == "crash-operation":
        crash_operation(args.root, args.vault, args.operation, args.boundary)
    elif args.action == "verify-init":
        verify_init(args.root, args.vault)
    elif args.action == "verify-operation":
        verify_operation(args.root, args.vault, args.operation, args.expected)
    elif args.action == "delete-staging-credential":
        delete_staging_credential(args.vault)
    elif args.action == "verify-fails-closed":
        verify_fails_closed(args.root, args.vault)
    else:
        raise SystemExit(f"unknown action: {args.action}")


if __name__ == "__main__":
    main()
