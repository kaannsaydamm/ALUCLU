from __future__ import annotations

import base64
import importlib
import sys
import uuid
from collections.abc import Callable
from pathlib import Path

import pytest

from aluclu.cognition import (
    DirectoryRecordKeyStore,
    InputBoundaryError,
    KeyringKeyProvider,
    KeyringRecordKeyStore,
    LedgerCapabilityUnavailable,
    LedgerIntegrityError,
    LedgerRollbackError,
    RecordKeyState,
    RecordKeyStoreProfile,
    StaticKeyProvider,
    create_record_key_store,
)

INTEGRITY_KEY = b"i" * 32
MASTER_KEY = b"m" * 32
LEDGER_ID = "ledger-1"
RECORD_HASH = "ab" * 32


class SimulatedCrash(RuntimeError):
    pass


class ArmedFault:
    def __init__(self) -> None:
        self.boundary: str | None = None

    def __call__(self, boundary: str) -> None:
        if boundary == self.boundary:
            raise SimulatedCrash(boundary)


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

    def get_password(self, service: str, username: str) -> str | None:
        return self._backend.get_password(service, username)

    def set_password(self, service: str, username: str, password: str) -> None:
        self._backend.set_password(service, username, password)


class FlappingKeyringModule:
    def __init__(self, *backends: MemoryKeyringBackend) -> None:
        self._backends = list(backends)
        self.calls = 0

    def get_keyring(self) -> MemoryKeyringBackend:
        self.calls += 1
        index = min(self.calls - 1, len(self._backends) - 1)
        return self._backends[index]


@pytest.fixture
def memory_keyring(monkeypatch: pytest.MonkeyPatch) -> MemoryKeyringBackend:
    backend = MemoryKeyringBackend()
    monkeypatch.setitem(sys.modules, "keyring", MemoryKeyringModule(backend))
    return backend


def _provider_with_master(backend: MemoryKeyringBackend) -> KeyringKeyProvider:
    backend.set_password(
        "aluclu-test",
        "owner",
        base64.b64encode(MASTER_KEY).decode("ascii"),
    )
    return KeyringKeyProvider("aluclu-test", "owner")


def test_record_store_profiles_and_static_factory_selection(tmp_path: Path) -> None:
    store = create_record_key_store(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
        integrity_key=INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        create=True,
    )

    assert isinstance(store, DirectoryRecordKeyStore)
    assert store.profile is RecordKeyStoreProfile.DIRECTORY


def test_keyring_factory_selects_keyring_store(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
) -> None:
    provider = _provider_with_master(memory_keyring)

    store = create_record_key_store(
        tmp_path / "memory.sqlite3",
        provider,
        integrity_key=INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        create=True,
    )

    assert isinstance(store, KeyringRecordKeyStore)
    assert store.profile is RecordKeyStoreProfile.OS_KEYRING


def test_keyring_capability_failure_precedes_disk_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "keyring", None)

    with pytest.raises(LedgerCapabilityUnavailable):
        create_record_key_store(
            tmp_path / "memory.sqlite3",
            KeyringKeyProvider("aluclu-test", "owner"),
            integrity_key=INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
            create=True,
        )

    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    ("service", "username_prefix"),
    [
        ("", "owner"),
        ("aluclu-test", ""),
        ("s" * 192, "owner"),
        ("aluclu-test", "u" * 192),
        ("ALUCLU", "owner"),
        ("aluclu", "Owner"),
        ("aluclu:test", "owner"),
        ("aluclu", "owner@host"),
    ],
)
def test_keyring_store_rejects_nonportable_identifiers_before_backend_or_disk_mutation(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
    service: str,
    username_prefix: str,
) -> None:
    with pytest.raises(InputBoundaryError):
        KeyringRecordKeyStore(
            tmp_path / "keys",
            INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
            service=service,
            username_prefix=username_prefix,
        )

    assert memory_keyring.credentials == {}
    assert list(tmp_path.iterdir()) == []


def test_keyring_maximum_identifiers_recover_after_root_publish_crash(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
) -> None:
    root = tmp_path / "keys"
    fault = ArmedFault()
    fault.boundary = "after_keyring_initialize_publish"

    with pytest.raises(SimulatedCrash):
        KeyringRecordKeyStore(
            root,
            INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
            service="s" * 191,
            username_prefix="u" * 191,
            _fault_injector=fault,
        )

    reopened = KeyringRecordKeyStore(
        root,
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        service="s" * 191,
        username_prefix="u" * 191,
        create=True,
    )

    reopened.verify_integrity()
    assert reopened.revision == 0
    assert not (root / "init.json").exists()


def test_keyring_credentials_transport_unicode_identity_as_bounded_ascii_and_recover(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
) -> None:
    root = tmp_path / "kéys"
    database_path = tmp_path / "données" / "mémoire.sqlite3"
    ledger_id = "lédger-世界"
    fault = ArmedFault()
    fault.boundary = "after_keyring_initialize_publish"

    with pytest.raises(SimulatedCrash):
        KeyringRecordKeyStore(
            root,
            INTEGRITY_KEY,
            ledger_id=ledger_id,
            service="aluclu-test",
            username_prefix="owner",
            database_path=database_path,
            _fault_injector=fault,
        )

    store = KeyringRecordKeyStore(
        root,
        INTEGRITY_KEY,
        ledger_id=ledger_id,
        service="aluclu-test",
        username_prefix="owner",
        database_path=database_path,
        create=True,
    )
    store.put_pending("evt-1", b"d" * 32)

    reopened = KeyringRecordKeyStore(
        root,
        INTEGRITY_KEY,
        ledger_id=ledger_id,
        service="aluclu-test",
        username_prefix="owner",
        database_path=database_path,
        create=False,
    )

    assert reopened.get("evt-1") == b"d" * 32
    reopened.verify_integrity()
    assert not (root / "init.json").exists()
    assert memory_keyring.credentials
    assert all(
        password.startswith("aluclu-keyring-v1:")
        and password.isascii()
        and len(password.encode("utf-16-le")) <= 2560
        for password in memory_keyring.credentials.values()
    )


def test_keyring_transport_compacts_bounded_unicode_identity_for_windows_blob_limit(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
) -> None:
    root = tmp_path / ("é" * 120)
    ledger_id = "é" * 128

    store = KeyringRecordKeyStore(
        root,
        INTEGRITY_KEY,
        ledger_id=ledger_id,
        service="aluclu-test",
        username_prefix="owner",
        database_path=tmp_path / "données" / "mémoire.sqlite3",
    )
    store.put_pending("evt-1", b"d" * 32)

    reopened = KeyringRecordKeyStore(
        root,
        INTEGRITY_KEY,
        ledger_id=ledger_id,
        service="aluclu-test",
        username_prefix="owner",
        database_path=tmp_path / "données" / "mémoire.sqlite3",
        create=False,
    )

    assert reopened.get("evt-1") == b"d" * 32
    assert all(
        len(password.encode("utf-16-le")) <= 2560
        for password in memory_keyring.credentials.values()
    )


@pytest.mark.parametrize(
    "malformed",
    [
        "aluclu-keyring-v2:WA==",
        "aluclu-keyring-v1:!!!!",
        "aluclu-keyring-v1:WA===",
        "aluclu-keyring-v1:" + "A" * 1281,
        "aluclu-keyring-v1:şifre",
    ],
)
def test_keyring_credential_transport_rejects_noncanonical_or_oversized_values(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
    malformed: str,
) -> None:
    store = KeyringRecordKeyStore(
        tmp_path / "keys",
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        service="aluclu-test",
        username_prefix="owner",
    )
    store.put_pending("evt-1", b"d" * 32)
    event_username = next(
        username for _, username in memory_keyring.credentials if ":event:" in username
    )
    memory_keyring.credentials[("aluclu-test", event_username)] = malformed

    with pytest.raises(LedgerIntegrityError):
        store.get("evt-1")


def test_keyring_oversized_backend_identity_cannot_publish_unreadable_init_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class OversizedIdentityBackend(MemoryKeyringBackend):
        pass

    OversizedIdentityBackend.__module__ = "keyring.backends.Windows"
    OversizedIdentityBackend.__qualname__ = "b" * 70_000
    backend = OversizedIdentityBackend()
    monkeypatch.setitem(sys.modules, "keyring", MemoryKeyringModule(backend))

    with pytest.raises(LedgerCapabilityUnavailable, match="backend identity"):
        KeyringRecordKeyStore(
            tmp_path / "keys",
            INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
            service="aluclu-test",
            username_prefix="owner",
        )

    assert backend.credentials == {}
    assert list(tmp_path.iterdir()) == []


def test_keyring_store_never_writes_state_larger_than_its_read_boundary(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
) -> None:
    store = KeyringRecordKeyStore(
        tmp_path / "keys",
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        service="aluclu-test",
        username_prefix="owner",
    )
    oversized_path = tmp_path / "keys" / "oversized.json"

    with pytest.raises(LedgerIntegrityError, match="size boundary"):
        store._write_bytes(oversized_path, b"x" * (64 * 1024 + 1))

    assert not oversized_path.exists()


def test_keyring_store_keeps_dek_only_in_backend_and_hashes_namespaces(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
) -> None:
    event_id = "customer:alice"
    dek = b"d" * 32
    store = KeyringRecordKeyStore(
        tmp_path / "keys",
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        service="aluclu-test",
        username_prefix="owner",
    )

    pending = store.put_pending(event_id, dek)
    committed = store.mark_committed(event_id, "ab" * 32)

    assert pending.state is RecordKeyState.PENDING
    assert committed.state is RecordKeyState.COMMITTED
    assert store.get(event_id) == dek
    assert all(
        credential_event_id not in username
        for _, username in memory_keyring.credentials
        for credential_event_id in (event_id, "customer", "alice", LEDGER_ID, "owner")
    )
    assert all(
        username.isascii() and len(username) <= 191
        for _, username in memory_keyring.credentials
    )
    encoded_dek = base64.b64encode(dek)
    for path in tmp_path.rglob("*"):
        if path.is_file():
            persisted = path.read_bytes()
            assert dek not in persisted
            assert encoded_dek not in persisted


def test_keyring_store_rejects_chainer_backend_before_disk_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ChainerBackend(MemoryKeyringBackend):
        backends = [MemoryKeyringBackend()]

    ChainerBackend.__module__ = "keyring.backends.chainer"
    monkeypatch.setitem(sys.modules, "keyring", MemoryKeyringModule(ChainerBackend()))

    with pytest.raises(LedgerCapabilityUnavailable):
        KeyringRecordKeyStore(
            tmp_path / "keys",
            INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
            service="aluclu-test",
            username_prefix="owner",
        )

    assert list(tmp_path.iterdir()) == []


def test_keyring_store_captures_and_validates_exact_backend_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ChainerBackend(MemoryKeyringBackend):
        backends = [MemoryKeyringBackend()]

    ChainerBackend.__module__ = "keyring.backends.chainer"
    secure_backend = MemoryKeyringBackend()
    insecure_second_backend = ChainerBackend()
    keyring_module = FlappingKeyringModule(secure_backend, insecure_second_backend)
    monkeypatch.setitem(sys.modules, "keyring", keyring_module)

    store = KeyringRecordKeyStore(
        tmp_path / "keys",
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        service="aluclu-test",
        username_prefix="owner",
    )

    assert store.profile is RecordKeyStoreProfile.OS_KEYRING
    assert keyring_module.calls == 1
    assert secure_backend.credentials
    assert insecure_second_backend.credentials == {}


def test_keyring_store_reopen_fails_closed_when_backend_identity_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class AlternateMemoryKeyringBackend(MemoryKeyringBackend):
        pass

    AlternateMemoryKeyringBackend.__module__ = "keyring.backends.macOS"
    root = tmp_path / "keys"
    database_path = tmp_path / "memory.sqlite3"
    original_backend = MemoryKeyringBackend()
    monkeypatch.setitem(sys.modules, "keyring", MemoryKeyringModule(original_backend))
    store = KeyringRecordKeyStore(
        root,
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        service="aluclu-test",
        username_prefix="owner",
        database_path=database_path,
    )
    store.put_pending("evt-backend-binding", b"b" * 32)
    disk_before = {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }

    alternate_backend = AlternateMemoryKeyringBackend()
    alternate_backend.credentials = dict(original_backend.credentials)
    credentials_before = dict(alternate_backend.credentials)
    monkeypatch.setitem(sys.modules, "keyring", MemoryKeyringModule(alternate_backend))

    with pytest.raises(LedgerIntegrityError):
        KeyringRecordKeyStore(
            root,
            INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
            service="aluclu-test",
            username_prefix="owner",
            database_path=database_path,
            create=False,
        )

    assert {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    } == disk_before
    assert alternate_backend.credentials == credentials_before


def test_keyring_store_rejects_exact_captured_chainer_without_second_lookup_or_disk_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ChainerBackend(MemoryKeyringBackend):
        backends = [MemoryKeyringBackend()]

    ChainerBackend.__module__ = "keyring.backends.chainer"
    keyring_module = FlappingKeyringModule(ChainerBackend(), MemoryKeyringBackend())
    monkeypatch.setitem(sys.modules, "keyring", keyring_module)

    with pytest.raises(LedgerCapabilityUnavailable):
        KeyringRecordKeyStore(
            tmp_path / "keys",
            INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
            service="aluclu-test",
            username_prefix="owner",
        )

    assert keyring_module.calls == 1
    assert list(tmp_path.iterdir()) == []
    assert all(backend.credentials == {} for backend in keyring_module._backends)


def test_real_platform_keyring_record_store_smoke(
    tmp_path: Path,
    record_property: Callable[[str, object], None],
) -> None:
    try:
        importlib.import_module("keyring")
    except Exception as exc:
        pytest.skip(f"keyring package unavailable: {exc}")

    service = f"aluclu-smoke-{uuid.uuid4().hex}"
    username_prefix = f"owner-{uuid.uuid4().hex}"
    root = tmp_path / "keys"
    store: KeyringRecordKeyStore | None = None
    reopened: KeyringRecordKeyStore | None = None
    try:
        try:
            store = KeyringRecordKeyStore(
                root,
                INTEGRITY_KEY,
                ledger_id=f"{LEDGER_ID}-real-keyring-smoke",
                service=service,
                username_prefix=username_prefix,
                database_path=tmp_path / "memory.sqlite3",
            )
        except LedgerCapabilityUnavailable as exc:
            pytest.skip(f"real OS keyring capability unavailable: {exc}")

        record_property("keyring_backend_id", store.backend_id)
        event_id = "evt-real-smoke"
        key = b"r" * 32
        pending = store.put_pending(event_id, key)
        committed = store.mark_committed(event_id, RECORD_HASH)

        assert pending.state is RecordKeyState.PENDING
        assert committed.state is RecordKeyState.COMMITTED
        assert store.get(event_id) == key
        assert store.shred(event_id, RECORD_HASH) is True

        reopened = KeyringRecordKeyStore(
            root,
            INTEGRITY_KEY,
            ledger_id=f"{LEDGER_ID}-real-keyring-smoke",
            service=service,
            username_prefix=username_prefix,
            database_path=tmp_path / "memory.sqlite3",
            create=False,
        )
        assert reopened.get(event_id) is None
        assert reopened.is_tombstoned(event_id)
        assert reopened.tombstone_hash(event_id) == RECORD_HASH
        reopened.verify_integrity()
    finally:
        for candidate in (reopened, store):
            if candidate is not None:
                candidate._delete_password_if_present(
                    candidate._credential_username("head")
                )


def test_keyring_probe_delete_failure_leaves_only_inert_external_credential(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class DeleteFailBackend(MemoryKeyringBackend):
        def delete_password(self, service: str, username: str) -> None:
            raise RuntimeError("delete unavailable")

    DeleteFailBackend.__module__ = "keyring.backends.Windows"
    backend = DeleteFailBackend()
    monkeypatch.setitem(sys.modules, "keyring", MemoryKeyringModule(backend))

    with pytest.raises(LedgerCapabilityUnavailable):
        KeyringRecordKeyStore(
            tmp_path / "keys",
            INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
            service="aluclu-test",
            username_prefix="owner",
        )

    assert list(tmp_path.iterdir()) == []
    assert len(backend.credentials) == 1
    assert all(":probe:" in username for _, username in backend.credentials)


@pytest.mark.parametrize(
    ("service", "username_prefix", "database_name"),
    [
        ("other-service", "owner", "memory.sqlite3"),
        ("aluclu-test", "other-owner", "memory.sqlite3"),
        ("aluclu-test", "owner", "moved.sqlite3"),
    ],
)
def test_keyring_store_binding_rejects_namespace_or_path_changes(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
    service: str,
    username_prefix: str,
    database_name: str,
) -> None:
    root = tmp_path / "keys"
    original_database = tmp_path / "memory.sqlite3"
    KeyringRecordKeyStore(
        root,
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        service="aluclu-test",
        username_prefix="owner",
        database_path=original_database,
    )
    before = {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }

    with pytest.raises(LedgerIntegrityError):
        KeyringRecordKeyStore(
            root,
            INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
            service=service,
            username_prefix=username_prefix,
            database_path=tmp_path / database_name,
            create=False,
        )

    after = {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    assert after == before


def test_keyring_head_is_an_independent_rollback_witness(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
) -> None:
    root = tmp_path / "keys"
    store = KeyringRecordKeyStore(
        root,
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        service="aluclu-test",
        username_prefix="owner",
    )
    old_head = (root / "head.json").read_bytes()
    store.put_pending("evt-1", b"d" * 32)
    (root / "head.json").write_bytes(old_head)

    with pytest.raises(LedgerRollbackError):
        KeyringRecordKeyStore(
            root,
            INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
            service="aluclu-test",
            username_prefix="owner",
            create=False,
        )


def test_keyring_older_witness_cannot_follow_a_newer_disk_head(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
) -> None:
    root = tmp_path / "keys"
    store = KeyringRecordKeyStore(
        root,
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        service="aluclu-test",
        username_prefix="owner",
    )
    head_name = next(
        username
        for service, username in memory_keyring.credentials
        if service == "aluclu-test" and ":head:" in username
    )
    old_witness = memory_keyring.credentials[("aluclu-test", head_name)]
    store.put_pending("evt-1", b"d" * 32)
    memory_keyring.credentials[("aluclu-test", head_name)] = old_witness

    with pytest.raises(LedgerIntegrityError):
        KeyringRecordKeyStore(
            root,
            INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
            service="aluclu-test",
            username_prefix="owner",
            create=False,
        )


def test_keyring_expected_disk_with_desired_witness_is_always_rollback(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
) -> None:
    root = tmp_path / "keys"
    fault = ArmedFault()
    store = KeyringRecordKeyStore(
        root,
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        service="aluclu-test",
        username_prefix="owner",
        _fault_injector=fault,
    )
    fault.boundary = "after_keyring_prepare"
    with pytest.raises(SimulatedCrash):
        store.put_pending("evt-1", b"d" * 32)
    stage = store._decode_staged((root / "staged.bin").read_bytes())
    desired_head = base64.b64decode(str(stage["head_state"]), validate=True)
    store._write_head_witness(desired_head)

    with pytest.raises(LedgerRollbackError):
        KeyringRecordKeyStore(
            root,
            INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
            service="aluclu-test",
            username_prefix="owner",
            create=False,
        )


def test_missing_initial_witness_is_never_repaired_without_init_intent(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
) -> None:
    root = tmp_path / "keys"
    KeyringRecordKeyStore(
        root,
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        service="aluclu-test",
        username_prefix="owner",
    )
    head_name = next(
        username for _, username in memory_keyring.credentials if ":head:" in username
    )
    del memory_keyring.credentials[("aluclu-test", head_name)]

    with pytest.raises(LedgerIntegrityError):
        KeyringRecordKeyStore(
            root,
            INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
            service="aluclu-test",
            username_prefix="owner",
            create=True,
        )

    assert (root / "identity.json").exists()
    assert not any(":head:" in username for _, username in memory_keyring.credentials)


def test_partial_initialization_requires_create_and_valid_intent(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
) -> None:
    root = tmp_path / "keys"
    fault = ArmedFault()
    fault.boundary = "after_keyring_initialize_publish"
    with pytest.raises(SimulatedCrash):
        KeyringRecordKeyStore(
            root,
            INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
            service="aluclu-test",
            username_prefix="owner",
            _fault_injector=fault,
        )

    with pytest.raises(LedgerIntegrityError):
        KeyringRecordKeyStore(
            root,
            INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
            service="aluclu-test",
            username_prefix="owner",
            create=False,
        )
    assert (root / "init.json").exists()
    assert not any(":head:" in username for _, username in memory_keyring.credentials)

    (root / "init.json").write_bytes(b"{}")
    with pytest.raises(LedgerIntegrityError):
        KeyringRecordKeyStore(
            root,
            INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
            service="aluclu-test",
            username_prefix="owner",
            create=True,
        )
    assert (root / "init.json").read_bytes() == b"{}"
    assert not any(":head:" in username for _, username in memory_keyring.credentials)


def test_keyring_tampered_credential_fails_closed(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
) -> None:
    store = KeyringRecordKeyStore(
        tmp_path / "keys",
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        service="aluclu-test",
        username_prefix="owner",
    )
    store.put_pending("evt-1", b"d" * 32)
    event_username = next(
        username
        for service, username in memory_keyring.credentials
        if service == "aluclu-test" and ":event:" in username
    )
    memory_keyring.credentials[("aluclu-test", event_username)] = "tampered"

    with pytest.raises(LedgerIntegrityError):
        store.get("evt-1")


def test_mark_committed_validates_credential_before_journaling(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
) -> None:
    root = tmp_path / "keys"
    store = KeyringRecordKeyStore(
        root,
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        service="aluclu-test",
        username_prefix="owner",
    )
    store.put_pending("evt-1", b"d" * 32)
    head_before = (root / "head.json").read_bytes()
    event_username = next(
        username for _, username in memory_keyring.credentials if ":event:" in username
    )
    memory_keyring.credentials[("aluclu-test", event_username)] = "tampered"

    with pytest.raises(LedgerIntegrityError):
        store.mark_committed("evt-1", RECORD_HASH)

    assert (root / "head.json").read_bytes() == head_before
    assert not (root / "prepare.json").exists()
    assert not (root / "staged.bin").exists()


def test_prepared_append_without_staged_or_final_credential_fails_closed(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
) -> None:
    root = tmp_path / "keys"
    fault = ArmedFault()
    store = KeyringRecordKeyStore(
        root,
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        service="aluclu-test",
        username_prefix="owner",
        _fault_injector=fault,
    )
    fault.boundary = "after_keyring_prepare"
    with pytest.raises(SimulatedCrash):
        store.put_pending("evt-1", b"d" * 32)
    staging_username = next(
        username
        for _, username in memory_keyring.credentials
        if ":staging:" in username
    )
    del memory_keyring.credentials[("aluclu-test", staging_username)]

    with pytest.raises(LedgerIntegrityError):
        KeyringRecordKeyStore(
            root,
            INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
            service="aluclu-test",
            username_prefix="owner",
            create=False,
        )

    assert not any(":event:" in username for _, username in memory_keyring.credentials)
    assert (root / "prepare.json").exists()


def test_shred_recovery_never_recreates_deleted_credential(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
) -> None:
    root = tmp_path / "keys"
    fault = ArmedFault()
    store = KeyringRecordKeyStore(
        root,
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        service="aluclu-test",
        username_prefix="owner",
        _fault_injector=fault,
    )
    store.put_pending("evt-1", b"d" * 32)
    store.mark_committed("evt-1", RECORD_HASH)
    fault.boundary = "after_keyring_final_credential"
    with pytest.raises(SimulatedCrash):
        store.shred("evt-1", RECORD_HASH)
    assert not any(":event:" in username for _, username in memory_keyring.credentials)

    reopened = KeyringRecordKeyStore(
        root,
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        service="aluclu-test",
        username_prefix="owner",
        create=False,
    )
    assert reopened.is_tombstoned("evt-1")
    assert reopened.get("evt-1") is None
    assert not any(":event:" in username for _, username in memory_keyring.credentials)


@pytest.mark.parametrize(
    "boundary",
    [
        "after_keyring_initialize_identity",
        "after_keyring_initialize_head",
        "after_keyring_initialize_intent",
        "after_keyring_initialize_publish",
        "after_keyring_initialize_witness",
        "after_keyring_initialize_cleanup",
    ],
)
def test_keyring_initialization_recovers_at_every_durable_boundary(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
    boundary: str,
) -> None:
    root = tmp_path / "keys"
    fault = ArmedFault()
    fault.boundary = boundary

    with pytest.raises(SimulatedCrash):
        KeyringRecordKeyStore(
            root,
            INTEGRITY_KEY,
            ledger_id=LEDGER_ID,
            service="aluclu-test",
            username_prefix="owner",
            _fault_injector=fault,
        )

    reopened = KeyringRecordKeyStore(
        root,
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        service="aluclu-test",
        username_prefix="owner",
        create=True,
    )
    reopened.verify_integrity()
    assert reopened.revision == 0
    assert tuple(reopened.iter_references()) == ()
    assert not (root / "init.json").exists()
    assert not any(":probe:" in username for _, username in memory_keyring.credentials)


@pytest.mark.parametrize(
    "operation",
    ["put_pending", "mark_committed", "discard_pending", "shred"],
)
@pytest.mark.parametrize(
    "boundary",
    [
        "after_keyring_staging_credential",
        "after_keyring_staged_metadata",
        "after_keyring_prepare",
        "after_keyring_final_credential",
        "after_keyring_event_state",
        "after_keyring_disk_head",
        "after_keyring_keyring_head",
        "after_keyring_cleanup",
    ],
)
def test_keyring_operation_crashes_recover_to_exact_old_or_new_state(
    tmp_path: Path,
    memory_keyring: MemoryKeyringBackend,
    operation: str,
    boundary: str,
) -> None:
    root = tmp_path / "keys"
    fault = ArmedFault()
    store = KeyringRecordKeyStore(
        root,
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        service="aluclu-test",
        username_prefix="owner",
        _fault_injector=fault,
    )
    event_id = "evt-1"
    key = b"d" * 32
    if operation != "put_pending":
        store.put_pending(event_id, key)
    if operation == "shred":
        store.mark_committed(event_id, RECORD_HASH)

    fault.boundary = boundary
    with pytest.raises(SimulatedCrash):
        if operation == "put_pending":
            store.put_pending(event_id, key)
        elif operation == "mark_committed":
            store.mark_committed(event_id, RECORD_HASH)
        elif operation == "discard_pending":
            store.discard_pending(event_id)
        else:
            store.shred(event_id, RECORD_HASH)

    reopened = KeyringRecordKeyStore(
        root,
        INTEGRITY_KEY,
        ledger_id=LEDGER_ID,
        service="aluclu-test",
        username_prefix="owner",
        create=False,
    )
    committed = boundary not in {
        "after_keyring_staging_credential",
        "after_keyring_staged_metadata",
    }
    reference = reopened.reference(event_id)
    if operation == "put_pending":
        assert reopened.get(event_id) == (key if committed else None)
        assert (reference is not None) is committed
        if reference is not None:
            assert reference.state is RecordKeyState.PENDING
    elif operation == "mark_committed":
        assert reopened.get(event_id) == key
        assert reference is not None
        assert reference.state is (
            RecordKeyState.COMMITTED if committed else RecordKeyState.PENDING
        )
        assert reference.record_hash == (RECORD_HASH if committed else None)
    elif operation == "discard_pending":
        assert reopened.get(event_id) == (None if committed else key)
        assert (reference is None) is committed
        assert not reopened.is_tombstoned(event_id)
    else:
        assert reopened.get(event_id) == (None if committed else key)
        assert reopened.is_tombstoned(event_id) is committed
        assert reopened.tombstone_hash(event_id) == (RECORD_HASH if committed else None)
    reopened.verify_integrity()
    assert not (root / "prepare.json").exists()
    assert not (root / "staged.bin").exists()
    assert not any(
        ":staging:" in username for _, username in memory_keyring.credentials
    )
