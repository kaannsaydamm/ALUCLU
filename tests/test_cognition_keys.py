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


def test_keyring_provider_rejects_invalid_base64(monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_file_record_key_store_repairs_pending_only_with_exact_hash(tmp_path: Path) -> None:
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


def test_file_record_key_store_detects_authenticated_state_tamper(tmp_path: Path) -> None:
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


def test_file_record_key_store_unknown_partial_state_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "keys.json"
    path.write_bytes(b'{"version":1}')

    with pytest.raises(LedgerIntegrityError):
        FileRecordKeyStore(path, b"m" * 32, ledger_id="ledger-1")


def test_file_record_key_store_manifest_without_pointer_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "keys.00000000000000000001.manifest.json").write_bytes(b"{}")

    with pytest.raises(LedgerIntegrityError):
        FileRecordKeyStore(tmp_path / "keys.json", b"m" * 32, ledger_id="ledger-1")


def test_file_record_key_store_concurrent_first_create_is_stable(tmp_path: Path) -> None:
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
