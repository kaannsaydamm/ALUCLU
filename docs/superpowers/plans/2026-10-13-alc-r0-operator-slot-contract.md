# Concrete local operator installation and bounded live slot

Baseline878c7b5. Prospective contract, not installed authority. Cooperating local
operator/runtime; no hostile same-user/OS or simultaneous full-storage rollback
protection. Existing worker denial is unchanged. First target is exact live-slot
codec/reader, then independently reviewed installation/updater/lease integration.
This is one component of the actual producer, not a substitute for it.

## Installation origin (must be reviewed before enabling any launch)

Future fixed coordinator source contains one reviewed absolute operator directory
and immutable installation descriptor root. Neither comes from request/argv/env
or nearby config. Proposed logical directory is
`C:/Users/kaann/AppData/Local/ALUCLU/research/alc-r0-smollm2-135m-v1/operator`.
Windows redirection may change its physical location: actual resolved ordinary
directory and all ancestors must be observed and independently pinned at real
installation, not trusted by this proposal. No directory is created now.

Descriptor `installation.json` canonical bytes, max16KiB, immutable after review:
schema, owner_decision_root, source_export_root, runtime_inventory_root,
snapshot_inventory_root, fixture_source_root, invocation_root,
accounting_policy_root, historical_coverage_root, clock_evidence_root,
resource_projection_root, declaration_genesis_root. Every root64lowerhex.
schema is alc-r0-operator-installation-v1. No accepting booleans/numeric guessed
history in this descriptor. Referenced factual evidence must separately verify.
Descriptor root in reviewed fixed source is the origin anchor on the cooperating
host; merely supplying same-shaped JSON is never installation provenance.
Updates of these pins require separate review/new installation, not live changes.

## Exact mutable status slot

Single fixed child `status.json`, canonical bytes1..4096. EXACT keys:
schema, installation_root, generation_root, sequence, revoked, expires_utc_ns.
schema=alc-r0-operator-status-v1; roots64lowerhex; sequence/expires are canonical
decimal strings1..2^63-1; revoked exact bool. Unknown/missing/extra fields deny.
No file path, executable, callback, scientific selection or resource assertion.
`generation_root` identifies the separately pinned per-control generation record
binding control/a001/initial, reservation/request/root/clock/child publication.
That generation record/handoff remains a subsequent exact contract, not solved
by this slot. Installation has max three declared D controls, no generalized jobs.

Read API `read_operator_status(path, deadline_ns)` is explicit observation only,
for temporary tests and later fixed internal production caller. It returns frozen
OperatorStatus(data/root/installation_root/generation_root/sequence/revoked/expiry).
Neither constructor/decoder/reader authenticates origin, evaluates time or creates
permit. Production caller may NOT choose path from request/CLI/environment.
Decoded sequence/expiry are exact Python integers, not lexical strings. The
string lexical cap counts raw UTF-8 content between quotes (escaped spellings
may therefore be rejected more conservatively). Observed replacement conflict
denies; no guarantee every overlapping replacement is detected. Installation
and generation changes stop a running consumer, never reset its sequence state.
Implement bounded lexical scan before canonical JSON parse: maxdepth2, maxtokens64,
maxstring256, max4096bytes; duplicate/trailing/noncanonical reject. Reuse existing
bounded lexical parser (if compatible) rather than unbounded json.loads.

Reader reuses reviewed ordinary local path/ancestor/leaf/open identity semantics,
single-link and no reparse points. Read once, initial/open size1..4096, decreasing
remaining sentinel allowance max4097, exact same-source fingerprints, ancestor
identity recheck, deadline throughout. No retry or latest discovery. The caller
owns deadline and interruption of blocking OS calls; Python checks cannot interrupt
OS I/O. Status updates use atomic replacement: if a read overlaps replacement,
observed inconsistency denies/stops, no in-reader retry. Record hash identifies
bytes observed, not an expected immutable hash (revocation may update slot).

## Updater, exclusion, and fresh observations (not yet implemented)

Fixed operator writer only, never worker. Total lock order: operator.lock BEFORE
reservation global.lock BEFORE journal locks. Live status read is lock-free,
bounded; no fulltree scan under250ms. Long verification while holding locks obeys
original deadline; no unbounded blocking lock admission in actual integration.
Writer atomically publishes canonical slot and retains exact prior/candidate intent
under operator ownership. sequence increases, expiry cannot be extended for an
already running generation, revoked is irreversible for that generation; new
generation cannot resume a consumed control. Stale/mixed/unknown publication denies.
Durable updater/intent recovery still requires TDD and separate implementation;
this document does not claim existing atomic-write helper alone proves recovery.

Each reader retains sequence/root: reject regression and equal-sequence changed
bytes; changed generation stops existing run. Restart anti-replay relies on durable
per-control reserve consumption, not this in-memory minimum or a nonce. Before
create hold operator then reservation ownership, consume exactcontrol once before
child creation; uncertainty never frees it. Before resume refresh same installation,
generation/status and exact child/request; do not accept slot as all factualproof.
No producer takes these locks in reverse. Live monitor observes same installedslot
and separately established monotonic/UTC upper-bound domain; expired/revoked/missing/
malformed/overdue stops. Origin/time evidence cannot be filled by decoder fields.

## TDD next step and boundary

After two independent design reviews: codec and single-read reader RED/GREEN,
negative duplicates/depth/numeric/types/size/path/link/expired read, harmless
temporary status update observation. No actual operator installation or updater,
guard replacement, model/CUDA/heldout work, history-zero or clock-reset.
Relevant request/wire/canonical/watch regressions; exact artifacts and sourcepins.
Acceptance is bounded status observation only; actual producer/updater/generation
binding/one-use/lease/worker handoff/resource/history/GPU2 remain OPEN.
