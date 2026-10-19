# E3 q/v reference stress: prospective implementation contract

Status: PROSPECTIVE_ENGINEERING_CONTRACT, not a launcher or resource PASS.
Parent checkpoint193: 84581dc4defde94104c86dd6915c4ef0610ed9b9.
Original scientific plan and section E of checkpoint implementation detail remain
authoritative. This contract fills implementation gaps, not scientific adoption.

## Verified gap and dependency order

Existing D parity_input accepts only32/64 common lengths. observe_accumulation
requires16 common64 examples and nonzero state. step_accumulation creates a fresh
optimizer and validates step1 only. run_accumulation_pair compares two arms before
stepping either. None implements E3's common4096, initial seeded A/B0, retained
optimizer and TWO16-microbatch updates. Do not relax those D contracts or claim
checkpoint189's short fake accumulation qualifies E3.

The existing reference factory provides30 q/v rank8 modules,460800 FP32 master
parameters over one frozen CPUFP32/CUDABF16 base. ReferenceResumeRecord is a
separate CPUFP32 step1 engineering codec; it is NOT an E3 CUDA checkpoint path.
Do not invoke it through a GPU-to-CPU fallback or include resume in E3's scope.

Implement pure token-only schedule -> independently review -> implement trusted
single-wrapper stress execution -> pure/fake tests and regressions -> independent
exact-byte review -> actual-host q/v parity qualification -> review/freeze exact
E3 invocation plus resources -> one owned fresh GPU E3 process. No asset/model/
tokenizer/GPU invocation is authorized by this document. Existing actual-host D
matrix and official-forward regressions remain mandatory; q/v host parity must
also be evidenced rather than inferred from capsule/q-only qualification.

## Separate immutable token-only E3 schedule

Use a distinct StressInput type and constructor, not forged D ParityInput or
expansion of its allowed lengths. Accept immutable independently verified prefix,
suffix and complete safe/vulnerable candidate tuples. Fix pinned vocabulary49152
and EOS0, matching the existing tokenizer metadata boundary; do not accept an
arbitrary EOS that collides with synthetic code IDs.
Exact integer nonempty bounded token tuples, distinct candidates, no EOS and
no boolean IDs; each supplied framing/candidate tuple<=64 tokens. Host tokenizer
provenance is an external binding, never inferred from plausible token IDs.

Common4096 includes framing, synthetic code and longest COMPLETE candidate.
Reserve=max(candidate lengths), code_length=4096-prefix-suffix-reserve>=1.
Use deterministic synthetic code-ID construction from the existing parity rule;
no task source/corpus/held-out file or tokenizer call. Shared prompt is identical
for both labels. Shorter candidate's actual sequence may be below4096; do not pad
or truncate it to claim4096 effective tokens. Emit all-ones attention mask,
unshifted labels -100 on prompt and every complete candidate token supervised,
contiguous position IDs. Host loss owns the next-token shift.

Exactly16 immutable inputs alternate safe/vulnerable starting safe. TWO updates
reuse this same frozen schedule; no random sampling, changed framing or adaptive
input search after outcomes. Record all actual candidate and sequence lengths,
prompt length, schedule digest, update count and microbatch count. Unexpected
counts/types/lengths/labels/masks/positions fail before execution/allocation.

## Prospective trusted stress executor, not a launch boundary

Caller supplies already authenticated host/wrapper, schedule and execution
context; single checkpoint-enabled reference wrapper, no second base or off arm.
Require initial fresh seeded A/B0, fixed complete120-factor roster, gradientsNone,
frozen eval base, FP32 masters and original fixed AdamW configuration. Create
optimizer once and retain it across both updates. CPU fake execution tests the
logic only; actual E3 accepts only separately admitted cuda:0 BF16 base context.

Each update clears gradients, runs exactly16 sequential complete candidate
forward/backward microbatches with loss/16 through owned checkpoint leases, exits
leases before clipping/step, clips norm1.0 with nonfinite rejection, and steps
fixed AdamW once. Validate complete populated factor/moment state at expected
step1 then step2, without an optimizer reset or altered schedule. Base parameter/
buffer bytes remain hash-identical, no base gradients, bindings/modes unchanged.
Require finite loss/logits/gradients/moments and nonnegative second moments.
Every factor must have a present gradient; zero-B step1 can legitimately yield
zero A gradients. Do NOT substitute D's nonzero-B/per-factor-nonzero parity rule.
Finite or aggregate factor change is not capability improvement. No state rollback
claim after failure: preserve terminal failure/counts, discard execution state.

## Admission, measurement and acceptance boundaries

One fresh owned GPU process, exactly2updates/32microbatches, common4096 and original
30-minute wrapper-inclusive terminal-verification ceiling. Establish the owned
child deadline early enough to reserve preflight/verification/cleanup within that
original ceiling; do not grant a fresh30minutes after host load. Private-job
cleanup can consume additional bounded emergency time after timeout, but the
attempt is INVALID, the full tail stays charged/reconciled, and it cannot PASS
or gain a budget extension. No retry/resume/OOM fallback without reviewed attempt.
All failed/interrupted attempts count in original resource history. Unknown
historical600GPUhour charge or first-job45day clock continues to deny launch;
the pending accounting clarification remains NOT adopted.

Preserve25GiB research ceiling,20GiB C:free floor, durable reservation/exclusion,
exact source/runtime/assets/invocation review, sampled owned-worker RSS/private
bytes and total CUDA allocated/reserved peaks plus loaded-base baseline. Resource
measurement belongs to an outer authenticated owned launcher, not a token helper.
Record synchronized phase timing, wrapper-inclusive wall, actual exit/timeout,
complete source/base/schedule digests and partial counts on any terminal failure.

Acceptance evidence: pure malformed/bounds/reserve/complete-label schedule tests;
fake executor ordering, optimizer persistence, lease exclusion, invariants and
failure-count tests; exact-byte independent code/architecture review; actual-host
q/v parity and one admitted complete E3 receipt. Pure/fake tests cannot close E3.
No resource PASS from parameter arithmetic or successful short CPU fixture.
Rights/sealer/evaluator/freeze and retrieval-off held-out capability remain OPEN;
E3 fit is not learning acceptance, final .alc or whole-program completion.
