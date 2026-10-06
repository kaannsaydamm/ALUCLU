# Prospective accumulation failure journal

Status: DRAFT, not implemented, not independently approved. Prepared while the
random CPU parity integration v3 is live on source commit
`417ecc4f6a67cbe039d99671e9a16823153bac48`. This document grants no execution,
training, resource-budget, pretrained-host, or scientific acceptance authority.
Do not change the running attempt or reuse its evidence for later source edits.

## Requirement and inspected gap

The existing `ParityCellFailure` retains the completed single-case prefix,
current/unrun single cases, and pending-pair losses. Its accumulation stage does
not distinguish an off/on microbatch failure from pre-clip comparison, clipping,
optimizer execution, or final full-state comparison. The previous v2 traceback
located an accelerator-init failure inside the reference optimizer step; the
bounded failure record alone could not locate that substage.

Inspected `checkpoint_parity_cell.py`, `checkpoint_accumulation_pair.py`,
`checkpoint_accumulation_step.py`, and the group execution/validation path in
`checkpoint_observation.py`. This is an observability gap, not evidence of a
numerical failure, learning failure, or permission to skip a scientific gate.

## Invariants that must remain unchanged

- Original fixtures, seeds, factor initialization/geometry, 18 single cases,
  pending-pair schedule, and the two 16-microbatch accumulation arms.
- Existing forward order, loss/16, serial loss addition, backward order,
  complete-gradient checks, and frozen-base/input/binding checks.
- Both complete pre-clip observations must be compared before either optimizer
  step; cross-arm storage checks must still precede both steps.
- Norm-1 clipping and existing fixed AdamW configuration, step-1 full factor and
  moment comparison, exact CPU comparison, and original GPU tolerances.
- No retries, catch-and-continue, tolerance relaxation, rollback claim, implicit
  host loading, accelerator access, callback injection, or new run authority.
- Success receipt framing remains unchanged. An empty single-case `unrun` tuple
  does not prove accumulation completion or whole-cell success.

## Proposed bounded data model, subject to review

Use an internal owner-created progress object and immutable snapshots. No public
callable/event callback is accepted. The object must have an exact admitted type
and fixed transition vocabulary; copied failure snapshots contain only bounded
primitive data, not wrappers, tensors, optimizers, graphs, exceptions, or traces.

The prospective snapshot identifies the current arm (`off`, `on`, or no arm),
fixed phase, current zero-based microbatch index or none, and separate completed
forward/backward counts per arm in 0..16. Counts advance only after the operation
returns; set the attempted phase/index before entering the operation. Also keep
separate booleans for complete observation validation, pre-clip parity, cross-arm
storage validation, and each arm's completed clipping, clipped-gradient capture,
optimizer-call return, postconditions, and step-state snapshot. Mark final
full-state comparison only after its complete return.

Execution counts are not validated numerical evidence: a returned backward does
not certify finite/complete gradients, full output validation, or parity. A
returned optimizer call does not certify postconditions or full-state parity.
Failure during clipping or optimizer execution may leave partially mutated
state even when its completion flag is false. No snapshot claims transactionality.

Reject malformed types/counts/phase-arm-index combinations and impossible
ordering using the contract below. Adopt a backward-compatible final optional
immutable `accumulation` field on `ParityCellFailure`, default `None`; existing
five-position constructions retain their meaning.
Propagate a validated inner snapshot into the outer cell error/interruption
without discarding the completed single-case prefix or pending-pair observations.
Do not allow a forged progress record to manufacture an acceptance receipt.

## Proposed phase boundaries

Pair-level boundaries cover off factory/binding validation, off observation,
on factory/shared-base/factor validation, on observation, pre-clip comparison,
cross-arm storage validation, off step, on step, and full-step comparison.

Inside each accumulation observation distinguish group admission/preparation,
forward, scalar-loss validation/scaling, backward, detached-loss capture/serial
addition, total-loss validation, and the existing final live-state/output/
complete-gradient validation and observation capture. Record no additional loss
scalars or tensor values merely for progress. Avoid extra device synchronization
and leave numerical execution unchanged.

Inside each step distinguish observation admission/live-gradient validation,
mutation guard, optimizer creation/configuration validation, clipping,
clipped-gradient capture, optimizer call, frozen/binding postconditions, full
step-state snapshot, and returned record construction. Cover errors before the
current step's `try` block as well as inside it without weakening cleanup.

The following concrete transition/transport proposal requires a new independent
review; the initial draft received code COMMENT and architecture BLOCK for these
previously unspecified details. Instrumentation must be included in subsequent measured timing/resource
evidence; bounded metadata is not a claim that Python traceback retention is
bounded or that a killed process can persist an in-memory snapshot.

## Concrete ownership and propagation proposal (revision 2)

Add a private `checkpoint_accumulation_progress.py` module with exact internal
mutable `_AccumulationOwner` and frozen primitive `AccumulationFailure` records.
This is cooperative execution instrumentation, not a hostile-caller security
boundary. Each owner contains a fresh opaque attempt token, exactly two internal
arm tickets (owner/token/arm identity), and fixed-size primitive progress state.
No ticket/token or live owner is copied into a failure payload. Downstream helpers
admit exact owner/ticket types AND object identity against the owner's registered
ticket and attempt token; a foreign attempt/ticket or subclass is rejected before
mutation. The owner/tickets retain no wrapper, model, factor, tensor, optimizer,
callable, or exception references. Closed/delegated phase identity must match.

The reference-suite entry creates one owner locally before invoking the cell and
passes it via a private optional `_accumulation_owner` keyword. A standalone cell
creates its own when none is supplied; a standalone pair likewise creates its
own. This keyword is data-only and grants no launch/comparison authority. The
cell keeps the owner separately from its existing singles/pending progress and
starts its accumulation state immediately before the pair invocation. Successful
single and pending helpers receive no owner or journal. The pair threads its
owner's off/on tickets through private optional arguments to
`observe_accumulation` -> `_observe_group` -> `_run_group`, and to
`step_accumulation`; callers without a ticket retain their prior behavior.
Admission must reject tickets outside `accumulate=True`, mismatched arm/checkpoint
mode, reused/completed owners, and any nonexact internal object. No contextvars,
global active journal, injected callback, public event hook, or factory API change.

The pair owns the full phase state and outer exception capture, including factory,
binding, delegated pre-try admission, optimizer construction, and late record
construction. Introduce exact `AccumulationError(ObservationError)` and
`AccumulationInterrupted(KeyboardInterrupt)` wrappers only for journaled pair
execution. Keep `str(original)` and chain `from original`; each contains only a
validated immutable snapshot (or `None` plus a bounded journal-fault marker),
never the owner. Ordinary observation/step callers retain their existing error
types. `SystemExit` and other non-Exception/BaseException failures retain their
classification and cleanup behavior; do not claim delivery of a bounded record
for those or abrupt process termination.

Before cleanup, defensively snapshot the owner into bounded primitives. If
snapshot validation fails, mark `journal_invalid` and omit its accumulation
payload; preserve the original numerical/execution exception as primary cause.
Existing pair-owned factor cleanup and cell/reference cleanup remain mandatory.
If cleanup itself raises, preserve the original primary cause and a fixed-size
cleanup-fault marker rather than replacing the primary error; no payload stores
the cleanup exception. Scope cleanup to already registered owned factors, never
caller-base gradients. A normal path without a primary failure treats invalid
journal/cleanup state as an error, never a successful receipt.

The cell copies validated owner state into its optional failure field when
wrapping a pair error or a later final-base/record-construction error. It preserves
its independently captured single/pending prefix even if journal admission or
snapshot validation failed. The reference owner survives cell return locally;
after `_completed_progress(cell)` obtains a valid prefix, final-base/receipt errors
attach its validated snapshot using `replace`. Typed cell errors retain their
existing exact-type propagation path. No journal is embedded in successful
`ParityCell`, `AccumulationPair`, or `ReferenceParityReceipt`; their schemas and
numerical acceptance remain unchanged. Tests substituting the cell must accept
the private data keyword; returned cells cannot fabricate owner transitions.

## Exact execution transition table (revision 2)

Use an attempted current phase, set BEFORE its operation, and a completed phase
ordinal, advanced only AFTER that operation returns. No inference from a later
traceback. Fixed loops compress their history to counts; there is no append-only
event list. Revision3 schema clarification: the exact frozen snapshot contains
`phase: str`, `arm: str | None`, `index: int | None`,
`completed_pair: int`, `off: ArmProgress`, `on: ArmProgress`,
`journal_fault: bool`, and `cleanup_fault: bool`. Exact frozen `ArmProgress`
contains `forwards: int`, `backwards: int`, `captured: int`,
`completed_observation: int`, and `completed_step: int`, nothing else.
All zero-initialized ordinals mean no completed phase. Pair ordinals1..12 follow
the12 ordered operations in the table below; step ordinals1..11 follow the11
ordered step phases below. Observation ordinals1..15 follow `observe_admit`,
`observe_prepare`, `observe_session_enter`, `micro_forward`, `micro_loss`,
`micro_backward`, `micro_capture`, `observe_total`, `observe_session_exit`,
`observe_bindings`, `observe_frozen`, `observe_outputs`, `observe_gradients`,
`observe_capture`, `observe_record`. The loop repeats ordinals4..7 with increasing
counts/index; that ordinal is the last returned operation of the current/prior
microbatch, not a monotone global operation count. Its validation therefore uses
counts/index and the defined loop boundary together. Step and pair ordinals do
not repeat. Nested ordinals persist separately for both arms after arm switching.

There are NO separately stored mutable completion flags. All earlier references
to flags are derived predicates: off/on observation-return means respectively
completed_pair>=3/>=6; off/on step-return means >=9/>=10; successful full comparison
means >=11; pair-return means ==12. Clipping, clipped capture, optimizer return,
postconditions, step snapshot and step record predicates mean respective arm
completed_step>=6,>=7,>=8,>=9,>=10,>=11. Nested record completion alone cannot
substitute for the enclosing call's return predicate. The schema's fixed fault
booleans are diagnostics, never completion evidence. Reject bool-as-int, extra
fields, unknown finite phase/arm values, impossible combinations, and counts or
ordinals outside their exact ranges. Phase/arm/index must agree with attempted
pair/nested position; arm is absent for pair-level comparison/record phases,
and index exists only for the four micro phases. The complete set is constant-
size regardless of failures or call count, with no duplicate mutable truth.

| Attempted phase(s), in fixed order | Entry requirements and update after return |
| --- | --- |
| `off_factory`, `off_bindings` | No arm observations/steps complete; advance pair ordinal only after each returns. |
| `off_observation` | Off factory/bindings complete; enter nested off phases below. Set off observation-return only when `observe_accumulation` returns its complete record. |
| `on_factory`, `on_bindings` | Complete off observation; on counts/steps still zero. Includes existing shared-base, initial-factor, roster/storage checks. |
| `on_observation` | On bindings complete; enter nested on phases. Set on observation-return only after its complete record returns. |
| `preclip_compare` | Both observation-return flags true; complete ordinal only after full comparison returns. |
| `cross_arm_storage` | Preclip comparison returned; complete ordinal only after all existing storage checks return. |
| `off_step` | Both prior checks complete; nested step phases below; mark off step-return only after complete `AccumulationStep` return. |
| `on_step` | Off step-return true, not merely off optimizer-return; nested on step phases. |
| `full_step_compare` | Both step-return flags true; complete ordinal only after the full original comparison returns. |
| `pair_record` | Full comparison returned; mark pair-return only after constructing/returning `AccumulationPair`. |

Nested observation phases for the current arm: `observe_admit`,
`observe_prepare`, `observe_session_enter`, then the following fixed loop, then
`observe_total`, `observe_session_exit`, `observe_bindings`, `observe_frozen`,
`observe_outputs`, `observe_gradients`, `observe_capture`, `observe_record`.
Off has no session enter/exit operation: mark their defined no-op boundaries
explicitly, not as proof of a checkpoint session. Existing comparisons remain in
their current order; output and gradient validation phases encompass their
existing whole-arm bounded loops, with index `None`.

For microbatch index i, entry requires captured=backward=forward=i. Attempt
`micro_forward(i)`; after return forward=i+1. Attempt `micro_loss(i)` for scalar
validation and loss/16; counts unchanged. Attempt `micro_backward(i)`;
after return backward=i+1. Attempt `micro_capture(i)` for existing detached clone
and serial total addition; after return captured=i+1. Only these four phases
carry index i. No index outside them. Always
`0 <= captured <= backward <= forward <= 16`, forward-backward<=1 and
backward-captured<=1; phase-specific equalities above are mandatory. Completed
16 backwards is not complete total/input/base/output/gradient/capture validation.
Observation-return requires all16 captured plus the complete observation record.

Nested step phases: `step_admit`, `step_live_gradients`, `step_guard`,
`step_optimizer_create`, `step_optimizer_group`, `step_clip`,
`step_clipped_capture`, `step_optimizer_call`, `step_postconditions`,
`step_snapshot`, `step_record`. Each requires the immediately preceding phase
returned, with index `None` and the appropriate arm. The first step requires
completed cross-arm validation; on's first step also requires off step-return.
Completed nested ordinal encodes all prior returned phases. Construction of the
final record can fail after snapshot returned; step-return remains false.
Clipping/optimizer failure may have mutated state despite unchanged completed
ordinal. A final comparison failure leaves both step-return flags true but no
full-comparison or pair-return success.

Snapshot validation checks nested ordinal against the owning pair phase, arm,
counts and flags, not just general numeric bounds. Preserve the last complete
pair snapshot for later cell/reference failures, without conflating its execution
completion with the cell/receipt's independent acceptance validation. Early
single/pending failures have accumulation `None`, not a fabricated zero-progress
accumulation attempt.

## RED -> GREEN -> regression and independent gates

After the live v3 attempt is terminal and its original evidence is preserved:

1. Review this design independently for code/security and architecture. Resolve
   ordering, exact-type admission, compatibility, ownership, and cleanup concerns
   before runtime edits. No independent verdict has been received for this draft.
2. Add focused CPU/fake-boundary tests exposing the absent fine-grained record.
   Inject ordinary failures and `KeyboardInterrupt` before/after representative
   operations, including off/on forward/backward, pre-clip comparison, clipping,
   optimizer entry/return, postconditions, and final full-state comparison.
3. Prove preserved completed/unrun framing, immutable bounded snapshots, rejected
   malformed transitions, no tensors/graphs in payloads, cleanup of owned
   gradients, and no hidden retry or skipped operation. A before/after returned
   operation must produce distinct execution progress without overstating parity.
4. Implement only the approved observer mechanism; retain computation and receipt
   behavior. Test outer error and interruption propagation, early admission
   failures, late capture failures, and absence of a journal before accumulation.
5. Run focused tests, relevant existing parity/observation/optimizer regressions,
   and independent exact-byte reviews. Preserve all negative results.
6. Any new real-model integration is a separate reviewed/admitted fresh attempt
   bound to the final source commit, unchanged numerical contract, and fresh
   artifact stem. Prior v3 evidence cannot certify the modified implementation.

Even full completion here establishes only failure observability. Actual pinned
pretrained-host qualification, scientific freeze/accounting, capability controls,
fresh-process retrieval-off durability, and ALC-R0 learning acceptance stay open.
