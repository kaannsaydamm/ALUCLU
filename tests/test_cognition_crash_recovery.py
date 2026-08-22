from __future__ import annotations

import base64
import shutil
import sqlite3
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from aluclu.cognition import (
    EncryptedLedger,
    FileRecordKeyStore,
    LedgerIntegrityError,
    LedgerKeyError,
    LedgerRollbackError,
    RecordKeyState,
    StaticKeyProvider,
)

MASTER_KEY = b"m" * 32
CRASH_EXIT_CODE = 73

_CRASH_SCRIPT = textwrap.dedent(
    """
    import os
    import sys
    from pathlib import Path

    from aluclu.cognition import EncryptedLedger, StaticKeyProvider

    path = Path(sys.argv[1])
    boundary = sys.argv[2]
    operation = sys.argv[3]

    def terminate_at(candidate: str) -> None:
        if candidate == boundary:
            os._exit(73)

    with EncryptedLedger(
        path,
        StaticKeyProvider(b"m" * 32),
        _fault_injector=terminate_at,
    ) as ledger:
        if operation == "append":
            ledger.append("evt_crash", {"value": "committed-exactly-once"})
        elif operation == "shred":
            ledger.shred("evt_target")
        else:
            raise AssertionError(f"unknown operation: {operation}")

    raise SystemExit(74)
    """
)


@pytest.mark.parametrize(
    ("boundary", "operation", "expected_count"),
    [
        ("after_pending_key_before_sqlite_insert", "append", 1),
        ("after_sqlite_commit_before_key_committed", "append", 2),
        ("after_key_committed_before_anchor", "append", 2),
        ("after_store_tombstone_before_sqlite_shred", "shred", 3),
        ("after_sqlite_shred_before_anchor", "shred", 3),
    ],
)
def test_real_process_crash_boundaries_recover_exactly_once(
    tmp_path: Path,
    boundary: str,
    operation: str,
    expected_count: int,
) -> None:
    path = tmp_path / "memory.sqlite3"
    target_hash: str | None = None
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        ledger.append("evt_keep", {"value": "survives"})
        if operation == "shred":
            target_hash = ledger.append(
                "evt_target",
                {"secret": "must-never-resurrect"},
            ).record.record_hash

    completed = subprocess.run(
        [sys.executable, "-c", _CRASH_SCRIPT, str(path), boundary, operation],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert completed.returncode == CRASH_EXIT_CODE, completed.stderr

    anchor_path = path.with_suffix(path.suffix + ".anchor.json")
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        assert ledger.event_count() == expected_count
        assert ledger.read("evt_keep") is not None
        store = ledger._record_store_required()
        if boundary == "after_pending_key_before_sqlite_insert":
            assert ledger.read("evt_crash") is None
            assert store.reference("evt_crash") is None
        elif operation == "append":
            recovered = ledger.read("evt_crash")
            assert recovered is not None
            assert recovered.payload == {"value": "committed-exactly-once"}
            reference = store.reference("evt_crash")
            assert reference is not None
            assert reference.state is RecordKeyState.COMMITTED
            assert reference.record_hash == recovered.record_hash
        else:
            assert ledger.read("evt_target") is None
            assert ledger.is_tombstoned("evt_target") is True
            assert target_hash is not None
            assert store.tombstone_hash("evt_target") == target_hash
        ledger.verify_integrity()
        recovered_revision = store.revision

    recovered_anchor = anchor_path.read_bytes()
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        ledger.verify_integrity()
        assert ledger.event_count() == expected_count
        assert ledger._record_store_required().revision == recovered_revision
    assert anchor_path.read_bytes() == recovered_anchor

    connection = sqlite3.connect(path)
    try:
        history = connection.execute(
            "SELECT operation, event_id FROM history ORDER BY sequence"
        ).fetchall()
    finally:
        connection.close()
    if boundary == "after_pending_key_before_sqlite_insert":
        assert history == [("append", "evt_keep")]
    elif operation == "append":
        assert history == [("append", "evt_keep"), ("append", "evt_crash")]
    else:
        assert history == [
            ("append", "evt_keep"),
            ("append", "evt_target"),
            ("shred", "evt_target"),
        ]


def test_same_process_repairs_sqlite_commit_before_receipt_without_duplicate(
    tmp_path: Path,
) -> None:
    fired = False

    def interrupt_once(boundary: str) -> None:
        nonlocal fired
        if boundary == "after_sqlite_commit_before_key_committed" and not fired:
            fired = True
            raise RuntimeError("injected boundary 6 interruption")

    ledger = EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
        _fault_injector=interrupt_once,
    )
    ledger.unlock()
    try:
        with pytest.raises(RuntimeError, match="boundary 6"):
            ledger.append_once("evt_1", {"value": 1})

        recovered = ledger.append_once("evt_1", {"value": 1})

        assert recovered.created is False
        assert ledger.event_count() == 1
        reference = ledger._record_store_required().reference("evt_1")
        assert reference is not None
        assert reference.state is RecordKeyState.COMMITTED
        assert reference.record_hash == recovered.record.record_hash
    finally:
        ledger.close()


def test_pending_receipt_repairs_only_after_exact_aead_verification(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    store = FileRecordKeyStore(
        tmp_path / "keys.json",
        b"s" * 32,
        ledger_id="ledger-1",
    )

    def interrupt(boundary: str) -> None:
        if boundary == "after_sqlite_commit_before_key_committed":
            raise RuntimeError("injected boundary 6 interruption")

    ledger = EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        record_key_store=store,
        _fault_injector=interrupt,
    )
    ledger.unlock()
    try:
        with pytest.raises(RuntimeError, match="boundary 6"):
            ledger.append("evt_1", {"value": 1})
    finally:
        ledger.close()

    state = store._load()
    entries = state["entries"]
    assert isinstance(entries, dict)
    entry = entries["evt_1"]
    assert isinstance(entry, dict)
    entry["key"] = base64.b64encode(b"x" * 32).decode("ascii")
    store._save(state)

    with pytest.raises(LedgerIntegrityError):
        EncryptedLedger(
            path,
            StaticKeyProvider(MASTER_KEY),
            record_key_store=store,
        ).unlock()

    reference = store.reference("evt_1")
    assert reference is not None
    assert reference.state is RecordKeyState.PENDING


def test_same_process_forward_recovers_external_first_shred(tmp_path: Path) -> None:
    fired = False

    def interrupt_once(boundary: str) -> None:
        nonlocal fired
        if boundary == "after_store_tombstone_before_sqlite_shred" and not fired:
            fired = True
            raise RuntimeError("injected boundary 8 interruption")

    ledger = EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
        _fault_injector=interrupt_once,
    )
    ledger.unlock()
    try:
        ledger.append("evt_1", {"secret": "never-resurrect"})
        with pytest.raises(RuntimeError, match="boundary 8"):
            ledger.shred("evt_1")

        assert ledger.read("evt_1") is None
        assert ledger.is_tombstoned("evt_1") is True
        assert ledger.shred("evt_1") is False
        assert ledger.event_count() == 2
    finally:
        ledger.close()


def test_committed_receipt_rollback_is_not_deleted_as_pending(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    snapshot = tmp_path / "before-second.sqlite3"
    anchor_path = path.with_suffix(path.suffix + ".anchor.json")

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        ledger.append("evt_1", {"value": 1})
    _backup_database(path, snapshot)
    old_anchor = anchor_path.read_bytes()

    ledger = EncryptedLedger(path, StaticKeyProvider(MASTER_KEY))
    ledger.unlock()
    ledger.append("evt_2", {"value": 2})
    store = ledger._record_store_required()
    ledger.close()

    _restore_database(snapshot, path)
    anchor_path.write_bytes(old_anchor)

    with pytest.raises(LedgerRollbackError):
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)).unlock()

    reference = store.reference("evt_2")
    assert reference is not None
    assert reference.state is RecordKeyState.COMMITTED


def test_anchor_ahead_of_otherwise_matching_database_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    store = FileRecordKeyStore(
        tmp_path / "keys.json",
        b"s" * 32,
        ledger_id="ledger-1",
    )
    with EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        record_key_store=store,
    ) as ledger:
        first = ledger.append("evt_1", {"value": 1})
        ledger.append("evt_2", {"value": 2})

    state = store._load()
    entries = state["entries"]
    assert isinstance(entries, dict)
    del entries["evt_2"]
    store._save(state)

    connection = sqlite3.connect(path)
    try:
        connection.execute("DELETE FROM records WHERE event_id = 'evt_2'")
        connection.execute("DELETE FROM history WHERE event_id = 'evt_2'")
        connection.execute(
            "UPDATE metadata SET value = ? WHERE key = 'head_sequence'",
            (sqlite3.Binary(b"1"),),
        )
        connection.execute(
            "UPDATE metadata SET value = ? WHERE key = 'head_hash'",
            (sqlite3.Binary(bytes.fromhex(first.record.record_hash)),),
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(LedgerRollbackError):
        EncryptedLedger(
            path,
            StaticKeyProvider(MASTER_KEY),
            record_key_store=store,
        ).unlock()


def test_live_record_without_key_or_tombstone_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    store = FileRecordKeyStore(
        tmp_path / "keys.json",
        b"s" * 32,
        ledger_id="ledger-1",
    )
    with EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        record_key_store=store,
    ) as ledger:
        ledger.append("evt_1", {"value": 1})

    state = store._load()
    entries = state["entries"]
    assert isinstance(entries, dict)
    del entries["evt_1"]
    store._save(state)

    with pytest.raises(LedgerKeyError):
        EncryptedLedger(
            path,
            StaticKeyProvider(MASTER_KEY),
            record_key_store=store,
        ).unlock()


def test_mismatched_committed_receipt_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    store = FileRecordKeyStore(
        tmp_path / "keys.json",
        b"s" * 32,
        ledger_id="ledger-1",
    )
    with EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        record_key_store=store,
    ) as ledger:
        outcome = ledger.append("evt_1", {"value": 1})

    wrong_hash = "ab" * 32
    assert wrong_hash != outcome.record.record_hash
    state = store._load()
    entries = state["entries"]
    assert isinstance(entries, dict)
    entry = entries["evt_1"]
    assert isinstance(entry, dict)
    entry["record_hash"] = wrong_hash
    store._save(state)

    with pytest.raises(LedgerIntegrityError):
        EncryptedLedger(
            path,
            StaticKeyProvider(MASTER_KEY),
            record_key_store=store,
        ).unlock()


def test_wrong_or_extra_external_tombstone_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    store = FileRecordKeyStore(
        tmp_path / "keys.json",
        b"s" * 32,
        ledger_id="ledger-1",
    )
    with EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        record_key_store=store,
    ) as ledger:
        outcome = ledger.append("evt_1", {"value": 1})

    assert store.shred("evt_1", outcome.record.record_hash)
    state = store._load()
    tombstones = state["tombstones"]
    assert isinstance(tombstones, dict)
    tombstones["evt_1"] = {"record_hash": "ab" * 32}
    store._save(state)

    with pytest.raises(LedgerIntegrityError):
        EncryptedLedger(
            path,
            StaticKeyProvider(MASTER_KEY),
            record_key_store=store,
        ).unlock()

    extra_path = tmp_path / "extra.sqlite3"
    extra_store = FileRecordKeyStore(
        tmp_path / "extra-keys.json",
        b"t" * 32,
        ledger_id="ledger-2",
    )
    with EncryptedLedger(
        extra_path,
        StaticKeyProvider(MASTER_KEY),
        record_key_store=extra_store,
    ):
        pass
    extra_store.put_pending("evt_extra", b"e" * 32)
    extra_store.mark_committed("evt_extra", "cd" * 32)
    extra_store.shred("evt_extra", "cd" * 32)

    with pytest.raises(LedgerIntegrityError):
        EncryptedLedger(
            extra_path,
            StaticKeyProvider(MASTER_KEY),
            record_key_store=extra_store,
        ).unlock()


def _backup_database(source: Path, destination: Path) -> None:
    source_connection = sqlite3.connect(source)
    destination_connection = sqlite3.connect(destination)
    try:
        source_connection.backup(destination_connection)
    finally:
        destination_connection.close()
        source_connection.close()


def _restore_database(source: Path, destination: Path) -> None:
    for suffix in ("-wal", "-shm"):
        Path(f"{destination}{suffix}").unlink(missing_ok=True)
    shutil.copyfile(source, destination)
