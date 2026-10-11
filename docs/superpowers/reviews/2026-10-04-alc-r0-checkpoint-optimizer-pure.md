# Pure canonical AdamW adapter — independent review and TDD evidence

Final independent GPT-6.1 Sol code/spec/security lane
`/root/alc_r0_timing_code_gate_61`: APPROVE.
Final independent architecture lane `/root/alc_r0_timing_architecture_gate_61`:
CLEAR. Synthesis: APPROVE only this read-only fixed-AdamW comparison adapter.
Both inspected complete exact-byte source/tests/contract; neither executed tests,
model/optimizer updates, assets/corpus/native code or edits.

Final bindings:

- src/aluclu/alc_r0/checkpoint_optimizer.py:
  6d36db5abe0a57693db894f733e4c2ed384d90e0fb1a434e6b216f8a40f29726
- tests/test_alc_r0_checkpoint_optimizer.py:
  ceee10e977f123c563d68030fc9a8d2ba85ba7c81e714bd542e621095ce9bbfd
- docs/superpowers/plans/2026-10-04-alc-r0-adamw-adapter-contract.md:
  bd62dee04f5d98268cddb726ca7e5000c8b16ef2702db6f8b175dabe4e634c48
- Governing checkpoint detail, section B:
  9eedbade26957c0105841ca5438abb75162db80fcfb4369cc27f810bc0ca4a1e

## Rejected first version and actual repair

First source4d323d5af21a6f1a82213efa82a73dc7e30a023824e8f007b6daf4799b2f722a,
testsbb80baf58e78240c348fbb0e463b1a216b66366b0c3d26e7b9a125b8b85c716a,
contracta83c359184da6553351e5c9d5d3369b8fcd60dfe7a8f65b246660c6cfc98ca3d:
code REQUEST CHANGES, architecture BLOCK. The snapshot validated comparison
storage against only its own base, then compared owned storage sets across arms
without retaining base sets. An otherwise matching factor/moment/step could
alias the opposite arm's frozen-base parameter and pass. Later updates could
modify that supposedly frozen base. This was a real P2 adapter defect despite
the first267-pass regression.

Root added eight symmetric counterexamples BEFORE repair. Actual pytest/shell1:
8 failures,0errors/skips,3.425s, all failures were DID NOT RAISE. The failed XML
is retained as alc_r0_checkpoint_optimizer_alias_red_v3_20261004.xml, SHA256
2b943b86b68fbb5cf8b57bc4aa6a53259f8f3904a4fd2662c2d2d51f0a5ad6ba.

Repair: _Snapshot retains base_storages (source:52,139); final comparison rejects
all comparison-owned storage against both bases' union (:209), while base/base
sharing remains allowed. Eight tests cover factor/exp_avg/exp_avg_sq/step against
the opposite base in both directions (test:314). Shared-base positive remains
(test:309). Both lanes independently confirmed closure in the final hashes.

## Root-observed execution evidence

All fixtures manually populate synthetic states, without optimizer.step or
model loading. XMLs are persisted; stdout/stderr are tool-captured only.

| Run artifact suffix | Actual result | XML SHA256 |
| --- | --- | --- |
| red_v1_20261004.xml | Missing module,1collection error,3.274s; shell1 did not preserve native pytest code | 78e39b9ba51bbf131fbf965d685070212e76c991792d81cac7f7c491969a15a7 |
| red_v2_20261004.xml | Explicit LASTEXITCODE,pytest/shell2,1collection error,3.353s | b7c70ada05343f88c1d65225f8190a269612487452be85e0d9b5769a0e590ac8 |
| green_v1_20261004.xml | pytest/shell0,103passed,0failure/error/skip,5.948s | a13ea3897e1dfd72820e564ccce44005a478a1c7bf132534d79b06697da01231 |
| pure_regression_v2_20261004.xml | pytest/shell0,267passed,0failure/error/skip,4.212s; later review rejected source | a205ec168e5d13ea6c5160c69ffb880da69351fd49143b88b59a77213b9304fd |
| alias_red_v3_20261004.xml | pytest/shell1,8failures,0error/skip,3.425s | 2b943b86b68fbb5cf8b57bc4aa6a53259f8f3904a4fd2662c2d2d51f0a5ad6ba |
| pure_regression_v4_20261004.xml | pytest/shell0,275passed,0failure/error/skip,4.530s; one Ruff formatting issue remained | 3527b4ad4cc196abec3a89e4043238ffb9a842720f071127e3eb530366c99840 |
| pure_regression_v5_20261004.xml | Final formatted bytes,pytest/shell0,275passed,0failure/error/skip,4.058s | 3744ae4716f55b0e9e4798b856078384714a8744ed013183e1179f84ec933525 |

Artifact prefix: results/alc_r0_checkpoint_optimizer_. Root personally parsed
all counts/hashes, confirmed132 adapter cases and all8 alias cases in v5, and
verified the real-tokenizer fixture was absent (explicitly deselected, not skipped).
Ruff format/check passed after formatting; this is not a full-project suite.

Final invocation used the already locked Windows CPython3.12 research venv,
PYTHONPATH=src, PYTHONDONTWRITEBYTECODE=1 and python -B:

```text
-m pytest
 tests/test_alc_r0_checkpoint_optimizer.py
 tests/test_alc_r0_checkpoint_fidelity.py
 tests/test_alc_r0_base_digest.py
 tests/test_alc_r0_capsule_artifact.py
 tests/test_alc_r0_canonical.py
 tests/test_alc_r0_schema_validation.py
 tests/test_alc_r0_banking_scoring.py
 --deselect=tests/test_alc_r0_banking_scoring.py::test_pinned_real_tokenizer_candidate_map_root_when_snapshot_is_present
 -q -p no:cacheprovider
 --junitxml=results/alc_r0_checkpoint_optimizer_pure_regression_v5_20261004.xml
```

## Scope and strongest residual objection

One exact pinned Torch2.14 AdamW group, fixed hyperparameters/flags, canonical
factor/membership/populated-state bijections, explicit scalar step1/2, finite
FP32 moments/nonnegative second moments and independent storage are validated.
Detached clones are compared using existing exact-byte/scale-sensitive criteria.
Every factor and moment is checked; no intersection-only or missing-state pass.
Version/schema drift fails closed, not a broad cross-platform/version claim.

Complete-looking caller bindings cannot prove every real-model factor/base was
included, an optimizer update actually occurred or snapshots were captured at
the correct lifecycle instant. Quiescence is a caller obligation, not a lock;
CPU parity callers MUST request exact=True. Future runner/wrapper reviews must
enforce these; default numerical comparison is never exact CPU parity evidence.

No update, checkpoint execution, host parity/resource fit, prompt adoption,
dataset training, learned capability or ALC-0 gate is established here. Session/
ticket/replay lifecycle, wrapper integration, actual-host invocation and full
qualification remain OPEN. The full ALUCLU objective remains ACTIVE.
