# ALC-R0 code-task data/protocol recovery decision (2026-09-28)

Status: **development design decision only — not a frozen amendment, R0.0
PASS, training permit, or held-out evaluation**. The original
`2026-09-20-alc-r0-neural-capability-proof.md` remains the controlling frozen
plan until a complete, versioned, independently validated amendment replaces
the affected code-family contract. Devign's 54 exact opposite-label groups
and PrimeVul's confirmed opposite-label near-clone pair remain negative
evidence; neither is rewritten as PASS.

## Evidence and failure class

The original PrimeVul authors explicitly include vulnerable functions and
textually similar patched/benign counterparts, and describe pair-wise
evaluation in [their paper](https://arxiv.org/abs/2403.18624), Section IV-B2.
The separate original-release train/validation paired files were acquired
from the [authors' repository](https://github.com/DLVulDet/PrimeVul) release
folder, but **neither** the full nor paired test file was acquired or read.
The paired-development receipt is
`results/alc_r0_primevul_pairs_development_20260928.json`.

The verified train/validation paired files contain 4,354 and 562 adjacent
opposite-label pairs, respectively. Every paired row is exactly identical to
its corresponding record in the previously pinned full development source.
All adjacent pairs share project and commit. However, pairs are **not all
independent**: train has 8,703 unique IDs for 8,708 pair rows (4,344 graph
components of size 2 and five of size 3); validation has 1,120 unique IDs
for 1,124 pair rows (557 components of size 2 and one of size 6).

The confirmed near-conflict witness `primevul:7`/`primevul:11213` is *not*
asserted to be one of the authors' adjacent pair edges; its records have
different commits. The observed failure class is **evaluation-design / data
protocol mismatch**: a blanket "mixed labels in a near-clone component =
source invalid" rule is incompatible with this task's intended hard examples.
The evidence does not show that the labels are wrong or that the neural
capsule hypothesis is false.

## Alternatives compared before any confirmatory access

| Route | Scientific validity / correctness | Capability preserved | Compute / complexity | Leakage / security | Decision |
|---|---|---|---|---|---|
| Keep frozen Devign or PrimeVul rule and train anyway | Violates an explicit R0.0 fail gate | Unproven | Low initial cost, invalid result | Mixed-label roots contaminate stated unit | **Reject** |
| Drop or relabel every mixed-label near-clone component | Removes precisely the vulnerable/patch distinction and changes the tested distribution after observing failure | Weakens the code task | Moderate | Selection bias; may inflate metric | **Reject** |
| Switch to another code dataset/task | Can be valid after new untouched split and full preregistration | May change the intended capability | New acquisition, controls, and model feasibility work | Depends on new source/license | **Reserve fallback** |
| PrimeVul with pair/clone-component-aware units | Can retain hard positive/negative distinctions while treating dependence explicitly | Keeps vulnerability detection and original paired challenge | Highest implementation/validation cost; full graph and sealer required | Requires component-level cross-split exclusion and sealed-test isolation | **Preferred next design to formalize, not yet authorized** |

This choice is about which **development protocol to engineer next**, not a
claim that PrimeVul has passed. Its exact dataset-license scope remains
unresolved. No acceptance threshold is lowered or reinterpreted here.

## Required explicit amendment and implementation gates

The preferred route must be issued as a **new versioned preregistration**
before training or any test access. At minimum it must specify, implement,
hash, independently review, and machine-validate all of the following:

1. Replace only family B's source/task contract in plan Section 4.2; retain
   the frozen SmolLM2 host, capsule/LoRA architecture and search grid, the
   Banking77 family, retention suites, fresh-process isolation, and the
   numeric P1–P14 floors unless a separately justified, stricter gate is
   added. The old Devign result remains in the evidence ledger.
2. Treat **identical normalized code with opposite labels** as an error.
   Preserve the frozen 256-permutation MinHash, 13-by-19 LSH candidate rule,
   five-token exact Jaccard >= 0.90, and lexical union-find roots. For
   different-code near-clone components, retain both labels. Combine the
   near-clone graph with the authors' explicit pair-edge graph so any shared
   source ID is one dependency component, not multiple independent pairs.
   Freeze the exact duplicate-row representative rule before data use.
3. Make the full development/train and validation datasets the primary binary
   task. Exclude a complete validation component if it connects to train;
   the independent sealer excludes complete test components connected to
   development. Do **not** discard mixed-label components merely because
   they are hard. The proposed confirmatory floor is no lower than **1,500
   independent components** and **250 components containing each class**;
   encode the exact component/class counting rule before the sealer sees test
   data. A shortfall fails the gate and cannot trigger a floor change.
4. Keep macro-F1 and the existing absolute-point P1–P6/P3 thresholds as the
   primary code-family estimands. Specify the new component-cluster bootstrap
   and one vote per retained distinct code/label observation within each
   component, with the exact duplicate and weighting policy frozen in advance.
   Add the author-provided pair-wise outcomes as a diagnostic or a separately
   preregistered *stricter* gate; never use raw pair rows as independent
   bootstrap observations. The paired test file may be opened only by the
   independent sealer after freeze.
5. Re-freeze prompts, labels, textual-profile and BM25 controls, matched LoRA,
   shuffled/wrong-family controls, evaluator and statistical fixtures,
   run-cardinality matrix, split/source hashes, access receipts, and sealer
   contracts. Re-run R0.0's adversarial validator, clean-checkout and
   environment checks. `training_authority=false` until this exact amended
   validator passes.

The next concrete implementation slice is a development-only pair/clone
component reference plus fixtures for overlapping and mixed-label components.
The full 209,857-row graph and resource fit must then be measured. If this
protocol cannot preserve a valid untouched confirmatory unit or satisfy the
predeclared test floor, use the reserve new-source route rather than changing
the threshold after seeing the result.
