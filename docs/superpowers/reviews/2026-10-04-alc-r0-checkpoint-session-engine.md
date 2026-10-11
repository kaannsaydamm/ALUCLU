# Explicit checkpoint session engine — scoped independent review

Final GPT-6.1 Sol code/spec/security lane `/root/alc_r0_timing_code_gate_61`:
APPROVE. Independent architecture lane `/root/alc_r0_timing_architecture_gate_61`:
CLEAR. Synthesis: APPROVE for the reusable cooperating-process engine only.
Reviewers inspected full exact bytes; no execution, edits, models, assets, corpus,
native backend, optimizer updates or training by reviewers.

Final source SHA256:
ba0cbbbb3a1a1109439d7a9220e154620839217130d9e2782c3af50fba886d6a
Final tests:
492ac5aa6c81d9d2db1d8f45b40e411e48606e1edb3ff0be6a3d12629fbaff6b
Session contract:
c28d8382da909df010315e9c1ec9d96b53433210aa212bb7962ba74d3ea2d4ea
Governing checkpoint implementation detail section C:
9eedbade26957c0105841ca5438abb75162db80fcfb4369cc27f810bc0ca4a1e

## Rejections, root counterexamples and repairs

1. Initial missing-module RED precedes implementation. First22-case attempt
   passed21/failed1: the test caught consumed-graph rejection but expected normal
   exit. The EXISTING contract requires lease invalidation, so the fixture was
   strengthened to require invalid exit/gradient clearing. No engine rejection
   was relaxed. Successful-close old-graph rejection is separately tested.
2. Root foreign-thread RED: a rejected raw backward incorrectly cleared pending
   tickets/released the owner lease. Moving thread/active preconditions outside
   hook abort handling preserves the owner's lease. Owner-thread violations
   still invalidate and clear accumulated gradients. Retired graph rejection
   cannot erase a fresh session's gradients.
3. First exact-byte review: code APPROVE, architecture BLOCK, therefore combined
   REQUEST CHANGES. Sourcea7572d8329e5c399d5f6977397c016c758f21da01a982bd29150825ebed0a4f1
   guarded parameters/modules but omitted registered buffers. Root reproduced
   ordinary buffer version change, replacement and unversioned boundary-byte
   drift, plus unrelated output with zero gradient-bearing blocks: all4 RED.
   Capture now includes full registered-buffer roster/stamps; each guard checks
   them and namespace-separated parameter/buffer bytes enter boundary digests.
   Tensor stamps include stride/offset; trainable buffers are rejected. Binding
   output requires at least one actual gradient-bearing block, not vacuous truth.
4. Root base-buffer alias RED: trainable factor storage could alias a frozen-base
   buffer. Base storage separation now includes parameters AND buffers and uses
   device/allocation identity. Static scalar/integer/bool buffers remain allowed.
5. Repaired bytes1179ce626833a469fd52ddaf03aac7f995f1e7df7365bb9ad53e2e3d8c0384b1
   received code APPROVE/architecture CLEAR. Before publication root reproduced
   layer-count shrink bypass with one additional RED. Session now validates/
   captures declared count at entry and guards type/value drift; run bounds and
   output completion use the captured count. Final exact-byte rereview confirmed
   closure: source:122,215,388,427 and tests:547.

Final lifecycle scope includes owner-local one-shot/nonnested lease, <=32 pending
graphs, module/parameter/buffer identity/mode/version/storage guards, private
metadata clones, guarded callable entry initial AND replay, explicit non-reentrant
checkpointing, final-output plus every gradient-bearing layer traversal, ticket
consumption only AFTER successful backward, failure cleanup/release and boundary
byte checks. Output hooks intentionally remain to reject retained old graphs.

## Root execution evidence, not reviewer execution

XML prefix: results/alc_r0_checkpoint_execution_. All11 attempts preserved.
stdout/stderr are tool-captured only; there are no redirected raw log files.
Root personally parsed XML counts/times/hashes and final fixture membership.
All fixtures use tiny CPU fake modules and autograd; no model/tokenizer/task data,
optimizer.step, held-out access, training or resource qualification.

| Suffix | pytest/shell result | XML SHA256 |
| --- | --- | --- |
| red_v1_20261004.xml | 2;1collection error;3.904s | 92e2cd2643399c34f3f4da7b140f54d4b295851174b658ea2f830158f0835544 |
| green_attempt_v2_20261004.xml | 1;21passed/1failed;4.107s | b466bf7a37a6bc3f877457ea2bd6fdd6bea96819273f59d56c1b28c076816578 |
| foreign_red_v3_20261004.xml | 1;1failure;3.681s | 5a2c3a29490c189e8af4243d9007b21911d03b66b96ba2f7d7ad97caa3575eaf |
| green_v4_20261004.xml | 0;25passed;3.243s | 42d0569cccea07a3df24b33d00a7d23a3b6a1aac5314873501410018253d9e7d |
| pure_regression_v5_20261004.xml | 0;320passed;4.280s;later review blocked | 4ae8a1739e532a3bd2e219b786e8bdb70d8e788293d85730e047c808f3c503b8 |
| binding_red_v6_20261004.xml | 1;4failures;3.351s | a8339afcd9de28705dd00fd940c443939030d05940cd570916e460bf890ecf1e |
| pure_regression_v7_20261004.xml | 0;324passed;4.676s | 410d5525ee3c27bbe2036c8e1ed565628ab081c0d5421db008db6b0c0661ff46 |
| buffer_alias_red_v8_20261004.xml | 1;1failure;2.007s | 4868596beebeb1fef157c41604f7699639498919edeb50204d29c7203d99b1be |
| pure_regression_v9_20261004.xml | 0;327passed;4.659s | 451fbcda71abf8d3818f0011c245b79ef14bf2c2cb733222b9db9c114355712a |
| layer_count_red_v10_20261004.xml | 1;1failure;3.320s | 2dcf71a4af990566f91dea310e4ee31ef683669901c0a2f64cd373da63012270 |
| pure_regression_v11_20261004.xml | 0;328passed;6.264s;final bytes | 82ccbf84f5ddd7d327e6c29417bb27bf29b1adbb82cc514fe08b5b43ad831288 |

Final328 result has0failures/errors/skips and53 session cases. The real-tokenizer/
Banking-label fixture is explicitly deselected, not skipped or run. Ruff format/
check passed. This is a relevant pure regression, NOT a full-project suite.
Executed locked research CPython3.12 venv, PYTHONPATH=src,
PYTHONDONTWRITEBYTECODE=1, python -B with:

```text
-m pytest
 tests/test_alc_r0_checkpoint_execution.py
 tests/test_alc_r0_checkpoint_optimizer.py
 tests/test_alc_r0_checkpoint_fidelity.py
 tests/test_alc_r0_base_digest.py
 tests/test_alc_r0_capsule_artifact.py
 tests/test_alc_r0_canonical.py
 tests/test_alc_r0_schema_validation.py
 tests/test_alc_r0_banking_scoring.py
 --deselect=tests/test_alc_r0_banking_scoring.py::test_pinned_real_tokenizer_candidate_map_root_when_snapshot_is_present
 -q -p no:cacheprovider
 --junitxml=results/alc_r0_checkpoint_execution_pure_regression_v11_20261004.xml
```

## Strongest residual objection and next gate

Traversing every DECLARED block cannot establish that the real wrapper declared
the correct graph, supplied complete host state or captured every intended layer/
factor operation. The actual wrappers have NOT been changed in this component.
Single-controller ownership, complete inventory including unregistered tensors/
computational attributes, captured port placement, mutation interception BEFORE
changes, cache/input/batch/dtype guards and actual-host autograd worker behavior
require independent integration inspection and execution qualification.

Unversioned .data drift is boundary-detected, not guaranteed to be intercepted
before every recomputation. Restoring writes/compromised host are explicitly not
covered. These fixtures establish neither CUDA parity nor memory savings. No
optimizer update, model capability acquisition, prompt adoption, dataset training,
ALC-0, learned .alc identity or full-goal completion follows. Wrapper integration,
actual-host parity/resource qualification and real neural gates remain OPEN.
