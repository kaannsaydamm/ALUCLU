# Cognition import isolation: bounded regression evidence

Status: FINAL_RUN_PASS; independent terminal synthesis APPROVE / CLEAR.
Parent source HEAD: `9d245071f4585665e1f7d3a43e6289e23e84afb5` plus explicitly
hashed initializer/test/fixture below. This is not a committed-source-only run.

## Contract and scope

Only cognition/__init__.py changes runtime behavior. The original 200 exported
names, ordered __all__ and defining modules are independently pinned from HEAD.
Ordinary importlib resolves original objects on demand; only successful values
are cached. No dependency fallback, custom loader, duplicate lock registry or
changed persistence/canonical semantics. Unknown exports raise AttributeError;
dir does not resolve exports. Incidental eager side effects require explicit
imports. Explicit heavy exports/star imports intentionally load dependencies.

Final SHA-256:

- initializer: f9dff92e6b418e82ce73387b9c46f6d2f649d0bab501e3bfa5a313be07532e16
- test: 64d3775dcccb8e9d888e16e3af15422941857b2e88893a0e43838a4fd1974c8e
- fixture: bf7d352a8d977b1ff4d9f1378d871bfc9f7c710d0f57cac3c03a3fc1dc705ddf

## Actual execution

Artifact stems under results/ contain XML, observed.log and exit.json. Log and
exit JSON are parent-persisted after actual native terminal observation, not
child-generated receipts. Native stderr was not redirected separately; log is
combined delivered tool output, with CRLF normalized to LF.

- Pre-edit RED: alc_r0_cognition_import_red_20261006; actual exit1, 1 test,
  1 failure, zero errors/skips, .464s. Genuine initializer -> keys -> blocked
  cryptography chain, not collection/path failure. XML SHA256
  ca952358cf4b1aa27738e1ca14906e6d3bb4ccd2dced0173f0b4bba83c5c2a1c.
- Targeted GREEN: alc_r0_cognition_import_green_20261006; session57756,
  terminal chunkacc280, actual exit0; 45/0/0/0, 34.157s. XML SHA256
  7b935a68cbcb927baa4f184600bfa0ac35273c7a4d71c28193fba9edf8b6635a.
- Final regression: alc_r0_cognition_import_regression_20261007; session11274,
  terminal chunk88e557, actual exit0 personally observed; 790/0/0/0, 506.247s.
  XML SHA256 82bf7820e1098885df4429a9209746aa5e6449b8519dfdbd25fed0c26429aaba.

Counts overlap and must not be summed. No source/test edits during live runs.
Reviewed final hashes personally rechecked after regression terminal.

Existing pinned Python executable, no installation/environment modification:
`C:\Users\kaann\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\ALUCLU\research\alc-r0-smollm2-135m-v1\windows-training\.venv\Scripts\python.exe`

Cwd: Desktop ALUCLU/.worktrees/unified-lifelong-cognition-local.
Env: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, CUDA_VISIBLE_DEVICES=-1,
PYTHONNOUSERSITE=1, PYTHONPATH=<cwd>\src.

```text
-m pytest -q
tests/test_cognition_import_isolation.py
tests/test_alc_r0_import_isolation.py
tests/test_cognition_persistence.py
tests/test_cognition_architecture.py
tests/test_cognition_codec.py
tests/test_cognition_contracts.py
tests/test_cognition_keys.py
tests/test_cognition_ledger.py
tests/test_cognition_sessions.py
tests/test_cognition_observation.py
tests/test_cognition_recall_features.py
tests/test_cognition_calibration.py
tests/test_cognition_sensorium.py
tests/test_cognition_sensorium_boundaries.py
tests/test_cognition_sensorium_replay.py
tests/test_cognition_recollection.py
tests/test_cognition_reconsolidation.py
-p no:cacheprovider
--junitxml=results/alc_r0_cognition_import_regression_20261007.xml
```

Coverage includes full identity/from/star/root exports, missing dependency retry,
submodule orders, concurrent imports, shared persistence lock identity/exclusion,
atomic temporary writes, synthetic ledgers/sessions/sensorium/recollection.
Tests use temporary storage, static keys and fake keyring backends. Owned test
subprocesses are bounded; the outer regression has no global timeout. Explicit
exports can import Torch, but no model assets, host loading, training, evaluation,
actual OS credentials, GPU work, corpus, held-out data or paid compute were used.

## Claim boundary and next dependency

Both independent GPT-6.1 Sol lanes approved implementation and admitted the exact
17-file command before launch. Terminal code/spec/security APPROVE and architecture
CLEAR independently verified stored counts/hashes/source consistency and corrected
log contents. Neither reviewer personally observed the native terminal exit;
that distinct observation belongs to the parent. A transient log serialization
defect was recovered from original accessible output chunks; trajectory records
the defect and correction. Corrected log SHA256:
cb757e2ec6154c4d482625384c62cf16bf7e3a16f30911e5c2d77ed851978818.
This certifies only scoped import compatibility/regression, not full repository,
whole Task2 acceptance, native Linux/macOS, actual host, durable learning or R0.
The historical launcher draft remains preserved unchanged; its eager-import
description is historical, not current behavior after these scoped checkpoints.
Whole journal composition still requires original RFC8785 (no JSON fallback).
Trusted authority/history/calendar, q/v work ceilings, reservation/publication/
crash reconciliation, resource/log bounds, actual-host qualification, controls,
scientific freeze and retrieval-off durable learning remain OPEN.
