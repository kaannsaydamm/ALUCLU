# Bounded q/v optimizer resume: prospective engineering contract

Status: PROSPECTIVE_ENGINEERING_CONTRACT; exact-byte review verdicts are recorded
in TRAJECTORY.md. No implementation, resume PASS or scientific adoption implied.
Parent source checkpoint: 67a4ae2c7162286dc70776bc445d3e6ab95b65d8.

## Purpose and boundaries

Factor-only remount does not restore AdamW training history. Add a separate
research checkpoint for the existing all30 rank8 q/v reference, then prove
step1 export/restoration followed by step2 against uninterrupted execution.
This is NOT the final .alc container, a portable Neural ABI, host attestation,
training permission or proof of durable learned capability. It is not a new
blocking scientific acceptance gate; it closes an engineering resume gap.

Initial implementation is explicitly CPU FP32, cooperating/quiescent callers,
fixed existing Torch2.14 AdamW schema, export at synthetic step1 only. Restoring
then checking step2 stays within the existing comparator's step1/2 contract.
Do not expand that comparator to arbitrary schedules or claim CUDA/BF16 support.
No GPU-to-CPU fallback, asset loader, optimizer step, disk access, pickle,
torch.save/load, arbitrary callbacks or executable payload in this component.
Original capsule256KiB, factor-only q/v2MiB, D/E grids and scientific/resource
thresholds remain unchanged. A separate research record bound is not a capsule
size allowance. Real model/data/GPU execution retains its original authority.

## Proposed interfaces and ownership

New module `reference_qv_resume.py`; pure tests in
`test_alc_r0_reference_qv_resume.py`, integration separately.

- Frozen `ReferenceResumeRecord` holds four exact byte strings: factor manifest,
  factor payload, optimizer manifest, optimizer payload. No paths/foreign object.
- `serialize_reference_resume(wrapper, optimizer)` validates a quiescent exact
  q/v wrapper, CPU FP32 frozen eval base, trainable reference, gradients None,
  complete existing optimizer group/state with every step exactly1, and storage
  separation (including base buffers). Require a hook-free source optimizer:
  reject registered local step/state-dict/load-state-dict pre/post hooks and
  registered global optimizer step hooks. Cooperating callers must not monkeypatch
  optimizer behavior; arbitrary runtime mutation is outside this codec's threat
  model. Never serialize or replay hooks. It clones and exports; never zeroes live
  gradients or modifies caller objects. Capture/recheck base/factor/binding/state
  evidence across export; callers exclusively own mutable state throughout.
- `restore_reference_optimizer(wrapper, record)` requires a new quiescent wrapper
  with already-mounted factor bytes exactly matching the record. It does NOT
  replace the caller's mount or mutate an existing optimizer. Validate everything
  first, create a fresh fixed optimizer, attach separately owned cloned moments
  by canonical factor names, validate complete state again, then return it.
  Any failure returns no optimizer; caller wrapper/base/factors remain unchanged.
  Fresh optimizer may be discarded on failure; no catch-and-continue/rollback
  claim. Live factor gradients must be None at restore and export boundaries.

Mounted factor preparation is explicit: independently parse the existing bounded
factor record, construct caller-owned wrapper, mount restored factors, then
restore moments. Factor parser success is not training authority. Never use
serialized integer parameter IDs or inferred parameter iteration order.

## Fixed format and pre-allocation checks

Factor manifest/payload use the existing unchanged q/v artifact format. Optimizer
manifest uses canonical bounded JSON, exact keys and a distinct schema/version.
It binds SHA256 and exact lengths of BOTH factor manifest/payload, frozen base
parameter-and-buffer digest, optimizer payload digest/length, actual Torch runtime
version, fixed CPU/FP32 contract, step1 and `training_authority=false`. Require
recorded runtime version equal to running version and the existing Torch2.14
schema; no invented host certificate from model labels or self-reported digests.
The manifest carries the complete fixed hyperparameter/flag contract, not params.
Compare it to the existing `_group` contract; reject unknown/missing fields.
Digest binding establishes consistency, not authenticity/signature/authorization.

Optimizer SafeTensors contains exactly360 entries: for each of120 canonical
factor names, `step/<name>` scalar FP32 and `exp_avg/<name>`,
`exp_avg_sq/<name>` FP32 with the corresponding fixed factor shape. Steps are
exactly1, finite moments required and second moments nonnegative. No metadata,
gradient, scheduler, RNG, hook, base tensor or foreign entry is permitted.
These deliberately exclude stochastic execution resume; later claims need those
states plus input/cursor identity and separate evidence, not this codec alone.

Bounds: optimizer manifest<=16KiB, optimizer header<=128KiB, optimizer payload
<=4MiB, aggregate four byte strings<=8MiB, and existing factor bound<=2MiB.
Exact raw optimizer data length is `2*460800*4 + 120*4 = 3686880` bytes.
The8MiB ceiling limits serialized input bytes, NOT peak RAM. Parsing/loading,
cloning/reserialization/snapshots and fresh optimizer may coexist; resource
admission must account for these bounded copies separately, without inferring
an8MiB execution footprint or changing the original research budget.
Reject aggregate/type/length/digest/manifest problems BEFORE tensor loading.
Preflight the entire optimizer header BEFORE any optimizer tensor loader or
optimizer construction: exact names/cardinality/entry keys, F32, exact dimensions
(including rank0 steps), exact integer offsets, shape products/lengths,
contiguous nonoverlapping coverage, no gaps/trailing bytes, bounded JSON/depth
and duplicate-key/constant rejection. No attacker-provided allocation shape.
Then bounded CPU SafeTensors load, finite/value validation and canonical
reserialization equality. Canonicality-after-bounded-load is not pre-load proof.
Only then map into fresh optimizer state by complete exact canonical names.
Capture live stamps/digests before parsing, recheck before publication; reject
factor/base/mount/mode/lease drift. No claim safe against arbitrary concurrent
mutation; caller ownership is required throughout, not just at entry.

## Acceptance and implementation sequence

1. Independent exact-byte review of this contract; address blockers before code.
2. RED missing-module/API tests, then smallest pure codec implementation.
3. Roundtrip byte equality and independent storage for all120 factors/moments,
   complete populated step1 comparison. Manual moments are codec fixtures only.
4. Negative tests: malformed/truncated/oversized bytes/header, duplicate/deep JSON,
   names/shape/dtype/offset/overlap/gap/trailing/resource bomb, unknown manifest,
   wrong runtime/group/step, nonfinite/negative second moment, payload/factor/base
   digest mismatch, missing/foreign state, alias with base/buffers/factors/moments,
   gradients present, active lease, mount/binding drift, source mutation and
   registered local/global optimizer hooks (no hook callback executed by codec).
   Instrument loader/constructor to prove invalid preflight never reaches them;
   preserve caller bytes/state on every failed restore. Record every RED/failure.
5. Disposable full30-block CPU integration: real fixture step1, clear gradients,
   export, restore factors into a separate wrapper and restore fresh optimizer;
   complete exact step1 comparison. Same second input/loss/gradient/clip/update
   for uninterrupted/restored arms; compare complete step2 state, output, factors,
   frozen base digest. No scheduler/RNG/accumulation replay is implied.
6. Separate owned subprocess fixture proves process-boundary resume only after
   same-process correctness. Fresh process rebuilds deterministic fake base,
   verifies exact base digest/runtime/records; no real assets/task data or GPU.
   Fixture architecture/configuration/source must be rebuilt and verified outside
   the codec; equal base tensor bytes alone do not authenticate computation.
7. Focused/integration/regression runs with observed exit/count/time/XML hashes,
   two independent exact-byte code/architecture reviews, trajectory, commit/push.

Do not implement final .alc infrastructure here. Actual-host provenance,
original rights/sealer/evaluator/freeze, historical resource admission, E3 and
retrieval-off held-out capability acceptance remain independently OPEN.
