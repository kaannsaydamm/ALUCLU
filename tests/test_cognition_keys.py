import base64
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from aluclu.cognition import (
    InputBoundaryError,
    KeyProviderUnavailable,
    LedgerIntegrityError,
    LedgerSecurityScope,
)
from aluclu.cognition import keys as keys_module
from aluclu.cognition.keys import (
    FileKeyProvider,
    FileRecordKeyStore,
    KeyringKeyProvider,
    RecordKeyState,
    StaticKeyProvider,
)


def test_static_key_provider_rejects_non_32_byte_key() -> None:
    with pytest.raises(InputBoundaryError):
        StaticKeyProvider(b"short")


def test_static_key_provider_returns_immutable_key_copy() -> None:
    source = bytearray(b"k" * 32)
    provider = StaticKeyProvider(source)
    source[:] = b"x" * 32

    assert provider.security_scope is LedgerSecurityScope.STATIC_TEST_KEY
    assert provider.get_key() == b"k" * 32
    assert type(provider.get_key()) is bytes


def test_file_key_provider_create_false_never_creates_secret(tmp_path: Path) -> None:
    path = tmp_path / "master.key"

    provider = FileKeyProvider(path, create=False)

    with pytest.raises(KeyProviderUnavailable):
        provider.get_key()
    assert not path.exists()


def test_file_key_provider_create_true_persists_exact_key(tmp_path: Path) -> None:
    path = tmp_path / "master.key"

    first = FileKeyProvider(path, create=True).get_key()
    second = FileKeyProvider(path, create=False).get_key()

    assert len(first) == 32
    assert second == first


def test_file_key_provider_posix_existing_permissive_file_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "master.key"
    path.write_bytes(b"k" * 32)
    path.chmod(0o644)
    monkeypatch.setattr(keys_module, "_POSIX_MODE_CHECKS", True, raising=False)

    with pytest.raises(KeyProviderUnavailable):
        FileKeyProvider(path, create=False).get_key()


def test_file_key_provider_posix_create_uses_exclusive_0600_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, int] = {}
    real_open = os.open
    monkeypatch.setattr(keys_module, "_POSIX_MODE_CHECKS", True, raising=False)
    monkeypatch.setattr(
        keys_module.FileKeyProvider,
        "_validate_existing_secret",
        lambda self: None,
    )

    def capture_open(path: str | bytes, flags: int, mode: int = 0o777) -> int:
        if str(path).endswith("master.key"):
            captured["flags"] = flags
            captured["mode"] = mode
        return real_open(path, flags, mode)

    monkeypatch.setattr(keys_module.os, "open", capture_open)

    FileKeyProvider(tmp_path / "master.key", create=True).get_key()

    assert captured["flags"] & os.O_CREAT
    assert captured["flags"] & os.O_EXCL
    assert captured["mode"] == 0o600


def test_file_key_provider_posix_short_write_completes_secret(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "master.key"
    real_open = os.open
    real_write = os.write
    monkeypatch.setattr(keys_module, "_POSIX_MODE_CHECKS", True, raising=False)
    monkeypatch.setattr(
        keys_module.FileKeyProvider,
        "_validate_existing_secret",
        lambda self: None,
    )

    def short_write(fd: int, data: bytes) -> int:
        return real_write(fd, data[:8])

    monkeypatch.setattr(keys_module.os, "open", real_open)
    monkeypatch.setattr(keys_module.os, "write", short_write)

    key = FileKeyProvider(path, create=True).get_key()

    assert len(key) == 32
    assert path.stat().st_size == 32


def test_file_key_provider_posix_zero_write_cleans_partial_secret(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "master.key"
    real_open = os.open
    monkeypatch.setattr(keys_module, "_POSIX_MODE_CHECKS", True, raising=False)

    def zero_write(fd: int, data: bytes) -> int:
        return 0

    monkeypatch.setattr(keys_module.os, "open", real_open)
    monkeypatch.setattr(keys_module.os, "write", zero_write)

    with pytest.raises(KeyProviderUnavailable):
        FileKeyProvider(path, create=True).get_key()
    assert not path.exists()


def test_file_key_provider_posix_write_error_cleans_partial_secret(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "master.key"
    real_open = os.open
    monkeypatch.setattr(keys_module, "_POSIX_MODE_CHECKS", True, raising=False)

    def failing_write(fd: int, data: bytes) -> int:
        raise OSError("disk full")

    monkeypatch.setattr(keys_module.os, "open", real_open)
    monkeypatch.setattr(keys_module.os, "write", failing_write)

    with pytest.raises(KeyProviderUnavailable):
        FileKeyProvider(path, create=True).get_key()
    assert not path.exists()


def test_file_key_provider_posix_fsync_error_cleans_complete_secret(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "master.key"
    monkeypatch.setattr(keys_module, "_POSIX_MODE_CHECKS", True, raising=False)

    def failing_fsync(fd: int) -> None:
        raise OSError("flush failed")

    monkeypatch.setattr(keys_module.os, "fsync", failing_fsync)

    with pytest.raises(KeyProviderUnavailable):
        FileKeyProvider(path, create=True).get_key()
    assert not path.exists()


def test_file_key_provider_rejects_path_replaced_by_symlink_after_construction(
    tmp_path: Path,
) -> None:
    path = tmp_path / "master.key"
    target = tmp_path / "target.key"
    provider = FileKeyProvider(path, create=False)
    target.write_bytes(b"k" * 32)
    try:
        path.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are unavailable on this platform")

    with pytest.raises(KeyProviderUnavailable):
        provider.get_key()


def test_keyring_provider_import_is_lazy_and_reports_missing_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "keyring", None)
    provider = KeyringKeyProvider("svc", "user")

    assert provider.security_scope is LedgerSecurityScope.OS_KEYRING
    with pytest.raises(KeyProviderUnavailable):
        provider.get_key()


def test_keyring_provider_accepts_portable_maximum_identifiers() -> None:
    provider = KeyringKeyProvider("s" * 191, "u" * 191)

    assert provider.service == "s" * 191
    assert provider.username == "u" * 191


@pytest.mark.parametrize(
    ("service", "username"),
    [
        ("", "user"),
        ("service", ""),
        ("s" * 192, "user"),
        ("service", "u" * 192),
        ("Service", "user"),
        ("service", "User"),
        ("sérvice", "user"),
        ("service", "usér"),
        ("-service", "user"),
        ("service-", "user"),
        ("service", "_user"),
        ("service", "user_"),
        ("service:name", "user"),
        ("service", "user@name"),
        ("service name", "user"),
        ("service", "user\nname"),
    ],
)
def test_keyring_provider_rejects_nonportable_identifiers_before_import(
    monkeypatch: pytest.MonkeyPatch,
    service: str,
    username: str,
) -> None:
    monkeypatch.setitem(sys.modules, "keyring", None)

    with pytest.raises(InputBoundaryError):
        KeyringKeyProvider(service, username)


def test_keyring_provider_accepts_single_and_interior_separator_components() -> None:
    provider = KeyringKeyProvider("s", "user.name_1-test")

    assert provider.service == "s"
    assert provider.username == "user.name_1-test"


def test_keyring_provider_rejects_invalid_base64(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeKeyring:
        @staticmethod
        def get_keyring() -> object:
            class SecureTestBackend:
                priority = 1

            return SecureTestBackend()

        @staticmethod
        def get_password(service: str, username: str) -> str:
            assert service == "svc"
            assert username == "user"
            return "not-base64!"

    monkeypatch.setitem(sys.modules, "keyring", FakeKeyring)

    with pytest.raises(KeyProviderUnavailable):
        KeyringKeyProvider("svc", "user").get_key()


def test_keyring_provider_rejects_priority_zero_backend_even_with_valid_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    encoded = base64.b64encode(b"k" * 32).decode("ascii")

    class FakeKeyring:
        @staticmethod
        def get_keyring() -> object:
            class Backend:
                priority = 0

            return Backend()

        @staticmethod
        def get_password(service: str, username: str) -> str:
            return encoded

    monkeypatch.setitem(sys.modules, "keyring", FakeKeyring)

    with pytest.raises(KeyProviderUnavailable):
        KeyringKeyProvider("svc", "user").get_key()


def test_keyring_provider_rejects_plaintext_backend_even_with_valid_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    encoded = base64.b64encode(b"k" * 32).decode("ascii")

    class FakeKeyring:
        @staticmethod
        def get_keyring() -> object:
            class PlaintextKeyring:
                priority = 1

            return PlaintextKeyring()

        @staticmethod
        def get_password(service: str, username: str) -> str:
            return encoded

    monkeypatch.setitem(sys.modules, "keyring", FakeKeyring)

    with pytest.raises(KeyProviderUnavailable):
        KeyringKeyProvider("svc", "user").get_key()


def test_keyring_provider_accepts_secure_fake_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    encoded = base64.b64encode(b"k" * 32).decode("ascii")

    class FakeKeyring:
        @staticmethod
        def get_keyring() -> object:
            class SecureTestBackend:
                priority = 1

            return SecureTestBackend()

        @staticmethod
        def get_password(service: str, username: str) -> str:
            return encoded

    monkeypatch.setitem(sys.modules, "keyring", FakeKeyring)

    assert KeyringKeyProvider("svc", "user").get_key() == b"k" * 32


def test_keyring_provider_accepts_chainer_with_all_secure_backends(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    encoded = base64.b64encode(b"k" * 32).decode("ascii")

    class SecureBackend:
        priority = 1

    SecureBackend.__module__ = "keyring.backends.SecretService"

    class ChainerBackend:
        priority = 10
        backends = [SecureBackend(), SecureBackend()]

    ChainerBackend.__module__ = "keyring.backends.chainer"

    class FakeKeyring:
        @staticmethod
        def get_keyring() -> object:
            return ChainerBackend()

        @staticmethod
        def get_password(service: str, username: str) -> str:
            return encoded

    monkeypatch.setitem(sys.modules, "keyring", FakeKeyring)

    assert KeyringKeyProvider("svc", "user").get_key() == b"k" * 32


def test_keyring_provider_rejects_chainer_with_mixed_insecure_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    encoded = base64.b64encode(b"k" * 32).decode("ascii")

    class SecureBackend:
        priority = 1

    SecureBackend.__module__ = "keyring.backends.SecretService"

    class PlaintextBackend:
        priority = 1

    PlaintextBackend.__module__ = "keyrings.alt.file"

    class ChainerBackend:
        priority = 10
        backends = [SecureBackend(), PlaintextBackend()]

    ChainerBackend.__module__ = "keyring.backends.chainer"

    class FakeKeyring:
        @staticmethod
        def get_keyring() -> object:
            return ChainerBackend()

        @staticmethod
        def get_password(service: str, username: str) -> str:
            return encoded

    monkeypatch.setitem(sys.modules, "keyring", FakeKeyring)

    with pytest.raises(KeyProviderUnavailable):
        KeyringKeyProvider("svc", "user").get_key()


def test_file_record_key_store_repairs_pending_only_with_exact_hash(
    tmp_path: Path,
) -> None:
    store = FileRecordKeyStore(tmp_path / "keys.json", b"m" * 32, ledger_id="ledger-1")

    pending = store.put_pending("evt_1", b"d" * 32)
    committed = store.mark_committed("evt_1", "ab" * 32)

    assert pending.state is RecordKeyState.PENDING
    assert committed.record_hash == "ab" * 32
    assert committed.state is RecordKeyState.COMMITTED
    assert store.get("evt_1") == b"d" * 32


def test_file_record_key_store_shred_removes_dek_and_keeps_tombstone(
    tmp_path: Path,
) -> None:
    store = FileRecordKeyStore(tmp_path / "keys.json", b"m" * 32, ledger_id="ledger-1")
    store.put_pending("evt_1", b"d" * 32)
    store.mark_committed("evt_1", "ab" * 32)

    assert store.shred("evt_1", "ab" * 32)

    assert store.get("evt_1") is None
    assert store.is_tombstoned("evt_1")


def test_file_record_key_store_tombstone_hash_is_exact_and_absent_is_none(
    tmp_path: Path,
) -> None:
    store = FileRecordKeyStore(tmp_path / "keys.json", b"m" * 32, ledger_id="ledger-1")
    store.put_pending("evt_1", b"d" * 32)
    store.mark_committed("evt_1", "ab" * 32)
    store.shred("evt_1", "ab" * 32)

    assert store.tombstone_hash("evt_1") == "ab" * 32
    assert store.tombstone_hash("evt_missing") is None


def test_file_record_key_store_tombstone_enumeration_is_sorted_and_snapshot_stable(
    tmp_path: Path,
) -> None:
    store = FileRecordKeyStore(tmp_path / "keys.json", b"m" * 32, ledger_id="ledger-1")
    for event_id, key, record_hash in (
        ("evt_z", b"z" * 32, "cd" * 32),
        ("evt_a", b"a" * 32, "ab" * 32),
    ):
        store.put_pending(event_id, key)
        store.mark_committed(event_id, record_hash)
        store.shred(event_id, record_hash)

    snapshot = store.iter_tombstones()

    store.put_pending("evt_m", b"m" * 32)
    store.mark_committed("evt_m", "ef" * 32)
    store.shred("evt_m", "ef" * 32)

    assert list(snapshot) == [("evt_a", "ab" * 32), ("evt_z", "cd" * 32)]
    assert list(store.iter_tombstones()) == [
        ("evt_a", "ab" * 32),
        ("evt_m", "ef" * 32),
        ("evt_z", "cd" * 32),
    ]


def test_file_record_key_store_tombstone_queries_each_load_one_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = FileRecordKeyStore(tmp_path / "keys.json", b"m" * 32, ledger_id="ledger-1")
    store.put_pending("evt_1", b"d" * 32)
    store.mark_committed("evt_1", "ab" * 32)
    store.shred("evt_1", "ab" * 32)
    original_load = store._load
    calls = 0

    def load_once() -> dict[str, object]:
        nonlocal calls
        calls += 1
        return original_load()  # type: ignore[return-value]

    monkeypatch.setattr(store, "_load", load_once)

    assert store.tombstone_hash("evt_1") == "ab" * 32
    assert calls == 1

    iterator = store.iter_tombstones()
    assert calls == 2
    assert list(iterator) == [("evt_1", "ab" * 32)]
    assert calls == 2


def test_file_record_key_store_shred_removes_dek_from_all_state_files(
    tmp_path: Path,
) -> None:
    encoded_dek = base64.b64encode(b"d" * 32)
    store = FileRecordKeyStore(tmp_path / "keys.json", b"m" * 32, ledger_id="ledger-1")
    store.put_pending("evt_1", b"d" * 32)
    store.mark_committed("evt_1", "ab" * 32)

    assert store.shred("evt_1", "ab" * 32)

    for state_file in tmp_path.glob("keys*"):
        if state_file.is_file():
            assert encoded_dek not in state_file.read_bytes()


def test_file_record_key_store_rejects_wrong_commit_hash(tmp_path: Path) -> None:
    store = FileRecordKeyStore(tmp_path / "keys.json", b"m" * 32, ledger_id="ledger-1")
    store.put_pending("evt_1", b"d" * 32)
    store.mark_committed("evt_1", "ab" * 32)

    with pytest.raises(LedgerIntegrityError):
        store.mark_committed("evt_1", "cd" * 32)


def test_file_record_key_store_keeps_committed_evidence_when_db_record_missing(
    tmp_path: Path,
) -> None:
    store = FileRecordKeyStore(tmp_path / "keys.json", b"m" * 32, ledger_id="ledger-1")
    store.put_pending("evt_1", b"d" * 32)
    store.mark_committed("evt_1", "ab" * 32)

    assert not store.discard_pending("evt_1")
    assert store.get("evt_1") == b"d" * 32


def test_file_record_key_store_discards_uncommitted_pending_key(tmp_path: Path) -> None:
    store = FileRecordKeyStore(tmp_path / "keys.json", b"m" * 32, ledger_id="ledger-1")
    store.put_pending("evt_1", b"d" * 32)

    assert store.discard_pending("evt_1")
    assert store.get("evt_1") is None
    assert store.reference("evt_1") is None


def test_file_record_key_store_detects_authenticated_state_tamper(
    tmp_path: Path,
) -> None:
    path = tmp_path / "keys.json"
    store = FileRecordKeyStore(path, b"m" * 32, ledger_id="ledger-1")
    store.put_pending("evt_1", b"d" * 32)
    manifest = sorted(tmp_path.glob("keys.*.manifest.json"))[-1]
    manifest.write_bytes(manifest.read_bytes().replace(b"ledger-1", b"ledger-2"))

    with pytest.raises(LedgerIntegrityError):
        FileRecordKeyStore(path, b"m" * 32, ledger_id="ledger-1").verify_integrity()


def test_file_record_key_store_rejects_renamed_state_copy(tmp_path: Path) -> None:
    first = tmp_path / "a.json"
    second = tmp_path / "b.json"
    store = FileRecordKeyStore(first, b"m" * 32, ledger_id="ledger-1")
    store.put_pending("evt_1", b"d" * 32)
    store.mark_committed("evt_1", "ab" * 32)
    second.write_bytes(first.read_bytes())

    with pytest.raises(LedgerIntegrityError):
        FileRecordKeyStore(second, b"m" * 32, ledger_id="ledger-1")


def test_file_record_key_store_rejects_non_json_suffix_before_artifacts(
    tmp_path: Path,
) -> None:
    path = tmp_path / "keys.txt"

    with pytest.raises(InputBoundaryError):
        FileRecordKeyStore(path, b"m" * 32, ledger_id="ledger-1")

    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("name", ["bad name.json", f"{'a' * 129}.json"])
def test_file_record_key_store_rejects_invalid_state_name_before_artifacts(
    tmp_path: Path,
    name: str,
) -> None:
    with pytest.raises(InputBoundaryError):
        FileRecordKeyStore(tmp_path / name, b"m" * 32, ledger_id="ledger-1")

    assert list(tmp_path.iterdir()) == []


def test_file_record_key_store_valid_distinct_names_coexist_and_reopen(
    tmp_path: Path,
) -> None:
    first = FileRecordKeyStore(tmp_path / "one.json", b"m" * 32, ledger_id="ledger-1")
    second = FileRecordKeyStore(tmp_path / "two.json", b"m" * 32, ledger_id="ledger-2")
    first.put_pending("evt_1", b"a" * 32)
    second.put_pending("evt_2", b"b" * 32)

    reopened_first = FileRecordKeyStore(
        tmp_path / "one.json", b"m" * 32, ledger_id="ledger-1"
    )
    reopened_second = FileRecordKeyStore(
        tmp_path / "two.json", b"m" * 32, ledger_id="ledger-2"
    )

    assert reopened_first.get("evt_1") == b"a" * 32
    assert reopened_first.get("evt_2") is None
    assert reopened_second.get("evt_2") == b"b" * 32
    assert reopened_second.get("evt_1") is None
    assert (tmp_path / "one.json.lock").exists()
    assert (tmp_path / "two.json.lock").exists()


def test_file_record_key_store_shred_reopen_prunes_after_pointer_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    encoded_dek = base64.b64encode(b"d" * 32)
    store = FileRecordKeyStore(tmp_path / "keys.json", b"m" * 32, ledger_id="ledger-1")
    store.put_pending("evt_1", b"d" * 32)
    store.mark_committed("evt_1", "ab" * 32)
    original_prune = keys_module.FileRecordKeyStore._prune_old_manifests

    def fail_prune_once(self: FileRecordKeyStore, current_generation: int) -> None:
        if self.is_tombstoned("evt_1"):
            raise OSError("prune interrupted")
        original_prune(self, current_generation)

    monkeypatch.setattr(
        keys_module.FileRecordKeyStore, "_prune_old_manifests", fail_prune_once
    )
    with pytest.raises(LedgerIntegrityError):
        store.shred("evt_1", "ab" * 32)

    monkeypatch.setattr(
        keys_module.FileRecordKeyStore,
        "_prune_old_manifests",
        original_prune,
    )
    reopened = FileRecordKeyStore(
        tmp_path / "keys.json", b"m" * 32, ledger_id="ledger-1"
    )

    assert reopened.is_tombstoned("evt_1")
    assert reopened.get("evt_1") is None
    for state_file in tmp_path.glob("keys*"):
        if state_file.is_file():
            assert encoded_dek not in state_file.read_bytes()


def test_file_record_key_store_recovery_uses_one_authenticated_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "keys.json"
    FileRecordKeyStore(path, b"m" * 32, ledger_id="ledger-1")
    original_load = keys_module.SafeStateCodec.load
    calls = 0

    def load_once(codec: object, name: str) -> object:
        nonlocal calls
        calls += 1
        if calls > 1:
            raise AssertionError("recovery reloaded a different state snapshot")
        return original_load(codec, name)  # type: ignore[arg-type]

    monkeypatch.setattr(keys_module.SafeStateCodec, "load", load_once)

    FileRecordKeyStore(path, b"m" * 32, ledger_id="ledger-1")
    assert calls == 1


def test_file_record_key_store_unknown_partial_state_fails_closed(
    tmp_path: Path,
) -> None:
    path = tmp_path / "keys.json"
    path.write_bytes(b'{"version":1}')

    with pytest.raises(LedgerIntegrityError):
        FileRecordKeyStore(path, b"m" * 32, ledger_id="ledger-1")


def test_file_record_key_store_manifest_without_pointer_fails_closed(
    tmp_path: Path,
) -> None:
    (tmp_path / "keys.00000000000000000001.manifest.json").write_bytes(b"{}")

    with pytest.raises(LedgerIntegrityError):
        FileRecordKeyStore(tmp_path / "keys.json", b"m" * 32, ledger_id="ledger-1")


def test_file_record_key_store_concurrent_first_create_is_stable(
    tmp_path: Path,
) -> None:
    path = tmp_path / "keys.json"

    def open_store() -> int:
        return FileRecordKeyStore(path, b"m" * 32, ledger_id="ledger-1").revision

    with ThreadPoolExecutor(max_workers=2) as executor:
        revisions = list(executor.map(lambda _: open_store(), range(2)))

    assert revisions == [0, 0]
    assert FileRecordKeyStore(path, b"m" * 32, ledger_id="ledger-1").revision == 0


def test_file_record_key_store_rejects_path_replaced_by_symlink(
    tmp_path: Path,
) -> None:
    path = tmp_path / "keys.json"
    target = tmp_path / "target.json"
    store = FileRecordKeyStore(path, b"m" * 32, ledger_id="ledger-1")
    target.write_bytes(path.read_bytes())
    path.unlink()
    try:
        path.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are unavailable on this platform")

    with pytest.raises(LedgerIntegrityError):
        store.verify_integrity()


def test_file_record_key_store_rejects_ledger_identity_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "keys.json"
    FileRecordKeyStore(path, b"m" * 32, ledger_id="ledger-1")

    with pytest.raises(LedgerIntegrityError):
        FileRecordKeyStore(path, b"m" * 32, ledger_id="ledger-2")


def test_file_record_key_store_returns_immutable_key_copies(tmp_path: Path) -> None:
    source = bytearray(b"d" * 32)
    store = FileRecordKeyStore(tmp_path / "keys.json", b"m" * 32, ledger_id="ledger-1")
    store.put_pending("evt_1", source)
    source[:] = b"x" * 32

    assert store.get("evt_1") == b"d" * 32
    assert type(store.get("evt_1")) is bytes
