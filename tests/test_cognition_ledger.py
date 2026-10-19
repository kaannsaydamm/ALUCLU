import base64
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from aluclu.cognition import (
    DirectoryRecordKeyStore,
    EncryptedLedger,
    FileKeyProvider,
    FileRecordKeyStore,
    KeyringKeyProvider,
    KeyringRecordKeyStore,
    LedgerCapabilityUnavailable,
    LedgerConflictError,
    LedgerIntegrityError,
    LedgerKeyError,
    LedgerLifecycleError,
    LedgerMigrationRequired,
    LedgerSecurityScope,
    RecordKeyStoreProfile,
    StaticKeyProvider,
)
from aluclu.cognition import ledger as ledger_module
from aluclu.cognition.codec import MAX_PAYLOAD_BYTES

MASTER_KEY = b"m" * 32


class MemoryKeyringBackend:
    priority = 1

    def __init__(self) -> None:
        self.credentials: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self.credentials.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self.credentials[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        self.credentials.pop((service, username), None)


MemoryKeyringBackend.__module__ = "keyring.backends.Windows"


class AlternateMemoryKeyringBackend(MemoryKeyringBackend):
    pass


AlternateMemoryKeyringBackend.__module__ = "keyring.backends.macOS"


class MemoryKeyringModule:
    def __init__(self, backend: MemoryKeyringBackend) -> None:
        self._backend = backend

    def get_keyring(self) -> MemoryKeyringBackend:
        return self._backend

    def get_password(self, service: str, username: str) -> str | None:
        return self._backend.get_password(service, username)

    def set_password(self, service: str, username: str, password: str) -> None:
        self._backend.set_password(service, username, password)


class FlappingMemoryKeyringModule:
    def __init__(self, *backends: MemoryKeyringBackend) -> None:
        self._backends = list(backends)
        self._active = backends[0]
        self.calls = 0

    def get_keyring(self) -> MemoryKeyringBackend:
        index = min(self.calls, len(self._backends) - 1)
        self._active = self._backends[index]
        self.calls += 1
        return self._active

    def get_password(self, service: str, username: str) -> str | None:
        return self._active.get_password(service, username)

    def set_password(self, service: str, username: str, password: str) -> None:
        self._active.set_password(service, username, password)


@pytest.fixture
def memory_keyring(monkeypatch: pytest.MonkeyPatch) -> MemoryKeyringBackend:
    backend = MemoryKeyringBackend()
    monkeypatch.setitem(sys.modules, "keyring", MemoryKeyringModule(backend))
    return backend


def _keyring_provider_with_master(backend: MemoryKeyringBackend) -> KeyringKeyProvider:
    backend.set_password(
        "aluclu-test",
        "owner",
        base64.b64encode(MASTER_KEY).decode("ascii"),
    )
    return KeyringKeyProvider("aluclu-test", "owner")


def test_construction_is_side_effect_free_and_lifecycle_is_typed(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    ledger = EncryptedLedger(path, StaticKeyProvider(MASTER_KEY))

    assert list(tmp_path.iterdir()) == []
    for operation in (
        ledger.event_count,
        lambda: ledger.read(""),
        lambda: ledger.append("", {"value": 1}),
        lambda: ledger.append_once("", {"value": 1}),
        lambda: ledger.shred(""),
        lambda: ledger.is_tombstoned(""),
    ):
        with pytest.raises(LedgerLifecycleError):
            operation()

    ledger.unlock()
    ledger.unlock()
    ledger.close()
    ledger.close()
    for operation in (
        ledger.event_count,
        lambda: ledger.read(""),
        lambda: ledger.append("", {"value": 1}),
        lambda: ledger.append_once("", {"value": 1}),
        lambda: ledger.shred(""),
        lambda: ledger.is_tombstoned(""),
    ):
        with pytest.raises(LedgerLifecycleError):
            operation()


def test_every_ledger_connection_enables_required_security_pragmas(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        connection = ledger._connection_required()
        assert connection.execute("PRAGMA trusted_schema").fetchone() == (0,)
        assert connection.execute("PRAGMA cell_size_check").fetchone() == (1,)

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        connection = ledger._connection_required()
        assert connection.execute("PRAGMA trusted_schema").fetchone() == (0,)
        assert connection.execute("PRAGMA cell_size_check").fetchone() == (1,)


def test_append_round_trip_is_encrypted_and_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    marker = "plain-marker-should-not-hit-sqlite"

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        first = ledger.append_once("evt_1", {"secret": marker})
        again = ledger.append_once("evt_1", {"secret": marker})

        assert first.created is True
        assert again.created is False
        assert again.record == first.record
        assert ledger.read("evt_1") == first.record
        assert ledger.event_count() == 1

    assert marker.encode() not in path.read_bytes()


def test_append_and_append_once_reject_conflicting_lineage(tmp_path: Path) -> None:
    with EncryptedLedger(tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)) as ledger:
        ledger.append("evt_1", {"value": 1})

        with pytest.raises(LedgerConflictError):
            ledger.append("evt_1", {"value": 1})
        with pytest.raises(LedgerConflictError):
            ledger.append_once("evt_1", {"value": 2})


def test_shred_destroys_key_but_preserves_authenticated_lineage(tmp_path: Path) -> None:
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
        outcome = ledger.append("evt_1", {"secret": "never-resurrect"})

        assert ledger.is_tombstoned("evt_1") is False
        assert ledger.shred("evt_1") is True
        assert ledger.shred("evt_1") is False
        assert ledger.read("evt_1") is None
        assert ledger.is_tombstoned("evt_1") is True
        assert ledger.event_count() == 2
        assert store.get("evt_1") is None
        assert store.tombstone_hash("evt_1") == outcome.record.record_hash
        ledger.verify_integrity()

    with EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        record_key_store=store,
    ) as ledger:
        assert ledger.read("evt_1") is None
        assert ledger.is_tombstoned("evt_1") is True
        ledger.verify_integrity()


def test_shred_absent_event_is_a_noop_and_event_id_never_resurrects(tmp_path: Path) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        assert ledger.shred("evt_missing") is False
        assert ledger.is_tombstoned("evt_missing") is False
        assert ledger.event_count() == 0

        ledger.append("evt_1", {"value": 1})
        assert ledger.shred("evt_1") is True

        with pytest.raises(LedgerConflictError):
            ledger.append("evt_1", {"value": 2})
        with pytest.raises(LedgerConflictError):
            ledger.append_once("evt_1", {"value": 2})


def test_wrong_master_key_cannot_claim_existing_empty_ledger(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(b"a" * 32)):
        pass

    with pytest.raises(LedgerKeyError):
        EncryptedLedger(path, StaticKeyProvider(b"b" * 32)).unlock()


def test_existing_incomplete_database_is_never_initialized(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    connection = sqlite3.connect(path)
    try:
        connection.execute("CREATE TABLE legacy(value TEXT)")
        connection.execute("PRAGMA user_version = 1")
        connection.commit()
        assert connection.execute("PRAGMA journal_mode").fetchone() == ("delete",)
    finally:
        connection.close()

    with pytest.raises(LedgerMigrationRequired):
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)).unlock()

    connection = sqlite3.connect(path)
    try:
        assert connection.execute("PRAGMA user_version").fetchone() == (1,)
        assert connection.execute("PRAGMA journal_mode").fetchone() == ("delete",)
        assert {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        } == {"legacy"}
    finally:
        connection.close()


def test_schema_v2_requires_explicit_migration_without_mutation(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    connection = sqlite3.connect(path)
    try:
        connection.execute("CREATE TABLE legacy_v2(value TEXT)")
        connection.execute("INSERT INTO legacy_v2(value) VALUES ('preserve')")
        connection.execute("PRAGMA user_version = 2")
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(
        LedgerMigrationRequired,
        match="explicit migration to schema v3",
    ):
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)).unlock()

    connection = sqlite3.connect(path)
    try:
        assert connection.execute("PRAGMA user_version").fetchone() == (2,)
        assert connection.execute("SELECT value FROM legacy_v2").fetchone() == (
            "preserve",
        )
    finally:
        connection.close()

def test_relative_ledger_path_does_not_follow_later_chdir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    monkeypatch.chdir(first)
    ledger = EncryptedLedger("memory.sqlite3", StaticKeyProvider(MASTER_KEY))

    monkeypatch.chdir(second)
    with ledger:
        ledger.append("evt_1", {"value": 1})

    assert (first / "memory.sqlite3").is_file()
    assert not (second / "memory.sqlite3").exists()


def test_schema_v3_and_exact_metadata_keys_are_created(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)):
        pass

    connection = sqlite3.connect(path)
    try:
        assert connection.execute("PRAGMA user_version").fetchone() == (3,)
        metadata = {row[0] for row in connection.execute("SELECT key FROM metadata")}
        assert metadata == {
            "schema_version",
            "ledger_id",
            "identity_root",
            "key_check",
            "head_sequence",
            "head_hash",
        }
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        assert tables == {
            "append_witnesses",
            "history",
            "metadata",
            "records",
            "tombstones",
        }
    finally:
        connection.close()


def test_schema_column_drift_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)):
        pass
    connection = sqlite3.connect(path)
    try:
        connection.execute("ALTER TABLE history ADD COLUMN injected TEXT")
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(LedgerIntegrityError):
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)).unlock()


def test_missing_identity_metadata_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)):
        pass
    connection = sqlite3.connect(path)
    try:
        connection.execute("DELETE FROM metadata WHERE key = 'identity_root'")
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(LedgerIntegrityError):
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)).unlock()


def test_existing_ledger_rejects_record_store_identity_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)):
        pass
    wrong_store = FileRecordKeyStore(
        tmp_path / "wrong-keys.json",
        b"s" * 32,
        ledger_id="wrong-ledger",
    )

    with pytest.raises(LedgerIntegrityError):
        EncryptedLedger(
            path,
            StaticKeyProvider(MASTER_KEY),
            record_key_store=wrong_store,
        ).unlock()


def test_new_ledger_accepts_explicit_matching_record_store(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    store = FileRecordKeyStore(
        tmp_path / "custom-keys.json",
        b"s" * 32,
        ledger_id="özel-ledger",
    )

    with EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        record_key_store=store,
    ) as ledger:
        assert ledger.ledger_id == "özel-ledger"
        ledger.append("evt_1", {"value": 1})
        assert ledger.read("evt_1") is not None


def test_explicit_file_record_store_at_default_legacy_path_remains_supported(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    legacy_path = path.with_suffix(path.suffix + ".record-keys.json")
    store = FileRecordKeyStore(
        legacy_path,
        b"s" * 32,
        ledger_id="explicit-ledger",
    )

    with EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        record_key_store=store,
    ) as ledger:
        ledger.append("evt_1", {"value": 1})
        assert ledger.read("evt_1") is not None

    with EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        record_key_store=store,
    ) as reopened:
        assert reopened.read("evt_1") is not None
        reopened.verify_integrity()

    assert legacy_path.is_file()
    assert not path.with_suffix(path.suffix + ".record-keys").exists()


def test_history_hash_matches_independent_literal_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "memory.sqlite3"
    random_values = iter(
        [b"i" * 32, b"d" * 32, b"w" * 12, b"n" * 12, b"c" * 12]
    )
    monkeypatch.setattr(ledger_module.secrets, "token_hex", lambda size: "11" * size)
    monkeypatch.setattr(
        ledger_module.secrets,
        "token_bytes",
        lambda size: next(random_values),
    )
    monkeypatch.setattr(ledger_module.time, "time_ns", lambda: 123_456_789)

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        outcome = ledger.append("evt_1", {"value": 1})

    connection = sqlite3.connect(path)
    try:
        ciphertext, record_hash = connection.execute(
            "SELECT ciphertext, record_hash FROM history WHERE sequence = 1"
        ).fetchone()
    finally:
        connection.close()

    assert ciphertext.hex() == "8fc5417fe8025043d55f044315ba791e56ff5a537db7090577525c"
    assert outcome.record.record_hash == (
        "dfd836e27cd9830968da021a8e2e222269f5b52b13e79cc4b79df13abb8479be"
    )
    assert record_hash.hex() == outcome.record.record_hash


def test_ledger_accepts_exact_maximum_canonical_payload(tmp_path: Path) -> None:
    payload = "x" * (MAX_PAYLOAD_BYTES - 2)

    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        outcome = ledger.append("evt_max", payload)
        assert outcome.record.payload == payload
        assert ledger.read("evt_max") == outcome.record


@pytest.mark.parametrize(
    "mutation",
    [
        "UPDATE history SET ciphertext = X'00' WHERE sequence = 1",
        "DELETE FROM records WHERE event_id = 'evt_1'",
        "UPDATE metadata SET value = X'00' WHERE key = 'head_hash'",
    ],
)
def test_direct_sql_tamper_fails_full_verification(tmp_path: Path, mutation: str) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        ledger.append("evt_1", {"value": 1})

    connection = sqlite3.connect(path)
    try:
        connection.execute(mutation)
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(LedgerIntegrityError):
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)).unlock()


def test_forged_tombstone_projection_fails_full_verification(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        ledger.append("evt_1", {"value": 1})

    connection = sqlite3.connect(path)
    try:
        connection.execute("DELETE FROM records WHERE event_id = 'evt_1'")
        connection.execute(
            """
            INSERT INTO tombstones(event_id, history_sequence, record_hash)
            SELECT event_id, sequence, record_hash FROM history WHERE sequence = 1
            """
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(LedgerIntegrityError):
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)).unlock()


def test_missing_anchor_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)):
        pass
    anchor = path.with_suffix(path.suffix + ".anchor.json")
    anchor.unlink()

    with pytest.raises(LedgerIntegrityError):
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)).unlock()


def test_invalid_utf8_and_duplicate_json_anchor_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    anchor = path.with_suffix(path.suffix + ".anchor.json")
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)):
        pass

    for invalid in (
        b"\xff",
        b'{"mac":"00","mac":"11","payload":{}}',
    ):
        anchor.write_bytes(invalid)
        with pytest.raises(LedgerIntegrityError):
            EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)).unlock()


def test_valid_lagging_anchor_advances_only_after_full_verification(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    anchor = path.with_suffix(path.suffix + ".anchor.json")
    ledger = EncryptedLedger(path, StaticKeyProvider(MASTER_KEY))
    ledger.unlock()
    old_anchor = anchor.read_bytes()
    try:
        ledger.append("evt_1", {"value": 1})
        current_anchor = anchor.read_bytes()
        anchor.write_bytes(old_anchor)

        ledger.verify_integrity()

        assert anchor.read_bytes() == current_anchor
    finally:
        ledger.close()


def test_static_provider_uses_directory_record_store_by_default(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    expected_root = path.with_suffix(path.suffix + ".record-keys")

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        ledger.append("evt_1", {"value": 1})
        store = ledger._record_store_required()
        assert isinstance(store, DirectoryRecordKeyStore)

    assert expected_root.is_dir()
    assert (expected_root / "identity.json").is_file()
    assert not path.with_suffix(path.suffix + ".record-keys.json").exists()


def test_local_file_provider_uses_directory_record_store_by_default(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    key_path = tmp_path / "master.key"

    with EncryptedLedger(path, FileKeyProvider(key_path, create=True)) as ledger:
        ledger.append("evt_1", {"value": 1})
        assert isinstance(ledger._record_store_required(), DirectoryRecordKeyStore)

    assert key_path.is_file()
    assert path.with_suffix(path.suffix + ".record-keys").is_dir()
    assert not path.with_suffix(path.suffix + ".record-keys.json").exists()


def test_os_keyring_provider_uses_keyring_record_store_by_default(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
) -> None:
    path = tmp_path / "memory.sqlite3"
    provider = _keyring_provider_with_master(memory_keyring)

    with EncryptedLedger(path, provider) as ledger:
        ledger.append("evt_1", {"value": 1})
        store = ledger._record_store_required()
        assert isinstance(store, KeyringRecordKeyStore)
        assert store.profile is RecordKeyStoreProfile.OS_KEYRING

    with EncryptedLedger(path, provider) as reopened:
        record = reopened.read("evt_1")

    assert record is not None
    assert record.payload == {"value": 1}
    assert path.with_suffix(path.suffix + ".record-keys").is_dir()
    assert not path.with_suffix(path.suffix + ".record-keys.json").exists()


def test_os_keyring_master_and_record_keys_share_one_captured_backend(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "memory.sqlite3"
    captured_backend = MemoryKeyringBackend()
    alternate_backend = AlternateMemoryKeyringBackend()
    provider = _keyring_provider_with_master(captured_backend)
    keyring_module = FlappingMemoryKeyringModule(
        captured_backend,
        alternate_backend,
    )
    monkeypatch.setitem(sys.modules, "keyring", keyring_module)

    with EncryptedLedger(path, provider) as ledger:
        ledger.append("evt_1", {"value": 1})

    assert keyring_module.calls == 1
    assert captured_backend.credentials
    assert alternate_backend.credentials == {}


def test_os_keyring_capability_failure_precedes_provider_or_disk_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "keyring", None)
    path = tmp_path / "memory.sqlite3"
    ledger = EncryptedLedger(path, KeyringKeyProvider("aluclu-test", "owner"))

    with pytest.raises(LedgerCapabilityUnavailable):
        ledger.unlock()

    assert list(tmp_path.iterdir()) == []


def test_os_keyring_scope_fails_before_provider_or_persistence_mutation(
    tmp_path: Path,
) -> None:
    class OsScopeProvider:
        @property
        def security_scope(self) -> LedgerSecurityScope:
            return LedgerSecurityScope.OS_KEYRING

        def get_key(self) -> bytes:
            raise AssertionError("Task 5 capability gate must run before get_key")

    path = tmp_path / "memory.sqlite3"
    ledger = EncryptedLedger(path, OsScopeProvider())

    with pytest.raises(LedgerCapabilityUnavailable):
        ledger.unlock()

    assert list(tmp_path.iterdir()) == []


def test_os_keyring_bootstrap_marker_binds_captured_store_backend(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class StopAfterMarker(Exception):
        pass

    def stop_after_marker(boundary: str) -> None:
        if boundary == "after_ledger_bootstrap_marker":
            raise StopAfterMarker

    path = tmp_path / "memory.sqlite3"
    provider = _keyring_provider_with_master(memory_keyring)
    pending = path.with_suffix(path.suffix + ".bootstrap.pending.json")

    with pytest.raises(StopAfterMarker):
        EncryptedLedger(
            path,
            provider,
            _fault_injector=stop_after_marker,
        ).unlock()
    marker_before = pending.read_bytes()

    alternate_backend = AlternateMemoryKeyringBackend()
    alternate_backend.credentials.update(memory_keyring.credentials)
    monkeypatch.setitem(sys.modules, "keyring", MemoryKeyringModule(alternate_backend))

    with pytest.raises(LedgerIntegrityError, match="binding changed"):
        EncryptedLedger(path, provider).unlock()

    assert pending.read_bytes() == marker_before
    assert not path.exists()


def test_explicit_keyring_store_must_match_provider_binding(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
) -> None:
    path = tmp_path / "memory.sqlite3"
    store = KeyringRecordKeyStore(
        path.with_suffix(path.suffix + ".record-keys"),
        b"s" * 32,
        ledger_id="ledger-1",
        service="aluclu-test",
        username_prefix="owner",
        database_path=path,
    )
    memory_keyring.set_password(
        "aluclu-test",
        "other-owner",
        base64.b64encode(MASTER_KEY).decode("ascii"),
    )

    with pytest.raises(LedgerIntegrityError, match="binding changed"):
        EncryptedLedger(
            path,
            KeyringKeyProvider("aluclu-test", "other-owner"),
            record_key_store=store,
        ).unlock()

    assert not path.exists()
    assert not path.with_suffix(path.suffix + ".bootstrap.pending.json").exists()


def test_explicit_keyring_store_with_matching_binding_opens(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
) -> None:
    path = tmp_path / "memory.sqlite3"
    provider = _keyring_provider_with_master(memory_keyring)
    store = KeyringRecordKeyStore(
        path.with_suffix(path.suffix + ".record-keys"),
        b"s" * 32,
        ledger_id="ledger-1",
        service="aluclu-test",
        username_prefix="owner",
        database_path=path,
    )

    with EncryptedLedger(path, provider, record_key_store=store) as ledger:
        ledger.append("evt_1", {"value": 1})

    with EncryptedLedger(path, provider, record_key_store=store) as reopened:
        record = reopened.read("evt_1")

    assert record is not None
    assert record.payload == {"value": 1}


def test_explicit_keyring_store_still_preflights_provider_backend(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "memory.sqlite3"
    store_root = path.with_suffix(path.suffix + ".record-keys")
    provider = _keyring_provider_with_master(memory_keyring)
    store = KeyringRecordKeyStore(
        store_root,
        b"s" * 32,
        ledger_id="ledger-1",
        service="aluclu-test",
        username_prefix="owner",
        database_path=path,
    )
    store_before = {
        store_path.relative_to(store_root): store_path.read_bytes()
        for store_path in store_root.rglob("*")
        if store_path.is_file()
    }
    monkeypatch.setitem(sys.modules, "keyring", None)

    with pytest.raises(LedgerCapabilityUnavailable):
        EncryptedLedger(path, provider, record_key_store=store).unlock()

    store_after = {
        store_path.relative_to(store_root): store_path.read_bytes()
        for store_path in store_root.rglob("*")
        if store_path.is_file()
    }
    assert store_after == store_before
    assert not path.exists()
    assert not path.with_suffix(path.suffix + ".bootstrap.pending.json").exists()


@pytest.mark.parametrize("legacy_kind", ["monolithic", "file_at_directory_root"])
def test_default_directory_store_rejects_legacy_or_file_state_without_mutation(
    tmp_path: Path,
    legacy_kind: str,
) -> None:
    path = tmp_path / "memory.sqlite3"
    if legacy_kind == "monolithic":
        legacy = path.with_suffix(path.suffix + ".record-keys.json")
    else:
        legacy = path.with_suffix(path.suffix + ".record-keys")
    legacy.write_bytes(b"legacy-state")
    before = {item.name: item.read_bytes() for item in tmp_path.iterdir()}

    with pytest.raises(LedgerMigrationRequired):
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)).unlock()

    after = {item.name: item.read_bytes() for item in tmp_path.iterdir()}
    assert after == before


def test_open_ledger_detects_external_key_check_mutation(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    ledger = EncryptedLedger(path, StaticKeyProvider(MASTER_KEY))
    ledger.unlock()
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "UPDATE metadata SET value = zeroblob(32) WHERE key = 'key_check'"
        )
        connection.commit()
    finally:
        connection.close()

    try:
        with pytest.raises(LedgerKeyError):
            ledger.verify_integrity()
    finally:
        ledger.close()


def test_anchor_replaced_by_symlink_after_construction_fails_closed(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    ledger = EncryptedLedger(path, StaticKeyProvider(MASTER_KEY))
    ledger.unlock()
    anchor = path.with_suffix(path.suffix + ".anchor.json")
    target = tmp_path / "copied-anchor.json"
    target.write_bytes(anchor.read_bytes())
    anchor.unlink()
    try:
        anchor.symlink_to(target)
    except (OSError, NotImplementedError):
        ledger.close()
        pytest.skip("symlinks are unavailable on this platform")

    try:
        with pytest.raises(LedgerIntegrityError):
            ledger.verify_integrity()
    finally:
        ledger.close()


def test_two_ledger_objects_cannot_fork_history(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    ledgers = [
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)),
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)),
    ]
    for ledger in ledgers:
        ledger.unlock()
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(
                pool.map(
                    lambda item: item[0].append(*item[1]),
                    zip(
                        ledgers,
                        [("evt_1", {"i": 1}), ("evt_2", {"i": 2})],
                        strict=True,
                    ),
                )
            )

        assert {outcome.record.sequence for outcome in outcomes} == {1, 2}
        ledgers[0].verify_integrity()
    finally:
        for ledger in ledgers:
            ledger.close()


def test_two_ledger_objects_sustain_concurrent_append_streams(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    ledgers = [
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)),
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)),
    ]
    for ledger in ledgers:
        ledger.unlock()

    def append_stream(ledger: EncryptedLedger, stream: int) -> list[int]:
        return [
            ledger.append(f"stream_{stream}_{index}", {"index": index}).record.sequence
            for index in range(32)
        ]

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(append_stream, ledger, stream)
                for stream, ledger in enumerate(ledgers)
            ]
            sequences = [
                sequence
                for future in futures
                for sequence in future.result(timeout=600)
            ]

        assert sorted(sequences) == list(range(1, 65))
        assert ledgers[0].event_count() == 64
        ledgers[0].verify_integrity()
    finally:
        for ledger in ledgers:
            ledger.close()
