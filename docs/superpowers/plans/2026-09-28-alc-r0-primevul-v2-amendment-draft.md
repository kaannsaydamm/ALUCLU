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

1. Independent code/science review of source binding, clone graph, pair graph,
   mixed-label handling, cross-split exclusion, deterministic ledgers, and
   scalable/reference parity. A repeatability run is necessary but cannot by
   itself establish algorithmic correctness. A separate structural checker now
   covers roots, exact groups, pair edges, overlap exclusion, and retained
   representatives on bounded fixtures; it has not yet audited the full
   corpus and does not rediscover near-clone edges independently.
2. A versioned machine-readable preregistration and fail-closed validator for
   source/split/label/prompt/control hashes, exact estimator/bootstrap fixtures,
   all P1–P14 thresholds, sealer-only test acquisition and output schema,
   cardinality matrix, environment locks, and clean-checkout freeze.
3. Original-release data and underlying-code rights/provenance review; the
   authors' repository MIT file alone does not resolve external JSONL scope.
4. An independently controlled sealer/key broker and test-acquisition process
   satisfying the v1 isolation and denial tests. Do not read held-out data to
   decide whether this draft should be adopted.

Until these are passed, `training_authority=false`, `held_out_data_present=false`
on the development side, and **ALC-0 remains OPEN**.
