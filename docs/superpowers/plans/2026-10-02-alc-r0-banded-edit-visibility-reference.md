# ALC-R0 bounded-band edit visibility reference: fixture-only declaration

Declared on 2026-10-02 before new implementation, tests, or fixture execution.
This is a new mathematical reference method, not a change to the existing
rectangular helper or its resource census. No corpus reader, corpus distance or
DP execution, tokenizer/model invocation, native implementation, training,
held-out access, common-budget selection, freeze authority, or trajectory edit
is authorized by this document. Synthetic fixtures alone are in scope.

## Estimand and method boundary

Inputs are two complete ordered token-ID tuples, one to five strictly increasing
positive code budgets, and an explicit nonnegative distance threshold K. Token
IDs are exact nonnegative Python integers, never bools; equality remains integer
equality without byte encoding or integer narrowing. Empty endpoints are valid
mathematical fixtures, not permission for empty production code. Budgets are code
budgets, not common prompt budgets. Full positions are retained exactly as in
the rectangular reference: all positions when length <= budget, otherwise first
ceil(budget/2) and last floor(budget/2), without a gap token.

The graph has unit insertion/deletion edges and zero-cost diagonals only for
equal IDs. Replacement costs two, through insertion plus deletion. No prefix or
suffix is stripped, even when equal; no chosen LCS, greedy snake, farthest-path
traceback, substitution edge, heuristic band, or adaptive threshold is used.

For all globally shortest paths S*, each budget reports independent min/max of
retained deletions V, retained insertions P, and direct total T=V+P. Total bounds
must be propagated directly, never inferred by adding marginal bounds. Joint
reachability is a four-bit set of signatures (V>0,P>0), with first flag 2 and
second flag 1. Different extrema need not be attained by the same path; there
is no claim of a joint alignment across different budgets.

Reuse the immutable BudgetExposure type from edit_token_visibility_reference.
Introduce a separate BandedEditVisibilityLimits and BandedEditVisibilityResult
in a new banded_edit_token_visibility_reference module. Do not modify the existing
EditVisibilityLimits, EditVisibilityResult, constants, estimator, or helper.

## Threshold band and exactness proof

Write n=len(first), m=len(second), delta=n-m, and k=i-j. A complete path through
(i,j) requires at least |k| indels before it and |delta-k| afterward. Therefore
every path of cost <=K lies in the region |k|+|delta-k|<=K. If K<|delta| there is
no feasible band and the method returns threshold-unresolved without DP.

Otherwise define L=ceil((delta-K)/2) and U=floor((delta+K)/2). The safe band is
L<=i-j<=U, clipped to 0<=i<=n and 0<=j<=m. Implement ceiling/floor with exact
integer arithmetic, including negative numerators. Do not force K to have the
same parity as delta. The number of un-clipped diagonals is K+1 when K and delta
have equal parity, and K when they have different parity. A mismatched parity
threshold still includes every feasible path: actual indel path costs have the
parity of delta. For K=0 and delta=0 the band is the main diagonal.

For row i, j_low=max(0,i-U) and j_high=min(m,i-L); an empty interval has width
zero. Before allocation compute the exact scheduled cell count
C=sum(max(0,j_high-j_low+1) for i in 0..n), including origin and boundaries, and
exact maximum active row width W=max(row widths). Preflight may iterate these
at most 32,769 rows but stores no row-width vector. C is the scheduled visited
DP cell count, not rectangular (n+1)*(m+1). No distance-based cell pruning is
permitted in this reference, so a completed DP visits exactly C cells.

Compute a primary-distance DP and weighted states on this entire band. At each
reachable cell retain every legal predecessor tying the minimum distance,
including insertion/deletion ties when the token IDs are equal. Each objective
has independent minimum and maximum addition/merge; each joint signature is
transformed by the consumed-position exposure flag, then unioned across tied
predecessors. This is the same mathematical recurrence as the full reference.

If terminal band distance d<=K, the answer is exact: every global path of cost
<=K lies inside the band, and this computed path proves the global optimum D is
<=K. Thus d=D and all globally optimal alternatives were included. Each prefix
of a globally shortest path is shortest to its vertex; otherwise replacing it
would improve the complete path. Keeping all primary-optimal predecessors and
merging states inductively therefore preserves all terminal extrema/signatures.
No backward distance pass or enumeration of paths is required.

If the terminal is unreachable or d>K, the only conclusion is D>K. Emit no
distance, partial bounds or signature set. The method must never call the full
rectangular helper as an automatic fallback or retry with a larger K.

The region derivation and all-alternatives proof above are this declaration's
own argument. Myers's original shortest-indel paper establishes the edit-graph
and scalar-distance context; its farthest-reaching greedy representation does
not establish weighted exposure preservation. Allison-Dix gives a bit-parallel
LCS alternative, not this all-path aggregate. Neither algorithm is executed or
introduced as a backend in this slice.

- Myers, An O(ND) Difference Algorithm and Its Variations, original paper:
  https://neil.fraser.name/writing/diff/myers.pdf
- Allison-Dix, A Bit-String Longest-Common-Subsequence Algorithm, author copy:
  https://www.cantab.net/users/mmlist/ll/Publications/1986IPL/

## Independent resource policy and result contract

New hard ceilings are endpoint tokens 32,768, budgets 5, threshold K 512,
scheduled band cells 4,194,304, and conservative helper-owned scratch 64 MiB.
The numeric band-cell ceiling matches the old numeric ceiling but counts a
different operation region: it does not relax or amend the old rectangular
policy. K<=512 bounds the un-clipped row width by 513; the cell cap separately
prevents a maximum-length, maximum-width workload from being accepted. This
conservative fixture ceiling is not a corpus coverage prediction. No global
100M cap belongs to this per-call helper.

Limits may only tighten these new hard ceilings. Endpoint/cell/scratch limits
are exact positive integers; max_distance_threshold is an exact integer in
0..512, allowing identity-only fixtures. K is an exact integer in
0..limits.max_distance_threshold. Invalid types, negative K, K exceeding the
declared limit, bools, zero positive-only limits, or relaxed ceilings raise a
method-specific ValueError subclass before allocation. Code-budget validation
matches the full helper, including arbitrarily large positive Python integers.

After all input/policy validation, reason precedence is:

1. endpoint-token-limit if an endpoint exceeds its declared ceiling;
2. distance-threshold-exceeded if |n-m|>K (no DP);
3. band-cell-limit if exact C exceeds its declared ceiling;
4. scratch-byte-limit if the packed estimate exceeds its declared ceiling;
5. otherwise run the bounded DP; terminal d>K/unreachable yields
   distance-threshold-exceeded after a complete C-cell run.

Do not classify cell/scratch rejections as distance-threshold failures. Resource
or threshold-unresolved results preserve caller dimensions but contain no exact
distance and budgets=(). All results set training_authority=false and
held_out_data_present=false. No ratios, prompt outcomes, scientific gate verdict
or semantic-localization interpretation is returned.

The separate immutable result records status, reason, first_tokens,
second_tokens, requested_code_budgets, distance_threshold, band_lower_diagonal,
band_upper_diagonal, scheduled_band_cells, visited_band_cells, max_row_width,
estimated_scratch_bytes, allocated_packed_payload_bytes, edit_distance, budgets,
limits, and the two false authority flags. Use status exact-non-authorizing or
resource-unresolved-non-authorizing (threshold is a bounded-method unresolved
reason, not an approximation). allocated_packed_payload_bytes is the exact
payload size of the prescribed buffers, excluding headers, not measured RSS.
It is zero when no buffers are allocated. visited_band_cells is zero for any
preflight rejection and exactly C for completed DP, including terminal-threshold
failure. Endpoint rejection uses null band geometry/C/W/estimate because the
bounded preflight is not attempted. Empty infeasible band (K<|delta|) uses null
lower/upper diagonal bounds, C=W=0 and null scratch estimate; accepted
empty-empty inputs visit the origin, with D=0 and
zero exposure. Cell/scratch rejection reports computed C,W and the estimate.

## Packed rows, scratch and boundary handling

Allocate two sets of 1+7B uint32 arrays, each of exactly W entries, and 2B byte
retention arrays with total payload B*(n+m). Require array('I').itemsize==4 and
array('B').itemsize==1. For S=1+7B the exact packed payload is
2*S*4*W+B*(n+m). The conservative scratch estimate adds 2*S uint32 array
headers, 2B byte-array headers, and the unchanged 65,536-byte bookkeeping
allowance, using empty-array getsizeof probes. Do not allocate DP/mask buffers
before preflight. Fixed multiplication, not generator append, creates buffers.
No extra full matrix, predecessor/row vector, traceback, per-cell heap object
history, or retained path list is permitted. Transient containers must remain
bounded by three predecessors, five budgets and the fixed state count.

The estimate bounds prescribed packed storage and bounded bookkeeping; it
excludes caller-owned token tuples/budgets and process RSS. Allocation evidence
must check the actual helper-owned traced peak against the estimate before this
reference can be called validated. Empty tuples, platform headers, temporary
allocation overlap, result construction and giant-budget handling are part of
that check. Do not claim a measured runtime or whole-process memory bound.

Row buffers have explicit global-column bases and valid intervals. Out-of-band
predecessors are unreachable; never read stale values merely because their
packed index exists. Before writing each cell, initialize distance/minima to
INF=n+m+1, maxima to zero and signatures to zero. Only the origin has distance
zero and initial signature bit 1. Reachable boundary cells accumulate actual
insertions/deletions. Skip transitions from INF and guard additions so INF
cannot masquerade as a valid distance. n+m<=65,536 under the hard endpoint
ceiling, so distance, counts and INF safely fit uint32. Comparison uses original
integer IDs without narrowing them. A budget >= endpoint length uses an all-one
mask before any head/tail arithmetic, avoiding giant-budget temporary integers.

## RED, oracle, GREEN and review sequence

Preserve this declaration first. Next write tests importing the absent new
module and record RED. Implement only the fixture helper afterward, then run
focused GREEN, Ruff, relevant ALC-R0 regression checks and independent source
review. No raw datasets, real tokenizer/model snapshot or corpus reader is
needed. Keep execution artifacts outside this main checkout. Actual commands,
exit status and final source hashes are evidence; this document is no PASS.

The existing independent recursive path oracle enumerates all legal paths,
selects terminal minima and measures original consumed positions. It does not
reuse DP recurrence, retention or signature helpers. For binary tuples of
lengths 0..4 and all five small budgets, compare every field against that oracle
and the unchanged rectangular reference for thresholds spanning 0..n+m+1.
When D<=K require exact equality; otherwise require unresolved with no partial
metrics. Include small ternary fixtures and all K/delta parity combinations,
negative delta, K<|delta|, K=0, empty endpoints and D=K exact equality.

Hand fixtures include crossed [1,2]/[2,1] at budget one (D=2, marginal [0,1],
direct total [1,1], signatures 01 and 10, never 11); repeated equal-token
ambiguity; equal prefixes/suffixes whose stripping loses exposure alternatives;
optimal ties skipping equal IDs; one-sided truncation; odd budgets and zero-tail;
endpoint swap with explicit signature remapping; nested-budget monotonicity;
all-retained counts; invalid tuples/IDs/types/limits and giant positive budgets.

Validate exact C and W with an independently enumerated geometric region on
small dimensions. Test cell-cap exact fit and one-over with tightened limits;
scratch estimate exact fit and one-under ceiling; endpoint hard boundary and
overflow; K=512 and invalid 513; no allocation on preflight rejections; and
visited=C for completed threshold failures. Distinguish scratch estimate from
exact packed payload and measure the declared allocation bound.

Include long corpus-free deterministic fixtures that the old rectangular cell
limit rejects but the new band admits: identical uniquely positioned tokens at
K=0, a single known insertion/deletion at K=1, and repeated-token insertion
ambiguity with analytically known exposure signatures. Sizes and expectations
are fixed here before execution: identical tuples range(10000), K=0, have
C=10001, W=1, D=0 and zero exposures (rectangular cells=100020001). Inserting
the unique token 10000 at position 5000 into that tuple gives m=10001, K=1,
C=20002, W=2 and D=1; budgets 1..5 expose neither endpoint (signature set {00}).
For first=(7,)*10000 and second=(7,)*10001 at K=1 and budget one, D=1,
V=[0,0], P=T=[0,1], and signatures are {00,01}, bitset 0b0011: the inserted
position can be retained or hidden. The deletion/swap counterparts must remap
signatures explicitly. All remain below the new endpoint/C/scratch ceilings.
Compare smaller analogues with the oracle/full reference; do not call
the old helper beyond its own limits or infer long expectations from the new
implementation.

Mutation checks must kill dropped equal-ID indel ties, one-selected-predecessor
traceback, prefix/suffix stripping, direct totals built from marginal arithmetic,
joint bits inferred from marginal maxima, parity-rounded inward bands, excluded
band boundaries, stale row access and acceptance of d>K. Keep mutations local
to isolated fixture checks, never committed scientific policy changes.

Any later native method, larger ceiling, adaptive K, full-development runner,
distance/resource census or risk acceptance requires a separate declaration and
review. This reference provides exact changed-token-position exposure when
resolved; it provides no vulnerability-bearing-edit localization, prompt
sufficiency, representative corpus coverage, learning PASS or training authority.
