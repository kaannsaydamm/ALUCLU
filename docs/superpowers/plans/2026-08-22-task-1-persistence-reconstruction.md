# Task 1 Persistence Reconstruction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reconstruct the missing Unified V2 encrypted cognition ledger and
finish its independently reviewed 8,192-turn scale gate before Task 2 begins.

**Architecture:** Canonical JSON payloads are envelope-encrypted with a unique
per-record AES-256-GCM key. SQLite stores authenticated append-only history and
live/tombstone projections; per-record keys live in a crash-forward external
store. A ledger-object-local verification certificate and lock-owning sessions
turn normal operations into bounded delta work while explicit integrity checks
remain streaming full scans.

**Tech Stack:** Python 3.10+, stdlib `sqlite3`, `hashlib`, `hmac`, `json`,
`pathlib`, `threading`, `cryptography` AESGCM/HKDF, optional `keyring`, pytest,
Ruff.

**Spec:** `docs/superpowers/specs/2026-08-22-task-1-persistence-reconstruction.md`

## Global Constraints

- Preserve all 50 published v0.1 tests unchanged.
- Do not implement Task 2 or later modules in this plan.
- Do not change `LICENSE`, READMEs, paper files, release metadata, or push.
- Python remains `>=3.10`; do not use `sqlite3.Connection.autocommit`.
- `event_id`: 1–256 ASCII bytes, regex
  `[A-Za-z0-9][A-Za-z0-9._:-]{0,255}`.
- Payload: at most 2,097,152 canonical UTF-8 bytes, depth 32, nodes 65,536.
- Master and record keys: exactly 32 bytes; AES-GCM nonce: 12 fresh random
  bytes; all contextual identity is AAD-bound.
- SQLite schema is v2 and uses explicit transactions, local-disk WAL,
  `synchronous=FULL`, `foreign_keys=ON`, `trusted_schema=OFF`, and
  `cell_size_check=ON`.
- Default record-key backend for new ledgers is `DirectoryRecordKeyStore`.
  `OS_KEYRING` instead selects `KeyringRecordKeyStore`; a failed keyring
  capability check never falls back to disk DEKs. Unknown/legacy state fails
  closed; no guessed migration.
- Normative external-store mutation order is
  `staged → prepare → event-state → head → cleanup`.
- A verification certificate is object/connection-local and is never shared.
- `verify_integrity()` always performs a streaming full verification.
- Every production behavior begins with a failing real-code test and is seen
  fail for the intended reason before implementation.
- Every task ends with focused tests, the complete suite, Ruff, diff-check,
  a Lore-protocol commit, and an independent task review.

---

### Task 0: Planning checkpoint and evidence workspace

**Files:**

- Track: `docs/superpowers/specs/2026-08-22-task-1-persistence-reconstruction.md`
- Track: `docs/superpowers/plans/2026-08-12-unified-lifelong-cognition.md`
- Track: `docs/superpowers/plans/2026-08-22-task-1-persistence-reconstruction.md`
- Create ignored runtime ledger:
  `.superpowers/sdd/2026-08-22-task-1-persistence-reconstruction/progress.md`

- [ ] **Step 1: Initialize the plan-scoped SDD workspace**

Run the installed `sdd-workspace` helper. Its `.superpowers/sdd/.gitignore`
intentionally keeps briefs, reports, review packages, and `progress.md` out of
branch history; the final reviewer receives them as explicit evidence files.

- [ ] **Step 2: Initialize the progress ledger**

Record branch, baseline SHA, baseline 50/50 pytest and Ruff results, plan/spec
paths, current host profile, and one row for Tasks 0–9. The ledger is the live
controller checkpoint; the three tracked planning documents are the durable
branch checkpoint.

- [ ] **Step 3: Verify and commit the tracked planning checkpoint**

```powershell
git diff --check
git add -- docs/superpowers/specs/2026-08-22-task-1-persistence-reconstruction.md docs/superpowers/plans/2026-08-12-unified-lifelong-cognition.md docs/superpowers/plans/2026-08-22-task-1-persistence-reconstruction.md
git diff --cached --check
git commit
```

```text
Recover the lost persistence trajectory before rebuilding its code

Constraint: The accepted V2 branch was never pushed and no Git object survives locally
Rejected: guessing implementation from v0.1 alone | the attachment preserves stricter crash and scale gates
Confidence: high
Scope-risk: narrow
Directive: Task 2 remains blocked until the reconstructed Task 1 scale gate is independently CLEAN
Tested: published 50-test baseline; Ruff; SQLite schema parse; plan and spec rereviews
Not-tested: persistence code begins in Task 1
```

## Mandatory per-task review loop

Tasks 1–8 end with this exact controller-owned loop after the task commit:

1. The controller records the task base/head SHAs and implementer report path
   in `progress.md`.
2. `review-package` writes the complete base-to-head diff under the plan-scoped
   ignored SDD workspace.
3. A fresh read-only reviewer receives the task brief, global constraints,
   implementer report, and review package; it verdicts spec compliance and code
   quality separately.
4. Critical/Important findings return to the same implementer. The implementer
   adds a failing regression test, fixes, reruns focused/full verification,
   commits, and appends evidence to the report. A fresh scoped rereviewer
   verdicts only the findings and fix diff.
5. The controller independently runs the task's focused command, full pytest,
   Ruff, and `git diff --check`, then records `CLEAN` or the exact blocker in
   `progress.md`. No later task starts from a non-CLEAN row.

The implementation plan's final numbered step for each task explicitly invokes
this loop. Review/runtime evidence stays ignored by design; commits and the
tracked plan/spec remain the durable audit trail.

---

### Task 1: Canonical contracts and strict codec

**Files:**

- Create: `src/aluclu/cognition/contracts.py`
- Create: `src/aluclu/cognition/codec.py`
- Create: `src/aluclu/cognition/__init__.py`
- Modify: `src/aluclu/__init__.py`
- Modify: `pyproject.toml`
- Create: `tests/test_cognition_contracts.py`
- Create: `tests/test_cognition_codec.py`

**Interfaces:**

- Produces: `JsonValue`, `LedgerSecurityScope`, `LedgerRecord`,
  `AppendOutcome`, `LedgerCursorCheckpoint`, typed exception hierarchy,
  `canonical_json_bytes()`, `strict_json_loads()`, `validate_event_id()`, and
  `SafeStateCodec`.
- Consumes: no new V2 interface.

- [ ] **Step 1: Write contract tests that fail because cognition is absent**

```python
import pytest

from aluclu.cognition import InputBoundaryError, validate_event_id


@pytest.mark.parametrize("value", ["", "has space", "é", "line\nbreak", "a" * 257])
def test_event_id_rejects_noncanonical_or_oversized_values(value: str) -> None:
    with pytest.raises(InputBoundaryError):
        validate_event_id(value)


@pytest.mark.parametrize("value", ["a", "evt_000001", "turn:1", "a.b-c_d"])
def test_event_id_accepts_canonical_ascii_values(value: str) -> None:
    assert validate_event_id(value) == value
```

- [ ] **Step 2: Run the two tests and confirm RED**

```powershell
.\.venv313\Scripts\python.exe -m pytest tests/test_cognition_contracts.py -q
```

Expected: collection fails with `ModuleNotFoundError: aluclu.cognition`.

- [ ] **Step 3: Write strict canonical JSON tests and confirm RED**

```python
import math

import pytest

from aluclu.cognition import InputBoundaryError, canonical_json_bytes, strict_json_loads


def test_canonical_json_has_literal_stable_bytes() -> None:
    assert canonical_json_bytes({"z": 1, "a": [True, None, "ı"]}) == (
        b'{"a":[true,null,"\xc4\xb1"],"z":1}'
    )


@pytest.mark.parametrize("value", [(1, 2), {1: "x"}, {"x": math.nan}, {"x": math.inf}])
def test_canonical_json_rejects_non_json_or_non_finite_values(value: object) -> None:
    with pytest.raises(InputBoundaryError):
        canonical_json_bytes(value)


def test_strict_json_rejects_duplicate_object_keys() -> None:
    with pytest.raises(InputBoundaryError):
        strict_json_loads(b'{"x":1,"x":2}')
```

Expected mutation caught: allowing Python coercions, duplicate keys, non-finite
floats, or locale-dependent output makes at least one assertion fail.

- [ ] **Step 4: Implement the minimal contracts and strict walker**

```python
MAX_EVENT_ID_BYTES = 256
MAX_PAYLOAD_BYTES = 2_097_152
MAX_JSON_DEPTH = 32
MAX_JSON_NODES = 65_536
EVENT_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}\Z")


def canonical_json_bytes(value: JsonValue) -> bytes:
    _validate_json_tree(value)
    encoded = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    if len(encoded) > MAX_PAYLOAD_BYTES:
        raise InputBoundaryError("canonical payload exceeds 2097152 bytes")
    return encoded
```

The tree walker is iterative, counts root/keys/values, tracks container IDs for
cycles, rejects subclasses that are not exact JSON types, and rejects lone
surrogates in every string.

- [ ] **Step 5: Add authenticated generation-based `SafeStateCodec` tests**

```python
def test_safe_state_codec_rejects_manifest_and_pointer_rewrite(tmp_path) -> None:
    codec = SafeStateCodec(tmp_path, integrity_key=b"k" * 32)
    codec.save("state", {"step": 1}, {"source": "test"})
    pointer = tmp_path / "state.json"
    pointer.write_bytes(pointer.read_bytes().replace(b'"generation":1', b'"generation":9'))
    with pytest.raises(StateIntegrityError):
        codec.load("state")


@pytest.mark.parametrize("name", ["../state", "a/b", "a\\b", "", "."])
def test_safe_state_codec_rejects_path_escape(tmp_path, name: str) -> None:
    codec = SafeStateCodec(tmp_path, integrity_key=b"k" * 32)
    with pytest.raises(InputBoundaryError):
        codec.save(name, {"step": 1}, {})
```

`SafeStateCodec.save()` writes a generation manifest, fsyncs it, then atomically
replaces an HMAC-authenticated pointer. `load()` verifies pointer and manifest
before returning `(state, metadata)`.

- [ ] **Step 6: Update exports and dependencies, then run verification**

```powershell
.\.venv313\Scripts\python.exe -m pytest tests/test_cognition_contracts.py tests/test_cognition_codec.py -q
.\.venv313\Scripts\python.exe -m pytest -q
.\.venv313\Scripts\ruff.exe check .
git diff --check
```

- [ ] **Step 7: Commit with the Lore protocol and run the mandatory review loop**

```text
Establish canonical cognition inputs before persistence accepts bytes

Constraint: Python 3.10+ and exact JSON limits from the reconstructed Task 1 spec
Rejected: permissive json.dumps coercion | it hides type drift and ambiguous payloads
Confidence: high
Scope-risk: narrow
Directive: Preserve literal canonical bytes because ledger AAD and hashes depend on them
Tested: focused cognition contracts/codec tests; full pytest; Ruff; git diff --check
Not-tested: crash-injected ledger operations begin in later tasks
```

After the commit, run the mandatory task review loop and record the verdict in
the plan-scoped `progress.md` before Task 2.

---

### Task 2: Atomic persistence utilities and external key contracts

**Files:**

- Create: `src/aluclu/cognition/persistence.py`
- Create: `src/aluclu/cognition/keys.py`
- Modify: `src/aluclu/cognition/__init__.py`
- Create: `tests/test_cognition_persistence.py`
- Create: `tests/test_cognition_keys.py`

**Interfaces:**

- Consumes: canonical JSON and typed integrity/input exceptions from Task 1.
- Produces: `exclusive_file_lock()`, `atomic_write_bytes()`,
  `resolve_ledger_path()`, `KeyProvider`, `StaticKeyProvider`,
  `FileKeyProvider`, `KeyringKeyProvider`, `RecordKeyState`,
  `RecordKeyReference`, `RecordKeyStore`, and `FileRecordKeyStore`.

- [ ] **Step 1: Write path and atomic-file RED tests**

```python
def test_resolved_relative_path_does_not_follow_later_chdir(tmp_path, monkeypatch) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    monkeypatch.chdir(first)
    resolved = resolve_ledger_path(Path("memory.sqlite3"))
    monkeypatch.chdir(second)
    assert resolved == (first / "memory.sqlite3").resolve()


@pytest.mark.skipif(os.name != "nt", reason="Win32 alias rule")
@pytest.mark.parametrize("name", ["memory.sqlite3.", "memory.sqlite3 "])
def test_windows_trailing_dot_or_space_path_fails_closed(tmp_path, name: str) -> None:
    with pytest.raises(UnsafePathError):
        resolve_ledger_path(tmp_path / name)
```

Expected mutation caught: deferring `Path.resolve()` or trimming an invalid
Win32 component would make a different physical database reachable.

- [ ] **Step 2: Implement path resolution, file fsync, and one cross-platform lock**

```python
@contextmanager
def exclusive_file_lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b", buffering=0) as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
            os.fsync(handle.fileno())
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
```

The implementation rejects symlink/reparse-point sidecars, resolves the
absolute ledger path at construction, and never derives paths from a later
working directory.

- [ ] **Step 3: Write provider and monolithic key-store RED tests**

```python
def test_file_record_key_store_repairs_pending_only_with_exact_hash(tmp_path) -> None:
    store = FileRecordKeyStore(tmp_path / "keys.json", b"m" * 32, ledger_id="ledger-1")
    pending = store.put_pending("evt_1", b"d" * 32)
    assert pending.state is RecordKeyState.PENDING
    committed = store.mark_committed("evt_1", "ab" * 32)
    assert committed.record_hash == "ab" * 32
    assert store.get("evt_1") == b"d" * 32


def test_file_record_key_store_shred_removes_dek_and_keeps_tombstone(tmp_path) -> None:
    store = FileRecordKeyStore(tmp_path / "keys.json", b"m" * 32, ledger_id="ledger-1")
    store.put_pending("evt_1", b"d" * 32)
    store.mark_committed("evt_1", "ab" * 32)
    assert store.shred("evt_1", "ab" * 32)
    assert store.get("evt_1") is None
    assert store.is_tombstoned("evt_1")
```

- [ ] **Step 4: Implement providers and authenticated `FileRecordKeyStore`**

`StaticKeyProvider` rejects non-32-byte keys. `FileKeyProvider(create=False)`
never creates a secret implicitly. `KeyringKeyProvider` imports `keyring`
inside `get_key()` and raises `KeyProviderUnavailable` for missing packages,
empty vault entries, invalid base64, insecure/unavailable backends, or backend
errors. The file key store uses `SafeStateCodec` and copies key material only
as immutable `bytes`.

- [ ] **Step 5: Verify, commit, and run the mandatory review loop**

```powershell
.\.venv313\Scripts\python.exe -m pytest tests/test_cognition_persistence.py tests/test_cognition_keys.py -q
.\.venv313\Scripts\python.exe -m pytest -q
.\.venv313\Scripts\ruff.exe check .
git diff --check
```

```text
Keep record keys outside SQLite so deletion has a cryptographic boundary

Constraint: Crash-safe local files and optional OS vaults without mandatory keyring import
Rejected: storing wrapped DEKs in SQLite | WAL and freelist pages can retain deleted rows
Confidence: high
Scope-risk: moderate
Directive: Never delete a COMMITTED orphan as if it were an uncommitted crash artifact
Tested: persistence/key-store tests; full pytest; Ruff; git diff --check
Not-tested: SQLite cross-store recovery is covered by the next ledger task
```

Record a CLEAN independent review before Task 3.

---

### Task 3: Schema-v2 encrypted ledger foundation

**Files:**

- Create: `src/aluclu/cognition/ledger.py`
- Modify: `src/aluclu/cognition/__init__.py`
- Modify: `src/aluclu/__init__.py`
- Create: `tests/test_cognition_ledger.py`

**Interfaces:**

- Consumes: Tasks 1–2 codecs, providers, file store, path/lock helpers.
- Produces: `EncryptedLedger` with `unlock`, `close`, `append`,
  `append_once`, `read`, `event_count`, and `verify_integrity`; schema-v2
  bootstrap; authenticated ledger identity and anchor.

- [ ] **Step 1: Write new-ledger, round-trip, idempotency, and wrong-key RED tests**

```python
def test_append_round_trip_is_encrypted_and_idempotent(tmp_path) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(b"m" * 32)) as ledger:
        first = ledger.append_once("evt_1", {"secret": "plain-marker"})
        again = ledger.append_once("evt_1", {"secret": "plain-marker"})
        assert first.created is True
        assert again.created is False
        assert again.record == first.record
        assert ledger.read("evt_1").payload == {"secret": "plain-marker"}
    assert b"plain-marker" not in path.read_bytes()


def test_wrong_master_key_cannot_claim_existing_empty_ledger(tmp_path) -> None:
    path = tmp_path / "memory.sqlite3"
    EncryptedLedger(path, StaticKeyProvider(b"a" * 32)).unlock()
    with pytest.raises(LedgerKeyError):
        EncryptedLedger(path, StaticKeyProvider(b"b" * 32)).unlock()
```

- [ ] **Step 2: Confirm RED, then implement schema/bootstrap and crypto helpers**

```powershell
.\.venv313\Scripts\python.exe -m pytest tests/test_cognition_ledger.py -q
```

The implementation creates schema v2 only when the path did not exist, writes
identity metadata and an external authenticated anchor, configures SQLite
pragmas, derives domain-separated keys with HKDF-SHA256, and treats every
existing incomplete/foreign database as `LedgerMigrationRequired` or
`LedgerIntegrityError`.

- [ ] **Step 3: Implement append/read under one lock and explicit transaction**

```python
def append_once(self, event_id: str, payload: JsonValue) -> AppendOutcome:
    with self.verified_session() as session:
        return session.append_once(event_id, payload)
```

The initial session may use full verification on each convenience call; Task 7
adds certificate reuse. A record is inserted only after `put_pending`; after
SQLite commit the exact HMAC record hash is passed to `mark_committed`.

- [ ] **Step 4: Add full-chain/projection/tamper and concurrent-writer tests**

```python
def test_two_ledger_objects_cannot_fork_the_history(tmp_path) -> None:
    path = tmp_path / "memory.sqlite3"
    ledgers = [EncryptedLedger(path, StaticKeyProvider(b"m" * 32)) for _ in range(2)]
    for ledger in ledgers:
        ledger.unlock()
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda pair: pair[0].append(*pair[1]), zip(ledgers, [
            ("evt_1", {"i": 1}),
            ("evt_2", {"i": 2}),
        ])))
    assert {outcome.record.sequence for outcome in outcomes} == {1, 2}
    ledgers[0].verify_integrity()
```

Add direct SQL mutations for `history`, `records`, `tombstones`, and `metadata`;
each must raise `LedgerIntegrityError` on full verification. The expected hashes
come from literal fixtures, never the ledger's private hash helper.

- [ ] **Step 5: Verify, commit, and run the mandatory review loop**

```powershell
.\.venv313\Scripts\python.exe -m pytest tests/test_cognition_ledger.py -q
.\.venv313\Scripts\python.exe -m pytest -q
.\.venv313\Scripts\ruff.exe check .
git diff --check
```

```text
Make encrypted history authoritative before higher cognition writes state

Constraint: Schema v2, explicit SQLite transactions, unique AES-GCM record keys
Rejected: trusting a plain SHA chain | a disk writer could recompute it after tampering
Confidence: high
Scope-risk: broad
Directive: All projections and external key states must remain derivable from authenticated history
Tested: ledger round-trip/idempotency/tamper/concurrency tests; full pytest; Ruff; diff-check
Not-tested: shredding and injected crash recovery are isolated in Task 4
```

Record a CLEAN independent review before Task 4.

---

### Task 4: Crypto-shred, rollback detection, and reconstructed round-5 gate

**Files:**

- Modify: `src/aluclu/cognition/ledger.py`
- Modify: `src/aluclu/cognition/keys.py`
- Modify: `tests/test_cognition_ledger.py`
- Modify: `tests/test_cognition_keys.py`
- Create: `tests/test_cognition_crash_recovery.py`

**Interfaces:**

- Consumes: Task 3 ledger and Task 2 external key state.
- Produces: `EncryptedLedger.shred`, `is_tombstoned`, forward recovery,
  selective rollback detection, and crash-injection test seams that are private
  and disabled unless explicitly passed by tests.

- [ ] **Step 1: Write shred and no-resurrection RED tests**

```python
def test_shred_destroys_key_but_preserves_authenticated_lineage(tmp_path) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(b"m" * 32)) as ledger:
        ledger.append("evt_1", {"secret": "marker"})
        assert ledger.shred("evt_1") is True
        assert ledger.shred("evt_1") is False
        assert ledger.read("evt_1") is None
        assert ledger.is_tombstoned("evt_1")
        ledger.verify_integrity()
```

- [ ] **Step 2: Add exact crash-boundary RED cases**

Parameterize steps 5–9 from the spec with a subprocess that terminates after
the named boundary. Reopen with the real backend and assert exactly one of:
the old state, the exact new state, or a typed integrity error. For SQLite
commit before receipt, assert the next same-process call repairs the exact hash
and a retry does not append a second event.

```python
def test_committed_receipt_rollback_is_not_deleted_as_pending(tmp_path) -> None:
    path = tmp_path / "memory.sqlite3"
    key = StaticKeyProvider(b"m" * 32)
    with EncryptedLedger(path, key) as ledger:
        ledger.append("evt_1", {"i": 1})
        ledger.append("evt_2", {"i": 2})
    _restore_database_without_last_record(path)
    with pytest.raises(LedgerRollbackError):
        EncryptedLedger(path, key).unlock()
```

- [ ] **Step 3: Implement external-first shred and deterministic recovery**

The shared file lock covers store mutation, SQLite transaction, and anchor
advance. Recovery deletes only unreferenced `PENDING` keys; it repairs exact
pending/live matches, forward-applies exact tombstones, and rejects every
committed-orphan or extra-tombstone mismatch.

- [ ] **Step 4: Add historical round-5 path/JSON/legacy oracles**

Add tests for relative-path stability after `chdir`, Windows trailing dot/space
aliases, missing identity metadata, missing anchor, anchor rollback, store
identity mismatch, extra external tombstone, invalid UTF-8/duplicate JSON keys,
and explicit rejection of a legacy monolithic store passed where the directory
backend is required.

- [ ] **Step 5: Run the reconstructed round-5 verification gate**

```powershell
.\.venv313\Scripts\python.exe -m pytest tests/test_cognition_codec.py tests/test_cognition_keys.py tests/test_cognition_ledger.py tests/test_cognition_crash_recovery.py -q
.\.venv313\Scripts\python.exe -m pytest -q
.\.venv313\Scripts\ruff.exe check .
git diff --check
```

- [ ] **Step 6: Commit**

```text
Prevent deleted or rolled-back cognition from being silently reclassified

Constraint: External-first key destruction and deterministic crash-forward repair
Rejected: deleting every key absent from SQLite | selective database rollback would become silent loss
Confidence: high
Scope-risk: broad
Directive: COMMITTED external state is evidence; never garbage-collect it without matching authenticated lineage
Tested: crash matrix and round-5 regression set; full pytest; Ruff; diff-check; independent task review
Not-tested: 8192-turn scale behavior begins after the directory backend lands
```

- [ ] **Step 7: Run the mandatory review loop**

The fresh reviewer must explicitly verdict committed-receipt rollback,
same-process recovery, Win32 aliases, legacy-store rejection, and mutation
strength. Record CLEAN before Task 5.

---

### Task 5: DirectoryRecordKeyStore and non-keyring production default

**Files:**

- Modify: `src/aluclu/cognition/keys.py`
- Modify: `src/aluclu/cognition/ledger.py`
- Modify: `src/aluclu/cognition/__init__.py`
- Modify: `tests/test_cognition_keys.py`
- Modify: `tests/test_cognition_ledger.py`
- Create: `tests/test_cognition_directory_store.py`

**Interfaces:**

- Consumes: `RecordKeyStore` state machine and atomic persistence utilities.
- Produces: `DirectoryRecordKeyStore`, HMAC-addressed fanout layout,
  fixed staged/prepare/head recovery, `revision`, bounded file mutation, and
  default construction for static/file-key ledgers.

- [ ] **Step 1: Write layout/privacy and bounded-mutation RED tests**

```python
def test_directory_store_never_uses_event_id_as_a_path(tmp_path) -> None:
    root = tmp_path / "keys"
    store = DirectoryRecordKeyStore(root, b"m" * 32, ledger_id="ledger-1")
    store.put_pending("customer:alice", b"d" * 32)
    relative_names = [str(path.relative_to(root)) for path in root.rglob("*")]
    assert all("customer" not in name and "alice" not in name for name in relative_names)


def test_directory_store_mutation_count_is_lifetime_independent(tmp_path) -> None:
    store = DirectoryRecordKeyStore(tmp_path / "keys", b"m" * 32, ledger_id="ledger-1")
    for index in range(256):
        event_id = f"evt_{index:06d}"
        store.put_pending(event_id, bytes([index % 251]) * 32)
        store.mark_committed(event_id, f"{index:064x}")
    before = _tree_fingerprint(tmp_path / "keys")
    store.put_pending("evt_final", b"z" * 32)
    changed = _changed_paths(before, _tree_fingerprint(tmp_path / "keys"))
    assert len(changed) <= 6
```

- [ ] **Step 2: Write prepare protocol crash RED tests**

For each store boundary `staged`, `prepare`, `event-state`, `head`, and
`cleanup`, terminate a subprocess and reopen. Before `prepare`, the old state
must remain. At/after `prepare`, reopen must forward-complete the exact new
state. Repeating recovery twice must not increment revision twice.

- [ ] **Step 3: Implement the exact on-disk protocol**

Use the spec's `identity.json`, `head.json`, `prepare.json`, `staged.bin`, and
two-level HMAC token layout. `prepare.json` authenticates the operation,
expected previous revision, new revision, target token, staged digest, and
target state. Recovery validates all fields before replacing files.

- [ ] **Step 4: Make directory storage the default and fail closed on legacy state**

For `STATIC_TEST_KEY` and `LOCAL_FILE_KEY`,
`EncryptedLedger(..., record_key_store=None)` creates or opens
`<database>.record-keys/`. Until Task 6 lands, `OS_KEYRING` raises
`LedgerCapabilityUnavailable` before mutation. Passing `FileRecordKeyStore`
remains supported explicitly. If a file already occupies the directory path or
an unknown store identity/version exists, raise `LedgerMigrationRequired`
without mutation.

- [ ] **Step 5: Verify, commit, and run the mandatory review loop**

```powershell
.\.venv313\Scripts\python.exe -m pytest tests/test_cognition_directory_store.py tests/test_cognition_keys.py tests/test_cognition_ledger.py tests/test_cognition_crash_recovery.py -q
.\.venv313\Scripts\python.exe -m pytest -q
.\.venv313\Scripts\ruff.exe check .
git diff --check
```

```text
Make per-record key updates independent of lifetime history size

Constraint: One crash-forward prepare record and HMAC-addressed event files
Rejected: rewriting one encrypted key map per mutation | it recreates quadratic lifetime cost
Confidence: high
Scope-risk: broad
Directive: Keep prepare as the commit intent and update head only after event-state is durable
Tested: directory layout, crash boundaries, bounded mutation, full pytest, Ruff, diff-check
Not-tested: OS-keyring record storage, session certificate, and benchmark land in Tasks 6–8
```

Record a CLEAN independent review before Task 6.

---

### Task 6: OS-keyring record-key profile and capability gate

**Files:**

- Modify: `src/aluclu/cognition/keys.py`
- Modify: `src/aluclu/cognition/ledger.py`
- Modify: `src/aluclu/cognition/__init__.py`
- Modify: `pyproject.toml`
- Create: `tests/test_cognition_keyring_store.py`
- Modify: `tests/test_cognition_ledger.py`

**Interfaces:**

- Consumes: `RecordKeyStore`, the directory store's authenticated metadata
  journal, and `KeyringKeyProvider` namespace.
- Produces: `KeyringRecordKeyStore`, `LedgerCapabilityUnavailable`, and exact
  `create_record_key_store(database_path, key_provider, *, ledger_id, create)`
  selection without disk fallback.

- [ ] **Step 1: Write capability and selection RED tests**

Use a deterministic in-memory keyring double only at the external keyring API
boundary. Test that lazy import/backend failure raises
`LedgerCapabilityUnavailable` before persistence mutation, `OS_KEYRING`
selects `KeyringRecordKeyStore`, and static/file scopes select
`DirectoryRecordKeyStore`. An explicitly passed valid store remains
authoritative.

```python
def test_keyring_capability_failure_never_falls_back_to_disk(tmp_path, monkeypatch) -> None:
    provider = KeyringKeyProvider("aluclu-test", "owner", create=True)
    monkeypatch.setattr(keys, "_load_keyring_backend", _raise_unavailable)
    with pytest.raises(LedgerCapabilityUnavailable):
        create_record_key_store(
            tmp_path / "memory.sqlite3",
            provider,
            ledger_id="ledger-1",
            create=True,
        )
    assert not (tmp_path / "memory.sqlite3.record-keys").exists()
```

- [ ] **Step 2: Write DEK-placement and head-witness RED tests**

Append one pending/committed key through a persistent fake keyring boundary.
Assert the 32-byte DEK is present only in the fake credential store and nowhere
under the disk root. Restore an earlier disk head after a later keyring-head
credential and assert `LedgerRollbackError` rather than repair or fallback.

- [ ] **Step 3: Write keyring crash-state RED tests**

Inject at `staging-credential`, `staged-metadata`, `prepare`,
`final-credential`, `event-state`, `disk-head`, `keyring-head`, and `cleanup`.
Before prepare, reopen discards only the fixed staging credential and retains
the old state. At/after prepare, reopen forward-completes the exact state when
the staging or final credential matches its authenticated digest; otherwise it
fails closed. Add the corresponding shred path with delete-before-tombstone
and prove a shredded credential is never recreated.

- [ ] **Step 4: Implement the keyring profile without secret disk bytes**

Reuse metadata canonicalization and prepare validation, not Directory store
secret serialization. Credential usernames bind service, username prefix,
ledger ID, purpose, and HMAC event token. Maintain one authenticated keyring
head credential as a rollback witness. A capability probe performs an isolated
set/get/delete round trip. `keyring` is imported only inside the adapter; add
the `os-keyring` optional dependency group.

- [ ] **Step 5: Integrate factory selection and explicit-store override**

`EncryptedLedger(record_key_store=None)` calls the exact factory after ledger
identity is known. An explicit store is accepted only when its ledger ID and
authenticated identity match. Generic providers claiming `OS_KEYRING` without
the concrete namespace contract fail with `LedgerCapabilityUnavailable`.

- [ ] **Step 6: Verify, commit, and run the mandatory review loop**

```powershell
.\.venv313\Scripts\python.exe -m pytest tests/test_cognition_keyring_store.py tests/test_cognition_keys.py tests/test_cognition_ledger.py -q
.\.venv313\Scripts\python.exe -m pytest -q
.\.venv313\Scripts\ruff.exe check .
git diff --check
```

```text
Preserve OS-vault record-key semantics without hiding a disk fallback

Constraint: Production keyring DEKs never enter regular files and keyring capability is environment-dependent
Rejected: wrapping keyring DEKs into DirectoryRecordKeyStore | it changes the accepted security scope silently
Confidence: high
Scope-risk: broad
Directive: Keep the keyring head as an independent rollback witness and fail closed on backend ambiguity
Tested: capability, placement, crash, rollback, factory, full pytest, Ruff, diff-check, independent task review
Not-tested: platform keyring quota at lifelong scale is reported as a runtime capability limit
```

---

### Task 7: Object-local verified sessions and bounded cursors

**Files:**

- Modify: `src/aluclu/cognition/contracts.py`
- Modify: `src/aluclu/cognition/ledger.py`
- Modify: `src/aluclu/cognition/__init__.py`
- Modify: `tests/test_cognition_ledger.py`
- Create: `tests/test_cognition_sessions.py`

**Interfaces:**

- Consumes: authenticated SQLite/store heads and store revision.
- Produces: `VerifiedLedgerSession`, `VerifiedLedgerCursor`,
  `LedgerCursorCheckpoint`, object-local verification certificate,
  frozen `LedgerVerificationStats`, `verified_session()`, `cursor()`,
  `suspend()`, and `resume_verified()`.

- [ ] **Step 1: Write lifecycle and snapshot RED tests**

```python
def test_session_and_cursor_fail_after_close(tmp_path) -> None:
    ledger = EncryptedLedger(tmp_path / "memory.sqlite3", StaticKeyProvider(b"m" * 32))
    ledger.unlock()
    session = ledger.verified_session()
    cursor = session.cursor()
    session.close()
    with pytest.raises(LedgerLifecycleError):
        session.event_count()
    with pytest.raises(LedgerLifecycleError):
        next(cursor)


def test_cursor_checkpoint_rejects_changed_head(tmp_path) -> None:
    with EncryptedLedger(tmp_path / "memory.sqlite3", StaticKeyProvider(b"m" * 32)) as ledger:
        ledger.append("evt_1", {"i": 1})
        with ledger.verified_session() as session:
            checkpoint = session.cursor().suspend()
        ledger.append("evt_2", {"i": 2})
        with ledger.verified_session() as session:
            with pytest.raises(LedgerSnapshotChanged):
                session.resume_verified(checkpoint)
```

- [ ] **Step 2: Write certificate invalidation RED tests**

Instrument only public evidence counters exposed through a frozen
`LedgerVerificationStats` value. Assert one full verification for many clean
short sessions. Commit through a second SQLite connection and assert the next
call increments full verifications because the first connection's
`PRAGMA data_version` changed. Explicit `verify_integrity()` always increments
full verifications.

- [ ] **Step 3: Implement session ownership and certificate checks**

The session owns one re-entrant object lock and the cross-process lock. It
performs recovery and either full or bounded delta verification once. The
certificate stores head, anchor digest, store revision, same-connection
`data_version`, and DB/WAL stat fingerprint. Clean close refreshes it; uncertain
exceptions invalidate it.

- [ ] **Step 4: Implement bounded cursor streaming**

The cursor uses `fetchmany(batch_size)` with `1 <= batch_size <= 4096`, freezes
the session's head, skips shredded records without loading their payloads, and
never calls `fetchall()`. A checkpoint is bound to ledger ID and exact snapshot
head.

- [ ] **Step 5: Verify, commit, and run the mandatory review loop**

```powershell
.\.venv313\Scripts\python.exe -m pytest tests/test_cognition_sessions.py tests/test_cognition_ledger.py tests/test_cognition_directory_store.py -q
.\.venv313\Scripts\python.exe -m pytest -q
.\.venv313\Scripts\ruff.exe check .
git diff --check
```

```text
Avoid re-verifying lifetime history when one ledger object already proved it

Constraint: Certificates are connection-local and external commits force a full scan
Rejected: sharing certificates across ledger objects | data_version and lock ownership are connection-specific
Confidence: high
Scope-risk: broad
Directive: Explicit verify_integrity remains a full scan regardless of certificate state
Tested: lifecycle, cursor, certificate invalidation, full pytest, Ruff, diff-check
Not-tested: end-to-end 8192-turn resource behavior lands in Task 8
```

Record a CLEAN independent review before Task 8.

---

### Task 8: Real 8,192-turn performance, RSS, and disk gate

**Files:**

- Create: `src/aluclu/cli/benchmark_cognition_ledger.py`
- Modify: `pyproject.toml`
- Create: `scripts/benchmark_cognition_ledger.py`
- Create: `tests/test_cognition_benchmark.py`
- Create: `results/cognition_ledger_scale.json` by running the gate

**Interfaces:**

- Consumes: public `EncryptedLedger.verified_session()` API only.
- Produces: `aluclu-benchmark-cognition-ledger` CLI and one atomic JSON result
  containing configuration, platform versions, success, quartile latency,
  verification counts, peak RSS, database/WAL/key-store byte totals, and the
  current host's CPU/RAM/GPU/storage profile.

- [ ] **Step 1: Write deterministic CLI/result RED test**

```python
def test_benchmark_writes_machine_readable_resource_evidence(tmp_path) -> None:
    output = tmp_path / "result.json"
    work_dir = tmp_path / "run"
    result = run_benchmark(
        turns=64,
        payload_bytes=128,
        output=output,
        work_dir=work_dir,
        seed=7,
    )
    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert persisted == result
    assert result["turns"] == 64
    assert result["success"] is True
    assert len(result["quartile_seconds"]) == 4
    assert result["full_verifications"] <= 2
    assert result["disk_bytes"]["total"] > 0
```

- [ ] **Step 2: Implement measurement outside the timed payload generator**

Use `time.perf_counter_ns`, deterministic payloads generated before each timed
batch, `resource.getrusage` on POSIX and `GetProcessMemoryInfo` via `ctypes` on
Windows, and atomic canonical JSON output. Record Python, SQLite,
cryptography, OS, CPU model, physical/logical core counts, total RAM,
GPU/CUDA availability, storage type/free space, filesystem path type, and git
commit. Derive the benchmark ledger root with `local_benchmark_root()` under
unsynchronised application state rather than `%TEMP%` or the OneDrive-synced
checkout. The artifact is a measurement of this host;
do not compare absolute latency or RSS against the missing PC as a pass/fail
oracle. Record whether the active environment uses system site packages and
whether installed versions satisfy `pyproject.toml`; a dependency mismatch is
visible evidence, not a silently ignored field. Torch/GPU are inventory only
and are not touched by the persistence loop.

- [ ] **Step 3: Prove the benchmark's failure behavior**

Add tests that an existing output is atomically replaced, invalid turn/payload
arguments fail before creating a ledger, and an injected append error writes no
false `success: true` artifact.

- [ ] **Step 4: Run the real 8,192-turn gate**

```powershell
$runId = 'task1d-20260822-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
$workDir = Join-Path $env:LOCALAPPDATA "ALUCLU\benchmarks\$runId"
.\.venv313\Scripts\python.exe scripts\benchmark_cognition_ledger.py --turns 8192 --payload-bytes 512 --seed 20260822 --work-dir $workDir --output results\cognition_ledger_scale.json
```

Acceptance: exit 0, 8,192 events, no integrity error, no duplicate, no more
than two full verifications in the single-process run, finite positive RSS and
disk metrics, fourth/first-quartile and second/first-half per-append ratios each
at most 1.75, peak RSS delta at most 256 MiB, and total logical persistent bytes
at most 128 MiB. The artifact reports the absolute LocalAppData run path, each
raw threshold input, the new host profile, and any declared/installed
dependency mismatch rather than hiding a missed gate. Preserve the run
directory through final review.

- [ ] **Step 5: Run full verification, commit, and mandatory task review**

```powershell
.\.venv313\Scripts\python.exe -m pytest -q
.\.venv313\Scripts\ruff.exe check .
git diff --check
git status --short
```

```text
Measure lifetime-ledger cost before allowing higher cognition to depend on it

Constraint: 8192 real encrypted appends on the production directory backend
Rejected: extrapolating from an in-memory or mocked store | it omits filesystem and crypto costs
Confidence: high
Scope-risk: moderate
Directive: Preserve raw machine-readable evidence and rerun it after persistence changes
Tested: benchmark tests; real 8192-turn gate; full pytest; Ruff; diff-check
Not-tested: long-duration power-loss behavior requires hardware fault injection
```

Record a CLEAN Task 8 review and preserve the LocalAppData run directory before
the whole-branch Task 9 gate.

---

### Task 9: Task 1 final review and Task 2 release gate

**Files:**

- Modify only files required by the single final-review fix wave.
- Create/Update ignored evidence:
  `.superpowers/sdd/2026-08-22-task-1-persistence-reconstruction/progress.md`

**Interfaces:**

- Consumes: the complete branch diff and all prior task reports.
- Produces: independent whole-branch spec/quality verdict and an explicit
  `Task 1 scale gate: CLEAN` ledger line, or a recorded blocking finding.

- [ ] **Step 1: Generate a whole-branch review package from merge-base to HEAD**

```powershell
git merge-base main HEAD
git log --oneline --decorate main..HEAD
git diff --stat main...HEAD
git diff --check main...HEAD
```

- [ ] **Step 2: Dispatch an independent reviewer**

The reviewer receives the spec, plan, progress ledger, implementation reports,
complete diff package, and benchmark artifact. It verdicts spec compliance and
code quality separately, with special attention to crash order, rollback,
path identity, AEAD AAD, key deletion, lock lifetime, streaming bounds, and
test mutation strength.

- [ ] **Step 3: Apply at most one final fix wave and one scoped re-review**

Every Critical/Important finding is fixed by a fresh implementer using a new
failing regression test. Re-run focused tests, full pytest, Ruff, diff-check,
and the 8,192-turn benchmark when persistence behavior changed.

- [ ] **Step 4: Record the gate without starting Task 2**

```text
Task 1 scale gate: CLEAN
Evidence: full pytest; focused persistence suite; Ruff; git diff --check; 8192-turn artifact; independent final review
Next allowed task: Task 2 sensorium/recall under its own reviewed implementation plan
Deferred: licensing/IP/docs/paper/release/push remain Tasks 13–14
```
