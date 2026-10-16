# Fixed original D worker and coordinator composition

Status: corrected design preserved; independent code APPROVE / architecture
CLEAR for preservation and next exact wire-contract specification only.
Only exact wire-contract specification and denial-only preparation are proposed
for admission now. No accepting worker/codec or full-launcher readiness claim.
Parent63bc4b9126b7e890979f3cc63ce1e2b72ac42254. This proposal does not launch
anything, adopt historical numbers, or reopen the accepted Task2 gate.
Owner method/local-training direction is already approved. Missing factual
history/clock coverage remains a blocker to actual execution, not design work.

## Scope and implementation target

ONE fixed worker invokes existing run_parity_qualification exactly once in one
fresh process. ONE coordinator composes accepted allocation_policy,
ReservationStore and ReservedOwnedLease. No generic experiment runner, callback,
module selector, command template, scientific RunSpec extension or new product
infrastructure. This is D plus existing official-forward regressions, not E1/E2/
E3, all-layer q/v qualification, a pilot, or a retrieval-off capability result.

Closed controls remain:

| Control ID | Device/dtype | Fresh process |
| --- | --- | --- |
| alc-r0-qualification-v1-d-cpu-fresh1-s20260916 | cpu/torch.float32 | CPU1 |
| alc-r0-qualification-v1-d-gpu-fresh1-s20260916 | cuda:0/torch.bfloat16 | GPU1 |
| alc-r0-qualification-v1-d-gpu-fresh2-s20260916 | cuda:0/torch.bfloat16 | GPU2 |

Each useful deadline is original entry monotonic time +2700000000000ns;
shared owned cleanup tail10000000000ns, full charge envelope2710000000000ns.
GPU reserve covers that entire envelope for one physical GPU; CPU reserve is0.
Preflight hashing/replay consumes that same useful allowance. Pre-reservation
work also needs explicitly verified external coverage, not uncharged GPU time.
Two GPU controls are separate reservations/receipts, not retries of one control.
Producer/coordinator must bind each control to exactly a001/initial and one fresh
invocation, rejecting a002/a003, resume and any subsequent invocation even after
release. Replay's broader structural attempt grammar is NOT authority to retry D.

## Trusted inputs versus transport

The operator-side producer is not implemented by a worker request parser. Its
trusted state must pin owner-decision evidence, independently reviewed exact
source/runtime/invocation/declaration, authority generation/revocation/expiry,
historical numeric coverage/clock, approved bounds and current owner root.
It constructs an internal VerifiedLaunchContext only after verifying all those
facts. Hashes bind bytes; no request can authenticate itself by carrying hashes,
"approved" booleans or review-shaped labels. Unknown facts deny actual launch.

Implementation must not expose a public constructor that converts arbitrary
JSON into a verified permit. The producer/verifier and the operator provenance
integration require concrete independent review before operational use. A
synthetic verifier in tests cannot be selected by the production entrypoint.
This proposal deliberately does not claim numeric reconciliation or producer
implementation is solved. Fixed worker/codec work may be implemented and tested
without exposing a functioning launch path; full coordinator readiness requires
the concrete verified producer, not a stub that always accepts.

Worker input is transport, NOT authority. Fixed command is the reviewed absolute
research Python executable, one reviewed absolute worker script and one absolute
request file. No -c, arbitrary -m, shell, executable override or callback argument.
The coordinator creates a new bounded regular single-link request file in its
owned output namespace. It pins its bytes/root before creation and again before
resume. Worker reads that exact file once, with byte cap before decoding, rejects
duplicate keys/trailing data/noncanonical bytes, then holds immutable values.
Worker does not discover latest manifests, reservations or trusted configurations.

Proposed request schema alc-r0-fixed-d-request-v1 has EXACT keys:
schema, control_id, reservation_id, declaration_root, source_export_root,
runtime_inventory_root, snapshot_inventory_root, fixture_source_root,
invocation_root, authority_generation_root, original_entry_root,
clock_domain_root, useful_deadline_monotonic_ns, snapshot_path.
All roots are64lowercasehex. Deadline is canonical decimal string/exact signed64
integer internally; snapshot_path is an absolute pinned regular-directory path,
not a download location. Control selects exact device/dtype from the CLOSED table;
device, dtype, seed, grid and tolerance are NOT independently selectable fields.
Reservation ID uses existing declaration grammar. Request <=16KiB; all unknown,
missing/extra fields and control drift reject. These are proposed implementation
caps, not changed scientific thresholds. The separately reviewed invocation
defines source/runtime/operator paths; they cannot be supplied by the request.

## Denial bootstrap and fixed scientific execution

Entrypoint bootstrap is Torch/Transformers/CUDA-free. Before importing the model
callable it validates bounded request syntax and exact request binding from the
coordinator, expected control, source/runtime/asset inventory and same-domain
unexpired original deadline against independently pinned reviewed configuration.
No self-asserted request establishes any of those trusted pins. Standalone worker
execution is not an approved experiment and cannot create launch authority.
Integrity checking is a cooperating-host boundary, not protection against a
fully compromised OS/runtime. Version strings alone are not runtime provenance.

All subprocess/hash work in scientific preflight must obey the original owned
deadline; source_checkout's unbounded per-blob subprocess loop cannot simply be
called in the unowned parent and described as bounded. Exact source-export and
runtime-inventory verification must have declared time/space bounds and terminal
coverage. No "clean HEAD" shortcut or installing/downloading on worker entry.

After verified admission only, worker explicitly establishes the settings that
checkpoint_parity_qualification._context requires: all3 offline flags1,
ordinary CPU default device, grad enabled, deterministic algorithms strict,
and for GPU CUDA0 BF16, CUBLAS:4096:8, TF32 off, cuDNN benchmark off/deterministic
on, math SDP only. Environment is fixed before importing Torch; no fallback,
warn-only deterministic setting, trust_remote_code or execution from model files.
CPU cannot initialize CUDA; GPU1/GPU2 must select the independently pinned same
physical GPU. Worker settings belong to this fresh process, not parent globals.

Call run_parity_qualification(snapshot, device=closed_device) exactly once.
It loads the pinned SmolLM2-135M revision
93efa2f097d58c2a74874c7e644dbc9b0cee75a2, verifies tokenizer/model inventory and
six fixed D fixtures, uses one frozen eager-reference base, executes all original
official-forward cases and all18 ordered grid/arm D cells, then rechecks assets,
context/base/rosters and complete receipts. No held-out or training dataset access.
Error/OOM/interruption is terminal, no smaller grid or replacement seed.

## Complete bounded worker receipt

One canonical JSON result on stdout; stderr carries bounded diagnostics only.
Proposed stream caps: stdout4MiB, stderr1MiB per declaration. Parent checks byte
caps before reading/allocating; no truncation is acceptable. These caps require
codec boundary tests for the full worst-size fixed schedule before acceptance.
No tensor, optimizer object, pickle, raw exception repr or arbitrary object dump.

Result schema alc-r0-fixed-d-result-v1 has EXACT common keys:
schema, request_root, control_id, reservation_id, declaration_root,
source_export_root, runtime_inventory_root, snapshot_inventory_root,
fixture_source_root, invocation_root, authority_generation_root,
original_entry_root, clock_domain_root, outcome, qualification, failure.
Roots/IDs must match pinned request and independently trusted declaration.
outcome is success/error/interrupted. On success qualification is the complete
bounded projection of ParityQualification and failure=null. Other outcomes have
qualification=null and a bounded closed failure record; no partial PASS.

Success projection retains source_device/dtype/base_digest, ALL tokenized fixture
bindings, all official cases and nonzero witnesses, and all matrix cell keys/
case losses/scores/digests/pending losses/AdamW comparison values and names.
Parent reconstructs the exact fixed schedules and validates every retained field,
count/order/range, finite scalar, base/fixture root and retained AdamW comparison
measurements. The parent cannot recompute tensor logits/allclose/argmax or named
gradient comparisons from digests and case losses/scores: these are performed
by the independently reviewed fixed callable in the cooperating-host boundary.
Do not change scientific dataclasses or silently add tensor evidence to disguise
that distinction. Existing typed _official/_matrix validators do not check every
wire numeric/digest field; the lightweight codec needs explicit retained-field
validation without importing Torch.
Integers encode as canonical decimal strings (bool is never integer); finite
float measurements retain round-trip numeric values under canonical JSON.
Tuple projections use bounded arrays. Define exact nested schemas from existing
receipt dataclasses before codec implementation; generic recursive asdict or
an "opaque payload" cannot substitute for these validations.
In particular preserve genuine ForwardCase booleans, TensorComparison nullable
relative_l2/cosine and exact_zero combinations, and signed -100 fixture labels.
Reconstruct original numeric-token fixture payload before checking fixture_sha256;
hashing a decimal-string wire projection changes the original fixture root.
Worst-schedule proof uses1296 official rows (24cases*3phases*18cells),18 witnesses,
18 matrix cells and18case rows/cell. Integer/float wire rules must be refined
for these nested fields before claiming that the codec contract is complete.

Failure projection has EXACT keys stage, category, completed_evidence_root;
stage is a closed qualification/bootstrap stage, category is validation/runtime/
oom/interrupted, completed_evidence_root is null or a bounded diagnostic digest.
Chained partial scientific receipts may be preserved separately only by a
reviewed bounded projection, never accepted as a full result. Missing/malformed
receipt or nonzero process exit cannot become success. Known failure process
exits are2(error)/130(interrupted); root Windows exit status remains unsigned32.
Success requires exit0 PLUS valid complete success receipt PLUS verified terminal
owned tree. Exit0 alone, a worker success flag or matching digest is insufficient.

GPU2 qualification remains a separately blocking scientific prerequisite. A
fieldwise evidence predicate is NOT yet defined by this proposal. It must preserve
original two-fresh-process stability semantics, distinguish exact digest/identity
comparison from numeric tolerance, retain null semantics, and exclude request-
specific roots/PID/timestamp. Existing reduced receipts cannot magically recover
tensor stability evidence. Two individually valid results alone are not that
proof. Specify and independently review the needed bounded evidence path before
claiming full qualification; do not invent tolerances, impose hash equality as
an unstated replacement threshold, or treat it as portability.

## Coordinator ordering and existing lease integration gap

Capture original entry UTC/monotonic/domain BEFORE any replay/hash. Verify trusted
producer facts and observations, assess original600GPUh/45day/25GiBresearch/
20GiBCfree independently with complete outstanding reservations/growth. Unknown
RAM/VRAM peak projections deny; point free-memory observations are not bounds.
Do not invent budgets or automatically kill unrelated applications.

Hold cooperating global reservation ownership and revalidate current generation,
revocation, expiry, numeric coverage, source/runtime/request pins and physical/
research/memory observations. Commit exact reserve intent/publication before
creation. No implicit empty store; reviewed complete genesis remains immutable.
Use ReservedOwnedLease only, never old run_owned_process immediate-resume path.
It creates a suspended private-job child and retains owned handles, FILETIME,
nonce, bounded output and reservation lock. Publish that exact child identity
durably before any resume. Revalidate trusted facts/deadline under the same
ownership immediately before creation AND before resume, then resume once.
Replays/audits and per-intent reads are also preflight work: lease publication
and public read/prepare/commit currently repeat complete retained-store audits.
The fixed composition must bound their total time/space under original entry
deadline/projections, deny on exhaustion and use already held ownership; no
unbounded recursive lock wait, lock gap or new snapshot/journal framework.

Existing lease does not itself verify authority/resources/source. A coordinator
must not claim an outer preflight check is immediate precreation verification:
lease entry performs replay/output setup between that check and child creation.
Implementation needs a reviewed fixed admission integration seam inside the
lease immediately before CreateProcess and inside resume before ResumeThread,
without arbitrary callback execution, lock gap, or new deadline. Proposed seam
is an internal concrete verifier object for this fixed coordinator, not a public
callable. Design/negative tests must establish ownership/lock ordering, refreshed
observations and failure cleanup before adopting it. Existing primitive API/tests
retain their trusted-low-level contract; no implicit scientific authority added.

After running publication releases the store lock, own/wait on the same retained
handles and capped outputs. Admission requires authority expiry to cover the
ENTIRE original charge envelope, including cleanup, using conservative UTC-clock
uncertainty bounds; unknown clock uncertainty denies. Active generation/revocation/
expiry observation failure must fail closed through owned termination, not keep
running. Proposed monitor bounds: poll at most250ms, obtain trusted observation
within250ms, existing owned wait sees terminal-denial signal within20ms; maximum
detection/termination-decision latency520ms plus the SAME10second cleanup tail.
These are mechanical proposed monitor bounds, not scientific thresholds or an
implemented guarantee. Blocking observation cannot be awaited indefinitely;
unobserved completion keeps charge/reservation. Concrete monitor implementation
and negative timing tests remain separate requirements, including generation
change/expiry/unknown-observation and no override from worker output. No deadline
or expiry check at resume substitutes for active enforcement.
At terminal reacquire ownership/revalidate pinned
publication and verify root-handle status+zero job members+bounded output audit.
Validate complete worker result independently; then persist terminal facts,
full allocation/cleanup charge and same-root materialized growth, then release.
Scientific failure may be resource-reconciled without becoming PASS. Unknown
charge/tree termination/creation retains pending/uncertain reservation. Overrun
is retained in full and denies admission, never clamped/refunded. Crash recovery
uses exact pinned predecessor/candidate intent, no reused-PID attachment/latest
discovery. Failed cleanup is not permission to launch another control.

## Implementation and execution gates

1. Independent design verdict must separate worker/codec readiness from unresolved
   full-launcher producer/admission/monitor readiness. Review may request changes;
   this proposal is not implementation permission by itself.
2. Define exact nested receipt wire contract first; only after separate scoped
   contract review, TDD bounded request/receipt codecs and denial-before-heavy-
   import bootstrap. No GPU, assets or host work for unit
   tests. Fake source/history roots are fixtures, never factual evidence.
3. Implement fixed worker settings/projection without public launch bypass;
   production bootstrap retains unconditional denial until the concrete reviewed
   operator pin source/handoff is installed and independently admitted. Request-
   adjacent JSON, environment "approved" roots or fixture default cannot supply
   that source. Test fixed invocation/context/settings and failure/result
   projection in non-launch scope only. Actual host still denied.
4. Resolve reviewed concrete producer, internal lease admission+revocation seams,
   numeric/clock coverage and realistic projected resource bounds. Synthetic
   owned harmless children test reserve/publication/authority races, expiry,
   deadline/preflight consumption, stream overflow, missing/partial/malformed
   result, kill, uncertainty and crash-forward without model/GPU invocation.
5. Resolve fieldwise fresh-process evidence contract, then exact final source/
   runtime/assets/invocation review and actual numeric/resource admission precede
   CPU1, GPU1 and GPU2 separately. No speculative launch to see
   if it fits; no claiming tests constitute real-host qualification.
6. Preserve E1/E2/E3, rights/evaluator/sealer and frozen scientific requirements
   before the original four200-update pilots, then full grid/held-out learning
   proof. No gate, phase ceiling, retry rule or learning threshold changed here.

Tests and exact source changes follow the required RED/GREEN/relevant-regression
cycle only after scoped design admission. Trajectory records every edit/verdict
and real invocation. Full unified goal remains active; this design is not a
scientific result, first-training execution or final ALC container investment.
