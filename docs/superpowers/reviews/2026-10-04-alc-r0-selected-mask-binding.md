# Checkpoint131: selected mask binding, not complete host acceptance

Baseline dde99709858853c9b68d8437ffd46b323d979a18; authoritative Desktop
worktree unified-lifelong-cognition-local. Full objective reread. Previous goal
turn was explanatory, not implementation progress; current turn repairs the
selected-mask gap established by checkpoint130's source inventory.

## Scope and residual limits

The module inventory now requires an explicit eager or SDPA Llama attention
route, resolves selected attention and mask functions, and binds both with the
existing bounded function freezer. This includes identity, code identity,
defaults, keyword defaults and supported closure state. Missing routes and
unsupported callable types fail with CheckpointExecutionError. The explicit
eager fallback passed to Transformers get_interface remains its actual resolution
semantics; absence of an eager registry key alone is not an error.

No monkeypatch is added to production. Six CPU fixtures construct a tiny Llama
attention module without loading assets or calling its forward. Four mutate the
mask registry using pytest-restored monkeypatch: eager/SDPA x preparation/replay.
They assert fingerprint drift, denial before the next side effect/block invocation,
lease release and gradient cleanup. Two reject an unknown route and missing mask.

This is NOT complete host certification. Transitive globals, class/property
dependencies, imported registry namespace replacement, dispatch-method mutation,
native kernels and ambient runtime dependencies remain outside this proof.
Mask mathematical parity is not tested here. No actual host weights/corpus,
language-model forward, CUDA workload, optimizer update or training was executed.
Actual host callback attachment, parity/resource qualification and scientific
retrieval-off/fresh-process learned capability remain OPEN.

## Executed evidence

Research Python executable is under the existing LocalCache research environment:
`ALUCLU/research/alc-r0-smollm2-135m-v1/windows-training/.venv/Scripts/python.exe`.
Environment: PYTHONPATH=src; PYTHONDONTWRITEBYTECODE=1. Commands use Python -B,
pytest -q -p no:cacheprovider --tb=short and unique --junitxml paths.

| Attempt | Scope | Actual pytest exit | JUnit tests/failures/errors/skipped | Time | XML SHA256 |
|---|---|---|---|---|---|
| red_v1 | state tests, -k 'selected_mask or unreviewed_attention', before repair | 1 | 6/6/0/0 | 91.230s | 43432c17c65e99a90576dafac24646e1db6f72a384f158a3792265e57fe01e55 |
| regression_v2 | state, forward, bound decoder, execution, lifecycle | 0 | 206/0/0/0 | 62.812s | 650775af3df24e8d0a2f0020ba452bb5681b521b66c5f70c6368355d5b7f05d7 |
| full_pure_v3 | explicit sixteen-file/target pure regression, final bytes | 0 | 527/0/0/0 | 41.131s | bdea5d8aea65868e2bd901365d9d19860162d7cba8f229a06e7059c5fd0974ce |

Artifacts are results/alc_r0_mask_binding_{red_v1,regression_v2}_20261004.xml.
RED failed at four unchanged fingerprints, unknown-route KeyError rather than
checkpoint error, and missing-mask non-rejection. These failures are retained.
Ruff format/check passed; formatting occurred while v2 was in flight, so v2 is
not represented as an exact-final-byte receipt. The broader pure v3 invocation
started after formatting and exact-byte hash capture; terminal exit0 and XML
counts/hash verified by root. Six new cases present, zero excluded asset cases.
Final source/test hashes remained identical to the independently reviewed bytes.
V3 artifact: results/alc_r0_mask_binding_full_pure_v3_20261004.xml.

V3 explicitly covers the sixteen test files/targets listed below, not the full
repository or actual-host/GPU qualification. Reproduction:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONDONTWRITEBYTECODE='1'
$scope = @(
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
# Supply the exact existing research Python path, and a NEW artifact name.
& $researchPython -B -m pytest -q -p no:cacheprovider @scope --deselect=tests/test_alc_r0_research_capsule.py::test_capsule_executes_bf16_host_path_on_cuda_with_fp32_factors --deselect=tests/test_alc_r0_banking_scoring.py::test_pinned_real_tokenizer_candidate_map_root_when_snapshot_is_present --tb=short --junitxml=$newArtifactPath
$LASTEXITCODE
```

## Independent exact-byte review

- Source SHA256 f18faa0c4ee9a77b96bb793d38b70c01ac10b55c6311b46f8dd3aa8bf3da4f57.
- Test SHA256 1c9da28c12507da67a3c3c8f96a9f90750edb58a46e93f5eb0fda5b83365e207.
- GPT-6.1 Sol code/spec/security lane: APPROVE, no actionable finding.
- GPT-6.1 Sol architecture lane: CLEAR, selected-callable binding only.
- Both inspected files/diff/hashes without imports/tests/assets/updates/edits.
- Synthesis: APPROVE SELECTED-CALLABLE BINDING ONLY, not complete host inventory,
  actual-host launch, mathematical parity, resources, learning or full objective.

Next: bind/audit the remaining explicit loss, factor-global, mask-helper and
runtime dependencies before actual-host callback attachment. Do not replace
missing coverage with a constant callback or reuse these pure receipts as ALC-0.
