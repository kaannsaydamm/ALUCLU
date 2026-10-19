# Checkpoint128: full opt-in wrapper orchestration

Baseline `29883c70b5fa1a534061cd8bcab92c383f206e74`. Authoritative checkout:
`C:\Users\kaann\Desktop\03_Projeler_Arge\ALUCLU\.worktrees\unified-lifelong-cognition-local`.

The default forward is unchanged when no session is supplied. Explicit
`checkpoint_session=session` requires the active owning thread/controller,
cache explicitly False, no past/cache/embeddings, batch-one valid int64 IDs,
binary matching masks, matching nonnegative int64 positions, valid labels and
full logits. Missing computational-state callback is rejected; **any callback
being present is NOT proof of complete host coverage**. The real constructor
still leaves the callback absent pending host-specific inventory integration.

An owned ticket clones caller inputs/mask/positions/labels. Its internal metadata
extension clones derived causal mask and rotary cos/sin before the first block,
rejecting replacement, trainable values and late extensions. All captured actual
layers run through the ticket, final logits are bound to traversal accounting,
then optional loss is computed using private labels. Owned failures abort and
clear gradients; foreign precondition rejection preserves the other owner's lease.

## Parent-observed execution evidence

Files under `results/`, prefix `alc_r0_checkpoint_forward_`:

| Artifact | Exit | Tests | Failure/error/skip | Seconds | SHA256 |
|---|---:|---:|---|---:|---|
| red_v1_20261004.xml | 1 | 28 | 28/0/0 | 7.396 | 0457c9e5a78216140ab587761be8279aee6ec65112dee40dd8d4726771d3c65a |
| green_v2_20261004.xml | 0 | 28 | 0/0/0 | 6.829 | eb6ead2be370531ab0bace81fc862c1f8a7b448e956eeeb66943850b1ad9f906 |
| regression_v3_20261004.xml | 0 | 517 | 0/0/0 | 9.658 | 913a6e2ee553faf242391875ddc66b7dd89489c070fb06d4fff801a8077c0e63 |

RED is missing explicit keyword/path. Initial Ruff style findings were corrected
by formatting; final Ruff check succeeds. Parent observed actual pytest/shell exit
and parsed XML counts/hash. No artifact overwritten. Logs are tool-captured, not
separate persisted stdout/stderr. Fake LM facade uses CPU tensors and config only;
no VerifiedHost, model assets, corpus, optimizer step or training run.

The fake fixture's constant callback is explicitly NOT a real-host certificate.
Tests cover exact default/checkpoint loss/logits/factor gradients, one/two pending
graphs, input/mask/positions/labels caller mutation isolation, no base gradients,
invalid inputs/cache/inventory, foreign owner preservation, omitted backward,
derived metadata lifecycle and no-label owned logits backward.

Reproduce checkpoint127's documented 485-case command with the additional
`tests/test_alc_r0_checkpoint_forward.py` and a new unique JUnit path. Retain both
asset-dependent explicit deselections. Environment: pinned local research Python,
`PYTHONPATH=src`, `PYTHONDONTWRITEBYTECODE=1`, Python `-B`, pytest
`-q -p no:cacheprovider --tb=short`. These are pure/fake fixtures, not actual-host
numerical parity, resource fit or scientific capability acceptance.

## Independent review and OPEN gates

Candidate hashes:

- host_wrapper.py: 6b15039c8b0f870b032f432b9d13a494b121d58fdb61d60ec9101ab2aadd8adc
- checkpoint_execution.py: 8f2fb6363e146612cee78bb618c7beef249d84a936e9b457debdd141efbb8be5
- test_alc_r0_checkpoint_forward.py: 330483e48d35147a18454ae99a256fdec072660e27cbd57e8596de0cf628061d

First independent code lane failed due provider quota, with no review verdict.
Same lane retry returned APPROVE; independent architecture returned CLEAR. Both
verified the three exact hashes and inspected without runtime execution. Synthesis:
APPROVE ORCHESTRATION ONLY. Both explicitly deny interpreting callback presence
or fake parity as proof of real host inventory or launch readiness. Parent parsed
32 forward cases and zero excluded asset cases in the final517-case artifact.
Full actual-host global/class/property/external state audit, callback attachment,
actual model parity/resource invocation and all scientific/learning gates OPEN.
