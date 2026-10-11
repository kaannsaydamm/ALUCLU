# Checkpoint169 owner-locked append integration contract

Parent49873d3. Existing publication CAS alone cannot recover intent lost between
page append and owner replacement. Before any page mutation, persist the complete
exact planned transition: previous owner bytes/root, candidate owner bytes/root,
canonical event, declaration, target page/index/identity, exact prior and next
journal heads, creation/rotation choice and review root. Caller independently
pins intent root; local discovery is not current-root authentication.

First prerequisite: journal162 must expose exact bounded append planning using
THE SAME record encoding and resource checks as actual append. Pure planner
accepts exact journal identity/head/canonical event; returns immutable exact line
and next head, no I/O/approval/receipt. Actual append validates disk predecessor,
writes/fsyncs this exact planned line and returns the SAME planned head. Never
duplicate a guessed record format in the transaction coordinator. Tests must
prove byte-for-byte parity and invalid inputs/boundaries before filesystem.

Integrated coordinator then holds owner lock BEFORE page lock through predecessor
check, all-page semantic preflight, durable intent, page create/append/rotation,
full166extension validation and167publication. No page mutation before durable
intent, no invalid semantic event appended, no scientific work launched by it.
Only bounded fixed-layout pages and intent records; original limits unchanged.
Rotating page must bind exact frozen predecessor head and preserve all events.

Explicit resume requires exact independently expected intent bytes/root, not
latest file search. Exact old owner + exact old target page: append intended
record once. Exact old owner + exact intended new target page: publish only,
never repeat append. New page absent/empty exact genesis can complete creation
under same owner lock. Exact candidate owner: identical167reconciliation only,
no additional event/generation/model work. Divergent/truncated/partial/extra/
malformed records reject without truncation, repair, adoption or retry loop.
Inventory and prior page heads must be checked before every recovery mutation.
An uncertain journal fsync needs explicit renewed durable acknowledgement, not
infer durability solely from visible bytes. Retain completed-intent evidence
within declared bounded growth; never silently delete failed research history.

Tests: exact planned byte/head parity, stale concurrent append, first-page/
same-page/rotation, invalid semantic event leaves all storage unchanged, same
owner lock blocks page writer during publication, competing one-event writers,
restart at durable intent/page create/append/fsync/owner-write boundaries, exact
completed idempotence, orphan/divergent intents and partial page failure. Actual
65536-record rotation boundary must preserve full work schedule, not shrink it.

Planner alone is NOT integrated coordinator or recovery. Implementation/review/
regression/crash controls required before integrated writer qualification. No
model/tokenizer/corpus/GPU/heldout/launch; original resource history/global matrix,
external monotone authority, native160 and neural experiment remain OPEN.

## Checkpoint170 implementation and remaining acceptance

Implemented OwnedAppend(owner, separate existing intentions directory): prepare
returns exact immutable AppendIntent bytes/root; commit persists it before page
mutation under owner lock; resume accepts only independently supplied exact
intention and exact previous/candidate owner. Page identity/old/new heads, full
previous/candidate envelopes, canonical event, rotation and review root are
reconstructed and compared, not accepted as opaque authority. No latest discovery.

Recovery explicitly re-fsyncs exact visible next page before publishing. Existing
empty genesis is also re-fsynced before append. Candidate-owner recovery rewrites
identical owner generation through existing reconciliation, never a new event.
Malformed/partial/extra/unrecorded/divergent state rejects without reset/repair.

Checkpoint170 scoped acceptance cases now include first/same/rotated pages,
logical interruption before page creation, after empty creation, after durable
append and after publication without response; exact completed repeated recovery;
stale/competing writer, forced owner-lock hold inside publication, real os.fsync
descriptor-error propagation without owner advancement, rehashed invalid intent,
partial page rejection and actual65536-record rotation preserving entire schedule.
The large test bulk-builds prior65536records then uses actual coordinator for the
finaltwo work events: boundary correctness, NOT sustained sequential throughput.

Next real coordinator qualification must use the actual imported source with
explicit isolated child instrumentation and precise Popen worker/runtime/source
hash assertions, applying checkpoint168's Windows venv-redirector lessons.
Exercise durable intent acknowledgement, new page creation acknowledgement,
journal before/after fsync, and owner replacement before response. Only kill
the exact created owned child; bounded pause/reap, no unrelated process changes.
Compare all resulting owner/intent/page bytes to exact allowed old/new state.
Partial writes reject, never truncate or pretend absence. Faults at native syscall
interiors/power loss remain separate, not implied by Python boundary tracing.

Other open acceptance: retained intentions historical chain/content/completeness
and external freshness authentication; original global research storage/time
reservation and historical accounting; full matrix evidence inventory; native160
and owned launch/restore binding; actual frozen host neural experiment. Current
inventory is only bounded old-file name/type/size plus exact supplied current
intent, NOT an authenticated audit history. Coordinator changes no scientific
schedule, seed, threshold, dataset, prompts, model assets or invocation authority.

## Checkpoint171 commit-interruption qualification scope

Actual imported coordinator/journal/atomic/publication sources are bound by
source origin and SHA256 in isolated child-local tracing. First/same/rotation
commit layouts run fault and exact Popen-owned kill modes at ten Python call/line
boundaries (same layout correctly lacks new-page creation). Four imported module
roots and actual directbase runtime/PID are required before termination.

Do not call atomic writer 'return' an unconditional acknowledgement: trace return
can mean exceptional unwinding. The owner_ack boundary is now the publication
statement AFTER atomic writer successfully returns. Negative control forces an
actual cleanup unlink(directory) failure after replacement at the moved owned
temporary path, with tracing still active. Candidate visibility must not emit
an acknowledgement marker; exact explicit reconciliation can subsequently finish.

This strengthens COMMIT interruption proof, not RESUME interruption proof. Next
qualification must separately start from exact pinned pending-intent states:
intent-only/empty-page/intended-next-page and already-visible candidate owner.
Interrupt resume's intent reacknowledgement, exact target re-fsync, resulting
publication or identical-generation owner reconciliation and pre-response return.
Repeated interrupted recovery must never add an event/generation, adopt a different
intent/root, advance on failed fsync, or reset history. Capture exact target bytes
and all frozen prior pages before each interruption; fail closed on divergence.
Reuse only actual owned child/runtime/source identity checks and bounded reaping,
not stale PIDs. No native call-interior/power-loss or global witness/resource/
matrix/scientific readiness claim follows from these Python-boundary fixtures.
