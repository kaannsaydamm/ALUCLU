from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import stat
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from .codec import (
    MAX_PAYLOAD_BYTES,
    canonical_json_bytes,
    strict_json_loads,
    validate_event_id,
)
from .contracts import (
    AppendOutcome,
    InputBoundaryError,
    JsonValue,
    KeyProvider,
    LedgerCapabilityUnavailable,
    LedgerConflictError,
    LedgerIntegrityError,
    LedgerKeyError,
    LedgerLifecycleError,
    LedgerMigrationRequired,
    LedgerRecord,
    LedgerRollbackError,
    LedgerSecurityScope,
    LedgerVerificationStats,
    PersistenceError,
    UnsafePathError,
)
from .keys import (
    DirectoryRecordKeyStore,
    KeyringKeyProvider,
    RecordKeyReference,
    RecordKeyState,
    RecordKeyStore,
    RecordKeyStoreProfile,
    _capture_keyring_store_plan,
    _CapturedKeyringStorePlan,
    create_record_key_store,
)
from .persistence import (
    atomic_publish_path,
    atomic_write_bytes,
    durable_unlink,
    exclusive_file_lock,
    resolve_ledger_path,
)

SCHEMA_VERSION = 2
ZERO_HASH = b"\0" * 32
_BOOTSTRAP_VERSION = 1
_BOOTSTRAP_MAX_BYTES = 16 * 1024
_HEX_DIGITS = frozenset("0123456789abcdef")
_METADATA_KEYS = {
    "schema_version",
    "ledger_id",
    "identity_root",
    "key_check",
    "head_sequence",
    "head_hash",
}
_EXPECTED_COLUMNS = {
    "metadata": (
        ("key", "TEXT", 1, 1),
        ("value", "BLOB", 1, 0),
    ),
    "history": (
        ("sequence", "INTEGER", 0, 1),
        ("operation", "TEXT", 1, 0),
        ("event_id", "TEXT", 1, 0),
        ("key_reference", "TEXT", 0, 0),
        ("nonce", "BLOB", 0, 0),
        ("ciphertext", "BLOB", 0, 0),
        ("created_ns", "INTEGER", 1, 0),
        ("previous_hash", "BLOB", 1, 0),
        ("record_hash", "BLOB", 1, 0),
    ),
    "records": (
        ("event_id", "TEXT", 1, 1),
        ("history_sequence", "INTEGER", 1, 0),
        ("record_hash", "BLOB", 1, 0),
    ),
    "tombstones": (
        ("event_id", "TEXT", 1, 1),
        ("history_sequence", "INTEGER", 1, 0),
        ("record_hash", "BLOB", 1, 0),
    ),
}

_SCHEMA = (
    """
    CREATE TABLE metadata (
        key TEXT PRIMARY KEY,
        value BLOB NOT NULL
    ) STRICT, WITHOUT ROWID
    """,
    """
    CREATE TABLE history (
        sequence INTEGER PRIMARY KEY CHECK(sequence > 0),
        operation TEXT NOT NULL CHECK(operation IN ('append', 'shred')),
        event_id TEXT NOT NULL,
        key_reference TEXT,
        nonce BLOB,
        ciphertext BLOB,
        created_ns INTEGER NOT NULL CHECK(created_ns > 0),
        previous_hash BLOB NOT NULL CHECK(length(previous_hash) = 32),
        record_hash BLOB NOT NULL UNIQUE CHECK(length(record_hash) = 32),
        CHECK(
            (operation = 'append' AND key_reference IS NOT NULL
                AND nonce IS NOT NULL AND length(nonce) = 12
                AND ciphertext IS NOT NULL)
            OR
            (operation = 'shred' AND key_reference IS NULL
                AND nonce IS NULL AND ciphertext IS NULL)
        )
    ) STRICT
    """,
    """
    CREATE TABLE records (
        event_id TEXT PRIMARY KEY,
        history_sequence INTEGER NOT NULL UNIQUE REFERENCES history(sequence),
        record_hash BLOB NOT NULL UNIQUE CHECK(length(record_hash) = 32)
    ) STRICT, WITHOUT ROWID
    """,
    """
    CREATE TABLE tombstones (
        event_id TEXT PRIMARY KEY,
        history_sequence INTEGER NOT NULL UNIQUE REFERENCES history(sequence),
        record_hash BLOB NOT NULL UNIQUE CHECK(length(record_hash) = 32)
    ) STRICT, WITHOUT ROWID
    """,
)
_SCHEMA_TABLES = ("metadata", "history", "records", "tombstones")


@dataclass(frozen=True)
class _LedgerState:
    metadata: dict[str, bytes]
    records: dict[str, tuple[int, bytes]]
    tombstones: dict[str, tuple[int, bytes]]
    live_rows: dict[str, HistoryRow]
    append_hashes: dict[str, bytes]
    key_references: dict[str, str]
    head_sequence: int
    head_hash: bytes


@dataclass(frozen=True)
class _LedgerBootstrap:
    bootstrap_id: str
    database_path: str
    identity_root: bytes
    ledger_id: str
    provider_scope: LedgerSecurityScope
    store_mode: str
    store_profile: RecordKeyStoreProfile
    store_binding: str | None


class EncryptedLedger:
    def __init__(
        self,
        path: str | Path,
        key_provider: KeyProvider,
        *,
        record_key_store: RecordKeyStore | None = None,
        _fault_injector: Callable[[str], None] | None = None,
    ) -> None:
        self._path = resolve_ledger_path(path)
        self._lock_path = self._path.with_suffix(self._path.suffix + ".lock")
        self._anchor_path = self._path.with_suffix(self._path.suffix + ".anchor.json")
        self._bootstrap_pending_path = self._path.with_suffix(
            self._path.suffix + ".bootstrap.pending.json"
        )
        self._bootstrap_complete_path = self._path.with_suffix(
            self._path.suffix + ".bootstrap.complete.json"
        )
        self._record_store_path = self._path.with_suffix(
            self._path.suffix + ".record-keys"
        )
        self._legacy_record_store_path = self._path.with_suffix(
            self._path.suffix + ".record-keys.json"
        )
        self._provider = key_provider
        self._provided_store = record_key_store
        self._fault_injector = _fault_injector
        self._record_store: RecordKeyStore | None = None
        self._connection: sqlite3.Connection | None = None
        self._ledger_id: str | None = None
        self._identity_root: bytes | None = None
        self._chain_key: bytes | None = None
        self._anchor_key: bytes | None = None
        self._store_key: bytes | None = None
        self._expected_key_check: bytes | None = None
        self._keyring_plan: _CapturedKeyringStorePlan | None = None
        self._open = False
        self._object_lock = threading.RLock()
        self._full_verifications = 0

    def __enter__(self) -> EncryptedLedger:
        self.unlock()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    @property
    def ledger_id(self) -> str:
        self._require_open()
        return cast(str, self._ledger_id)

    @property
    def verification_stats(self) -> LedgerVerificationStats:
        return LedgerVerificationStats(
            full_verifications=self._full_verifications,
            delta_verifications=0,
        )

    def unlock(self) -> None:
        with self._object_lock:
            if self._open:
                return
            self._preflight_record_store()
            try:
                resolve_ledger_path(self._path)
                with exclusive_file_lock(self._lock_path):
                    master_key = self._master_key()
                    bootstrap_phase = self._bootstrap_phase()
                    if bootstrap_phase is not None:
                        self._resume_bootstrap(master_key, phase=bootstrap_phase)
                    elif self._path.exists():
                        self._unlock_existing(master_key)
                    else:
                        self._unlock_new(master_key)
                    self._open = True
            except Exception:
                self._close_connection()
                self._clear_secrets()
                raise

    def close(self) -> None:
        with self._object_lock:
            self._close_connection()
            self._record_store = None
            self._clear_secrets()
            self._open = False

    def append(self, event_id: str, payload: JsonValue) -> AppendOutcome:
        return self._append(event_id, payload, idempotent=False)

    def append_once(self, event_id: str, payload: JsonValue) -> AppendOutcome:
        return self._append(event_id, payload, idempotent=True)

    def read(self, event_id: str) -> LedgerRecord | None:
        with self._object_lock:
            self._require_open()
            safe_event_id = validate_event_id(event_id)
            with exclusive_file_lock(self._lock_path):
                connection = self._connection_required()
                connection.execute("BEGIN IMMEDIATE")
                try:
                    verification = self._verify_integrity_locked()
                    record = self._read_record_locked(safe_event_id)
                    connection.execute("COMMIT")
                except Exception:
                    if connection.in_transaction:
                        connection.execute("ROLLBACK")
                    raise
                self._advance_verified_anchor(verification)
                return record

    def shred(self, event_id: str) -> bool:
        with self._object_lock:
            self._require_open()
            safe_event_id = validate_event_id(event_id)
            with exclusive_file_lock(self._lock_path):
                connection = self._connection_required()
                store = self._record_store_required()
                connection.execute("BEGIN IMMEDIATE")
                try:
                    verification = self._verify_integrity_locked()
                    lineage = self._lineage(safe_event_id)
                    if lineage is None or lineage[0] == "tombstone":
                        connection.execute("COMMIT")
                        self._advance_verified_anchor(verification)
                        return False

                    row = verification[0].live_rows.get(safe_event_id)
                    if row is None:
                        raise LedgerIntegrityError("live record history is missing")
                    append_hash = row[8]
                    if not store.shred(safe_event_id, append_hash.hex()):
                        raise LedgerIntegrityError("record key could not be shredded")
                    self._inject_fault("after_store_tombstone_before_sqlite_shred")
                    sequence, record_hash = self._append_shred_history_locked(
                        safe_event_id,
                        append_hash,
                    )
                    connection.execute("COMMIT")
                except Exception:
                    if connection.in_transaction:
                        connection.execute("ROLLBACK")
                    raise
                self._inject_fault("after_sqlite_shred_before_anchor")
                self._write_anchor(sequence, record_hash)
                return True

    def is_tombstoned(self, event_id: str) -> bool:
        with self._object_lock:
            self._require_open()
            safe_event_id = validate_event_id(event_id)
            with exclusive_file_lock(self._lock_path):
                connection = self._connection_required()
                connection.execute("BEGIN IMMEDIATE")
                try:
                    verification = self._verify_integrity_locked()
                    found = self._lineage(safe_event_id)
                    result = found is not None and found[0] == "tombstone"
                    connection.execute("COMMIT")
                except Exception:
                    if connection.in_transaction:
                        connection.execute("ROLLBACK")
                    raise
                self._advance_verified_anchor(verification)
                return result

    def event_count(self) -> int:
        with self._object_lock:
            self._require_open()
            with exclusive_file_lock(self._lock_path):
                connection = self._connection_required()
                connection.execute("BEGIN IMMEDIATE")
                try:
                    verification = self._verify_integrity_locked()
                    count = cast(
                        int,
                        connection.execute("SELECT COUNT(*) FROM history").fetchone()[
                            0
                        ],
                    )
                    connection.execute("COMMIT")
                except Exception:
                    if connection.in_transaction:
                        connection.execute("ROLLBACK")
                    raise
                self._advance_verified_anchor(verification)
                return count

    def verify_integrity(self) -> None:
        with self._object_lock:
            self._require_open()
            with exclusive_file_lock(self._lock_path):
                connection = self._connection_required()
                connection.execute("BEGIN IMMEDIATE")
                try:
                    verification = self._verify_integrity_locked()
                    connection.execute("COMMIT")
                except Exception:
                    if connection.in_transaction:
                        connection.execute("ROLLBACK")
                    raise
                self._advance_verified_anchor(verification)

    def _unlock_new(self, master_key: bytes) -> None:
        if self._anchor_path.exists() or self._record_state_exists():
            raise LedgerIntegrityError("new ledger has pre-existing sidecar state")
        if self._provided_store is not None:
            self._require_empty_bootstrap_store(self._provided_store)
        ledger_id = (
            self._provided_store.ledger_id
            if self._provided_store is not None
            else secrets.token_hex(16)
        )
        identity_root = secrets.token_bytes(32)
        self._install_identity(master_key, ledger_id, identity_root)
        bootstrap = _LedgerBootstrap(
            bootstrap_id=secrets.token_hex(32),
            database_path=self._database_path_identity(),
            identity_root=identity_root,
            ledger_id=ledger_id,
            provider_scope=self._provider.security_scope,
            store_mode=self._bootstrap_store_mode(),
            store_profile=self._bootstrap_store_profile(),
            store_binding=self._bootstrap_store_binding(),
        )
        self._write_bootstrap_marker(
            bootstrap, self._bootstrap_pending_path, master_key
        )
        self._inject_fault("after_ledger_bootstrap_marker")
        self._resume_bootstrap(master_key, phase="pending")

    def _resume_bootstrap(self, master_key: bytes, *, phase: str) -> None:
        marker_path = (
            self._bootstrap_pending_path
            if phase == "pending"
            else self._bootstrap_complete_path
        )
        bootstrap = self._load_bootstrap_marker(marker_path, master_key)
        self._validate_bootstrap_binding(bootstrap)
        self._install_identity(
            master_key,
            bootstrap.ledger_id,
            bootstrap.identity_root,
        )
        bootstrap_key_check = self._bootstrap_key_check(master_key, bootstrap)
        if self._provided_store is not None:
            self._require_empty_bootstrap_store(self._provided_store)

        if not self._path.exists():
            if phase != "pending":
                raise LedgerIntegrityError("completed bootstrap database is missing")
            if self._anchor_path.exists() or (
                self._provided_store is None and self._record_store_path.exists()
            ):
                raise LedgerIntegrityError(
                    "bootstrap sidecars exist before the database publish"
                )
            self._cleanup_bootstrap_scratch(bootstrap)
            self._build_bootstrap_database(bootstrap, bootstrap_key_check)
            self._inject_fault("after_ledger_bootstrap_database")

        try:
            connection = self._connect(configure=False)
        except sqlite3.DatabaseError as exc:
            raise LedgerIntegrityError("bootstrap database is invalid") from exc
        self._connection = connection
        try:
            stored_key_check = self._verify_bootstrap_database(
                connection,
                bootstrap,
                bootstrap_key_check,
                phase=phase,
            )
        except sqlite3.DatabaseError as exc:
            raise LedgerIntegrityError("bootstrap database is invalid") from exc
        self._configure_connection(connection)
        self._cleanup_bootstrap_scratch(bootstrap)

        store_exists = (
            self._provided_store is not None or self._record_store_path.exists()
        )
        if phase == "complete" and not store_exists:
            raise LedgerIntegrityError("completed bootstrap record store is missing")
        if self._anchor_path.exists() and not store_exists:
            raise LedgerIntegrityError(
                "bootstrap anchor exists before the record store"
            )
        self._record_store = self._open_record_store(
            create=phase == "pending" and not store_exists
        )
        self._verify_empty_bootstrap_store()
        if phase == "pending":
            self._inject_fault("after_ledger_bootstrap_store")

        if self._anchor_path.exists():
            self._verify_zero_bootstrap_anchor()
        elif phase == "pending":
            self._write_anchor(0, ZERO_HASH)
            self._inject_fault("after_ledger_bootstrap_anchor")
        else:
            raise LedgerIntegrityError("completed bootstrap anchor is missing")

        if phase == "pending":
            atomic_publish_path(
                self._bootstrap_pending_path,
                self._bootstrap_complete_path,
            )
            self._inject_fault("after_ledger_bootstrap_complete_marker")
        if hmac.compare_digest(stored_key_check, bootstrap_key_check):
            self._finalize_bootstrap_key_check(connection, bootstrap_key_check)
            self._inject_fault("after_ledger_bootstrap_key_check")

        self._verify_integrity_locked()
        self._inject_fault("after_ledger_bootstrap_verified")
        durable_unlink(self._bootstrap_complete_path)

    def _build_bootstrap_database(
        self,
        bootstrap: _LedgerBootstrap,
        bootstrap_key_check: bytes,
    ) -> None:
        staging = self._bootstrap_staging_path(bootstrap)
        connection = self._connect(configure=True, path=staging)
        try:
            connection.execute("BEGIN IMMEDIATE")
            for statement in _SCHEMA:
                connection.execute(statement)
            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            metadata = {
                "schema_version": str(SCHEMA_VERSION).encode("ascii"),
                "ledger_id": bootstrap.ledger_id.encode("utf-8"),
                "identity_root": bootstrap.identity_root,
                "key_check": bootstrap_key_check,
                "head_sequence": b"0",
                "head_hash": ZERO_HASH,
            }
            connection.executemany(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                [(key, sqlite3.Binary(value)) for key, value in metadata.items()],
            )
            connection.execute("COMMIT")
            self._inject_fault("after_ledger_bootstrap_staging_commit")
            checkpoint = connection.execute(
                "PRAGMA wal_checkpoint(TRUNCATE)"
            ).fetchone()
            if checkpoint is None or tuple(checkpoint) != (0, 0, 0):
                raise LedgerCapabilityUnavailable(
                    "bootstrap SQLite WAL cannot be checkpointed"
                )
            journal_mode = cast(
                str,
                connection.execute("PRAGMA journal_mode = DELETE").fetchone()[0],
            )
            if journal_mode.casefold() != "delete":
                raise LedgerCapabilityUnavailable(
                    "bootstrap SQLite journal cannot be made self-contained"
                )
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()
        self._inject_fault("after_ledger_bootstrap_staging_database")

        verification = self._connect(configure=False, path=staging)
        try:
            self._verify_bootstrap_database(
                verification,
                bootstrap,
                bootstrap_key_check,
                phase="pending",
            )
        finally:
            verification.close()
        atomic_publish_path(staging, self._path)
        self._cleanup_bootstrap_scratch(bootstrap)

    def _verify_bootstrap_database(
        self,
        connection: sqlite3.Connection,
        bootstrap: _LedgerBootstrap,
        bootstrap_key_check: bytes,
        *,
        phase: str,
    ) -> bytes:
        self._verify_schema(connection)
        metadata = self._metadata(connection)
        if (
            metadata["ledger_id"] != bootstrap.ledger_id.encode("utf-8")
            or metadata["identity_root"] != bootstrap.identity_root
            or metadata["head_sequence"] != b"0"
            or not hmac.compare_digest(metadata["head_hash"], ZERO_HASH)
        ):
            raise LedgerIntegrityError("bootstrap database identity is invalid")
        stored_key_check = metadata["key_check"]
        final_key_check = cast(bytes, self._expected_key_check)
        is_bootstrap = hmac.compare_digest(stored_key_check, bootstrap_key_check)
        is_final = hmac.compare_digest(stored_key_check, final_key_check)
        if not is_bootstrap and not is_final:
            raise LedgerKeyError("master key does not match bootstrap database")
        if phase == "pending" and not is_bootstrap:
            raise LedgerIntegrityError("pending bootstrap marker was replayed")
        counts = tuple(
            cast(int, connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in ("history", "records", "tombstones")
        )
        if counts != (0, 0, 0):
            raise LedgerIntegrityError("bootstrap database is not empty")
        return stored_key_check

    def _verify_empty_bootstrap_store(self) -> None:
        self._require_empty_bootstrap_store(self._record_store_required())

    def _require_empty_bootstrap_store(self, store: RecordKeyStore) -> None:
        store.verify_integrity()
        if (
            store.revision != 0
            or tuple(store.iter_references())
            or tuple(store.iter_tombstones())
        ):
            raise LedgerIntegrityError("bootstrap record store is not empty")

    def _verify_zero_bootstrap_anchor(self) -> None:
        sequence, record_hash = self._load_anchor()
        if sequence != 0 or not hmac.compare_digest(record_hash, ZERO_HASH):
            raise LedgerIntegrityError("bootstrap anchor is not empty")

    def _finalize_bootstrap_key_check(
        self,
        connection: sqlite3.Connection,
        bootstrap_key_check: bytes,
    ) -> None:
        connection.execute("BEGIN IMMEDIATE")
        try:
            cursor = connection.execute(
                "UPDATE metadata SET value = ? WHERE key = 'key_check' AND value = ?",
                (
                    sqlite3.Binary(cast(bytes, self._expected_key_check)),
                    sqlite3.Binary(bootstrap_key_check),
                ),
            )
            if cursor.rowcount != 1:
                raise LedgerIntegrityError("bootstrap key check changed unexpectedly")
            connection.execute("COMMIT")
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise

    def _bootstrap_phase(self) -> str | None:
        try:
            resolve_ledger_path(self._bootstrap_pending_path)
            resolve_ledger_path(self._bootstrap_complete_path)
        except UnsafePathError as exc:
            raise LedgerIntegrityError(
                "ledger bootstrap marker path is unsafe"
            ) from exc
        pending = self._bootstrap_pending_path.exists()
        complete = self._bootstrap_complete_path.exists()
        if pending and complete:
            raise LedgerIntegrityError("ledger bootstrap phases conflict")
        if pending:
            return "pending"
        if complete:
            return "complete"
        return None

    def _write_bootstrap_marker(
        self,
        bootstrap: _LedgerBootstrap,
        path: Path,
        master_key: bytes,
    ) -> None:
        body: JsonValue = {
            "bootstrap_id": bootstrap.bootstrap_id,
            "database_path": bootstrap.database_path,
            "identity_root": base64.b64encode(bootstrap.identity_root).decode("ascii"),
            "kind": "ledger-bootstrap",
            "ledger_id": bootstrap.ledger_id,
            "provider_scope": bootstrap.provider_scope.value,
            "store_binding": bootstrap.store_binding,
            "store_mode": bootstrap.store_mode,
            "store_profile": bootstrap.store_profile.value,
            "version": _BOOTSTRAP_VERSION,
        }
        body_bytes = canonical_json_bytes(body)
        key = _derive(
            master_key,
            bootstrap.identity_root,
            bootstrap.ledger_id,
            b"bootstrap-marker-auth",
        )
        envelope: JsonValue = {
            "body": body,
            "mac": hmac.new(
                key,
                b"aluclu/v2/bootstrap-marker\0" + body_bytes,
                hashlib.sha256,
            ).hexdigest(),
        }
        atomic_write_bytes(path, canonical_json_bytes(envelope))

    def _load_bootstrap_marker(
        self,
        path: Path,
        master_key: bytes,
    ) -> _LedgerBootstrap:
        encoded = _read_bootstrap_file(path)
        try:
            decoded = strict_json_loads(encoded)
            if canonical_json_bytes(decoded) != encoded:
                raise LedgerIntegrityError("ledger bootstrap marker is not canonical")
        except InputBoundaryError as exc:
            raise LedgerIntegrityError("ledger bootstrap marker is malformed") from exc
        if type(decoded) is not dict or set(decoded) != {"body", "mac"}:
            raise LedgerIntegrityError("ledger bootstrap envelope is malformed")
        body = decoded.get("body")
        supplied_mac = decoded.get("mac")
        if type(body) is not dict or type(supplied_mac) is not str:
            raise LedgerIntegrityError("ledger bootstrap envelope is malformed")
        if set(body) != {
            "bootstrap_id",
            "database_path",
            "identity_root",
            "kind",
            "ledger_id",
            "provider_scope",
            "store_binding",
            "store_mode",
            "store_profile",
            "version",
        }:
            raise LedgerIntegrityError("ledger bootstrap fields are invalid")
        if body.get("kind") != "ledger-bootstrap" or body.get("version") != 1:
            raise LedgerMigrationRequired("ledger bootstrap version is unsupported")

        bootstrap_id = body.get("bootstrap_id")
        database_path = body.get("database_path")
        ledger_id = body.get("ledger_id")
        encoded_identity = body.get("identity_root")
        scope_value = body.get("provider_scope")
        store_binding = body.get("store_binding")
        store_mode = body.get("store_mode")
        store_profile_value = body.get("store_profile")
        if (
            type(bootstrap_id) is not str
            or not _is_lower_hex(bootstrap_id, length=64)
            or type(database_path) is not str
            or not database_path
            or type(ledger_id) is not str
            or not ledger_id
            or len(ledger_id.encode("utf-8")) > 256
            or type(encoded_identity) is not str
            or type(scope_value) is not str
            or type(store_mode) is not str
            or store_mode not in {"directory", "keyring", "provided"}
            or type(store_profile_value) is not str
            or (
                store_binding is not None
                and (
                    type(store_binding) is not str
                    or not _is_lower_hex(store_binding, length=64)
                )
            )
            or not _is_lower_hex(supplied_mac, length=64)
        ):
            raise LedgerIntegrityError("ledger bootstrap value is malformed")
        try:
            identity_root = base64.b64decode(
                encoded_identity.encode("ascii"),
                validate=True,
            )
            provider_scope = LedgerSecurityScope(scope_value)
            store_profile = RecordKeyStoreProfile(store_profile_value)
        except (UnicodeEncodeError, ValueError) as exc:
            raise LedgerIntegrityError("ledger bootstrap value is malformed") from exc
        if len(identity_root) != 32:
            raise LedgerIntegrityError("ledger bootstrap identity root is malformed")

        bootstrap = _LedgerBootstrap(
            bootstrap_id=bootstrap_id,
            database_path=database_path,
            identity_root=identity_root,
            ledger_id=ledger_id,
            provider_scope=provider_scope,
            store_mode=store_mode,
            store_profile=store_profile,
            store_binding=store_binding,
        )
        key = _derive(
            master_key,
            bootstrap.identity_root,
            bootstrap.ledger_id,
            b"bootstrap-marker-auth",
        )
        expected_mac = hmac.new(
            key,
            b"aluclu/v2/bootstrap-marker\0" + canonical_json_bytes(body),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(supplied_mac, expected_mac):
            raise LedgerKeyError("master key does not match ledger bootstrap")
        return bootstrap

    def _validate_bootstrap_binding(self, bootstrap: _LedgerBootstrap) -> None:
        if bootstrap.database_path != self._database_path_identity():
            raise LedgerIntegrityError("ledger bootstrap database path changed")
        if bootstrap.provider_scope is not self._provider.security_scope:
            raise LedgerIntegrityError("ledger bootstrap provider scope changed")
        expected_mode = self._bootstrap_store_mode()
        if bootstrap.store_mode != expected_mode:
            raise LedgerIntegrityError("ledger bootstrap record-store mode changed")
        if bootstrap.store_profile is not self._bootstrap_store_profile():
            raise LedgerIntegrityError("ledger bootstrap record-store profile changed")
        expected_binding = self._bootstrap_store_binding()
        if not _optional_digest_matches(bootstrap.store_binding, expected_binding):
            raise LedgerIntegrityError("ledger bootstrap record-store binding changed")
        if (
            self._provided_store is not None
            and self._provided_store.ledger_id != bootstrap.ledger_id
        ):
            raise LedgerIntegrityError("ledger bootstrap record-store identity changed")

    def _bootstrap_key_check(
        self,
        master_key: bytes,
        bootstrap: _LedgerBootstrap,
    ) -> bytes:
        key = _derive(
            master_key,
            bootstrap.identity_root,
            bootstrap.ledger_id,
            b"bootstrap-key-check",
        )
        message = b"\0".join(
            (
                b"aluclu/v2/bootstrap-key-check",
                bootstrap.bootstrap_id.encode("ascii"),
                bootstrap.database_path.encode("utf-8"),
            )
        )
        return hmac.new(key, message, hashlib.sha256).digest()

    def _database_path_identity(self) -> str:
        return os.path.normcase(os.path.normpath(str(self._path)))

    def _bootstrap_staging_path(self, bootstrap: _LedgerBootstrap) -> Path:
        return self._path.parent / (
            f".{bootstrap.bootstrap_id}.aluclu-bootstrap.sqlite3"
        )

    def _cleanup_bootstrap_scratch(self, bootstrap: _LedgerBootstrap) -> None:
        staging = self._bootstrap_staging_path(bootstrap)
        paths = (
            staging,
            Path(f"{staging}-wal"),
            Path(f"{staging}-shm"),
            Path(f"{staging}-journal"),
        )
        existing: list[Path] = []
        for path in paths:
            try:
                resolved = resolve_ledger_path(path)
                path_stat = resolved.lstat()
            except FileNotFoundError:
                continue
            except (OSError, UnsafePathError) as exc:
                raise LedgerIntegrityError(
                    "ledger bootstrap scratch is unsafe"
                ) from exc
            if os.path.normcase(str(resolved.parent)) != os.path.normcase(
                str(self._path.parent)
            ) or not stat.S_ISREG(path_stat.st_mode):
                raise LedgerIntegrityError("ledger bootstrap scratch is malformed")
            existing.append(resolved)
        for path in existing:
            try:
                durable_unlink(path)
            except PersistenceError as exc:
                raise LedgerIntegrityError(
                    "ledger bootstrap scratch cannot be cleaned"
                ) from exc

    def _unlock_existing(self, master_key: bytes) -> None:
        connection = self._connect(configure=False)
        self._connection = connection
        if (
            cast(int, connection.execute("PRAGMA user_version").fetchone()[0])
            != SCHEMA_VERSION
        ):
            raise LedgerMigrationRequired("existing database is not schema v2")
        if not self._anchor_path.exists():
            raise LedgerIntegrityError("ledger anchor is missing")
        metadata = self._metadata(connection)
        try:
            ledger_id = metadata["ledger_id"].decode("utf-8")
            identity_root = metadata["identity_root"]
        except (KeyError, UnicodeDecodeError) as exc:
            raise LedgerIntegrityError("ledger identity metadata is malformed") from exc
        if (
            not ledger_id
            or len(ledger_id.encode("utf-8")) > 256
            or len(identity_root) != 32
        ):
            raise LedgerIntegrityError("ledger identity root is malformed")
        self._install_identity(master_key, ledger_id, identity_root)
        if not hmac.compare_digest(
            metadata["key_check"], cast(bytes, self._expected_key_check)
        ):
            raise LedgerKeyError("master key does not match ledger")
        self._configure_connection(connection)
        self._record_store = self._open_record_store(create=False)
        connection.execute("BEGIN IMMEDIATE")
        try:
            verification = self._verify_integrity_locked()
            connection.execute("COMMIT")
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        self._advance_verified_anchor(verification)

    def _append(
        self,
        event_id: str,
        payload: JsonValue,
        *,
        idempotent: bool,
    ) -> AppendOutcome:
        with self._object_lock:
            self._require_open()
            safe_event_id = validate_event_id(event_id)
            payload_bytes = canonical_json_bytes(payload)
            with exclusive_file_lock(self._lock_path):
                connection = self._connection_required()
                store = self._record_store_required()
                connection.execute("BEGIN IMMEDIATE")
                pending_created = False
                sqlite_committed = False
                try:
                    verification = self._verify_integrity_locked()
                    existing = self._lineage(safe_event_id)
                    if existing is not None:
                        operation = existing[0]
                        if idempotent and operation == "record":
                            record = self._read_record_locked(safe_event_id)
                            if (
                                record is None
                                or canonical_json_bytes(record.payload) != payload_bytes
                            ):
                                raise LedgerConflictError(
                                    "event payload conflicts with live record"
                                )
                            connection.execute("COMMIT")
                            sqlite_committed = True
                            self._advance_verified_anchor(verification)
                            return AppendOutcome(record=record, created=False)
                        raise LedgerConflictError("event ID already has ledger lineage")

                    metadata = self._metadata(connection)
                    sequence = _metadata_int(metadata, "head_sequence") + 1
                    previous_hash = _metadata_hash(metadata, "head_hash")
                    created_ns = max(1, time.time_ns())
                    record_key = secrets.token_bytes(32)
                    before = store.reference(safe_event_id)
                    reference = store.put_pending(safe_event_id, record_key)
                    pending_created = before is None
                    self._inject_fault("after_pending_key_before_sqlite_insert")
                    nonce = secrets.token_bytes(12)
                    aad = self._aad(
                        operation="append",
                        sequence=sequence,
                        event_id=safe_event_id,
                        key_reference=reference.reference,
                        previous_hash=previous_hash,
                        created_ns=created_ns,
                    )
                    ciphertext = AESGCM(record_key).encrypt(nonce, payload_bytes, aad)
                    record_hash = self._history_hash(
                        sequence=sequence,
                        operation="append",
                        event_id=safe_event_id,
                        key_reference=reference.reference,
                        nonce=nonce,
                        ciphertext=ciphertext,
                        created_ns=created_ns,
                        previous_hash=previous_hash,
                    )
                    connection.execute(
                        """
                        INSERT INTO history(
                            sequence, operation, event_id, key_reference, nonce,
                            ciphertext, created_ns, previous_hash, record_hash
                        ) VALUES (?, 'append', ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            sequence,
                            safe_event_id,
                            reference.reference,
                            sqlite3.Binary(nonce),
                            sqlite3.Binary(ciphertext),
                            created_ns,
                            sqlite3.Binary(previous_hash),
                            sqlite3.Binary(record_hash),
                        ),
                    )
                    connection.execute(
                        "INSERT INTO records(event_id, history_sequence, record_hash) VALUES (?, ?, ?)",
                        (safe_event_id, sequence, sqlite3.Binary(record_hash)),
                    )
                    self._set_head(connection, sequence, record_hash)
                    connection.execute("COMMIT")
                    sqlite_committed = True
                    self._inject_fault("after_sqlite_commit_before_key_committed")
                    store.mark_committed(safe_event_id, record_hash.hex())
                    self._inject_fault("after_key_committed_before_anchor")
                    self._write_anchor(sequence, record_hash)
                    decoded = strict_json_loads(payload_bytes)
                    return AppendOutcome(
                        record=LedgerRecord(
                            sequence=sequence,
                            event_id=safe_event_id,
                            payload=decoded,
                            record_hash=record_hash.hex(),
                            created_ns=created_ns,
                        ),
                        created=True,
                    )
                except Exception:
                    if connection.in_transaction:
                        connection.execute("ROLLBACK")
                    if not sqlite_committed and pending_created:
                        store.discard_pending(safe_event_id)
                    raise

    def _verify_integrity_locked(self) -> tuple[_LedgerState, bool]:
        state = self._scan_history_locked()
        anchor_lagging = self._verify_anchor_locked(state)
        if self._recover_external_state_locked(state):
            state = self._scan_history_locked()
        self._verify_external_state_locked(state)
        anchor_lagging = self._verify_anchor_locked(state)
        self._full_verifications += 1
        return state, anchor_lagging

    def _scan_history_locked(self) -> _LedgerState:
        connection = self._connection_required()
        store = self._record_store_required()
        self._verify_schema(connection)
        metadata = self._metadata(connection)
        try:
            stored_ledger_id = metadata["ledger_id"].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise LedgerIntegrityError("ledger identity is not ASCII") from exc
        if stored_ledger_id != self._ledger_id:
            raise LedgerIntegrityError("ledger identity changed")
        if metadata["identity_root"] != self._identity_root:
            raise LedgerIntegrityError("ledger identity root changed")
        if not hmac.compare_digest(
            metadata["key_check"], cast(bytes, self._expected_key_check)
        ):
            raise LedgerKeyError("ledger key check changed")
        store.verify_integrity()

        expected_records: dict[str, tuple[int, bytes]] = {}
        expected_tombstones: dict[str, tuple[int, bytes]] = {}
        live_rows: dict[str, HistoryRow] = {}
        append_hashes: dict[str, bytes] = {}
        expected_key_references: dict[str, str] = {}
        previous_hash = ZERO_HASH
        expected_sequence = 1
        rows = connection.execute(
            """
            SELECT sequence, operation, event_id, key_reference, nonce,
                   ciphertext, created_ns, previous_hash, record_hash
            FROM history ORDER BY sequence
            """
        )
        for raw_row in rows:
            row = _history_row(raw_row)
            sequence = row[0]
            if sequence != expected_sequence or not hmac.compare_digest(
                row[7],
                previous_hash,
            ):
                raise LedgerIntegrityError("history chain sequence is broken")
            try:
                validate_event_id(row[2])
            except InputBoundaryError as exc:
                raise LedgerIntegrityError("stored event ID is invalid") from exc
            try:
                computed_hash = self._history_hash(
                    sequence=sequence,
                    operation=row[1],
                    event_id=row[2],
                    key_reference=row[3],
                    nonce=row[4],
                    ciphertext=row[5],
                    created_ns=row[6],
                    previous_hash=row[7],
                )
            except (InputBoundaryError, UnicodeEncodeError) as exc:
                raise LedgerIntegrityError(
                    "history authenticated bytes are invalid"
                ) from exc
            if not hmac.compare_digest(row[8], computed_hash):
                raise LedgerIntegrityError("history record hash does not verify")
            if row[1] == "append":
                if row[2] in append_hashes:
                    raise LedgerIntegrityError("event lineage is duplicated")
                expected_records[row[2]] = (sequence, row[8])
                live_rows[row[2]] = row
                append_hashes[row[2]] = row[8]
                expected_key_references[row[2]] = cast(str, row[3])
            elif row[1] == "shred":
                live = expected_records.pop(row[2], None)
                live_rows.pop(row[2], None)
                expected_key_references.pop(row[2], None)
                if live is None or row[2] in expected_tombstones:
                    raise LedgerIntegrityError("shred lineage has no live record")
                expected_tombstones[row[2]] = (sequence, row[8])
            else:
                raise LedgerIntegrityError("history operation is invalid")
            previous_hash = row[8]
            expected_sequence += 1

        actual_head_sequence = expected_sequence - 1
        if _metadata_int(metadata, "head_sequence") != actual_head_sequence:
            raise LedgerIntegrityError("metadata head sequence does not verify")
        if not hmac.compare_digest(
            _metadata_hash(metadata, "head_hash"), previous_hash
        ):
            raise LedgerIntegrityError("metadata head hash does not verify")
        if not _projections_match(_projection(connection, "records"), expected_records):
            raise LedgerIntegrityError("live record projection does not verify")
        if not _projections_match(
            _projection(connection, "tombstones"),
            expected_tombstones,
        ):
            raise LedgerIntegrityError("tombstone projection does not verify")

        return _LedgerState(
            metadata=metadata,
            records=expected_records,
            tombstones=expected_tombstones,
            live_rows=live_rows,
            append_hashes=append_hashes,
            key_references=expected_key_references,
            head_sequence=actual_head_sequence,
            head_hash=previous_hash,
        )

    def _recover_external_state_locked(self, state: _LedgerState) -> bool:
        store = self._record_store_required()
        references, tombstones = self._external_state_snapshot()
        pending_commits: list[tuple[str, str]] = []
        pending_discards: list[str] = []
        forward_shreds: list[tuple[str, bytes]] = []

        for event_id, (_sequence, record_hash) in state.records.items():
            reference = references.get(event_id)
            tombstone_hash = tombstones.get(event_id)
            if reference is None:
                if tombstone_hash is None:
                    raise LedgerKeyError("live record has no key or tombstone")
                if not hmac.compare_digest(tombstone_hash, record_hash.hex()):
                    raise LedgerIntegrityError(
                        "record key tombstone hash does not verify"
                    )
                forward_shreds.append((event_id, record_hash))
                continue
            if tombstone_hash is not None:
                raise LedgerIntegrityError("record key is both live and tombstoned")
            if not hmac.compare_digest(
                reference.reference,
                state.key_references[event_id],
            ):
                raise LedgerIntegrityError("record key reference does not verify")
            if reference.state is RecordKeyState.PENDING:
                if reference.record_hash is not None:
                    raise LedgerIntegrityError("pending record key has a receipt")
                pending_commits.append((event_id, record_hash.hex()))
            elif reference.state is not RecordKeyState.COMMITTED or (
                reference.record_hash is None
                or not hmac.compare_digest(reference.record_hash, record_hash.hex())
            ):
                raise LedgerIntegrityError(
                    "committed record key receipt does not verify"
                )

        for event_id in state.tombstones:
            if event_id in references:
                raise LedgerIntegrityError("shredded lineage still has a record key")
            tombstone_hash = tombstones.get(event_id)
            if tombstone_hash is None:
                raise LedgerKeyError("shredded lineage has no external tombstone")
            if not hmac.compare_digest(
                tombstone_hash,
                state.append_hashes[event_id].hex(),
            ):
                raise LedgerIntegrityError("record key tombstone hash does not verify")

        for event_id, reference in references.items():
            if event_id in state.records:
                continue
            if reference.state is RecordKeyState.COMMITTED:
                raise LedgerRollbackError(
                    "committed record key is absent from database"
                )
            if reference.state is not RecordKeyState.PENDING:
                raise LedgerIntegrityError("record key state is invalid")
            pending_discards.append(event_id)

        for event_id, tombstone_hash in tombstones.items():
            append_hash = state.append_hashes.get(event_id)
            if append_hash is None:
                raise LedgerIntegrityError("external tombstone has no database lineage")
            if not hmac.compare_digest(tombstone_hash, append_hash.hex()):
                raise LedgerIntegrityError("external tombstone hash does not verify")
            if event_id not in state.records and event_id not in state.tombstones:
                raise LedgerIntegrityError("external tombstone lineage is incomplete")

        for event_id, row in state.live_rows.items():
            if event_id in references:
                self._decrypt_row(row)

        for event_id in sorted(pending_discards):
            if not store.discard_pending(event_id):
                raise LedgerIntegrityError(
                    "unreferenced pending key could not be discarded"
                )
        for event_id, record_hash in sorted(pending_commits):
            store.mark_committed(event_id, record_hash)
        for event_id, append_hash in sorted(forward_shreds):
            self._append_shred_history_locked(event_id, append_hash)

        return bool(pending_discards or pending_commits or forward_shreds)

    def _verify_external_state_locked(self, state: _LedgerState) -> None:
        references, tombstones = self._external_state_snapshot()
        extra_references = set(references) - set(state.records)
        for event_id in extra_references:
            if references[event_id].state is RecordKeyState.COMMITTED:
                raise LedgerRollbackError(
                    "committed record key is absent from database"
                )
        if extra_references or set(state.records) - set(references):
            raise LedgerKeyError("record key projection does not verify")
        if set(tombstones) != set(state.tombstones):
            raise LedgerIntegrityError(
                "record key tombstone projection does not verify"
            )

        for event_id, (_sequence, record_hash) in state.records.items():
            reference = references[event_id]
            if (
                reference.state is not RecordKeyState.COMMITTED
                or reference.record_hash is None
                or not hmac.compare_digest(reference.record_hash, record_hash.hex())
                or not hmac.compare_digest(
                    reference.reference,
                    state.key_references[event_id],
                )
            ):
                raise LedgerIntegrityError("record key state does not verify")
            self._decrypt_row(state.live_rows[event_id])
        for event_id, tombstone_hash in tombstones.items():
            if not hmac.compare_digest(
                tombstone_hash,
                state.append_hashes[event_id].hex(),
            ):
                raise LedgerIntegrityError("record key tombstone does not verify")

    def _external_state_snapshot(
        self,
    ) -> tuple[dict[str, RecordKeyReference], dict[str, str]]:
        store = self._record_store_required()
        revision_before = store.revision
        references: dict[str, RecordKeyReference] = {}
        for reference in store.iter_references():
            if reference.event_id in references:
                raise LedgerIntegrityError("record key reference is duplicated")
            references[reference.event_id] = reference
        tombstones: dict[str, str] = {}
        for event_id, record_hash in store.iter_tombstones():
            if event_id in tombstones:
                raise LedgerIntegrityError("record key tombstone is duplicated")
            tombstones[event_id] = record_hash
        revision_after = store.revision
        if revision_before != revision_after:
            raise LedgerIntegrityError("record key store changed during verification")
        if set(references) & set(tombstones):
            raise LedgerIntegrityError("record key store state overlaps")
        return references, tombstones

    def _verify_anchor_locked(self, state: _LedgerState) -> bool:
        anchor_sequence, anchor_hash = self._load_anchor()
        if anchor_sequence > state.head_sequence:
            raise LedgerRollbackError("ledger anchor is ahead of database")
        if anchor_sequence == state.head_sequence:
            if not hmac.compare_digest(anchor_hash, state.head_hash):
                raise LedgerIntegrityError("ledger anchor head does not verify")
            return False
        if anchor_sequence == 0:
            expected_anchor_hash = ZERO_HASH
        else:
            row = (
                self._connection_required()
                .execute(
                    "SELECT record_hash FROM history WHERE sequence = ?",
                    (anchor_sequence,),
                )
                .fetchone()
            )
            if row is None or type(row[0]) is not bytes:
                raise LedgerRollbackError(
                    "ledger anchor lineage is absent from database"
                )
            expected_anchor_hash = cast(bytes, row[0])
        if not hmac.compare_digest(anchor_hash, expected_anchor_hash):
            raise LedgerRollbackError("ledger anchor is not a database ancestor")
        return True

    def _advance_verified_anchor(self, verification: tuple[_LedgerState, bool]) -> None:
        state, anchor_lagging = verification
        if anchor_lagging:
            self._write_anchor(state.head_sequence, state.head_hash)

    def _append_shred_history_locked(
        self,
        event_id: str,
        append_hash: bytes,
    ) -> tuple[int, bytes]:
        connection = self._connection_required()
        metadata = self._metadata(connection)
        sequence = _metadata_int(metadata, "head_sequence") + 1
        previous_hash = _metadata_hash(metadata, "head_hash")
        created_ns = max(1, time.time_ns())
        record_hash = self._history_hash(
            sequence=sequence,
            operation="shred",
            event_id=event_id,
            key_reference=None,
            nonce=None,
            ciphertext=None,
            created_ns=created_ns,
            previous_hash=previous_hash,
        )
        connection.execute(
            """
            INSERT INTO history(
                sequence, operation, event_id, key_reference, nonce,
                ciphertext, created_ns, previous_hash, record_hash
            ) VALUES (?, 'shred', ?, NULL, NULL, NULL, ?, ?, ?)
            """,
            (
                sequence,
                event_id,
                created_ns,
                sqlite3.Binary(previous_hash),
                sqlite3.Binary(record_hash),
            ),
        )
        deleted = connection.execute(
            "DELETE FROM records WHERE event_id = ? AND record_hash = ?",
            (event_id, sqlite3.Binary(append_hash)),
        )
        if deleted.rowcount != 1:
            raise LedgerIntegrityError("live record projection changed during shred")
        connection.execute(
            "INSERT INTO tombstones(event_id, history_sequence, record_hash) VALUES (?, ?, ?)",
            (event_id, sequence, sqlite3.Binary(record_hash)),
        )
        self._set_head(connection, sequence, record_hash)
        return sequence, record_hash

    def _read_record_locked(self, event_id: str) -> LedgerRecord | None:
        connection = self._connection_required()
        row = connection.execute(
            """
            SELECT h.sequence, h.operation, h.event_id, h.key_reference, h.nonce,
                   h.ciphertext, h.created_ns, h.previous_hash, h.record_hash
            FROM records AS r JOIN history AS h ON h.sequence = r.history_sequence
            WHERE r.event_id = ?
            """,
            (event_id,),
        ).fetchone()
        if row is None:
            return None
        parsed = _history_row(row)
        payload = self._decrypt_row(parsed)
        return LedgerRecord(
            sequence=parsed[0],
            event_id=parsed[2],
            payload=payload,
            record_hash=parsed[8].hex(),
            created_ns=parsed[6],
        )

    def _decrypt_row(self, row: HistoryRow) -> JsonValue:
        if row[1] != "append" or row[3] is None or row[4] is None or row[5] is None:
            raise LedgerIntegrityError("append history row is malformed")
        record_key = self._record_store_required().get(row[2])
        if record_key is None:
            raise LedgerKeyError("record key is missing")
        aad = self._aad(
            operation="append",
            sequence=row[0],
            event_id=row[2],
            key_reference=row[3],
            previous_hash=row[7],
            created_ns=row[6],
        )
        try:
            plaintext = AESGCM(record_key).decrypt(row[4], row[5], aad)
            return strict_json_loads(plaintext)
        except (InvalidTag, InputBoundaryError) as exc:
            raise LedgerIntegrityError("record ciphertext does not verify") from exc

    def _aad(
        self,
        *,
        operation: str,
        sequence: int,
        event_id: str,
        key_reference: str | None,
        previous_hash: bytes,
        created_ns: int,
    ) -> bytes:
        value: JsonValue = {
            "created_ns": created_ns,
            "event_id": event_id,
            "key_reference": key_reference,
            "ledger_id": cast(str, self._ledger_id),
            "operation": operation,
            "previous_hash": previous_hash.hex(),
            "schema_version": SCHEMA_VERSION,
            "sequence": sequence,
        }
        return canonical_json_bytes(value)

    def _history_hash(
        self,
        *,
        sequence: int,
        operation: str,
        event_id: str,
        key_reference: str | None,
        nonce: bytes | None,
        ciphertext: bytes | None,
        created_ns: int,
        previous_hash: bytes,
    ) -> bytes:
        event: JsonValue = {
            "ciphertext": _optional_b64(ciphertext),
            "created_ns": created_ns,
            "event_id": event_id,
            "key_reference": key_reference,
            "ledger_id": cast(str, self._ledger_id),
            "nonce": _optional_b64(nonce),
            "operation": operation,
            "previous_hash": previous_hash.hex(),
            "schema_version": SCHEMA_VERSION,
            "sequence": sequence,
        }
        return hmac.new(
            cast(bytes, self._chain_key),
            b"aluclu/v2/history\0" + _internal_canonical_json(event),
            hashlib.sha256,
        ).digest()

    def _lineage(self, event_id: str) -> tuple[str, int] | None:
        connection = self._connection_required()
        row = connection.execute(
            """
            SELECT 'record', history_sequence FROM records WHERE event_id = ?
            UNION ALL
            SELECT 'tombstone', history_sequence FROM tombstones WHERE event_id = ?
            """,
            (event_id, event_id),
        ).fetchone()
        if row is None:
            return None
        return cast(str, row[0]), cast(int, row[1])

    def _set_head(
        self, connection: sqlite3.Connection, sequence: int, record_hash: bytes
    ) -> None:
        connection.execute(
            "UPDATE metadata SET value = ? WHERE key = 'head_sequence'",
            (sqlite3.Binary(str(sequence).encode("ascii")),),
        )
        connection.execute(
            "UPDATE metadata SET value = ? WHERE key = 'head_hash'",
            (sqlite3.Binary(record_hash),),
        )

    def _install_identity(
        self, master_key: bytes, ledger_id: str, identity_root: bytes
    ) -> None:
        self._ledger_id = ledger_id
        self._identity_root = identity_root
        self._chain_key = _derive(master_key, identity_root, ledger_id, b"chain-mac")
        self._anchor_key = _derive(master_key, identity_root, ledger_id, b"anchor-auth")
        self._store_key = _derive(
            master_key, identity_root, ledger_id, b"record-store-root"
        )
        self._expected_key_check = self._key_check(master_key)

    def _key_check(self, master_key: bytes) -> bytes:
        material = cast(str, self._ledger_id).encode("utf-8") + cast(
            bytes, self._identity_root
        )
        key = _derive(
            master_key,
            cast(bytes, self._identity_root),
            cast(str, self._ledger_id),
            b"key-check",
        )
        return hmac.new(
            key, b"aluclu/v2/key-check\0" + material, hashlib.sha256
        ).digest()

    def _open_record_store(self, *, create: bool) -> RecordKeyStore:
        if self._provided_store is not None:
            if self._provided_store.ledger_id != self._ledger_id:
                raise LedgerIntegrityError("record key store ledger identity mismatch")
            self._validate_record_store_profile(self._provided_store)
            self._provided_store.verify_integrity()
            return self._provided_store
        if self._provider.security_scope is LedgerSecurityScope.OS_KEYRING:
            if self._keyring_plan is None:
                raise LedgerCapabilityUnavailable(
                    "OS-keyring record storage is unavailable"
                )
            return self._keyring_plan.open_store(
                cast(bytes, self._store_key),
                ledger_id=cast(str, self._ledger_id),
                create=create,
                fault_injector=self._fault_injector,
            )
        if self._fault_injector is not None:
            return DirectoryRecordKeyStore(
                self._record_store_path,
                cast(bytes, self._store_key),
                ledger_id=cast(str, self._ledger_id),
                create=create,
                _fault_injector=self._fault_injector,
            )
        return create_record_key_store(
            self._path,
            self._provider,
            integrity_key=cast(bytes, self._store_key),
            ledger_id=cast(str, self._ledger_id),
            create=create,
        )

    def _write_anchor(self, head_sequence: int, head_hash: bytes) -> None:
        payload: JsonValue = {
            "head_hash": head_hash.hex(),
            "head_sequence": head_sequence,
            "ledger_id": cast(str, self._ledger_id),
            "schema_version": SCHEMA_VERSION,
            "version": 1,
        }
        payload_bytes = canonical_json_bytes(payload)
        envelope: JsonValue = {
            "mac": hmac.new(
                cast(bytes, self._anchor_key),
                b"aluclu/v2/anchor\0" + payload_bytes,
                hashlib.sha256,
            ).hexdigest(),
            "payload": payload,
        }
        atomic_write_bytes(self._anchor_path, canonical_json_bytes(envelope))

    def _load_anchor(self) -> tuple[int, bytes]:
        try:
            resolve_ledger_path(self._anchor_path)
            envelope = strict_json_loads(self._anchor_path.read_bytes())
        except (OSError, InputBoundaryError, UnsafePathError) as exc:
            raise LedgerIntegrityError("ledger anchor is unreadable") from exc
        if type(envelope) is not dict or set(envelope) != {"mac", "payload"}:
            raise LedgerIntegrityError("ledger anchor is malformed")
        payload = envelope.get("payload")
        mac = envelope.get("mac")
        if type(payload) is not dict or type(mac) is not str:
            raise LedgerIntegrityError("ledger anchor is malformed")
        payload_bytes = canonical_json_bytes(payload)
        expected = hmac.new(
            cast(bytes, self._anchor_key),
            b"aluclu/v2/anchor\0" + payload_bytes,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(mac, expected):
            raise LedgerIntegrityError("ledger anchor MAC does not verify")
        if (
            set(payload)
            != {
                "head_hash",
                "head_sequence",
                "ledger_id",
                "schema_version",
                "version",
            }
            or payload.get("version") != 1
            or payload.get("schema_version") != SCHEMA_VERSION
            or payload.get("ledger_id") != self._ledger_id
            or type(payload.get("head_sequence")) is not int
            or type(payload.get("head_hash")) is not str
        ):
            raise LedgerIntegrityError("ledger anchor identity is invalid")
        encoded_head_hash = cast(str, payload["head_hash"])
        try:
            head_hash = bytes.fromhex(encoded_head_hash)
        except ValueError as exc:
            raise LedgerIntegrityError("ledger anchor hash is invalid") from exc
        head_sequence = cast(int, payload["head_sequence"])
        if (
            head_sequence < 0
            or len(head_hash) != 32
            or len(encoded_head_hash) != 64
            or encoded_head_hash != encoded_head_hash.lower()
        ):
            raise LedgerIntegrityError("ledger anchor head is invalid")
        return head_sequence, head_hash

    def _verify_schema(self, connection: sqlite3.Connection) -> None:
        if (
            cast(int, connection.execute("PRAGMA user_version").fetchone()[0])
            != SCHEMA_VERSION
        ):
            raise LedgerMigrationRequired("ledger schema version is unsupported")
        tables = {
            cast(str, row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        if tables != {"metadata", "history", "records", "tombstones"}:
            raise LedgerIntegrityError("ledger schema tables do not match")
        actual_sql = {
            cast(str, row[0]): _normalize_schema_sql(cast(str, row[1]))
            for row in connection.execute(
                "SELECT name, sql FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        expected_sql = {
            table: _normalize_schema_sql(statement)
            for table, statement in zip(_SCHEMA_TABLES, _SCHEMA, strict=True)
        }
        if actual_sql != expected_sql:
            raise LedgerIntegrityError("ledger schema SQL does not match")
        table_modes = {
            cast(str, row[1]): (cast(int, row[4]), cast(int, row[5]))
            for row in connection.execute("PRAGMA table_list")
            if row[0] == "main"
            and row[2] == "table"
            and not str(row[1]).startswith("sqlite_")
        }
        if table_modes != {
            "metadata": (1, 1),
            "history": (0, 1),
            "records": (1, 1),
            "tombstones": (1, 1),
        }:
            raise LedgerIntegrityError("ledger table modes do not match")
        for table, expected in _EXPECTED_COLUMNS.items():
            actual = tuple(
                (
                    cast(str, row[1]),
                    cast(str, row[2]),
                    cast(int, row[3]),
                    cast(int, row[5]),
                )
                for row in connection.execute(f"PRAGMA table_info({table})")
            )
            if actual != expected:
                raise LedgerIntegrityError(f"ledger {table} columns do not match")

    def _metadata(self, connection: sqlite3.Connection) -> dict[str, bytes]:
        try:
            rows = connection.execute("SELECT key, value FROM metadata").fetchall()
        except sqlite3.DatabaseError as exc:
            raise LedgerMigrationRequired(
                "ledger metadata schema is unavailable"
            ) from exc
        metadata: dict[str, bytes] = {}
        for key, value in rows:
            if type(key) is not str or type(value) is not bytes:
                raise LedgerIntegrityError("ledger metadata value is malformed")
            metadata[key] = value
        if set(metadata) != _METADATA_KEYS:
            raise LedgerIntegrityError("ledger metadata keys do not match")
        if metadata["schema_version"] != b"2":
            raise LedgerMigrationRequired("ledger metadata schema is unsupported")
        if len(metadata["key_check"]) != 32:
            raise LedgerIntegrityError("ledger key check is malformed")
        return metadata

    def _connect(
        self,
        *,
        configure: bool,
        path: Path | None = None,
    ) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self._path if path is None else path,
            isolation_level=None,
            check_same_thread=False,
            timeout=30.0,
        )
        try:
            connection.execute("PRAGMA trusted_schema = OFF")
            trusted_schema = cast(
                int, connection.execute("PRAGMA trusted_schema").fetchone()[0]
            )
            if trusted_schema != 0:
                raise LedgerCapabilityUnavailable(
                    "SQLite trusted_schema=OFF is unavailable"
                )

            connection.execute("PRAGMA cell_size_check = ON")
            cell_size_check = cast(
                int, connection.execute("PRAGMA cell_size_check").fetchone()[0]
            )
            if cell_size_check != 1:
                raise LedgerCapabilityUnavailable(
                    "SQLite cell_size_check=ON is unavailable"
                )

            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA busy_timeout = 30000")
            if configure:
                self._configure_connection(connection)
            return connection
        except Exception:
            connection.close()
            raise

    def _configure_connection(self, connection: sqlite3.Connection) -> None:
        journal_mode = cast(
            str, connection.execute("PRAGMA journal_mode = WAL").fetchone()[0]
        )
        if journal_mode.casefold() != "wal":
            raise LedgerCapabilityUnavailable("SQLite WAL mode is unavailable")
        connection.execute("PRAGMA synchronous = FULL")
        synchronous = cast(int, connection.execute("PRAGMA synchronous").fetchone()[0])
        if synchronous != 2:
            raise LedgerCapabilityUnavailable(
                "SQLite FULL synchronous mode is unavailable"
            )

    def _master_key(self) -> bytes:
        if isinstance(self._provider, KeyringKeyProvider):
            if self._keyring_plan is None:
                raise LedgerCapabilityUnavailable(
                    "OS-keyring record storage is unavailable"
                )
            key = self._provider._get_key_from_captured_backend(
                self._keyring_plan.backend
            )
        else:
            key = self._provider.get_key()
        if type(key) is not bytes or len(key) != 32:
            raise LedgerKeyError("master key must be exactly 32 immutable bytes")
        return bytes(key)

    def _record_state_exists(self) -> bool:
        if self._provided_store is not None:
            return False
        if self._record_store_path.exists() or self._legacy_record_store_path.exists():
            return True
        state_name = self._legacy_record_store_path.stem
        return any(
            self._legacy_record_store_path.parent.glob(f"{state_name}.*.manifest.json")
        )

    def _preflight_record_store(self) -> None:
        self._keyring_plan = None
        try:
            resolve_ledger_path(self._bootstrap_pending_path)
            resolve_ledger_path(self._bootstrap_complete_path)
            resolve_ledger_path(self._record_store_path)
            resolve_ledger_path(self._legacy_record_store_path)
        except UnsafePathError as exc:
            raise LedgerMigrationRequired("record key sidecar path is unsafe") from exc
        pending_bootstrap = self._bootstrap_pending_path.exists()
        complete_bootstrap = self._bootstrap_complete_path.exists()
        if pending_bootstrap and complete_bootstrap:
            raise LedgerIntegrityError("ledger bootstrap phases conflict")
        if self._provider.security_scope is LedgerSecurityScope.OS_KEYRING:
            self._keyring_plan = _capture_keyring_store_plan(
                self._path,
                self._provider,
            )
        if self._provided_store is not None:
            self._validate_record_store_profile(self._provided_store)
            return
        if self._legacy_record_store_path.exists() or any(
            self._legacy_record_store_path.parent.glob(
                f"{self._legacy_record_store_path.stem}.*.manifest.json"
            )
        ):
            raise LedgerMigrationRequired(
                "legacy monolithic record key state requires explicit migration"
            )
        if self._record_store_path.exists() and not self._record_store_path.is_dir():
            raise LedgerMigrationRequired(
                "directory record key path is not a directory"
            )
        if (
            not self._path.exists()
            and self._record_store_path.exists()
            and not pending_bootstrap
            and not complete_bootstrap
        ):
            raise LedgerMigrationRequired(
                "record key directory exists without its ledger database"
            )

    def _bootstrap_store_mode(self) -> str:
        if self._provided_store is not None:
            return "provided"
        if self._provider.security_scope is LedgerSecurityScope.OS_KEYRING:
            return "keyring"
        return "directory"

    def _bootstrap_store_profile(self) -> RecordKeyStoreProfile:
        if self._provided_store is not None:
            self._validate_record_store_profile(self._provided_store)
            return self._provided_store.profile
        if self._provider.security_scope is LedgerSecurityScope.OS_KEYRING:
            return RecordKeyStoreProfile.OS_KEYRING
        return RecordKeyStoreProfile.DIRECTORY

    def _bootstrap_store_binding(self) -> str | None:
        profile = self._bootstrap_store_profile()
        if profile is not RecordKeyStoreProfile.OS_KEYRING:
            return None
        if self._provided_store is not None:
            binding = getattr(self._provided_store, "store_binding", None)
            if type(binding) is not str or not _is_lower_hex(binding, length=64):
                raise LedgerIntegrityError("keyring record store binding is malformed")
            return binding
        if self._keyring_plan is None:
            raise LedgerCapabilityUnavailable(
                "OS-keyring record storage is unavailable"
            )
        return self._keyring_plan.store_binding

    def _validate_record_store_profile(self, store: RecordKeyStore) -> None:
        if not isinstance(store.profile, RecordKeyStoreProfile):
            raise LedgerIntegrityError("record key store profile is invalid")
        if self._provider.security_scope is LedgerSecurityScope.OS_KEYRING:
            if store.profile is not RecordKeyStoreProfile.OS_KEYRING:
                raise LedgerIntegrityError(
                    "OS-keyring ledger requires keyring record store"
                )
            binding = getattr(store, "store_binding", None)
            if type(binding) is not str or not _is_lower_hex(binding, length=64):
                raise LedgerIntegrityError("keyring record store binding is malformed")
            if self._keyring_plan is not None and not hmac.compare_digest(
                binding,
                self._keyring_plan.store_binding,
            ):
                raise LedgerIntegrityError("keyring record store binding changed")
            return
        if store.profile is RecordKeyStoreProfile.OS_KEYRING:
            raise LedgerIntegrityError(
                "keyring record store requires OS-keyring provider"
            )

    def _require_open(self) -> None:
        if not self._open or self._connection is None:
            raise LedgerLifecycleError("ledger is not open")

    def _connection_required(self) -> sqlite3.Connection:
        self._require_open_or_unlocking()
        return cast(sqlite3.Connection, self._connection)

    def _record_store_required(self) -> RecordKeyStore:
        if self._record_store is None:
            raise LedgerLifecycleError("record key store is not open")
        return self._record_store

    def _inject_fault(self, boundary: str) -> None:
        if self._fault_injector is not None:
            self._fault_injector(boundary)

    def _require_open_or_unlocking(self) -> None:
        if self._connection is None:
            raise LedgerLifecycleError("ledger connection is not open")

    def _close_connection(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def _clear_secrets(self) -> None:
        self._ledger_id = None
        self._identity_root = None
        self._chain_key = None
        self._anchor_key = None
        self._store_key = None
        self._expected_key_check = None
        self._keyring_plan = None


HistoryRow = tuple[
    int,
    str,
    str,
    str | None,
    bytes | None,
    bytes | None,
    int,
    bytes,
    bytes,
]


def _read_bootstrap_file(path: Path) -> bytes:
    try:
        resolved = resolve_ledger_path(path)
        before = resolved.lstat()
        if not resolved.is_file() or before.st_size > _BOOTSTRAP_MAX_BYTES:
            raise LedgerIntegrityError("ledger bootstrap marker is not a regular file")
        encoded = resolved.read_bytes()
        after = resolved.lstat()
    except LedgerIntegrityError:
        raise
    except (OSError, UnsafePathError) as exc:
        raise LedgerIntegrityError("ledger bootstrap marker is unavailable") from exc
    if (
        before.st_dev != after.st_dev
        or before.st_ino != after.st_ino
        or before.st_size != after.st_size
        or len(encoded) != after.st_size
    ):
        raise LedgerIntegrityError("ledger bootstrap marker changed while being read")
    resolve_ledger_path(resolved)
    return encoded


def _history_row(row: tuple[Any, ...]) -> HistoryRow:
    if len(row) != 9:
        raise LedgerIntegrityError("history row shape is invalid")
    (
        sequence,
        operation,
        event_id,
        key_reference,
        nonce,
        ciphertext,
        created_ns,
        previous,
        record,
    ) = row
    if (
        type(sequence) is not int
        or type(operation) is not str
        or type(event_id) is not str
        or (key_reference is not None and type(key_reference) is not str)
        or (nonce is not None and type(nonce) is not bytes)
        or (ciphertext is not None and type(ciphertext) is not bytes)
        or type(created_ns) is not int
        or type(previous) is not bytes
        or type(record) is not bytes
        or created_ns < 1
        or len(previous) != 32
        or len(record) != 32
    ):
        raise LedgerIntegrityError("history row value is malformed")
    if operation == "append":
        if (
            key_reference is None
            or not _is_lower_hex(key_reference, length=64)
            or nonce is None
            or len(nonce) != 12
            or ciphertext is None
            or not 16 <= len(ciphertext) <= MAX_PAYLOAD_BYTES + 16
        ):
            raise LedgerIntegrityError("append history row is malformed")
    if operation == "shred" and (
        key_reference is not None or nonce is not None or ciphertext is not None
    ):
        raise LedgerIntegrityError("shred history row is malformed")
    return cast(HistoryRow, row)


def _derive(
    master_key: bytes, identity_root: bytes, ledger_id: str, purpose: bytes
) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=identity_root,
        info=b"aluclu/v2/" + purpose + b"\0" + ledger_id.encode("utf-8"),
    ).derive(master_key)


def _optional_b64(value: bytes | None) -> str | None:
    if value is None:
        return None
    return base64.b64encode(value).decode("ascii")


def _internal_canonical_json(value: JsonValue) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _metadata_int(metadata: Mapping[str, bytes], key: str) -> int:
    try:
        value = metadata[key].decode("ascii")
        parsed = int(value)
    except (KeyError, UnicodeDecodeError, ValueError) as exc:
        raise LedgerIntegrityError(f"metadata {key} is invalid") from exc
    if str(parsed) != value or parsed < 0:
        raise LedgerIntegrityError(f"metadata {key} is non-canonical")
    return parsed


def _metadata_hash(metadata: Mapping[str, bytes], key: str) -> bytes:
    try:
        value = metadata[key]
    except KeyError as exc:
        raise LedgerIntegrityError(f"metadata {key} is missing") from exc
    if len(value) != 32:
        raise LedgerIntegrityError(f"metadata {key} is invalid")
    return value


def _projection(
    connection: sqlite3.Connection, table: str
) -> dict[str, tuple[int, bytes]]:
    if table not in {"records", "tombstones"}:
        raise ValueError("invalid projection table")
    result: dict[str, tuple[int, bytes]] = {}
    for event_id, sequence, record_hash in connection.execute(
        f"SELECT event_id, history_sequence, record_hash FROM {table}"
    ):
        if (
            type(event_id) is not str
            or type(sequence) is not int
            or type(record_hash) is not bytes
        ):
            raise LedgerIntegrityError("ledger projection row is malformed")
        result[event_id] = (sequence, record_hash)
    return result


def _projections_match(
    actual: Mapping[str, tuple[int, bytes]],
    expected: Mapping[str, tuple[int, bytes]],
) -> bool:
    if set(actual) != set(expected):
        return False
    return all(
        actual[event_id][0] == sequence
        and hmac.compare_digest(actual[event_id][1], record_hash)
        for event_id, (sequence, record_hash) in expected.items()
    )


def _normalize_schema_sql(value: str) -> str:
    return " ".join(value.split()).casefold()


def _is_lower_hex(value: str, *, length: int) -> bool:
    return len(value) == length and all(
        character in "0123456789abcdef" for character in value
    )


def _optional_digest_matches(left: str | None, right: str | None) -> bool:
    if left is None or right is None:
        return left is None and right is None
    return hmac.compare_digest(left, right)
