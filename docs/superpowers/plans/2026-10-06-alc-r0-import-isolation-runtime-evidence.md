# ALC-R0 package import isolation — bounded development evidence

Status: FINAL_RUN_PASS; independent terminal verdicts tracked in TRAJECTORY.md.
This is an import
prerequisite, not ALC-R0 acceptance, real-host qualification or a launch permit.
Parent source HEAD: `3b9fe764e5a87937aaaf58a08dad363346068073` plus the four
explicitly hashed implementation/test files below. No committed-source-only claim.

## Change and compatibility contract

Only `aluclu/__init__.py` and `aluclu/alc_r0/__init__.py` change runtime behavior.
Static module/symbol allowlists resolve through ordinary importlib on public export
access, cache only successful resolutions, propagate original dependency errors,
and raise AttributeError for unknown exports. No lock, path-based loader, dependency
probe, module substitution, fallback stub or arithmetic-policy change was added.
Root version remains 0.1.0. Both public __all__ rosters retain exact contents/order.
The fixture independently pins the pre-edit HEAD associations, not the new maps.

Plain package imports and ordinary checkpoint_resource_admission imports are now
tested without third-party imports. Explicit computational exports and star import
intentionally load their actual dependencies. Incidental eager module attributes
are not promised after plain import; direct/from-submodule imports retain normal
semantics. Consumers that depended on eager side effects may need explicit imports.

## Exact final bytes

- Root initializer: `8e9d02f68b1f56d232b557557d6fa602c7c02718e6a0dd16c01b9e6489b9df0f`
- R0 initializer: `d6bc75a07db299686186873f268125a8423753e16a604e392e24d83daf0e44b2`
- Import tests: `bceadcc0c98af0b37542f208a417d94afa6b52dbaa3a76de958df91fbbe09ec2`
- Export fixture: `55f1209d73b599a4ad6961cde6b36c830ce5cbda254f1b81ec749974553dc9ea`

Existing Ruff check and format --check passed on these four final files (f8ff5e).
Initial lint/format failure was corrected after the preceding suite was terminal;
the final run below revalidates the changed bytes. No source/test edits while live.

## RED, GREEN and final-byte regression

All artifact stems are relative to results/ and include XML, observed.log and
exit.json. Logs/exit JSON were persisted by the parent after terminal observation;
they are not child-generated exit receipts. stderr from the native command was
not redirected separately: observed.log is the tool's combined output. Each import
test captures child stdout/stderr and asserts its own stderr condition.

| Attempt | Stem | Actual terminal | JUnit tests/failures/errors/skips | Time |
| --- | --- | --- | --- | --- |
| Pre-edit RED | alc_r0_import_isolation_red_20261006 | chunk39d496, exit1 | 1/1/0/0 | 0.430s |
| Targeted GREEN | alc_r0_import_isolation_green_20261006 | session14385, chunkcec7af, exit0 | 87/0/0/0 | 24.317s |
| Expanded pre-format regression | alc_r0_import_isolation_regression_20261006 | session87679, chunk834f15, exit0 | 278/0/0/0 | 47.913s |
| Final-byte regression | alc_r0_import_isolation_final_20261006 | session8812, chunk83ada1, exit0 | 278/0/0/0 | 51.004s |

Counts overlap; do not sum them as unique cases. RED failed genuinely at
aluclu -> cognition -> keys -> cryptography before initializer edits, not pytest
collection or PYTHONPATH. The final run retains history-unreconciled denial; making
imports pure does not make unknown history complete or admit research.

XML SHA-256, personally recomputed and parsed:

- RED: `b31eeb488180766c9c578485888f96b3b4799e54f3b06b8892a1317bdb2a6e52`
- GREEN: `b21fdce34ae19e161c12b7122504b9e7546dec7ed51c18fc1590820f08600811`
- Expanded: `ec386744c33fb53b35203fe75eb81b41853af59037786fe2f57ba1ed5c62ad57`
- Final: `6e6e233d6f92d670a28a5a84517d08371dc35cc9aa0a83d485f50cef619783bf`

## Reproduction selection and runtime

Existing pinned executable, no installation or environment modification:

`C:\Users\kaann\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\ALUCLU\research\alc-r0-smollm2-135m-v1\windows-training\.venv\Scripts\python.exe`

Authoritative cwd is the Desktop unified-lifelong-cognition-local worktree.
Environment: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, CUDA_VISIBLE_DEVICES=-1,
PYTHONNOUSERSITE=1, PYTHONPATH=<authoritative worktree>\src.

Arguments for the final run:

```text
-m pytest -q
tests/test_alc_r0_import_isolation.py
tests/test_alc_r0_resource_admission.py
tests/test_cognition_architecture.py
tests/test_model.py
tests/test_compression.py
tests/test_episodic.py
tests/test_exact_cache.py
tests/test_zoology_mqar.py
tests/test_cognition_codec.py
tests/test_cognition_contracts.py
tests/test_alc_r0_canonical.py
tests/test_alc_r0_schema_validation.py
tests/test_alc_r0_host.py
tests/test_alc_r0_wrapper_namespaces.py
-p no:cacheprovider
--junitxml=results/alc_r0_import_isolation_final_20261006.xml
```

Import tests cover all public direct-object identities/from/star imports, roster,
non-resolving dir, unknown names, dependency failure/retry without failed cache,
submodule import orders, concurrent same/different exports plus direct imports,
four CLI imports without main execution, and third-party-denied pure admission.
Children have bounded 30s/90s timeouts; the outer suite has no global timeout.
Other tests use tiny synthetic CPU tensors/models, fake host backend and temporary
fabricated snapshots/local schema fixtures. No pretrained model, tokenizer, corpus,
held-out data, paid compute, model acquisition or CUDA workload was invoked.

## Independent review and residual gates

Existing independent GPT-6.1 Sol code and architecture lanes reviewed the contract,
implementation, each exact invocation and final-byte formatting changes before
execution: code APPROVE; architecture CLEAR for narrow import scope, with WATCH
for incidental-attribute timing and omitted full-suite/launcher coverage.
Both explicitly assessed the fourteen-file suite as sufficient for this bounded
checkpoint; this is not full-repository PASS. Terminal verdicts are recorded
separately in TRAJECTORY.md after independent synthesis.

Deferred: long scale benchmarks, approximately 23-minute full random parity test,
real pretrained host qualification, GPU/backend/OS portability and full repository
regression. Prior numerical evidence remains tied to its older source hashes.
Full journal bootstrap (canonical/rfc8785 and cognition/cryptography), trusted
accounting/authority, q/v ceilings, durable reservation/publication/crash contracts,
rights/evaluator/sealer/scientific freeze and actual retrieval-off durable neural
learning acceptance remain OPEN. No threshold/grid/accounting clock was changed.
