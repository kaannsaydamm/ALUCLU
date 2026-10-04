# ALC-R0 retained author-pair resource census preregistration

Declared on 2026-10-02 before implementation, fixture execution, or any full-data
census. Implementation is an independently reviewable prerequisite. Full-data
execution requires a separate clean-source freeze/review by the coordinating
agent. This declaration does not amend the v2 candidate or P1-P14.

## Population and immutable inputs

Use only pinned original PrimeVul train/validation and author-paired development
bytes, the existing pinned SmolLM2 tokenizer snapshot, frozen UTF-8/whitespace
normalization and token-ID validation, and the unchanged scalable dependency
graph. No held-out files, network, model forward, training, new dependency,
edit-distance computation, prompt equality, changed-token exposure, or semantic
visibility computation is admitted. Validate sources before reading and again
after scanning. The production CLI revalidates model inventory and the exact
clean source checkout before emitting canonical aggregate JSON.

Rebuild the graph and require all four prior ledgers:

- Pair edges: `4ed968d05b79bcb826f5d4e6756df0cac9b4f5a53d392c31e4b3e0291a87fe9a`.
- Component roots: `7a39cd3ce27002838ae3aef73a8caa7902651401b272b76ead3fb636bd239059`.
- Retained train IDs: `4589f0acfcc69edf743733ef7ebb069c987c9b30ccd30c72b5827e0dd5388d61`.
- Retained validation IDs: `0d3db4ae9bba39c231c14129662181feb367f113feaa7b01400580529b297c4c`.

Classify every author pair as both-retained, vulnerable-only-retained,
safe-only-retained, or neither-retained using original endpoint IDs and each
split's retained set. The classes exhaust the verified author-pair denominator.
Select only both original endpoints retained; do not substitute duplicate
representatives. Expected prior populations are 4,344 train and 482 validation
pairs; these are provenance, not resource coverage evidence. Preserve paired
file order, with all train pairs before all validation pairs. Shared endpoints
remain author-pair observations, while component strata use root set unions.

## Fixed prospective cost and admission policy

Encode complete normalized code endpoints with `add_special_tokens=False` and
the unchanged nonempty exact nonnegative integer/BOS/EOS checks. Never truncate
an endpoint to compute cost. For lengths n,m compute `(n+1)*(m+1)` cells. Compute
the existing helper's five-budget packed scratch estimate only when both
endpoints are within its absolute 32,768-token ceiling; otherwise it is null.
The estimate excludes caller-owned inputs, tokenizer/graph memory and process
RSS; it is not a measured runtime/memory bound.

Bind the unchanged ordered common budget grid `512,1024,2048,4096,8192`, derived
template code budgets, longest-label reserve, and SHA-256 commitments to prefix,
suffix, and both ordered label candidate ID sequences. These are provenance
only. No endpoint prompt is constructed and no actual prompt outcomes are
compared. The prospective helper cost uses all five budgets.

Local eligibility is exactly the helper's ordered checks:

1. Maximum endpoint length exceeds 32,768: `endpoint-token-limit`.
2. Cell cost exceeds 4,194,304: `dp-cell-limit`.
3. Estimated packed scratch exceeds 64 MiB: `scratch-byte-limit`.
4. Otherwise locally eligible.

The fixed global prospective cap is **100,000,000 cells**, declared now, before
full-data execution. Simulate admission in pinned train-then-validation order.
Admit a locally eligible pair iff its whole cell cost fits the remaining cap,
including equality. At the first eligible pair that does not fit, exhaust global
admission permanently. Mark that pair and every later locally eligible pair
`total-cell-budget-exhausted`, even if a later pair would fit the remainder.
Locally ineligible pairs keep their local reason regardless of global state.
Do not skip a nonfitting eligible pair to admit a later smaller one. This is a
simulation only: it executes no dynamic program and produces no resolved edit,
zero-distance, changed-token exposure, or outcome ratios.

The pure aggregate fixture API may tighten local ceilings and the total cap;
resource limits/caps must be exact positive integers, never bools, and cannot
relax production limits. Full endpoint lengths in this census must also be exact
positive integers: empty code is rejected. The unchanged mathematical helper's
empty-endpoint fixture support remains separate from this source census. The
development runner accepts synthetic source/pair
expectations and a fixture tokenizer. For pinned original expectations it
requires the fixed limits, cap, grid, and graph hashes. The CLI offers no policy
override, fixture expectation, or alternate graph hash flag.

## Aggregate output and commitments

Separately by split report the exhaustive survival partition, both-retained
universe denominator, locally eligible/admitted/prospectively unresolved counts
and cell sums/maxima, local/global reason counts, and component counts for the
universe, eligible, admitted, unresolved and each unresolved reason. Component
strata can overlap; unresolved is their set union. Also report eligible and
admitted fractions using the complete both-retained denominator. Empty universes
have null fractions, zero counts/sums/maxima, and empty-digest commitments.

Fixed disjoint full-endpoint length bins have inclusive upper boundaries
`512,1024,2048,4096,8192,16384,32768`, plus overflow. Count endpoint appearances
in selected author pairs, not unique endpoint IDs. Fixed disjoint pair-cell bins
have inclusive upper boundaries `16384,65536,262144,1048576,4194304`, plus
overflow. Counts/sums/maxima are permitted; vectors and per-pair output are not.

For each selected pair, increment an ordered internal digest with canonical JSON
records followed by LF containing split, original vulnerable/safe IDs, component
root, full normalized-code token-ID commitments, full endpoint lengths, cells,
scratch estimate, and eligibility/admission/reason classification. Emit only the
digest, never these records, IDs, source code, token IDs, lengths vectors, or
component memberships. Bind exact source and pair expectation roots, verified
source receipt, model inventory, graph ledgers, policy root, and CLI committed
code tree/commit and invocation identity. Set `training_authority=false` and
`held_out_data_present=false` throughout. Any malformed input, inconsistent
shared endpoint/root, changed snapshot, invalid resource policy or source
mutation fails closed before an aggregate receipt is emitted.

An explicit terminal-verification seam may accept a synthetic model snapshot
expectation for fixtures. The CLI calls it with the fixed original snapshot
expectation and its starting clean-checkout evidence; no CLI override exists.
Before work and before output, the CLI also requires its actual resolved module
path to equal the regular file at the recorded checkout's
`src/aluclu/alc_r0/retained_pair_resource_census.py`. This prevents binding an
unrelated clean working directory to execution from another import path.
All author endpoints, including unselected survival categories, must satisfy
frozen normalization before selection. Only both-retained endpoints are encoded
for full token costs.

## Fixture verification and evidence sequence

Write this declaration first, then tests importing the absent module (RED), then
implementation (GREEN). Preserve actual failures and superseded receipts. Tests
cover 2047x2047 exact cell-cap equality and 2048x2048 overflow; endpoint/cell/
scratch precedence; global exhaustion through validation and preservation of
local reasons; all four survival categories; shared endpoints/root union;
empty-universe null fractions; histogram boundaries; ordered commitments and
no raw leakage; source changes during scanning; strict bool/type/negative
validation; and inability to relax production policy. Use no monkeypatch or
implicit global mutation. Run focused tests, Ruff, then serial broad
`pytest tests -k alc_r0`, with bytecode/cache disabled and artifacts outside the
main checkout. Root reviews final code/design before any development census.

This census cannot authorize training or prompt freeze, alter P1-P14, choose a
common budget, establish representative coverage of an admitted subset, or
resolve the family-B information-loss/rights/sealer gates. Poor prospective
coverage requires explicit unresolved reporting or a separately declared exact
scalable method; it never justifies silent endpoint truncation or subset claims.
