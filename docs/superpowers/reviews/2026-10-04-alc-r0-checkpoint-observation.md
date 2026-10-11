# Checkpoint141: prospective parity observation core

Baseline d37bc1da3b8f93e1844e2337eed9a85eff0a81f3. Authoritative Desktop
worktree verified and full unified objective reread. Previous interactive
answer was status-only, classified NO PROGRESS; implementation resumed from
the existing uncommitted observation core and four proper RED cases.

## Implemented scope

Single cooperating-wrapper forward/backward observation, checkpoint off/on:
complete scalar loss, full logits, complete candidate score, every individual
A/B factor gradient, frozen base including buffers and unchanged factor values.
Strict input tuple supervision/mask/positions checks precede execution. Live
base/factor bindings, named rosters, tensor metadata and input values must remain
unchanged. Metadata stamps include identity, version, shape, dtype, device,
requires_grad, storage identity, stride and offset. Byte digests remain required.
Factors are finite trainable FP32; zero-B requires exactly zero A gradients and
nonzero B gradients; nonzero state requires every factor gradient nonzero.
Capture detached cloned CPU tensors. Pair comparison requires matching metadata,
full loss/logits/candidate score and complete unique named gradient sets.

Tiny harness tests include off/on positive state/padding cells, value mismatches,
backward failure, replaced base/factors/mode, replaced parameters, base buffer
mutation, changed inputs, nonfinite gradients, aliased factor names, malformed
fixtures and identical-byte parameter/buffer metadata changes. Harness base
weights are not used in its forward: these are component controls, NOT actual
language-model parity or neural acquisition evidence.

## Executed evidence

Research Python3.12, PYTHONPATH=src, PYTHONDONTWRITEBYTECODE=1,
Python-B -m pytest-q -p no:cacheprovider --tb=short, unique JUnit filenames.

| Attempt | Actual pytest exit | Tests/failures/errors/skipped | Time | XML SHA256 |
|---|---|---|---|---|
| red_v1 | 2 | 1/0/1/0 | 1.127s | f360efee046f41f9acd1ca7d9abe56b40356637c9aca23edca4049de8a47912e |
| red_v2 | 2 | 1/0/1/0 | 21.404s | 93a2640df9e1ed2517f8490a85c5f3170a7fbb16bc0cc0ae1a2f079cb43d39f4 |
| green_v3 | 0 | 9/0/0/0 | 90.099s | da1c026c5b7f959c0354992a9f458b0fcde57e9e91274c82096c58ece95055ec |
| binding_red_v4 | 1 | 13/4/0/0 | 41.200s | d2a17bbb04934092fa53b5cbe846d71f740129d08a823a69f3afd785dd4f9d63 |
| green_v5 | 0 | 13/0/0/0 | 39.859s | 947266f3c62e6636ce59f870a7711118c93ec2baf62213d5f4f8c8c547066ec9 |
| regression_v6 | 0 | 854/0/0/0 | 89.992s | 0c563e469a93b62e376930862cf6a2ee61d5803be165d0570834245ccbf7d864 |
| metadata_red_v7 | 1 | 1/1/0/0 | 37.354s | d73f2bc626bf82d45315bfa2d6653e24223a3ea826231f4aa64ccbbed2d3d278 |
| regression_v8 | 0 | 856/0/0/0 | 66.996s | e9c7ec407ab2eefbc703a0160648f01578352131f9b34bfca87a6e7d6a866408 |

v1 was a test syntax typo, v2 missing-new-module collection error; neither is
numeric evidence. v4 exposed three live binding/mode omissions and duplicate
gradient name collapse. v7 independently reproduced code review's shape-drift
finding: id/raw-byte checks alone passed a changed frozen base. All retained,
including intermediate successful runs. No threshold or data changes.

Final regression directly observed actual exit0; root independently parsed
856 cases including25 new cases and unchanged final source/test hashes.
Ruff and diff checks passed. Reproduce by prepending
tests/test_alc_r0_checkpoint_observation.py to checkpoint140's exact25-target
regression command, retaining both asset/GPU case deselections. This is26
explicit component targets, NOT a full repository/model/GPU suite. New module
has25 cases. Always write a new result filename. Pytest wall times are NOT
inference latency or resource-fit evidence.

## Independent review and remaining boundaries

Initial independent GPT6.1Sol code REQUEST CHANGES for metadata drift;
architecture WATCH for mutable artifacts and failure-not-rollback. Implemented
metadata fix with proper RED and explicitly documented caller obligations.
Final source SHA256:4436ba47987dd87190c80a9347157883733ecc587b9dadfc7a6cab10857690ed.
Final tests SHA256:63e1484e7a8981ac8868e25651ef2f7af5b9f40333905fd6ebe512fd455b5c45.
Final independent code lane APPROVE, architecture CLEAR for those exact bytes.
Both reread full files; no edits/imports/test/model/corpus invocation, and no
inference of pending regression. Root subsequently verified final terminal run.
Synthesis: APPROVE SINGLE OBSERVATION/COMPARISON COMPONENT ONLY.

Caller must exclusively own observations until comparison/receipt generation.
Frozen dataclass does not make tensor contents immutable or authenticated.
Failures clear original factor gradients but do not rollback arbitrary state
or replaced live factors: record terminal failure and discard/rebuild the
affected wrapper before another arm. Catch-and-continue is NOT supported.

Matching cooperating observations is not correctness/provenance of arbitrary
loss callbacks. This core cannot authenticate host/tokenizer/callback or confer
launch authority. Complete section-D nine-cell/two-arm CPU/GPU matrix,
cross-label ordering, repeated states, pending forwards,16-microbatch accumulation
and AdamW step remain OPEN, as do official-forward host controls and E resource
qualification. No host assets, tokenizer, task corpus, held-out data, optimizer
or GPU execution this turn. Neural acquisition, learning persistence and .alc
product gates remain OPEN; full unified goal ACTIVE.
