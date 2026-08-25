from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import os
import secrets
import stat
import uuid
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Protocol, cast

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from .codec import (
    STATE_NAME_PATTERN,
    SafeStateCodec,
    canonical_json_bytes,
    strict_json_loads,
    validate_event_id,
)
from .contracts import (
    InputBoundaryError,
    JsonValue,
    KeyProvider,
    KeyProviderUnavailable,
    LedgerIntegrityError,
    LedgerMigrationRequired,
    LedgerSecurityScope,
    PersistenceError,
    StateIntegrityError,
    UnsafePathError,
)
from .persistence import (
    atomic_publish_path,
    atomic_write_bytes,
    exclusive_file_lock,
    resolve_ledger_path,
)

_POSIX_MODE_CHECKS = os.name != "nt"
_INSECURE_KEYRING_BACKEND_TOKENS = (
    "plaintext",
)
_DIRECTORY_STORE_VERSION = 2
_DIRECTORY_STORE_MAX_ENVELOPE_BYTES = 64 * 1024
_EMPTY_ACCUMULATOR = bytes(32)
_HEX_DIGITS = frozenset("0123456789abcdef")
_INITIALIZATION_TEMP_SUFFIX = ".init.tmp"
_ROOT_ATOMIC_TARGETS = frozenset(
    {"head.json", "identity.json", "prepare.json", "staged.bin"}
)

__all__ = [
    "DirectoryRecordKeyStore",
    "FileKeyProvider",
    "FileRecordKeyStore",
    "KeyProvider",
    "KeyringKeyProvider",
    "RecordKeyReference",
    "RecordKeyState",
    "RecordKeyStore",
    "StaticKeyProvider",
]


class StaticKeyProvider:
    def __init__(self, key: bytes | bytearray | memoryview) -> None:
        self._key = _key_bytes(key, label="key")

    @property
    def security_scope(self) -> LedgerSecurityScope:
        return LedgerSecurityScope.STATIC_TEST_KEY

    def get_key(self) -> bytes:
        return bytes(self._key)


class FileKeyProvider:
    def __init__(self, path: str | Path, *, create: bool = False) -> None:
        self._path = resolve_ledger_path(path)
        self._create = create

    @property
    def security_scope(self) -> LedgerSecurityScope:
        return LedgerSecurityScope.LOCAL_FILE_KEY

    def get_key(self) -> bytes:
        try:
            resolve_ledger_path(self._path)
        except UnsafePathError as exc:
            raise KeyProviderUnavailable("file key path is unsafe") from exc
        if not self._path.exists():
            if not self._create:
                raise KeyProviderUnavailable("file key is missing")
            self._create_secret()
        self._validate_existing_secret()
        try:
            data = self._path.read_bytes()
        except OSError as exc:
            raise KeyProviderUnavailable("file key is unavailable") from exc
        return _key_bytes(data, label="file key")

    def _create_secret(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if _POSIX_MODE_CHECKS:
            flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
            if hasattr(os, "O_BINARY"):
                flags |= os.O_BINARY
            try:
                fd = os.open(str(self._path), flags, 0o600)
            except FileExistsError:
                return
            except OSError as exc:
                raise KeyProviderUnavailable("file key cannot be created") from exc
            opened_stat = os.fstat(fd)
            failure: OSError | None = None
            try:
                _write_all(fd, secrets.token_bytes(32))
                os.fsync(fd)
            except OSError as exc:
                failure = exc
            try:
                os.close(fd)
            except OSError as exc:
                failure = failure or exc
            if failure is not None:
                _unlink_if_same_file(self._path, opened_stat)
                raise KeyProviderUnavailable("file key cannot be written") from failure
            return
        try:
            with self._path.open("xb") as handle:
                handle.write(secrets.token_bytes(32))
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError:
            return

    def _validate_existing_secret(self) -> None:
        try:
            stat_result = self._path.lstat()
        except OSError as exc:
            raise KeyProviderUnavailable("file key is unavailable") from exc
        if not stat.S_ISREG(stat_result.st_mode):
            raise KeyProviderUnavailable("file key path is not a regular file")
        if _POSIX_MODE_CHECKS and stat_result.st_mode & 0o077:
            raise KeyProviderUnavailable("file key mode is too permissive")


class KeyringKeyProvider:
    def __init__(self, service: str, username: str, *, create: bool = False) -> None:
        if not service or not username:
            raise InputBoundaryError("keyring service and username are required")
        self._service = service
        self._username = username
        self._create = create

    @property
    def security_scope(self) -> LedgerSecurityScope:
        return LedgerSecurityScope.OS_KEYRING

    @property
    def service(self) -> str:
        return self._service

    @property
    def username(self) -> str:
        return self._username

    def get_key(self) -> bytes:
        try:
            import keyring  # type: ignore[import-not-found]
        except Exception as exc:
            raise KeyProviderUnavailable("keyring backend is unavailable") from exc
        _validate_keyring_backend(keyring)
        try:
            encoded = keyring.get_password(self._service, self._username)
            if encoded is None and self._create:
                secret = base64.b64encode(secrets.token_bytes(32)).decode("ascii")
                keyring.set_password(self._service, self._username, secret)
                encoded = keyring.get_password(self._service, self._username)
        except Exception as exc:
            raise KeyProviderUnavailable("keyring backend failed") from exc
        if type(encoded) is not str or not encoded:
            raise KeyProviderUnavailable("keyring entry is missing")
        try:
            data = base64.b64decode(encoded.encode("ascii"), validate=True)
        except (UnicodeEncodeError, binascii.Error) as exc:
            raise KeyProviderUnavailable("keyring entry is not valid base64") from exc
        return _key_bytes(data, label="keyring key")


class RecordKeyState(str, Enum):
    PENDING = "pending"
    COMMITTED = "committed"


@dataclass(frozen=True, kw_only=True)
class RecordKeyReference:
    event_id: str
    reference: str
    state: RecordKeyState
    record_hash: str | None


class RecordKeyStore(Protocol):
    @property
    def ledger_id(self) -> str: ...

    @property
    def revision(self) -> int: ...

    def put_pending(self, event_id: str, key: bytes) -> RecordKeyReference: ...
    def get(self, event_id: str) -> bytes | None: ...
    def reference(self, event_id: str) -> RecordKeyReference | None: ...
    def mark_committed(self, event_id: str, record_hash: str) -> RecordKeyReference: ...
    def shred(self, event_id: str, record_hash: str) -> bool: ...
    def discard_pending(self, event_id: str) -> bool: ...
    def is_tombstoned(self, event_id: str) -> bool: ...
    def tombstone_hash(self, event_id: str) -> str | None: ...
    def iter_references(self) -> Iterator[RecordKeyReference]: ...
    def iter_tombstones(self) -> Iterator[tuple[str, str]]: ...
    def verify_integrity(self) -> None: ...


class FileRecordKeyStore:
    def __init__(
        self,
        path: str | Path,
        integrity_key: bytes,
        *,
        ledger_id: str,
        create: bool = True,
    ) -> None:
        self._path = resolve_ledger_path(path)
        _validate_json_store_path(self._path)
        self._lock_path = self._path.with_suffix(self._path.suffix + ".lock")
        self._key = _key_bytes(integrity_key, label="integrity_key")
        self._ledger_id = _validate_ledger_id(ledger_id)
        self._state_name = _state_name_for_path(self._path)
        self._codec = SafeStateCodec(self._path.parent, integrity_key=self._key)
        with exclusive_file_lock(self._lock_path):
            if not self._path.exists():
                if _has_partial_state(self._path.parent, self._state_name):
                    raise LedgerIntegrityError("record key store is partial")
                if not create:
                    raise LedgerIntegrityError("record key store is missing")
                self._save(_initial_state(self._ledger_id))
            current_generation = self._load_generation()
            self._prune_old_manifests(current_generation)

    @property
    def ledger_id(self) -> str:
        return self._ledger_id

    @property
    def revision(self) -> int:
        return int(self._load()["revision"])

    def put_pending(self, event_id: str, key: bytes | bytearray | memoryview) -> RecordKeyReference:
        safe_event_id = validate_event_id(event_id)
        safe_key = _key_bytes(key, label="record key")
        with exclusive_file_lock(self._lock_path):
            state = self._load()
            entries = cast(dict[str, JsonValue], state["entries"])
            tombstones = cast(dict[str, JsonValue], state["tombstones"])
            if safe_event_id in tombstones:
                raise LedgerIntegrityError("record key is already tombstoned")
            existing = entries.get(safe_event_id)
            if existing is not None:
                entry = _entry_dict(existing)
                if entry.get("state") != RecordKeyState.PENDING.value:
                    raise LedgerIntegrityError("committed record key already exists")
                if not hmac.compare_digest(cast(str, entry["key"]), _b64(safe_key)):
                    raise LedgerIntegrityError("pending record key does not match")
                return _reference(safe_event_id, entry)
            entries[safe_event_id] = {
                "key": _b64(safe_key),
                "record_hash": None,
                "state": RecordKeyState.PENDING.value,
            }
            _bump(state)
            self._save(state)
            return self.reference(safe_event_id) or _missing_reference()

    def get(self, event_id: str) -> bytes | None:
        safe_event_id = validate_event_id(event_id)
        entry = cast(dict[str, JsonValue], self._load()["entries"]).get(safe_event_id)
        if entry is None:
            return None
        data = base64.b64decode(cast(str, _entry_dict(entry)["key"]), validate=True)
        return bytes(data)

    def reference(self, event_id: str) -> RecordKeyReference | None:
        safe_event_id = validate_event_id(event_id)
        entry = cast(dict[str, JsonValue], self._load()["entries"]).get(safe_event_id)
        if entry is None:
            return None
        return _reference(safe_event_id, _entry_dict(entry))

    def mark_committed(self, event_id: str, record_hash: str) -> RecordKeyReference:
        safe_event_id = validate_event_id(event_id)
        safe_hash = _record_hash(record_hash)
        with exclusive_file_lock(self._lock_path):
            state = self._load()
            entry = _entry_dict(cast(dict[str, JsonValue], state["entries"]).get(safe_event_id))
            current_hash = entry.get("record_hash")
            if entry.get("state") == RecordKeyState.COMMITTED.value:
                if type(current_hash) is str and hmac.compare_digest(current_hash, safe_hash):
                    return _reference(safe_event_id, entry)
                raise LedgerIntegrityError("committed record hash mismatch")
            if entry.get("state") != RecordKeyState.PENDING.value:
                raise LedgerIntegrityError("record key state is invalid")
            entry["state"] = RecordKeyState.COMMITTED.value
            entry["record_hash"] = safe_hash
            cast(dict[str, JsonValue], state["entries"])[safe_event_id] = entry
            _bump(state)
            self._save(state)
            return _reference(safe_event_id, entry)

    def shred(self, event_id: str, record_hash: str) -> bool:
        safe_event_id = validate_event_id(event_id)
        safe_hash = _record_hash(record_hash)
        with exclusive_file_lock(self._lock_path):
            state = self._load()
            entries = cast(dict[str, JsonValue], state["entries"])
            tombstones = cast(dict[str, JsonValue], state["tombstones"])
            if safe_event_id in tombstones:
                return False
            entry = entries.get(safe_event_id)
            if entry is None:
                return False
            entry_dict = _entry_dict(entry)
            if entry_dict.get("state") != RecordKeyState.COMMITTED.value:
                raise LedgerIntegrityError("only committed record keys can be shredded")
            current_hash = cast(str, entry_dict.get("record_hash"))
            if not hmac.compare_digest(current_hash, safe_hash):
                raise LedgerIntegrityError("shred record hash mismatch")
            del entries[safe_event_id]
            tombstones[safe_event_id] = {"record_hash": safe_hash}
            _bump(state)
            self._save(state)
            return True

    def discard_pending(self, event_id: str) -> bool:
        safe_event_id = validate_event_id(event_id)
        with exclusive_file_lock(self._lock_path):
            state = self._load()
            entries = cast(dict[str, JsonValue], state["entries"])
            entry = entries.get(safe_event_id)
            if entry is None:
                return False
            entry_dict = _entry_dict(entry)
            if entry_dict.get("state") == RecordKeyState.COMMITTED.value:
                return False
            del entries[safe_event_id]
            _bump(state)
            self._save(state)
            return True

    def is_tombstoned(self, event_id: str) -> bool:
        safe_event_id = validate_event_id(event_id)
        return safe_event_id in cast(dict[str, JsonValue], self._load()["tombstones"])

    def tombstone_hash(self, event_id: str) -> str | None:
        safe_event_id = validate_event_id(event_id)
        state = self._load()
        tombstone = cast(dict[str, JsonValue], state["tombstones"]).get(safe_event_id)
        if tombstone is None:
            return None
        return _tombstone_record_hash(tombstone)

    def iter_references(self) -> Iterator[RecordKeyReference]:
        entries = cast(dict[str, JsonValue], self._load()["entries"])
        for event_id in sorted(entries):
            yield _reference(event_id, _entry_dict(entries[event_id]))

    def iter_tombstones(self) -> Iterator[tuple[str, str]]:
        state = self._load()
        tombstones = cast(dict[str, JsonValue], state["tombstones"])
        snapshot = tuple(
            (event_id, _tombstone_record_hash(tombstones[event_id]))
            for event_id in sorted(tombstones)
        )
        return iter(snapshot)

    def verify_integrity(self) -> None:
        self._load()

    def _load(self) -> dict[str, JsonValue]:
        try:
            resolve_ledger_path(self._path)
            state, metadata = self._codec.load(self._state_name)
        except (OSError, InputBoundaryError, StateIntegrityError, UnsafePathError) as exc:
            raise LedgerIntegrityError("record key store is unreadable") from exc
        try:
            self._validate_metadata(metadata)
            if type(state) is not dict:
                raise StateIntegrityError("record key store state is malformed")
            self._validate_state(state)
        except (InputBoundaryError, StateIntegrityError) as exc:
            raise LedgerIntegrityError("record key store state is invalid") from exc
        return cast(dict[str, JsonValue], state)

    def _save(self, state: dict[str, JsonValue]) -> None:
        try:
            generation = self._codec.save(self._state_name, state, self._metadata())
            self._prune_old_manifests(generation)
        except (InputBoundaryError, OSError) as exc:
            raise LedgerIntegrityError("record key store cannot be saved") from exc

    def _prune_old_manifests(self, current_generation: int) -> None:
        current_name = f"{self._state_name}.{current_generation:020d}.manifest.json"
        for manifest in self._path.parent.glob(f"{self._state_name}.*.manifest.json"):
            if manifest.name == current_name:
                continue
            manifest.unlink()

    def _load_generation(self) -> int:
        state = self._load()
        return cast(int, state["revision"]) + 1

    def _metadata(self) -> dict[str, JsonValue]:
        return {
            "ledger_id": self._ledger_id,
            "store_name": self._state_name,
            "store_path_name": self._path.name,
            "version": 1,
        }

    def _validate_metadata(self, metadata: dict[str, JsonValue]) -> None:
        if metadata != self._metadata():
            raise StateIntegrityError("record key store metadata mismatch")

    def _validate_state(self, state: dict[str, JsonValue]) -> None:
        if state.get("version") != 1 or state.get("ledger_id") != self._ledger_id:
            raise StateIntegrityError("record key store identity mismatch")
        if type(state.get("revision")) is not int or cast(int, state["revision"]) < 0:
            raise StateIntegrityError("record key store revision is invalid")
        entries = state.get("entries")
        tombstones = state.get("tombstones")
        if type(entries) is not dict or type(tombstones) is not dict:
            raise StateIntegrityError("record key store maps are malformed")
        for event_id, raw_entry in entries.items():
            validate_event_id(event_id)
            entry = _entry_dict(raw_entry)
            key = _b64_key(cast(str, entry["key"]))
            _key_bytes(key, label="record key")
            if entry.get("state") == RecordKeyState.PENDING.value:
                if entry.get("record_hash") is not None:
                    raise StateIntegrityError("pending key has record hash")
            elif entry.get("state") == RecordKeyState.COMMITTED.value:
                _record_hash(cast(str, entry.get("record_hash")))
            else:
                raise StateIntegrityError("unknown record key state")
        for event_id, raw_tombstone in tombstones.items():
            validate_event_id(event_id)
            if event_id in entries:
                raise StateIntegrityError("record key is live and tombstoned")
            if type(raw_tombstone) is not dict:
                raise StateIntegrityError("tombstone is malformed")
            _record_hash(cast(str, raw_tombstone.get("record_hash")))


@dataclass(frozen=True)
class _DirectoryHead:
    revision: int
    event_count: int
    tombstone_count: int
    accumulator: bytes
    encoded: bytes


@dataclass(frozen=True)
class _DirectoryEvent:
    event_id: str
    token: str
    state: RecordKeyState
    record_hash: str | None
    key: bytes
    revision: int
    encoded: bytes


@dataclass(frozen=True)
class _DirectoryTombstone:
    event_id: str
    token: str
    record_hash: str
    revision: int
    encoded: bytes


class DirectoryRecordKeyStore:
    """Crash-forward, HMAC-addressed per-record key directory.

    Each mutation changes one event/tombstone member and one authenticated
    head.  The head carries a keyed commutative accumulator, allowing the
    mutation cost to remain independent of lifetime history while a full
    verification can still detect every missing, extra, or rolled-back member.
    """

    def __init__(
        self,
        root: str | Path,
        integrity_key: bytes | bytearray | memoryview,
        *,
        ledger_id: str,
        create: bool = True,
        _fault_injector: Callable[[str], None] | None = None,
    ) -> None:
        self._root = resolve_ledger_path(root)
        self._lock_path = self._root.with_name(f"{self._root.name}.lock")
        self._master_key = _key_bytes(integrity_key, label="integrity_key")
        self._ledger_id = _validate_ledger_id(ledger_id)
        self._root_name = self._root.name
        self._fault_injector = _fault_injector
        self._identity_path = self._root / "identity.json"
        self._head_path = self._root / "head.json"
        self._prepare_path = self._root / "prepare.json"
        self._staged_path = self._root / "staged.bin"
        self._events_root = self._root / "events"
        self._tombstones_root = self._root / "tombstones"
        self._store_id = ""
        self._identity_key = b""
        self._auth_key = b""
        self._address_key = b""
        self._encryption_key = b""
        self._highest_revision = -1
        self._highest_head_digest: str | None = None
        self._verified_revision = -1
        self._verified_head_digest: str | None = None
        self._verified_event_digests: dict[str, str] = {}
        self._verified_tombstone_digests: dict[str, str] = {}
        self._membership_uncertain = True

        # Invalid pre-existing roots are rejected before acquiring the sidecar
        # lock, so a failed open cannot silently initialize or alter them.
        if self._root.exists():
            self._preflight_existing_root()
            self._load_identity()
        elif not create:
            raise LedgerIntegrityError("record key directory is missing")

        with exclusive_file_lock(self._lock_path):
            if not self._root.exists():
                if not create:
                    raise LedgerIntegrityError("record key directory is missing")
                self._initialize()
            else:
                self._preflight_existing_root()
                self._load_identity()
            self._cleanup_root_atomic_write_temps_locked()
            self._recover_locked()
            self._verify_integrity_locked()

    @property
    def ledger_id(self) -> str:
        return self._ledger_id

    @property
    def revision(self) -> int:
        with exclusive_file_lock(self._lock_path):
            return self._open_locked().revision

    def put_pending(
        self,
        event_id: str,
        key: bytes | bytearray | memoryview,
    ) -> RecordKeyReference:
        safe_event_id = validate_event_id(event_id)
        safe_key = _key_bytes(key, label="record key")
        with exclusive_file_lock(self._lock_path):
            head = self._open_locked()
            token = self._token(safe_event_id)
            event, tombstone = self._read_target(safe_event_id, token)
            if tombstone is not None:
                raise LedgerIntegrityError("record key is already tombstoned")
            if event is not None:
                if event.state is not RecordKeyState.PENDING:
                    raise LedgerIntegrityError("committed record key already exists")
                if not hmac.compare_digest(event.key, safe_key):
                    raise LedgerIntegrityError("pending record key does not match")
                return self._reference_for_event(event)

            new_revision = head.revision + 1
            encoded_event = self._encode_event(
                event_id=safe_event_id,
                token=token,
                state=RecordKeyState.PENDING,
                record_hash=None,
                key=safe_key,
                revision=new_revision,
            )
            self._mutate_locked(
                operation="put_pending",
                event_id=safe_event_id,
                token=token,
                head=head,
                old_event=None,
                old_tombstone=None,
                new_event=encoded_event,
                new_tombstone=None,
            )
            return RecordKeyReference(
                event_id=safe_event_id,
                reference=token,
                state=RecordKeyState.PENDING,
                record_hash=None,
            )

    def get(self, event_id: str) -> bytes | None:
        safe_event_id = validate_event_id(event_id)
        with exclusive_file_lock(self._lock_path):
            self._open_locked()
            token = self._token(safe_event_id)
            event, tombstone = self._read_target(safe_event_id, token)
            if tombstone is not None:
                return None
            return None if event is None else bytes(event.key)

    def reference(self, event_id: str) -> RecordKeyReference | None:
        safe_event_id = validate_event_id(event_id)
        with exclusive_file_lock(self._lock_path):
            self._open_locked()
            token = self._token(safe_event_id)
            event, tombstone = self._read_target(safe_event_id, token)
            if tombstone is not None or event is None:
                return None
            return self._reference_for_event(event)

    def mark_committed(self, event_id: str, record_hash: str) -> RecordKeyReference:
        safe_event_id = validate_event_id(event_id)
        safe_hash = _record_hash(record_hash)
        with exclusive_file_lock(self._lock_path):
            head = self._open_locked()
            token = self._token(safe_event_id)
            event, tombstone = self._read_target(safe_event_id, token)
            if tombstone is not None:
                raise LedgerIntegrityError("record key is already tombstoned")
            if event is None:
                raise LedgerIntegrityError("record key entry is missing")
            if event.state is RecordKeyState.COMMITTED:
                if event.record_hash is not None and hmac.compare_digest(
                    event.record_hash,
                    safe_hash,
                ):
                    return self._reference_for_event(event)
                raise LedgerIntegrityError("committed record hash mismatch")

            encoded_event = self._encode_event(
                event_id=safe_event_id,
                token=token,
                state=RecordKeyState.COMMITTED,
                record_hash=safe_hash,
                key=event.key,
                revision=head.revision + 1,
            )
            self._mutate_locked(
                operation="mark_committed",
                event_id=safe_event_id,
                token=token,
                head=head,
                old_event=event.encoded,
                old_tombstone=None,
                new_event=encoded_event,
                new_tombstone=None,
            )
            return RecordKeyReference(
                event_id=safe_event_id,
                reference=token,
                state=RecordKeyState.COMMITTED,
                record_hash=safe_hash,
            )

    def shred(self, event_id: str, record_hash: str) -> bool:
        safe_event_id = validate_event_id(event_id)
        safe_hash = _record_hash(record_hash)
        with exclusive_file_lock(self._lock_path):
            head = self._open_locked()
            token = self._token(safe_event_id)
            event, tombstone = self._read_target(safe_event_id, token)
            if tombstone is not None:
                if not hmac.compare_digest(tombstone.record_hash, safe_hash):
                    raise LedgerIntegrityError("tombstone record hash mismatch")
                return False
            if event is None:
                return False
            if event.state is not RecordKeyState.COMMITTED:
                raise LedgerIntegrityError("only committed record keys can be shredded")
            if event.record_hash is None or not hmac.compare_digest(
                event.record_hash,
                safe_hash,
            ):
                raise LedgerIntegrityError("shred record hash mismatch")

            encoded_tombstone = self._encode_tombstone(
                event_id=safe_event_id,
                token=token,
                record_hash=safe_hash,
                revision=head.revision + 1,
            )
            self._mutate_locked(
                operation="shred",
                event_id=safe_event_id,
                token=token,
                head=head,
                old_event=event.encoded,
                old_tombstone=None,
                new_event=None,
                new_tombstone=encoded_tombstone,
            )
            return True

    def discard_pending(self, event_id: str) -> bool:
        safe_event_id = validate_event_id(event_id)
        with exclusive_file_lock(self._lock_path):
            head = self._open_locked()
            token = self._token(safe_event_id)
            event, tombstone = self._read_target(safe_event_id, token)
            if tombstone is not None or event is None:
                return False
            if event.state is RecordKeyState.COMMITTED:
                return False
            self._mutate_locked(
                operation="discard_pending",
                event_id=safe_event_id,
                token=token,
                head=head,
                old_event=event.encoded,
                old_tombstone=None,
                new_event=None,
                new_tombstone=None,
            )
            return True

    def is_tombstoned(self, event_id: str) -> bool:
        safe_event_id = validate_event_id(event_id)
        with exclusive_file_lock(self._lock_path):
            self._open_locked()
            token = self._token(safe_event_id)
            _, tombstone = self._read_target(safe_event_id, token)
            return tombstone is not None

    def tombstone_hash(self, event_id: str) -> str | None:
        safe_event_id = validate_event_id(event_id)
        with exclusive_file_lock(self._lock_path):
            self._open_locked()
            token = self._token(safe_event_id)
            _, tombstone = self._read_target(safe_event_id, token)
            return None if tombstone is None else tombstone.record_hash

    def iter_references(self) -> Iterator[RecordKeyReference]:
        with exclusive_file_lock(self._lock_path):
            self._open_locked()
            events, _ = self._verify_integrity_locked()
            snapshot = tuple(
                self._reference_for_event(event)
                for event in sorted(events.values(), key=lambda item: item.event_id)
            )
        return iter(snapshot)

    def iter_tombstones(self) -> Iterator[tuple[str, str]]:
        with exclusive_file_lock(self._lock_path):
            self._open_locked()
            _, tombstones = self._verify_integrity_locked()
            snapshot = tuple(
                (item.event_id, item.record_hash)
                for item in sorted(tombstones.values(), key=lambda item: item.event_id)
            )
        return iter(snapshot)

    def verify_integrity(self) -> None:
        with exclusive_file_lock(self._lock_path):
            self._open_locked()
            self._verify_integrity_locked()

    def _initialize(self) -> None:
        self._cleanup_initialization_directories_locked()
        staging = self._root.parent / (
            f".{self._root.name}.{os.getpid()}.{uuid.uuid4().hex}"
            f"{_INITIALIZATION_TEMP_SUFFIX}"
        )
        try:
            staging.mkdir(parents=False, exist_ok=False)
            (staging / "events").mkdir()
            (staging / "tombstones").mkdir()
        except OSError as exc:
            raise LedgerIntegrityError("record key directory cannot be created") from exc
        try:
            self._set_identity(secrets.token_hex(32))
            identity = self._identity_body()
            self._write_authenticated(staging / "identity.json", identity, self._identity_key)
            self._inject("after_directory_initialize_identity")
            initial_head = self._head_body(
                revision=0,
                event_count=0,
                tombstone_count=0,
                accumulator=_EMPTY_ACCUMULATOR,
            )
            self._write_authenticated(staging / "head.json", initial_head, self._auth_key)
            self._inject("after_directory_initialize_head")
            _fsync_directory(staging)
            self._publish_initialization_directory(staging)
            self._inject("after_directory_initialize_publish")
        finally:
            if staging.exists():
                self._remove_initialization_directory(staging)

    def _preflight_existing_root(self) -> None:
        resolve_ledger_path(self._root)
        if not self._root.is_dir():
            raise LedgerMigrationRequired("record key directory path is not a directory")
        if not self._identity_path.exists() or not self._head_path.exists():
            raise LedgerMigrationRequired("record key directory identity is missing")

    def _open_locked(self) -> _DirectoryHead:
        self._validate_root_locked()
        self._load_identity()
        self._cleanup_root_atomic_write_temps_locked()
        self._recover_locked()
        head = self._read_head()
        head_digest = _sha256_hex(head.encoded)
        if (
            self._membership_uncertain
            or self._verified_revision != head.revision
            or self._verified_head_digest is None
            or not hmac.compare_digest(self._verified_head_digest, head_digest)
        ):
            self._verify_integrity_locked()
            head = self._read_head()
        return head

    def _validate_root_locked(self) -> None:
        resolved = resolve_ledger_path(self._root)
        if os.path.normcase(str(resolved)) != os.path.normcase(str(self._root)):
            raise UnsafePathError("record key directory path changed")
        if not self._root.is_dir():
            raise LedgerIntegrityError("record key directory is unavailable")

    def _cleanup_initialization_directories_locked(self) -> None:
        try:
            candidates = tuple(self._root.parent.iterdir())
        except OSError as exc:
            raise LedgerIntegrityError("record key directory parent is unreadable") from exc
        for candidate in sorted(candidates, key=lambda path: path.name):
            if _is_initialization_temp_name(candidate.name, self._root.name):
                self._remove_initialization_directory(candidate)

    def _remove_initialization_directory(self, path: Path) -> None:
        try:
            resolved = resolve_ledger_path(path)
        except UnsafePathError as exc:
            raise LedgerIntegrityError(
                "record key initialization directory is unsafe"
            ) from exc
        if (
            os.path.normcase(str(resolved.parent))
            != os.path.normcase(str(self._root.parent))
            or not _is_initialization_temp_name(resolved.name, self._root.name)
        ):
            raise LedgerIntegrityError("record key initialization directory is invalid")
        try:
            root_stat = resolved.lstat()
            entries = tuple(resolved.iterdir())
        except OSError as exc:
            raise LedgerIntegrityError(
                "record key initialization directory is unreadable"
            ) from exc
        if not stat.S_ISDIR(root_stat.st_mode):
            raise LedgerIntegrityError("record key initialization path is not a directory")

        files: list[Path] = []
        directories: list[Path] = []
        for entry in entries:
            try:
                resolve_ledger_path(entry)
                entry_stat = entry.lstat()
            except (OSError, UnsafePathError) as exc:
                raise LedgerIntegrityError(
                    "record key initialization state is unsafe"
                ) from exc
            if entry.name in {"events", "tombstones"}:
                if not stat.S_ISDIR(entry_stat.st_mode):
                    raise LedgerIntegrityError(
                        "record key initialization fanout is malformed"
                    )
                try:
                    if any(entry.iterdir()):
                        raise LedgerIntegrityError(
                            "record key initialization fanout is not empty"
                        )
                except OSError as exc:
                    raise LedgerIntegrityError(
                        "record key initialization fanout is unreadable"
                    ) from exc
                directories.append(entry)
                continue

            atomic_target = _atomic_temp_target(entry.name)
            if entry.name not in {"identity.json", "head.json"} and atomic_target not in {
                "identity.json",
                "head.json",
            }:
                raise LedgerIntegrityError("record key initialization layout is invalid")
            _validate_cleanup_file(entry_stat)
            files.append(entry)

        try:
            for entry in files:
                entry.unlink()
            for entry in directories:
                entry.rmdir()
            resolved.rmdir()
        except OSError as exc:
            raise LedgerIntegrityError(
                "record key initialization directory cannot be cleaned"
            ) from exc
        _fsync_directory(self._root.parent)

    def _publish_initialization_directory(self, staging: Path) -> None:
        try:
            resolved_staging = resolve_ledger_path(staging)
            resolved_root = resolve_ledger_path(self._root)
        except UnsafePathError as exc:
            raise LedgerIntegrityError(
                "record key initialization directory is unsafe"
            ) from exc
        if (
            os.path.normcase(str(resolved_staging.parent))
            != os.path.normcase(str(self._root.parent))
            or not _is_initialization_temp_name(resolved_staging.name, self._root.name)
            or resolved_root.exists()
        ):
            raise LedgerIntegrityError("record key initialization publish is invalid")
        try:
            atomic_publish_path(resolved_staging, resolved_root)
        except (OSError, PersistenceError) as exc:
            raise LedgerIntegrityError(
                "record key initialization directory cannot be published"
            ) from exc
        _fsync_directory(self._root.parent)

    def _cleanup_root_atomic_write_temps_locked(self) -> None:
        try:
            entries = tuple(self._root.iterdir())
        except OSError as exc:
            raise LedgerIntegrityError("record key directory is unreadable") from exc
        allowed = {
            "events",
            "head.json",
            "identity.json",
            "prepare.json",
            "staged.bin",
            "tombstones",
        }
        temps: list[Path] = []
        for entry in entries:
            if entry.name in allowed:
                continue
            if _atomic_temp_target(entry.name) not in _ROOT_ATOMIC_TARGETS:
                raise LedgerIntegrityError("record key directory layout is invalid")
            try:
                entry_stat = entry.lstat()
            except OSError as exc:
                raise LedgerIntegrityError(
                    "record key temporary state is unavailable"
                ) from exc
            _validate_cleanup_file(entry_stat)
            temps.append(entry)
        for temp in temps:
            self._remove_file(temp)

    def _cleanup_staged_target_atomic_write_temps_locked(
        self,
        stage_body: Mapping[str, JsonValue],
    ) -> None:
        token = cast(str, stage_body["token"])
        temps: list[Path] = []
        for target in (self._event_path(token), self._tombstone_path(token)):
            if not target.parent.exists():
                continue
            try:
                resolve_ledger_path(target.parent)
                if not target.parent.is_dir():
                    raise LedgerIntegrityError(
                        "record key fanout path is not a directory"
                    )
                entries = tuple(target.parent.iterdir())
            except OSError as exc:
                raise LedgerIntegrityError("record key fanout is unreadable") from exc
            for entry in entries:
                if _atomic_temp_target(entry.name) != target.name:
                    continue
                try:
                    entry_stat = entry.lstat()
                except OSError as exc:
                    raise LedgerIntegrityError(
                        "record key temporary state is unavailable"
                    ) from exc
                _validate_cleanup_file(entry_stat)
                temps.append(entry)
        for temp in temps:
            self._remove_file(temp)

    def _set_identity(self, store_id: str) -> None:
        _validate_store_id(store_id)
        keys = self._derive_identity_keys(store_id)
        self._store_id = store_id
        (
            self._identity_key,
            self._auth_key,
            self._address_key,
            self._encryption_key,
        ) = keys

    def _derive_identity_keys(self, store_id: str) -> tuple[bytes, bytes, bytes, bytes]:
        salt = canonical_json_bytes(
            {
                "ledger_id": self._ledger_id,
                "root_name": self._root_name,
                "store_id": store_id,
                "version": _DIRECTORY_STORE_VERSION,
            }
        )
        return (
            _derive_store_key(
                self._master_key,
                salt,
                b"aluclu/v2/record-key-store/identity",
            ),
            _derive_store_key(
                self._master_key,
                salt,
                b"aluclu/v2/record-key-store/authentication",
            ),
            _derive_store_key(
                self._master_key,
                salt,
                b"aluclu/v2/record-key-store/addressing",
            ),
            _derive_store_key(
                self._master_key,
                salt,
                b"aluclu/v2/record-key-store/encryption",
            ),
        )

    def _load_identity(self) -> None:
        encoded = _read_regular_file(self._identity_path)
        body, supplied_mac = _decode_canonical_envelope(encoded, label="store identity")
        if body.get("version") != _DIRECTORY_STORE_VERSION:
            raise LedgerMigrationRequired("record key directory version is unsupported")
        _require_exact_keys(
            body,
            {"kind", "ledger_id", "root_name", "store_id", "version"},
            label="store identity",
        )
        if body.get("kind") != "identity":
            raise LedgerMigrationRequired("record key directory identity is unsupported")
        if body.get("ledger_id") != self._ledger_id or body.get("root_name") != self._root_name:
            raise LedgerIntegrityError("record key directory identity mismatch")
        store_id = body.get("store_id")
        if type(store_id) is not str:
            raise LedgerIntegrityError("record key directory store ID is malformed")
        _validate_store_id(store_id)
        previous_store_id = self._store_id
        candidate_keys = self._derive_identity_keys(store_id)
        _verify_envelope_mac(body, supplied_mac, candidate_keys[0], label="store identity")
        if previous_store_id and not hmac.compare_digest(previous_store_id, store_id):
            raise LedgerIntegrityError("record key directory store ID changed")
        self._store_id = store_id
        (
            self._identity_key,
            self._auth_key,
            self._address_key,
            self._encryption_key,
        ) = candidate_keys

    def _identity_body(self) -> dict[str, JsonValue]:
        return {
            "kind": "identity",
            "ledger_id": self._ledger_id,
            "root_name": self._root_name,
            "store_id": self._store_id,
            "version": _DIRECTORY_STORE_VERSION,
        }

    def _common_body(self, kind: str) -> dict[str, JsonValue]:
        return {
            "kind": kind,
            "ledger_id": self._ledger_id,
            "root_name": self._root_name,
            "store_id": self._store_id,
            "version": _DIRECTORY_STORE_VERSION,
        }

    def _validate_common_body(self, body: Mapping[str, JsonValue], *, kind: str) -> None:
        if (
            body.get("version") != _DIRECTORY_STORE_VERSION
            or body.get("kind") != kind
            or body.get("ledger_id") != self._ledger_id
            or body.get("root_name") != self._root_name
            or body.get("store_id") != self._store_id
        ):
            raise LedgerIntegrityError(f"record key {kind} identity mismatch")

    def _token(self, event_id: str) -> str:
        return hmac.new(self._address_key, event_id.encode("ascii"), hashlib.sha256).hexdigest()

    def _event_path(self, token: str) -> Path:
        _validate_token(token)
        return self._events_root / token[:2] / f"{token}.json"

    def _tombstone_path(self, token: str) -> Path:
        _validate_token(token)
        return self._tombstones_root / token[:2] / f"{token}.json"

    def _read_head(self) -> _DirectoryHead:
        encoded = _read_regular_file(self._head_path)
        body = _decode_authenticated_envelope(encoded, self._auth_key, label="store head")
        _require_exact_keys(
            body,
            {
                "accumulator",
                "event_count",
                "kind",
                "ledger_id",
                "revision",
                "root_name",
                "store_id",
                "tombstone_count",
                "version",
            },
            label="store head",
        )
        self._validate_common_body(body, kind="head")
        revision = _nonnegative_int(body.get("revision"), label="store revision")
        event_count = _nonnegative_int(body.get("event_count"), label="event count")
        tombstone_count = _nonnegative_int(
            body.get("tombstone_count"),
            label="tombstone count",
        )
        accumulator = _hex_bytes(body.get("accumulator"), label="state accumulator")
        head_digest = _sha256_hex(encoded)
        if revision < self._highest_revision:
            raise LedgerIntegrityError("record key directory head rolled back")
        if (
            revision == self._highest_revision
            and self._highest_head_digest is not None
            and not hmac.compare_digest(self._highest_head_digest, head_digest)
        ):
            raise LedgerIntegrityError("record key directory head forked at one revision")
        self._highest_revision = revision
        self._highest_head_digest = head_digest
        return _DirectoryHead(
            revision=revision,
            event_count=event_count,
            tombstone_count=tombstone_count,
            accumulator=accumulator,
            encoded=encoded,
        )

    def _head_body(
        self,
        *,
        revision: int,
        event_count: int,
        tombstone_count: int,
        accumulator: bytes,
    ) -> dict[str, JsonValue]:
        body = self._common_body("head")
        body.update(
            {
                "accumulator": accumulator.hex(),
                "event_count": event_count,
                "revision": revision,
                "tombstone_count": tombstone_count,
            }
        )
        return body

    def _encode_event(
        self,
        *,
        event_id: str,
        token: str,
        state: RecordKeyState,
        record_hash: str | None,
        key: bytes,
        revision: int,
    ) -> bytes:
        metadata = self._common_body("event")
        metadata.update(
            {
                "event_id": event_id,
                "record_hash": record_hash,
                "revision": revision,
                "state": state.value,
                "token": token,
            }
        )
        nonce = secrets.token_bytes(12)
        wrapped_key = AESGCM(self._encryption_key).encrypt(
            nonce,
            key,
            self._event_aad(metadata),
        )
        body = dict(metadata)
        body["nonce"] = _b64(nonce)
        body["wrapped_key"] = _b64(wrapped_key)
        return _encode_authenticated_envelope(body, self._auth_key)

    def _decode_event(self, encoded: bytes, *, expected_token: str) -> _DirectoryEvent:
        body = _decode_authenticated_envelope(encoded, self._auth_key, label="event key")
        _require_exact_keys(
            body,
            {
                "event_id",
                "kind",
                "ledger_id",
                "nonce",
                "record_hash",
                "revision",
                "root_name",
                "state",
                "store_id",
                "token",
                "version",
                "wrapped_key",
            },
            label="event key",
        )
        self._validate_common_body(body, kind="event")
        event_id = validate_event_id(_required_str(body.get("event_id"), label="event ID"))
        token = _required_str(body.get("token"), label="event token")
        _validate_token(token)
        if not hmac.compare_digest(token, expected_token) or not hmac.compare_digest(
            token,
            self._token(event_id),
        ):
            raise LedgerIntegrityError("event key address mismatch")
        try:
            state = RecordKeyState(_required_str(body.get("state"), label="record key state"))
        except ValueError as exc:
            raise LedgerIntegrityError("record key state is invalid") from exc
        raw_hash = body.get("record_hash")
        if state is RecordKeyState.PENDING:
            if raw_hash is not None:
                raise LedgerIntegrityError("pending record key has a record hash")
            record_hash = None
        else:
            record_hash = _record_hash(cast(str, raw_hash))
        revision = _positive_int(body.get("revision"), label="event revision")
        nonce = _decode_b64_bytes(body.get("nonce"), expected_length=12, label="event nonce")
        wrapped = _decode_b64_bytes(
            body.get("wrapped_key"),
            expected_length=48,
            label="wrapped record key",
        )
        metadata = {key: value for key, value in body.items() if key not in {"nonce", "wrapped_key"}}
        try:
            key = AESGCM(self._encryption_key).decrypt(
                nonce,
                wrapped,
                self._event_aad(cast(dict[str, JsonValue], metadata)),
            )
        except InvalidTag as exc:
            raise LedgerIntegrityError("wrapped record key authentication failed") from exc
        _key_bytes(key, label="record key")
        return _DirectoryEvent(
            event_id=event_id,
            token=token,
            state=state,
            record_hash=record_hash,
            key=key,
            revision=revision,
            encoded=encoded,
        )

    def _event_aad(self, metadata: Mapping[str, JsonValue]) -> bytes:
        return canonical_json_bytes(
            {
                "metadata": dict(metadata),
                "operation": "wrap_record_key",
            }
        )

    def _encode_tombstone(
        self,
        *,
        event_id: str,
        token: str,
        record_hash: str,
        revision: int,
    ) -> bytes:
        body = self._common_body("tombstone")
        body.update(
            {
                "event_id": event_id,
                "record_hash": record_hash,
                "revision": revision,
                "token": token,
            }
        )
        return _encode_authenticated_envelope(body, self._auth_key)

    def _decode_tombstone(
        self,
        encoded: bytes,
        *,
        expected_token: str,
    ) -> _DirectoryTombstone:
        body = _decode_authenticated_envelope(encoded, self._auth_key, label="tombstone")
        _require_exact_keys(
            body,
            {
                "event_id",
                "kind",
                "ledger_id",
                "record_hash",
                "revision",
                "root_name",
                "store_id",
                "token",
                "version",
            },
            label="tombstone",
        )
        self._validate_common_body(body, kind="tombstone")
        event_id = validate_event_id(_required_str(body.get("event_id"), label="event ID"))
        token = _required_str(body.get("token"), label="event token")
        _validate_token(token)
        if not hmac.compare_digest(token, expected_token) or not hmac.compare_digest(
            token,
            self._token(event_id),
        ):
            raise LedgerIntegrityError("tombstone address mismatch")
        return _DirectoryTombstone(
            event_id=event_id,
            token=token,
            record_hash=_record_hash(cast(str, body.get("record_hash"))),
            revision=_positive_int(body.get("revision"), label="tombstone revision"),
            encoded=encoded,
        )

    def _read_target(
        self,
        event_id: str,
        token: str,
    ) -> tuple[_DirectoryEvent | None, _DirectoryTombstone | None]:
        event_bytes = _read_optional_regular_file(self._event_path(token))
        tombstone_bytes = _read_optional_regular_file(self._tombstone_path(token))
        self._verify_target_membership(token, event_bytes, tombstone_bytes)
        if event_bytes is not None and tombstone_bytes is not None:
            raise LedgerIntegrityError("record key is live and tombstoned")
        event = (
            None
            if event_bytes is None
            else self._decode_event(event_bytes, expected_token=token)
        )
        tombstone = (
            None
            if tombstone_bytes is None
            else self._decode_tombstone(tombstone_bytes, expected_token=token)
        )
        if event is not None and event.event_id != event_id:
            raise LedgerIntegrityError("record key event ID mismatch")
        if tombstone is not None and tombstone.event_id != event_id:
            raise LedgerIntegrityError("tombstone event ID mismatch")
        return event, tombstone

    def _verify_target_membership(
        self,
        token: str,
        event_bytes: bytes | None,
        tombstone_bytes: bytes | None,
    ) -> None:
        if self._membership_uncertain or self._verified_revision < 0:
            raise LedgerIntegrityError("record key membership snapshot is unavailable")
        expected_event = self._verified_event_digests.get(token)
        expected_tombstone = self._verified_tombstone_digests.get(token)
        if not _optional_digest_matches(_optional_digest(event_bytes), expected_event):
            raise LedgerIntegrityError("record key event membership changed unexpectedly")
        if not _optional_digest_matches(
            _optional_digest(tombstone_bytes),
            expected_tombstone,
        ):
            raise LedgerIntegrityError("record key tombstone membership changed unexpectedly")

    def _reference_for_event(self, event: _DirectoryEvent) -> RecordKeyReference:
        return RecordKeyReference(
            event_id=event.event_id,
            reference=event.token,
            state=event.state,
            record_hash=event.record_hash,
        )

    def _mutate_locked(
        self,
        *,
        operation: str,
        event_id: str,
        token: str,
        head: _DirectoryHead,
        old_event: bytes | None,
        old_tombstone: bytes | None,
        new_event: bytes | None,
        new_tombstone: bytes | None,
    ) -> None:
        new_head = self._next_head(
            head,
            token=token,
            old_event=old_event,
            old_tombstone=old_tombstone,
            new_event=new_event,
            new_tombstone=new_tombstone,
        )
        stage_body = self._common_body("staged")
        stage_body.update(
            {
                "event_id": event_id,
                "event_state": _optional_b64(new_event),
                "expected_event_digest": _optional_digest(old_event),
                "expected_head_digest": _sha256_hex(head.encoded),
                "expected_revision": head.revision,
                "expected_tombstone_digest": _optional_digest(old_tombstone),
                "head_state": _b64(new_head.encoded),
                "new_revision": new_head.revision,
                "operation": operation,
                "token": token,
                "tombstone_state": _optional_b64(new_tombstone),
            }
        )
        staged = _encode_authenticated_envelope(stage_body, self._auth_key)
        prepare_body = self._common_body("prepare")
        prepare_body.update(
            {
                "event_digest": _optional_digest(new_event),
                "event_id": event_id,
                "expected_head_digest": _sha256_hex(head.encoded),
                "expected_revision": head.revision,
                "head_digest": _sha256_hex(new_head.encoded),
                "new_revision": new_head.revision,
                "operation": operation,
                "staged_digest": _sha256_hex(staged),
                "token": token,
                "tombstone_digest": _optional_digest(new_tombstone),
            }
        )
        prepare = _encode_authenticated_envelope(prepare_body, self._auth_key)

        self._membership_uncertain = True
        self._write_bytes(self._staged_path, staged)
        self._inject("after_directory_staged")
        self._write_bytes(self._prepare_path, prepare)
        self._inject("after_directory_prepare")
        self._apply_staged_target(stage_body, allow_expected=True)
        self._inject("after_directory_event_state")
        self._write_bytes(self._head_path, new_head.encoded)
        self._highest_revision = new_head.revision
        self._highest_head_digest = _sha256_hex(new_head.encoded)
        self._inject("after_directory_head")
        self._cleanup_mutation_files()
        self._record_verified_mutation(
            token=token,
            new_event=new_event,
            new_tombstone=new_tombstone,
            new_head=new_head,
        )
        self._inject("after_directory_cleanup")

    def _next_head(
        self,
        head: _DirectoryHead,
        *,
        token: str,
        old_event: bytes | None,
        old_tombstone: bytes | None,
        new_event: bytes | None,
        new_tombstone: bytes | None,
    ) -> _DirectoryHead:
        accumulator = bytearray(head.accumulator)
        for kind, encoded in (
            ("event", old_event),
            ("tombstone", old_tombstone),
            ("event", new_event),
            ("tombstone", new_tombstone),
        ):
            if encoded is not None:
                _xor_into(accumulator, self._member_digest(kind, token, encoded))
        event_count = head.event_count - int(old_event is not None) + int(new_event is not None)
        tombstone_count = (
            head.tombstone_count
            - int(old_tombstone is not None)
            + int(new_tombstone is not None)
        )
        if event_count < 0 or tombstone_count < 0:
            raise LedgerIntegrityError("record key directory counts are inconsistent")
        body = self._head_body(
            revision=head.revision + 1,
            event_count=event_count,
            tombstone_count=tombstone_count,
            accumulator=bytes(accumulator),
        )
        encoded = _encode_authenticated_envelope(body, self._auth_key)
        return _DirectoryHead(
            revision=head.revision + 1,
            event_count=event_count,
            tombstone_count=tombstone_count,
            accumulator=bytes(accumulator),
            encoded=encoded,
        )

    def _member_digest(self, kind: str, token: str, encoded: bytes) -> bytes:
        message = b"\0".join(
            (
                b"aluclu/v2/record-key-store/member",
                kind.encode("ascii"),
                token.encode("ascii"),
                hashlib.sha256(encoded).digest(),
            )
        )
        return hmac.new(self._auth_key, message, hashlib.sha256).digest()

    def _record_verified_mutation(
        self,
        *,
        token: str,
        new_event: bytes | None,
        new_tombstone: bytes | None,
        new_head: _DirectoryHead,
    ) -> None:
        if new_event is None:
            self._verified_event_digests.pop(token, None)
        else:
            self._verified_event_digests[token] = _sha256_hex(new_event)
        if new_tombstone is None:
            self._verified_tombstone_digests.pop(token, None)
        else:
            self._verified_tombstone_digests[token] = _sha256_hex(new_tombstone)
        self._verified_revision = new_head.revision
        self._verified_head_digest = _sha256_hex(new_head.encoded)
        self._membership_uncertain = False

    def _recover_locked(self) -> None:
        staged = _read_optional_regular_file(self._staged_path)
        prepare = _read_optional_regular_file(self._prepare_path)
        if staged is not None or prepare is not None:
            self._membership_uncertain = True
        if prepare is not None and staged is None:
            raise LedgerIntegrityError("record key prepare is missing staged state")
        if staged is None:
            return
        stage_body = self._decode_staged(staged)
        if prepare is None:
            self._recover_orphan_staged(stage_body)
            return
        prepare_body = self._decode_prepare(prepare)
        self._validate_prepare_pair(staged, stage_body, prepare_body)
        self._forward_recover(stage_body)

    def _recover_orphan_staged(self, stage_body: dict[str, JsonValue]) -> None:
        current_head = self._read_head()
        current_digest = _sha256_hex(current_head.encoded)
        expected_digest = cast(str, stage_body["expected_head_digest"])
        desired_head = _decode_b64_bytes(
            stage_body.get("head_state"),
            expected_length=None,
            label="staged head",
        )
        if hmac.compare_digest(current_digest, expected_digest):
            self._validate_expected_targets(stage_body)
            self._remove_file(self._staged_path)
            _fsync_directory(self._root)
            return
        if hmac.compare_digest(current_digest, _sha256_hex(desired_head)):
            self._apply_staged_target(stage_body, allow_expected=False)
            self._remove_file(self._staged_path)
            _fsync_directory(self._root)
            return
        raise LedgerIntegrityError("orphan staged state does not match the store head")

    def _validate_expected_targets(self, stage_body: Mapping[str, JsonValue]) -> None:
        token = cast(str, stage_body["token"])
        expected = (
            (
                self._event_path(token),
                _digest_or_none(
                    stage_body.get("expected_event_digest"),
                    label="expected event digest",
                ),
            ),
            (
                self._tombstone_path(token),
                _digest_or_none(
                    stage_body.get("expected_tombstone_digest"),
                    label="expected tombstone digest",
                ),
            ),
        )
        for path, expected_digest in expected:
            if not _optional_digest_matches(
                _optional_digest(_read_optional_regular_file(path)),
                expected_digest,
            ):
                raise LedgerIntegrityError("orphan staged target changed unexpectedly")

    def _forward_recover(self, stage_body: dict[str, JsonValue]) -> None:
        current_head = self._read_head()
        current_digest = _sha256_hex(current_head.encoded)
        expected_digest = cast(str, stage_body["expected_head_digest"])
        desired_head = _decode_b64_bytes(
            stage_body.get("head_state"),
            expected_length=None,
            label="staged head",
        )
        desired_digest = _sha256_hex(desired_head)
        current_is_expected = hmac.compare_digest(current_digest, expected_digest)
        current_is_desired = hmac.compare_digest(current_digest, desired_digest)
        if not current_is_expected and not current_is_desired:
            raise LedgerIntegrityError("record key prepare does not match the store head")
        self._cleanup_staged_target_atomic_write_temps_locked(stage_body)
        if current_is_expected:
            self._apply_staged_target(stage_body, allow_expected=True)
            self._write_bytes(self._head_path, desired_head)
            decoded_head = self._decode_head_bytes(desired_head)
            self._highest_revision = decoded_head.revision
            self._highest_head_digest = _sha256_hex(decoded_head.encoded)
        else:
            self._apply_staged_target(stage_body, allow_expected=False)
        self._cleanup_mutation_files()

    def _decode_staged(self, encoded: bytes) -> dict[str, JsonValue]:
        body = _decode_authenticated_envelope(encoded, self._auth_key, label="staged state")
        _require_exact_keys(
            body,
            {
                "event_id",
                "event_state",
                "expected_event_digest",
                "expected_head_digest",
                "expected_revision",
                "expected_tombstone_digest",
                "head_state",
                "kind",
                "ledger_id",
                "new_revision",
                "operation",
                "root_name",
                "store_id",
                "token",
                "tombstone_state",
                "version",
            },
            label="staged state",
        )
        self._validate_common_body(body, kind="staged")
        self._validate_mutation_body(body)
        return body

    def _decode_prepare(self, encoded: bytes) -> dict[str, JsonValue]:
        body = _decode_authenticated_envelope(encoded, self._auth_key, label="prepare state")
        _require_exact_keys(
            body,
            {
                "event_digest",
                "event_id",
                "expected_head_digest",
                "expected_revision",
                "head_digest",
                "kind",
                "ledger_id",
                "new_revision",
                "operation",
                "root_name",
                "staged_digest",
                "store_id",
                "token",
                "tombstone_digest",
                "version",
            },
            label="prepare state",
        )
        self._validate_common_body(body, kind="prepare")
        self._validate_mutation_body(body)
        _digest_or_none(body.get("event_digest"), label="prepared event digest")
        _digest_or_none(body.get("tombstone_digest"), label="prepared tombstone digest")
        _digest(body.get("head_digest"), label="prepared head digest")
        _digest(body.get("staged_digest"), label="staged digest")
        return body

    def _validate_mutation_body(self, body: Mapping[str, JsonValue]) -> None:
        operation = body.get("operation")
        if operation not in {"put_pending", "mark_committed", "shred", "discard_pending"}:
            raise LedgerIntegrityError("record key mutation operation is invalid")
        event_id = validate_event_id(_required_str(body.get("event_id"), label="event ID"))
        token = _required_str(body.get("token"), label="event token")
        _validate_token(token)
        if not hmac.compare_digest(token, self._token(event_id)):
            raise LedgerIntegrityError("record key mutation address mismatch")
        expected_revision = _nonnegative_int(
            body.get("expected_revision"),
            label="expected revision",
        )
        new_revision = _positive_int(body.get("new_revision"), label="new revision")
        if new_revision != expected_revision + 1:
            raise LedgerIntegrityError("record key mutation revision is not contiguous")
        _digest(body.get("expected_head_digest"), label="expected head digest")

    def _validate_prepare_pair(
        self,
        staged: bytes,
        stage_body: Mapping[str, JsonValue],
        prepare_body: Mapping[str, JsonValue],
    ) -> None:
        if not hmac.compare_digest(
            cast(str, prepare_body["staged_digest"]),
            _sha256_hex(staged),
        ):
            raise LedgerIntegrityError("record key staged digest mismatch")
        for name in ("event_id", "expected_revision", "new_revision", "operation"):
            if prepare_body[name] != stage_body[name]:
                raise LedgerIntegrityError("record key prepare/staged mismatch")
        for name in ("expected_head_digest", "token"):
            if not hmac.compare_digest(
                cast(str, prepare_body[name]),
                cast(str, stage_body[name]),
            ):
                raise LedgerIntegrityError("record key prepare/staged mismatch")
        event_state = _optional_decoded_bytes(stage_body.get("event_state"), label="event state")
        tombstone_state = _optional_decoded_bytes(
            stage_body.get("tombstone_state"),
            label="tombstone state",
        )
        desired_head = _decode_b64_bytes(
            stage_body.get("head_state"),
            expected_length=None,
            label="staged head",
        )
        if not _optional_digest_matches(
            cast(str | None, prepare_body["event_digest"]),
            _optional_digest(event_state),
        ):
            raise LedgerIntegrityError("prepared event state mismatch")
        if not _optional_digest_matches(
            cast(str | None, prepare_body["tombstone_digest"]),
            _optional_digest(tombstone_state),
        ):
            raise LedgerIntegrityError("prepared tombstone state mismatch")
        if not hmac.compare_digest(
            cast(str, prepare_body["head_digest"]),
            _sha256_hex(desired_head),
        ):
            raise LedgerIntegrityError("prepared head state mismatch")
        desired = self._decode_head_bytes(desired_head)
        if desired.revision != cast(int, stage_body["new_revision"]):
            raise LedgerIntegrityError("prepared head revision mismatch")

    def _apply_staged_target(
        self,
        stage_body: Mapping[str, JsonValue],
        *,
        allow_expected: bool,
    ) -> None:
        token = cast(str, stage_body["token"])
        event_id = cast(str, stage_body["event_id"])
        event_state = _optional_decoded_bytes(stage_body.get("event_state"), label="event state")
        tombstone_state = _optional_decoded_bytes(
            stage_body.get("tombstone_state"),
            label="tombstone state",
        )
        if event_state is not None:
            event = self._decode_event(event_state, expected_token=token)
            if event.event_id != event_id:
                raise LedgerIntegrityError("staged event ID mismatch")
        if tombstone_state is not None:
            tombstone = self._decode_tombstone(tombstone_state, expected_token=token)
            if tombstone.event_id != event_id:
                raise LedgerIntegrityError("staged tombstone event ID mismatch")
        targets = (
            (
                self._event_path(token),
                _digest_or_none(
                    stage_body.get("expected_event_digest"),
                    label="expected event digest",
                ),
                event_state,
            ),
            (
                self._tombstone_path(token),
                _digest_or_none(
                    stage_body.get("expected_tombstone_digest"),
                    label="expected tombstone digest",
                ),
                tombstone_state,
            ),
        )
        # New durable state is installed before obsolete state is removed.  A
        # shred crash can therefore leave both members temporarily, but never
        # loses the committed key-destruction receipt; prepare recovery removes
        # the obsolete event before advancing the head.
        for desired_presence in (True, False):
            for path, expected_digest, desired in targets:
                if (desired is not None) is desired_presence:
                    self._apply_one_target(
                        path,
                        expected_digest=expected_digest,
                        desired=desired,
                        allow_expected=allow_expected,
                    )

    def _apply_one_target(
        self,
        path: Path,
        *,
        expected_digest: str | None,
        desired: bytes | None,
        allow_expected: bool,
    ) -> None:
        current = _read_optional_regular_file(path)
        current_digest = _optional_digest(current)
        desired_digest = _optional_digest(desired)
        if _optional_digest_matches(current_digest, desired_digest):
            return
        if not allow_expected or not _optional_digest_matches(
            current_digest,
            expected_digest,
        ):
            raise LedgerIntegrityError("record key mutation target changed unexpectedly")
        if desired is None:
            self._remove_file(path)
        else:
            self._write_bytes(path, desired)

    def _decode_head_bytes(self, encoded: bytes) -> _DirectoryHead:
        body = _decode_authenticated_envelope(encoded, self._auth_key, label="staged head")
        self._validate_common_body(body, kind="head")
        _require_exact_keys(
            body,
            {
                "accumulator",
                "event_count",
                "kind",
                "ledger_id",
                "revision",
                "root_name",
                "store_id",
                "tombstone_count",
                "version",
            },
            label="staged head",
        )
        return _DirectoryHead(
            revision=_nonnegative_int(body.get("revision"), label="store revision"),
            event_count=_nonnegative_int(body.get("event_count"), label="event count"),
            tombstone_count=_nonnegative_int(
                body.get("tombstone_count"),
                label="tombstone count",
            ),
            accumulator=_hex_bytes(body.get("accumulator"), label="state accumulator"),
            encoded=encoded,
        )

    def _cleanup_mutation_files(self) -> None:
        # Commit intent is removed first.  A crash between the two unlinks then
        # leaves an authenticated orphan stage that can be safely discarded.
        self._remove_file(self._prepare_path)
        self._remove_file(self._staged_path)
        _fsync_directory(self._root)

    def _inject(self, boundary: str) -> None:
        if self._fault_injector is not None:
            self._fault_injector(boundary)

    def _write_authenticated(
        self,
        path: Path,
        body: Mapping[str, JsonValue],
        key: bytes,
    ) -> None:
        self._write_bytes(path, _encode_authenticated_envelope(body, key))

    def _write_bytes(self, path: Path, encoded: bytes) -> None:
        parent_existed = path.parent.exists()
        try:
            atomic_write_bytes(path, encoded)
        except OSError as exc:
            raise LedgerIntegrityError("record key directory cannot be written") from exc
        if not parent_existed:
            _fsync_directory(path.parent.parent)

    def _remove_file(self, path: Path) -> None:
        resolve_ledger_path(path)
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise LedgerIntegrityError("record key directory cannot be cleaned") from exc
        _fsync_directory(path.parent)

    def _verify_integrity_locked(
        self,
    ) -> tuple[dict[str, _DirectoryEvent], dict[str, _DirectoryTombstone]]:
        self._validate_root_layout()
        head = self._read_head()
        events = self._scan_events()
        tombstones = self._scan_tombstones()
        if set(events).intersection(tombstones):
            raise LedgerIntegrityError("record key is live and tombstoned")
        accumulator = bytearray(_EMPTY_ACCUMULATOR)
        for token, event in events.items():
            _xor_into(accumulator, self._member_digest("event", token, event.encoded))
        for token, tombstone in tombstones.items():
            _xor_into(
                accumulator,
                self._member_digest("tombstone", token, tombstone.encoded),
            )
        if (
            head.event_count != len(events)
            or head.tombstone_count != len(tombstones)
            or not hmac.compare_digest(head.accumulator, bytes(accumulator))
        ):
            raise LedgerIntegrityError("record key directory head does not match state")
        self._verified_event_digests = {
            token: _sha256_hex(event.encoded) for token, event in events.items()
        }
        self._verified_tombstone_digests = {
            token: _sha256_hex(tombstone.encoded)
            for token, tombstone in tombstones.items()
        }
        self._verified_revision = head.revision
        self._verified_head_digest = _sha256_hex(head.encoded)
        self._membership_uncertain = False
        return events, tombstones

    def _validate_root_layout(self) -> None:
        allowed = {"events", "head.json", "identity.json", "tombstones"}
        try:
            entries = tuple(self._root.iterdir())
        except OSError as exc:
            raise LedgerIntegrityError("record key directory is unreadable") from exc
        names = {entry.name for entry in entries}
        if names != allowed:
            raise LedgerIntegrityError("record key directory layout is invalid")
        for path in (self._events_root, self._tombstones_root):
            resolve_ledger_path(path)
            if not path.is_dir():
                raise LedgerIntegrityError("record key fanout path is not a directory")

    def _scan_events(self) -> dict[str, _DirectoryEvent]:
        result: dict[str, _DirectoryEvent] = {}
        for token, encoded in self._scan_member_files(self._events_root):
            event = self._decode_event(encoded, expected_token=token)
            if token in result:
                raise LedgerIntegrityError("duplicate record key address")
            result[token] = event
        if len({event.event_id for event in result.values()}) != len(result):
            raise LedgerIntegrityError("duplicate record key event ID")
        return result

    def _scan_tombstones(self) -> dict[str, _DirectoryTombstone]:
        result: dict[str, _DirectoryTombstone] = {}
        for token, encoded in self._scan_member_files(self._tombstones_root):
            tombstone = self._decode_tombstone(encoded, expected_token=token)
            if token in result:
                raise LedgerIntegrityError("duplicate tombstone address")
            result[token] = tombstone
        if len({item.event_id for item in result.values()}) != len(result):
            raise LedgerIntegrityError("duplicate tombstone event ID")
        return result

    def _scan_member_files(self, root: Path) -> Iterator[tuple[str, bytes]]:
        try:
            fanouts = sorted(root.iterdir(), key=lambda path: path.name)
        except OSError as exc:
            raise LedgerIntegrityError("record key fanout is unreadable") from exc
        for fanout in fanouts:
            resolve_ledger_path(fanout)
            if (
                not fanout.is_dir()
                or len(fanout.name) != 2
                or any(character not in _HEX_DIGITS for character in fanout.name)
            ):
                raise LedgerIntegrityError("record key fanout directory is malformed")
            try:
                members = sorted(fanout.iterdir(), key=lambda path: path.name)
            except OSError as exc:
                raise LedgerIntegrityError("record key fanout is unreadable") from exc
            for member in members:
                name = member.name
                if not name.endswith(".json"):
                    raise LedgerIntegrityError("record key member filename is malformed")
                token = name[:-5]
                _validate_token(token)
                if token[:2] != fanout.name:
                    raise LedgerIntegrityError("record key member fanout mismatch")
                yield token, _read_regular_file(member)


def _atomic_temp_target(name: str) -> str | None:
    if not name.startswith(".") or not name.endswith(".tmp"):
        return None
    try:
        target, process_id, nonce = name[1:-4].rsplit(".", 2)
    except ValueError:
        return None
    if (
        not target
        or not _is_canonical_process_id(process_id)
        or len(nonce) != 32
        or nonce != nonce.lower()
        or any(character not in _HEX_DIGITS for character in nonce)
    ):
        return None
    return target


def _is_initialization_temp_name(name: str, root_name: str) -> bool:
    prefix = f".{root_name}."
    if not name.startswith(prefix) or not name.endswith(_INITIALIZATION_TEMP_SUFFIX):
        return False
    middle = name[len(prefix) : -len(_INITIALIZATION_TEMP_SUFFIX)]
    try:
        process_id, nonce = middle.rsplit(".", 1)
    except ValueError:
        return False
    return (
        _is_canonical_process_id(process_id)
        and len(nonce) == 32
        and nonce == nonce.lower()
        and all(character in _HEX_DIGITS for character in nonce)
    )


def _is_canonical_process_id(value: str) -> bool:
    return value.isascii() and value.isdigit() and not value.startswith("0")


def _validate_cleanup_file(path_stat: os.stat_result) -> None:
    if (
        not stat.S_ISREG(path_stat.st_mode)
        or path_stat.st_size > _DIRECTORY_STORE_MAX_ENVELOPE_BYTES
    ):
        raise LedgerIntegrityError("record key temporary state is malformed")


def _derive_store_key(master_key: bytes, salt_material: bytes, info: bytes) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=hashlib.sha256(salt_material).digest(),
        info=info,
    ).derive(master_key)


def _encode_authenticated_envelope(
    body: Mapping[str, JsonValue],
    key: bytes,
) -> bytes:
    canonical_body = canonical_json_bytes(dict(body))
    envelope: dict[str, JsonValue] = {
        "body": dict(body),
        "mac": hmac.new(key, canonical_body, hashlib.sha256).hexdigest(),
    }
    return canonical_json_bytes(envelope)


def _decode_authenticated_envelope(
    encoded: bytes,
    key: bytes,
    *,
    label: str,
) -> dict[str, JsonValue]:
    body, supplied_mac = _decode_canonical_envelope(encoded, label=label)
    _verify_envelope_mac(body, supplied_mac, key, label=label)
    return body


def _decode_canonical_envelope(
    encoded: bytes,
    *,
    label: str,
) -> tuple[dict[str, JsonValue], str]:
    try:
        decoded = strict_json_loads(encoded)
        if canonical_json_bytes(decoded) != encoded:
            raise StateIntegrityError(f"{label} is not canonical JSON")
    except (InputBoundaryError, StateIntegrityError) as exc:
        raise LedgerIntegrityError(f"{label} is malformed") from exc
    if type(decoded) is not dict or set(decoded) != {"body", "mac"}:
        raise LedgerIntegrityError(f"{label} envelope is malformed")
    body = decoded.get("body")
    supplied_mac = decoded.get("mac")
    if type(body) is not dict or type(supplied_mac) is not str:
        raise LedgerIntegrityError(f"{label} envelope is malformed")
    _digest(supplied_mac, label=f"{label} MAC")
    return cast(dict[str, JsonValue], body), supplied_mac


def _verify_envelope_mac(
    body: Mapping[str, JsonValue],
    supplied_mac: str,
    key: bytes,
    *,
    label: str,
) -> None:
    expected_mac = hmac.new(
        key,
        canonical_json_bytes(dict(body)),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(supplied_mac, expected_mac):
        raise LedgerIntegrityError(f"{label} authentication failed")


def _read_optional_regular_file(path: Path) -> bytes | None:
    resolve_ledger_path(path)
    try:
        path.lstat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise LedgerIntegrityError("record key state is unavailable") from exc
    return _read_regular_file(path)


def _read_regular_file(path: Path) -> bytes:
    resolve_ledger_path(path)
    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode):
            raise LedgerIntegrityError("record key state path is not a regular file")
        if before.st_size > _DIRECTORY_STORE_MAX_ENVELOPE_BYTES:
            raise LedgerIntegrityError("record key state exceeds the size boundary")
        encoded = path.read_bytes()
        after = path.lstat()
    except LedgerIntegrityError:
        raise
    except OSError as exc:
        raise LedgerIntegrityError("record key state is unavailable") from exc
    if (
        before.st_dev != after.st_dev
        or before.st_ino != after.st_ino
        or before.st_size != after.st_size
        or len(encoded) != after.st_size
        or len(encoded) > _DIRECTORY_STORE_MAX_ENVELOPE_BYTES
    ):
        raise LedgerIntegrityError("record key state changed while being read")
    resolve_ledger_path(path)
    return encoded


def _require_exact_keys(
    value: Mapping[str, JsonValue],
    expected: set[str],
    *,
    label: str,
) -> None:
    if set(value) != expected:
        raise LedgerIntegrityError(f"{label} fields are invalid")


def _required_str(value: JsonValue | None, *, label: str) -> str:
    if type(value) is not str or not value:
        raise LedgerIntegrityError(f"{label} is malformed")
    return value


def _nonnegative_int(value: JsonValue | None, *, label: str) -> int:
    if type(value) is not int or value < 0:
        raise LedgerIntegrityError(f"{label} is malformed")
    return value


def _positive_int(value: JsonValue | None, *, label: str) -> int:
    result = _nonnegative_int(value, label=label)
    if result == 0:
        raise LedgerIntegrityError(f"{label} must be positive")
    return result


def _validate_store_id(value: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or value != value.lower()
        or any(character not in _HEX_DIGITS for character in value)
    ):
        raise LedgerIntegrityError("record key directory store ID is malformed")
    return value


def _validate_token(value: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or value != value.lower()
        or any(character not in _HEX_DIGITS for character in value)
    ):
        raise LedgerIntegrityError("record key address token is malformed")
    return value


def _digest(value: JsonValue | None, *, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or value != value.lower()
        or any(character not in _HEX_DIGITS for character in value)
    ):
        raise LedgerIntegrityError(f"{label} is malformed")
    return value


def _digest_or_none(value: JsonValue | None, *, label: str) -> str | None:
    if value is None:
        return None
    return _digest(value, label=label)


def _hex_bytes(value: JsonValue | None, *, label: str) -> bytes:
    return bytes.fromhex(_digest(value, label=label))


def _decode_b64_bytes(
    value: JsonValue | None,
    *,
    expected_length: int | None,
    label: str,
) -> bytes:
    if type(value) is not str:
        raise LedgerIntegrityError(f"{label} is malformed")
    try:
        decoded = base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error) as exc:
        raise LedgerIntegrityError(f"{label} is malformed") from exc
    if expected_length is not None and len(decoded) != expected_length:
        raise LedgerIntegrityError(f"{label} has an invalid length")
    if len(decoded) > _DIRECTORY_STORE_MAX_ENVELOPE_BYTES:
        raise LedgerIntegrityError(f"{label} exceeds the size boundary")
    return decoded


def _optional_decoded_bytes(value: JsonValue | None, *, label: str) -> bytes | None:
    if value is None:
        return None
    return _decode_b64_bytes(value, expected_length=None, label=label)


def _optional_b64(value: bytes | None) -> str | None:
    return None if value is None else _b64(value)


def _optional_digest(value: bytes | None) -> str | None:
    return None if value is None else _sha256_hex(value)


def _optional_digest_matches(left: str | None, right: str | None) -> bool:
    if left is None or right is None:
        return left is None and right is None
    return hmac.compare_digest(left, right)


def _sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _xor_into(target: bytearray, value: bytes) -> None:
    if len(target) != len(value):
        raise LedgerIntegrityError("state accumulator length mismatch")
    for index, byte in enumerate(value):
        target[index] ^= byte


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _initial_state(ledger_id: str) -> dict[str, JsonValue]:
    return {"entries": {}, "ledger_id": ledger_id, "revision": 0, "tombstones": {}, "version": 1}


def _bump(state: dict[str, JsonValue]) -> None:
    state["revision"] = cast(int, state["revision"]) + 1


def _reference(event_id: str, entry: dict[str, JsonValue]) -> RecordKeyReference:
    token = hmac.new(b"reference", event_id.encode("ascii"), hashlib.sha256).hexdigest()
    return RecordKeyReference(
        event_id=event_id,
        reference=token,
        state=RecordKeyState(cast(str, entry["state"])),
        record_hash=cast(str | None, entry["record_hash"]),
    )


def _missing_reference() -> RecordKeyReference:
    raise LedgerIntegrityError("record key reference disappeared")


def _entry_dict(value: JsonValue | None) -> dict[str, JsonValue]:
    if type(value) is not dict:
        raise LedgerIntegrityError("record key entry is missing or malformed")
    if type(value.get("key")) is not str or type(value.get("state")) is not str:
        raise LedgerIntegrityError("record key entry is malformed")
    if value.get("record_hash") is not None and type(value.get("record_hash")) is not str:
        raise LedgerIntegrityError("record key hash is malformed")
    return cast(dict[str, JsonValue], value)


def _tombstone_record_hash(value: JsonValue) -> str:
    if type(value) is not dict:
        raise LedgerIntegrityError("tombstone is malformed")
    return _record_hash(cast(str, value.get("record_hash")))


def _key_bytes(value: bytes | bytearray | memoryview, *, label: str) -> bytes:
    if type(value) not in (bytes, bytearray, memoryview):
        raise InputBoundaryError(f"{label} must be bytes-like")
    data = bytes(value)
    if len(data) != 32:
        raise InputBoundaryError(f"{label} must be exactly 32 bytes")
    return data


def _record_hash(value: str) -> str:
    if type(value) is not str or len(value) != 64:
        raise LedgerIntegrityError("record hash must be 32-byte hex")
    try:
        bytes.fromhex(value)
    except ValueError as exc:
        raise LedgerIntegrityError("record hash must be 32-byte hex") from exc
    return value


def _validate_ledger_id(value: str) -> str:
    if type(value) is not str or not value or len(value.encode("utf-8")) > 256:
        raise InputBoundaryError("ledger_id is outside canonical boundary")
    return value


def _state_name_for_path(path: Path) -> str:
    _validate_json_store_path(path)
    name = path.stem
    if STATE_NAME_PATTERN.fullmatch(name) is None:
        raise InputBoundaryError("record key store path must have a canonical state name")
    return name


def _validate_json_store_path(path: Path) -> None:
    if path.suffix != ".json":
        raise InputBoundaryError("record key store path must end with .json")


def _write_all(fd: int, data: bytes) -> None:
    offset = 0
    while offset < len(data):
        written = os.write(fd, data[offset:])
        if written <= 0:
            raise OSError("short file key write")
        offset += written


def _unlink_if_same_file(path: Path, opened_stat: os.stat_result) -> None:
    try:
        current_stat = path.lstat()
        if (
            stat.S_ISREG(current_stat.st_mode)
            and current_stat.st_dev == opened_stat.st_dev
            and current_stat.st_ino == opened_stat.st_ino
        ):
            path.unlink()
    except OSError:
        pass


def _has_partial_state(root: Path, state_name: str) -> bool:
    return any(root.glob(f"{state_name}.*.manifest.json"))


def _validate_keyring_backend(keyring_module: object) -> None:
    get_keyring = getattr(keyring_module, "get_keyring", None)
    if not callable(get_keyring):
        raise KeyProviderUnavailable("keyring backend is unavailable")
    try:
        backend = get_keyring()
    except Exception as exc:
        raise KeyProviderUnavailable("keyring backend is unavailable") from exc
    if backend is None:
        raise KeyProviderUnavailable("keyring backend is unavailable")
    if not _is_secure_keyring_backend(backend):
        raise KeyProviderUnavailable("keyring backend is not secure")


def _is_secure_keyring_backend(backend: object) -> bool:
    backend_type = type(backend)
    module = getattr(backend_type, "__module__", "").lower()
    if module in {"keyring.backends.fail", "keyring.backends.null"}:
        return False
    try:
        priority = getattr(backend, "priority")
    except Exception:
        return False
    try:
        if float(priority) < 1:
            return False
    except (TypeError, ValueError):
        return False
    backend_name = _backend_name(backend)
    if module.startswith("keyrings.alt"):
        return False
    if any(token in backend_name for token in _INSECURE_KEYRING_BACKEND_TOKENS):
        return False
    if module == "keyring.backends.chainer":
        candidate_backends = getattr(backend, "backends", None)
        if not candidate_backends:
            return False
        return all(_is_secure_keyring_backend(candidate) for candidate in candidate_backends)
    return True


def _backend_name(backend: object) -> str:
    backend_type = type(backend)
    module = getattr(backend_type, "__module__", "")
    qualname = getattr(backend_type, "__qualname__", backend_type.__name__)
    name = getattr(backend_type, "__name__", backend_type.__name__)
    return f"{module}.{qualname}.{name}".lower()


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _b64_key(value: str) -> bytes:
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error) as exc:
        raise StateIntegrityError("record key is not valid base64") from exc
