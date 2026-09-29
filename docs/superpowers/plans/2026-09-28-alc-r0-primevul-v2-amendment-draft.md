# ALC-R0 family-B PrimeVul amendment v2 — DRAFT, NON-AUTHORIZING

Status: **candidate protocol only**. This document does not amend the frozen
2026-09-20 v1 plan, permit test access, or authorize training. It is written
after development-only evidence and before any confirmatory PrimeVul test
access. Independent scientific review, machine-readable freeze, source-rights
review, and R0.0 validation remain blocking.

## Scope and preserved gates

Only target family B's source, duplicate/statistical unit, and sealer-specific
contract are proposed to change. The frozen SmolLM2-135M host/revision,
Banking77 family, ResearchCapsuleV0/LoRA comparison, port/rank search grid,
training seed/cardinality matrix, attach/detach and fresh-process isolation,
retention and negative-control suites, and numerical P1–P14 floors are retained.
The Devign exact-label conflict failure remains in the evidence ledger. No
threshold is lowered because PrimeVul development data were inspected.

## Proposed family-B source and development graph

- Source: authors' *original-release* PrimeVul train and validation JSONL,
  plus their adjacent train/validation paired files; use the exact byte counts,
  SHA-256 digests, row counts, and labels pinned in
  `primevul_source.py` and `primevul_pairs_source.py`. Do not substitute the
  later v0.1 subset or a third-party mirror. The authors' test and paired-test
  files remain inaccessible to development and may be acquired only by the
  independent sealer after the amended protocol is frozen.
- Preserve v1 UTF-8/NFC/line/whitespace normalization, tokenizer, five-token
  shingles, normalized-code SHA-256, 256-permutation MinHash with seed
  `20260916`, 13 bands by 19 rows, exact Jaccard >= 0.90 after LSH candidacy,
  and lexicographically minimal union-find source-ID roots. These are *not*
  tuned to make the replacement pass.
- Add an edge between the ordered 1/0 members of every verified adjacent
  author pair. Shared endpoints join transitively. Reject a self, duplicate,
  unknown, wrongly labeled, cross-split, or inconsistent-content pair. Join
  exact same-code/same-label records; reject exact same normalized code with
  opposite labels. Different-code near clones with opposite labels remain in
  one dependency component with both observations; do not relabel or drop them.
- Within each split retain the lexicographically smallest source ID for each
  distinct normalized-code/label observation. A component may retain several
  observations, including both labels. Remove **all** validation observations
  from any component connected to train. Development commits source, pair-edge,
  component-root, retained-train-ID, and retained-validation-ID ledgers by
  canonical SHA-256; raw source text is not committed.
- Existing full-development graph evidence from frozen source commit `101c302`
  is an input to review, not a training gate. It retained 22,157 validation
  components; 552 contain a positive and 22,087 contain a negative observation.
  The overlap (482 mixed components by inclusion-exclusion) counts in **both**
  class-support sets, never as two independent components. A second complete
  development run reproduced the first run's canonical stdout byte-for-byte
  (SHA-256 `e54c729d9c7d3ccaa3f50efcb6edcfc492c880131f0c5cf61df1db9714533243`);
  this establishes deterministic replay, not graph correctness. Independent
  audit is still required before freeze.

## Proposed point metric and uncertainty unit

- Primary family-B metric remains fixed-label `[safe, vulnerable]` macro-F1;
  balanced accuracy and MCC remain companion metrics. For a point estimate,
  each retained distinct normalized-code/label observation contributes one
  prediction/label vote. Do not collapse a mixed-label component to a single
  label, and do not weight an author pair as two independent clusters.
- The statistical resampling unit is the **dependency component root**. In
  each of the frozen 10,000 paired bootstrap replicates, sample component
  indices with replacement. Every selected root contributes *all* of its
  retained distinct observations, with multiplicity equal to the number of
  times that root was sampled. Use the same sampled component vector for all
  arms and selected seeds. Then compute fixed-label macro-F1 per seed/arm and
  the existing five-seed paired differences and Bonferroni bounds. Banking77,
  LAMBADA, and WikiText resampling rules remain unchanged.
- This fixes the unit of statistical uncertainty, not the observation-level
  point estimand. An independent hand fixture must include a mixed-label
  component, a two-observation same-label component, and an isolated component;
  it must prove that duplicate rows add no vote and resampling a mixed
  component copies both labels together. No final score may be used to choose
  the weighting rule. A non-authorizing exact arithmetic reference now lives in
  `src/aluclu/alc_r0/primevul_component_metric_reference.py`, with fixed-label
  macro-F1 and duplicate/cluster hand fixtures. It does not implement the
  10,000-replicate evaluator or confidence bounds.
- Author-pair outcomes are diagnostic only until separately preregistered as a
  stricter gate. Paired rows may not enter bootstrap as independent samples.

## Proposed independent sealer contract

- The sealer, never development, acquires exact pinned original test and
  paired-test bytes. It applies the *same* normalization, clone candidacy,
  exact-Jaccard, pair-edge, and duplicate-representative rules to the combined
  train/validation/test dependency graph. It excludes every **entire** test
  component connected to a development component. Source IDs and graph roots
  spanning test stay within the sealer boundary before terminal scoring.
- Before confirmation, development may receive only aggregate input/retained
  example counts, independent component count, positive-containing and
  negative-containing component counts, exclusion counts, and the complete
  encrypted-shard commitment allowed by v1 section 8.1. A component with
  both labels increments both class-support counters but the total only once.
  The confirmatory floor remains at least 1,500 independent components and
  at least 250 components containing each class. A shortfall fails the gate;
  it cannot trigger a floor change after test access.
- The sealed scorer uses the same observation-level point metric and
  component-cluster bootstrap defined above. Pair-wise diagnostics, if run,
  are isolated from the blocking P1–P14 decisions. The v1 key-broker,
  namespace, one-transaction, no-network, ciphertext, and access-counter
  policies are preserved.

## Required proof before this draft can become an amendment

Development-only, non-authorizing pair-prompt contrast diagnostic (declared
before its full-data execution): verify the pinned original train/validation
and paired-development bytes, then encode each author-ordered vulnerable/patch
pair with the same SmolLM2 tokenizer and fixed 512-token candidate prompt.
Report train and validation pair counts, counts with both/one/neither code
truncated, and the count whose **complete prompt token-ID sequences are
identical**, plus ordered prompt-pair roots. An identical pair is provably
indistinguishable from this input alone; a nonidentical pair is **not** proof
that the vulnerability-bearing change survived or that a model can learn it.
This diagnostic covers author development pairs, not necessarily the final
deduplicated/excluded retained cohort. It adds no acceptance threshold and
cannot authorize training or test access; its result informs the independent
pre-held-out scientific decision below.

Development-only result from source commit `4bc8160`: **1,284/4,354 (29.49%)**
train and **160/562 (28.47%)** validation author pairs collapsed to identical
complete prompt IDs. Separate independent code and science reviews found the
diagnostic suitable for this narrow inference; the science review marked
freezing the **current 512-token head/tail family-B prompt unchanged BLOCK**.
This is not a falsification of the broader ALC-0 hypothesis. A new versioned,
pre-held-out single-function prompt proposal and matched-arm budget policy must
be reviewed and tested on development data before any family-B freeze. The
current v1 prompt and failed candidate evidence must remain in the ledger.

Before a v2 prompt is proposed for freeze, run one additional *non-authorizing*
development-only context-budget sensitivity grid using the same pinned original
train/validation author pairs, tokenizer, normalization, head/tail rule, label
candidates, and receipt checks. The complete prespecified grid is common
candidate-sequence budgets **512, 1024, 2048, 4096, 8192** tokens, evaluated
in that order. Report exact prompt-ID collision counts, both/one/neither
truncation partitions, ordered pair-prompt roots, source/model roots, and local
runtime/resource observations for each budget. Do not use held-out data, model
forwards, or label outcomes to pick or tune a budget. These measurements test
only an information-availability mechanism; they do not establish learnability,
acceptable training memory, or a new acceptance threshold. Keep the 512 result
and every grid result, including negative ones. A separate versioned,
independently reviewed amendment must choose the single-function prompt and
equalized-arm budget *before* training or confirmatory access.

The complete grid ran from clean source commit `e316531` with terminal exit
zero at every budget. Exact prompt-ID collisions (train author pairs out of
4,354 / validation author pairs out of 562) were **1,284/160 at 512**,
**671/88 at 1,024**, **311/41 at 2,048**, **124/14 at 4,096**, and
**37/4 at 8,192**. The last value equals the pinned model's maximum context;
it does not mean that a larger single forward is available. Complete counts,
truncation partitions, ordered roots, provenance, runtime observations, and
hashes are in `results/alc_r0_prompt_budget_grid_e316531_20260929_*` and
`TRAJECTORY.md` checkpoint 62. More context reduces exact input collisions,
but nonidentical prompts do not prove that the vulnerability signal is intact
or learnable. The author-pair population is not automatically the final
retained cohort, and local training memory at these budgets remains untested.
Thus the grid does **not** select a v2 budget or authorize ALC-0 training.
The PrimeVul authors also note that some vulnerabilities span multiple
functions, an additional limit on any single-function classifier
([paper](https://arxiv.org/html/2403.18624v2)).

Before choosing a longer-context v2 candidate, run a separate **synthetic-only
local gradient resource probe**, not the v1 R0.4 200-step pilot. Predeclared
sequence lengths are **512, 1024, 2048** in ascending order; at each length,
run `ResearchCapsuleV0` and exactly matched q-only LoRA, separately, with the
pinned real SmolLM2-135M host/revision, BF16 host, FP32 rank-8 factors at ports
14 and 29, batch 1, a deterministic synthetic token sequence, one final-token
cross-entropy backward, `use_cache=False`, and **zero optimizer updates**.
Use the locked Windows research environment and eager attention, requiring at
least 20 GiB free on C: before each process. Record finite loss/gradients,
frozen-base pre/post canonical digest, CUDA allocated/reserved peak, wall time,
exact source/model/environment identity, and every failed/OOM attempt. Each
arm/length is a fresh process; a failure does not become a PASS by silently
reducing length, changing dtype, or altering the effective batch. This probe
tests resource feasibility only: it neither licenses the PrimeVul data nor
proves 200-step training, full task learning, retention, or portability.

The six synthetic-only cells were run from clean source commit `d4fb2d1` and
all returned exit zero with finite loss and gradients, identical pinned-base
pre/post digests, and zero optimizer updates. CUDA peak allocated memory was
**683.1 / 696.6 MiB** at 512, **1,483.3 / 1,535.4 MiB** at 1,024, and
**4,423.5 / 4,602.0 MiB** at 2,048 for capsule / matched q-only LoRA,
respectively. Receipts and exact hashes are recorded in
`results/alc_r0_context_gradient_probe_d4fb2d1_20260929_*` and trajectory
checkpoint 64. The tested loss supervises only a single final token; these
numbers are **not** a full label-sequence training-memory bound. The 2,048
cell fits one backward on the 6,141-MiB local GPU, but no optimizer step,
microbatch sequence, 200-step stability, or real-data capability was proven.
No longer budget was silently selected or authorized.

Before using author-pair prompt collisions to judge the proposed graph-cleaned
family-B cohort, run one additional **development-only, non-authorizing**
survivor-pair audit. Rebuild the pinned train/validation graph with unchanged
rules and require its pair-edge, component-root, retained-train-ID, and
retained-validation-ID ledgers to match the prior full graph. For each split,
classify every ordered author pair by whether both endpoints, only the
vulnerable endpoint, only the safe endpoint, or neither endpoint survives in
that split's retained observation set; these four counts must sum to the
verified author-pair count. For the **both-retained** subset only, repeat the
unchanged prompt-ID collision and both/one/neither truncation counts at the
complete predeclared common-budget grid **512, 1024, 2048, 4096, 8192**, in
that order, with the same pinned tokenizer and prompt. Preserve the ordered
prompt-pair roots and source/model/graph provenance; emit only aggregates,
not code or IDs. Zero surviving pairs, if encountered, must be reported as an
empty diagnostic, not silently divided by zero. This is a conditional
description of surviving *author pairs*, not of all retained observations;
it cannot select a budget, establish vulnerability learnability, authorize
training or held-out access, or alter any acceptance threshold.

1. Independent code/science review of source binding, clone graph, pair graph,
   mixed-label handling, cross-split exclusion, deterministic ledgers, and
   scalable/reference parity. A repeatability run is necessary but cannot by
   itself establish algorithmic correctness. A separate structural checker now
   covers roots, exact groups, pair edges, overlap exclusion, and retained
   representatives. It does not rediscover near-clone edges independently. A pinned
   full-development structural-audit runner was run on all 209,857 pinned
   development rows from frozen code commit `323e1ea`; its canonical result
   and 206-event progress evidence are under
   `results/alc_r0_primevul_structural_audit_full_323e1ea_20260928.*`.
   Structural invariants and prior ledger hashes matched. A subsequent
   independent MinHash/LSH/Jaccard implementation also traversed all 209,857
   pinned development rows from frozen code commit `322cc73`; it rediscovered
   19,874 candidates and 13,229 near edges, with every edge in one graph
   component and counts matching the prior receipt. Raw metadata-only output
   and progress evidence are in
   `results/alc_r0_primevul_near_edge_full_322cc73_20260929.*`. This pass
   shares the frozen normalization/tokenization functions and is not an
   independent scientific review or held-out leakage proof.
2. A versioned machine-readable preregistration and fail-closed validator for
   source/split/label/prompt/control hashes, exact estimator/bootstrap fixtures,
   all P1–P14 thresholds, sealer-only test acquisition and output schema,
   cardinality matrix, environment locks, and clean-checkout freeze.
   Before freezing the family-B prompt, independent scientific review must
   confront the development-only class-conditional truncation audit: under the
   candidate 512-token common budget and 499-code-token head/tail rule,
   3,608/5,574 vulnerable train observations (64.73%) and 299/562 vulnerable
   validation observations (53.20%) are truncated, versus 35,468/171,717
   safe train (20.65%) and 4,363/22,210 safe validation (19.64%). This does
   not measure whether the vulnerability itself was removed. The reviewer must
   explicitly accept this information-loss risk, require a fully prespecified
   v2 prompt amendment before any held-out access, or reject this code task.
   No test result may be used to tune the budget or truncation policy.
3. Original-release data and underlying-code rights/provenance review; the
   authors' repository MIT file alone does not resolve external JSONL scope.
   On 2026-09-29, the [authors' README](https://github.com/DLVulDet/PrimeVul/blob/main/README.md)
   was checked: it links the original release and gives training examples.
   The [repository LICENSE](https://github.com/DLVulDet/PrimeVul/blob/main/LICENSE)
   is MIT for the described software and associated documentation. Neither
   page explicitly resolves licensing of the separate Google Drive JSONL
   distribution or the rights of embedded third-party source snippets.
   This is a provenance observation, not a legal conclusion or rights PASS.
4. An independently controlled sealer/key broker and test-acquisition process
   satisfying the v1 isolation and denial tests. Do not read held-out data to
   decide whether this draft should be adopted.

Until these are passed, `training_authority=false`, `held_out_data_present=false`
on the development side, and **ALC-0 remains OPEN**.
