from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
import types
from pathlib import Path


class PersistentRaceKeyringBackend:
    priority = 1

    def __init__(
        self,
        vault_path: Path,
        *,
        ledger_lock_path: Path,
        master_service: str,
        master_username: str,
        barrier_name: str,
        participants: int,
        timeout_seconds: float,
    ) -> None:
        self._vault_path = vault_path
        self._ledger_lock_path = ledger_lock_path
        self._master_service = master_service
        self._master_username = master_username
        self._barrier_name = barrier_name
        self._participants = participants
        self._timeout_seconds = timeout_seconds
        self._master_barrier_used = False
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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pid INTEGER NOT NULL,
                    operation TEXT NOT NULL,
                    service TEXT NOT NULL,
                    username TEXT NOT NULL,
                    password TEXT,
                    observed TEXT,
                    created_ns INTEGER NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS barrier_arrivals (
                    barrier_name TEXT NOT NULL,
                    pid INTEGER NOT NULL,
                    PRIMARY KEY (barrier_name, pid)
                )
                """
            )

    def get_password(self, service: str, username: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT password FROM credentials WHERE service = ? AND username = ?",
                (service, username),
            ).fetchone()
            observed = None if row is None else str(row[0])
            self._log(connection, "get", service, username, None, observed)
        if self._should_wait_at_master_read(service, username, observed):
            self._master_barrier_used = True
            self._wait_for_peer_master_read()
        return observed

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
            self._log(connection, "set", service, username, password, None)

    def delete_password(self, service: str, username: str) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM credentials WHERE service = ? AND username = ?",
                (service, username),
            )
            self._log(connection, "delete", service, username, None, None)
        if cursor.rowcount == 0:
            raise RuntimeError("credential is missing")

    def _should_wait_at_master_read(
        self,
        service: str,
        username: str,
        observed: str | None,
    ) -> bool:
        return (
            service == self._master_service
            and username == self._master_username
            and observed is None
            and not self._master_barrier_used
            and not self._ledger_lock_is_held_by_this_process()
        )

    def _ledger_lock_is_held_by_this_process(self) -> bool:
        from aluclu.cognition.persistence import _held_process_paths

        lock_key = os.path.normcase(os.path.normpath(str(self._ledger_lock_path)))
        return lock_key in _held_process_paths()

    def _wait_for_peer_master_read(self) -> None:
        deadline = time.monotonic() + self._timeout_seconds
        while True:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO barrier_arrivals(barrier_name, pid)
                    VALUES (?, ?)
                    """,
                    (self._barrier_name, os.getpid()),
                )
                arrived = int(
                    connection.execute(
                        """
                        SELECT COUNT(*) FROM barrier_arrivals
                        WHERE barrier_name = ?
                        """,
                        (self._barrier_name,),
                    ).fetchone()[0]
                )
            if arrived >= self._participants:
                return
            if time.monotonic() > deadline:
                raise AssertionError(
                    f"timed out waiting at master-key read barrier: {arrived}/"
                    f"{self._participants} arrived"
                )
            time.sleep(0.02)

    def _log(
        self,
        connection: sqlite3.Connection,
        operation: str,
        service: str,
        username: str,
        password: str | None,
        observed: str | None,
    ) -> None:
        connection.execute(
            """
            INSERT INTO operations(
                pid,
                operation,
                service,
                username,
                password,
                observed,
                created_ns
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                os.getpid(),
                operation,
                service,
                username,
                password,
                observed,
                time.time_ns(),
            ),
        )

    def _connect(self) -> sqlite3.Connection:
        deadline = time.monotonic() + self._timeout_seconds
        while True:
            connection = sqlite3.connect(self._vault_path, timeout=10)
            try:
                connection.execute("PRAGMA journal_mode=WAL")
                connection.execute("PRAGMA synchronous=FULL")
            except sqlite3.OperationalError as exc:
                connection.close()
                transient_lock = any(
                    marker in str(exc).lower() for marker in ("locked", "busy")
                )
                if not transient_lock or time.monotonic() >= deadline:
                    raise
                time.sleep(0.02)
                continue
            return connection


PersistentRaceKeyringBackend.__module__ = "keyring.backends.Windows"


def _install_fake_keyring(
    vault_path: Path,
    *,
    ledger_lock_path: Path,
    master_service: str,
    master_username: str,
    barrier_name: str,
    participants: int,
    timeout_seconds: float,
) -> None:
    backend = PersistentRaceKeyringBackend(
        vault_path,
        ledger_lock_path=ledger_lock_path,
        master_service=master_service,
        master_username=master_username,
        barrier_name=barrier_name,
        participants=participants,
        timeout_seconds=timeout_seconds,
    )
    module = types.ModuleType("keyring")
    module.get_keyring = lambda: backend  # type: ignore[attr-defined]
    module.get_password = backend.get_password  # type: ignore[attr-defined]
    module.set_password = backend.set_password  # type: ignore[attr-defined]
    module.delete_password = backend.delete_password  # type: ignore[attr-defined]
    sys.modules["keyring"] = module


def _open_reopen_and_write(
    ledger_path: Path,
    vault_path: Path,
    worker_id: str,
    *,
    service: str,
    username: str,
    participants: int,
    timeout_seconds: float,
) -> None:
    _install_fake_keyring(
        vault_path,
        ledger_lock_path=ledger_path.with_suffix(ledger_path.suffix + ".lock"),
        master_service=service,
        master_username=username,
        barrier_name=f"master-read:{ledger_path}",
        participants=participants,
        timeout_seconds=timeout_seconds,
    )

    from aluclu.cognition import (
        EncryptedLedger,
        KeyringKeyProvider,
        RecordKeyStoreProfile,
    )

    event_id = f"race_{worker_id}"
    provider = KeyringKeyProvider(service, username, create=True)
    with EncryptedLedger(ledger_path, provider) as ledger:
        outcome = ledger.append_once(event_id, {"worker": worker_id})
        assert (
            ledger._record_store_required().profile is RecordKeyStoreProfile.OS_KEYRING
        )
        sequence = outcome.record.sequence

    with EncryptedLedger(ledger_path, provider) as reopened:
        record = reopened.read(event_id)
        assert record is not None
        assert record.payload == {"worker": worker_id}
        assert (
            reopened._record_store_required().profile
            is RecordKeyStoreProfile.OS_KEYRING
        )
        event_count = reopened.event_count()

    print(
        json.dumps(
            {
                "event_count": event_count,
                "event_id": event_id,
                "sequence": sequence,
                "worker": worker_id,
            },
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--vault", required=True, type=Path)
    parser.add_argument("--worker-id", required=True)
    parser.add_argument("--service", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--participants", required=True, type=int)
    parser.add_argument("--timeout-seconds", required=True, type=float)
    args = parser.parse_args()

    _open_reopen_and_write(
        args.ledger,
        args.vault,
        args.worker_id,
        service=args.service,
        username=args.username,
        participants=args.participants,
        timeout_seconds=args.timeout_seconds,
    )


if __name__ == "__main__":
    main()
