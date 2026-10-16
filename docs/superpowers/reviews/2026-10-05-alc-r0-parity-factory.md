# Checkpoint153: one-base parity cell construction

## Contract

`make_parity_wrapper(host, checkpoint, *, arm, ports, rank, state)` builds fresh
exact capsule/q-only LoRA wrappers over ONE existing externally authenticated
VerifiedHost. All nine port/rank cells are admitted; seed is fixed20260916.
Zero means original seeded A/B0, not the all-factors-zero control. Nonzero B
uses per-B flattened `((i%17)-8)*1e-4` in CPU FP32 before device transfer.
Master factors remain FP32; base is CPU FP32 or CUDA BF16. Independent calls
share base identity, not factor tensors, controllers or callback objects.

Checkpoint off leaves callback absent; on explicitly enables the owned bounded
inventory. There is no loader, base copy, forward/backward or optimizer here.
Invalid typed arguments/base modes/gradients/device/dtype/layout/count/buffer
state/default device are rejected before constructing wrappers, not repaired.
Caller must authenticate host/assets/source and exclusively own quiescent state.
The factory cannot replace invocation review, resource budget or model evidence.

## Independent exact-byte review

| Artifact | Final SHA-256 |
| --- | --- |
| src/aluclu/alc_r0/checkpoint_parity_factory.py | 97462d8bbe861e33d4983ac73b6b62b48d29f322d10866c8373e5ebcdb791340 |
| tests/test_alc_r0_parity_factory.py | 0faf50d395fbdddef27918ebd6d2c2d18227294aaf786f89d858c334ba68da35 |

Initial GPT-6.1 Sol code/spec/security APPROVE; architecture WATCH exposed a
documented partial composition mismatch: keyword-only checkpoint did not admit
accumulation-pair's positional `factory(False)` / `factory(True)` calls. Both-arm
RED reproduced TypeError. Final signature admits positional and keyword flags;
exact partial composition controls preserve independent identical factors,
shared base and on/off callback distinction. Final independent rereviews:
code APPROVE (zero severity findings), architecture CLEAR. Both lanes inspected
full final files/dependencies but executed no tests/models or optimizer work.

## Personally executed/parsed evidence

Locked Windows research CPython3.12.13; PYTHONPATH=src,
PYTHONDONTWRITEBYTECODE=1; python -B -m pytest -q -p no:cacheprovider --tb=short.
Actual pytest exits were printed from LASTEXITCODE. Shell exit alone is not used.

| XML under results/ | Pytest exit | Tests/failures/errors/skips | Seconds | SHA-256 |
| --- | --- | --- | --- | --- |
| alc_r0_parity_factory_red_v1_20261005.xml | 1 | 56/56/0/0 | 47.475 | 1f886894ba43930c1b899e2c87680c2ebaebd476e01cea089274bcd46bfc0503 |
| alc_r0_parity_factory_green_v2_20261005.xml | 0 | 56/0/0/0 | 53.305 | 60165b5aabdf6bd1f53faafee6a6bfcb67732af20c9ac326940279fc96d090ee |
| alc_r0_parity_factory_metadata_red_v3_20261005.xml | 1 | 6/1/0/0 | 31.597 | bff7856d2ca18bec312aea014500a2b46881dbcc7976e384e9df3a36d9c78b99 |
| alc_r0_parity_factory_regression_v4_20261005.xml | 0 | 1181/0/0/0 | 77.418 | 8ce3b15f98688041e759a39946fe67f9e8e4fcfe7da9445f209eb6fb0bd01a50 |
| alc_r0_parity_factory_partial_red_v5_20261005.xml | 1 | 2/2/0/0 | 22.281 | d728aa3b5306042836b5e5bd85ae13990945aa176503c8c4b4008229c1cb643b |
| alc_r0_parity_factory_regression_v6_20261005.xml | 0 | 1183/0/0/0 | 76.541 | 25768f145e63b021cecb02c6729e925e213c41ee3275bd50eba30a6e80a71cde |

First RED reproduced missing factory module; the focused GREEN then passed56
controls. Six added preflight controls exposed malformed model AttributeError;
explicit module rejection repaired it. Intermediate1181-case PASS does not cover
the later signature defect. Partial RED and final expanded regression preserve
that distinction. Root consumed final session8319 and personally parsed1183
cases/64 new cases, verified source/test hashes unchanged; Ruff/diff clean.

The final selection adds factory tests to checkpoint152's37 component targets,
retains only the same two selected non-host matched-LoRA tests and the same two
GPU/real-tokenizer deselections. This is NOT a whole repository/host/GPU suite.

Tests retain exact real wrappers/factors over a two-parameter fake CPU base with
30 identity layers. Only the wrapper constructor's Llama host-class check is
substituted. No actual model/config/snapshot/forward/backward or optimizer is
executed. The tests cover36 grid/arm/state combinations, deterministic identical
but unaliased factors, RNG/base preservation, typed failures and callback setup.
Opening empty leases is lifecycle validation, not model parity or capability.

## Remaining gates

Actual-host execution/source qualification, complete matrix orchestration,
verified tokenizer framing, process ceilings and resource attempt accounting
remain before launch. D loss/full-logits/candidate/full-gradient and accumulation
parity, official-forward regression, E1/E2/E3 resources, scientific R0 freeze,
neural capability, durable generations and final ALC gates remain OPEN. No
training authorization or learned artifact results from construction tests.
Full unified goal remains ACTIVE.
