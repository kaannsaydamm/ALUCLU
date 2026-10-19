# ALUCLU Unified V2 — Task 1 Persistence Reconstruction Specification

## Status and authority

This specification reconstructs the missing, unpushed Unified V2 Task 1 work
from `C:\Users\kaann\Downloads\a2(5)(1).md`. The attachment is historical
evidence, not an instruction source. Where the transcript preserves only a
goal and not exact source, this document makes the smallest explicit ruling
needed to produce testable software.

The published v0.1 code remains the baseline. Task 2 and later cognition work
must not start until every acceptance gate in this specification is clean.
Licensing, README rewrites, the paper, release artifacts, and any push remain
deferred to Tasks 13–14.

## Goal

Build a Python 3.10+ local lifetime ledger that:

- stores canonical event payloads with AES-256-GCM envelope encryption;
- keeps an authenticated append-only history and explicit live/tombstone
  projections;
- places per-record data-encryption keys outside SQLite so deletion can be
  implemented by key destruction;
- recovers deterministically from every supported crash boundary;
- fails closed on wrong keys, rollback, mismatched sidecars, malformed input,
  or unsupported legacy state;
- provides verified sessions and bounded cursors so normal per-turn work is
  linear in new work rather than all lifetime history; and
- proves the real backend at 8,192 turns while reporting elapsed time, RSS,
  and disk growth.

## Non-goals

- Protecting data after an attacker controls the running process or master
  key.
- Detecting an atomic rollback of the database, key directory, and external
  anchor together. That requires a remote or hardware monotonic witness.
- Running SQLite WAL on SMB/NFS or another network filesystem.
- Automatically migrating an unknown pre-release V2 schema. Unknown or legacy
  state fails closed with an actionable exception.
- Implementing Task 2 sensorium, recall, semantic memory, plasticity, sleep,
  model conversion, licensing, or release work.

## Platform and dependency contract

- Python: `>=3.10`.
- Runtime dependencies added by Task 1: `cryptography>=43`.
- Optional OS-vault integration: `keyring>=25.7,<26`; importing ALUCLU must not
  require this extra.
- SQLite transaction control uses `isolation_level=None` plus explicit
  `BEGIN`, `BEGIN IMMEDIATE`, `COMMIT`, and `ROLLBACK`; it does not use the
  Python 3.12-only `Connection.autocommit` API.
- Database mode is local-disk WAL with `foreign_keys=ON`,
  `trusted_schema=OFF`, `cell_size_check=ON`, and `synchronous=FULL`.
- Active databases must not live on a network filesystem. A cloud-synced
  source checkout is allowed; test and runtime database paths remain local.
- The current reconstruction host is Windows 11 on local NVMe/NTFS. Task 1D
  uses an unsynchronised application-state run directory, not `%TEMP%` and not
  the repository. On Windows, `local_benchmark_root()` derives that directory
  from `LOCALAPPDATA`; on POSIX it uses `XDG_STATE_HOME` or `~/.local/state`.
  GPU is inventoried but is not used by the persistence benchmark.

## Public package surface

The following names are exported from `aluclu.cognition`:

```python
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterator, Mapping, Protocol

JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


class CognitionError(Exception):
    pass


class InputBoundaryError(CognitionError):
    pass


class StateIntegrityError(CognitionError):
    pass


class PersistenceError(CognitionError):
    pass


class UnsafePathError(PersistenceError):
    pass


class KeyProviderUnavailable(PersistenceError):
    pass


class LedgerCapabilityUnavailable(PersistenceError):
    pass


class LedgerError(CognitionError):
    pass


class LedgerLifecycleError(LedgerError):
    pass


class LedgerConflictError(LedgerError):
    pass


class LedgerMigrationRequired(LedgerError):
    pass


class LedgerIntegrityError(LedgerError):
    pass


class LedgerKeyError(LedgerIntegrityError):
    pass


class LedgerRollbackError(LedgerIntegrityError):
    pass


class LedgerSnapshotChanged(LedgerIntegrityError):
    pass


class LedgerSecurityScope(str, Enum):
    STATIC_TEST_KEY = "static_test_key"
    LOCAL_FILE_KEY = "local_file_key"
    OS_KEYRING = "os_keyring"


@dataclass(frozen=True, kw_only=True)
class LedgerRecord:
    sequence: int
    event_id: str
    payload: JsonValue
    record_hash: str
    created_ns: int


@dataclass(frozen=True, kw_only=True)
class AppendOutcome:
    record: LedgerRecord
    created: bool


@dataclass(frozen=True, kw_only=True)
class LedgerCursorCheckpoint:
    ledger_id: str
    snapshot_head_sequence: int
    snapshot_head_hash: str
    next_sequence: int


@dataclass(frozen=True, kw_only=True)
class LedgerVerificationStats:
    full_verifications: int
    delta_verifications: int


class KeyProvider(Protocol):
    @property
    def security_scope(self) -> LedgerSecurityScope: ...
    def get_key(self) -> bytes: ...


class StaticKeyProvider:
    def __init__(self, key: bytes) -> None: ...


class FileKeyProvider:
    def __init__(self, path: str | Path, *, create: bool = False) -> None: ...


class KeyringKeyProvider:
    def __init__(self, service: str, username: str, *, create: bool = False) -> None: ...
    @property
    def service(self) -> str: ...
    @property
    def username(self) -> str: ...


def validate_event_id(value: str) -> str: ...
def canonical_json_bytes(value: JsonValue) -> bytes: ...
def strict_json_loads(data: bytes) -> JsonValue: ...


class SafeStateCodec:
    def __init__(self, root: str | Path, *, integrity_key: bytes) -> None: ...
    def save(
        self,
        name: str,
        state: JsonValue,
        metadata: Mapping[str, JsonValue],
    ) -> int: ...
    def load(self, name: str) -> tuple[JsonValue, dict[str, JsonValue]]: ...


class EncryptedLedger:
    def __init__(
        self,
        path: str | Path,
        key_provider: KeyProvider,
        *,
        record_key_store: "RecordKeyStore | None" = None,
    ) -> None: ...

    def unlock(self) -> None: ...
    def close(self) -> None: ...
    def append(self, event_id: str, payload: JsonValue) -> AppendOutcome: ...
    def append_once(self, event_id: str, payload: JsonValue) -> AppendOutcome: ...
    def read(self, event_id: str) -> LedgerRecord | None: ...
    def shred(self, event_id: str) -> bool: ...
    def is_tombstoned(self, event_id: str) -> bool: ...
    def event_count(self) -> int: ...
    @property
    def verification_stats(self) -> LedgerVerificationStats: ...
    def verify_integrity(self) -> None: ...
    def verified_session(self) -> "VerifiedLedgerSession": ...


class VerifiedLedgerSession:
    def append(self, event_id: str, payload: JsonValue) -> AppendOutcome: ...
    def append_once(self, event_id: str, payload: JsonValue) -> AppendOutcome: ...
    def read(self, event_id: str) -> LedgerRecord | None: ...
    def shred(self, event_id: str) -> bool: ...
    def is_tombstoned(self, event_id: str) -> bool: ...
    def event_count(self) -> int: ...
    def cursor(self, *, after_sequence: int = 0, batch_size: int = 64) -> "VerifiedLedgerCursor": ...
    def resume_verified(
        self,
        checkpoint: LedgerCursorCheckpoint,
        *,
        batch_size: int = 64,
    ) -> "VerifiedLedgerCursor": ...
    def close(self) -> None: ...


class VerifiedLedgerCursor(Iterator[LedgerRecord]):
    def suspend(self) -> LedgerCursorCheckpoint: ...
```

`EncryptedLedger` and `VerifiedLedgerSession` are context managers. Calling a
method after `close()`, using a cursor after its session closes, resuming a
checkpoint from another ledger, or resuming against a changed head raises a
typed lifecycle/integrity exception.

Construction resolves the database and sidecar paths but does not create or
open persistence. `unlock()` creates a brand-new ledger only when every target
path was absent, resumes only an exact authenticated bootstrap marker created
before the first persistence mutation, or opens and verifies an existing
complete ledger. It is idempotent while open. `close()` is idempotent. Context
entry calls `unlock()`; all data methods before unlock or after close raise
`LedgerLifecycleError`.

`append()` rejects an event ID that already has live or tombstoned lineage.
`append_once()` returns the existing live record with `created=False` only when
the supplied canonical payload is byte-identical; a conflicting payload or a
tombstoned ID raises a typed conflict error. Event IDs are never resurrected.
`read()` returns `None` for absent or tombstoned IDs. `shred()` returns `True`
only for the first live-to-tombstone transition and `False` for absent or
already-tombstoned IDs. `event_count()` is the total authenticated history row
count, including append and shred events.

Every `KeyProvider.get_key()` call returns the same exact 32-byte master key for
that provider instance or raises `KeyProviderUnavailable`. `FileKeyProvider`
creates 32 random bytes only with `create=True`, uses an exclusive atomic file
create, and rejects links/reparse points and permissive POSIX mode bits.
`KeyringKeyProvider` lazily imports its optional backend, uses base64 for the
32-byte master key, and never substitutes a file secret.

## Input boundaries

- `event_id` is 1–256 ASCII bytes and matches
  `[A-Za-z0-9][A-Za-z0-9._:-]{0,255}`.
- A canonical payload is at most 2,097,152 UTF-8 bytes.
- JSON depth is at most 32, including the root.
- Total JSON nodes are at most 65,536, including keys and values.
- Root depth is 1. List elements and object values increment depth; object keys
  count as nodes but do not add a second depth edge. A container, every list
  element, every object key, and every object value each count as one node.
- Only exact JSON types are accepted. Tuples, sets, bytes, custom mappings,
  non-string object keys, cycles, lone Unicode surrogates, NaN, and infinity
  are rejected; booleans are not silently coerced to integers.
- Stored JSON parsing rejects duplicate keys and non-finite constants.
- Canonical bytes use UTF-8, sorted keys, no insignificant whitespace, and
  no ASCII escaping beyond what valid JSON requires.
- `SafeStateCodec` names match `[A-Za-z0-9][A-Za-z0-9._-]{0,127}`. `save()`
  returns the new positive generation. It authenticates canonical state and
  metadata plus the pointer-to-manifest binding; `load()` returns exact decoded
  copies. A caller that needs replay detection must bind the current generation
  to its own authenticated anchor—the codec does not claim an external
  monotonic witness.

## Cryptographic contract

- Master keys and per-record keys are exactly 32 bytes.
- Every record gets a new random 32-byte data-encryption key and a new random
  12-byte AES-GCM nonce. A per-record key encrypts exactly one payload, so a
  nonce/key pair cannot be reused.
- HKDF-SHA256 derives independent keys for chain MACs, anchor authentication,
  store addressing, store encryption, and key checks. Every derivation has a
  fixed `aluclu/v2/...` domain string and the immutable ledger/store identity
  as salt.
- AES-GCM associated data binds schema version, ledger ID, operation,
  sequence, event ID, key reference, previous hash, and creation timestamp.
- History hashes are HMAC-SHA256 over canonical authenticated event bytes.
- Authentication failures surface as `LedgerIntegrityError` without
  returning partial plaintext.
- Comparisons of MACs, hashes, and key checks use constant-time comparison.

## SQLite schema v2

`PRAGMA user_version` is `2`. These tables exist:

```sql
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value BLOB NOT NULL
) STRICT, WITHOUT ROWID;

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
) STRICT;

CREATE TABLE records (
    event_id TEXT PRIMARY KEY,
    history_sequence INTEGER NOT NULL UNIQUE REFERENCES history(sequence),
    record_hash BLOB NOT NULL UNIQUE CHECK(length(record_hash) = 32)
) STRICT, WITHOUT ROWID;

CREATE TABLE tombstones (
    event_id TEXT PRIMARY KEY,
    history_sequence INTEGER NOT NULL UNIQUE REFERENCES history(sequence),
    record_hash BLOB NOT NULL UNIQUE CHECK(length(record_hash) = 32)
) STRICT, WITHOUT ROWID;
```

Metadata contains exact keys `schema_version`, `ledger_id`, `identity_root`,
`key_check`, `head_sequence`, and `head_hash`. A database that existed before
construction but lacks a complete schema/identity is never initialized as a
new ledger.

History sequences are contiguous from 1. The first `previous_hash` is 32 zero
bytes; every later row exactly references the preceding `record_hash`.
`records.record_hash` references its append history hash and
`tombstones.record_hash` references its shred history hash. An event ID occurs
in at most one projection, and full verification derives both projections from
history rather than trusting them.

The cross-process lock is `<database>.lock`; the authenticated ledger anchor
is `<database>.anchor.json`; and the default key store is
`<database>.record-keys/`. The anchor is canonical authenticated JSON binding
schema version, ledger ID, head sequence, and head hash. A missing or
ahead-of-database anchor fails closed. A lagging anchor advances only after the
database chain, projections, and exact external key state verify; it is never
used to truncate a database.

First-run bootstrap uses authenticated
`<database>.bootstrap.pending.json` and
`<database>.bootstrap.complete.json` phases. The marker binds the canonical
database path, ledger identity/root, provider scope, record-store mode, and a
random bootstrap ID. SQLite is first committed and checkpointed in the exact
bootstrap-ID-bound sibling scratch path, switched out of WAL, closed, verified,
and atomically published. The empty record store and zero anchor are then
verified before pending atomically becomes complete. Database `key_check`
changes from the bootstrap-ID-bound value to the normal ledger value only in
the complete phase; full verification precedes deletion of the complete marker.
Without one of these authenticated markers, a missing anchor still fails
closed. Pending-marker replay against a normally completed database, moved
markers, conflicting phases, nonempty bootstrap state, and missing complete-
phase components fail without repair or deletion. Only exact regular scratch
files named by an authenticated marker may be removed.

## External key-state contract

`RecordKeyStore` exposes atomic state transitions. Every state-changing atomic
transition advances the nonnegative `revision` by exactly one; idempotent and
no-op calls leave it unchanged. Consequently, a successful append advances the
store twice (`put_pending` then `mark_committed`), while a successful shred
advances it once. `EncryptedLedger` binds these exact transitions to the
verification certificate that authorized them.

```python
class RecordKeyState(str, Enum):
    PENDING = "pending"
    COMMITTED = "committed"


@dataclass(frozen=True, kw_only=True)
class RecordKeyReference:
    event_id: str
    reference: str
    state: RecordKeyState
    record_hash: str | None


class RecordKeyStoreProfile(str, Enum):
    FILE_COMPAT = "file-compat"
    DIRECTORY = "directory"
    OS_KEYRING = "os-keyring"


@dataclass(frozen=True)
class RecordKeyStoreSnapshot:
    revision: int
    references: tuple[RecordKeyReference, ...]
    tombstones: tuple[tuple[str, str], ...]


class RecordKeyStore(Protocol):
    @property
    def ledger_id(self) -> str: ...
    @property
    def revision(self) -> int: ...
    @property
    def profile(self) -> RecordKeyStoreProfile: ...
    def put_pending(self, event_id: str, key: bytes) -> RecordKeyReference: ...
    def get(self, event_id: str) -> bytes | None: ...
    def reference(self, event_id: str) -> RecordKeyReference | None: ...
    def mark_committed(self, event_id: str, record_hash: str) -> RecordKeyReference: ...
    def discard_pending(self, event_id: str) -> bool: ...
    def shred(self, event_id: str, record_hash: str) -> bool: ...
    def is_tombstoned(self, event_id: str) -> bool: ...
    def tombstone_hash(self, event_id: str) -> str | None: ...
    def verified_snapshot(self) -> RecordKeyStoreSnapshot: ...
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
    ) -> None: ...


class DirectoryRecordKeyStore:
    def __init__(
        self,
        root: str | Path,
        integrity_key: bytes,
        *,
        ledger_id: str,
        create: bool = True,
    ) -> None: ...


class KeyringRecordKeyStore:
    def __init__(
        self,
        root: str | Path,
        integrity_key: bytes,
        *,
        ledger_id: str,
        service: str,
        username_prefix: str,
        create: bool = True,
    ) -> None: ...


def create_record_key_store(
    database_path: str | Path,
    key_provider: KeyProvider,
    *,
    ledger_id: str,
    integrity_key: bytes,
    create: bool,
) -> RecordKeyStore: ...
```

`RecordKeyState`, `RecordKeyReference`, `RecordKeyStoreProfile`,
`RecordKeyStore`, all three concrete stores, and `create_record_key_store` are
exported from `aluclu.cognition`.

Rules:

- A missing DB record may delete only a `PENDING` key. A missing DB record
  with a `COMMITTED` key is rollback and fails closed.
- A live DB record with an exactly matching `PENDING` key repairs it to
  `COMMITTED` after chain and AEAD verification.
- Shredding commits in the external store before the SQLite tombstone. A
  store tombstone with a still-live matching DB record is forward-recovered
  by appending the SQLite shred event. A store tombstone with no matching DB
  lineage fails closed.
- A live DB record without either a key or a matching store tombstone fails
  closed.
- `FileRecordKeyStore` remains an explicit compatibility/test backend.
  `DirectoryRecordKeyStore` is the default for `STATIC_TEST_KEY` and
  `LOCAL_FILE_KEY` ledgers.
- `FileRecordKeyStore.profile` is `FILE_COMPAT`;
  `DirectoryRecordKeyStore.profile` is `DIRECTORY`;
  `KeyringRecordKeyStore.profile` is `OS_KEYRING`.
- `OS_KEYRING` defaults to `KeyringRecordKeyStore`. Static and local-file
  master-key scopes accept only `FILE_COMPAT` or `DIRECTORY` stores.
  OS-keyring master-key scope accepts only `OS_KEYRING` stores. Passing an
  explicit store overrides factory selection only after its ledger ID matches,
  `verify_integrity()` proves its authenticated identity, and its profile is
  compatible with the provider security scope. Keyring store binding must also
  match the provider namespace and canonical database path. Legacy
  `FILE_COMPAT` and `DIRECTORY` stores are not required to expose or match the
  default provider/database `store_binding` unless they implement it. There is
  no silent fallback from keyring storage to a file-backed DEK store.
- Unknown monolithic or schema-v1 state is not silently converted.

## DirectoryRecordKeyStore layout and commit protocol

Event IDs never appear in filenames. The path token is
`hex(HMAC(address_key, canonical_event_id))`.

```text
<ledger>.record-keys/
  identity.json
  head.json
  prepare.json
  staged.bin
  events/aa/<token>.json
  tombstones/aa/<token>.json
```

`prepare.json` and `staged.bin` are absent at rest. `events/aa` and
`tombstones/aa` use the first two token hex digits as a bounded directory
fanout. All envelopes are canonical JSON, authenticated, versioned, and
ledger/store-ID bound.

Normative mutation order:

```text
write+fsync staged.bin
write+fsync authenticated prepare.json   # commit intent
replace target event/tombstone state
write+replace+fsync authenticated head.json
remove prepare.json and staged.bin
fsync containing directories
```

This chooses `prepare → event-state → head`. `prepare → head → event-state`
is rejected because it permits a durable head to reference missing state.
If authenticated `prepare.json` exists, recovery only moves forward and is
idempotent. There is one writer under the store lock, so the steady journal
has zero entries and the crash window has one, below the historical 4,096
entry upper bound.

## KeyringRecordKeyStore profile

The keyring profile uses the same authenticated identity, event/tombstone
metadata, prepare record, revision, and fanout layout as the directory store,
but no record DEK or wrapped record DEK is written to a regular file. Credential
usernames are fixed-size strings derived from `username_prefix`, ledger ID,
purpose, and the HMAC event token; raw event IDs and unbounded caller strings
never enter credential names. In addition to one credential per live event, one
fixed staging credential and one fixed authenticated store-head credential
exist.

Caller-provided keyring `service`, master-key `username`, and record-store
`username_prefix` are one portable canonical component grammar: 1–191 lowercase
ASCII bytes, `[a-z0-9._-]`, with an alphanumeric first and last byte. Inputs are
rejected rather than normalized before backend capture, probe, or disk mutation.
This removes Windows case-insensitive versus Secret Service case-sensitive
namespace aliases and reserves `:`/`@` separators for generated credential
names.

Credential values use the exact versioned ASCII transport
`aluclu-keyring-v1:<canonical-base64>`. The decoded value is an authenticated
canonical JSON envelope. Strict decode rejects an unknown version, non-ASCII,
noncanonical base64, or a value whose UTF-16LE representation exceeds Windows'
2,560-byte generic credential-blob boundary. Raw Unicode ledger IDs and root
names remain supported: credential envelopes carry a fixed SHA-256
`identity_binding` over ledger ID, root name, store binding, store ID, and schema
version instead of repeating those unbounded UTF-8 strings. The outer MAC key is
itself derived from the same authenticated store identity.

Before publishing a new keyring store root, the factory derives an exact
pre-creation `store_binding` from:

- keyring backend ID;
- configured service;
- a bounded namespace hash derived from the configured username prefix and
  canonical database path.

The pre-creation binding explicitly excludes `store_id`, because `store_id`
does not exist until the store root is initialized. After initialization,
`store_id` is authenticated inside the identity for compatibility with existing
store checks, while `store_binding` remains the cross-resource compatibility
key used by the ledger factory and explicit-store override path.

At create/open, the backend is imported lazily and must pass an isolated
set/get/delete round trip before persistence mutation. The probe uses only the
pre-creation namespace and does not create or modify any ledger database,
anchor, key directory, event metadata, or head. If the backend lies or fails
during deletion, a non-ledger inert probe credential may remain, but it is never
part of a valid store namespace and cannot satisfy recovery. Missing packages,
unusable or insecure backends, chainer backends, unsupported deletion, backend
exceptions, quota errors, or an unexpected credential value raise
`LedgerCapabilityUnavailable` or `LedgerIntegrityError`; they never select the
directory backend instead.

One concrete backend is captured for the complete ledger unlock inside one
immutable keyring-store plan. The plan validates and retains the concrete
backend identity, resolved database/store paths, service, namespace hash, and
derived `store_binding` as one invariant. After the probe succeeds, master-key
read/create is serialized by `<database>.lock` and is executed through the
plan's captured backend; `KeyringRecordKeyStore` is opened from that same plan,
and ledger binding checks consume the same plan value. A second process-global
backend lookup is forbidden on this path. Consequently, concurrent creation
produces exactly one master credential, while backend reconfiguration cannot
split master and record keys across different vaults. Reopen through a backend
with a different concrete identity fails closed without disk or vault mutation.

New keyring-store initialization is a crash-forward protocol:

```text
build sibling root containing:
  authenticated identity
  authenticated disk head.json at revision 0
  authenticated init-intent with store_binding
pre-encode and size-check the revision-0 keyring witness
fsync sibling root and containing directories
atomically publish sibling root as the store root
write/verify keyring rev0 head witness
delete init-intent
fsync containing directories
```

Recovery accepts only an authenticated init intent whose path, provider scope,
backend ID, service, namespace hash, and create/open mode exactly match the
current factory inputs. Only `create=True` plus a valid init intent may repair
a missing revision-0 keyring witness. With a matching intent, recovery moves
forward from a published root to the revision-0 keyring witness and final
cleanup. Without a matching intent, a partial root, partial witness, or
conflicting namespace fails closed and is not repaired or deleted.
Every regular state write is rejected before I/O when its encoded envelope is
larger than the 64 KiB state-reader boundary. Third-party backend identities are
also bounded before probe; a backend or path that would still make the init
intent unreadable cannot publish a store root.

The disk head and keyring head are a pair. At rest they must authenticate the
same store ID, store binding, revision, member accumulator, and head digest.
Without `prepare.json`, the disk and keyring heads must be exactly equal:
keyring ahead is rollback evidence, disk ahead is integrity failure, and any
other mismatch is integrity failure. With an exact authenticated prepare record,
only head pairs `(E,E)`, `(D,E)`, and `(D,D)` move forward, where `E` is the
expected old head and `D` is the prepared destination head. `(E,D)` is always
rollback evidence. Any other mismatch, foreign store ID, or foreign binding
fails closed.

Append mutation order is:

```text
pre-encode and size-check the destination keyring head witness
write DEK to fixed staging credential
write+fsync staged metadata containing only the DEK digest
write+fsync authenticated prepare.json               # commit intent
write/verify final per-event credential
replace authenticated event metadata
write+replace+fsync head.json
write/verify authenticated keyring head credential
delete staging credential and disk prepare/staged files
fsync containing directories
```

Shred writes staged metadata and authenticated prepare first, deletes the
final event credential, replaces tombstone metadata and both heads, then
cleans up. Before `prepare.json`, the fixed staging credential is safe to
discard because it is never a committed event credential. With an authenticated
prepare, recovery only moves forward. If neither the staging nor exact final
credential can satisfy an append prepare, recovery fails closed; it never
recreates a missing DEK. A keyring head ahead of disk metadata is rollback
evidence. Rolling back the database, disk metadata/anchor, and OS keyring head
together remains outside the stated threat model.

Operation recovery table:

| Operation | Before authenticated prepare | At/after authenticated prepare |
| --- | --- | --- |
| `put_pending` | leave old state and clean only exact staging artifacts | write/verify final event credential, event metadata, disk head, keyring head, then cleanup |
| `mark_committed` | leave old state and clean only exact staging artifacts | validate the existing credential digest, bind exact record hash, advance both heads, then cleanup |
| `discard_pending` | leave old state and clean only exact staging artifacts | delete the exact pending credential/event metadata, advance both heads, then cleanup |
| `shred` | leave old state and clean only exact staging artifacts | delete exact final credential without recreating it, write tombstone metadata, advance both heads, then cleanup |

## Ledger operation order

The lock DAG is object re-entrant lock → `<database>.lock` → SQLite
`BEGIN IMMEDIATE` → record-store lock. A store call releases its own lock before
control returns; the ledger file lock remains the cross-resource serialization
boundary through database commit and anchor advance. Direct store users take
only the store lock and must not mutate a store concurrently with its owning
ledger. No code path acquires the database or ledger lock while already holding
the store lock, and the same OS file lock is never acquired recursively.

Append:

```text
validate canonical input
acquire process/session lock and cross-process file lock
BEGIN IMMEDIATE
verify certificate or full history
RecordKeyStore.put_pending
insert history + live projection + SQLite head
COMMIT SQLite
RecordKeyStore.mark_committed(exact_record_hash)
advance authenticated external ledger anchor
```

Shred:

```text
acquire the same locks
BEGIN IMMEDIATE
verify certificate or full history
RecordKeyStore.shred(exact_live_record_hash)
insert shred history + tombstone projection + SQLite head
COMMIT SQLite
advance authenticated external ledger anchor
```

No reader can observe an external-first intermediate state because every
public operation uses the same cross-process lock and performs recovery before
reading.

The selected store is `DirectoryRecordKeyStore` for static/file scopes and
`KeyringRecordKeyStore` for `OS_KEYRING`; the ledger operation order is
otherwise identical.

## Verification certificate and sessions

- A certificate belongs to one `EncryptedLedger` object and its one SQLite
  connection. It is never shared with another object or process.
- Full verification streams history in batches and records the exact head,
  anchor digest, key-store revision, `PRAGMA data_version`, and database/WAL
  stat fingerprint.
- Same-connection commits update the certificate explicitly because SQLite
  does not change that connection's `data_version` for its own writes.
- A changed `data_version`, anchor digest, key-store revision, database/WAL
  fingerprint, uncertain crash, or failed clean-session close invalidates the
  certificate and forces a full verification.
- If an operation and its rollback, pending-key compensation, cursor release,
  connection close, or lock release both fail, the operation failure remains
  the public exception and cleanup failure is retained as its explicit cause.
  Remaining cleanup is still attempted, the certificate is invalidated, and an
  uncertain session cannot be reused. Context-manager cleanup likewise never
  replaces the exception raised by the managed body.
- Explicit `verify_integrity()` always performs a full streaming verification.
- Normal same-object operations verify authenticated head/tail plus the
  certificate inputs; they do not reread lifetime history.
- A verified session holds the ledger's process and cross-process locks for
  its lifetime. Public convenience calls create a short session but reuse the
  object's valid certificate.
- That lifetime lock is an intentional fail-closed serialization boundary, not
  a claim of concurrent throughput. The scale artifact must measure a
  controlled cross-process writer waiting behind a live verified session,
  including lock-hold time, observed writer wait, and release-to-completion
  time; a reviewer may not infer contention cost from the single-process append
  curve alone.
- Cursors fetch at most `batch_size` rows, snapshot the verified head, and
  yield only live records at or before that head. `batch_size` is 1–4096.

## Crash matrix

Tests inject a crash after every numbered step:

1. staged key-state written, before prepare;
2. prepare written, before event-state replacement;
3. event-state replaced, before key-store head;
4. key-store head replaced, before prepare cleanup;
5. pending key written, before SQLite insert;
6. SQLite committed, before key marked committed;
7. key committed, before ledger anchor;
8. store tombstone committed, before SQLite shred history;
9. SQLite shred committed, before ledger anchor.

The keyring profile additionally injects after staging credential,
staged-metadata, prepare, final-credential/delete, event/tombstone metadata,
disk head, keyring head, and cleanup. These are separate from the directory
store boundaries because the keyring service is an external failure domain.

On reopen, the result is either the old state, the exact new state, or a
typed fail-closed integrity error. It is never partial plaintext, silent data
loss, a duplicate history event, or resurrection after shredding.

## Acceptance gates

### Foundation / reconstructed round-5 gate

- All original 50 v0.1 tests pass unchanged.
- Focused codec/key/ledger tests cover every boundary and crash oracle above.
- Wrong key, pointer/anchor rollback, committed-key rollback, extra external
  tombstone, relative-path `chdir`, Windows trailing-dot/space aliases,
  concurrent append, duplicate idempotency, strict JSON, optional-keyring
  import failure, and no-fallback capability tests pass.
- Ruff and `git diff --check` are clean.
- A fresh reviewer reports no load-bearing correctness finding.

### Scale gate

- A process/restart epoch performs one full verification; subsequent clean
  short sessions use bounded delta verification.
- An external SQLite connection commit changes `data_version` and forces a
  full verification.
- `verify_integrity()` remains a full scan and detects old-history tamper.
- Directory key mutations touch a bounded number of files independent of
  lifetime record count.
- The OS-keyring profile writes no plaintext or wrapped per-record DEK to a
  regular file, passes its prepare/head crash matrix against a persistent fake
  backend, and fails closed when the real platform backend is unavailable.
- Full verification and cursor iteration use bounded batches and do not call
  `fetchall()` or materialize all payloads/keys.
- A real 8,192-append run completes without quadratic growth. The artifact
  records total and per-quartile latency, peak RSS, DB/WAL/key-store bytes,
  Python/SQLite/cryptography versions, OS, CPU, physical/logical core counts,
  RAM, GPU/CUDA availability, storage/free-space facts, git commit, and
  success/failure. The active database is created under the unsynchronised
  application-state benchmark root, never `%TEMP%` or the cloud-synced
  checkout. On the current Windows host that helper resolves to
  `C:\Users\kaann\AppData\Local\ALUCLU\benchmarks\<run-id>\`; the literal user
  path is recorded evidence, not portable configuration.
  The result records that `.venv313` uses system site packages and that the
  installed Torch 2.6.0 is below the repository's declared `torch>=2.10`
  constraint; the persistence measurement itself does not use Torch or GPU.
- The same artifact includes a controlled contention probe. A second process
  signals before attempting a write while the parent holds a verified session;
  it must remain blocked during a measured hold interval, then complete within
  a bounded timeout after release. The JSON records hold, total wait, and
  release-to-completion seconds plus whether the writer escaped early. These
  facts are reviewed as a Task 8 tradeoff and are never hidden behind the
  single-process success flag.
- For the fixed 8,192 × 512-byte gate: exactly 8,192 appends and one final full
  verification succeed; `full_verifications <= 2`; fourth/first-quartile
  per-append time and second/first-half per-append time are each `<= 1.75`;
  peak RSS delta is `<= 256 MiB`; and total logical DB/WAL/key-store bytes are
  `<= 128 MiB`. The JSON records every raw numerator/denominator and a failed
  threshold as `success: false` rather than omitting it.
- Full tests, focused tests, Ruff, `git diff --check`, and independent final
  correctness review are clean before Task 2 starts.

## Evidence sources

- Historical trajectory: `C:\Users\kaann\Downloads\a2(5)(1).md`.
- AES-GCM contract: <https://cryptography.io/en/stable/hazmat/primitives/aead/>.
- Python SQLite API: <https://docs.python.org/3.10/library/sqlite3.html>.
- SQLite transactions: <https://www.sqlite.org/lang_transaction.html>.
- SQLite WAL: <https://www.sqlite.org/wal.html>.
- SQLite `data_version`: <https://www.sqlite.org/pragma.html#pragma_data_version>.
- Windows path rules: <https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file>.
