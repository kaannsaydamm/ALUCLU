from __future__ import annotations

import base64
import json
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

_BOOTSTRAP_CRASH_SCRIPT = textwrap.dedent(
    """
    import os
    import sys
    from pathlib import Path

    from aluclu.cognition import EncryptedLedger, StaticKeyProvider

    path = Path(sys.argv[1])
    boundary = sys.argv[2]

    def terminate_at(candidate: str) -> None:
        if candidate == boundary:
            os._exit(73)

    ledger = EncryptedLedger(
        path,
        StaticKeyProvider(b"m" * 32),
        _fault_injector=terminate_at,
    )
    ledger.unlock()
    raise SystemExit(74)
    """
)

_EXPLICIT_BOOTSTRAP_CRASH_SCRIPT = textwrap.dedent(
    """
    import os
    import sys
    from pathlib import Path

    from aluclu.cognition import (
        EncryptedLedger,
        FileRecordKeyStore,
        StaticKeyProvider,
    )

    path = Path(sys.argv[1])
    store_path = Path(sys.argv[2])

    def terminate_at(candidate: str) -> None:
        if candidate == "after_ledger_bootstrap_marker":
            os._exit(73)

    store = FileRecordKeyStore(
        store_path,
        b"s" * 32,
        ledger_id="explicit-ledger",
    )
    EncryptedLedger(
        path,
        StaticKeyProvider(b"m" * 32),
        record_key_store=store,
        _fault_injector=terminate_at,
    ).unlock()
    raise SystemExit(74)
    """
)


@pytest.mark.parametrize(
    "boundary",
    [
        "after_ledger_bootstrap_marker",
        "after_ledger_bootstrap_staging_commit",
        "after_ledger_bootstrap_staging_database",
        "after_ledger_bootstrap_database",
        "after_directory_initialize_identity",
        "after_directory_initialize_head",
        "after_directory_initialize_publish",
        "after_ledger_bootstrap_store",
        "after_ledger_bootstrap_anchor",
        "after_ledger_bootstrap_complete_marker",
        "after_ledger_bootstrap_key_check",
        "after_ledger_bootstrap_verified",
    ],
)
def test_real_process_bootstrap_crash_recovers_without_weakening_anchor(
    tmp_path: Path,
    boundary: str,
) -> None:
    path = tmp_path / "memory.sqlite3"

    completed = subprocess.run(
        [sys.executable, "-c", _BOOTSTRAP_CRASH_SCRIPT, str(path), boundary],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert completed.returncode == CRASH_EXIT_CODE, completed.stderr

    if boundary == "after_ledger_bootstrap_marker":
        assert not path.exists()
    if boundary == "after_ledger_bootstrap_staging_commit":
        assert list(tmp_path.glob(".*.aluclu-bootstrap.sqlite3-wal"))
    if boundary == "after_ledger_bootstrap_staging_database":
        assert list(tmp_path.glob(".*.aluclu-bootstrap.sqlite3"))
        assert not list(tmp_path.glob(".*.aluclu-bootstrap.sqlite3-wal"))
    if boundary in {
        "after_ledger_bootstrap_database",
        "after_directory_initialize_identity",
        "after_directory_initialize_head",
        "after_directory_initialize_publish",
        "after_ledger_bootstrap_store",
        "after_ledger_bootstrap_anchor",
        "after_ledger_bootstrap_complete_marker",
        "after_ledger_bootstrap_key_check",
        "after_ledger_bootstrap_verified",
    }:
        assert path.exists()
    if boundary in {
        "after_ledger_bootstrap_complete_marker",
        "after_ledger_bootstrap_key_check",
        "after_ledger_bootstrap_verified",
    }:
        assert path.with_suffix(path.suffix + ".bootstrap.complete.json").is_file()

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        assert ledger.event_count() == 0
        ledger.append("evt_after_bootstrap", {"value": boundary})
        ledger.verify_integrity()

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as reopened:
        record = reopened.read("evt_after_bootstrap")
        assert record is not None
        assert record.payload == {"value": boundary}
        assert reopened.event_count() == 1

    assert not path.with_suffix(path.suffix + ".bootstrap.pending.json").exists()
    assert not path.with_suffix(path.suffix + ".bootstrap.complete.json").exists()
    assert not list(tmp_path.glob(".*.aluclu-bootstrap.sqlite3*"))


def test_bootstrap_marker_wrong_key_fails_before_state_mutation(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    pending = path.with_suffix(path.suffix + ".bootstrap.pending.json")
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            _BOOTSTRAP_CRASH_SCRIPT,
            str(path),
            "after_ledger_bootstrap_marker",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert completed.returncode == CRASH_EXIT_CODE, completed.stderr
    marker_before = pending.read_bytes()

    with pytest.raises(LedgerKeyError):
        EncryptedLedger(path, StaticKeyProvider(b"w" * 32)).unlock()

    assert pending.read_bytes() == marker_before
    assert not path.exists()
    assert not path.with_suffix(path.suffix + ".anchor.json").exists()
    assert not path.with_suffix(path.suffix + ".record-keys").exists()

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as recovered:
        recovered.verify_integrity()


def test_pending_bootstrap_marker_replay_cannot_claim_completed_ledger(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    pending = path.with_suffix(path.suffix + ".bootstrap.pending.json")
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            _BOOTSTRAP_CRASH_SCRIPT,
            str(path),
            "after_ledger_bootstrap_marker",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert completed.returncode == CRASH_EXIT_CODE, completed.stderr
    replay = pending.read_bytes()
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)):
        pass
    pending.write_bytes(replay)

    with pytest.raises(LedgerIntegrityError, match="replayed"):
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)).unlock()

    assert pending.read_bytes() == replay
    pending.unlink()
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as reopened:
        reopened.verify_integrity()


def test_complete_bootstrap_marker_never_recreates_missing_anchor(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    complete = path.with_suffix(path.suffix + ".bootstrap.complete.json")
    anchor = path.with_suffix(path.suffix + ".anchor.json")
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            _BOOTSTRAP_CRASH_SCRIPT,
            str(path),
            "after_ledger_bootstrap_complete_marker",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert completed.returncode == CRASH_EXIT_CODE, completed.stderr
    replay = complete.read_bytes()
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)):
        pass
    anchor.unlink()
    complete.write_bytes(replay)

    with pytest.raises(LedgerIntegrityError, match="anchor is missing"):
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)).unlock()

    assert not anchor.exists()
    assert complete.read_bytes() == replay


def test_bootstrap_marker_is_bound_to_exact_database_path(tmp_path: Path) -> None:
    original = tmp_path / "original.sqlite3"
    moved = tmp_path / "moved.sqlite3"
    original_pending = original.with_suffix(
        original.suffix + ".bootstrap.pending.json"
    )
    moved_pending = moved.with_suffix(moved.suffix + ".bootstrap.pending.json")
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            _BOOTSTRAP_CRASH_SCRIPT,
            str(original),
            "after_ledger_bootstrap_marker",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert completed.returncode == CRASH_EXIT_CODE, completed.stderr
    shutil.copyfile(original_pending, moved_pending)

    with pytest.raises(LedgerIntegrityError, match="path changed"):
        EncryptedLedger(moved, StaticKeyProvider(MASTER_KEY)).unlock()

    assert not moved.exists()
    assert moved_pending.is_file()


def test_bootstrap_marker_never_authorizes_unexpected_final_database(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    pending = path.with_suffix(path.suffix + ".bootstrap.pending.json")
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            _BOOTSTRAP_CRASH_SCRIPT,
            str(path),
            "after_ledger_bootstrap_marker",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert completed.returncode == CRASH_EXIT_CODE, completed.stderr
    marker_before = pending.read_bytes()
    unexpected = b"not-a-bootstrap-database"
    path.write_bytes(unexpected)

    with pytest.raises(LedgerIntegrityError, match="bootstrap database is invalid"):
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)).unlock()

    assert path.read_bytes() == unexpected
    assert pending.read_bytes() == marker_before
    assert not path.with_suffix(path.suffix + ".record-keys").exists()
    assert not path.with_suffix(path.suffix + ".anchor.json").exists()


def test_bootstrap_marker_binds_explicit_store_mode_and_requires_empty_store(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    store_path = tmp_path / "explicit-keys.json"
    pending = path.with_suffix(path.suffix + ".bootstrap.pending.json")
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            _EXPLICIT_BOOTSTRAP_CRASH_SCRIPT,
            str(path),
            str(store_path),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert completed.returncode == CRASH_EXIT_CODE, completed.stderr
    marker_before = pending.read_bytes()

    with pytest.raises(LedgerIntegrityError, match="mode changed"):
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)).unlock()
    assert not path.exists()
    assert pending.read_bytes() == marker_before

    store = FileRecordKeyStore(
        store_path,
        b"s" * 32,
        ledger_id="explicit-ledger",
    )
    store.put_pending("evt_unexpected", b"u" * 32)
    with pytest.raises(LedgerIntegrityError, match="store is not empty"):
        EncryptedLedger(
            path,
            StaticKeyProvider(MASTER_KEY),
            record_key_store=store,
        ).unlock()

    assert not path.exists()
    assert pending.read_bytes() == marker_before


def test_bootstrap_never_recursively_cleans_reserved_scratch_directory(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    pending = path.with_suffix(path.suffix + ".bootstrap.pending.json")
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            _BOOTSTRAP_CRASH_SCRIPT,
            str(path),
            "after_ledger_bootstrap_marker",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert completed.returncode == CRASH_EXIT_CODE, completed.stderr
    marker = json.loads(pending.read_bytes())
    bootstrap_id = marker["body"]["bootstrap_id"]
    scratch = tmp_path / f".{bootstrap_id}.aluclu-bootstrap.sqlite3"
    scratch.mkdir()
    unknown = scratch / "user-data.bin"
    unknown.write_bytes(b"must-not-be-recursively-deleted")

    with pytest.raises(LedgerIntegrityError, match="scratch is malformed"):
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)).unlock()

    assert unknown.read_bytes() == b"must-not-be-recursively-deleted"
    assert not path.exists()


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
