# Operator status transaction and explicit forward recovery

Baseline a5ac3b620a441ed1a46c96bd8b22979eb484fd69, clean authoritative Desktop.
Previous goal turn PROGRESS: reviewed shared deadline exclusion native proof.
This implements the mutable-publication part of the prospective operator slot,
not the full installed producer/launcher. Source-origin descriptor, generation
rotation/terminal predecessor checks, reservation composition and actual clock/
resource/history facts remain mandatory. No real operator namespace installed.

## Concrete state and interface

StatusPublicationStore(directory, installation_root, generation_root) receives
existing absolute ordinary local namespace and exact64lowerhex roots. Inputs are
transport/test pins, NOT authenticated installation origin. Future coordinator
must resolve them internally from independently reviewed fixed source, never
request/argv/env. Existing worker guard stays unconditional. No model/science.

Fixed names operator.lock (shared original-deadline lock), status.intent.json
and status.json. No fulltree/history/latest scan. Namespace must persist and not
be externally removed/replaced. No hostile-user/ABA/storage-rollback protection.

PreparedStatusIntent is immutable(data:bytes,root:str). Exact canonical schema
alc-r0-operator-status-intent-v1 with keys schema,previous_status,candidate_status.
previous_status is null only for initialization; otherwise exact nested status
object. candidate is exact nested status. Raw cap16KiB, existing fixed-D bounded
parser depth12/token100000/string4096 BEFORE canonical parse; each reconstructed
status independently obeys its stricter4096/depth2/token64/string256 codec.
No arbitrary payload/functions/paths. Recompute full intent root and every typed
status field at decode; caller-created dataclass is never accepted by shape only.

prepare_status_intent(previous,candidate) is pure transition validation. First
sequence1; initialization may already be revoked. Updates exact sequence+1,
same installation/generation, expiry cannot increase, revoked cannot clear.
Sequence exhaustion denies. This transaction layer deliberately CANNOT rotate
generation: adding rotation before one-use/terminal ownership composition would
fake readiness. Rotation remains separately blocking, not removed from roadmap.
Store binds both original roots on every read/write/recovery. Status time is not
evaluated here; observing expired status never grants authority.

## Commit and crash behavior

publish(intent, deadline_ns): validate exact intent/root before mutation. Hold
operator.lock under SAME original deadline. For initialization, BOTH status and
intent absent; exclusive empty intent claim then durable full intent publication.
The claim is the first transaction-record mutation; operator.lock may be created
as bounded exclusion housekeeping before it. Constructor validates syntax/roots;
existing physical namespace is validated during operations under original deadline.
Every error keeps the claim; no unlink/reset/idempotent initialization fallback.
For update, read fully committed prior slot and compare exact previous bytes,
not merely sequence; pending/unknown old transaction blocks new publication.
Atomic-write new intent, bounded readback exact intent; atomic-write candidate
status, then committed readback exact candidate. No deadline renewal. Atomic
helper temp cleanup is not claim release; parent recreation/namespace-loss are
excluded and ancestor identity checks remain before/after each publication.

read_committed_operator_status(directory, installation_root,generation_root,
deadline_ns), also store.read(deadline_ns), is lock-free and finite: bounded
intent read, bounded existing status read, bounded second intent read. Compare
exact intent bytes/root across reads and exact candidate status bytes/typedfields
with slot; check roots/ancestors/deadline throughout. Each intent read max16385
bytes including sentinel, slot max4097. No retry. Mixed/stale/pending/missing/
malformed record rejects. Mere raw read_operator_status remains diagnostic and
MUST NOT be the future installed producer's publication observation. During
publication even a normal updater may cause live denial; availability is not
claimed. Read consistency does not authenticate source or detect every ABA.

recover(intent, deadline_ns): caller supplies exact previously pinned full intent,
not file-discovered latest intent. Hold same operator.lock; stored full intent
must equal caller bytes. Slot absent only for initial intent, or slot equals
exact previous/candidate. Forward-complete candidate if absent/previous; candidate
already present verifies idempotent recovery. Third state/changed intent/empty
claim denies. Never rollback old status, delete evidence, free consumption or
restart a scientific attempt. Prior intents overwritten on ordinary updates:
this bounded current transaction is NOT an archived full-history journal or
restart anti-rollback. External pinned expected roots, one-use consumption and
future installed ownership remain necessary; no freshness claim on a restored
whole directory. Publication errors never silently call recovery.

## Dependency integration and acceptance

Commit/recovery owns operator lock only, never takes reservation locks in reverse.
Future exact coordinator holds operator then bounded reservation ownership and
pins committed status before create/resume; existing raw-slot watch consumer is
not yet that producer. The next connection must use committed reader and prove
pending publication stops actual owned work, not leave raw-only production path.
This checkpoint cannot close full operator writer, generation rotation, trusted
producer or mandatory launch gates. No approving status substituted for missing
historical/accounting/resource/clock evidence.

TDD: RED missing module; valid initialize/tighten/revoke; stale-root and concurrent
two-process writer rejection; malformed/forged intent/status/root; expiry extension,
revocation clearing, generation change, sequence skip/overflow; pending transaction
reader rejection; exact initial/update forward recovery and third-state refusal;
empty sticky claim refusal; deadline/unsafe path/multilink/junction denial.
Fresh harmless subprocess crash at full-intent-before-status boundary, retained
native exit17 and fresh committed-reader rejection, then explicitly pinned
forward recovery. Use private diagnostic step override, not global monkeypatch
or public callback injection; no real scientific child. Run status/consumption/
deadline-lock relevant regressions under original owned runner. Two independent
design and final code/architecture/evidence reviews; exact raw hashes retained.
