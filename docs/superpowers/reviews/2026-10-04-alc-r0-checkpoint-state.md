# Checkpoint126: optional computational-state fingerprint bridge

Baseline: `4fd94682e52a99706a75787672257fd31e224f92`.
Authoritative checkout: `C:\Users\kaann\Desktop\03_Projeler_Arge\ALUCLU\.worktrees\unified-lifelong-cognition-local`.

## Contract and limits

The checkpoint controller optionally accepts a cooperating caller's fingerprint
callback. A session captures callback identity and a strict lowercase 64-hex
digest, and every existing guard rejects callback replacement or digest drift.
The default `None` preserves the previous engine behavior.

The separate helper inventories module attributes, configuration, supported
containers, forward bindings and small unregistered nontrainable tensors.
Unknown objects, foreign bound-method owners, cycles, hooks, compiled calls,
implicit HF checkpointing and declared nondefault RoPE are rejected.
Registered parameters/buffers remain the engine's responsibility.

Component caps: roots16; module records4096; module depth64; children2048;
root/child-name characters256; attributes/container items2048; value depth32;
visited values100000; UTF8 scalar strings64KiB; scalar integers256bits;
unregistered tensor bytes64KiB; serialized stream16MiB. These are not a measured
total peak-memory, latency or real-host resource-fit guarantee.

Function globals, arbitrary class/property dependencies and external state are
explicitly **not inventoried**. A fixture changes a function-global scalar,
demonstrates changed output and unchanged digest, then restores the scalar. This
records a limitation, not complete-inventory acceptance. The later host-specific
audit must identify and bind/reject those dependencies before actual execution.
The fingerprint carries process-local identities; it is not a portable content
hash or hostile/compromised-host security boundary.

## Execution evidence

Each file below is retained under `results/`; exit codes were observed by the
parent shell, not inferred from XML. Parent parsed terminal JUnit and SHA256.

| Artifact stem `alc_r0_checkpoint_state_` | Exit | Tests | Failure/error/skip | Seconds | SHA256 |
|---|---:|---:|---|---:|---|
| red_v1_20261004.xml | 2 | 1 | 0/1/0 | 8.232 | e0615e3f33f09592c05b644d93ff5007f432b198c5795d8bb262919c7253302b |
| green_v2_20261004.xml | 0 | 23 | 0/0/0 | 9.139 | dc5bc8b818f76176b1ea73e5eb60ecebde1d9966e7c118bedc31604a11107dac |
| method_red_v3_20261004.xml | 1 | 2 | 1/0/0 | 10.671 | b7e88cc8cb11a7f9613fcc9bd504d4a5181cddb17407db9dac16769487337295 |
| regression_v4_20261004.xml | 0 | 457 | 0/0/0 | 12.751 | 5605054e49b10c723688f744f567cfbb14a5c8332fc6cd3d4af668ecbc92578b |
| bounds_red_v5_20261004.xml | 1 | 5 | 5/0/0 | 9.690 | 170c53e3b4e6f316075e434762b0df0ce139f57ff7219ca68a62acdd7f4eaed7 |
| bounds_green_v6_20261004.xml | 0 | 36 | 0/0/0 | 9.833 | 0d0f5b44c693bca725c6e5af27bb3792ab16aa07d3807828a85a4730063d7b94 |
| regression_v7_20261004.xml | 0 | 463 | 0/0/0 | 13.981 | f1ac790ffcc6f9a27db8002edb4f5512f5b3ae5d1bb9333be53462a1f2bce2cf |

REDv1 is a missing-module collection error. MethodRED reproduced foreign-method
acceptance, not the separate static ephemeral-method identity risk. BoundsRED
reproduced five missing caps. No artifact was overwritten or reinterpreted.
Initial Ruff E731 was repaired; final Ruff format/check succeeded.
Final suite includes 36 state tests plus 427 previous pure cases. The excluded
real CUDA host and pinned real-tokenizer cases are absent, not reported skipped.
No model asset, corpus, optimizer step, training or capability evaluation ran.
Logs are tool-captured; separate persisted stdout/stderr files were not created.

## Reproduction

Windows research Python: `C:\Users\kaann\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\ALUCLU\research\alc-r0-smollm2-135m-v1\windows-training\.venv\Scripts\python.exe`.
Use `PYTHONPATH=src`, `PYTHONDONTWRITEBYTECODE=1`, Python `-B`, pytest
`-q -p no:cacheprovider --tb=short --junitxml=<new unique results path>`.

Select these files/nodes:

```text
tests/test_alc_r0_checkpoint_state.py
tests/test_alc_r0_wrapper_checkpoint_lifecycle.py
tests/test_alc_r0_bound_factor_operations.py
tests/test_alc_r0_research_capsule.py
tests/test_alc_r0_matched_lora.py::test_matched_lora_has_exact_count_and_capsule_initial_A
tests/test_alc_r0_matched_lora.py::test_lora_initialization_preserves_global_rng
tests/test_alc_r0_checkpoint_execution.py
tests/test_alc_r0_checkpoint_optimizer.py
tests/test_alc_r0_checkpoint_fidelity.py
tests/test_alc_r0_base_digest.py
tests/test_alc_r0_capsule_artifact.py
tests/test_alc_r0_canonical.py
tests/test_alc_r0_schema_validation.py
tests/test_alc_r0_banking_scoring.py
```

Explicit deselections:

```text
--deselect=tests/test_alc_r0_research_capsule.py::test_capsule_executes_bf16_host_path_on_cuda_with_fp32_factors
--deselect=tests/test_alc_r0_banking_scoring.py::test_pinned_real_tokenizer_candidate_map_root_when_snapshot_is_present
```

## Independent review

First code lane COMMENT, architecture CLEAR. Both explicitly rejected interpreting
this prerequisite as complete host-state coverage. Parent added global-dependency
counterexample/documentation and explicit resource bounds, retaining negative
evidence. Repaired-byte final code APPROVE, architecture CLEAR; synthesis APPROVE
PREREQUISITE BRIDGE ONLY. Both verified all three candidate hashes below, inspected
without execution, and withheld actual-host/training/learning approval. Parent
separately verified the terminal 463-case regression and its artifact hash.

Reviewed candidate hashes:

- `checkpoint_execution.py`: ec2b3a85ed96105e962f83ae9ac883870460e184004267385f006f3f90540ef9
- `checkpoint_state.py`: a4d897b6c8c0b921a7473e5cea60aa8c757a0a61801358cdbf70461a57e0770e
- `test_alc_r0_checkpoint_state.py`: 293273341d534adff32f76b18e91513a05b4d8f0a822b8283b38b7313d682cb8

Opt-in real forward attachment, complete pinned host inventory, actual-host parity,
resource qualification, confirmatory neural capability, governed user learning,
final `.alc` container and portability/longitudinal gates remain OPEN.
