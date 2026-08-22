from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import os
import secrets
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Protocol, cast

from .codec import canonical_json_bytes, strict_json_loads, validate_event_id
from .contracts import (
    InputBoundaryError,
    JsonValue,
    KeyProvider,
    KeyProviderUnavailable,
    LedgerIntegrityError,
    LedgerSecurityScope,
    StateIntegrityError,
    UnsafePathError,
)
from .persistence import atomic_write_bytes, exclusive_file_lock, resolve_ledger_path

__all__ = [
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
        try:
            data = self._path.read_bytes()
        except OSError as exc:
            raise KeyProviderUnavailable("file key is unavailable") from exc
        return _key_bytes(data, label="file key")

    def _create_secret(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._path.open("xb") as handle:
                handle.write(secrets.token_bytes(32))
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError:
            return
        if os.name != "nt":
            mode = self._path.stat().st_mode & 0o777
            if mode & 0o077:
                try:
                    self._path.chmod(0o600)
                except OSError as exc:
                    raise KeyProviderUnavailable("file key mode is too permissive") from exc


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
    def is_tombstoned(self, event_id: str) -> bool: ...
    def iter_references(self) -> Iterator[RecordKeyReference]: ...
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
        self._lock_path = self._path.with_suffix(self._path.suffix + ".lock")
        self._key = _key_bytes(integrity_key, label="integrity_key")
        self._ledger_id = _validate_ledger_id(ledger_id)
        if not self._path.exists():
            if not create:
                raise LedgerIntegrityError("record key store is missing")
            self._save(_initial_state(self._ledger_id))
        self.verify_integrity()

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
                if current_hash == safe_hash:
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
            if entry_dict.get("record_hash") != safe_hash:
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

    def iter_references(self) -> Iterator[RecordKeyReference]:
        entries = cast(dict[str, JsonValue], self._load()["entries"])
        for event_id in sorted(entries):
            yield _reference(event_id, _entry_dict(entries[event_id]))

    def verify_integrity(self) -> None:
        self._load()

    def _load(self) -> dict[str, JsonValue]:
        try:
            resolve_ledger_path(self._path)
            envelope = strict_json_loads(self._path.read_bytes())
        except (OSError, InputBoundaryError, UnsafePathError) as exc:
            raise LedgerIntegrityError("record key store is unreadable") from exc
        if type(envelope) is not dict:
            raise LedgerIntegrityError("record key store envelope is malformed")
        payload = envelope.get("payload")
        mac = envelope.get("mac")
        if type(payload) is not dict or type(mac) is not str:
            raise LedgerIntegrityError("record key store envelope is malformed")
        payload_bytes = canonical_json_bytes(payload)
        expected = self._mac(payload_bytes)
        if not hmac.compare_digest(mac, expected):
            raise LedgerIntegrityError("record key store MAC does not verify")
        try:
            self._validate_state(payload)
        except (InputBoundaryError, StateIntegrityError) as exc:
            raise LedgerIntegrityError("record key store state is invalid") from exc
        return cast(dict[str, JsonValue], payload)

    def _save(self, state: dict[str, JsonValue]) -> None:
        payload_bytes = canonical_json_bytes(state)
        envelope = {"mac": self._mac(payload_bytes), "payload": state}
        atomic_write_bytes(self._path, canonical_json_bytes(cast(JsonValue, envelope)))

    def _mac(self, payload: bytes) -> str:
        return hmac.new(
            self._key,
            b"aluclu/v2/file-record-key-store\0" + payload,
            hashlib.sha256,
        ).hexdigest()

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


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _b64_key(value: str) -> bytes:
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error) as exc:
        raise StateIntegrityError("record key is not valid base64") from exc
