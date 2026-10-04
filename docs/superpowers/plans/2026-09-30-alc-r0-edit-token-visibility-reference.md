# ALC-R0 edit-token visibility reference — fixture-only, non-authorizing

Declared before implementation and fixture execution on 2026-09-30. Starting
commit: `66355527f9321b235084587855c23e3ec909fd30`. The separate live audit
checkout remains frozen. This slice has no source-data runner, acquisition,
tokenizer, model forward, training, held-out access, or prompt-policy change.

## Estimand and exact algorithm

Inputs are two ordered full-code token-ID tuples and one to five strictly
increasing positive **code** budgets. Common sequence budgets are not code
budgets: a later adapter would obtain them from the unchanged defect template.
Positions retained at code budget c are all positions if length <= c; otherwise
the first ceil(c/2) and last floor(c/2), with no gap token. Empty tuples are
allowed solely to test mathematical boundary states; production prompt code
must still be nonempty.

Let S* be all minimum unit insertion/deletion scripts between the complete token
tuples. Replacement costs two operations, accounting separately for each
endpoint token; substitutions and edit hunks have no canonical pairing here.
For every s in S*, V(s) counts retained deleted positions on the first endpoint,
P(s) retained inserted positions on the second, and T(s)=V(s)+P(s). Report exact
min/max of each objective, computing T extrema directly, plus the reachable
signatures {(V(s)>0,P(s)>0)}. Signature index uses first-endpoint bit 2 and
second-endpoint bit 1; a four-bit set stores reachability of indices 0..3.
Marginal maxima do not imply joint existence. Bounds are per budget, not a
single alignment simultaneously attaining all reported extrema.

A packed two-row dynamic program propagates distance, six extrema and a
signature bitset per budget. At each cell consider deletion, insertion, and
zero-cost diagonal only for equal IDs. Keep all transitions tying the least
distance; combine objective minima/maxima independently and union transformed
signature sets. Even equal IDs may have optimal insertion/deletion alternatives.
No prefix/suffix stripping or heuristic traceback is permitted. Boundary rows
are accumulated insertions/deletions. Token identity has distance zero and
zero exposure; ratios are absent from this reference.

## Bounded helper contract

Hard ceilings: 32,768 tokens per endpoint; 4,194,304 grid cells including
boundaries; five budgets; 64 MiB conservative helper-owned scratch estimate.
Frozen per-call limits may only tighten these ceilings, permitting cap fixtures
without monkeypatching. Preflight occurs before DP/mask allocation. The scratch
estimate includes both packed rows, all retention masks, their array headers,
and 64 KiB bookkeeping allowance; caller-owned input tuples and process RSS are
outside that accounting. uint32 storage must have four-byte items on this host.
When a code budget exceeds an endpoint length, construct its all-one mask
directly, avoiding arithmetic that could allocate large temporary integers for
an arbitrarily large positive caller-owned budget. Oversized hard-limit
endpoints have a null scratch estimate because allocation is not attempted.
Exceeded resource limits return an immutable structured unresolved result with
the reason and estimated dimensions, never an approximate or partial metric.
Malformed inputs raise an error. Tokens are exact nonnegative integers, not
Boolean values; budgets must be a tuple of increasing positive integers.

## RED/GREEN validation declared before execution

An independent recursive oracle enumerates all legal edit paths for tiny
tuples, filters terminal paths to minimum distance, and measures consumed
positions directly. It must not reuse the DP recurrence, retention helper, or
signature transformer. Exhaustively compare binary-alphabet lengths 0..4 and
small budgets. Hand fixtures cover hidden/head/mixed changes, insertion and
deletion, repeated-token ambiguity, odd budgets, tail=0, one-sided truncation,
and full retention. The decisive fixture [1,2] versus [2,1] at c=1 has distance
2, marginal intervals [0,1], total interval [1,1], and signatures {01,10}.
Test identity, symmetry, nested-budget monotonicity, invalid inputs, exact cap
boundaries, tightened resource limits, estimate arithmetic and prompt parity
with the existing byte tokenizer. No real snapshot is required. First execute
tests while the implementation module is absent (RED), then implement and run
focused tests, Ruff and relevant ALC-R0 regressions (GREEN).

## Interpretation and later scope

This is changed-token position exposure, not vulnerability localization,
semantic sufficiency, macro-F1, learning, confidence intervals, or a new gate.
Repeated tokens may produce equal retained sequences despite a positive upper
exposure bound. Actual prompt equality is a separate diagnostic. Larger nested
retention masks cannot lower either total bound; this does not choose a budget.

Any later full-development runner needs a separate preregistration and review:
pinned original train/validation bytes and four unchanged graph ledgers;
both-retained author pairs only; fixed common grid 512,1024,2048,4096,8192;
exact reconstruction against unchanged prompt IDs; separate split counts,
unresolved and zero-distance denominators; dependence-component strata;
aggregate-only outputs and canonical ordered internal-record commitments;
source/model/tokenizer/policy provenance and terminal reverification. A proposed
100,000,000 total-cell cap belongs to that future runner, not this helper. No
raw code, IDs, token sequences or alignment paths are emitted by a runner.
The current family-B freeze remains BLOCK; P1–P14, training authority and held-out
access are unchanged. Synthetic optimizer fit remains mechanism/resource evidence.

## Supplementary allocation reproduction

From a checkout containing this helper, run the existing Python 3.12.13 runtime:

```powershell
python -I scripts/alc_r0_edit_visibility_allocation_probe.py src/aluclu/alc_r0/edit_token_visibility_reference.py
```

The script imports only the helper file and Python standard-library modules;
it does not initialize the ALUCLU package or Torch. It constructs caller-owned
inputs before tracing, checks the actual traced peak against the helper's
scratch estimate in the giant-budget and maximum-row-width fixtures, and emits
aggregate JSON. This is supplementary allocation evidence, separate from normal
package integration, whole-process RSS, and maximum-cell runtime. Final normal
package test evidence is recorded in trajectory checkpoint 72.
