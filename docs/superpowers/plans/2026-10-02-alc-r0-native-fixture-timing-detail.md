# Fixed native fixture timing detail, declared before timing implementation

This adds operational detail to the unchanged original native fixture design;
it changes no case, budget, ceiling, repetition count or acceptance criterion.
Real mutation evidence cb3385f954aa6792429318fae3a2ddbf5c928690fecddd188bb99c62f24dc53d
is independently APPROVE/CLEAR. Final partitioned regression is still running.
No timing execution until that regression succeeds and the separate timing
implementation receives independent code APPROVE plus architecture CLEAR.

## Files and boundaries

Separate scripts/alc_r0_banded_native_fixture_timing.py and
tests/test_alc_r0_banded_native_fixture_timing.py; no edits to frozen C++, native
adapter, reference, builder, mutation generator or execution files. Data-only
RED/GREEN tests import without builds, DLL loads, timing, corpus or models.
An explicit CLI alone performs approved timing, using the full original reviewed
build-d739a35-v1 receipt and NativeBandedBackend, never a mutant artifact or an
alternative loader. One retained backend in a fresh isolated timing process.

Clean committed timer sources/tree/hash, fixed six-source original receipt and
actual DLL hash are recorded separately. Pin the original design/reference/
adapter and this detail before execution. Full receipt/source/artifact validation
before loading, backend retained through exit, post-run held artifact recheck.
Output must be fresh canonical external non-reparse file; no automatic retries.
CPU/platform/Python/compiler flags and exact serial measurement order recorded.
No dependencies installed, threads, subprocess training, GPU, corpus, held-out,
paid compute, adaptive cases, thresholds, speculative speedup or product claims.

## Unchanged fixed schedule

Use budgets (1,2,3,4,5) for every case:

1. tuple(range(10000)) against itself, K0.
2. tuple(range(10000)) against insertion of unique token10000 at5000, K1.
3. repeated token7 lengths10000 and10001, K1.
4. tuple(range(600)) against itself, K512.

Exactly two warmups followed by five measured repetitions per method/case,
serial fixed case order above. Each case measures in this explicit method order:
Python reference call, rank mapping, buffer marshalling, raw native C ABI call
through ctypes, full public NativeBandedBackend.audit end-to-end. Never exclude
failed samples or substitute another case. Public end-to-end includes all its
per-call validation, artifact verification, geometry, mapping, allocation, ABI
call and output decoding. It excludes one-time loading only; load duration is
reported separately. Load includes actual constructor validation and DLL load,
so it is not claimed as operating-system loader time alone.

## Ownership, correctness and measurement interpretation

Use perf_counter_ns around exactly the named operation. Report every measured
integer-ns sample and mean/median/min/max. No subtraction of inferred overhead;
component durations need not sum to public end-to-end and must not be presented
as an additive profile. Raw native timing includes ctypes call overhead, not
pure C++ compute. Mapping measures rank_tokens only. Marshalling measures private
input/effective-budget/policy/workspace/output allocation from already mapped
tokens and preflight reference geometry; clearly exclude mapping from that phase.
Keep named owners live across every raw call. Exact reference-derived payload,
logical capacity, rounded backing and guard regions are checked for raw samples;
kernel measurement excludes buffer preparation and post-call correctness checks.
Raw timing must use the unchanged export and reviewed limits/headers/ranks.

For each fixture establish the immutable Python reference result and independently
encode all64 ABI words for B5, including signed geometry, metadata, every exposure,
unused/reserved zeros and false authority. This fixture-only pure encoder needs
data-only tests. Compare every warmup/measured raw output to those words, check
transport0 and both guards, and compare every full Python/public native result
to the reference. Check exact resource ceilings before allocating. Failed parity,
guard or infrastructure yields failure, never a timing success or retained sample
speedup. All input/array owners are private and no buffer/callback escapes.

Median public native end-to-end / median Python reference for each fixed case
is the declared comparison; report actual ratio and whether native is faster,
even when it loses. Do not call raw kernel improvement end-to-end improvement.
Do not average four heterogeneous case ratios into a global/corpus speed claim.
Timing supports only these local synthetic fixtures, not native research/kernel
acceptance or learning. training_authority=false and held_out_data_present=false.
