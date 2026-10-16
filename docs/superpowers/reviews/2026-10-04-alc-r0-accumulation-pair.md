# Checkpoint144: enforced accumulation-pair phase ordering

Baseline: 8b10df741958c088d502d8b1371c55ef8d981bb3. Scope is the new
cooperating-factory accumulation orchestrator and fourteen tiny harness cases.
This is NOT actual language-model learning or full section D/E acceptance.

## Executable contract

Factory returns two fresh wrappers with independent, identical initial nonzero
factors over ONE existing frozen base. CPU exact mode is mandatory; CUDA mode
uses the existing fixed tolerance contract, without a CUDA execution claim.
The off observation completes first. Factory/state/identity/storage checks and
complete initial-factor comparison precede the on observation. Complete
pre-clip accumulation comparison must succeed before EITHER fixed optimizer
step. Cross-arm gradient/state storage aliases are rejected before steps.
Each fixed step retains existing clip-norm-1 and AdamW configuration validation;
the result comparison includes observations, clipped gradients, factors and
complete optimizer moments/step state.

The factory is a cooperating, separately authenticated boundary, not an
untrusted sandbox. This API does not authorize host loads, training or launch,
qualify the real host callback, authenticate fixtures, or construct the full
parity matrix. Mutable artifacts/live optimizers require exclusive quiescent
ownership. A failed factory that never returns owns cleanup of its unreturned
objects. Captured factor gradients are cleared on failure; partially updated
parameters/moments and arbitrary mutations are NOT rolled back. Record failure
and discard/rebuild both arms; never catch-and-continue.

## Preserved implementation evidence

| Receipt | Actual pytest exit | Tests/failures/errors/skips | Time | XML SHA256 |
| --- | --- | --- | --- | --- |
| red_v1 | 2 | 1/0/1/0 | 112.880s | fd0775924ba5d0f21157841ef379d61964e342b37d1dcd215c6c5b1b462fd16e |
| green_v2 | 0 | 30/0/0/0 | 31.304s | 44e7273f8a913f13bcc00c9a32075df5ca4be13fe45ea3ba07343eaac52a2dec |
| order_red_v3 | 1 | 1/1/0/0 | 13.612s | 7c2da52859e46e26351375067bcd31cc3491c62b9305c7932b0313ce8a4d11fb |
| regression_v4 | 0 | 904/0/0/0 | 32.128s | 5d8c48b01117f756df2ec18f1ebc14f418c8fbe586f7dbc5f916aabe677a2c47 |

Initial RED is missing-module collection evidence only. Original live GREEN
handle41659 returned actual exit0, independently matched to XML counts/hash.
GREEN preceded the extra registration-order reproducer and repair. The latter
showed that unchanged B-before-A registration was falsely treated as drift;
canonical UTF8/non-deduplicated roster ordering repairs this without weakening
the state invariant. Preserve the failing receipt, not just final success.

## Reviewed bytes and acceptance boundary

- New source SHA256: d1e2c4cf1407294ab9967396c01ce02a94f388af6e69f1458d2a8add13bba6b2.
- New tests SHA256: 49f345c63dc98d59acf80f7d4d346babcc6f523a234a257b3e7df90c7f8def68.
- Independent GPT6.1Sol code lane APPROVE, zero severity findings;
  architecture CLEAR for the bounded two-arm pipeline. Both reviewed complete
  files and relevant imported validators without editing or executing tests,
  models or corpus. Factory provenance and nontransactional failure cleanup
  are explicit integration boundaries, not claimed guarantees.
- Root consumed regression handle92041 actual exit0 and parsed904 cases,
  including14 new cases, no failures/errors/skips; reviewed bytes unchanged.
  Ruff and diff checks passed. Synthesis APPROVE PAIR COMPONENT ONLY.

Reproduce by prepending tests/test_alc_r0_accumulation_pair.py to the exact
checkpoint143 28-target command. Retain its two explicit actual GPU/tokenizer
case deselections; this is a 29-target component regression, not the full
repository or portability suite. Fourteen new cases cover shared-base/fresh
factors, phase ordering, invalid factories/initial state, pre-clip failure,
factory cleanup, cross-arm aliasing, comparison modes and registration order.

Actual-host runner/callback qualification, complete D matrix, E resource gates,
scientific R0, interaction-driven durable learning and final secure .alc
remain OPEN. Full unified goal ACTIVE; no acceptance claim inferred from static
review, tiny tensor execution, suite time or stored factor state.
