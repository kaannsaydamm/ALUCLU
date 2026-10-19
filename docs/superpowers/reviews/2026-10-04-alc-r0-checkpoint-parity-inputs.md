# Checkpoint140: token fixtures for prospective actual-host parity

Baseline db089ab1ec3c099d2e6174215990691ee70bab34; clean authoritative Desktop
checkout verified, full unified objective and prospective section D reread.
Previous goal turn PROGRESS. Inspection established that D's real-host parity
runner is absent and wrapper controller has no computational inventory callback
by default. Existing component suites are not substitutes for either gate.

## Implemented portion of D

Added token-only fixture construction without Torch/tokenizer/model imports.
The eventual runner must independently verify the pinned tokenizer and actual
prefix/suffix/leading-space candidate encodings BEFORE using this helper.
Syntactic validation alone cannot establish that in-range IDs encode that text.

Fixed common budgets32/64, strict immutable nonempty tuples bounded64, exact
integer IDs in vocabulary49152 and explicit EOS schema. Reject EOS in supplied
framing/candidates and identical candidate tuples. Reserve the longest complete
candidate to give both labels the SAME prompt/code. Synthetic code IDs exactly
(index+1)%49151+1. If framing/reserve leaves no code token, fail rather than
truncate labels, change framing, grow a budget or silently drop the cell.
Shorter candidate gives a shorter total sequence within the common budget;
there is no label-dependent extra code context or implicit filler.

Every candidate token is supervised, every prompt token ignored. Labels are
unshifted; the future host's standard loss shift owns next-token alignment.
Optional right padding is allowed only for64 and adds exactly7 EOS input IDs,
zero attention and ignored targets. Positions are contiguous0..n-1. Output is
a frozen dataclass of immutable tuples. No optimizer, factors, gradient state,
tokenizer or language model is touched by this construction.

Tests cover both labels and lengths, exact code/prompt/input/label/mask/position
arrays, longest-candidate reserve, masked padding,16 malformed/infeasible cases
and immutability. They are fixture checks, not actual-host parity evidence.

## Executed evidence

Existing research Python, PYTHONPATH=src, PYTHONDONTWRITEBYTECODE=1,
Python-B -m pytest-q -p no:cacheprovider --tb=short, new JUnit paths.

| Attempt | Actual pytest exit | Tests/failures/errors/skipped | Time | XML SHA256 |
|---|---|---|---|---|
| red_v1 | 2 | 1/0/1/0 | 18.810s | 9627986291be0b247d1b534889ba6200015f564b3298d70a08995ce5aafde995 |
| green_v2 | 0 | 23/0/0/0 | 17.490s | 6f6528e65af33da1fcbe8b973cb3b124ee78c53c2d9d0ba0758d0791cb21e317 |
| full_pure_v3 | 0 | 831/0/0/0 | 90.981s | b667250716560b0ff43f6b27aa00adfcdee6b4b2cf602191ca924dca51212432 |

RED is a missing-new-module collection error, NOT numerical parity failure.
Root witnessed actual exits and independently parsed JUnit counts/hashes.
Full pure v3 later terminated with directly observed actual exit0. Root parsed
all JUnit counts,23 new cases and exact XML hash; source/test bytes unchanged.
An earlier read while the process was live found no XML and was not treated as
test failure, completion or grounds to restart. Ruff/diff checks passed. Suite
duration is not inference-latency or resource-fit evidence.

## Reproduction and independent review

Use139's exact24-target pure regression command and prepend
tests/test_alc_r0_checkpoint_parity_inputs.py. Total25 explicit targets,
preserve both asset-case deselections and research environment from134;
always use a new evidence filename. Not a full repo/model/GPU suite.

- Source SHA256:e2d277ca31c99f746d0de638926f4e6419084e42678e0a2be9f42b8aa36f2084.
- Tests SHA256:81a1690762cbdcc25124535abe561a3e1bc84c92b0e84c96340dc72b4433c202.
- Independent GPT6.1Sol code APPROVE, architecture CLEAR for these exact bytes.
  Reviewers read the full new files and prospective section D; no edits, imports,
  test/model/corpus invocation. They did not infer pending final regression.
- Final regression subsequently verified on unchanged reviewed bytes.
- Synthesis APPROVE TOKEN-FIXTURE CONSTRUCTION ONLY.

## Remaining real-host gates

This helper neither authenticates a tokenizer nor binds an actual host callback,
creates a parity runner, verifies parameter/gradient/AdamW equality, measures
GPU/CPU resource fit or authorizes model/dataset training. Section D's complete
9cell/2arm CPU/GPU matrix, both factor states, repeated/two-pending/accumulation
fixtures and separately reviewed launch remain OPEN. E resource matrix and
scientific proof remain OPEN. No actual-host parity, learning or ALC-0 PASS.
