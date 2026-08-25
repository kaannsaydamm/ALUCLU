from __future__ import annotations

import base64
import hashlib
import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from aluclu.cognition import (
    DirectoryRecordKeyStore,
    LedgerIntegrityError,
    LedgerMigrationRequired,
    RecordKeyState,
)

INTEGRITY_KEY = b"m" * 32
LEDGER_ID = "ledger-1"
CRASH_EXIT_CODE = 74

_CRASH_SCRIPT = textwrap.dedent(
    """
    import os
    import sys
    from pathlib import Path

    from aluclu.cognition import DirectoryRecordKeyStore

    root = Path(sys.argv[1])
    boundary = sys.argv[2]
    operation = sys.argv[3]

    def terminate_at(candidate: str) -> None:
        if candidate == boundary:
            os._exit(74)

    store = DirectoryRecordKeyStore(
        root,
        b"m" * 32,
        ledger_id="ledger-1",
        _fault_injector=terminate_at,
    )
    if operation == "put":
        store.put_pending("evt_crash", b"d" * 32)
    elif operation == "shred":
        store.shred("evt_target", "ab" * 32)
    else:
        raise AssertionError(f"unknown operation: {operation}")

    raise SystemExit(75)
    """
)


def _file_fingerprint(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_directory_store_layout_hides_path_identity_and_encrypts_dek(
    tmp_path: Path,
) -> None:
    root = tmp_path / "keys"
    event_id = "customer:alice"
    dek = b"d" * 32
    store = DirectoryRecordKeyStore(root, INTEGRITY_KEY, ledger_id=LEDGER_ID)

    reference = store.put_pending(event_id, dek)
    store.mark_committed(event_id, "ab" * 32)

    relative_names = [path.relative_to(root).as_posix() for path in root.rglob("*")]
    assert all("customer" not in name and "alice" not in name for name in relative_names)
    assert len(reference.reference) == 64
    assert reference.reference == reference.reference.lower()
    int(reference.reference, 16)
    assert (root / "events" / reference.reference[:2] / f"{reference.reference}.json").is_file()
    assert (root / "identity.json").is_file()
    assert (root / "head.json").is_file()
    assert not (root / "prepare.json").exists()
    assert not (root / "staged.bin").exists()

    encoded_dek = base64.b64encode(dek)
    for path in root.rglob("*"):
        if path.is_file():
            persisted = path.read_bytes()
            assert dek not in persisted
            assert encoded_dek not in persisted
    assert store.get(event_id) == dek


def test_directory_store_state_machine_is_idempotent_and_never_resurrects(
    tmp_path: Path,
) -> None:
    store = DirectoryRecordKeyStore(
        tmp_path / "keys",
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
    )
    assert store.revision == 0

    pending = store.put_pending("evt_1", b"d" * 32)
    assert pending.state is RecordKeyState.PENDING
    assert store.revision == 1
    assert store.put_pending("evt_1", b"d" * 32) == pending
    assert store.revision == 1

    committed = store.mark_committed("evt_1", "ab" * 32)
    assert committed.state is RecordKeyState.COMMITTED
    assert committed.record_hash == "ab" * 32
    assert store.revision == 2
    assert store.mark_committed("evt_1", "ab" * 32) == committed
    assert store.revision == 2

    assert store.shred("evt_1", "ab" * 32)
    assert store.revision == 3
    assert not store.shred("evt_1", "ab" * 32)
    assert store.revision == 3
    assert store.get("evt_1") is None
    assert store.reference("evt_1") is None
    assert store.is_tombstoned("evt_1")
    assert store.tombstone_hash("evt_1") == "ab" * 32
    assert list(store.iter_tombstones()) == [("evt_1", "ab" * 32)]
    with pytest.raises(LedgerIntegrityError):
        store.put_pending("evt_1", b"n" * 32)


def test_directory_store_discards_only_pending_keys(tmp_path: Path) -> None:
    store = DirectoryRecordKeyStore(
        tmp_path / "keys",
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
    )
    store.put_pending("evt_pending", b"p" * 32)
    store.put_pending("evt_committed", b"c" * 32)
    store.mark_committed("evt_committed", "ab" * 32)

    assert store.discard_pending("evt_pending")
    assert not store.discard_pending("evt_committed")
    assert store.reference("evt_pending") is None
    assert store.get("evt_committed") == b"c" * 32


def test_directory_store_mutation_count_is_lifetime_independent(tmp_path: Path) -> None:
    root = tmp_path / "keys"
    store = DirectoryRecordKeyStore(root, INTEGRITY_KEY, ledger_id=LEDGER_ID)
    for index in range(256):
        event_id = f"evt_{index:06d}"
        store.put_pending(event_id, bytes([index % 251]) * 32)
        store.mark_committed(event_id, f"{index:064x}")

    before = _file_fingerprint(root)
    store.put_pending("evt_final", b"z" * 32)
    after = _file_fingerprint(root)
    changed = {
        path
        for path in before.keys() | after.keys()
        if before.get(path) != after.get(path)
    }

    assert len(changed) <= 6
    assert not (root / "prepare.json").exists()
    assert not (root / "staged.bin").exists()


def test_directory_store_detects_event_and_head_rollback(tmp_path: Path) -> None:
    root = tmp_path / "keys"
    store = DirectoryRecordKeyStore(root, INTEGRITY_KEY, ledger_id=LEDGER_ID)
    reference = store.put_pending("evt_1", b"d" * 32)
    event_path = root / "events" / reference.reference[:2] / f"{reference.reference}.json"
    old_event = event_path.read_bytes()
    old_head = (root / "head.json").read_bytes()
    store.mark_committed("evt_1", "ab" * 32)
    committed_event = event_path.read_bytes()

    event_path.write_bytes(old_event)
    with pytest.raises(LedgerIntegrityError):
        store.verify_integrity()

    event_path.write_bytes(committed_event)
    store.verify_integrity()
    (root / "head.json").write_bytes(old_head)
    with pytest.raises(LedgerIntegrityError):
        store.verify_integrity()


def test_directory_store_point_read_rejects_authenticated_event_rollback(
    tmp_path: Path,
) -> None:
    root = tmp_path / "keys"
    store = DirectoryRecordKeyStore(root, INTEGRITY_KEY, ledger_id=LEDGER_ID)
    reference = store.put_pending("evt_1", b"d" * 32)
    event_path = root / "events" / reference.reference[:2] / f"{reference.reference}.json"
    pending_event = event_path.read_bytes()
    store.mark_committed("evt_1", "ab" * 32)

    event_path.write_bytes(pending_event)

    with pytest.raises(LedgerIntegrityError):
        store.reference("evt_1")


@pytest.mark.parametrize("operation", ["mark_committed", "discard_pending"])
def test_directory_store_mutator_rejects_authenticated_event_rollback_without_writing(
    tmp_path: Path,
    operation: str,
) -> None:
    root = tmp_path / "keys"
    store = DirectoryRecordKeyStore(root, INTEGRITY_KEY, ledger_id=LEDGER_ID)
    reference = store.put_pending("evt_1", b"d" * 32)
    event_path = root / "events" / reference.reference[:2] / f"{reference.reference}.json"
    pending_event = event_path.read_bytes()
    store.mark_committed("evt_1", "ab" * 32)
    event_path.write_bytes(pending_event)
    before = _file_fingerprint(root)

    with pytest.raises(LedgerIntegrityError):
        if operation == "mark_committed":
            store.mark_committed("evt_1", "ab" * 32)
        else:
            store.discard_pending("evt_1")

    assert _file_fingerprint(root) == before


def test_directory_store_point_read_rejects_missing_committed_member(
    tmp_path: Path,
) -> None:
    root = tmp_path / "keys"
    store = DirectoryRecordKeyStore(root, INTEGRITY_KEY, ledger_id=LEDGER_ID)
    reference = store.put_pending("evt_1", b"d" * 32)
    store.mark_committed("evt_1", "ab" * 32)
    event_path = root / "events" / reference.reference[:2] / f"{reference.reference}.json"

    event_path.unlink()

    with pytest.raises(LedgerIntegrityError):
        store.get("evt_1")


def test_directory_store_point_read_never_resurrects_shredded_member(
    tmp_path: Path,
) -> None:
    root = tmp_path / "keys"
    store = DirectoryRecordKeyStore(root, INTEGRITY_KEY, ledger_id=LEDGER_ID)
    reference = store.put_pending("evt_1", b"d" * 32)
    store.mark_committed("evt_1", "ab" * 32)
    event_path = root / "events" / reference.reference[:2] / f"{reference.reference}.json"
    committed_event = event_path.read_bytes()
    store.shred("evt_1", "ab" * 32)
    tombstone_path = (
        root
        / "tombstones"
        / reference.reference[:2]
        / f"{reference.reference}.json"
    )

    tombstone_path.unlink()
    event_path.write_bytes(committed_event)

    with pytest.raises(LedgerIntegrityError):
        store.get("evt_1")


def test_directory_store_refreshes_membership_after_other_object_mutation(
    tmp_path: Path,
) -> None:
    root = tmp_path / "keys"
    first = DirectoryRecordKeyStore(root, INTEGRITY_KEY, ledger_id=LEDGER_ID)
    second = DirectoryRecordKeyStore(root, INTEGRITY_KEY, ledger_id=LEDGER_ID)

    second.put_pending("evt_external", b"e" * 32)

    assert first.get("evt_external") == b"e" * 32


def test_directory_store_rejects_consistent_same_revision_fork(tmp_path: Path) -> None:
    primary_root = tmp_path / "primary" / "keys"
    alternate_root = tmp_path / "alternate" / "keys"
    primary_root.parent.mkdir()
    alternate_root.parent.mkdir()
    DirectoryRecordKeyStore(primary_root, INTEGRITY_KEY, ledger_id=LEDGER_ID)
    shutil.copytree(primary_root, alternate_root)
    primary = DirectoryRecordKeyStore(primary_root, INTEGRITY_KEY, ledger_id=LEDGER_ID)
    alternate = DirectoryRecordKeyStore(alternate_root, INTEGRITY_KEY, ledger_id=LEDGER_ID)
    primary.put_pending("evt_primary", b"p" * 32)
    alternate.put_pending("evt_alternate", b"a" * 32)

    for member in (primary_root / "events").rglob("*.json"):
        member.unlink()
    shutil.copytree(
        alternate_root / "events",
        primary_root / "events",
        dirs_exist_ok=True,
    )
    (primary_root / "head.json").write_bytes(
        (alternate_root / "head.json").read_bytes()
    )

    with pytest.raises(LedgerIntegrityError):
        _ = primary.revision


def test_directory_store_local_mutations_do_not_rescan_lifetime_history(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = DirectoryRecordKeyStore(
        tmp_path / "keys",
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
    )

    def reject_full_scan() -> None:
        raise AssertionError("a local mutation triggered a lifetime-history scan")

    monkeypatch.setattr(store, "_verify_integrity_locked", reject_full_scan)
    store.put_pending("evt_1", b"d" * 32)
    store.mark_committed("evt_1", "ab" * 32)
    assert store.get("evt_1") == b"d" * 32
    assert store.shred("evt_1", "ab" * 32)
    assert store.is_tombstoned("evt_1")


@pytest.mark.parametrize(
    ("boundary", "committed"),
    [
        ("after_directory_staged", False),
        ("after_directory_prepare", True),
        ("after_directory_event_state", True),
        ("after_directory_head", True),
    ],
)
def test_directory_store_same_object_refreshes_membership_after_fault_recovery(
    tmp_path: Path,
    boundary: str,
    committed: bool,
) -> None:
    armed = True

    def inject(candidate: str) -> None:
        nonlocal armed
        if armed and candidate == boundary:
            armed = False
            raise RuntimeError("injected directory-store fault")

    store = DirectoryRecordKeyStore(
        tmp_path / "keys",
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        _fault_injector=inject,
    )

    with pytest.raises(RuntimeError, match="injected directory-store fault"):
        store.put_pending("evt_fault", b"f" * 32)

    assert store.get("evt_fault") == (b"f" * 32 if committed else None)
    assert store.revision == (1 if committed else 0)
    store.verify_integrity()


@pytest.mark.parametrize(
    ("boundary", "committed"),
    [
        ("after_directory_staged", False),
        ("after_directory_prepare", True),
        ("after_directory_event_state", True),
        ("after_directory_head", True),
        ("after_directory_cleanup", True),
    ],
)
def test_directory_store_real_process_append_crash_recovers_exactly_once(
    tmp_path: Path,
    boundary: str,
    committed: bool,
) -> None:
    root = tmp_path / "keys"
    DirectoryRecordKeyStore(root, INTEGRITY_KEY, ledger_id=LEDGER_ID)

    completed = subprocess.run(
        [sys.executable, "-c", _CRASH_SCRIPT, str(root), boundary, "put"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert completed.returncode == CRASH_EXIT_CODE, completed.stderr

    store = DirectoryRecordKeyStore(root, INTEGRITY_KEY, ledger_id=LEDGER_ID)
    if committed:
        assert store.get("evt_crash") == b"d" * 32
        assert store.revision == 1
    else:
        assert store.get("evt_crash") is None
        assert store.revision == 0
    store.verify_integrity()
    recovered_revision = store.revision

    reopened = DirectoryRecordKeyStore(root, INTEGRITY_KEY, ledger_id=LEDGER_ID)
    assert reopened.revision == recovered_revision
    assert reopened.get("evt_crash") == (b"d" * 32 if committed else None)
    assert not (root / "prepare.json").exists()
    assert not (root / "staged.bin").exists()


@pytest.mark.parametrize(
    ("boundary", "committed"),
    [
        ("after_directory_staged", False),
        ("after_directory_prepare", True),
        ("after_directory_event_state", True),
        ("after_directory_head", True),
        ("after_directory_cleanup", True),
    ],
)
def test_directory_store_real_process_shred_crash_never_resurrects(
    tmp_path: Path,
    boundary: str,
    committed: bool,
) -> None:
    root = tmp_path / "keys"
    store = DirectoryRecordKeyStore(root, INTEGRITY_KEY, ledger_id=LEDGER_ID)
    store.put_pending("evt_target", b"d" * 32)
    store.mark_committed("evt_target", "ab" * 32)

    completed = subprocess.run(
        [sys.executable, "-c", _CRASH_SCRIPT, str(root), boundary, "shred"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert completed.returncode == CRASH_EXIT_CODE, completed.stderr

    store = DirectoryRecordKeyStore(root, INTEGRITY_KEY, ledger_id=LEDGER_ID)
    if committed:
        assert store.get("evt_target") is None
        assert store.is_tombstoned("evt_target")
        assert store.tombstone_hash("evt_target") == "ab" * 32
        assert store.revision == 3
    else:
        assert store.get("evt_target") == b"d" * 32
        assert not store.is_tombstoned("evt_target")
        assert store.revision == 2
    store.verify_integrity()
    recovered_revision = store.revision

    reopened = DirectoryRecordKeyStore(root, INTEGRITY_KEY, ledger_id=LEDGER_ID)
    assert reopened.revision == recovered_revision
    assert reopened.is_tombstoned("evt_target") is committed
    assert not (root / "prepare.json").exists()
    assert not (root / "staged.bin").exists()


def test_directory_store_missing_open_is_side_effect_free(tmp_path: Path) -> None:
    root = tmp_path / "keys"

    with pytest.raises(LedgerIntegrityError):
        DirectoryRecordKeyStore(
            root,
            INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
            create=False,
        )

    assert list(tmp_path.iterdir()) == []


def test_directory_store_unknown_identity_version_fails_without_mutation(
    tmp_path: Path,
) -> None:
    root = tmp_path / "keys"
    DirectoryRecordKeyStore(root, INTEGRITY_KEY, ledger_id=LEDGER_ID)
    identity_path = root / "identity.json"
    identity = json.loads(identity_path.read_bytes())
    identity["body"]["version"] = 999
    identity_path.write_bytes(
        json.dumps(
            identity,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )
    before = _file_fingerprint(tmp_path)

    with pytest.raises(LedgerMigrationRequired):
        DirectoryRecordKeyStore(
            root,
            INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
            create=False,
        )

    assert _file_fingerprint(tmp_path) == before
