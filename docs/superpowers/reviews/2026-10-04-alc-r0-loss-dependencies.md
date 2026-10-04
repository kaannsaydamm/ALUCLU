# Checkpoint133: causal loss bindings, not complete host qualification

Baseline8d12dec5179e1009d5c82ccac2d0f13127820683; clean authoritative Desktop
worktree unified-lifelong-cognition-local revalidated. Full objective reread.
Previous goal turn PROGRESS; this turn binds loss dependencies identified by130.

## Numerical counterexample and scope

Replacing fixed_cross_entropy doubled actual numeric causal loss while leaving
the prior computational fingerprint unchanged. Five preparation cases reached
side effects and five replay cases failed to deny property/registry/fixed-helper/
cross_entropy/pad dependency drift. All11 original RED failures are retained.

The helper now statically inspects the loss property and override without invoking
the property. It requires the reviewed property, bounded dictionary registry and
explicit ForCausalLM route or exact reviewed function override. Unknown implicit
fallback routes, foreign selected loss/helper functions and unsupported namespaces/
callable schemas fail with CheckpointExecutionError.

Bindings enumerate property getter, registry/global namespace identities, selected
loss/helper function identity/code/default/keyword-default/closure state, resolved
NN functional pad/cross_entropy functions, Torch/native namespace identities,
native pad/cross_entropy_loss callable identities and is_tensor function state.
This is NOT generic transitive global traversal or native implementation audit.
It is deliberately coupled to the reviewed installed loss/runtime structure.

The new fixtures subclass LlamaForCausalLM solely to exercise actual loss-property
resolution, but initialize only nn.Module and one tiny frozen parameter; model
construction is bypassed and forward explicitly raises. CPU loss/factor gradients
are exercised, not actual language-model forward. No model weights/assets/corpus,
held-out data, CUDA workload, optimizer updates or training acquisition occurred.

Final25 fixtures:10 preparation/replay denials, one numeric helper counterexample,
two complete unchanged loss-gradient sessions (registry and known exact override),
nine unsupported route/registry/override negatives, three same-function default/
property-code mutations. Positives verify stable digest, lease release, finite
factor gradients and no base gradients. Shared registry/function changes and
private namespace replacements use pytest monkeypatch restoration.

## Executed receipts

Existing LocalCache research Python; PYTHONPATH=src, PYTHONDONTWRITEBYTECODE=1,
Python-B, pytest-q -p no:cacheprovider --tb=short, unique --junitxml for each run.
Root observed actual printed pytest exit and independently parsed JUnit/hash.

| Attempt | Scope | Exit | Tests/failures/errors/skipped | Time | XML SHA256 |
|---|---|---|---|---|---|
| red_v1 | first11 new fixtures before repair | 1 | 11/11/0/0 | 58.933s | a79a6667591f99f76b571267ddfa27cdc712beef1ab7c6a04dc5665eacd23ef9 |
| green_v2 | first11 + state + factor dependency tests | 0 | 86/0/0/0 | 15.987s | bba63b34e0839a33f689022ad491b97c1a794f66ea4a00369d568eb04210f583 |
| full_pure_v3 | final25 + explicit existing pure regression | 0 | 581/0/0/0 | 53.926s | 5272f071fffcb8b9af0203a33b31425cec809600d5e343dbfd364bc8b214ee72 |

Artifacts:results/alc_r0_loss_dependencies_{red_v1,green_v2,full_pure_v3}_20261004.xml.
Final XML includes25 new cases and0 excluded model/tokenizer asset cases. Reviewed
source/test hashes unchanged after final execution; Ruff and diff checks passed.

## Reproduction

Use the explicit seventeen-file/target scope in checkpoint132's reproduction
record, prefixed with tests/test_alc_r0_loss_dependency_state.py. Preserve both
asset deselections; this is NOT a full repository or host/GPU suite. Full exact
command (existing research Python path in researchPython; NEW path in newArtifactPath):

```powershell
$env:PYTHONPATH='src'
$env:PYTHONDONTWRITEBYTECODE='1'
& $researchPython -B -m pytest -q -p no:cacheprovider tests/test_alc_r0_loss_dependency_state.py tests/test_alc_r0_factor_dependency_state.py tests/test_alc_r0_checkpoint_forward.py tests/test_alc_r0_bound_decoder_blocks.py tests/test_alc_r0_checkpoint_state.py tests/test_alc_r0_wrapper_checkpoint_lifecycle.py tests/test_alc_r0_bound_factor_operations.py tests/test_alc_r0_research_capsule.py tests/test_alc_r0_matched_lora.py::test_matched_lora_has_exact_count_and_capsule_initial_A tests/test_alc_r0_matched_lora.py::test_lora_initialization_preserves_global_rng tests/test_alc_r0_checkpoint_execution.py tests/test_alc_r0_checkpoint_optimizer.py tests/test_alc_r0_checkpoint_fidelity.py tests/test_alc_r0_base_digest.py tests/test_alc_r0_capsule_artifact.py tests/test_alc_r0_canonical.py tests/test_alc_r0_schema_validation.py tests/test_alc_r0_banking_scoring.py --deselect=tests/test_alc_r0_research_capsule.py::test_capsule_executes_bf16_host_path_on_cuda_with_fp32_factors --deselect=tests/test_alc_r0_banking_scoring.py::test_pinned_real_tokenizer_candidate_map_root_when_snapshot_is_present --tb=short --junitxml=$newArtifactPath
$LASTEXITCODE
```

## Independent review and residual limits

- Source SHA256 a4b624a8c69b46b6c9ac4c329e248102e86dfe20e789234a62fb4b4f3e2f12e0.
- Tests SHA256 fb8a0487ad0a221ddbc95a785701932722be0696b1ea331391111356c85c8fb1.
- Independent GPT6.1Sol code/spec/security APPROVE, no actionable finding.
- Independent GPT6.1Sol architecture CLEAR, enumerated loss-binding ONLY.
- Neither reviewer ran imports/tests/models/assets/corpus/optimizer or edited files.
- Synthesis APPROVE ENUMERATED LOSS BINDINGS ONLY; no host/launch/learning approval.

Explicit identity checks bind imported reviewed property/functions and selected
runtime structure; they do not freeze all globals/transitive functional branches,
Tensor behavior, arbitrary attribute resolution or native implementation state.
Native behavior can change while callable identity remains unchanged. A matching
fingerprint is cooperating-process drift evidence, not hostile-host security,
mathematical parity, complete host inventory or source/runtime qualification.

Remaining work includes mask/helper route globals, ambient backend settings,
decorated callable/class/context paths, actual pinned host attribute qualification
and callback attachment. These precede separately reviewed/frozen/budgeted actual
CPU/GPU parity/resource invocations and the scientific retrieval-off/fresh-process
learned-capability gate. Full unified goal remains ACTIVE; thresholds unchanged.
