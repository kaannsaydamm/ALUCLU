# Checkpoint132: enumerated factor dependencies, not host acceptance

Baseline ce5bfac77f89e44acc362115ec0d917901e0d3b6; authoritative Desktop
worktree unified-lifelong-cognition-local. Previous goal turn PROGRESS; clean
checkout revalidated and full objective reread before changes.

## Reproduced gap and implementation

Already-bound capsule operations still read global width/epsilon, F.linear and
Torch math/autocast bindings. The RED counterexample changes normalization epsilon
and proves changed numerical output with an unchanged prior fingerprint. Twelve
session fixtures additionally demonstrate missing preparation/replay denial for
capsule epsilon/width/linear/autocast and LoRA linear/autocast dependencies.

The helper now identifies known ResearchCapsuleV0 and MatchedQProjLoRA factor
classes and inventories the actual selected factory bound method and its globals
namespace. It records F/Torch namespace identities, linear callable, FP32 dtype,
and autocast binding. For capsule bind_port it additionally records width,
epsilon, BF16 dtype and sqrt. Python functions use the existing code/default/
keyword-default/closure freezer; builtin functions bind callable/self identity
ONLY, not native implementation code. Autocast classes bind identity and Python
init/enter/exit function state. Unsupported factory/namespace/callable/scalar/dtype
forms fail with CheckpointExecutionError; nonfinite scalar state also fails.

Known factor classes are lazily imported at fingerprint invocation, avoiding an
eager state/wrapper/LoRA import cycle. No production monkeypatch or optimizer was
added. Test namespace replacements use private module copies, never modify shared
Torch namespace contents, and are restored by pytest monkeypatch.

The final29 tests contain12 phase/arm/dependency denial cases, one real factor-math
epsilon counterexample, two complete unmodified-factor session positives and14
unsupported factory/namespace/callable/scalar rejection cases. Positives verify
finite factor gradients, no base gradients, lease release and a stable digest.
All execution is CPU factor math; no host weights, assets, corpus, actual language
model forward, CUDA workload, optimizer step or training acquisition was used.

## Executed receipts

Each command used the existing LocalCache research Python, PYTHONPATH=src,
PYTHONDONTWRITEBYTECODE=1, Python -B, pytest -q -p no:cacheprovider --tb=short and
a unique --junitxml artifact. Actual pytest exits were printed and observed.

| Attempt | Scope | Exit | Tests/failures/errors/skipped | Time | XML SHA256 |
|---|---|---|---|---|---|
| red_v1 | first13 new fixtures, prior production helper | 1 | 13/13/0/0 | 18.426s | 9eebcd5a4467453cc980e22d91e5c15839b4455babb8dbe586989a9f7927a801 |
| green_v2 | first13 + state + bound factor operations | 0 | 86/0/0/0 | 14.738s | 693bd76f4b3c4fd5452cd85f1f90ccc841c798b8a96c2da37b86a84815e37bb3 |
| full_pure_v3 | final29 + explicit existing pure regression | 0 | 556/0/0/0 | 19.121s | 5ca849e013a00672af31a3f2bcdb51f9b1be364ed401b09448daf4d25473c8c7 |

Artifacts: results/alc_r0_factor_dependencies_{red_v1,green_v2,full_pure_v3}_20261004.xml.
RED remains retained: six preparation cases reached side effects, five replay
cases failed to deny drift, width drift reached a late ValueError, and the
epsilon counterexample retained the old digest. These are not hidden as passing
cases. Root parsed all receipts, confirmed29new cases and0excluded asset cases
in final XML, and verified exact source/test hashes remained reviewed bytes.
Ruff format/check and git diff --check passed.

## Reproduction, exact scope

Use the seventeen explicit files/targets below. This is a pure research component
regression, NOT the full repository or actual-host/model/GPU qualification suite.
The two deselections intentionally exclude model/GPU and actual-tokenizer assets.

```powershell
$env:PYTHONPATH='src'
$env:PYTHONDONTWRITEBYTECODE='1'
$scope = @(
 'tests/test_alc_r0_factor_dependency_state.py',
 'tests/test_alc_r0_checkpoint_forward.py',
 'tests/test_alc_r0_bound_decoder_blocks.py',
 'tests/test_alc_r0_checkpoint_state.py',
 'tests/test_alc_r0_wrapper_checkpoint_lifecycle.py',
 'tests/test_alc_r0_bound_factor_operations.py',
 'tests/test_alc_r0_research_capsule.py',
 'tests/test_alc_r0_matched_lora.py::test_matched_lora_has_exact_count_and_capsule_initial_A',
 'tests/test_alc_r0_matched_lora.py::test_lora_initialization_preserves_global_rng',
 'tests/test_alc_r0_checkpoint_execution.py',
 'tests/test_alc_r0_checkpoint_optimizer.py',
 'tests/test_alc_r0_checkpoint_fidelity.py',
 'tests/test_alc_r0_base_digest.py',
 'tests/test_alc_r0_capsule_artifact.py',
 'tests/test_alc_r0_canonical.py',
 'tests/test_alc_r0_schema_validation.py',
 'tests/test_alc_r0_banking_scoring.py'
)
# Set researchPython to the exact existing executable and newArtifactPath to a NEW file.
& $researchPython -B -m pytest -q -p no:cacheprovider @scope --deselect=tests/test_alc_r0_research_capsule.py::test_capsule_executes_bf16_host_path_on_cuda_with_fp32_factors --deselect=tests/test_alc_r0_banking_scoring.py::test_pinned_real_tokenizer_candidate_map_root_when_snapshot_is_present --tb=short --junitxml=$newArtifactPath
$LASTEXITCODE
```

## Independent review and claim boundary

- Source SHA256 27a863914f11e42eb8ed788141780dfa0af5833451bf0be663abe7f70ba33099.
- Tests SHA256 6b4d55a902df2fdf2737dec88b0aec0966f6b08e216d6ddffc4de9608f371cbb.
- Independent GPT-6.1 Sol code/spec/security: APPROVE, no actionable finding.
- Independent GPT-6.1 Sol architecture: CLEAR, enumerated factor component ONLY.
- Neither reviewer ran tests/imports/model/assets/corpus/optimizer or edited files.
- Synthesis APPROVE ENUMERATED FACTOR BINDINGS ONLY, not full host/launch/learning.

Strongest residual risk: the inventory reads the CURRENT selected factory's
globals, while a previously captured closure can come from another function.
Subclass overrides/dynamically substituted factories and arbitrary transitive
helper/global/native state are not generically audited. Later actual-host
integration must prove the captured operations originated from the intended
reviewed factories under the lease, not accept arbitrary callbacks/subclasses as
a coverage certificate. Class import namespaces, factory helpers such as cast,
Torch context implementation globals, Tensor method/native behavior, and unrelated
host/mask/loss/runtime dependencies remain separate obligations.

Next safe work: complete explicit loss/mask/helper/runtime dependency audit and
attachment qualification before separately reviewed/frozen/budgeted actual CPU/GPU
parity/resource invocations. ALC-R0 neural capability, fresh-process learned-state
acceptance and full unified objective remain ACTIVE/OPEN. No threshold changed.
