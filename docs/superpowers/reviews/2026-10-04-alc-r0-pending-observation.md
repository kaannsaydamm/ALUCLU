# Checkpoint142: two pending forward observations

Baseline f557a479fe4b145f9d58dc28dff94797ce8b60fd; previous turn PROGRESS.
Clean authoritative Desktop checkout verified, full unified objective reread.
This extends the existing observation core toward section D of the checkpoint
implementation detail, without substituting component tests for actual-host
parity or neural capability acquisition.

## Implemented scope

Public observe_pending_pair accepts exactly two immutable, structurally valid
candidate fixtures with a common prompt, distinct complete candidate tokens,
maximum sequence length32 and no masked padding. Nonzero factor state required.
Token provenance remains the separately reviewed runner's responsibility.

Shared internal group core handles either the existing single API or the new
pair. BOTH forwards are executed before one backward of their summed losses.
Checkpoint mode uses a single session and session.backward on the sum, so
omitted owned graphs trigger the existing unconsumed-ticket enforcement.
Each loss and the sum must be finite, scalar and differentiable. Every output,
input, base/factor binding, named roster, tensor stamp and byte digest retains
the previous single observation invariant. Factor gradients must be finite,
complete and individually nonzero for the pair's nonzero state.

PendingObservation stores the actual summed-loss tensor detached/cloned to CPU,
not a reconstructed sum of converted captures. Its per-forward observations
store their individual losses/logits/candidate scores but each carries the SAME
summed-backward gradients. They are not incorrectly presented as individual
forward gradients. Gradient clones are independently owned per capture.
Pair comparison checks sum plus both complete ordered forward observations.
Single API and all its25 previous cases remain regression requirements.

Tiny tests verify off/on exact pair equality, forward-before-backward ordering,
both candidate orders, agreement with separately computed gradient sums,
invalid pair counts/second fixture, duplicate candidates, second-forward
failure cleanup, omitted graph rejection, nonfinite second loss, zero-state
rejection and summed-loss mismatch. The tiny base is unused in its forward;
these are component/graph controls, NOT a language-model capability result.

## Executed evidence

Existing research Python3.12, PYTHONPATH=src, PYTHONDONTWRITEBYTECODE=1,
Python-B -m pytest-q -p no:cacheprovider --tb=short, unique JUnit paths.

| Attempt | Actual pytest exit | Tests/failures/errors/skipped | Time | XML SHA256 |
|---|---|---|---|---|
| red_v1 | 2 | 1/0/1/0 | 16.430s | 50647a46b2a23cec15c574331493f00caa177f4e0321b70209eed6b9d0e3bd93 |
| green_v2 | 0 | 38/0/0/0 | 53.709s | 6929baa38de0adf83aa71142acc64febc56a5aab4ee3f8fd8cb74ddb0c7d1948 |
| regression_v3 | 0 | 873/0/0/0 | 206.398s | ab6147af13399e2e16b0564c37c8244bd1bb845b5281daf7af01e68e66701e31 |

RED is missing new public API collection error, not numeric parity failure.
GREENv2 preceded four added negative controls, import ordering correction and
direct summed-loss capture fix; preserve as intermediate, not final bytes.
Final expanded regression directly observed actual exit0. Root independently
parsed873 cases including17 new cases,0failure/error/skip, SHA256 and unchanged
reviewed source/new-test/old-test hashes. Ruff/diff passed. Initial silence was
revalidated against live process command lines, not assumed terminal or grounds
to restart. Reproduce by
prepending tests/test_alc_r0_pending_observation.py to checkpoint141's exact26
target command. Keep GPU capsule and real-tokenizer asset case deselections;
this is27 explicit component targets, NOT a full repo/model/GPU suite. New
module17 cases plus prior856; always use a new evidence path. Suite wall time
is not inference-latency/resource-fit evidence.

## Exact bytes, review and limits

Source SHA256:5cb1117c38bf02aa3bf07c634886f84884ae84f79748c8ff4fd2eaf4cd167b27.
New tests SHA256:5da032e1007b25d56a210f6dc9f2f5024f666d620db4f578be35ef2725e783f3.
Existing single test SHA256 unchanged:
63e1484e7a8981ac8868e25651ef2f7af5b9f40333905fd6ebe512fd455b5c45.
Independent GPT6.1Sol code APPROVE, architecture CLEAR for these exact bytes.
Both read full source/tests/diff and relevant D/API contracts; no edits,
imports/tests/model/corpus invocation or inferred live regression outcome.
Root subsequently verified final terminal regression on unchanged bytes.
Synthesis APPROVE TWO-PENDING-FORWARD OBSERVATION COMPONENT ONLY.

Caller must exclusively own mutable observation tensors through comparison
and receipt creation. Failures clear original factor grads, not rollback
arbitrary state: record failure and discard/rebuild before another arm.
Consume only ONE aggregate gradient roster from the pair; adding the two
per-forward copies together would double the true gradient. The forward records
are separate only for their loss/logits/candidate-score observations.
Matching arbitrary cooperating loss callbacks is not authentication or proof
of correct host semantics. No assets/tokenizer/task data/held-out/optimizer/GPU
run occurs here; actual-host callback qualification and launch review remain
OPEN. Full D nine-cell/two-arm CPU/GPU matrix, candidate ordering/repetition,
16-microbatch accumulation, AdamW and official-forward controls remain OPEN,
as do E resource matrix and neural learning acceptance. Full unified goal ACTIVE.
