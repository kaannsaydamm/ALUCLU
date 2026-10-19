# ALC-R0 Devign exact-label-conflict preflight (2026-09-26)

This is a negative development-data result under the already frozen
`docs/superpowers/plans/2026-09-20-alc-r0-neural-capability-proof.md` rules. It
does **not** amend the dataset, labels, clone threshold, hypothesis, or acceptance
floor. It does not authorize training or access to the official test split.

## Scope and result

- Input: only the byte-pinned official Devign train and validation Parquet files
  at repository revision `69bd48c03223c2104342acd9a807caf61ac3efb8`,
  accepted by `load_verified_devign_development`.
- Preflight: strict UTF-8/NFC/LF/trailing-ASCII/outer-blank normalization,
  normalized SHA-256 grouping, and label comparison across all 24,586
  development rows. No probabilistic MinHash or LSH decision is needed to
  detect these conflicts.
- Observed: 24,532 distinct exact normalized-code groups; 54 duplicate groups,
  each with two members bearing opposite Boolean labels. A second independent
  scan found the same 54 groups. One pair was compared directly: source IDs
  `devign:00000817` and `devign:00015755` normalize to identical UTF-8 bytes
  (SHA-256 `ef28bc19e1aa874e4f608b069372acfbdf36449d44cebb250e8b415ef51a1c5c`)
  but have `False` and `True` labels, respectively. No source code is committed.
- Canonical metadata-only receipt:
  `results/alc_r0_devign_exact_conflict_preflight_20260926.json`. Its
  conflict-ledger SHA-256 commits the ordered conflicting digest/member/label
  tuples without publishing those tuples in the receipt. The source receipt
  SHA-256 binds the exact upstream development manifest.

The frozen plan says **any clone root with conflicting labels fails R0.0**.
Therefore this Devign source cannot enter the declared training or confirmatory
run. This is a dataset qualification failure, **not** a falsification of the
neural-capsule hypothesis. Do not resolve it by silently dropping, relabeling,
or threshold-tuning the contradictory pairs. `training_authority=false` and
R0.0 remains closed.

## Implemented but not promoted clone machinery

The fixture-tested development-only reference implements:

- 256 deterministic affine-32 MinHash permutations from seed `20260916`;
  each five-token shingle is canonical-JSON encoded, SHA-256 hashed, and its
  first 32 big-endian bits are used as the affine input;
- coefficient `a_i` = odd first 32 bits and `b_i` = next 32 bits of
  `SHA-256("aluclu-devign-minhash-affine32-v1\\0" || seed_u64_be || i_u32_be)`;
  the 256 `(a_i,b_i)` pairs, packed as big-endian `u32` pairs, hash to
  `08ed1ca23b267dc9f06267b318f2e95990c72c0f2b06480647afcd79aeaf9e42`;
- a 0.85 soft-threshold LSH candidate index with 13 bands of 19 rows (the
  equal-weight false-positive/false-negative area minimum for 256 permutations,
  using 247 values), then **exact** five-shingle Jaccard `>= 0.90` via an
  integer comparison before union;
- lexicographically minimal union-find roots, fail-closed label conflict,
  one representative per split, and train-root exclusion from validation.

The candidate-index formula and its soft-threshold caveat follow the
[datasketch MinHashLSH documentation](https://ekzhu.com/datasketch/lsh.html).
The implementation is in-repo rather than a `datasketch` dependency. The
research environment pins NumPy `2.5.3`; the source and fixture digest bind
the rest of the algorithm. Because exact conflicts stop preflight, the LSH was
**not** executed on the full official development data; synthetic transitive
and nonduplicate fixtures are not a full-corpus accuracy or runtime claim.

## Next decision boundary

The original R0.0 plan cannot proceed with this frozen Devign artifact. A
scientifically defensible continuation needs a transparent preregistration
amendment **before any held-out access**, including an independently sourced
replacement task/dataset (or a justified new data protocol), an untouched
confirmatory split, licensing review, a fresh conflict/clone audit, and
revalidated controls/metrics. Other independent engineering prerequisites can
continue, but no ALC-0 capability claim follows from this preflight.
