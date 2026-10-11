# Family-B prompt and resource amendment v3 — DRAFT, NON-AUTHORIZING

This is a prospective candidate for independent scientific/design review, not
an adopted amendment to v1, a training permit, a resource PASS or a prompt
freeze. It follows checkpoint119's BLOCK on unchanged512. No held-out results
or model task scores have been observed or used to propose it. Existing failed
and negative evidence remains immutable. P1-P14 and the two-family capability
claim are unchanged; the Banking77 task is not replaced by an easier task.

## 1. Proposed single candidate and explicit contract changes

Propose family-B common candidate-sequence budget4096, with exactly the existing
pair-blind single-function head/tail token-ID construction. Retain512 additional
tokens for the existing textual-profile/BM25 controls. Family-B total ceiling
becomes4608; Banking77 remains common512/control512/total1024. Do not pad the
neural arms with unused control tokens. All arms receive exactly the same
normalized query representation at the family-specific common budget.

This explicitly proposes changes to v1 section5.1's uniform512+512 within1024
and section6's target-task maximum1024; it does not silently reinterpret them.
Full candidate supervision/scoring, optimizer, seeds, ports/ranks, comparison
arms, graph/statistical rules, retention tasks and P1-P14 remain unchanged.
No runtime heuristic chooses a shorter prompt after an OOM, a model score or
inspection of the evaluation example's label. No4096/8192 budget search is added
to the development optimization grid.

The proposal must be rejected or revised prospectively if the independent
review cannot justify its residual information loss or if resource qualification
fails. Revisions get a new named version before new execution. Failure is not
permission to fall back to512, shrink ranks, drop examples, remove controls,
silently switch attention or lower a capability threshold.

## 2. Choice rationale and limits, not a sufficiency proof

| Alternative | Information/resource tradeoff | Disposition in this proposal |
| --- | --- | --- |
| Unchanged512 eager | Existing independent scientific BLOCK; known information loss | Preserve negative evidence; not adopted |
| Common2048 eager | Existing one-backward synthetic fit only; still substantial observed truncation | Not selected; not called infeasible or scientifically falsified |
| Common4096 eager, explicit activation recomputation | Longer unchanged pair-blind input; retains separate512 control allocation inside host8192 ceiling | Single proposed candidate; fit and fidelity unproven |
| Common8192 plus512 controls | Exceeds pinned8192 context limit before any resource argument | Not a valid equalized-arm allocation |
| Shortening8192 query to7680 for controls | Different common budget, not the measured8192 query representation | Not silently substituted or selected |
| Flash/SDPA attention replacement | May save memory but changes the locked eager reference execution | Not introduced here |
| Label/pair-aware slicing or patch input | Would expose privileged comparison information unavailable to classifier | Prohibited |
| Multi-window/AST/new task formulation | Changes inference/aggregation/input semantics and needs a separate scientific protocol | Not smuggled into this amendment |

4096 is proposed as a bounded intermediate candidate, not proven Pareto-optimal
or chosen by task accuracy. The already declared information-availability grid
and complete audit inform an explicit pre-held-out risk decision, not an
outcome-tuned optimization objective. Independent reviewers must approve that
decision, not merely validate this document's arithmetic.

At4096 the retained-observation audit reports141 train/7 validation minimum
deterministic prompt-only errors, not a macro-F1 ceiling. Opposite-label classes
include149/5574 vulnerable train and7/562 vulnerable validation observations,
with146/171717 and7/22210 safe counterparts. Classifier errors are not assigned
to a particular class by these participation counts. Truncation is565/5574
vulnerable train and26/562 vulnerable validation, versus1673/171717 and
137/22210 safe. Minority-class information risk remains and is not excused by
a small overall fraction. Single-function inputs cannot represent every
multi-function vulnerability. All retained observations remain in evaluation;
no contradictory, truncated, hard or unresolved examples are removed.

Separately, at4083 code tokens, all optimal paths hide all edits for48/4118
train and2/464 validation resolved-positive pairs, with mean minimum exposure
0.983010352596865/0.9927056987389569. The244 unresolved pairs remain explicit.
These conditional numbers neither locate vulnerability evidence nor establish
whole-population sufficiency. Useful learning can still be possible with
imperfect input; whether it occurs must be decided by the unchanged real
capability gates, not by this diagnostic. Residual-risk acceptance for this
candidate remains a named independent scientific decision, not a new relaxed
numerical input gate or a PASS declaration by the author.

Receipts: retained information SHA256
9f2a0bec51c102be9c8588e9494f4b96013e56b9996aeb6b8eda45c4e9f0576c;
full edit exposure SHA256
8bc7eb3e96d96a1292181557dd6e44d46de6d00a857c188dafccc48c67b50a46.
Their populations differ and must never be pooled.

## 3. Exact input, loss and control semantics

Use the unchanged `DefectPromptTemplate` with proposed `max_tokens=4096`;
normalization, prefix `Labels: safe vulnerable\nInput: `, suffix `\nVerdict:`,
leading-space candidate encoding and ordered labels `[safe, vulnerable]` are
unchanged. Pin the actual tokenizer's framing/candidate IDs and derived4083
code budget in a versioned manifest, verifying that derivation rather than
hardcoding an assumed framing length. For longer code keep
`ceil(code_budget/2)` head IDs and `floor(code_budget/2)` tail IDs; no new marker
or source reconstruction. Prompt/answer/candidate are never truncated. Train
only on all intended candidate label tokens, with prompt/padding labels-100;
retain existing per-example loss and effective batch16 conventions.

For base/capsule/q-LoRA/shuffled/zero/wrong-family/detached arms use this exact
common query without profile/retrieval/filler. The control insertion was not
previously bound by an implemented family-B control builder. Propose an explicit
new binding: `control_ids + prefix_ids + code_ids + suffix_ids + candidate_ids`.
Encode the final `\n\n` separator separately without special tokens. For a
nonempty profile encode the unchanged v1 rendered profile without special tokens
and concatenate its IDs with separator IDs. For nonempty RAG concatenate each
ranked example's v1 framing/code/answer IDs after its existing at-most64-token
head/tail construction, then add separator IDs. Never decode/re-encode a
truncated example or retokenize across example boundaries. Select the longest
ranked prefix whose resulting control IDs fit512, permanently stopping at the
first whole nonfit, including the reserved separator in every fit check. Empty
controls contribute no separator and no IDs. Separators/framing
count within512, not outside4608. No retokenization across the control/common
boundary is allowed: deleting the leading control IDs must reproduce the exact
common query/candidate IDs for every arm. This placement/counting is proposed
explicitly, not called an already proven unchanged implementation. BM25
tokenization, ranking, k8 and64-token example limit remain unchanged; qualification
fixtures must verify the complete token construction and whole-prefix stop.
No evaluation query uses author-pair IDs, patch code,
vulnerability labels, test metadata or train examples in the neural claim arm.

Scoring remains one full uncached forward per complete label, mean candidate
next-token log probability and canonical UTF-8 tie ordering. No final-token-only
loss, candidate shortening, label-conditioned code cropping or change to the
observation point estimand/component bootstrap is permitted. Training label
availability is not permission to choose that example's input representation.

## 4. Proposed resource optimization: explicit non-reentrant recomputation

Keep the locked Torch2.14.0/Transformers5.17.0, eager attention, BF16 frozen
host/activations, FP32 factor/gradient/optimizer state, deterministic algorithms,
TF32 off, microbatch1, accumulation16, no cache and zero dropout. Propose
standard PyTorch block-level activation checkpointing with
`use_reentrant=False`, `preserve_rng_state=True`, no compile or custom kernels.
This trades recomputation for saved activations; it does not guarantee fit.

Our wrappers explicitly traverse decoder blocks: toggling the underlying HF
model's checkpoint flag alone is not an implementation. The wrapper must
checkpoint an explicitly bound callable for each block, including the selected
arm's factor operation. Bind the layer, index, factor identities and masks/
positions at forward time; no late-bound loop variables. A frozen-parameter
first block may receive inputs without gradients: non-reentrant semantics must
still propagate gradients to captured trainable factors at selected ports.
No artificial trainable embeddings or base `requires_grad` are introduced.

No mount/detach/replacement, parameter update, cache mutation or device move is
allowed between forward and backward recomputation. Add a fail-closed mount/
execution-state guard and explicit tests; capturing mutable `self.capsule` or
`self.lora` is insufficient. The detail must define a guarded lifetime spanning
every outstanding forward/backward graph, multiple accumulation forwards,
exception cleanup and attempted detach. Bind/check layer/base mode, factor
identities/tensor versions, device/dtype and private immutable mask/position
inputs. Reject supplied mutable caches even with `use_cache=False`. Verify guards
at callable entry before the first recomputed operation: non-reentrant early-stop
means a trailing check alone can be skipped. Default wrapper/evaluation behavior
remains the existing eager traversal. Checkpointing is
explicitly requested only in the prospective training/resource path; no hidden
global patch of decoder forward or monkeypatch of HF model methods.

Primary references, inspected2026-10-03:
[PyTorch2.14 checkpoint](https://docs.pytorch.org/docs/2.14/checkpoint.html) and
[Transformers checkpointing explanation](https://huggingface.co/docs/transformers/v5.10.0/en/grad_checkpointing).
The latter is conceptual documentation, not the pinned5.17 wrapper API. Exact
installed code and independent parity tests decide compatibility. Documentation
describes recomputation and RNG handling, not our local memory/gradient PASS.

## 5. Required fidelity gates before any resource execution

TDD pure/fake-host controls then actual pinned-host synthetic parity:

- Off-by-default traversal unchanged; wrong type, cache-enabled training,
  changed mount/identity/mode and invalid checkpoint requests fail closed.
- Loss/logits and every factor gradient compare checkpoint-on versus off on
  identical actual-host synthetic inputs, both arms, all nine declared grid
  configurations; include frozen-input/no-input-grad first active port, zero
  initialization, nonzero factors, padding mask and every token in each of the
  two complete tokenizer-derived candidate sequences, even if lengths differ.
- CPU FP32 exact parity; GPU BF16 numerical comparisons use the existing
  conformance rtol1e-3/atol1e-3 plus identical candidate ordering. No tolerance
  broadening after results; every compared gradient must be finite, present
  and appropriately nonzero in a declared nonzero-factor fixture. Compare
  zero gradients explicitly, not with an allclose test that hides missing ones.
  For each nonzero-reference FP32 factor gradient, also require relative L2
  error `norm(actual-reference)/norm(reference) <= 1e-5` and cosine similarity
  at least `1-1e-6`, computing comparison norms in float64. If reference norm
  is exactly zero, actual must be present and exactly zero. These checks apply
  to individual and accumulated gradients; missing/zero actual with nonzero
  reference fails. They supplement, not replace or broaden, elementwise checks.
  A small nonzero-gradient sign/direction mutation that passes elementwise
  allclose under atol1e-3 must still be killed by the scale-sensitive criterion.
- Repeat checkpointed backward from fresh matching state; compare accumulation
  across16 microbatches and one identical optimizer update with off-path
  synthetic reference at a short fixed feasible length; compare resulting
  factors and complete AdamW moment/step state as well as gradients/loss.
  Zero-initialized B may legitimately give zero A gradients, so freeze its
  expected pattern separately from the nonzero-factor fixture. Actual base hashes
  before/after must match; no base parameter gradient or optimizer membership.
- Deliberate stale-layer/index, detached-factor and disabled-grad mutations must
  fail tests. Preserve official-forward no-mount, zero/detach and cached-inference
  conformance in the unchanged evaluation path. Run relevant regression suites.

Parity fixtures use synthetic sequences only, never task files or training
labels. Their optimizer updates test implementation math only and are not
training authority, a capability gate or the R0.4 pilot. Detailed fixed lengths,
seed/state construction, artifact binding and mutation targets must be declared
in a separate implementation/execution detail before actual-host runs.

## 6. Prospective resource qualification, not the200-update pilot

Before executing, freeze a separate exact synthetic qualification plan. It must
use actual tokenizer candidates, full masked-label loss, proposed4096 common
sequence and4608 control maximum, matched factor/optimizer construction,
accumulation16 and the selected checkpoint policy, not a one-token backward.
Primary nine configurations x two arms all require measured training fit.
The nonblocking q+v reference also needs its own declared fit evidence; do not
infer its fit from q-only factors. Profile/RAG frozen-base4608 full-candidate
scoring needs separate measured inference fit. All cells/attempts are preserved;
do not only report a favorable M-r8 cell or treat an unrun cell as covered.

Each invocation is a named fresh offline process from a committed clean source
and locked research environment, with exact model/inventory/source hashes,
synthetic input/candidate/label roots, actual exit, raw stdout/stderr and resource
receipt. No acquisition, task data, model updates to base or held-out access.
Record full CPU/GPU/RAM/free disk observations, forward/backward/optimizer
timing, allocated/reserved CUDA peaks, finite losses/gradients and factor/base
digests. Distinguish sampled RAM from OS peaks. Preserve20GiB free C:; no user
process termination, paid compute, undeclared retry, altered dtype/attention,
smaller effective batch or changed optimizer on failure. Qualification consumes
and journals the existing global resource budgets, not an unmetered loophole.

The exact count and policy for disposable synthetic optimizer updates, short
parity references, per-cell runtime bound and whether qualification includes
prefill/candidate scoring must be frozen in that detail before launching.
No dataset-training command is admitted by this document or by qualification.
Measured failure produces a precise local resource boundary and a separately
reviewed next method; no capability falsification follows solely from OOM.

## 7. Adoption and implementation order

1. Independent evidence/spec and scientific architecture review must explicitly
   accept or reject the residual-risk decision and common/control allocation.
2. If accepted, freeze the detailed checkpoint implementation/parity/qualification
   plan, then implement TDD. No corpus DP rerun is needed to implement this path.
3. Qualify the actual pinned host as synthetic-only execution under the detailed
   reviewed plan; no task training or source-rights conclusion follows.
4. A passing candidate still needs source/code rights, independent sealer,
   mixed-component/paired evaluator and complete machine-readable R0.0 validator
   and committed freeze before dataset training. Preserve held-out boundary.
5. Run the unchanged four-job200-update R0.4 pilot and full immutable development/
   confirmation matrix only when those original authority gates actually pass.

This proposal is neither8192 adoption nor a claim of zero information loss.
Final ALC-0 still requires real retrieval-off neural capability, frozen base,
fresh-process remount, controls and all P1-P14; persistence/toy fit is not enough.
