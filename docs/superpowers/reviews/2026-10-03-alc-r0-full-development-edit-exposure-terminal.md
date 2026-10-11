# Full-development edit-exposure terminal review

## Verdict and reviewed boundary

Code/spec/security lane `/root/alc_r0_timing_code_gate_61`: **APPROVE**.
Architecture lane `/root/alc_r0_timing_architecture_gate_61`: **CLEAR**.
Both are independent GPT-6.1 Sol reviews. Deterministic synthesis: **APPROVE
for the completed development diagnostic receipt only**. There were no blocking
code, security, architecture or aggregate-accounting findings in this scope.

The lanes independently inspected the full retained stdout, stderr, launch,
exit and monitoring records and verified the clean frozen source commit
`62b5c7b6577078db5aa79fd2822a9b2381286597` before evidence/documentation edits.
They did not edit files, rerun native DP, reopen corpus/model files, execute
training, or reconstruct the hidden ordered pair-level records. This document
records their returned findings; it is not a new execution or author-only review.

## Terminal evidence and accounting

The actual exit is zero; terminal timestamp is
`2026-10-03T19:59:57.5374821+00:00`, elapsed `1893.5970206` seconds. The launch
and exit agree on the frozen source and child PID30076. Module worker8972 was
the monitored worker; it is not the venv launcher or a Git subprocess.

Stdout SHA-256:
`8bc7eb3e96d96a1292181557dd6e44d46de6d00a857c188dafccc48c67b50a46`.
Stderr SHA-256:
`c6b8e66951862a6a98da4bcd920130b8d998c2e297f16e56ff88a1d6e0a32b77`.
Stdout is one compact JSON document with exactly one terminal LF, no CR and
no progress contamination. The frozen geometry core matches the prior committed
receipt. Original source/pair expectations, source receipt, model inventory/
snapshot commitments, native source hashes, four graph ledgers and second-pass
geometry digests reconcile with their previously reviewed provenance.

| Split | Universe | Attempted | Exact positive | Exact zero | Local unresolved | Terminal D>K | Global unresolved |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Train | 4344 | 4160 | 4118 | 0 | 184 | 42 | 0 |
| Validation | 482 | 469 | 464 | 0 | 13 | 5 | 0 |

Both lanes independently reconciled exhaustive universe/outcome partitions,
attempted/completed partitions, known/unknown geometry, scheduled/visited cells,
exposure denominators, signature histogram sums, hide/expose predicate
complements, direct-total bounds and means from per-pair ratio sums. Scheduled
and visited total `2705212284`; remaining `294787716` completes the declared
3B cap with exhaustion false. Original 100M geometry remains unchanged and
exhausted. Root strata are overlapping unions, not disjoint partitions.

At code budget499, all optima hide all edits for 1148/4118 train and 100/464
validation resolved-positive pairs. Mean minimum retained edit fractions are
`0.6135911530873144` and `0.6847882693202717`. At8179 every optimum exposes
every edit for all4582 resolved-positive pairs. The remaining244 of4826 pairs
are unresolved:197 local rejections and47 completed threshold rejections.

## Residual limits

- Resolution depends on the outcome and geometry. Saturation at8179 is not
  whole-population information sufficiency; the244 unresolved pairs are not
  silently excluded from the full-universe accounting.
- Changed-token exposure does not locate vulnerability-bearing edits, validate
  labels, establish prompt acceptance, or choose a new scientific token budget.
  The previous class-conditional truncation and contradiction evidence remains.
- Ordered digests bind hidden records but were not independently reconstructed
  by terminal reviewers. Aggregate validation and the root's prospective checker
  are not an independent whole-corpus DP oracle. DP fidelity rests on immutable
  native code and prior independent reference, mutation and synthetic integration
  evidence.
- Resource observations are sampled module-worker-only maxima, excluding Git
  children: working-set1476063232B, private3011993600B. The code lane checked865
  successful samples. These are not guaranteed OS peaks or whole-process-tree
  bounds. CPU1537.796875s is last observed, not guaranteed final CPU time. The
  final unavailable observation is consistent with worker exit, not zero memory.
- The tokenizer length warning is consistent with full untruncated tokenization.
  There was no model forward; it does not establish a model-execution failure.
- This receipt grants no source rights, prompt/family-B freeze, sealer approval,
  training authority, R0.0/ALC-0, learning, cross-model or broad portability PASS.

Raw byte-preserved records live under
`results/alc_r0_full_edit_exposure_development_62b5c7b_v1.*`; checkpoint118 in
`TRAJECTORY.md` records the execution and next open scientific gates. Copies
retain original external paths intentionally. The copied verifier and launcher
are provenance, not portable scripts to rerun automatically on another machine.
