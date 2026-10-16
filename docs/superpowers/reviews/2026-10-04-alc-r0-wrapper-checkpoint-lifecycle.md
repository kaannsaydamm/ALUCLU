# Wrapper checkpoint lifecycle bridge — partial integration evidence

Checkpoint125, baseline5bc11183c18aab54651c3656ebb59c3b47a9769b.
Implements the owner-controller/mutation portion of checkpoint detail section C.
The explicit checkpoint-bearing forward keyword/path, private metadata binding,
complete factor placement and unregistered host computational inventory remain
OPEN. A session factory is not forward authorization or training authority.

Both real wrapper classes now own ONE persistent CheckpointController, bound to
the lazy current base/factor getters and declared30layers. Controller initialization
is after base/capsule assignment and before eval; LoRA's getter is invoked only at
session entry, after subclass construction. Ordinary controller replacement,
deletion and reinitialization are denied even outside a lease. Default forward
refuses any active lease before computing, so no unaccounted default path exists.

Active lease prechecks cover ordinary wrapper attribute writes/deletion, train/
eval, _apply/device/dtype changes, mount/detach, load_state_dict, requires_grad_,
zero_grad, add_module/register_module/set_submodule, register_parameter/buffer.
The explicit register_module override is necessary because the inherited alias
would otherwise bypass add_module. Outside leases methods delegate to PyTorch
normally. This is a cooperating-process API contract, NOT comprehensive hostile
Python interception. Descendant mutation, direct dictionaries/.data, external
optimizer writes and unregistered computational state need engine replay/boundary
guards and the later host-specific inventory. No claims of complete protection.

Tests deliberately bypass VerifiedHost constructors and use a 4x4 frozen Linear
base plus research factors. They prove lifecycle plumbing only: no real Llama
model, tokenizer assets, task corpus, optimizer step, GPU or learned capsule.

## Root verified attempts

Locked research Python3.12, Torch2.14, Transformers5.17, CPU fixtures. All exit
codes observed from actual pytest/shell. JUnit counts/time/hash personally parsed.
Stdout/stderr tool-captured only, not separate persisted log artifacts.

| results/ artifact | Actual exit | Counts/time | SHA256 |
| --- | --- | --- | --- |
| alc_r0_wrapper_lifecycle_red_v1_20261004.xml | 1 | 25failures,0errors/skips,11.837s | 60132eef624976b82d229b5ca06760b770ebcf1f871aaea57820d6c91f85610b |
| alc_r0_wrapper_lifecycle_green_v2_20261004.xml | 0 | 25passes,0errors/skips,10.108s | 0efe2c0426e5055909d96ce9712478a7fc3adfff7f476562c33f2d2a4f5a5824 |
| alc_r0_wrapper_lifecycle_mutator_red_v3_20261004.xml | 1 | 12failures,0errors/skips,9.985s | 0448a93cd2e84d628df824d7b294c37b55337b03139ce7b58a9802dcccde0668 |
| alc_r0_wrapper_lifecycle_regression_v4_20261004.xml | 0 | 419passes,0failures/errors/skips,16.038s | 61ac84469eb70eb51829f3e58665e213a1d951badd734037adb55bce5039b4a4 |
| alc_r0_wrapper_lifecycle_attribute_red_v5_20261004.xml | 1 | 4failures/2passes,0errors/skips,12.819s | d43e8a2ff9d2060c9a0aaf1240efbab6abc92d95dca718d76d3f1bd173a28662 |
| alc_r0_wrapper_lifecycle_regression_v6_20261004.xml | 0 | 425passes,0failures/errors/skips,25.022s | 2d5a76592765e3f6c56133ce1a8ba994c5476baeafc1e11a331f12688fae3182 |
| alc_r0_wrapper_lifecycle_regression_v7_20261004.xml | 0 | 427passes,0failures/errors/skips,41.449s | 2ae67e256a61b943134ec494c42354066c266337e1782b83917872e09c2b3b61 |
| alc_r0_wrapper_lifecycle_regression_v8_lf_20261004.xml | 0 | 427passes,0failures/errors/skips,13.100s | 9ea94d45d88b6db68400b85fced2cf1c15443484a3e4919ec106303f2e12057c |

REDv1: missing initializer. REDv3: six mutator APIs per arm missing prechecks.
First code review REQUEST CHANGES: ordinary nonprotected module assignment and
registered state deletion bypassed four-name guard via nn.Module internals.
Architecture lane CLEAR did not override this blocker; synthesis REQUEST CHANGES.
REDv5 reproduced module/plain assignment and module/buffer deletion; parameter/
buffer assignment already routed to explicit prechecks. Repaired by rejecting
ALL ordinary wrapper attribute mutation during a lease. Added positive no-lease
delegation fixtures before finalv7. No thresholds or scientific criteria changed.

Final regression includes53lifecycle cases and all374 prior relevant pure cases.
Root checked53count and absence of explicitly deselected CUDA capsule and pinned
real-tokenizer tests. Real-host LoRA fixtures were not selected. Ruff passed.

Repaired source/test bytes initially reviewed before host LF normalization:

- host_wrapper.py e48f391c69e9928ba21786094b827d73c360b0936ace31f508d2067b7670c8f7
- matched_lora.py f4c866f1d04872d1d6a6d203a5450438d1aac90408bb4bebfea8b1b5ead58fc0
- test_alc_r0_wrapper_checkpoint_lifecycle.py f82ea1ce7867cfa2532e1d2892af9f04fdc6075bc65f804bb6354f0cc9e7269f

Staged raw-byte publication check detected host_wrapper CRLF normalization and
stopped BEFORE commit/push. Ruff had preserved the original CRLF file ending.
Mechanically normalized host_wrapper to LF, pinned its Git attribute and repeated
the same427-case suite as v8_lf. Final host SHA:
8ac521e9eaa7265b9a801ad2d5517450320c8fd943d66be53219a990859e36fa.
LoRA/test hashes unchanged. Both independent lanes revalidated finalLF hash/text:
code APPROVE, architecture CLEAR. Root verifiedv8 terminal exit0,53lifecycle cases,
excluded-case absence and XMLhash above; all prior seven attempts retained.

Final independent repaired-byte rereviews returned code/security APPROVE and
architecture CLEAR, independently matching all three hashes above. Synthesis
APPROVE LIFECYCLE BRIDGE ONLY. The first rejected review and RED reproduction
remain recorded; the old architecture CLEAR never overrode code REQUEST CHANGES.
Final reviewers performed no execution and did not infer terminalv7 from an
assignment that described it as running; root separately verified its exit/counts.
Architecture residual: later forward must not write wrapper bookkeeping during
the active lease or weaken the guard to accommodate it. Full objective ACTIVE.
Next: actual opt-in checkpoint forward integration,
host computational inventory, then separately reviewed model parity/resource
invocations. Neither lifecycle unit tests nor review prove neural capability,
actual-host parity/resource fit, portability or .alc durability.

## Reproduction

From authoritative checkout with locked windows-training/.venv/Scripts/python.exe,
PYTHONPATH=src and PYTHONDONTWRITEBYTECODE=1. Use NEW artifact names on repetition.

```text
python -B -m pytest tests/test_alc_r0_wrapper_checkpoint_lifecycle.py tests/test_alc_r0_bound_factor_operations.py tests/test_alc_r0_research_capsule.py tests/test_alc_r0_matched_lora.py::test_matched_lora_has_exact_count_and_capsule_initial_A tests/test_alc_r0_matched_lora.py::test_lora_initialization_preserves_global_rng tests/test_alc_r0_checkpoint_execution.py tests/test_alc_r0_checkpoint_optimizer.py tests/test_alc_r0_checkpoint_fidelity.py tests/test_alc_r0_base_digest.py tests/test_alc_r0_capsule_artifact.py tests/test_alc_r0_canonical.py tests/test_alc_r0_schema_validation.py tests/test_alc_r0_banking_scoring.py --deselect=tests/test_alc_r0_research_capsule.py::test_capsule_executes_bf16_host_path_on_cuda_with_fp32_factors --deselect=tests/test_alc_r0_banking_scoring.py::test_pinned_real_tokenizer_candidate_map_root_when_snapshot_is_present -q -p no:cacheprovider --junitxml=results/alc_r0_wrapper_lifecycle_regression_v7_20261004.xml
```
