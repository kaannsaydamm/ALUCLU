# Checkpoint143: 16 microbatches and one fixed synthetic optimizer step

Baseline ea3c93dad0e8a0aae4c630fc2b4b6b649b957fca; previous turn PROGRESS.
Clean authoritative Desktop checkout verified; full unified objective and D's
fixed accumulation/optimizer contract reread. No Task2/ALC/R0 gate is reset or
reinterpreted. This implements prospective parity machinery, NOT task learning.

## Implemented contract

Exactly16 immutable, prevalidated alternating common-length64 candidate
fixtures, nonzero factors and no padding. Common prompt/distinct candidates;
the shorter candidate's actual sequence may be shorter than64 by the existing
maximum-candidate reserve convention. Verify ALL fixtures before first forward.
Shared observation core preserves the single and two-pending APIs. Accumulation
executes one forward and loss/16 backward per microbatch, without clearing grads
between examples. Checkpoint mode uses one owned session, consumes each graph
before the next forward, and closes before any optimizer mutation.

Capture actual detached averaged loss from the scaled backward inputs, all
per-forward loss/full logits/complete candidate scores and final accumulated
gradient roster. Every forward record explicitly contains the SAME final
aggregate gradients, not an individual gradient or a partial running sum. Use
ONE aggregate roster, never sum the sixteen copies. Preserve binding/metadata/
byte/input/frozen base invariants and complete finite nonzero factor gradients.

observe_accumulation returns BEFORE clipping. Caller must explicitly compare
both off/on accumulations BEFORE invoking either step_accumulation. This phase
order is a cooperating-caller obligation, not a hidden launch/authentication
claim. Step validates live base/factor digests and complete pre-clip gradients
against the exclusively owned record, disallows gradient storage aliases and
active checkpoint leases, clips global norm1 with nonfinite errors and
foreach=False, then invokes exactly one fresh fixed AdamW step:
LR3e-4,betas(.9,.999),eps1e-8,weight_decay0,foreach=False,fused=False.

Afterward validate base binding/eval/metadata/value invariants, factor structure
and complete populated fixed-schema AdamW step1 using existing _snapshot.
Result keeps cloned norm/clipped gradients and LIVE optimizer/factor bindings;
complete independent off/on factor/moment/step comparison uses the existing
compare_adamw_states, never serialized integer parameter IDs. Caller must keep
both arms/state quiescent and independently owned through final comparison.

Tests run only tiny synthetic factors and an unused tiny base. They check
16-times forward/backward ordering, normalization and agreement with separately
computed average gradients, off/on and complete step comparison, malformed
count/last fixture/alternation, mid-loop failure cleanup, changed pre-clip
gradients, stale observation reuse, active-lease step denial, injected frozen
base mutation and independent fixed Torch reference parameters/moments/step.
These execute an optimizer on tiny tensors, not a language-model training run.

## Executed evidence

Existing research Python3.12/Torch2.14; PYTHONPATH=src,
PYTHONDONTWRITEBYTECODE=1; Python-B -m pytest-q -p no:cacheprovider --tb=short.

| Attempt | Actual pytest exit | Tests/failures/errors/skipped | Time | XML SHA256 |
|---|---|---|---|---|
| red_v1 | 2 | 1/0/1/0 | 145.620s | e4c025a7d15528f56ca1956ed9baca51c774a34e9c73f626b0dc8ae12a33be49 |
| green_v2 | 0 | 56/0/0/0 | 48.299s | bd79e52f922e9d2698707da1423862d94b9ee0916442f21856cb2318b4e268af |
| regression_v3 | 0 | 890/0/0/0 | 99.976s | bb270958a4060df4d32be1d4dc74f749bb4a2de23d9540d5384ae32e35fa182c |

RED is missing step-module collection error, not numeric evidence. Startup
silence revalidated against exact live owned processes; no restart. The shared
observation extension was written while the step module remained absent, so
the RED's proven scope is that missing module, not missing observation methods.
GREENv2 preceded extra lease/mutation/reference tests and gradient-layout check;
preserve as intermediate, not final reviewed bytes. Final regression directly
observed actual exit0; root parsed890 cases including17new,0failure/error/skip,
XML hash and unchanged reviewed three source/test hashes. Ruff/diff passed.
Reproduce by prepending tests/test_alc_r0_accumulation_observation.py
to checkpoint142's exact27-target command;28 explicit component targets, keep
both asset/GPU case deselections and unique JUnit filenames. Not a full repo,
model, GPU or portability suite. Suite time is not latency/resource evidence.

## Exact review bytes and open work

- Observation source:a69c704884ca96336dd71fb214a930357984fd0b82b38993567d923379fec79a.
- Step source:4b374efb4217ab8676c5feb4b870266cbeedef99b1c31b931406a28a44c621e6.
- New tests:5836aad4ab0fcac637c6698e9be04df3a4e06cd6c1586c6232a77cb9d7422451.
- Independent GPT6.1Sol code APPROVE, architecture CLEAR for exact bytes.
  Both reviewed full source/tests/diff, D and optimizer API; no edits, imports,
  test/model/corpus execution or inference of pending terminal regression.
  Root subsequently verified final regression on unchanged bytes.
- Synthesis APPROVE ACCUMULATION/DISPOSABLE-STEP COMPONENTS ONLY.

Mutable captures/live optimizer states are not authenticated artifacts; caller
owns them exclusively. Failure clears originally captured factor gradients,
not arbitrary mutated state or partially updated parameters/moments: record
failure, discard/rebuild, never catch-and-continue or imply rollback.
No host assets/tokenizer/task corpus/held-out/GPU execution; no task-training,
launch authority or neural acquisition/persistence/portability claim. Actual
host callback/runner integration, full D matrix and official host controls,
E1/E2/E3 resource matrix and scientific R0 gates remain OPEN. Goal ACTIVE.
