# Durable global reservation publication

Status: PROPOSED; implementation/admission pending independent review.
Parent0f272be6d3cd2eb308fe47b366f96c174ed5c77f. This is local research execution
plumbing, not the final .alc container. Owner accounting/training direction already
approved. Historical numeric/calendar values and actual launch authority remain
separate prerequisites; this contract grants neither.

## Existing boundary and reuse

ReservationReplay validates complete immutable declarations and event semantics.
AttemptJournal supplies bounded chained records, cooperating path locking,
append+fsync and exact-head reconciliation. OwnedAppend is per-attempt; its owner
schema depends on RunSpec and cannot represent global reservations. Reuse
AttemptJournal and persistence primitives, not a second storage format/library.

ReservationStore uses one dedicated existing absolute trusted namespace root with
root/owner.json, root/global.lock, root/journal.jsonl, root/journal.jsonl.lock,
root/intents/initialization.json and intent-NNNNNN.json. Intents directory already
exists. Reject links/reparse aliases, nonregular/multiple-link files, unexpected
inventory and unsafe parents using existing persistence checks. Cooperating
trusted coordinator writers only, NOT hostile-directory TOCTOU or total-host
compromise protection. ALL mutations hold global.lock, then journal's own lock;
no reverse lock acquisition and no unowned writes to these files.

Caller supplies exact declarations at construction and independently current
owner SHA256 to read/prepare. Workers/files cannot supply a latest trusted root.
No implicit create, recover, truncation, fallback or root adoption. Hashes prove
integrity only; rollback of both disk and independent authority is outside this
local scope. Launch authority/resource policy remains the later verified adapter.

## Exact records and resource bounds

Journal identity = ReservationReplay(declarations).snapshot().root (genesis).
Existing journal envelopes use existing integer sequence/counts <=65536 and
<=32MiB journal bytes, event<=8192bytes. Reservation fixed-field events are small;
planner still rejects larger values. These storage caps do not silently redefine
the pure contract: deny before mutation and report capacity, do not forget work
or substitute paging. Original fixed experiment must demonstrate fit before
scientific admission; if not, reviewed paging integration is required.

Owner canonical JSON EXACT fields: schema="alc-r0-reservation-owner-v1",
generation (decimal string0..65536), declaration_genesis_root (64lowercasehex),
previous_owner_root (null only genesis), review_root (null only genesis),
journal_head (exact existing {count,byte_length,digest}), reservation_root.
generation=head.count=validated replay.event_count; reservation_root is the exact
semantic replay root; genesis journal head is AttemptJournal's domain genesis,
not the semantic genesis. Owner<=4096bytes; counts/head are range/type checked.
Version distinction is explicit; no rewriting canonical.py.

PreparedReservationIntent immutable data:bytes and sha256:str. Canonical EXACT
fields: schema="alc-r0-reservation-intent-v1", previous_owner (object or null),
candidate_owner (object), event (object or null), review_root (root or null).
<=16384bytes. Canonically embedded owners can be reconstructed and their hashes
derived; sha256 is independently pinned by caller, not read as authority from
disk. Initialization has null previous/event/review and a genesis candidate.
Append intent has exactly one event, valid old owner, nonnull review root,
generation+1, predecessor owner hash and exact plan_journal_append head.
Rebuild byte-for-byte using semantic replay, not arbitrary candidate acceptance.

Retain all intents including initialization. <=65537 files and <=128MiB total
intent bytes; individually <=16KiB. Scan/stat before reading, enforce aggregate
bound and exact contiguous names through current generation; at most the exact
caller-pinned next intent may additionally exist for explicit recovery. Missing
completed intent, orphan future intent, wrong digest or extra file denies. Journal
framing corruption is not auto-repair. Additional bounded owner/locks/staging
overhead is declared in actual resource projections; these caps are not RSS or
disk availability claims. Reads are bounded before parse/allocation.

EVERY normal read/prepare/commit/resume audits the COMPLETE retained intent chain:
derive exact initialization candidate from declarations/journal genesis, then for
each completed generation rebuild canonical intent from exact prior owner,
corresponding journal prefix/event and retained review root; replay semantics and
plan exact journal head; require byte-for-byte equality to persisted intent.
Its candidate becomes the next prior; final reconstructed owner must equal the
independently pinned observed owner. Shape/name/local digest alone is insufficient.
The optional next recovery intent is similarly exact and independently pinned.
No authenticated summary shortcut. Before first mutation, check PROJECTED new
intent count/total bytes, journal plan count/bytes, owner bytes and semantic sums.
Capacity denial preserves all predecessor files/root.

## API and transaction ordering

- initialization_intent(): pure candidate for explicit reviewed initialization.
- initialize(intent): global lock, closed inventory check, reconstruct/verify
  exact initialization bytes; persist initialization intent BEFORE journal/owner
  creation; create or reconcile EXACT empty journal; atomically fsync+publish
  genesis owner. Existing nonempty history or another owner denies. Exact visible
  genesis may re-acknowledge only with persisted matching initialization intent.
  Missing owner/journal alone never proves empty history. External reviewed
  empty-history scope and explicit initializer admission are mandatory.
- read(expected_owner_root): under global lock load bounded exact owner, complete
  journal at its exact head, replay declarations/events against semantic root,
  verify retained inventory. Does not repair or silently read through pending
  intent/journal uncertainty. Return PublishedReservation(data,sha256,snapshot).
- prepare(expected_owner_root,event,review_root): lock, exact current read and
  inventory with NO pending next intent; validate event semantically using replay,
  plan exact journal append, construct candidate/intent. No persistence. Capturing
  policy/resource admission remains external; this method is not a permit.
- commit(intent): lock, decode/rebuild intent, require exact previous owner and
  journal predecessor, no existing target intent or unrecorded journal mutation;
  persist exact intent durably; append+fsync journal; atomically publish candidate
  owner; return durable PublishedReservation only after all operations succeed.
  If any write/fsync fails, no success receipt; retain visible evidence unchanged.
- resume(intent): explicit lock, independently pinned exact intent MUST exist;
  observed owner is only exact previous or candidate; complete journal is only
  exact previous prefix or previous+exact event. Revalidate entire semantic
  prefix and intent/inventory BEFORE mutation. Re-fsync intent; append missing
  event or reconcile exact already-visible candidate journal; re-fsync/publish
  exact candidate owner. Never duplicate event or create a new generation.
  Wrong/truncated suffix or missing persisted intent denies without repair.

Explicit initialization matrix (all cases require exact independently pinned
initialization intent and closed namespace):

| Persisted intent | Journal | Owner | Action |
| --- | --- | --- | --- |
| absent | absent | absent | first explicit initialize: persist intent, create empty journal, publish genesis |
| exact matching | absent | absent | re-fsync intent, create empty journal, publish genesis |
| exact matching | exact empty genesis | absent | re-fsync intent and journal, publish genesis |
| exact matching | exact empty genesis | exact genesis | re-fsync all three and re-acknowledge |

All other combinations deny without mutation, including owner present but journal
absent, any nonempty journal, missing/mismatched intent with pre-existing storage,
unexpected owner/inventory. No initializer can overwrite a published generation.

Append recovery matrix (exact persisted caller-pinned append intent required):

| Owner | Journal | Action |
| --- | --- | --- |
| exact previous | exact previous prefix | re-fsync intent, append event, publish candidate |
| exact previous | exact candidate prefix | re-fsync intent/journal, publish candidate |
| exact candidate | exact candidate prefix | re-fsync intent/journal/owner, re-acknowledge |
| exact candidate | previous prefix | DENY: publication contradicts missing event; never append to repair |

Missing owner/journal, malformed/truncated journal or any other prefix/suffix deny
without mutation. Only initialization handles its own absent-owner cases. The
candidate prefix must have exactly the old events plus the exact intended event;
complete predecessor intent chain must still verify before any recovery write.

The store publishes the GLOBAL reservation event, including child identity and
release accounting when those events are supplied. It does not create/kill/resume
processes, verify allocation facts, produce authority, or implement full scientific
launch by itself. Later split owned lease must consume its independently current
published receipt and keep the global lock through revalidation/creation ordering.
Reservation publication alone is not enough to start a model.

## Proof and implementation sequence

TDD missing-module RED, then concrete immutable record/store implementation and
synthetic temp-directory tests. Validate initialization idempotent explicit
re-acknowledgment, stale head conflicts, same-prefix competing coordinators,
cross-reservation aggregate replay, exact semantics before mutation, tampering,
unknown inventory, malformed/oversized/multiple-link/reparse paths, append and
publication uncertainty, correct explicit recovery after visible intent/journal/
owner. Bounded test subclasses may fail AFTER the real protected persistence
methods; no monkeypatch/global mutation. These injected exceptions are diagnostics,
not proof of actual process/power-loss durability.

Then bounded real subprocess termination at intent/journal/owner publication
boundaries and interprocess contention with harmless temporary children; read
through a fresh process and verify exact previous/new roots and full reservation
retention. Exact test/fixture/source invocation independently admitted before
execution; original native handle terminal personally observed. Relevant canonical,
journal, pure reservation and owner/publication regressions follow. No edit while
tests are live. Source/reviews/runtime evidence/trajectory all preserved.

Actual pinned host and original4x200update pilot remain downstream of durable
store + split owned lease + numerical/authority/declaration/resource admission;
no model/GPU/held-out access through this checkpoint.
