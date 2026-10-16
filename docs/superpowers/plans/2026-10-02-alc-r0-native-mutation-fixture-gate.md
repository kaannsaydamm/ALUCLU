# Closed native semantic mutation fixture gate

Implementation detail for the already declared nine native semantic checks;
does not revise the original fixture policy or authorize corpus/model work.
Baseline kernel commit d739a35dc7d184c77fec893a22c972fb5d40cf34, C++ SHA-256
c577846b7f5de113230b89224d96a707eceecaf7659cad2b316d2138201f96ad.
Reference dff2a30af16daa97dd0acd1ab39fe89403b35b6a4b181c95f7bf5db21f707f8d.
Original plan 0cac0b1ac5f70bc7a3167a43d232672d90aed5eec168d0bd1fd150380fa3e3f3.
Independent GPT-6.1 Sol architecture design supplied before implementation.

## Frozen schedule and substitutions

Build ten independent locally authored variants: unchanged control and exactly
nine IDs. Replace one checked anchor per mutant from immutable baseline bytes,
never cumulatively. Record old/new bytes and generated hash. Budget1 throughout.

- drop-equal-indel-ties: ignore optimal indel predecessors when both current
  endpoint tokens equal. Witness (7,), (7,7), K1.
- single-predecessor: preserve candidate order, retain only first optimal
  predecessor. Witness (1,2), (2,1), K2.
- strip-equal-ends: trim equal prefix/suffix through local pointers/counts before
  geometry/masks. Original caller metadata must remain independently available.
  Witness (7,), (7,7), K1.
- marginal-total: publish sums of endpoint marginal minima/maxima instead of
  independently propagated direct totals. Witness (1,2), (2,1), K2.
- marginal-joint: publish single signature inferred from endpoint maxima instead
  of union. Same crossed witness, K2.
- inward-parity: increment lower/decrement upper when K-delta is odd before
  geometry enumeration. Witness (1,), (1,), K1, then fixed grid if necessary.
- exclude-boundary: keep enumeration/initialization/visited bookkeeping; skip
  recurrence at j==high. Witness (1,), (1,), K0. Do not disable invariants.
- stale-column: deletion predecessor uses j-low instead of j-prev_low while
  preserving range guards and other predecessors. Fixed grid witness schedule.
- accept-over-threshold: disable terminal distance>K rejection. Witness
  (1,), (2,), K0.

Fixed grid: binary sequences lengths0..3, first/second lexicographic product,
thresholds range(n+m+2), matching immutable Python mutation probe. No adaptive
search outside grid. Control covers every scheduled witness and whole grid,
with immutable Python reference and independent recursive path oracle.

## Build, isolation and interpretation

Separate test-only closed harness; do not change production loader, source
allowlist, decoder, thresholds or resource limits to admit mutant binaries.
Verify baseline/plan/reference/probe and original positive receipt before build.
Fresh external directory per variant; reviewed explicit compiler flags,
CL/_CL_ cleared, exact-byte snapshot/include locks, source-bound build ID,
compiler/linker before/after identities and command/log/exit/dependency hashes.
No installation, paid compute, corpus, model, tokenizer, training or held-out.

Child process per artifact selects only closed IDs from verified manifest, not
arbitrary DLL paths. Require canonical external paths, exact DLL/source/include
hashes, held deny-write/delete handle, restricted DLL-directory/System32 loading,
module identity, ABI and actual source-bound identifier before C ABI calls.
Private owned buffers remain live throughout calls. Report all64 raw words,
transport, geometry/allocation metadata and guard canaries. No decoder rejection
alone can stand in for a mathematical mismatch.

Semantic kill requires normal child exit, transport0, intact canaries, and a
completed mathematical/metadata disagreement with independent expectations.
Compile-failed, child-crashed, transport-rejected, invariant-detected,
canary-failed and survived are separate statuses, never semantic kills.
Inward-parity/stale-column may hit invariants first: preserve that observation
and use only frozen grid for a completed counterexample. If none exists, leave
that semantic requirement unresolved; never disable invariants or relax oracle.
Final report includes all nine IDs, exact witnesses/field differences, control
coverage and counts by category. False training_authority/held_out flags.

Review harness before compiling/executing it. Native acceptance remains open
until these requirements and remaining edges/broad regression clear. Timing
retains original four fixtures/warmup2/measured5, only after correctness gates.
