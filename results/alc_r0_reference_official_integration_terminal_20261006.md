# Checkpoint201: random CPU full-wrapper integration

Parent code commit: 70fdc8a03b3a25e2c69607a7035239763c4d92d2.
This is random test-only CPU wiring, NOT pretrained SmolLM2 qualification,
learning, gradient/optimizer validation, E3 or actual-host resource admission.

## Exact bytes independently reviewed

- tests/alc_r0_random_qv_host.py: 9f50ff2855f0108821e4ef0203e7a289515e35670c14f96947e69aaf6d6202f5
- tests/test_alc_r0_reference_official_integration.py: 5b7fe0a4679a82afe2cc9ec9006bbd714335d574e57551cf47dea8660deb4eeb
- scripts/alc_r0_full_factor_cpu_tests.ps1: 60ccd7a3a6003101b463e2976aac82b6b04eaadab4b0d36b828d7239ed3c39b0

GPT6.1Sol independent code lane APPROVE; architecture lane WATCH. Combined
verdict COMMENT, not merge-ready APPROVE. No blocker for the manually owned
serial fake CPU attempt. WATCH concerns: memory snapshot/duplicate heuristic
provides no reservation, atomic lock, sandbox or owned timeout; random thin MLP,
embedding and output head do not establish full pretrained numerical/resource
behavior, gradients, checkpoint backward or optimizer correctness.

Constructor uses actual Transformers Llama forward, 30 layers, attention width576,
q576/v192, nine query heads and three KV heads of width64. Explicit test deviations:
embedding1024, MLP64, rank16 head emitting49152 logits; 31280448 frozen parameters.
Fabricated host metadata is non-authenticating test wiring. CPU RNG/thread state
restored, CUDA seed/init forbidden. No assets/tokenizer/corpus/GPU acquisition.

## Integration terminal evidence

Invocation: powershell.exe -NoProfile -ExecutionPolicy Bypass -File
scripts/alc_r0_full_factor_cpu_tests.ps1 -Suite OfficialIntegration -ArtifactStem
alc_r0_reference_official_integration_v1_20261006

Tool session80472 personally returned exit0. Persisted exit log agrees:
pytest_exit_code=0, child_pid=15788,
observed_at=2026-10-06T14:55:24.0721019+03:00.
stdout: four dots,100pct; stderr empty. JUnit tests4/failures0/errors0/skipped0,
time246.156s. Full72 real-forward/cache/witness/detach test214.825s; no-op mount,
corrupted actual cache receipt and exceptional fixture state-restoration negatives
also passed. Relevant Python processes absent after completion.

XML SHA256: 51dfe5dae343de5b44bb50acb4c075957ed8eca4472449d4ddebe6a60360d18f.
Raw start/exit/stdout/stderr/XML files retained with the v1 stem.

## Separate relevant regression

Pinned existing Python, PYTHONPATH=<Desktop worktree>/src:
python -m pytest tests/test_alc_r0_reference_official_suite.py
tests/test_alc_r0_reference_official_guard.py tests/test_alc_r0_reference_qv_artifact.py
tests/test_alc_r0_parity_factory.py -q
--junitxml=results/alc_r0_reference_official_integration_regression_v1_20261006.xml

Tool session61601 personally returned exit0; captured tool stdout reached100pct.
JUnit tests153/failures0/errors0/skipped0/time28.882s. XML SHA256:
57807600c6a51698475e09a612373ed340398cabd2fdd7a94fcae6f46ead1a74.
This note transcribes the observed terminal tool evidence; no separate raw
stdout/stderr/exit log was generated for this foreground regression.
The four integration tests and153 regressions are separate invocations.

## Limits and next gate

No threshold, seed, original schedule, scientific grid or production code changed.
CPU AST, PowerShell parse, Ruff checks passed before execution. Reviewed hashes
revalidated unchanged afterward. No RED collection claim: original fixture
execution was deferred for low RAM, not represented as a failing test.

Separate q/v gradient/pending/optimizer composition and bounded120-factor receipt
remain required. Actual pinned-host invocation/authentication/resource/accounting,
rights/sealer/evaluation freeze and retrieval-off held-out durable learning remain
OPEN. No R0 PASS, universal portability or final program completion claim.
