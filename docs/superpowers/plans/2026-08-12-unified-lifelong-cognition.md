# ALUCLU Unified Lifelong Cognition Roadmap

> Reconstructed on 2026-08-22 from the unpushed V2 trajectory. This file is a
> roadmap; each implementation task receives its own reviewed plan and gate.

## Binding invariants

- The published v0.1 four-lane model remains the immutable comparison baseline.
- Memory is not belief; inference is not evidence; familiarity is not exact
  recollection; model output cannot certify itself.
- Exact and approximate memory are distinct in types, storage, metrics, and
  user-facing behavior.
- Neural working state is bounded. Lifetime encrypted storage may grow and is
  measured separately.
- Host-model weights remain frozen in normal use.
- Every external side effect is typed, budgeted, journaled, and fail-closed.
- Claims such as SOTA, zero forgetting, or fastest are blocked until their
  predeclared experiments pass.
- Task 1 scale persistence must be CLEAN before Task 2 implementation starts.
- Licensing/IP, multilingual README, paper, release, and push are deferred to
  Tasks 13–14.

## Fixed execution order

### Task 1 — encrypted lifetime persistence and scale gate

Reconstruct the accepted round-5 behavior, then implement schema v2,
`DirectoryRecordKeyStore`, the separate fail-closed OS-keyring per-record DEK
profile, single-object verified sessions/cursors, streaming verification, crash
recovery, and the 8,192-turn RSS/disk/latency gate.

### Task 2 — sensorium, exact recollection, calibration, reconsolidation

Implement typed observations, storage-pure duplicate receipt classification,
deterministic event boundaries, exact/approximate recall separation, bounded
working state, calibrated selective-risk profiles, and explicit
reconsolidation without nested ledger sessions.

### Task 3 — frozen host bridge and routing ABI

Implement `FULL_WHITEBOX`, `COMPAT_BLACKBOX`, and later `NATIVE` capability
profiles; explicit layer junctions; request-scoped routing authorization;
frozen differentiable output-head artifacts; call correlation; and physical
token/memory preflight. CPU eager-attention host requests are capped at 2,048
tokens unless a measured capability profile proves a safer bound.

### Task 4 — semantic evidence cortex

Implement temporal claims, provenance, source-copy independence, contradiction
and supersession, bounded encrypted family projections, and verification
states that cannot turn a user statement or model output into external fact.

### Task 5 — planner, prospective memory, and tools

Implement typed plan/act/observe/revise steps, schema-validated tool calls,
allowlists, timeouts, rollback policies, action-outcome history, eligibility
traces, and active information-seeking under the shared resource contract.

### Task 6 — pure plastic proposal substrate

Implement fixed-capacity expert/anchor math as a pure computation layer. Task 6
does not mutate live state or mint runtime authority. The chronology is
permit → read-only evaluation grant → evaluation worker → sealed proposal →
learning grant → Task 7 training transaction.

### Task 7 — transactional sleep, learning, deletion, rollback

Implement the sole mutator for private candidate training, sealed canaries,
PREPARED publication, crash-forward recovery, deletion drain, and honest
rollback classes. A lineage whose keys were shredded is irreversible and is
never advertised as exactly rollback-capable.

### Task 8 — resource governor

Implement issuer-bound one-use leases, distinct SUM and PEAK accounting,
REQUEST and SLEEP_JOB owner separation, fail-closed overrun settlement, bounded
controller inputs/outputs, and a learned controller that remains disabled
until held-out Pareto gates pass.

### Task 9 — unified runtime and CLI

Implement one explicit phase machine, one passed-through Task 1 verified
session, durable `WORK_INTENT → DISPATCH_FENCED → settlement`, deterministic
replay slots, deletion/read barriers, secure export, and machine-readable CLI
results. Domain policy remains in Tasks 2–8 rather than a god object.

### Task 10 — native ALUCLU language model

Implement native config/model/checkpoint APIs with explicit
`intermediate_size` and `rms_norm_eps`, then the bounded-state causal LM needed
for conversion and future pretraining.

### Task 11 — SmolLM2 conversion and training infrastructure

Implement explicit wrapper attachment and staged attention replacement using
the pinned SmolLM2-135M teacher, layer regression, alpha transitions,
distillation/recovery, deterministic datasets, safe checkpoints, and exact
resume. No brittle monkeypatch or forward-hook architecture.

### Task 12 — experiments and claim gates

Run baseline/ablation, selective-risk, memory, forgetting, plasticity,
security, latency, state-byte, persistent-byte, FLOP, energy, and replay-cost
experiments with predeclared seeds and confidence intervals. Components survive
only when their quality/resource Pareto gate passes.

### Task 13 — legal/IP and publication materials

Only after measured technical gates: obtain qualified legal review; decide the
V2 community/research/commercial license regime; address prior MIT history,
CLA, trademark, and patent timing; then update package metadata, seven README
languages, diagrams, and the long LaTeX paper consistently.

### Task 14 — release audit and push

Perform a clean-clone install/test/lint/build/release audit, generate hashes and
SBOM/artifacts, remove bloat without deleting evidence, verify license notices,
and only then push the complete non-bloat repository.

## Current checkpoint

The other PC's accepted Task 1 round-5 commit (`b011a75`, 180 tests) was never
pushed and cannot be recovered from this checkout. The active reconstruction
plan is `docs/superpowers/plans/2026-08-22-task-1-persistence-reconstruction.md`.
No later task may be marked started until that plan's final gate is clean.
