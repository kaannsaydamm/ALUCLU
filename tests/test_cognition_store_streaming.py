from __future__ import annotations

import gc
import sys
import weakref
from dataclasses import FrozenInstanceError, dataclass
from pathlib import Path
from typing import Any

import pytest

from aluclu.cognition import (
    DirectoryRecordKeyStore,
    KeyringRecordKeyStore,
    LedgerIntegrityError,
    RecordKeyReference,
    RecordKeyState,
    atomic_write_bytes,
)

INTEGRITY_KEY = b"i" * 32
LEDGER_ID = "ledger-streaming"


class MemoryKeyringBackend:
    priority = 1

    def __init__(self) -> None:
        self.credentials: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self.credentials.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self.credentials[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        try:
            del self.credentials[(service, username)]
        except KeyError as exc:
            raise RuntimeError("credential is missing") from exc


MemoryKeyringBackend.__module__ = "keyring.backends.Windows"


class MemoryKeyringModule:
    def __init__(self, backend: MemoryKeyringBackend) -> None:
        self._backend = backend

    def get_keyring(self) -> MemoryKeyringBackend:
        return self._backend


@dataclass(frozen=True)
class _StoreHarness:
    name: str
    root: Path
    store: DirectoryRecordKeyStore


class _TrackedDecodedEvent:
    __slots__ = ("_event", "__weakref__")

    def __init__(self, event: Any) -> None:
        self._event = event

    def __getattr__(self, name: str) -> Any:
        return getattr(self._event, name)


@pytest.fixture(params=("directory", "keyring"))
def store_harness(
    request: pytest.FixtureRequest,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> _StoreHarness:
    name = str(request.param)
    root = tmp_path / f"{name}-keys"
    if name == "directory":
        store: DirectoryRecordKeyStore = DirectoryRecordKeyStore(
            root,
            INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
        )
    else:
        backend = MemoryKeyringBackend()
        monkeypatch.setitem(sys.modules, "keyring", MemoryKeyringModule(backend))
        store = KeyringRecordKeyStore(
            root,
            INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
            service="aluclu-test",
            username_prefix="owner",
            database_path=tmp_path / "memory.sqlite3",
        )
    return _StoreHarness(name=name, root=root, store=store)


def _put_pending_records(
    store: DirectoryRecordKeyStore,
    event_ids: list[str],
) -> dict[str, RecordKeyReference]:
    return {
        event_id: store.put_pending(event_id, bytes([index + 1]) * 32)
        for index, event_id in enumerate(event_ids)
    }


def _put_committed(
    store: DirectoryRecordKeyStore,
    event_id: str,
    index: int,
) -> str:
    record_hash = f"{index + 1:064x}"
    store.put_pending(event_id, bytes([index + 1]) * 32)
    reference = store.mark_committed(event_id, record_hash)
    assert reference.state is RecordKeyState.COMMITTED
    return record_hash


def _event_path(root: Path, reference: RecordKeyReference) -> Path:
    token = reference.reference
    return root / "events" / token[:2] / f"{token}.json"


def test_store_verification_does_not_retain_decoded_events_or_plaintext_deks(
    store_harness: _StoreHarness,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    event_ids = [f"evt_{index:02d}" for index in range(16)]
    _put_pending_records(store_harness.store, event_ids)

    original_decode = store_harness.store._decode_event
    decoded_refs: list[weakref.ReferenceType[_TrackedDecodedEvent]] = []
    retained_before_decode: list[int] = []

    def tracked_decode(encoded: bytes, *, expected_token: str) -> Any:
        gc.collect()
        retained_before_decode.append(
            sum(reference() is not None for reference in decoded_refs)
        )
        tracked = _TrackedDecodedEvent(
            original_decode(encoded, expected_token=expected_token)
        )
        decoded_refs.append(weakref.ref(tracked))
        return tracked

    monkeypatch.setattr(store_harness.store, "_decode_event", tracked_decode)

    store_harness.store.verify_integrity()
    gc.collect()

    # One prior loop temporary may remain alive while Python evaluates the
    # next decoder call. Retaining two means verification accumulated events.
    assert max(retained_before_decode, default=0) <= 1
    assert all(reference() is None for reference in decoded_refs)


def test_failed_scan_forces_fresh_membership_verification_after_exact_restore(
    store_harness: _StoreHarness,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    references = _put_pending_records(
        store_harness.store,
        ["evt_alpha", "evt_beta", "evt_gamma"],
    )
    target = _event_path(store_harness.root, references["evt_beta"])
    original = target.read_bytes()
    tampered = bytearray(original)
    tampered[len(tampered) // 2] ^= 1
    atomic_write_bytes(target, bytes(tampered))
    try:
        with pytest.raises(LedgerIntegrityError):
            store_harness.store.verify_integrity()
    finally:
        atomic_write_bytes(target, original)

    assert target.read_bytes() == original
    original_verify = store_harness.store._verify_integrity_locked
    verification_calls = 0

    def counted_verify() -> Any:
        nonlocal verification_calls
        verification_calls += 1
        return original_verify()

    monkeypatch.setattr(
        store_harness.store,
        "_verify_integrity_locked",
        counted_verify,
    )

    recovered = store_harness.store.reference("evt_beta")

    assert recovered == references["evt_beta"]
    assert verification_calls >= 1


def test_reference_and_tombstone_iterators_are_sorted_frozen_snapshots(
    store_harness: _StoreHarness,
) -> None:
    store = store_harness.store
    hashes = {
        event_id: _put_committed(store, event_id, index)
        for index, event_id in enumerate(["evt_z", "evt_a", "evt_m", "evt_y"])
    }
    assert store.shred("evt_z", hashes["evt_z"])
    assert store.shred("evt_a", hashes["evt_a"])

    reference_snapshot = store.iter_references()
    tombstone_snapshot = store.iter_tombstones()

    hashes["evt_b"] = _put_committed(store, "evt_b", 4)
    assert store.shred("evt_m", hashes["evt_m"])

    old_references = tuple(reference_snapshot)
    old_tombstones = tuple(tombstone_snapshot)
    assert [reference.event_id for reference in old_references] == [
        "evt_m",
        "evt_y",
    ]
    assert old_tombstones == (
        ("evt_a", hashes["evt_a"]),
        ("evt_z", hashes["evt_z"]),
    )
    with pytest.raises(FrozenInstanceError):
        old_references[0].event_id = "evt_changed"  # type: ignore[misc]

    assert [reference.event_id for reference in store.iter_references()] == [
        "evt_b",
        "evt_y",
    ]
    assert tuple(store.iter_tombstones()) == (
        ("evt_a", hashes["evt_a"]),
        ("evt_m", hashes["evt_m"]),
        ("evt_z", hashes["evt_z"]),
    )
