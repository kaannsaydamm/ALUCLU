# Real-host qualification launcher and preflight — prospective draft

Status: DRAFT_PENDING_INDEPENDENT_REVIEW. No implementation, asset access,
accounting-policy adoption, invocation admission or launch authority is supplied.
Parent checkpoint c037dfc94e8900082d7516246f821adb99347054. The source-bound random
CPU v4 integration passed; that fixture cannot authenticate the pretrained host.

## Scope and existing boundaries

Prepare the actual-host qualification execution boundary, not capability training
or final ALC product infrastructure. Preserve the original scientific plan,
matched D grid, separate q/v contract, seeds, thresholds and resource ceilings.

Existing components are not interchangeable:

- `checkpoint_resource_admission.assess_resources` performs pure arithmetic on
  caller observations. `resource_fit` neither authenticates nor reserves.
- `attempt_state` supplies declared attempt semantics; `attempt_journal` supplies
  bounded storage. Neither creates an authenticated measurement history.
- `checkpoint_owned_process.run_owned_process` owns a newly created Windows x64
  process tree and an absolute deadline. It is not admission or a sandbox.
- `checkpoint_parity_qualification.run_parity_qualification` loads the pinned
  host/tokenizer and composes the ORIGINAL official suite and matched D matrix.
- `reference_official_suite` and `reference_parity_suite` are SEPARATE all-layer
  q/v computations. They must not replace or extend the original matched grid.
- `host_evidence.observe_verified_host` currently requires BF16. Do not apply its
  validator to CPU FP32, cast solely to satisfy it, or silently broaden its schema.

The proposed parent imports no Torch/model/tokenizer modules during denial-only
preflight. Scientific workers are fixed reviewed entry points, not a caller-
provided Python callback, arbitrary module, shell command or executable payload.

This is a REQUIRED FUTURE boundary, not current package behavior: `aluclu` eagerly
imports computational modules and `aluclu.alc_r0` imports host support. A normal
import of the named pure helpers traverses these initializers. Before implementation,
separately specify/review either an import-safe stdlib bootstrap/package boundary
or compatible lazy initializer changes. Do not use arbitrary path-based loading to
bypass package initialization. Fresh subprocess tests must reject Torch/Transformers
imports and prove denial can finish without them or asset access. This import
boundary is a first implementation prerequisite, not a promised property today.

## Required admission order

0. At entry, before source/runtime hashing, history replay or any other preflight,
   capture the monotonic attempt origin. Once a separately authenticated applicable
   ceiling is known, derive its absolute deadline from THAT original instant; all
   elapsed work is charged. Unknown ceiling/authority denies; it never renews the
   origin. Bounded denial processing has no scientific launch authority and must
   not be relabeled an admitted attempt. UTC program-window checks remain separate.
1. Resolve the authoritative Desktop source export and isolated research/output
   roots. Bind committed source bytes, dependency/runtime identities, entry-point
   bytes and exact invocation/environment. Hashes are identity links, not proof
   that the caller has approval. Refuse mutable/unreviewed runtime/source routes.
2. Authenticate the reviewed run declaration and its relation to original attempt
   and resource rules. Separate original qualification from q/v qualification.
   The accounting phase/ceiling mapping for the separate q/v invocation is an OPEN
   review item: never assign it D merely because the arithmetic helper accepts D,
   create a new allowance, or bypass budget/calendar checks with a synthetic label.
3. Authenticate reconciled historical coverage and approved accounting policy,
   evidenced first-development instant, pending reservations and trusted journal
   head. Unknowns remain denial, including CPU routes. The allocation-wall draft
   is NOT adopted. Method approval alone does not approve numeric charge/clock.
4. Under exclusive cooperating ownership, replay declared attempt semantics and
   reservations; collect current storage/resource observations and conservative
   peak growth. Use the entry-origin absolute deadline, never a new one. UTC
   program deadline remains distinct. Full preflight/load/hash/serialization and
   qualification overhead is included; cleanup is retained separately, not free.
5. Persist and fsync exact intent/reservation before any scientific child can run;
   publish the trusted monotone owner state with a separately specified reservation
   transaction. Existing journal/owned-append persistence is NOT a global resource
   reservation protocol; do not treat it as one without the missing composition.
   Refuse conflict, malformed/truncated journals and uncertain publication. Never
   infer an empty history or zero outstanding reservation from missing files.
6. Revalidate storage, reviewed bytes, current reservations and deadline immediately
   before launch. Bind each child to the reserved attempt and exact fixed command.
   Use the existing creation-time job ownership primitive, explicit environment,
   exclusive output creation and no shell. A denial must not start a child.
7. The worker independently checks offline and deterministic context, exact device/
   dtype, pinned revision/inventory/tokenizer and immutable fixtures, then loads
   one frozen host. CPU FP32 and CUDA0 BF16 are separate declared attempts with
   no automatic fallback. CPU must not initialize CUDA; GPU is one physical device
   with the existing math-reference backend and tolerance settings.
8. Execute only the declared complete suite. Retain typed bounded stage failures
   and causal diagnostics; no retry, smaller grid, tolerance change or skip.
   Revalidate base bytes/roster/configuration and assets at terminal boundaries.
9. Parent observes the owned tree's terminal state, parses bounded worker outputs,
   and cross-checks invocation/source/host/fixture identities and complete schedules.
   Exit0 alone, JUnit alone, or a stale/copied receipt is insufficient. Reconcile
   resource charge under the approved convention before releasing reservations;
   timeout/reboot/uncertain tails retain outstanding reservations until reconciled.
10. Publish terminal evidence and independent assessment. Windows evidence is not
    Linux/native macOS qualification. Exactly two fresh-process qualifications,
    where required by the original contract, remain independently admitted jobs.

## Test-first decomposition before any actual-host invocation

Implement a pure bounded preflight decision contract first, with explicit missing
authority and provenance denial reasons. It must not accept hashes as signatures,
invent historical values, import heavy runtimes or touch model/corpus assets.
Then implement durable reservation/publication composition using existing owned
journal primitives; only afterward add the fixed parent/worker execution adapter.
Keep schema/policy amendments separately reviewed rather than repurposing existing
attempt fields such as `gpu_ns` or allowing arbitrary caller-defined thresholds.

Required RED/GREEN/regression cases include missing/unknown historical inputs,
wrong source/runtime/entry-point roots, wrong declaration/phase, stale trusted
head, competing reservations, truncated/oversized/duplicate input, peak-growth
understatement, asset/symlink/path substitution, preflight deadline expiry,
publication crash boundaries and denial-before-child creation. Fake local child
tests cover nonzero exit, timeout, surviving descendant, reused PID and partial
output. They must not load the model, count as scientific attempts, or certify
hostile privileged escape containment. Actual runtime invocation needs its own
exact-byte independent review and resource admission after these tests pass.

## Open decisions and acceptance limits

Independent review of initial bytes907912ce38cb916a84f32ad3525bab673f96e2da3776ce838ae376ed2c176583:
code/spec/security COMMENT for draft preservation, REQUEST CHANGES for implementation;
architecture CLEAR for draft preservation, BLOCK for implementation readiness.
The original sequencing/import flaws are preserved here as negative design evidence.
The entry-origin and import-boundary corrections above require exact-byte rereview.

Before any implementation, resolve five specific interfaces in a subsequent
reviewed contract: (1) bounded authority inputs, trusted producer/verifier, policy
version, expiry/revocation and owner responsibilities; (2) separate q/v declaration,
work set and approved ceilings; (3) stdlib bootstrap/import isolation; (4) explicit
reservation/created-owned-child/identity-publication/resume/terminal crash states;
(5) units, coverage and justified upper bounds for memory/storage/log growth and
charge. Missing child metadata after parent failure never proves zero charge or no
surviving child; reservation persists until independently reconciled. Existing
owned-process creation-time containment alone does not publish/authenticate its
reservation relationship. No guessed interface or policy may be implemented.

This draft does not claim the launcher exists. Exact bounded manifest fields,
trusted reviewer/owner authority interface, separate q/v declaration/ceiling map,
resource measurement convention and peak/log growth bounds require review before
implementation. Source/runtime binary provenance cannot be inferred from package
version strings. Snapshot checks are not reservations against unrelated processes.

Still OPEN: complete accounting/clock reconciliation and user authority, actual
host invocation/reproducibility, D/E1/E2/E3 qualification, rights/evaluator/sealer,
scientific freeze, capability controls and retrieval-off fresh-process durable
learning. The program remains active; no downstream product claim is promoted.
