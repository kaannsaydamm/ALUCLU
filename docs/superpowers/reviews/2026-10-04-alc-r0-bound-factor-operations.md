# Captured factor operations — CPU binding evidence

Baseline: c3e185f8369abe39fa43888ef6105a21d6030461. Checkpoint 124.

Implements one prerequisite of checkpoint detail section C, not full wrapper
integration. `ResearchCapsuleV0.bind_port(port)` captures actual A/B tensor
references. `MatchedQProjLoRA.bind_q_projection(port, attention)` captures actual
A/B tensor references and the current q_proj module. Existing live APIs delegate
to these operations without changing factor math, initialization, ports or ranks.

Captures are references, not copies or immutable snapshots. Replacing a factor
module, its parameters or attention.q_proj must not redirect an already captured
operation. In-place changes to captured tensors remain visible. A later wrapper
must bind these operations inside checkpointed blocks and enforce the complete
session identity/version/boundary guards. The session guard should reject mutation,
not silently accept continuation merely because a captured operation still works.

Capturing q_proj does not capture immutable q_proj parameter state. Registered
module/parameter/buffer guards and the host's unregistered computational inventory
remain integration obligations. No host-forward/cache loop changed in this stage.

## Root-verified evidence

Locked Windows research Python 3.12 environment, CPU synthetic tensors only.
No real host/tokenizer assets, corpus, optimizer steps or training authorization.
Stdout/stderr are tool-captured, not separate persisted log artifacts.

| Artifact in results/ | Actual exit | Counts | SHA-256 |
| --- | --- | --- | --- |
| alc_r0_bound_factor_red_v1_20261004.xml | 1 | 21 failures, 0 errors/skips, 32.125s | 863e8a37b78bd23579532eee1e8580fa258a320fcdd8c7183528fb2bee49df3a |
| alc_r0_bound_factor_green_v2_20261004.xml | 0 | 21 passed | 9fefe365651ece93e099a428c3eaac86be717a68eed76ec50126bb99383069f4 |
| alc_r0_bound_factor_regression_v3_20261004.xml | 0 | 374 passed, 0 failures/errors/skips, 13.954s | 999283ebecd5abb940efd617c1795f578f67d821b146ee0bd0fe1b4b6b8c687d |
| alc_r0_bound_factor_regression_v4_lf_20261004.xml | 0 | 374 passed, 0 failures/errors/skips, 19.033s | 07a7f6c241732a8c4148ca1a231f06a62148e42c8c370644a332bafec726e7d1 |

RED failures were missing bind APIs. Final regression includes 27 new binding
cases, the previous 328 pure regression cases, CPU capsule tests and four pure
LoRA initialization/count cases. The CUDA capsule case and actual-tokenizer
banking case were explicitly deselected, not interpreted as skipped successes.
Real-host LoRA fixtures were not selected. Root parsed JUnit counts, checked the
27 binding cases and absence of both excluded cases, and hashed all artifacts.
Ruff check passed after replacing two test lambdas with named functions and
formatting the new test file. No scientific acceptance criteria changed.

Binding cases cover first/last ports, FP32/BF16 output and gradients, independent
formula under CPU autocast, same-module parameter replacement, projection module
replacement, nonreentrant recomputation with non-gradient input, original factor
gradient destination, unknown ports, execution-time dtype and device rejection.

Initially reviewed source bytes (mixed existing CRLF/new LF before normalization):

- research_capsule.py: dfda084d0ffca98ea971def6fe679116edcdc59f705705cad7d32f7c3c7d331c
- matched_lora.py: e05a6a3e58d67fd73613db836bfe81b40d7dd42b143274bd36a293a67d3a520d
- test_alc_r0_bound_factor_operations.py: afea038276ce673bf0d74072a9b6c33515d25bff6ecb16a14d1984c98c13770e

Staged raw-byte precheck detected source line-ending normalization and stopped
publication BEFORE commit/push. Mechanically normalized both sources to LF and
pinned their attributes; text/diff semantics unchanged. Repeated the same whole
pure regression as v4_lf, actual exit0, root parsed final counts/hash above.
Final LF source hashes:

- research_capsule.py: 7a1484f2ff2d485475497a0c62ff717d2b4f95f56460fcf15abf613f3fac401e
- matched_lora.py: 8bfbabe274bf57a68bffee6d6b60eecd8cef6008a4e942498fd9f61ad8314505
- Tests unchanged, afea038276ce673bf0d74072a9b6c33515d25bff6ecb16a14d1984c98c13770e.
Both independent lanes revalidated these final LF bytes: code/security APPROVE,
architecture CLEAR. No new semantic change or blocker found; synthesis remains
APPROVE BINDING PREREQUISITE ONLY.

## Independent exact-byte synthesis

Code/security lane `/root/alc_r0_timing_code_gate_61`: APPROVE, no actionable
finding. Architecture lane `/root/alc_r0_timing_architecture_gate_61`: CLEAR,
no architectural blocker in declared scope. Both independently matched all three
source/test hashes above, inspected full new tests and executed no tests/assets.
Synthesis: APPROVE BINDING PREREQUISITE ONLY. Strongest counterargument and residual
obligation: captured module internals/tensor values remain mutable; bind under the
lease, guard before all execution/replay, never cache across mount changes, and
keep the full factor operation inside its checkpointed block. Tests demonstrating
old-reference replay are not authorization to mutate during an active lease.

Reproduction uses the locked `windows-training/.venv/Scripts/python.exe` with
`PYTHONPATH=src`, `PYTHONDONTWRITEBYTECODE=1` from the authoritative checkout:

```text
python -B -m pytest tests/test_alc_r0_bound_factor_operations.py tests/test_alc_r0_research_capsule.py tests/test_alc_r0_matched_lora.py::test_matched_lora_has_exact_count_and_capsule_initial_A tests/test_alc_r0_matched_lora.py::test_lora_initialization_preserves_global_rng tests/test_alc_r0_checkpoint_execution.py tests/test_alc_r0_checkpoint_optimizer.py tests/test_alc_r0_checkpoint_fidelity.py tests/test_alc_r0_base_digest.py tests/test_alc_r0_capsule_artifact.py tests/test_alc_r0_canonical.py tests/test_alc_r0_schema_validation.py tests/test_alc_r0_banking_scoring.py --deselect=tests/test_alc_r0_research_capsule.py::test_capsule_executes_bf16_host_path_on_cuda_with_fp32_factors --deselect=tests/test_alc_r0_banking_scoring.py::test_pinned_real_tokenizer_candidate_map_root_when_snapshot_is_present -q -p no:cacheprovider --junitxml=results/alc_r0_bound_factor_regression_v3_20261004.xml
```

Use a NEW artifact path for reproduction; preserve all original attempts.
Full objective ACTIVE. Next gate:
opt-in real-host wrapper integration and computational inventory audit, then
separately reviewed actual-host parity/resource invocations. This CPU evidence
does not prove model checkpoint parity, GPU fit, neural learning or .alc durability.
