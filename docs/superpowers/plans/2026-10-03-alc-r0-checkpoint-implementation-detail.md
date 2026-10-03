# Checkpoint fidelity and qualification implementation detail — prospective

Parent candidate: family-B v3 draft, SHA256
3c7e56cd33ffa6aaec0a5baa7cead146bc7a0ca2688c447c1ecf63424e0cdf38.
Status: design pending independent review. This detail cannot adopt that prompt,
authorize dataset training or admit actual-host execution by its existence.
It specifies implementation and later synthetic parity/qualification; model
runs additionally require exact-byte implementation and invocation review.

## A. Files and order

1. `src/aluclu/alc_r0/checkpoint_fidelity.py` and corresponding pure CPU tests:
   scale-sensitive tensor/gradient/AdamW state comparison. No model loading,
   optimizer update or checkpoint execution is part of this first component.
2. `checkpoint_execution.py`: explicit scoped lease, outstanding-graph tickets,
   bound replay guards and non-reentrant execution. Pure/fake-block tests first.
3. Minimal explicit opt-in integration in `host_wrapper.py` and `matched_lora.py`;
   existing default signature behavior, traversal and evaluation remain unchanged.
4. Dedicated synthetic parity and resource runners/tests with pinned offline host.
   No general product container, compiler, routing or dataset training commands.

Every component follows RED/GREEN/regression and independent exact-byte review.
Do not edit the old probe or replace its one-token negative limitations with
new results. Preserve candidate/source/environment receipts separately.

## B. Fixed fidelity arithmetic

`compare_tensor(reference, actual, *, exact=False)` must validate real dense
floating tensors, same nonempty shape/dtype/device, finite entries, no sparse/
complex/integer/bool tensors, no mutation and no missing/None values. Compare
detached CPU float64 views for metric arithmetic; this is verification overhead,
not a production inference feature. Reject bool/nonbool mode drift explicitly.

Return frozen finite metrics: reference/actual L2 norms, absolute-difference L2,
relative L2 and cosine; exact-zero status is explicit and undefined ratios are
null, never NaN/Infinity or an invented1. Nonfinite input fails before metrics.
For a nonzero reference require nonzero actual, elementwise rtol1e-3/atol1e-3,
relative L2<=1e-5 and cosine>=1-1e-6. Calculate norms by scaling each vector by
its max-absolute value before float64 norm/dot operations to avoid overflow/
underflow. A nonfinite resulting norm fails, not a silently clamped metric.
If reference is exactly zero, actual must be present and exactly zero; metrics
are norms0/difference0, relative/cosine null. For exact=True additionally require
original tensors elementwise bit-preserving equality, including signed zeros
using contiguous byte views, before the other applicable checks.

`compare_named_tensors` requires identical nonempty canonical string key sets,
then checks EVERY tensor in UTF-8 key order; no intersection-only comparison.
Use this for all factor parameters and individual/accumulated gradients.
The caller must include zero gradients, not omit them; None is a failure.

AdamW comparison maps state to canonical factor names, not Python parameter
addresses: exact same name/shape/dtype maps, optimizer hyperparameters and
state keys. Require exact step values and exact state key/cardinality identity;
compare exp_avg/exp_avg_sq and resulting factors with the above criteria, exact
on CPU FP32. Required step is1 in the parity fixture and2 in qualification.
No unexpected state, missing parameter, base parameter membership or silently
empty state after a claimed step is allowed. The runner, not the tensor helper,
owns construction/binding of the optimizer metadata and step count.

Pure tests include exact identity, zero/negative-zero, missing/wrong names,
wrong shapes/dtypes/devices, nonfinite/sparse/complex/empty/bool inputs,
tiny/subnormal finite values and nonfinite norm; a small-gradient sign reversal
such as reference[1e-6,-2e-6]/actual[-1e-6,2e-6] must pass loose allclose but be
rejected by this comparator. A scale-error perturbation and accumulated-gradient
mutation must also fail. Fixtures do not touch model/assets or run an optimizer.

## C. Explicit execution scope and replay guard

Proposed API: `with wrapper.checkpoint_session() as session:` and explicit
`wrapper(..., checkpoint_session=session, use_cache=False)`;
`session.backward(loss)` owns completion accounting. No process-global switch,
implicit HF flag, global monkeypatch or default-on behavior. Only the owner
wrapper/thread may use a session. No nesting; at most32 outstanding forward
graphs per session. The wrapper must be training, factors trainable FP32, base
eval/frozen, cache absent, input IDs batch1 and supported host dtype. Refuse
supplied past_key_values even with use_cache=False. Keep the evaluation cache
path unchanged when no session is requested.

Each forward takes a ticket and binds layer/index/arm/factor identities and
versions, modes, dtypes/devices and input/mask/position metadata. Private masks/
positions are cloned once per forward; no exposed writable shared-input alias
is used by replay. Callable entry validates the live session and all bound
state BEFORE computing anything, both initial forward and recomputation. Bind
the actual factor operation inside the block callable; never read mutable
current mounts from replay. Non-reentrant checkpoint retains captured-factor
gradients when frozen embeddings produce inputs without requires_grad.

Logits hooks mark ticket traversal and reject backward outside the owner
session.backward or after scope closure. session.backward accepts a finite
scalar differentiable loss and retain_graph=False only; multiple forward losses
may be summed. Mark tickets consumed only after backward returns successfully,
not when an output hook first fires. A ticket unvisited by backward remains
outstanding; normal exit with any outstanding ticket fails. No duplicate/reused
ticket can be consumed. Normal complete exit invalidates all replay closures
and releases the lease. Any exception invalidates/releases all tickets then
propagates; retained failed graphs must never be reused. Clear partial factor
gradients before a new independent attempt, recording the failed attempt.

Mount/detach/replacement, train/eval, device/dtype change and supported in-place
factor/base mutation are forbidden while a lease is active. Check tensor versions
and frozen-base flags at replay entry; fingerprints at session boundaries also
detect unversioned value changes. This is a cooperating-process contract, not
security against a compromised host or malicious restoring writes through.data.
No optimizer step occurs inside the session. Accumulation16 means16 complete
forward/backward microbatches with unchanged factor values, followed by clipping/
step after the last lease closes. Multiple-forward combined-loss tests exercise
the outstanding-ticket case independently of that main accumulation schedule.

Pure fake-block tests must prove correct first/last layer binding, factor gradients
with input requires_grad=False, correct port placement, all lifecycle denials,
retained-graph/foreign-session rejection, two pending forwards, omitted loss,
exception cleanup, mask/position isolation and guard-entry-before-early-stop.
Fixed test mutants: late-bound final layer/index, reading a replacement mount,
factor operation outside checkpoint, no captured-factor gradient, guard only at
tail, missing-ticket accounting, and bypassed small-gradient comparison.

## D. Actual-host parity fixtures, only after separate launch gate

Pinned host/revision/snapshot and locked Python3.12/Torch2.14/Transformers5.17
remain unchanged, no acquisition/network/trust_remote_code. Use all nine grid
configurations in v1 order, each capsule then q-only LoRA; CPU FP32 then GPU
BF16 in separate invocations. Fixed seed20260916. In each invocation load one
base, run off and on arms sequentially from identical fresh factor states;
never keep two base copies. Parameter keys/counts must match before comparison.

Synthetic code IDs are `(arange(n)+1)%49151+1`; prefix/suffix/candidates come
from the verified tokenizer. Common sequence lengths32 and64, one safe and one
vulnerable candidate per state/length. Code length is common length minus
actual framing/max-candidate reserve; no artificial embedding/input gradients.
Two states: seeded original A with B0, and same A with each B flattened entry
`((i%17)-8)*1e-4` in FP32. Nonzero-state every factor gradient must have nonzero
norm; zero-B state A gradient exactly0 and each B gradient nonzero. A violation
is a recorded failure, not a change of fixture or tolerance.

At64 add right EOS padding7, attention mask0 on padding and labels-100. Masked
full next-token loss supervises every token of the intended candidate. Preserve
the standard shift; no logits_to_keep=1 shortcut. Compare loss/logits, candidate
scores/order, each factor gradient and base/no-gradient invariants. CPU exact;
GPU elementwise plus scale-sensitive criteria in B. Repeat the nonzero fixture
twice from identical state. Test two pending length32 forwards with summed
loss and compare off-path summed loss/gradients.

Accumulation fixture: sixteen length64 examples alternating safe/vulnerable,
nonzero state, loss/16 per microbatch; compare accumulated gradients before
clipping. Apply one identical AdamW step with LR3e-4, betas(.9,.999), eps1e-8,
weight_decay0, foreach=False, fused=False and clip global norm1.0. Compare full
state/factors afterwards. This disposable synthetic step is implementation
parity, not the R0.4 optimizer schedule or a real-task learned capsule.

Existing official-forward no-mount/zero/detach/cache tests remain regression
requirements, not inferred from new comparisons. Missing snapshot/CUDA is an
unavailable invocation, not an accepted skip. Each CPU/GPU parity invocation
has45min wrapper-inclusive ceiling; no undisclosed retries or dropped cells.

## E. Separate synthetic resource matrix

After complete actual-host parity, declare exact-byte launcher and run:

- E1: nine configurations x capsule/q-only LoRA, fixed order as in D,
  common4096, eighteen fresh GPU BF16 processes. Each performs exactly TWO
  disposable synthetic optimizer updates; each update has16 alternating-label
  complete forward/backward microbatches, loss/16, clip1.0 and fixed AdamW above.
  Start at seeded A/B0. Update2 measures populated optimizer state and nonzero
  factors. No scheduler or adaptive learning-rate search: this is stress fit,
  not the scientific pilot. Thirty-minute ceiling per process.
- E2: frozen-base actual profile encoding and separate synthetic RAG maximum
  control inference, two fresh GPU processes. Profile uses exactly frozen v1
  text plus separately encoded separator, no filler; RAG uses synthetic ordered
  <=64-token framed example ID blocks with true candidates, with the final
  admitted block sized so total control including separator is512. Common query
  remains4096. Both score both complete candidates, use_cache=False and no
  factors/gradients; report actual sequence lengths (profile need not be4608).
  Each has ten-minute ceiling. Pure token fixtures prove the RAG construction
  and framing/answer reserves before any host run.
- E3: all-30-layer q+v rank8 reference is460800 parameters and is NOT inferred
  from E1. Its adapter path is not presently implemented here. Before resource
  qualification can be called whole-candidate complete, that path must receive
  separate TDD/exact-byte review and one declared common4096 two-update/16-accum
  stress process under the same30min ceiling. Keep E3 OPEN until then; E1/E2
  success alone is only partial candidate qualification, never full PASS.

Only synthetic IDs and tokenizer candidates; no PrimeVul/Banking task files,
held-out paths or meaningful learned artifact is consumed/produced. No new
matrix variant after outcomes. On failed/OOM cell preserve the exact failure,
attempt accounting and unrun matrix; do not continue/select a smaller budget
under the label of this candidate's PASS. Any repair/retry needs prior reviewed
invocation and preserved attempts, within original limits.

Each child starts from a clean frozen commit and verifies model inventory,
environment/source hashes, offline settings, free C:>=20GiB and no live duplicate
attempt. Reserve/journal the attempt in the existing600-GPU-hour/25GiB research
resource program before launch, including previously consumed attempts; missing
budget accounting prevents launch, not permission to assume full remaining
budget. No paid compute, installations, user process termination or OOM fallback.

Wall timing is wrapper-inclusive load/preflight/compute/terminal verification;
GPU phase timing uses synchronized intervals. Peak CUDA allocated/reserved is
reset AFTER host load but includes factors/optimizer/compute and is reported as
total allocated peak plus baseline, not an inference-tax claim. Record sampled
exact-worker RSS/private memory separately, disk before/after, gradient/loss
finiteness, full candidate supervision, successful update/microbatch counts,
factor/state/base digests, raw logs, actual exit, interruption/timeout and every
matrix status. Rehash snapshot/clean source/base before canonical receipt.
Timeout kills only the exact validated owned child/process tree, records a
terminal INVALID attempt and never becomes a numerical/capability failure.

## F. Gate order and honest claim boundary

Review this detail -> implement first pure component RED/GREEN/regression ->
independent byte review -> implement scope/wrapper and pure/fake tests ->
review exact code -> commit/freeze -> review actual-host invocation -> parityD ->
review terminal parity -> freeze/resource launch review -> E1/E2/E3 as available.
Resource fit alone permits continued amendment review, not adoption or task
training. Rights, sealer, evaluator, machine R0.0 validation and scientific
freeze remain OPEN before the original four-job200-update pilot. All P1-P14,
base-frozen/retrieval-off/fresh-process capability and later roadmap gates stand.
