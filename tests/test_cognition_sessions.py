from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import textwrap
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import FrozenInstanceError, dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any, cast

import pytest

import aluclu.cognition.ledger as ledger_module
from aluclu.cognition import (
    EncryptedLedger,
    InputBoundaryError,
    LedgerConflictError,
    LedgerIntegrityError,
    LedgerLifecycleError,
    LedgerSnapshotChanged,
    LedgerVerificationStats,
    StaticKeyProvider,
    VerifiedLedgerCursor,
    atomic_write_bytes,
)
from aluclu.cognition.contracts import JsonValue

MASTER_KEY = b"m" * 32

_CROSS_PROCESS_LOCK_SCRIPT = textwrap.dedent(
    """
    import sys
    from pathlib import Path

    from aluclu.cognition import EncryptedLedger, StaticKeyProvider

    ledger_path = Path(sys.argv[1])
    ready_path = Path(sys.argv[2])
    ledger = EncryptedLedger(ledger_path, StaticKeyProvider(b"m" * 32))
    ready_path.write_text("ready", encoding="utf-8")
    with ledger:
        ledger.append("evt_child", {"source": "child"})
    print("DONE", flush=True)
    """
)


@dataclass
class _SqliteTrace:
    execute_sql: list[str] = field(default_factory=list)
    fetchmany_calls: list[tuple[str, int]] = field(default_factory=list)
    fetchall_sql: list[str] = field(default_factory=list)


class _ObservedCursor:
    def __init__(self, cursor: sqlite3.Cursor, trace: _SqliteTrace) -> None:
        self._cursor = cursor
        self._trace = trace
        self._sql = ""

    def execute(
        self,
        sql: str,
        parameters: Any = (),
    ) -> _ObservedCursor:
        self._sql = _normalized_sql(sql)
        self._trace.execute_sql.append(self._sql)
        self._cursor.execute(sql, parameters)
        return self

    def executemany(
        self,
        sql: str,
        parameters: Any,
    ) -> _ObservedCursor:
        self._sql = _normalized_sql(sql)
        self._trace.execute_sql.append(self._sql)
        self._cursor.executemany(sql, parameters)
        return self

    def fetchone(self) -> tuple[Any, ...] | None:
        return self._cursor.fetchone()

    def fetchmany(self, size: int | None = None) -> list[tuple[Any, ...]]:
        if type(size) is not int or not 1 <= size <= 4096:
            raise AssertionError("streaming reads must use a bounded explicit size")
        self._trace.fetchmany_calls.append((self._sql, size))
        return self._cursor.fetchmany(size)

    def fetchall(self) -> list[tuple[Any, ...]]:
        self._trace.fetchall_sql.append(self._sql)
        raise AssertionError("verified scans and cursors must not call fetchall()")

    def __iter__(self) -> _ObservedCursor:
        return self

    def __next__(self) -> tuple[Any, ...]:
        return next(self._cursor)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._cursor, name)


class _ObservedConnection:
    def __init__(
        self,
        connection: sqlite3.Connection,
        trace: _SqliteTrace,
    ) -> None:
        self._connection = connection
        self._trace = trace

    def execute(
        self,
        sql: str,
        parameters: Any = (),
    ) -> _ObservedCursor:
        cursor = self._connection.cursor()
        return _ObservedCursor(cursor, self._trace).execute(sql, parameters)

    def executemany(self, sql: str, parameters: Any) -> _ObservedCursor:
        cursor = self._connection.cursor()
        return _ObservedCursor(cursor, self._trace).executemany(sql, parameters)

    def cursor(self, *args: Any, **kwargs: Any) -> _ObservedCursor:
        return _ObservedCursor(self._connection.cursor(*args, **kwargs), self._trace)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._connection, name)


class _PrimaryCursorFailure(RuntimeError):
    pass


class _PrimarySessionFailure(RuntimeError):
    pass


class _PrimaryVerificationFailure(RuntimeError):
    pass


class _PrimaryBootstrapFailure(RuntimeError):
    pass


class _BootstrapSetupAbort(RuntimeError):
    pass


class _PendingCleanupFailure(RuntimeError):
    pass


class _CursorCommitFailure(RuntimeError):
    pass


class _CursorRollbackFailure(RuntimeError):
    pass


class _LockContextExitFailure(RuntimeError):
    pass


class _ObjectLockExitFailure(RuntimeError):
    pass


class _PrimaryUnlockFailure(RuntimeError):
    pass


class _CursorReleaseFailure(RuntimeError):
    pass


class _TransactionFailureConnection:
    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        fail_commits: int = 0,
        fail_rollbacks: int = 0,
    ) -> None:
        self._connection = connection
        self._fail_commits = fail_commits
        self._fail_rollbacks = fail_rollbacks
        self.close_calls = 0

    def execute(self, sql: str, parameters: Any = ()) -> sqlite3.Cursor:
        normalized = _normalized_sql(sql)
        if normalized == "commit" and self._fail_commits:
            self._fail_commits -= 1
            raise _CursorCommitFailure("injected cursor commit failure")
        if normalized == "rollback" and self._fail_rollbacks:
            self._fail_rollbacks -= 1
            raise _CursorRollbackFailure("injected cursor rollback failure")
        return self._connection.execute(sql, parameters)

    def cursor(self, *args: Any, **kwargs: Any) -> sqlite3.Cursor:
        return self._connection.cursor(*args, **kwargs)

    def close(self) -> None:
        self.close_calls += 1
        self._connection.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._connection, name)


class _PrimaryStatementFailureConnection(_TransactionFailureConnection):
    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        primary: BaseException,
        fail_on_sql: Callable[[str], bool],
        fail_rollbacks: int = 1,
    ) -> None:
        super().__init__(connection, fail_rollbacks=fail_rollbacks)
        self._primary = primary
        self._fail_on_sql = fail_on_sql
        self._primary_raised = False

    def execute(self, sql: str, parameters: Any = ()) -> sqlite3.Cursor:
        normalized = _normalized_sql(sql)
        if not self._primary_raised and self._fail_on_sql(normalized):
            self._primary_raised = True
            raise self._primary
        return super().execute(sql, parameters)


class _FailingExitLockContext:
    def __init__(self, inner: Any, failure: BaseException) -> None:
        self._inner = inner
        self._failure = failure

    def __enter__(self) -> object:
        return self._inner.__enter__()

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> object:
        self._inner.__exit__(exc_type, exc, traceback)
        raise self._failure


class _FailingExitObjectLock:
    def __init__(self, inner: Any, failure: BaseException) -> None:
        self._inner = inner
        self._failure = failure
        self._armed = True

    def acquire(self, *args: Any, **kwargs: Any) -> object:
        return self._inner.acquire(*args, **kwargs)

    def release(self) -> None:
        self._inner.release()

    def __enter__(self) -> object:
        return self._inner.__enter__()

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> object:
        result = self._inner.__exit__(exc_type, exc, traceback)
        if self._armed:
            self._armed = False
            raise self._failure
        return result


def _normalized_sql(sql: str) -> str:
    return " ".join(sql.casefold().split())


def _assert_object_lock_available_from_other_thread(lock: Any) -> None:
    attempts: list[bool] = []

    def acquire_once() -> None:
        acquired = lock.acquire(timeout=1.0)
        attempts.append(acquired)
        if acquired:
            lock.release()

    worker = threading.Thread(target=acquire_once, daemon=True)
    worker.start()
    worker.join(timeout=2.0)
    assert not worker.is_alive()
    assert attempts == [True]


def _assert_primary_with_cleanup_cause(
    public: BaseException,
    *,
    primary: BaseException,
    cleanup: BaseException,
) -> None:
    assert public is primary
    assert public.__cause__ is cleanup
    seen: set[int] = set()
    pending: list[BaseException] = [public]
    while pending:
        current = pending.pop()
        identity = id(current)
        assert identity not in seen
        seen.add(identity)
        if current.__cause__ is not None:
            pending.append(current.__cause__)
        if current.__context__ is not None:
            pending.append(current.__context__)


def _assert_ledger_path_unmarked(lock_path: Path) -> None:
    assert (
        ledger_module._ledger_path_key(lock_path)
        not in ledger_module._active_ledger_paths()
    )


def _reachable_object_graph(root: object) -> list[object]:
    pending = [root]
    reachable: list[object] = []
    seen: set[int] = set()
    while pending:
        value = pending.pop()
        identity = id(value)
        if identity in seen:
            continue
        seen.add(identity)
        reachable.append(value)
        if isinstance(value, (bytes, str, int, float, bool, type(None))):
            continue
        if is_dataclass(value) and not isinstance(value, type):
            pending.extend(getattr(value, item.name) for item in fields(value))
        elif isinstance(value, Mapping):
            pending.extend(value.keys())
            pending.extend(value.values())
        elif isinstance(value, (list, tuple, set, frozenset)):
            pending.extend(value)
    return reachable


def _call_from_non_owner_thread(
    operation: Callable[[], object],
    *,
    timeout: float = 3.0,
) -> BaseException:
    started = threading.Event()
    finished = threading.Event()
    failures: list[BaseException] = []

    def run() -> None:
        started.set()
        try:
            operation()
        except BaseException as exc:
            failures.append(exc)
        else:
            failures.append(
                AssertionError("non-owner session operation unexpectedly succeeded")
            )
        finally:
            finished.set()

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    if not started.wait(timeout) or not finished.wait(timeout):
        return TimeoutError("non-owner session operation did not fail promptly")
    worker.join(timeout=0.25)
    if worker.is_alive() or len(failures) != 1:
        return TimeoutError("non-owner session operation did not terminate cleanly")
    return failures[0]


def _touch_valid_metadata_from_external_connection(path: Path) -> None:
    external = sqlite3.connect(path, isolation_level=None, timeout=30.0)
    try:
        external.execute("PRAGMA busy_timeout = 30000")
        external.execute("BEGIN IMMEDIATE")
        external.execute(
            "UPDATE metadata SET value = X'3033' WHERE key = 'schema_version'"
        )
        external.execute(
            "UPDATE metadata SET value = X'33' WHERE key = 'schema_version'"
        )
        external.execute("COMMIT")
    finally:
        if external.in_transaction:
            external.execute("ROLLBACK")
        external.close()


def _try_valid_metadata_commit_from_external_connection(path: Path) -> str:
    external = sqlite3.connect(path, isolation_level=None, timeout=0.0)
    try:
        external.execute("PRAGMA busy_timeout = 0")
        try:
            external.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError as exc:
            if "locked" in str(exc).lower():
                return "blocked"
            raise
        external.execute(
            "UPDATE metadata SET value = X'3033' WHERE key = 'schema_version'"
        )
        external.execute(
            "UPDATE metadata SET value = X'33' WHERE key = 'schema_version'"
        )
        external.execute("COMMIT")
        return "committed"
    finally:
        if external.in_transaction:
            external.execute("ROLLBACK")
        external.close()


def _repoint_live_projection_from_external_connection(path: Path) -> None:
    external = sqlite3.connect(path, isolation_level=None, timeout=30.0)
    try:
        external.execute("PRAGMA busy_timeout = 30000")
        external.execute("BEGIN IMMEDIATE")
        external.execute("DELETE FROM records WHERE event_id = 'evt_b'")
        external.execute(
            """
            UPDATE records
            SET history_sequence = (
                    SELECT sequence FROM history
                    WHERE event_id = 'evt_b' AND operation = 'append'
                ),
                record_hash = (
                    SELECT record_hash FROM history
                    WHERE event_id = 'evt_b' AND operation = 'append'
                )
            WHERE event_id = 'evt_a'
            """
        )
        external.execute("COMMIT")
    finally:
        if external.in_transaction:
            external.execute("ROLLBACK")
        external.close()


def _rewrite_anchor_without_changing_head(anchor_path: Path) -> None:
    envelope = json.loads(anchor_path.read_bytes())
    rewritten = json.dumps(envelope, indent=2, sort_keys=True).encode("utf-8")
    assert rewritten != anchor_path.read_bytes()
    atomic_write_bytes(anchor_path, rewritten)


def test_session_and_cursor_contexts_fail_closed_after_close(tmp_path: Path) -> None:
    ledger = EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    )
    with pytest.raises(LedgerLifecycleError):
        ledger.verified_session()

    ledger.unlock()
    session = ledger.verified_session()
    with session as entered:
        assert entered is session
        assert session.event_count() == 0
        cursor = session.cursor()

    session.close()
    with pytest.raises(LedgerLifecycleError):
        session.event_count()
    with pytest.raises(LedgerLifecycleError):
        session.cursor()
    with pytest.raises(LedgerLifecycleError):
        session.authenticated_tombstoned_append_witness(
            witness_schema="aluclu.test-witness.v1",
            link_digest="0" * 64,
            after_sequence=0,
            before_sequence=1,
        )
    with pytest.raises(LedgerLifecycleError):
        next(cursor)

    ledger.close()
    with pytest.raises(LedgerLifecycleError):
        ledger.verified_session()


@pytest.mark.parametrize(
    "operation_name",
    [
        "session_method",
        "authenticated_witness",
        "session_close",
        "cursor_next",
        "cursor_suspend",
    ],
)
def test_session_and_cursor_are_strictly_thread_owned(
    tmp_path: Path,
    operation_name: str,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        ledger.append("evt_1", {"index": 1})
        session = ledger.verified_session()
        cursor = session.cursor(batch_size=1)
        operations: dict[str, Callable[[], object]] = {
            "session_method": session.event_count,
            "authenticated_witness": lambda: session.authenticated_tombstoned_append_witness(
                witness_schema="aluclu.test-witness.v1",
                link_digest="0" * 64,
                after_sequence=0,
                before_sequence=1,
            ),
            "session_close": session.close,
            "cursor_next": lambda: next(cursor),
            "cursor_suspend": cursor.suspend,
        }
        try:
            failure = _call_from_non_owner_thread(operations[operation_name])

            assert isinstance(failure, LedgerLifecycleError)
            assert session.event_count() == 1
            assert next(cursor).event_id == "evt_1"
        finally:
            session.close()


def test_unlock_refresh_failure_leaves_closed_retriable_lifecycle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class RefreshFailure(RuntimeError):
        pass

    ledger = EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    )
    original_refresh = ledger._refresh_verification_certificate_locked
    refresh_calls = 0

    def fail_once(*, expected: Any = None) -> None:
        nonlocal refresh_calls
        refresh_calls += 1
        if refresh_calls == 1:
            raise RefreshFailure("injected certificate refresh failure")
        original_refresh(expected=expected)

    monkeypatch.setattr(
        ledger,
        "_refresh_verification_certificate_locked",
        fail_once,
    )
    try:
        with pytest.raises(RefreshFailure):
            ledger.unlock()
        with pytest.raises(LedgerLifecycleError):
            ledger.verified_session()

        ledger.unlock()
        with ledger.verified_session() as session:
            outcome = session.append("evt_recovered", {"recovered": True})
            assert outcome.created is True
            assert session.read("evt_recovered") == outcome.record
    finally:
        ledger.close()


def test_one_full_verification_is_reused_by_many_short_and_long_sessions(
    tmp_path: Path,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        assert ledger.verification_stats == LedgerVerificationStats(
            full_verifications=1,
            delta_verifications=0,
        )

        for _ in range(7):
            assert ledger.event_count() == 0

        assert ledger.verification_stats == LedgerVerificationStats(
            full_verifications=1,
            delta_verifications=7,
        )

        with ledger.verified_session() as session:
            assert session.event_count() == 0
            assert session.read("evt_missing") is None
            assert session.is_tombstoned("evt_missing") is False

        assert ledger.verification_stats == LedgerVerificationStats(
            full_verifications=1,
            delta_verifications=8,
        )


def test_explicit_integrity_checks_always_run_full_and_stats_are_frozen(
    tmp_path: Path,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        ledger.event_count()
        before = ledger.verification_stats
        assert before == LedgerVerificationStats(
            full_verifications=1,
            delta_verifications=1,
        )
        with pytest.raises(FrozenInstanceError):
            before.full_verifications = 99  # type: ignore[misc]

        ledger.verify_integrity()
        first = ledger.verification_stats
        ledger.verify_integrity()
        second = ledger.verification_stats

        assert first == LedgerVerificationStats(
            full_verifications=2,
            delta_verifications=1,
        )
        assert second == LedgerVerificationStats(
            full_verifications=3,
            delta_verifications=1,
        )


def test_unknown_exception_escaping_session_invalidates_certificate(
    tmp_path: Path,
) -> None:
    class UnknownSessionFailure(Exception):
        pass

    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        with pytest.raises(UnknownSessionFailure):
            with ledger.verified_session() as session:
                assert session.event_count() == 0
                raise UnknownSessionFailure

        assert ledger.verification_stats == LedgerVerificationStats(
            full_verifications=1,
            delta_verifications=1,
        )
        assert ledger.event_count() == 0
        assert ledger.verification_stats == LedgerVerificationStats(
            full_verifications=2,
            delta_verifications=1,
        )


def test_base_exception_during_pending_append_cleans_and_releases_session(
    tmp_path: Path,
) -> None:
    class InjectedAbort(BaseException):
        pass

    armed = True

    def inject(boundary: str) -> None:
        nonlocal armed
        if armed and boundary == "after_pending_key_before_sqlite_insert":
            armed = False
            raise InjectedAbort("injected non-Exception abort")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
        _fault_injector=inject,
    ) as ledger:
        failed_session = None
        with pytest.raises(InjectedAbort):
            with ledger.verified_session() as failed_session:
                failed_session.append("evt_aborted", {"value": "discard"})

        assert failed_session is not None
        with pytest.raises(LedgerLifecycleError):
            failed_session.event_count()

        connection = ledger._connection_required()
        store = ledger._record_store_required()
        transaction_was_open = connection.in_transaction
        orphan_after_abort = store.reference("evt_aborted")
        tombstone_after_abort = store.tombstone_hash("evt_aborted")

        with ledger.verified_session() as fresh:
            outcome = fresh.append("evt_recovered", {"value": "committed"})
            assert fresh.event_count() == 1

        assert transaction_was_open is False
        assert orphan_after_abort is None
        assert tombstone_after_abort is None
        assert outcome.created is True
        assert ledger.read("evt_aborted") is None
        assert store.reference("evt_aborted") is None
        assert ledger.verification_stats == LedgerVerificationStats(
            full_verifications=2,
            delta_verifications=2,
        )


def test_tampered_anchor_invalidates_certificate_and_restores_cleanly(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    anchor_path = path.with_suffix(path.suffix + ".anchor.json")
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        ledger.event_count()
        before = ledger.verification_stats
        assert before == LedgerVerificationStats(
            full_verifications=1,
            delta_verifications=1,
        )
        original = anchor_path.read_bytes()
        tampered = bytearray(original)
        tampered[-1] ^= 1
        atomic_write_bytes(anchor_path, bytes(tampered))
        try:
            with pytest.raises(LedgerIntegrityError):
                ledger.event_count()
        finally:
            atomic_write_bytes(anchor_path, original)

        assert anchor_path.read_bytes() == original
        assert ledger.verification_stats == before
        assert ledger.event_count() == 0
        assert ledger.verification_stats == LedgerVerificationStats(
            full_verifications=2,
            delta_verifications=1,
        )


def test_store_revision_change_forces_full_recovery_without_residue(
    tmp_path: Path,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        ledger.event_count()
        before = ledger.verification_stats
        assert before == LedgerVerificationStats(
            full_verifications=1,
            delta_verifications=1,
        )
        store = ledger._record_store_required()
        revision_before = store.revision

        store.put_pending("evt_orphan", b"k" * 32)
        assert store.revision > revision_before
        assert store.reference("evt_orphan") is not None

        assert ledger.event_count() == 0
        assert ledger.verification_stats == LedgerVerificationStats(
            full_verifications=before.full_verifications + 1,
            delta_verifications=before.delta_verifications,
        )
        assert store.reference("evt_orphan") is None
        assert store.is_tombstoned("evt_orphan") is False


def test_external_sqlite_data_version_change_invalidates_certificate(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        ledger.event_count()
        connection = ledger._connection_required()
        version_before = connection.execute("PRAGMA data_version").fetchone()[0]
        stats_before = ledger.verification_stats
        assert stats_before == LedgerVerificationStats(
            full_verifications=1,
            delta_verifications=1,
        )

        _touch_valid_metadata_from_external_connection(path)

        version_after = connection.execute("PRAGMA data_version").fetchone()[0]
        assert version_after > version_before
        assert ledger.event_count() == 0
        assert ledger.verification_stats == LedgerVerificationStats(
            full_verifications=stats_before.full_verifications + 1,
            delta_verifications=stats_before.delta_verifications,
        )


@pytest.mark.parametrize("target", ["database", "wal"])
def test_file_fingerprint_only_change_invalidates_certificate(
    tmp_path: Path,
    target: str,
) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        ledger.append("evt_1", {"index": 1})
        assert ledger.event_count() == 1
        before = ledger.verification_stats
        target_path = path if target == "database" else Path(f"{path}-wal")
        target_stat = target_path.stat()

        os.utime(
            target_path,
            ns=(target_stat.st_atime_ns, target_stat.st_mtime_ns + 1_000_000),
        )

        assert ledger.event_count() == 1
        assert ledger.verification_stats == LedgerVerificationStats(
            full_verifications=before.full_verifications + 1,
            delta_verifications=before.delta_verifications,
        )


def test_same_connection_append_and_shred_refresh_without_full_rescan(
    tmp_path: Path,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        connection = ledger._connection_required()
        initial_data_version = connection.execute("PRAGMA data_version").fetchone()[0]

        ledger.append("evt_1", {"index": 1})
        after_append = ledger.verification_stats
        assert connection.execute("PRAGMA data_version").fetchone()[0] == (
            initial_data_version
        )
        assert after_append == LedgerVerificationStats(
            full_verifications=1,
            delta_verifications=1,
        )

        assert ledger.shred("evt_1") is True
        assert connection.execute("PRAGMA data_version").fetchone()[0] == (
            initial_data_version
        )
        assert ledger.verification_stats == LedgerVerificationStats(
            full_verifications=1,
            delta_verifications=2,
        )
        assert ledger.is_tombstoned("evt_1") is True
        assert ledger.verification_stats == LedgerVerificationStats(
            full_verifications=1,
            delta_verifications=3,
        )


def test_failed_clean_session_close_invalidates_certificate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class InjectedCloseFailure(RuntimeError):
        pass

    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        session = ledger.verified_session()
        assert session.event_count() == 0
        original_close_verification = ledger._close_verified_session_locked

        def fail_close_verification() -> None:
            raise InjectedCloseFailure("injected clean-close verification failure")

        monkeypatch.setattr(
            ledger,
            "_close_verified_session_locked",
            fail_close_verification,
        )
        with pytest.raises(InjectedCloseFailure):
            session.close()
        monkeypatch.setattr(
            ledger,
            "_close_verified_session_locked",
            original_close_verification,
        )

        before_recovery = ledger.verification_stats
        assert before_recovery == LedgerVerificationStats(
            full_verifications=1,
            delta_verifications=1,
        )
        assert ledger.event_count() == 0
        assert ledger.verification_stats == LedgerVerificationStats(
            full_verifications=2,
            delta_verifications=1,
        )


def test_explicit_full_verification_rejects_external_commit_before_certificate(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    armed = False

    def inject(boundary: str) -> None:
        nonlocal armed
        if armed and boundary == "after_full_verification_commit_before_certificate":
            armed = False
            _touch_valid_metadata_from_external_connection(path)

    with EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        _fault_injector=inject,
    ) as ledger:
        ledger.append("evt_1", {"index": 1})
        before = ledger.verification_stats
        armed = True

        with pytest.raises(LedgerIntegrityError):
            ledger.verify_integrity()

        assert ledger.verification_stats == LedgerVerificationStats(
            full_verifications=before.full_verifications + 1,
            delta_verifications=before.delta_verifications,
        )
        assert ledger.event_count() == 1
        assert ledger.verification_stats == LedgerVerificationStats(
            full_verifications=before.full_verifications + 2,
            delta_verifications=before.delta_verifications,
        )


def test_existing_unlock_rejects_external_commit_before_certificate(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as initial:
        initial.append("evt_1", {"index": 1})

    armed = True

    def inject(boundary: str) -> None:
        nonlocal armed
        if armed and boundary == "after_full_verification_commit_before_certificate":
            armed = False
            _touch_valid_metadata_from_external_connection(path)

    reopened = EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        _fault_injector=inject,
    )
    try:
        with pytest.raises(LedgerIntegrityError):
            reopened.unlock()
        with pytest.raises(LedgerLifecycleError):
            reopened.verified_session()

        reopened.unlock()
        assert reopened.event_count() == 1
    finally:
        reopened.close()


def test_fresh_unlock_primary_survives_file_lock_exit_failure_after_certificate_gap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "memory.sqlite3"
    primary = _PrimaryUnlockFailure("injected fresh-unlock primary failure")
    cleanup = _LockContextExitFailure("injected fresh-unlock file-lock exit failure")
    armed = True

    def inject(boundary: str) -> None:
        nonlocal armed
        if armed and boundary == "after_full_verification_commit_before_certificate":
            armed = False
            raise primary

    original_lock_factory = ledger_module.exclusive_file_lock
    wrapped = False

    def fail_first_lock_exit(lock_path: Path) -> _FailingExitLockContext | object:
        nonlocal wrapped
        inner = original_lock_factory(lock_path)
        if wrapped:
            return inner
        wrapped = True
        return _FailingExitLockContext(inner, cleanup)

    ledger = EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        _fault_injector=inject,
    )
    with monkeypatch.context() as local_patch:
        local_patch.setattr(
            ledger_module,
            "exclusive_file_lock",
            fail_first_lock_exit,
        )

        with pytest.raises(_PrimaryUnlockFailure) as caught:
            ledger.unlock()

    _assert_primary_with_cleanup_cause(
        caught.value,
        primary=primary,
        cleanup=cleanup,
    )
    assert ledger._connection is None
    assert ledger._record_store is None
    assert ledger._verification_certificate is None
    assert not ledger._open
    _assert_ledger_path_unmarked(ledger._lock_path)
    _assert_object_lock_available_from_other_thread(ledger._object_lock)
    with pytest.raises(LedgerLifecycleError):
        ledger.verified_session()

    ledger.unlock()
    try:
        assert ledger.event_count() == 0
    finally:
        ledger.close()


def test_existing_unlock_primary_survives_file_lock_exit_failure_after_certificate_gap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as original:
        original.append("evt_1", {"index": 1})

    primary = _PrimaryUnlockFailure("injected existing-unlock primary failure")
    cleanup = _LockContextExitFailure("injected existing-unlock file-lock exit failure")
    armed = True

    def inject(boundary: str) -> None:
        nonlocal armed
        if armed and boundary == "after_full_verification_commit_before_certificate":
            armed = False
            raise primary

    original_lock_factory = ledger_module.exclusive_file_lock
    wrapped = False

    def fail_first_lock_exit(lock_path: Path) -> _FailingExitLockContext | object:
        nonlocal wrapped
        inner = original_lock_factory(lock_path)
        if wrapped:
            return inner
        wrapped = True
        return _FailingExitLockContext(inner, cleanup)

    reopened = EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        _fault_injector=inject,
    )
    with monkeypatch.context() as local_patch:
        local_patch.setattr(
            ledger_module,
            "exclusive_file_lock",
            fail_first_lock_exit,
        )

        with pytest.raises(_PrimaryUnlockFailure) as caught:
            reopened.unlock()

    _assert_primary_with_cleanup_cause(
        caught.value,
        primary=primary,
        cleanup=cleanup,
    )
    assert reopened._connection is None
    assert reopened._record_store is None
    assert reopened._verification_certificate is None
    assert not reopened._open
    _assert_ledger_path_unmarked(reopened._lock_path)
    _assert_object_lock_available_from_other_thread(reopened._object_lock)
    with pytest.raises(LedgerLifecycleError):
        reopened.verified_session()

    reopened.unlock()
    try:
        assert reopened.event_count() == 1
    finally:
        reopened.close()


def test_public_verify_primary_survives_file_lock_exit_failure_after_certificate_gap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "memory.sqlite3"
    primary = _PrimaryVerificationFailure("injected public-verify primary failure")
    cleanup = _LockContextExitFailure("injected public-verify file-lock exit failure")
    armed = False

    def inject(boundary: str) -> None:
        nonlocal armed
        if armed and boundary == "after_full_verification_commit_before_certificate":
            armed = False
            raise primary

    original_lock_factory = ledger_module.exclusive_file_lock
    wrapped = False

    def fail_first_lock_exit(lock_path: Path) -> _FailingExitLockContext | object:
        nonlocal wrapped
        inner = original_lock_factory(lock_path)
        if wrapped:
            return inner
        wrapped = True
        return _FailingExitLockContext(inner, cleanup)

    with EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        _fault_injector=inject,
    ) as ledger:
        ledger.append("evt_1", {"index": 1})
        armed = True
        with monkeypatch.context() as local_patch:
            local_patch.setattr(
                ledger_module,
                "exclusive_file_lock",
                fail_first_lock_exit,
            )

            with pytest.raises(_PrimaryVerificationFailure) as caught:
                ledger.verify_integrity()

        _assert_primary_with_cleanup_cause(
            caught.value,
            primary=primary,
            cleanup=cleanup,
        )
        assert ledger._verification_certificate is None
        _assert_ledger_path_unmarked(ledger._lock_path)
        _assert_object_lock_available_from_other_thread(ledger._object_lock)
        assert ledger.event_count() == 1


def test_fresh_unlock_primary_survives_object_lock_exit_failure_after_certificate_gap(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    primary = _PrimaryUnlockFailure("injected fresh-unlock primary failure")
    cleanup = _ObjectLockExitFailure("injected fresh-unlock object-lock exit failure")
    armed = True

    def inject(boundary: str) -> None:
        nonlocal armed
        if armed and boundary == "after_full_verification_commit_before_certificate":
            armed = False
            raise primary

    ledger = EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        _fault_injector=inject,
    )
    raw_object_lock = ledger._object_lock
    ledger._object_lock = cast(
        Any,
        _FailingExitObjectLock(raw_object_lock, cleanup),
    )

    with pytest.raises(_PrimaryUnlockFailure) as caught:
        ledger.unlock()

    _assert_primary_with_cleanup_cause(
        caught.value,
        primary=primary,
        cleanup=cleanup,
    )
    assert ledger._connection is None
    assert ledger._record_store is None
    assert ledger._verification_certificate is None
    assert not ledger._open
    _assert_ledger_path_unmarked(ledger._lock_path)
    _assert_object_lock_available_from_other_thread(ledger._object_lock)
    with pytest.raises(LedgerLifecycleError):
        ledger.verified_session()

    ledger._object_lock = raw_object_lock
    ledger.unlock()
    try:
        assert ledger.event_count() == 0
    finally:
        ledger.close()


def test_existing_unlock_primary_survives_object_lock_exit_failure_after_certificate_gap(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as original:
        original.append("evt_1", {"index": 1})

    primary = _PrimaryUnlockFailure("injected existing-unlock primary failure")
    cleanup = _ObjectLockExitFailure(
        "injected existing-unlock object-lock exit failure"
    )
    armed = True

    def inject(boundary: str) -> None:
        nonlocal armed
        if armed and boundary == "after_full_verification_commit_before_certificate":
            armed = False
            raise primary

    reopened = EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        _fault_injector=inject,
    )
    raw_object_lock = reopened._object_lock
    reopened._object_lock = cast(
        Any,
        _FailingExitObjectLock(raw_object_lock, cleanup),
    )

    with pytest.raises(_PrimaryUnlockFailure) as caught:
        reopened.unlock()

    _assert_primary_with_cleanup_cause(
        caught.value,
        primary=primary,
        cleanup=cleanup,
    )
    assert reopened._connection is None
    assert reopened._record_store is None
    assert reopened._verification_certificate is None
    assert not reopened._open
    _assert_ledger_path_unmarked(reopened._lock_path)
    _assert_object_lock_available_from_other_thread(reopened._object_lock)
    with pytest.raises(LedgerLifecycleError):
        reopened.verified_session()

    reopened._object_lock = raw_object_lock
    reopened.unlock()
    try:
        assert reopened.event_count() == 1
    finally:
        reopened.close()


def test_public_verify_primary_survives_object_lock_exit_failure_after_certificate_gap(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    primary = _PrimaryVerificationFailure("injected public-verify primary failure")
    cleanup = _ObjectLockExitFailure("injected public-verify object-lock exit failure")
    armed = False

    def inject(boundary: str) -> None:
        nonlocal armed
        if armed and boundary == "after_full_verification_commit_before_certificate":
            armed = False
            raise primary

    with EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        _fault_injector=inject,
    ) as ledger:
        ledger.append("evt_1", {"index": 1})
        raw_object_lock = ledger._object_lock
        ledger._object_lock = cast(
            Any,
            _FailingExitObjectLock(raw_object_lock, cleanup),
        )

        armed = True
        with pytest.raises(_PrimaryVerificationFailure) as caught:
            ledger.verify_integrity()

        _assert_primary_with_cleanup_cause(
            caught.value,
            primary=primary,
            cleanup=cleanup,
        )
        assert ledger._verification_certificate is None
        _assert_ledger_path_unmarked(ledger._lock_path)
        _assert_object_lock_available_from_other_thread(ledger._object_lock)

        ledger._object_lock = raw_object_lock
        assert ledger.event_count() == 1


def test_unlock_callback_cannot_reenter_same_ledger_path(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as initial:
        initial.append("evt_1", {"index": 1})

    peer = EncryptedLedger(path, StaticKeyProvider(MASTER_KEY))
    peer.unlock()
    observed: list[BaseException] = []

    def inject(boundary: str) -> None:
        if boundary != "after_full_verification_commit_before_certificate":
            return
        try:
            peer.append("evt_forbidden", {"index": 2})
        except BaseException as exc:
            observed.append(exc)

    reopened = EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        _fault_injector=inject,
    )
    try:
        reopened.unlock()
        assert len(observed) == 1
        assert isinstance(observed[0], LedgerLifecycleError)
        assert reopened.event_count() == 1
        peer.append("evt_allowed", {"index": 2})
        assert reopened.event_count() == 2
    finally:
        reopened.close()
        peer.close()


def test_explicit_verify_callback_cannot_reenter_same_ledger_path(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    armed = False
    observed: list[BaseException] = []
    peer: EncryptedLedger | None = None

    def inject(boundary: str) -> None:
        if not armed or boundary != "after_full_verification_commit_before_certificate":
            return
        assert peer is not None
        try:
            peer.append("evt_forbidden", {"index": 2})
        except BaseException as exc:
            observed.append(exc)

    ledger = EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        _fault_injector=inject,
    )
    ledger.unlock()
    ledger.append("evt_1", {"index": 1})
    peer = EncryptedLedger(path, StaticKeyProvider(MASTER_KEY))
    peer.unlock()
    try:
        armed = True
        ledger.verify_integrity()
        armed = False
        assert len(observed) == 1
        assert isinstance(observed[0], LedgerLifecycleError)
        assert ledger.event_count() == 1
        peer.append("evt_allowed", {"index": 2})
        assert ledger.event_count() == 2
    finally:
        peer.close()
        ledger.close()


@pytest.mark.parametrize(
    ("operation", "boundary"),
    [
        ("append", "after_append_anchor_before_certificate"),
        ("shred", "after_shred_anchor_before_certificate"),
    ],
)
def test_mutation_rejects_external_commit_before_certificate(
    tmp_path: Path,
    operation: str,
    boundary: str,
) -> None:
    path = tmp_path / "memory.sqlite3"
    armed = False

    def inject(observed: str) -> None:
        nonlocal armed
        if armed and observed == boundary:
            armed = False
            _touch_valid_metadata_from_external_connection(path)

    with EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        _fault_injector=inject,
    ) as ledger:
        if operation == "shred":
            ledger.append("evt_target", {"index": 1})
        before = ledger.verification_stats
        armed = True

        with pytest.raises(LedgerIntegrityError):
            if operation == "append":
                ledger.append("evt_target", {"index": 1})
            else:
                ledger.shred("evt_target")

        assert ledger.verification_stats == LedgerVerificationStats(
            full_verifications=before.full_verifications,
            delta_verifications=before.delta_verifications + 1,
        )
        if operation == "append":
            assert ledger.event_count() == 1
            assert ledger.read("evt_target") is not None
        else:
            assert ledger.is_tombstoned("evt_target") is True
            assert ledger.read("evt_target") is None
        assert ledger.verification_stats.full_verifications == (
            before.full_verifications + 1
        )


def test_session_full_fallback_rejects_external_commit_before_certificate(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    armed = False

    def inject(boundary: str) -> None:
        nonlocal armed
        if armed and boundary == "after_full_verification_commit_before_certificate":
            armed = False
            _touch_valid_metadata_from_external_connection(path)

    with EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        _fault_injector=inject,
    ) as ledger:
        ledger.append("evt_1", {"index": 1})
        _touch_valid_metadata_from_external_connection(path)
        before = ledger.verification_stats
        armed = True

        with pytest.raises(LedgerIntegrityError):
            ledger.verified_session()

        assert ledger.verification_stats == LedgerVerificationStats(
            full_verifications=before.full_verifications + 1,
            delta_verifications=before.delta_verifications,
        )
        assert ledger.event_count() == 1
        assert ledger.verification_stats == LedgerVerificationStats(
            full_verifications=before.full_verifications + 2,
            delta_verifications=before.delta_verifications,
        )


def test_certificate_refresh_rejects_anchor_digest_change_with_same_head(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "memory.sqlite3"
    anchor_path = path.with_suffix(path.suffix + ".anchor.json")
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        ledger.append("evt_1", {"index": 1})
        original_advance = ledger._advance_verified_anchor
        armed = True

        def advance_then_rewrite_anchor(verification: Any) -> Any:
            nonlocal armed
            expectation = original_advance(verification)
            if armed:
                armed = False
                _rewrite_anchor_without_changing_head(anchor_path)
            return expectation

        monkeypatch.setattr(
            ledger,
            "_advance_verified_anchor",
            advance_then_rewrite_anchor,
        )
        before = ledger.verification_stats

        with pytest.raises(LedgerIntegrityError):
            ledger.verify_integrity()

        assert ledger.verification_stats == LedgerVerificationStats(
            full_verifications=before.full_verifications + 1,
            delta_verifications=before.delta_verifications,
        )
        assert ledger.event_count() == 1
        assert ledger.verification_stats == LedgerVerificationStats(
            full_verifications=before.full_verifications + 2,
            delta_verifications=before.delta_verifications,
        )


def test_second_ledger_object_has_no_shared_certificate(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    first = EncryptedLedger(path, StaticKeyProvider(MASTER_KEY))
    first.unlock()
    try:
        first.event_count()
        first_before = first.verification_stats
        assert first_before == LedgerVerificationStats(
            full_verifications=1,
            delta_verifications=1,
        )

        with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as second:
            assert second.verification_stats == LedgerVerificationStats(
                full_verifications=1,
                delta_verifications=0,
            )
            second.append("evt_external", {"source": "second-object"})

        assert first.verification_stats == first_before
        assert first.event_count() == 1
        assert first.verification_stats == LedgerVerificationStats(
            full_verifications=first_before.full_verifications + 1,
            delta_verifications=first_before.delta_verifications,
        )
    finally:
        first.close()


@pytest.mark.parametrize(
    "operation_name",
    ["read", "is_tombstoned", "event_count", "cursor", "resume_verified"],
)
def test_active_session_rejects_external_commit_before_returning_data(
    tmp_path: Path,
    operation_name: str,
) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        record = ledger.append("evt_1", {"secret": "must-not-return"}).record
        with ledger.verified_session() as setup_session:
            checkpoint = setup_session.cursor(batch_size=1).suspend()

        with ledger.verified_session() as session:
            operations: dict[str, Callable[[], object]] = {
                "read": lambda: session.read("evt_1"),
                "is_tombstoned": lambda: session.is_tombstoned("evt_1"),
                "event_count": session.event_count,
                "cursor": lambda: session.cursor(batch_size=1),
                "resume_verified": lambda: session.resume_verified(
                    checkpoint,
                    batch_size=1,
                ),
            }
            _touch_valid_metadata_from_external_connection(path)

            with pytest.raises(LedgerIntegrityError):
                operations[operation_name]()

        assert ledger.event_count() == 1
        assert ledger.read("evt_1") == record


def test_active_cursor_rejects_external_commit_before_returning_next_record(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        ledger.append("evt_1", {"secret": "must-not-return"})

        with ledger.verified_session() as session:
            cursor = session.cursor(batch_size=1)
            _touch_valid_metadata_from_external_connection(path)

            with pytest.raises(LedgerIntegrityError):
                next(cursor)

        assert ledger.event_count() == 1


def test_cursor_next_fences_external_writer_while_fetching_and_decrypting_row(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        expected = ledger.append("evt_1", {"secret": "must-return"}).record
        attempts: list[str] = []
        original_decrypt_row = ledger._decrypt_row

        def decrypt_with_external_writer_attempt(row: object) -> object:
            attempts.append(_try_valid_metadata_commit_from_external_connection(path))
            return original_decrypt_row(row)  # type: ignore[arg-type]

        monkeypatch.setattr(ledger, "_decrypt_row", decrypt_with_external_writer_attempt)

        with ledger.verified_session() as session:
            cursor = session.cursor(batch_size=1)

            assert next(cursor) == expected

        assert attempts == ["blocked"]
        assert ledger.event_count() == 1


def test_cursor_next_fences_external_writer_while_returning_prefetched_row(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        first = ledger.append("evt_1", {"secret": "first"}).record
        second = ledger.append("evt_2", {"secret": "second"}).record
        attempts: list[str] = []
        original_record = ledger_module.LedgerRecord

        def record_with_external_writer_attempt(**kwargs: object) -> object:
            if kwargs.get("event_id") == "evt_2":
                attempts.append(_try_valid_metadata_commit_from_external_connection(path))
            return original_record(**kwargs)  # type: ignore[arg-type]

        monkeypatch.setattr(ledger_module, "LedgerRecord", record_with_external_writer_attempt)

        with ledger.verified_session() as session:
            cursor = session.cursor(batch_size=2)
            assert next(cursor) == first

            assert next(cursor) == second

        assert attempts == ["blocked"]
        assert ledger.event_count() == 2


def test_cursor_dependency_stop_iteration_is_integrity_failure_not_exhaustion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        ledger.append("evt_1", {"secret": "must-not-truncate"})

        def unexpected_stop(_row: object) -> object:
            raise StopIteration("injected dependency truncation")

        monkeypatch.setattr(ledger, "_decrypt_row", unexpected_stop)
        with ledger.verified_session() as session:
            cursor = session.cursor(batch_size=1)

            with pytest.raises(LedgerIntegrityError) as caught:
                list(cursor)

            assert isinstance(caught.value.__cause__, StopIteration)
            assert session._poisoned
            assert cursor not in session._cursors
            assert not ledger._connection_required().in_transaction
            assert ledger._verification_certificate is None
            with pytest.raises(LedgerLifecycleError):
                next(cursor)


def test_cursor_primary_failure_survives_rollback_failure_and_always_cleans_up(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        ledger.append("evt_1", {"secret": "must-not-return"})

        def fail_decrypt(_row: object) -> object:
            raise _PrimaryCursorFailure("injected primary cursor failure")

        monkeypatch.setattr(ledger, "_decrypt_row", fail_decrypt)
        with ledger.verified_session() as session:
            cursor = session.cursor(batch_size=1)
            real_connection = ledger._connection_required()
            faulting = _TransactionFailureConnection(
                real_connection,
                fail_rollbacks=1,
            )
            ledger._connection = cast(Any, faulting)

            with pytest.raises(_PrimaryCursorFailure) as caught:
                next(cursor)

            assert isinstance(caught.value.__cause__, _CursorRollbackFailure)
            assert session._poisoned
            assert cursor not in session._cursors
            assert faulting.in_transaction
            assert ledger._verification_certificate is None
            with pytest.raises(LedgerLifecycleError):
                next(cursor)

        assert not faulting.in_transaction


def test_cursor_exhaustion_commit_and_rollback_failure_never_looks_clean(
    tmp_path: Path,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        with ledger.verified_session() as session:
            cursor = session.cursor(batch_size=1)
            real_connection = ledger._connection_required()
            faulting = _TransactionFailureConnection(
                real_connection,
                fail_commits=1,
                fail_rollbacks=1,
            )
            ledger._connection = cast(Any, faulting)

            with pytest.raises(_CursorCommitFailure) as caught:
                next(cursor)

            assert isinstance(caught.value.__cause__, _CursorRollbackFailure)
            assert cursor._exhausted
            assert session._poisoned
            assert cursor not in session._cursors
            assert faulting.in_transaction
            assert ledger._verification_certificate is None
            with pytest.raises(LedgerLifecycleError):
                next(cursor)

        assert not faulting.in_transaction


@pytest.mark.parametrize(
    "operation_name",
    ["append", "read", "shred", "is_tombstoned", "event_count"],
)
def test_non_cursor_operation_preserves_primary_when_rollback_also_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation_name: str,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        session = ledger.verified_session()
        faulting: _TransactionFailureConnection | None = None
        try:
            def fail_after_begin() -> object:
                raise _PrimarySessionFailure(
                    f"injected {operation_name} primary failure"
                )

            monkeypatch.setattr(
                ledger,
                "_require_current_verification_certificate_locked",
                fail_after_begin,
            )
            real_connection = ledger._connection_required()
            faulting = _TransactionFailureConnection(
                real_connection,
                fail_rollbacks=1,
            )
            ledger._connection = cast(Any, faulting)
            operations: dict[str, Callable[[], object]] = {
                "append": lambda: session.append("evt_new", {"value": 1}),
                "read": lambda: session.read("evt_target"),
                "shred": lambda: session.shred("evt_target"),
                "is_tombstoned": lambda: session.is_tombstoned("evt_target"),
                "event_count": session.event_count,
            }

            with pytest.raises(_PrimarySessionFailure) as caught:
                operations[operation_name]()

            assert isinstance(caught.value.__cause__, _CursorRollbackFailure)
            assert session._poisoned
            assert ledger._verification_certificate is None
            assert faulting.in_transaction
            with pytest.raises(LedgerLifecycleError):
                session.event_count()
        finally:
            session.close()

        assert faulting is not None
        assert not faulting.in_transaction
        with pytest.raises(LedgerLifecycleError):
            session.event_count()


def test_expected_conflict_still_poisons_when_rollback_cleanup_fails(
    tmp_path: Path,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        ledger.append("evt_existing", {"value": "original"})
        session = ledger.verified_session()
        faulting: _TransactionFailureConnection | None = None
        try:
            real_connection = ledger._connection_required()
            faulting = _TransactionFailureConnection(
                real_connection,
                fail_rollbacks=1,
            )
            ledger._connection = cast(Any, faulting)

            with pytest.raises(LedgerConflictError) as caught:
                session.append("evt_existing", {"value": "conflict"})

            assert isinstance(caught.value.__cause__, _CursorRollbackFailure)
            assert session._poisoned
            assert ledger._verification_certificate is None
            assert faulting.in_transaction
            with pytest.raises(LedgerLifecycleError):
                session.read("evt_existing")
        finally:
            session.close()

        assert faulting is not None
        assert not faulting.in_transaction
        with pytest.raises(LedgerLifecycleError):
            session.event_count()


def test_non_cursor_commit_failure_preserves_rollback_cleanup_failure(
    tmp_path: Path,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        session = ledger.verified_session()
        faulting: _TransactionFailureConnection | None = None
        try:
            real_connection = ledger._connection_required()
            faulting = _TransactionFailureConnection(
                real_connection,
                fail_commits=1,
                fail_rollbacks=1,
            )
            ledger._connection = cast(Any, faulting)

            with pytest.raises(_CursorCommitFailure) as caught:
                session.read("evt_missing")

            assert isinstance(caught.value.__cause__, _CursorRollbackFailure)
            assert session._poisoned
            assert ledger._verification_certificate is None
            assert faulting.in_transaction
            with pytest.raises(LedgerLifecycleError):
                session.event_count()
        finally:
            session.close()

        assert faulting is not None
        assert not faulting.in_transaction
        with pytest.raises(LedgerLifecycleError):
            session.read("evt_missing")


@pytest.mark.parametrize("cleanup_failure_mode", ["exception", "false"])
def test_append_preserves_primary_when_pending_key_cleanup_also_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cleanup_failure_mode: str,
) -> None:
    def fail_after_pending(boundary: str) -> None:
        if boundary == "after_pending_key_before_sqlite_insert":
            raise _PrimarySessionFailure("injected append primary failure")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
        _fault_injector=fail_after_pending,
    ) as ledger:
        store = ledger._record_store_required()

        def fail_pending_cleanup(_event_id: str) -> bool:
            if cleanup_failure_mode == "exception":
                raise _PendingCleanupFailure("injected pending-key cleanup failure")
            return False

        monkeypatch.setattr(store, "discard_pending", fail_pending_cleanup)
        session = ledger.verified_session()
        try:
            with pytest.raises(_PrimarySessionFailure) as caught:
                session.append("evt_pending", {"value": "must-not-commit"})

            expected_cleanup_type = (
                _PendingCleanupFailure
                if cleanup_failure_mode == "exception"
                else LedgerIntegrityError
            )
            assert isinstance(caught.value.__cause__, expected_cleanup_type)
            assert session._poisoned
            assert ledger._verification_certificate is None
            assert not ledger._connection_required().in_transaction
            assert store.reference("evt_pending") is not None
            with pytest.raises(LedgerLifecycleError):
                session.event_count()
        finally:
            session.close()

        with pytest.raises(LedgerLifecycleError):
            session.event_count()


def test_session_open_preserves_primary_when_verification_rollback_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        def fail_certificate_capture() -> object:
            raise _PrimarySessionFailure(
                "injected session-open verification failure"
            )

        monkeypatch.setattr(
            ledger,
            "_capture_verification_certificate_locked",
            fail_certificate_capture,
        )
        real_connection = ledger._connection_required()
        faulting = _TransactionFailureConnection(
            real_connection,
            fail_rollbacks=1,
        )
        ledger._connection = cast(Any, faulting)

        with pytest.raises(_PrimarySessionFailure) as caught:
            ledger.verified_session()

        assert isinstance(caught.value.__cause__, _CursorRollbackFailure)
        assert ledger._verification_certificate is None
        assert ledger._active_sessions == 0
        assert faulting.in_transaction
        faulting.execute("ROLLBACK")
        assert not faulting.in_transaction


def test_certificate_refresh_preserves_primary_when_rollback_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        def fail_certificate_capture() -> object:
            raise _PrimarySessionFailure("injected certificate refresh failure")

        monkeypatch.setattr(
            ledger,
            "_capture_verification_certificate_locked",
            fail_certificate_capture,
        )
        real_connection = ledger._connection_required()
        faulting = _TransactionFailureConnection(
            real_connection,
            fail_rollbacks=1,
        )
        ledger._connection = cast(Any, faulting)

        with pytest.raises(_PrimarySessionFailure) as caught:
            ledger._refresh_verification_certificate_locked()

        assert isinstance(caught.value.__cause__, _CursorRollbackFailure)
        assert ledger._verification_certificate is None
        assert faulting.in_transaction
        faulting.execute("ROLLBACK")
        assert not faulting.in_transaction


def test_public_integrity_verification_preserves_primary_when_rollback_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        primary = _PrimaryVerificationFailure(
            "injected public integrity verification failure"
        )

        def fail_full_verification() -> object:
            raise primary

        monkeypatch.setattr(ledger, "_verify_integrity_locked", fail_full_verification)
        real_connection = ledger._connection_required()
        faulting = _TransactionFailureConnection(
            real_connection,
            fail_rollbacks=1,
        )
        ledger._connection = cast(Any, faulting)

        with pytest.raises(_PrimaryVerificationFailure) as caught:
            ledger.verify_integrity()

        assert caught.value is primary
        assert isinstance(caught.value.__cause__, _CursorRollbackFailure)
        assert ledger._verification_certificate is None
        assert faulting.in_transaction
        assert (
            ledger_module._ledger_path_key(ledger._lock_path)
            not in ledger_module._active_ledger_paths()
        )

        faulting.execute("ROLLBACK")
        assert not faulting.in_transaction
        monkeypatch.setattr(
            ledger,
            "_verify_integrity_locked",
            ledger_module.EncryptedLedger._verify_integrity_locked.__get__(ledger),
        )
        assert ledger.event_count() == 0


def test_existing_unlock_preserves_primary_and_closes_after_rollback_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as original:
        assert original.event_count() == 0

    primary = _PrimaryVerificationFailure(
        "injected existing-ledger unlock verification failure"
    )
    faulting_connections: list[_TransactionFailureConnection] = []
    original_connect = ledger_module.EncryptedLedger._connect

    def connect_with_rollback_failure(
        ledger: EncryptedLedger,
        *,
        configure: bool,
        path: Path | None = None,
    ) -> sqlite3.Connection:
        connection = original_connect(ledger, configure=configure, path=path)
        faulting = _TransactionFailureConnection(
            connection,
            fail_rollbacks=1,
        )
        faulting_connections.append(faulting)
        return cast(sqlite3.Connection, faulting)

    def fail_full_verification(_ledger: EncryptedLedger) -> object:
        raise primary

    reopened = ledger_module.EncryptedLedger.__new__(ledger_module.EncryptedLedger)
    with monkeypatch.context() as local_patch:
        local_patch.setattr(
            ledger_module.EncryptedLedger,
            "_connect",
            connect_with_rollback_failure,
        )
        local_patch.setattr(
            ledger_module.EncryptedLedger,
            "_verify_integrity_locked",
            fail_full_verification,
        )

        ledger_module.EncryptedLedger.__init__(
            reopened,
            path,
            StaticKeyProvider(MASTER_KEY),
        )
        with pytest.raises(_PrimaryVerificationFailure) as caught:
            reopened.unlock()

    assert caught.value is primary
    assert isinstance(caught.value.__cause__, _CursorRollbackFailure)
    assert len(faulting_connections) == 1
    faulting = faulting_connections[0]
    assert faulting.close_calls == 1
    with pytest.raises(sqlite3.ProgrammingError):
        faulting.execute("SELECT 1")
    assert reopened._connection is None
    assert reopened._record_store is None
    assert reopened._verification_certificate is None
    assert not reopened._open
    assert (
        reopened._ledger_id,
        reopened._identity_root,
        reopened._chain_key,
        reopened._anchor_key,
        reopened._store_key,
        reopened._expected_key_check,
        reopened._keyring_plan,
    ) == (None, None, None, None, None, None, None)
    assert (
        ledger_module._ledger_path_key(reopened._lock_path)
        not in ledger_module._active_ledger_paths()
    )
    _assert_object_lock_available_from_other_thread(reopened._object_lock)

    reopened.unlock()
    try:
        assert reopened.event_count() == 0
        assert reopened._verification_certificate is not None
    finally:
        reopened.close()


def test_bootstrap_build_preserves_primary_closes_owned_connection_on_rollback_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "memory.sqlite3"
    ledger = EncryptedLedger(path, StaticKeyProvider(MASTER_KEY))

    ledger_id = "bootstrap-build-ledger"
    identity_root = b"i" * 32
    master_key = ledger._master_key()
    ledger._install_identity(master_key, ledger_id, identity_root)
    bootstrap = ledger_module._LedgerBootstrap(
        bootstrap_id="b" * 64,
        database_path=ledger._database_path_identity(),
        identity_root=identity_root,
        ledger_id=ledger_id,
        provider_scope=ledger._provider.security_scope,
        store_mode=ledger._bootstrap_store_mode(),
        store_profile=ledger._bootstrap_store_profile(),
        store_binding=ledger._bootstrap_store_binding(),
    )
    bootstrap_key_check = ledger._bootstrap_key_check(master_key, bootstrap)
    staging = ledger._bootstrap_staging_path(bootstrap)
    primary = _PrimaryBootstrapFailure("injected bootstrap build failure")
    faulting_connections: list[_PrimaryStatementFailureConnection] = []
    original_connect = ledger._connect

    def connect_with_statement_failure(
        *,
        configure: bool,
        path: Path | None = None,
    ) -> sqlite3.Connection:
        connection = original_connect(configure=configure, path=path)
        if path == staging:
            faulting = _PrimaryStatementFailureConnection(
                connection,
                primary=primary,
                fail_on_sql=lambda sql: sql.startswith("pragma user_version"),
            )
            faulting_connections.append(faulting)
            return cast(sqlite3.Connection, faulting)
        return connection

    monkeypatch.setattr(ledger, "_connect", connect_with_statement_failure)
    try:
        with pytest.raises(_PrimaryBootstrapFailure) as caught:
            ledger._build_bootstrap_database(bootstrap, bootstrap_key_check)

        assert caught.value is primary
        assert isinstance(caught.value.__cause__, _CursorRollbackFailure)
        assert len(faulting_connections) == 1
        faulting = faulting_connections[0]
        assert faulting.close_calls == 1
        with pytest.raises(sqlite3.ProgrammingError):
            faulting.execute("SELECT 1")
        assert ledger._connection is None
    finally:
        ledger._cleanup_bootstrap_scratch(bootstrap)
        ledger.close()


def test_bootstrap_resume_preserves_primary_and_leaves_connection_recoverable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "memory.sqlite3"

    def stop_after_key_check(boundary: str) -> None:
        if boundary == "after_ledger_bootstrap_key_check":
            raise _BootstrapSetupAbort("leave a deterministic complete bootstrap")

    setup_ledger = EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        _fault_injector=stop_after_key_check,
    )
    with pytest.raises(_BootstrapSetupAbort):
        setup_ledger.unlock()

    ledger = EncryptedLedger(path, StaticKeyProvider(MASTER_KEY))

    assert ledger._bootstrap_phase() == "complete"
    primary = _PrimaryBootstrapFailure("injected bootstrap resume failure")
    faulting_connections: list[_TransactionFailureConnection] = []
    original_connect = ledger._connect

    def connect_with_rollback_failure(
        *,
        configure: bool,
        path: Path | None = None,
    ) -> sqlite3.Connection:
        connection = original_connect(configure=configure, path=path)
        faulting = _TransactionFailureConnection(
            connection,
            fail_rollbacks=1,
        )
        faulting_connections.append(faulting)
        return cast(sqlite3.Connection, faulting)

    def fail_full_verification() -> object:
        raise primary

    monkeypatch.setattr(ledger, "_connect", connect_with_rollback_failure)
    monkeypatch.setattr(ledger, "_verify_integrity_locked", fail_full_verification)
    master_key = ledger._master_key()
    try:
        with pytest.raises(_PrimaryBootstrapFailure) as caught:
            ledger._resume_bootstrap(master_key, phase="complete")

        assert caught.value is primary
        assert isinstance(caught.value.__cause__, _CursorRollbackFailure)
        assert len(faulting_connections) == 1
        faulting = faulting_connections[0]
        assert ledger._connection is faulting
        assert faulting.in_transaction
        assert faulting.close_calls == 0
        assert ledger._bootstrap_complete_path.exists()

        faulting.execute("ROLLBACK")
        assert not faulting.in_transaction
        ledger._close_connection()
        assert faulting.close_calls == 1
        assert ledger._connection is None
    finally:
        if ledger._connection is not None:
            ledger._close_connection()
        ledger._record_store = None
        ledger._clear_secrets()


def test_bootstrap_finalize_preserves_primary_and_keeps_caller_connection_open(
    tmp_path: Path,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        primary = _PrimaryBootstrapFailure("injected bootstrap finalize failure")
        real_connection = ledger._connection_required()
        faulting = _PrimaryStatementFailureConnection(
            real_connection,
            primary=primary,
            fail_on_sql=lambda sql: sql.startswith("update metadata set value"),
        )

        with pytest.raises(_PrimaryBootstrapFailure) as caught:
            ledger._finalize_bootstrap_key_check(cast(Any, faulting), b"b" * 32)

        assert caught.value is primary
        assert isinstance(caught.value.__cause__, _CursorRollbackFailure)
        assert faulting.in_transaction
        assert faulting.close_calls == 0
        assert faulting.execute("SELECT 1").fetchone() == (1,)
        faulting.execute("ROLLBACK")
        assert not faulting.in_transaction
        assert ledger.event_count() == 0


def test_session_body_primary_survives_lock_release_failure_and_releases_all_locks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        primary = _PrimarySessionFailure("injected session body failure")
        cleanup = _LockContextExitFailure("injected session lock release failure")
        original_lock_factory = ledger_module.exclusive_file_lock
        wrapped = False

        def fail_first_lock_exit(path: Path) -> Any:
            nonlocal wrapped
            inner = original_lock_factory(path)
            if wrapped:
                return inner
            wrapped = True
            return _FailingExitLockContext(inner, cleanup)

        monkeypatch.setattr(
            ledger_module,
            "exclusive_file_lock",
            fail_first_lock_exit,
        )
        session = ledger.verified_session()

        with pytest.raises(_PrimarySessionFailure) as caught:
            with session:
                raise primary

        assert caught.value is primary
        assert caught.value.__cause__ is cleanup
        assert session._closed
        assert session._lock_context is None
        assert not session._path_marked
        assert ledger._active_sessions == 0
        assert ledger._verification_certificate is None
        assert (
            ledger_module._ledger_path_key(ledger._lock_path)
            not in ledger_module._active_ledger_paths()
        )
        _assert_object_lock_available_from_other_thread(ledger._object_lock)
        with pytest.raises(LedgerLifecycleError):
            session.event_count()
        assert ledger.event_count() == 0


def test_session_constructor_primary_survives_lock_exit_failure_without_markers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        primary = _PrimarySessionFailure("injected session constructor failure")
        cleanup = _LockContextExitFailure(
            "injected constructor lock-context exit failure"
        )
        original_lock_factory = ledger_module.exclusive_file_lock

        def failing_lock(path: Path) -> _FailingExitLockContext:
            return _FailingExitLockContext(original_lock_factory(path), cleanup)

        def fail_session_open() -> object:
            raise primary

        candidate = ledger_module.VerifiedLedgerSession.__new__(
            ledger_module.VerifiedLedgerSession
        )
        with monkeypatch.context() as local_patch:
            local_patch.setattr(ledger_module, "exclusive_file_lock", failing_lock)
            local_patch.setattr(
                ledger,
                "_open_verified_session_locked",
                fail_session_open,
            )

            with pytest.raises(_PrimarySessionFailure) as caught:
                ledger_module.VerifiedLedgerSession.__init__(candidate, ledger)

        assert caught.value is primary
        assert caught.value.__cause__ is cleanup
        assert candidate._closed
        assert candidate._lock_context is None
        assert not candidate._path_marked
        assert ledger._active_sessions == 0
        assert ledger._verification_certificate is None
        assert (
            ledger_module._ledger_path_key(ledger._lock_path)
            not in ledger_module._active_ledger_paths()
        )
        _assert_object_lock_available_from_other_thread(ledger._object_lock)
        assert ledger.event_count() == 0


def test_cursor_constructor_preserves_primary_and_poisoned_session_recovers_rollback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        session = ledger.verified_session()
        primary = _PrimaryCursorFailure("injected cursor constructor failure")
        real_connection = ledger._connection_required()
        faulting = _TransactionFailureConnection(
            real_connection,
            fail_rollbacks=1,
        )
        ledger._connection = cast(Any, faulting)

        def fail_certificate_check() -> object:
            raise primary

        monkeypatch.setattr(
            ledger,
            "_require_current_verification_certificate_locked",
            fail_certificate_check,
        )
        try:
            with pytest.raises(_PrimaryCursorFailure) as caught:
                session.cursor(batch_size=1)

            assert caught.value is primary
            assert isinstance(caught.value.__cause__, _CursorRollbackFailure)
            assert session._poisoned
            assert not session._cursors
            assert ledger._verification_certificate is None
            assert faulting.in_transaction
            with pytest.raises(LedgerLifecycleError):
                session.cursor()
        finally:
            session.close()

        assert not faulting.in_transaction
        assert session._closed
        assert ledger._active_sessions == 0


def test_cursor_body_primary_survives_release_failure_and_forces_unregister(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        session = ledger.verified_session()
        cursor = session.cursor(batch_size=1)
        primary = _PrimaryCursorFailure("injected cursor body failure")
        cleanup = _CursorReleaseFailure("injected cursor release failure")
        original_release = cursor._release_sql

        def release_then_fail() -> None:
            original_release()
            raise cleanup

        monkeypatch.setattr(cursor, "_release_sql", release_then_fail)
        try:
            with pytest.raises(_PrimaryCursorFailure) as caught:
                with cursor:
                    raise primary

            assert caught.value is primary
            assert caught.value.__cause__ is cleanup
            assert cursor._closed
            assert cursor not in session._cursors
            assert session._poisoned
            assert ledger._verification_certificate is None
            with pytest.raises(LedgerLifecycleError):
                next(cursor)
        finally:
            session.close()

        assert session._closed
        assert ledger._active_sessions == 0


def test_active_session_never_returns_plaintext_from_repointed_live_projection(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        ledger.append("evt_a", {"secret": "a"})
        ledger.append("evt_b", {"secret": "b-must-not-return"})

        with ledger.verified_session() as session:
            _repoint_live_projection_from_external_connection(path)

            with pytest.raises(LedgerIntegrityError):
                session.read("evt_a")


def test_get_ident_spoofing_cannot_bypass_session_or_cursor_ownership(
    tmp_path: Path,
) -> None:
    def call_from_non_owner_with_spoofed_ident(
        operation: Callable[[], object],
        owner_ident: int,
    ) -> BaseException:
        failures: list[BaseException] = []

        def run() -> None:
            original_get_ident = threading.get_ident
            threading.get_ident = lambda: owner_ident
            try:
                operation()
            except BaseException as exc:
                failures.append(exc)
            else:
                failures.append(
                    AssertionError("spoofed non-owner operation unexpectedly succeeded")
                )
            finally:
                threading.get_ident = original_get_ident

        worker = threading.Thread(target=run, daemon=True)
        worker.start()
        worker.join(timeout=3.0)
        if worker.is_alive() or len(failures) != 1:
            return TimeoutError("spoofed non-owner operation did not terminate cleanly")
        return failures[0]

    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        record = ledger.append("evt_1", {"index": 1}).record
        with ledger.verified_session() as session:
            cursor = session.cursor(batch_size=1)
            owner_ident = session._owner_thread.ident
            assert type(owner_ident) is int

            session_failure = call_from_non_owner_with_spoofed_ident(
                session.event_count,
                owner_ident,
            )
            cursor_failure = call_from_non_owner_with_spoofed_ident(
                lambda: next(cursor),
                owner_ident,
            )

            assert isinstance(session_failure, LedgerLifecycleError), session_failure
            assert isinstance(cursor_failure, LedgerLifecycleError), cursor_failure
            assert next(cursor) == record


def test_read_record_locked_rejects_repointed_live_projection_event_id_mismatch(
    tmp_path: Path,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        ledger.append("evt_a", {"secret": "a"})
        ledger.append("evt_b", {"secret": "b-must-not-return"})
        connection = ledger._connection_required()

        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM records WHERE event_id = 'evt_b'")
            connection.execute(
                """
                UPDATE records
                SET history_sequence = (
                        SELECT sequence FROM history
                        WHERE event_id = 'evt_b' AND operation = 'append'
                    ),
                    record_hash = (
                        SELECT record_hash FROM history
                        WHERE event_id = 'evt_b' AND operation = 'append'
                    )
                WHERE event_id = 'evt_a'
                """
            )

            with pytest.raises(LedgerIntegrityError):
                ledger._read_record_locked("evt_a")
        finally:
            if connection.in_transaction:
                connection.execute("ROLLBACK")


def test_full_verification_reads_one_verified_external_store_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        ledger.append("evt_1", {"index": 1})
        store = ledger._record_store_required()
        store_private = cast(Any, store)
        verified_snapshot = store.verified_snapshot
        verify_integrity_locked = store_private._verify_integrity_locked
        calls = {"snapshot": 0, "scan": 0}

        def counted_snapshot() -> object:
            calls["snapshot"] += 1
            return verified_snapshot()

        def counted_scan() -> object:
            calls["scan"] += 1
            return verify_integrity_locked()

        monkeypatch.setattr(store, "verified_snapshot", counted_snapshot)
        monkeypatch.setattr(store_private, "_verify_integrity_locked", counted_scan)

        ledger.verify_integrity()

        assert calls == {"snapshot": 1, "scan": 1}


@pytest.mark.parametrize("mutation", ["append", "shred"])
def test_active_cursor_rejects_same_session_mutation_without_damage(
    tmp_path: Path,
    mutation: str,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        live = ledger.append("evt_live", {"index": 1}).record
        target = ledger.append("evt_target", {"index": 2}).record

        with ledger.verified_session() as session:
            cursor = session.cursor(batch_size=1)
            assert next(cursor) == live
            if mutation == "append":

                def operation() -> object:
                    return session.append("evt_forbidden", {"index": 3})

            else:

                def operation() -> object:
                    return session.shred("evt_target")

            with pytest.raises(LedgerLifecycleError):
                operation()

            assert list(cursor) == [target]
            assert session.event_count() == 2
            assert session.read("evt_forbidden") is None
            assert session.is_tombstoned("evt_target") is False
            assert session.read("evt_target") == target


@pytest.mark.parametrize("nested_operation", ["verified_session", "append"])
def test_outer_session_rejects_nested_entry_and_preserves_checkpoint_head(
    tmp_path: Path,
    nested_operation: str,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        outcomes = [
            ledger.append(f"evt_{index}", {"index": index})
            for index in range(1, 4)
        ]

        with ledger.verified_session() as outer:
            if nested_operation == "verified_session":

                def operation() -> object:
                    nested = ledger.verified_session()
                    nested.close()
                    return nested

            else:

                def operation() -> object:
                    return ledger.append("evt_nested", {"index": 99})

            with pytest.raises(LedgerLifecycleError):
                operation()

            cursor = outer.cursor(batch_size=1)
            assert next(cursor) == outcomes[0].record
            checkpoint = cursor.suspend()
            assert outer.event_count() == 3
            assert outer.read("evt_nested") is None

        assert checkpoint.snapshot_head_sequence == outcomes[-1].record.sequence
        assert checkpoint.snapshot_head_hash == outcomes[-1].record.record_hash
        assert checkpoint.next_sequence == outcomes[1].record.sequence
        with ledger.verified_session() as fresh:
            assert list(fresh.resume_verified(checkpoint, batch_size=1)) == [
                outcome.record for outcome in outcomes[1:]
            ]


def test_same_thread_second_object_cannot_bypass_verified_session_path_lock(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    first = EncryptedLedger(path, StaticKeyProvider(MASTER_KEY))
    second = EncryptedLedger(path, StaticKeyProvider(MASTER_KEY))
    third = EncryptedLedger(path, StaticKeyProvider(MASTER_KEY))
    first.unlock()
    first_record = first.append("evt_1", {"index": 1}).record
    second.unlock()
    try:
        with first.verified_session() as outer:
            checkpoint = outer.cursor().suspend()

            with pytest.raises(LedgerLifecycleError):
                second.append("evt_forbidden", {"index": 2})
            with pytest.raises(LedgerLifecycleError):
                first.verify_integrity()
            with pytest.raises(LedgerLifecycleError):
                second.verify_integrity()
            with pytest.raises(LedgerLifecycleError):
                third.unlock()

            assert outer.event_count() == 1
            assert list(outer.resume_verified(checkpoint)) == [first_record]

        second_record = second.append("evt_2", {"index": 2}).record
        third.unlock()
        assert third.event_count() == 2
        assert first.read("evt_2") == second_record
    finally:
        third.close()
        second.close()
        first.close()


def test_cross_thread_second_object_waits_for_verified_session_path_lock(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    first = EncryptedLedger(path, StaticKeyProvider(MASTER_KEY))
    second = EncryptedLedger(path, StaticKeyProvider(MASTER_KEY))
    first.unlock()
    first.append("evt_1", {"index": 1})
    second.unlock()
    started = threading.Event()
    finished = threading.Event()
    outcomes: list[object] = []
    failures: list[BaseException] = []

    def append_from_second_thread() -> None:
        started.set()
        try:
            outcomes.append(second.append("evt_2", {"index": 2}))
        except BaseException as exc:
            failures.append(exc)
        finally:
            finished.set()

    worker = threading.Thread(target=append_from_second_thread, daemon=True)
    try:
        with first.verified_session() as outer:
            worker.start()
            assert started.wait(3.0)
            assert finished.wait(0.25) is False
            assert outer.event_count() == 1

        assert finished.wait(10.0)
        worker.join(timeout=0.25)
        assert worker.is_alive() is False
        assert failures == []
        assert len(outcomes) == 1
        assert first.event_count() == 2
    finally:
        second.close()
        first.close()


def test_verified_session_holds_cross_process_lock_for_lifetime(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    ready_path = tmp_path / "child.ready"
    process: subprocess.Popen[str] | None = None
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        ledger.append("evt_parent", {"source": "parent"})
        try:
            with ledger.verified_session() as session:
                process = subprocess.Popen(
                    [
                        sys.executable,
                        "-c",
                        _CROSS_PROCESS_LOCK_SCRIPT,
                        str(path),
                        str(ready_path),
                    ],
                    cwd=Path(__file__).resolve().parents[1],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                deadline = time.monotonic() + 10.0
                while not ready_path.exists() and time.monotonic() < deadline:
                    if process.poll() is not None:
                        break
                    time.sleep(0.02)
                assert ready_path.is_file()
                time.sleep(0.25)
                assert process.poll() is None
                assert session.event_count() == 1

            stdout, stderr = process.communicate(timeout=60)
            assert process.returncode == 0, stderr
            assert stdout.strip() == "DONE"
            assert ledger.event_count() == 2
            assert ledger.read("evt_child") is not None
        finally:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait(timeout=10)


def test_cursor_orders_live_records_and_honors_after_sequence(tmp_path: Path) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        outcomes = [
            ledger.append(f"evt_{index}", {"index": index})
            for index in range(1, 7)
        ]
        assert ledger.shred("evt_2") is True

        with ledger.verified_session() as session:
            records = list(session.cursor(after_sequence=2, batch_size=2))

        assert [record.sequence for record in records] == [3, 4, 5, 6]
        assert [record.event_id for record in records] == [
            "evt_3",
            "evt_4",
            "evt_5",
            "evt_6",
        ]
        assert records == [outcome.record for outcome in outcomes[2:]]


@pytest.mark.parametrize(
    ("after_sequence", "before_sequence"),
    [
        (-1, 1),
        (True, 1),
        (0, True),
        (0, 0),
        (1, 1),
        (2, 1),
        (0, 2),
    ],
)
def test_authenticated_witness_rejects_noncanonical_or_out_of_snapshot_bounds(
    tmp_path: Path,
    after_sequence: object,
    before_sequence: object,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        with ledger.verified_session() as session:
            with pytest.raises(InputBoundaryError):
                session.authenticated_tombstoned_append_witness(
                    witness_schema="aluclu.test-witness.v1",
                    link_digest="0" * 64,
                    after_sequence=after_sequence,  # type: ignore[arg-type]
                    before_sequence=before_sequence,  # type: ignore[arg-type]
                )


def test_authenticated_witness_is_atomic_private_and_visible_only_after_shred(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    schema = "aluclu.test-witness.v1"
    witnessed_link = "1" * 64
    raw_link = "2" * 64
    body: dict[str, JsonValue] = {"digest": "3" * 64, "schema": schema}
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        with ledger.verified_session() as session:
            witnessed = session._append_once_with_authenticated_witness(
                "evt_witnessed",
                {"value": "private"},
                witness_schema=schema,
                link_digest=witnessed_link,
                witness_body=body,
            )
            raw = session.append_once("evt_raw", {"value": "generic"})
            live_proof = session.authenticated_live_append_witness(
                event_id="evt_witnessed",
                append_sequence=witnessed.record.sequence,
                append_record_hash=witnessed.record.record_hash,
                witness_schema=schema,
                link_digest=witnessed_link,
            )
            assert live_proof == {
                "append_record_hash": witnessed.record.record_hash,
                "append_sequence": witnessed.record.sequence,
                "event_id": "evt_witnessed",
                "link_digest": witnessed_link,
                "witness_body": body,
                "witness_schema": schema,
            }
            assert (
                session.authenticated_live_append_witness(
                    event_id="evt_raw",
                    append_sequence=raw.record.sequence,
                    append_record_hash=raw.record.record_hash,
                    witness_schema=schema,
                    link_digest=raw_link,
                )
                is None
            )
            assert (
                session.authenticated_tombstoned_append_witness(
                    witness_schema=schema,
                    link_digest=witnessed_link,
                    after_sequence=0,
                    before_sequence=raw.record.sequence + 1,
                )
                is None
            )

        assert ledger.shred("evt_witnessed") is True
        assert ledger.shred("evt_raw") is True
        with ledger.verified_session() as session:
            cursor = session.cursor(batch_size=1)
            proof = session.authenticated_tombstoned_append_witness(
                witness_schema=schema,
                link_digest=witnessed_link,
                after_sequence=0,
                before_sequence=raw.record.sequence + 1,
            )
            assert proof == {
                "append_record_hash": witnessed.record.record_hash,
                "append_sequence": witnessed.record.sequence,
                "event_id": "evt_witnessed",
                "link_digest": witnessed_link,
                "witness_body": body,
                "witness_schema": schema,
            }
            assert (
                session.authenticated_tombstoned_append_witness(
                    witness_schema=schema,
                    link_digest=raw_link,
                    after_sequence=0,
                    before_sequence=5,
                )
                is None
            )
            cursor.close()

    connection = sqlite3.connect(path)
    try:
        stored_body = connection.execute(
            "SELECT witness_body FROM append_witnesses WHERE event_id = ?",
            ("evt_witnessed",),
        ).fetchone()
        assert stored_body is not None
        expected_body = json.dumps(
            body,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        assert stored_body[0] == expected_body
        assert b"private" not in stored_body[0]
    finally:
        connection.close()


def test_authenticated_witness_idempotency_requires_exact_witness(
    tmp_path: Path,
) -> None:
    schema = "aluclu.test-witness.v1"
    link = "4" * 64
    body = {"schema": schema, "value": 1}
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        with ledger.verified_session() as session:
            first = session._append_once_with_authenticated_witness(
                "evt_once",
                {"value": 1},
                witness_schema=schema,
                link_digest=link,
                witness_body=body,
            )
            duplicate = session._append_once_with_authenticated_witness(
                "evt_once",
                {"value": 1},
                witness_schema=schema,
                link_digest=link,
                witness_body=body,
            )
            assert first.created is True
            assert duplicate.created is False
            assert duplicate.record == first.record
            with pytest.raises(LedgerConflictError):
                session._append_once_with_authenticated_witness(
                    "evt_once",
                    {"value": 1},
                    witness_schema=schema,
                    link_digest="5" * 64,
                    witness_body=body,
                )
            with pytest.raises(LedgerConflictError):
                session._append_once_with_authenticated_witness(
                    "evt_once",
                    {"value": 1},
                    witness_schema=schema,
                    link_digest=link,
                    witness_body={"schema": schema, "value": 2},
                )


def test_append_witness_fault_rolls_back_record_key_and_sqlite_rows(
    tmp_path: Path,
) -> None:
    class InjectedWitnessFailure(RuntimeError):
        pass

    armed = True

    def inject(boundary: str) -> None:
        nonlocal armed
        if armed and boundary == "after_append_witness_before_sqlite_commit":
            armed = False
            raise InjectedWitnessFailure("injected witness transaction failure")

    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
        _fault_injector=inject,
    ) as ledger:
        failed_session = None
        with pytest.raises(InjectedWitnessFailure):
            with ledger.verified_session() as failed_session:
                failed_session._append_once_with_authenticated_witness(
                    "evt_rolled_back",
                    {"value": 1},
                    witness_schema="aluclu.test-witness.v1",
                    link_digest="6" * 64,
                    witness_body={"value": 1},
                )
        assert failed_session is not None
        with pytest.raises(LedgerLifecycleError):
            failed_session.event_count()
        connection = ledger._connection_required()
        assert connection.in_transaction is False
        assert connection.execute("SELECT COUNT(*) FROM history").fetchone() == (0,)
        assert connection.execute(
            "SELECT COUNT(*) FROM append_witnesses"
        ).fetchone() == (0,)
        assert ledger._record_store_required().reference("evt_rolled_back") is None
        assert ledger.event_count() == 0


@pytest.mark.parametrize(
    "boundary",
    [
        "after_sqlite_commit_before_key_committed",
        "after_key_committed_before_anchor",
        "after_append_anchor_before_certificate",
    ],
)
def test_committed_append_witness_recovers_forward_after_interruption(
    tmp_path: Path,
    boundary: str,
) -> None:
    class InjectedWitnessInterruption(RuntimeError):
        pass

    path = tmp_path / f"{boundary}.sqlite3"
    armed = True

    def inject(observed: str) -> None:
        nonlocal armed
        if armed and observed == boundary:
            armed = False
            raise InjectedWitnessInterruption(boundary)

    ledger = EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        _fault_injector=inject,
    )
    ledger.unlock()
    with pytest.raises(InjectedWitnessInterruption):
        with ledger.verified_session() as session:
            session._append_once_with_authenticated_witness(
                "evt_recover_witness",
                {"value": 1},
                witness_schema="aluclu.test-witness.v1",
                link_digest="8" * 64,
                witness_body={"value": 1},
            )
    ledger.close()

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as recovered:
        record = recovered.read("evt_recover_witness")
        assert record is not None
        with recovered.verified_session() as session:
            proof = session.authenticated_live_append_witness(
                event_id=record.event_id,
                append_sequence=record.sequence,
                append_record_hash=record.record_hash,
                witness_schema="aluclu.test-witness.v1",
                link_digest="8" * 64,
            )
            assert proof == {
                "append_record_hash": record.record_hash,
                "append_sequence": record.sequence,
                "event_id": record.event_id,
                "link_digest": "8" * 64,
                "witness_body": {"value": 1},
                "witness_schema": "aluclu.test-witness.v1",
            }


@pytest.mark.parametrize("tamper", ["body", "mac", "record_hash"])
def test_append_witness_external_tamper_fails_full_verification(
    tmp_path: Path,
    tamper: str,
) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        with ledger.verified_session() as session:
            session._append_once_with_authenticated_witness(
                "evt_tampered",
                {"value": 1},
                witness_schema="aluclu.test-witness.v1",
                link_digest="7" * 64,
                witness_body={"value": 1},
            )

    connection = sqlite3.connect(path)
    try:
        if tamper == "body":
            connection.execute(
                "UPDATE append_witnesses SET witness_body = ?",
                (sqlite3.Binary(b'{"value":2}'),),
            )
        elif tamper == "mac":
            connection.execute(
                "UPDATE append_witnesses SET witness_mac = ?",
                (sqlite3.Binary(b"x" * 32),),
            )
        else:
            connection.execute(
                "UPDATE append_witnesses SET append_record_hash = ?",
                (sqlite3.Binary(b"y" * 32),),
            )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(LedgerIntegrityError):
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)).unlock()


@pytest.mark.parametrize("batch_size", [0, -1, 4097, True, 1.0, "1", None])
def test_cursor_rejects_noncanonical_batch_size(
    tmp_path: Path,
    batch_size: object,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        with ledger.verified_session() as session:
            with pytest.raises(InputBoundaryError):
                session.cursor(batch_size=batch_size)  # type: ignore[arg-type]


@pytest.mark.parametrize("after_sequence", [-1, True, 1.0, "0", None])
def test_cursor_rejects_noncanonical_after_sequence(
    tmp_path: Path,
    after_sequence: object,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        with ledger.verified_session() as session:
            with pytest.raises(InputBoundaryError):
                session.cursor(
                    after_sequence=after_sequence,  # type: ignore[arg-type]
                    batch_size=1,
                )


def test_cursor_accepts_batch_boundaries_and_empty_tail(tmp_path: Path) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        ledger.append("evt_1", {"index": 1})
        with ledger.verified_session() as session:
            assert list(session.cursor(batch_size=1))
            assert list(session.cursor(batch_size=4096))
            assert list(session.cursor(after_sequence=10, batch_size=1)) == []


@pytest.mark.parametrize(
    ("case", "expected_error"),
    [
        ("batch_zero", InputBoundaryError),
        ("batch_too_large", InputBoundaryError),
        ("batch_bool", InputBoundaryError),
        ("next_zero", InputBoundaryError),
        ("next_past_snapshot", InputBoundaryError),
        ("head_negative", InputBoundaryError),
        ("hash_short", InputBoundaryError),
        ("head_mismatch", LedgerSnapshotChanged),
        ("hash_mismatch", LedgerSnapshotChanged),
    ],
)
def test_direct_cursor_constructor_rejects_boundaries_before_sql_or_registration(
    tmp_path: Path,
    case: str,
    expected_error: type[BaseException],
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        record = ledger.append("evt_1", {"index": 1}).record
        with ledger.verified_session() as session:
            trace = _SqliteTrace()
            ledger._connection = cast(
                sqlite3.Connection,
                _ObservedConnection(ledger._connection_required(), trace),
            )
            arguments: dict[str, object] = {
                "next_sequence": 1,
                "batch_size": 1,
                "snapshot_head_sequence": record.sequence,
                "snapshot_head_hash": bytes.fromhex(record.record_hash),
            }
            if case == "batch_zero":
                arguments["batch_size"] = 0
            elif case == "batch_too_large":
                arguments["batch_size"] = 4097
            elif case == "batch_bool":
                arguments["batch_size"] = True
            elif case == "next_zero":
                arguments["next_sequence"] = 0
            elif case == "next_past_snapshot":
                arguments["next_sequence"] = record.sequence + 2
            elif case == "head_negative":
                arguments["snapshot_head_sequence"] = -1
            elif case == "hash_short":
                arguments["snapshot_head_hash"] = b"x" * 31
            elif case == "head_mismatch":
                arguments["snapshot_head_sequence"] = record.sequence + 1
            elif case == "hash_mismatch":
                actual_hash = bytes.fromhex(record.record_hash)
                arguments["snapshot_head_hash"] = bytes(
                    [actual_hash[0] ^ 1]
                ) + actual_hash[1:]
            else:  # pragma: no cover - parametrization guard
                raise AssertionError(f"unknown constructor case: {case}")

            registered_before = len(session._cursors)
            executed_before = len(trace.execute_sql)
            with pytest.raises(expected_error):
                VerifiedLedgerCursor(
                    session,
                    next_sequence=arguments["next_sequence"],  # type: ignore[arg-type]
                    batch_size=arguments["batch_size"],  # type: ignore[arg-type]
                    snapshot_head_sequence=arguments[  # type: ignore[arg-type]
                        "snapshot_head_sequence"
                    ],
                    snapshot_head_hash=arguments[  # type: ignore[arg-type]
                        "snapshot_head_hash"
                    ],
                )

            assert len(session._cursors) == registered_before
            assert len(trace.execute_sql) == executed_before
            assert session.event_count() == 1
            assert list(session.cursor(batch_size=1)) == [record]


def test_direct_cursor_constructor_rejects_closed_session_before_sql(
    tmp_path: Path,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        record = ledger.append("evt_1", {"index": 1}).record
        session = ledger.verified_session()
        session.close()
        trace = _SqliteTrace()
        ledger._connection = cast(
            sqlite3.Connection,
            _ObservedConnection(ledger._connection_required(), trace),
        )

        with pytest.raises(LedgerLifecycleError):
            VerifiedLedgerCursor(
                session,
                next_sequence=1,
                batch_size=1,
                snapshot_head_sequence=record.sequence,
                snapshot_head_hash=bytes.fromhex(record.record_hash),
            )

        assert trace.execute_sql == []
        assert session._cursors == set()
        assert ledger.event_count() == 1


def test_direct_cursor_constructor_rejects_non_owner_before_sql_or_registration(
    tmp_path: Path,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        record = ledger.append("evt_1", {"index": 1}).record
        with ledger.verified_session() as session:
            trace = _SqliteTrace()
            ledger._connection = cast(
                sqlite3.Connection,
                _ObservedConnection(ledger._connection_required(), trace),
            )

            def construct_cursor() -> object:
                cursor = VerifiedLedgerCursor(
                    session,
                    next_sequence=1,
                    batch_size=1,
                    snapshot_head_sequence=record.sequence,
                    snapshot_head_hash=bytes.fromhex(record.record_hash),
                )
                cursor.close()
                return cursor

            failure = _call_from_non_owner_thread(construct_cursor)

            assert isinstance(failure, LedgerLifecycleError), failure
            assert trace.execute_sql == []
            assert session._cursors == set()
            assert session.event_count() == 1
            assert list(session.cursor(batch_size=1)) == [record]


def test_cursor_checkpoint_resumes_exact_unmodified_snapshot(tmp_path: Path) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        outcomes = [
            ledger.append(f"evt_{index}", {"index": index})
            for index in range(1, 6)
        ]
        with ledger.verified_session() as session:
            cursor = session.cursor(batch_size=2)
            assert next(cursor) == outcomes[0].record
            assert next(cursor) == outcomes[1].record
            checkpoint = cursor.suspend()

        assert checkpoint.ledger_id == ledger.ledger_id
        assert checkpoint.snapshot_head_sequence == outcomes[-1].record.sequence
        assert checkpoint.snapshot_head_hash == outcomes[-1].record.record_hash
        assert checkpoint.next_sequence == outcomes[2].record.sequence

        with ledger.verified_session() as session:
            resumed = list(session.resume_verified(checkpoint, batch_size=1))

        assert resumed == [outcome.record for outcome in outcomes[2:]]


def test_exhausted_cursor_checkpoint_advances_across_shredded_tail_gaps(
    tmp_path: Path,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        live = ledger.append("evt_live", {"index": 1}).record
        ledger.append("evt_tail_a", {"index": 2})
        ledger.append("evt_tail_b", {"index": 3})
        assert ledger.shred("evt_tail_a") is True
        assert ledger.shred("evt_tail_b") is True

        with ledger.verified_session() as session:
            cursor = session.cursor(batch_size=1)
            assert list(cursor) == [live]
            checkpoint = cursor.suspend()

        assert checkpoint.snapshot_head_sequence == 5
        assert checkpoint.next_sequence == checkpoint.snapshot_head_sequence + 1
        with ledger.verified_session() as session:
            assert list(session.resume_verified(checkpoint, batch_size=1)) == []


def test_cursor_checkpoint_rejects_wrong_ledger_and_changed_head(
    tmp_path: Path,
) -> None:
    first_path = tmp_path / "first.sqlite3"
    second_path = tmp_path / "second.sqlite3"
    with EncryptedLedger(first_path, StaticKeyProvider(MASTER_KEY)) as first:
        first.append("evt_1", {"index": 1})
        with first.verified_session() as session:
            checkpoint = session.cursor().suspend()

        with EncryptedLedger(second_path, StaticKeyProvider(MASTER_KEY)) as second:
            second.append("evt_1", {"index": 1})
            with second.verified_session() as session:
                with pytest.raises(LedgerSnapshotChanged):
                    session.resume_verified(checkpoint)

        first.append("evt_2", {"index": 2})
        with first.verified_session() as session:
            with pytest.raises(LedgerSnapshotChanged):
                session.resume_verified(checkpoint)


def test_full_verification_and_cursor_use_bounded_fetchmany(tmp_path: Path) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        for index in range(9):
            ledger.append(f"evt_{index}", {"index": index})

        trace = _SqliteTrace()
        ledger._connection = cast(
            sqlite3.Connection,
            _ObservedConnection(ledger._connection_required(), trace),
        )
        ledger.verify_integrity()
        with ledger.verified_session() as session:
            records = list(session.cursor(batch_size=3))

        assert [record.event_id for record in records] == [
            f"evt_{index}" for index in range(9)
        ]
        history_batches = [
            size
            for sql, size in trace.fetchmany_calls
            if "from history" in sql and "order by sequence" in sql
        ]
        cursor_batches = [
            size
            for sql, size in trace.fetchmany_calls
            if "from records as r join history" in sql and "order by" in sql
        ]
        assert history_batches
        assert cursor_batches
        assert all(1 <= size <= 4096 for size in history_batches)
        assert all(size == 3 for size in cursor_batches)
        assert trace.fetchall_sql == []


def test_cursor_and_resume_default_to_64_row_batches(tmp_path: Path) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        for index in range(130):
            ledger.append(f"evt_{index}", {"index": index})

        with ledger.verified_session() as session:
            checkpoint = session.cursor(batch_size=1).suspend()

        trace = _SqliteTrace()
        ledger._connection = cast(
            sqlite3.Connection,
            _ObservedConnection(ledger._connection_required(), trace),
        )
        with ledger.verified_session() as session:
            assert len(list(session.cursor())) == 130
            assert len(list(session.resume_verified(checkpoint))) == 130

        cursor_batches = [
            size
            for sql, size in trace.fetchmany_calls
            if "from records as r join history" in sql and "order by" in sql
        ]
        assert cursor_batches
        assert all(size == 64 for size in cursor_batches)


def test_full_scan_state_does_not_retain_history_rows_or_ciphertexts(
    tmp_path: Path,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        first = ledger.append(
            "evt_live",
            {"marker": "live-ciphertext-marker-" + ("a" * 1024)},
        ).record
        ledger.append(
            "evt_shredded",
            {"marker": "shredded-ciphertext-marker-" + ("b" * 1024)},
        )
        assert ledger.shred("evt_shredded") is True

        with ledger.verified_session():
            connection = ledger._connection_required()
            ciphertexts = [
                row[0]
                for row in connection.execute(
                    "SELECT ciphertext FROM history WHERE operation = 'append' "
                    "ORDER BY sequence"
                )
            ]
            state = ledger._scan_history_locked()

        assert state.head_sequence == 3
        assert state.records["evt_live"][0] == first.sequence
        assert len(ciphertexts) == 2
        assert all(type(ciphertext) is bytes for ciphertext in ciphertexts)

        reachable = _reachable_object_graph(state)
        assert not any(
            type(value) is bytes and value in ciphertexts for value in reachable
        )
        assert not any(
            type(value) is tuple
            and len(value) == 9
            and type(value[0]) is int
            and type(value[1]) is str
            and type(value[2]) is str
            and type(value[5]) is bytes
            and type(value[8]) is bytes
            for value in reachable
        )


def test_cursor_is_lazy_and_never_loads_shredded_payload_or_lifetime_keys(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        for index in range(1, 7):
            ledger.append(f"evt_{index}", {"index": index})
        ledger.shred("evt_2")

        store = ledger._record_store_required()
        original_get = store.get
        key_reads: list[str] = []

        def tracked_get(event_id: str) -> bytes | None:
            key_reads.append(event_id)
            return original_get(event_id)

        def lifetime_scan_forbidden() -> Any:
            raise AssertionError("cursor path reread the lifetime key projection")

        monkeypatch.setattr(store, "get", tracked_get)
        monkeypatch.setattr(store, "iter_references", lifetime_scan_forbidden)
        monkeypatch.setattr(store, "iter_tombstones", lifetime_scan_forbidden)

        with ledger.verified_session() as session:
            cursor = session.cursor(batch_size=2)
            assert key_reads == []
            first = next(cursor)
            assert first.event_id == "evt_1"
            assert 1 <= len(key_reads) <= 2
            records = [first, *cursor]

        assert [record.event_id for record in records] == [
            "evt_1",
            "evt_3",
            "evt_4",
            "evt_5",
            "evt_6",
        ]
        assert key_reads == [record.event_id for record in records]
        assert "evt_2" not in key_reads
