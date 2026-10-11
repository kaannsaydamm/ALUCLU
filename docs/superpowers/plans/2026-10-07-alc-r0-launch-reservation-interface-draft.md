# Local qualification launch and reservation interface

Status: PROPOSED, pending independent design review. No implementation or launch.
Parent9bd9da737e96ceb5a0b63ac9b0c2929ee6fee93b. Owner accounting method/local
training direction is approved; numeric history/clock remains a distinct input.
This is research execution plumbing, not the downstream final ALC container.

## Concrete gap and first implementation scope

Current checkpoint_owned_process._execute creates a job-owned suspended child and
immediately resumes it. It has no durable reservation/child-identity publication
step. OwnedAppend commits one attempt event, not global resource reservations.
Do not wrap run_owned_process and pretend the missing interval is covered.

First component proposed for TDD: pure ReservationReplay, exact immutable
declarations/events and state transitions described below. It has no filesystem,
OS processes, model/runtime imports, reservation creation, authentication or
launch permit. This is one REQUIRED part of the full adapter, not a substitute.
Actual disk coordinator and split owned-process adapter follow only after review
and negative integration tests. All existing scientific gates remain blocking.

## 1. Authority producer and verified input boundary

Owner direction originates in the direct human chat, preserved in the committed
owner-decision record. A document/hash alone is not activation authority. Trusted
local coordinator owns the reviewed operator configuration and independently
pins its current authority generation; workers/output directories cannot choose
this root, revocation status or a latest trusted generation.

Proposed VerifiedLaunchContext input fields: policy_version, owner_decision_root,
authority_generation, valid_from_utc_ns, expires_utc_ns, revoked, declaration_root,
source_export_root, runtime_inventory_root, fixed_entrypoint_root,
invocation_root, accounting_policy_root, accounting_coverage_root,
effective_charge_kind (observed/allocation_upper_bound), effective_gpu_ns,
clock_kind (observed/conservative_boundary/prospective_pending), clock_utc_ns,
current_global_owner_root, numeric_bounds_root. Unknown required roots/values
deny. Exact typed context is an internal verified input, not a user JSON permit.
The producer verifies the original owner authorization and two independent
exact-byte declaration/source/invocation reviews, current revocation/generation,
provenance/coverage of numeric history and clock BEFORE constructing it.

Verifier compares against independently pinned operator state; it must not accept
caller self-asserted booleans, signature-shaped strings or hash equality as origin
authentication. Revalidate authority generation/expiry/revocation under global
reservation ownership immediately before child creation and before resume.
Coordinator may revoke without erasing evidence; active owned work terminates
through owned handles and retains charge until reconciliation. This interface
does not claim producer/verifier implementation exists. No extra enterprise IAM
or portable capsule cryptography is introduced for this local research boundary.

## 2. Exact declarations, ceilings and bounded units

Launch declaration binds experiment/run/attempt IDs, qualification lane,
ordered work IDs, source/runtime/entrypoint/invocation/assets roots, device/dtype,
original-rule provenance, wall ceiling, one-GPU maximum (or CPU/no-CUDA),
memory/physical/research/log projections and named outputs. Source command and
environment are fixed reviewed data, not arbitrary callback/module/shell input.

Original matched D is45minutes; E1/E3 are30minutes and E2 is10minutes under
existing detail. Full pilot is separately four200-update jobs, at most2hours
each, seed20260916; never classify a pilot as D or reduce its update schedule.
Separate all-layer q/v qualification has no approved D/E ceiling mapping yet:
it stays undeclared/denied until its exact work declaration/ceiling is reviewed.
No new allowance or automatic CPU/GPU fallback. Existing RunSpec attempt rules,
one exact resume/one repair and resource retries remain unchanged.

Proposed implementation bounds, NOT scientific thresholds: each declaration/event
<=16KiB RFC8785 bytes; complete replay <=4096 distinct declarations (including
released tombstones), <=512 nonreleased reservations, <=262144 events, <=4MiB
total declaration bytes and <=32MiB total event bytes. Validate all byte/count
limits BEFORE materializing or appending a record. Fixed schemas bound field
counts; the encoded-byte caps are not an RSS measurement. Overflow/cap denial is
atomic: previous state/root unchanged. No forgetting released IDs or resetting
history when a cap is reached. Initial implementation replays COMPLETE history
from explicit genesis only: no suffix, caller summary or snapshot shortcut.
Future paging/snapshot support needs separately verified complete predecessor
coverage. Existing per-run paging is not that proof.

IDs are 1..128 ASCII bytes matching [A-Za-z0-9_-]+; roots exactly64lowercasehex;
owner_nonce exactly32lowercasehex. Resources/UTC/monotonic values are integers
0..2^63-1, excluding bool/float. PID is1..2^32-1, process creation FILETIME is
1..2^64-1. Windows exit_code is null (unknown) or unsigned32 0..2^32-1, never
bool; it is not POSIX signed status. Sequences start at1 and are consecutive.
All arithmetic is checked before mutation; derived sums also fit signed64.
Wire encoding: ALL numeric fields listed in this document are canonical decimal
STRINGS, matching 0|[1-9][0-9]*, at most20 characters, then range-checked and
converted to exact Python integers internally. JSON numbers/bools/floats are
rejected for these fields. Nullable exit_code alone may be JSON null. This avoids
RFC8785's binary64-safe integer domain silently rounding UTC ns or FILETIME;
canonicalization remains unchanged. Typed views expose exact integers.
Ordered work IDs are independently bound through RunSpec roots. Policy version,
charge/clock kinds and roots remain explicit.
Unknown estimated history is not silently written to ProgramAccounting's
observed fields; a separately reviewed policy adapter will interpret provenance.

## 3. Bootstrap and storage ownership

Denial-only preflight captures entry monotonic origin BEFORE hashing/replay.
Import-safe root/R0/cognition helpers are now tested; composed canonical journal
still uses original RFC8785 dependency, no stdlib JSON fallback.
Missing global owner/journal files do not mean empty history. Genesis requires
explicit reviewed initialization and externally pinned empty-history scope.
One cooperating global coordinator lock serializes every reservation transition
and aggregate accounting update. Existing per-run OwnedAppend is used for attempt
events but cannot substitute for this global lock/publication root.

## 4. Pure reservation lifecycle and later durable ordering

Pure declaration has EXACT fields: experiment_id, reservation_id, run_id,
attempt_id, segment, declaration_root, device, useful_wall_ceiling_ns,
cleanup_ceiling_ns, charge_envelope_ns, gpu_reservation_ns,
research_growth_bytes, physical_growth_bytes, stdout_limit_bytes,
stderr_limit_bytes. experiment_id is alc-r0-smollm2-135m-v1; run_id obeys the
existing OriginalRunSpec grammar; attempt_id is a001/a002/a003; segment is
initial/resume; device is cpu/gpu. cleanup_ceiling_ns is10000000000 for the
current Windows primitive. Useful ceiling is positive, charge_envelope_ns >=
useful_wall_ceiling_ns + cleanup_ceiling_ns. GPU declaration reserves at least
that full envelope (one GPU); CPU reserves0GPU ns. These are mechanical
constraints on externally reviewed bounds, NOT authority to choose a ceiling.
Existing independent declarations bind the authority/work/source roots.

One immutable declaration per reservation_id and (run_id, attempt_id, segment).
Only one live reservation per (run_id, attempt_id); resume requires the matching
initial segment already RELEASED. This does not admit a resume: OriginalRunSpec,
checkpoint and authority verification remain separate requirements. Initial
complete declarations are ordered lexicographically by reservation_id; genesis
root is SHA256(RFC8785({"schema":"alc-r0-reservations-v1","declarations":
[the complete ordered canonical declaration objects]})). No declaration
replacement or duplicate IDs, even after release.

Every event has EXACT common fields: sequence, previous_root, reservation_id,
kind, evidence_root, plus ONLY the kind-specific fields below. Missing/extra
fields reject. sequence is global, consecutive; previous_root equals current
replay root (genesis for first event); next root is SHA256 of RFC8785 encoding of
the whole event. This binds order/predecessor but is integrity, not provenance.
Evidence roots are internally verified inputs at the later coordinator boundary,
not authentication of arbitrary user-supplied strings by the pure component.
Every event must reference an existing declaration; reserve may occur only once.
No duplicate/reordered event, invalid predecessor, mismatched roots or event
after RELEASED. Event types / legal predecessor / retained fields:

| Event | Predecessor -> successor | Required additional fields |
| --- | --- | --- |
| reserve | absent -> RESERVED | declaration_root, entry_utc_ns, clock_domain_root, entry_monotonic_ns, useful_deadline_monotonic_ns |
| child_created | RESERVED -> CREATED | pid, creation_filetime_100ns, owner_nonce, identity_receipt_root |
| identity_published | CREATED -> READY | identity_receipt_root, publication_root |
| running | READY -> RUNNING | resume_receipt_root |
| terminal | RESERVED/CREATED/READY/RUNNING/UNCERTAIN -> TERMINAL_PENDING | fact_kind, identity_receipt_root or null, exit_code or null, terminal_fact_root |
| uncertain | RESERVED/CREATED/READY/RUNNING -> UNCERTAIN | reason, prior_state |
| reconcile | TERMINAL_PENDING -> RECONCILED | resource_charge_root, wall_kind, effective_wall_ns, effective_gpu_ns, growth_observation_root, materialized_research_bytes, materialized_physical_bytes |
| release | RECONCILED -> RELEASED | global_publication_root |

reserve requires matching declaration_root and useful deadline = entry origin +
declared useful ceiling (checked addition). clock_domain_root binds the particular
boot and monotonic clock execution domain through external verified evidence.
Numbers from different domains cannot be compared. Reboot invalidates operational
reuse of the old deadline; it does not change the persisted origin/envelope or
create a new allowance. An independently admitted resume policy must account for
the consumed original allowance before a new segment is declared.

Identity receipt publication must equal the exact retained child-created receipt.
Known PID/FILETIME/nonce/receipt survive all later states. Nonce is unique across
created reservations. Running requires exact prior READY; no skipped states.
uncertain reason is one of creation/publication/resume/timeout/reboot/terminal;
prior_state must equal actual replay state. Repeated uncertain, uncertainty from
TERMINAL_PENDING/RECONCILED/RELEASED and overwriting known identity are forbidden.
Missing identity in UNCERTAIN never establishes absence of a child.

terminal fact_kind is verified_no_child or verified_owned_tree_terminal.
verified_no_child requires null identity and exit_code, and no retained created
identity; RESERVED or creation-uncertain may use it only after independently
verified negative creation evidence. PID absence alone is not that evidence.
verified_owned_tree_terminal requires matching retained nonnull identity (and
therefore known owned child), externally verified root-handle termination and
zero private-job members. Exit code may remain unknown without implying PASS.
If creation occurred but identity cannot be established, retain UNCERTAIN until
separately reviewed recovery can supply proof; no fabricated terminal transition.

Unknown charge remains TERMINAL_PENDING: do not append reconcile until complete
verified facts arrive. reconcile metrics are NEVER null; wall_kind is observed
or allocation_upper_bound; effective GPU charge is0 forCPU and equals effective
wall charge for the fixed one-GPU scope. Exact charge provenance must include
preflight/cleanup coverage; pure integers alone cannot establish that coverage.
Exit-code unknown may release only after valid terminal-tree/no-child proof and
complete charge; release is not training validity or scientific PASS.

Pure replay retains immutable declarations/events and original reserved amounts.
Aggregate outstanding GPU ns sums original reservations for ALL nonreleased
states, including RECONCILED; consumed GPU ns sums reconciled RELEASED charges.
At release, atomically transfer reservation to consumed actual/bounded charge;
never sum both for the same reservation. A charge larger than reservation is
retained in full, flagged overrun and denies further admission, never clamped.
The pure component exposes arithmetic/overruns, not a launch permit.

For space, original declared research/physical growth remains held before known
materialization. reconcile binds materialized byte values to one independently
verified growth_observation_root, with each <= corresponding declared growth;
otherwise reject and retain full reservation pending reviewed overrun recovery.
Observed filesystem usage already includes those materialized bytes. Remaining
growth = declared - materialized for RECONCILED; other nonreleased states retain
full declared growth conservatively. RELEASED contributes no pending growth.
External capacity checks must use that SAME observation root when subtracting
materialization; mismatched/unknown observations use full pending growth or deny,
not a guessed reduction. Released charge history remains in all-time consumed
accounting. Checked aggregates/limits apply to the complete retained history.

Later durable coordinator sequence: global lock/revalidate -> fsync reserve intent
and trusted publication -> create suspended child atomically in private job ->
observe process creation FILETIME through owned handle -> persist child identity
and independently current reservation publication -> revalidate deadline/authority
-> resume exact owned thread -> publish running observation. Parent's private
job handle alone is not a persisted identity; PID alone is never a recovery key.
Creation -> identity publication uncertainty retains reservation, kills/drains
only owned handles if accessible, and denies new attempts. Parent crash cannot
justify attaching to/reaping a reused PID or accepting zero charge.

Split owned-process API proposal: context-managed created-owned lease,
publish_identity(binding), resume_verified(binding), wait_terminal(). No arbitrary
caller callback executes inside the creation interval. Existing run_owned_process
keeps its current trusted primitive contract; qualification adapter uses only the
new tested lease. No scientific launch through the old bypass route.

Owned-tree release requires job active_processes=0, root handle terminal observed,
reviewed worker receipt matched (or separately verified missing/invalid receipt
failure, never PASS), and complete charge. Verified-no-child release instead
requires its independent negative creation proof and complete charge: it cannot
require a worker receipt for a worker that never existed. Both use the same
global release publication; neither means successful scientific execution.
Timeout/observation timeout/reboot never implicitly release. Crash-forward exact
intent recovery uses predecessor/candidate roots, no rollback or latest discovery.
Resume remains an independently admitted same-attempt operation with exact prior
checkpoint/work/source, never a new deadline or hidden retry.

## 5. Resource observations and bounding policy

At entry/precreation/preresume/terminal observe current research bytes and Cfree,
pending research and physical growth separately, available system/GPU memory,
fixed device scope and stdout/stderr length. Review declared upper bounds before
launch; no numeric projections are invented by this document.
Include log/receipt/journal copies, temporary output, checkpoint staging and asset
loading/hash overhead in peaks. Enforce declared stream byte caps at runtime by
owned bounded sinks/monitor; truncation or excess is INVALID, never a successful
partial receipt. Parent also caps read/parse allocation before opening outputs.

Charge entry preflight and full owned allocation/cleanup lifetime conservatively;
retain wall/phase/cleanup diagnostics separately. Capture entry origin BEFORE
hash/replay; useful deadline includes that preflight. Reserve a charge envelope
covering the full useful ceiling plus the existing10second cleanup bound BEFORE
creation. Entry/pre-reservation preflight still needs external coverage; missing
coverage denies execution, not zero charge. Timeout/failed cleanup never releases
the held reservation; even an envelope overrun remains fully accounted. No
absolute scientific budget or numeric historical charge is calculated here.
UTC45day program window remains independent; expiry and remaining-budget checks
must include full reserved overhead/tail, not just worker inference/train time.
Historical bounds need coverage/device/envelope proof under approved owner method.

## Acceptance and implementation order

Design review must decide pure model schema/state details and whether external
producer/ceiling/numeric dependencies block ONLY actual launch or also proposed
pure replay implementation. Do not call this full-launcher implementation-ready
while those dependencies are unresolved. No source/test edits before that verdict.

TDD first pure replay: RED missing module; GREEN exact declaration/events, unknown
facts, duplicates, malformed/truncated/oversized values, illegal transitions,
identity mismatch, no-child uncertainty, later completion of initially unknown
charge, clock-domain mismatch, retained identity, overrun, complete-history byte
caps and checked outstanding/consumed/materialized sums. Relevant regression
with synthetic inputs only. Then durable interprocess reservation/crash recovery,
then owned lease identity-before-resume tests using harmless temp children.
Actual host invocation needs final exact-byte review and resource admission.
Real pinned host -> original fixed pilot -> full grid -> held-out controlled
evaluation/fresh-process learning proof remains the real objective. No toy or
denial-only component can replace it; no downstream product gates promoted.
