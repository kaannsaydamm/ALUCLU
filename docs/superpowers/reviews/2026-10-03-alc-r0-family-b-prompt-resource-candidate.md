# Prospective family-B v3 candidate review

## Exact reviewed scope and verdict

Candidate: `../plans/2026-10-03-alc-r0-family-b-prompt-resource-v3-draft.md`.
Final SHA256:
`3c7e56cd33ffa6aaec0a5baa7cead146bc7a0ca2688c447c1ecf63424e0cdf38`.

Independent GPT-6.1 Sol evidence/spec/code-design lane
`/root/alc_r0_timing_code_gate_61`: **APPROVE**.
Independent GPT-6.1 Sol scientific architecture lane
`/root/alc_r0_timing_architecture_gate_61`: **CLEAR**, residual information risk
accepted **for prospective synthetic qualification only**. Scoped synthesis:
**APPROVE for advancing this one candidate to detailed specification**.

Both lanes independently reread complete revised bytes and verified the digest.
They did not edit files, run tests, execute models/corpus/native code, train,
access held-out data or spawn additional agents. This is candidate-specification
review, not empirical fidelity, fit or neural capability evidence.

## Initial review and resolved comments

Initial draft SHA256:
`838e85ab84eedfc5343146bbef0f194711de9cbb59d383fc59056bb11b4ce943`.
Scientific architecture returned CLEAR for its bounded prospective scope;
the evidence/spec lane returned COMMENT. Its three concrete issues were:

1. Elementwise gradient atol1e-3 can accept a substantial small-gradient
   sign/direction error even when both gradients are finite and nonzero.
2. Actual profile/RAG control insertion and separator accounting were not yet
   bound. Existing prompt code cannot establish an unimplemented control path.
3. State guarding needs an outstanding-graph lifetime and entry checks before
   recomputation; non-reentrant early-stop can skip a trailing check.

The final candidate now supplements elementwise checks with fixed per-factor
relative-L2/cosine criteria, explicit zero/missing/nonzero patterns, accumulated
gradient and complete optimizer-state/factor comparisons. A small-gradient
mutation that passes loose allclose must be killed.

Control IDs precede the unchanged separately encoded common query/candidate;
separator/framing counts within512. RAG admits whole ranked prefixes using
at-most64-token example ID blocks, reserves separator IDs in fit checks and
does not decode/re-encode truncated examples or retokenize query boundaries.
The document calls this a proposed new binding, not proven old behavior.

Guards must cover graph lifetimes, accumulation, failure cleanup, factor/layer
identities, tensor versions, modes, device/dtype and immutable mask/position
inputs. Supplied mutable caches are rejected even when use_cache=False. Checks
must occur before the first recomputed operation, not only at its tail.
Both lanes judged these comments resolved at the candidate level.

## Scientific rationale and preserved objections

4096 common query plus512 controls within4608 is a defensible single candidate
to qualify, not an automatically selected optimum. It explicitly changes the
old uniform common/total limits, keeps Banking unchanged, preserves equal
family-B query IDs across arms and gives neural arms no filler. The host's8192
ceiling says nothing about local GPU fit.

The strongest counterargument remains that fewer contradictions and more edit
exposure do not demonstrate vulnerability-bearing signal or learnability.
The candidate keeps minority-class information loss, observation-level
contradictions, all244 unresolved pairs and single-function limits explicit.
Those populations must not be pooled. Imperfect input does not falsify useful
learning, but qualification success does not justify final scientific adoption.

Eager non-reentrant block recomputation is a proposed separately validated
compute-memory tradeoff. An HF flag alone cannot implement it in our explicit
decoder traversal. There is no checkpoint fidelity or memory PASS yet.

## Required next gate

Freeze one detailed implementation/parity/qualification plan with exact
synthetic fixtures, factor states, lengths, seeds, update counts, gradient and
optimizer-state comparison rules, complete matrix, runtime/resource limits,
artifact/source/model binding and invocation review. Then implement TDD; run
actual-host synthetic parity/qualification only after those scoped gates pass.
No further generic corpus diagnostic or automatic budget search is required
to specify this detail.

This review does not adopt the4096 amendment or grant final prompt freeze,
actual-host execution approval, dataset training, source rights, sealer/R0.0
validation or ALC-0 PASS. Unchanged512 family-B scientific freeze remains BLOCK.
Successful future qualification permits continued adoption review only; all
original dataset-training authority gates and the unchanged200-update pilot
remain required.
