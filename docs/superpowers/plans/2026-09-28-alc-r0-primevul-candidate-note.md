# ALC-R0 PrimeVul development-source candidate (2026-09-28)

This note records a possible replacement for the CodeXGLUE/Devign target-family
dataset after the frozen Devign development source failed the exact-label
conflict gate. It does **not** amend the frozen 2026-09-20 preregistration or
authorize training, held-out access, R0.0 PASS, or an ALC-0 claim.

## Source and observed preflight

- Original PrimeVul release: the authors'
  [repository](https://github.com/DLVulDet/PrimeVul) and
  [paper](https://arxiv.org/abs/2403.18624), with source files in
  Google Drive folder `19iLaNDS0z99N8kB_jBRTmDLehwZBolMY`. Only the original
  train file `1qRO_Qdy7KXcZbJJAu5J3VZWkRVvT4Kbu` and validation file
  `1CMQ185Ww_bsBWGbJe4sZW0vzceWnmNE7` were acquired and read. The test
  file was not downloaded or inspected. The repository describes its license
  as MIT; the scope of that declaration over the Drive-hosted dataset is
  unresolved and must not be inferred from the repository alone.
- The development-only verifier binds exact raw file lengths and SHA-256,
  strict JSONL/UTF-8 structure, unique `idx`, binary targets, row/class counts,
  and exact normalized-code clone groups. It rejects any extra file, including
  a test file. The receipt is
  `results/alc_r0_primevul_development_candidate_20260926.json`.
- Train: 184,427 rows, 5,574 positive; validation: 25,430 rows, 699 positive.
  There are 201,484 exact normalized-code groups across 209,857 development
  rows, 8,338 duplicate groups, 1,237 groups spanning train/validation, and
  **zero exact opposite-label groups** under the existing Devign normalization.
  This is a necessary preflight only. It does not show near-clone cleanliness,
  validation eligibility after group exclusion, or sufficient sealed-test
  roots/class counts.

## Required next gates before any model run

1. Resolve dataset-specific use/redistribution scope and record the source
   authority. Keep raw code and test examples out of repository artifacts.
2. Run the preregistered 256-permutation MinHash/LSH plus exact five-shingle
   Jaccard >= 0.90 clone audit on development data; fail closed on any
   conflicting-label connected component. Recompute retained validation
   roots and class counts after train-root exclusion. A clean exact-hash scan
   alone does not satisfy this gate.
3. Write an explicit versioned preregistration amendment that names PrimeVul,
   fixes its task metric/controls/prompt/split/sealer protocol and retains an
   untouched independent confirmatory split. Freeze and hash it **before**
   sealed-test access or training. Do not silently replace the original
   Devign contract or relax thresholds to make a result pass.
4. Complete the R0.0 machine validator and all environment, model, prompt,
   reference, and resource prerequisites. `training_authority=false` until
   that gate passes; no test split has been used as development data.

The frozen Devign negative result remains first-class evidence. PrimeVul is
currently only a data-source **candidate**, not the selected task, a passed
R0.0 source, or a neural capability result.
