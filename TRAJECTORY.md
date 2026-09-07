# ALUCLU Development Trajectory

This is the durable continuity ledger for the repository. It exists so work can
resume from repository evidence even when a chat, machine, account, process, or
agent context disappears.

## Continuity contract

- Update this file in the same commit as every logical tracked change.
- Also record verification runs, independent reviews, gate decisions, benchmark
  artifacts, failures, interrupted runs, and material environment changes.
- Entries are chronological and append-only. Correct an older entry with a new
  entry; do not silently rewrite history.
- A passing label is not enough: record the command scope, result count, and any
  skips, warnings, unresolved risks, or interrupted evidence.
- Never mark a roadmap task CLEAN until its reviewed plan and acceptance gates
  are satisfied by current repository evidence.
- Local orchestration state under `.omc/`, `.omx/`, and ignored
  `.superpowers/sdd/` directories is supporting evidence, not a substitute for
  this tracked ledger.

## Authoritative plans

- Global order and invariants:
  `docs/superpowers/plans/2026-08-12-unified-lifelong-cognition.md`
- Task 1 persistence reconstruction:
  `docs/superpowers/plans/2026-08-22-task-1-persistence-reconstruction.md`
- Task 2 sensorium/recollection:
  `docs/superpowers/plans/2026-09-02-task-2-sensorium-recollection.md`

## Roadmap state

| Task | State | Authoritative checkpoint | Next gate |
|---|---|---|---|
| 1 — encrypted lifetime persistence | CLEAN | `f5a30e0` | Frozen unless a concrete regression is proved |
| 2 — sensorium/recollection | TASK 2.0 CLEAN / 2.1 VERIFICATION | `3aa3fd8`; corrected plan hash `01669B9D...8357`; GREEN implementation pending acceptance | Independent review, full/static/determinism gates |
| 3–14 | NOT STARTED | global roadmap | Start only after every preceding task is CLEAN |

## Reconstructed committed history

The Task 1 row below is backfilled from the current Git history and its retained
Task 1 evidence ledger. Commit subjects are preserved verbatim so a future
session can map each decision to the exact diff.

| Date | Commit | Durable outcome |
|---|---|---|
| 2026-08-22 | `8f28e8c` | Recover the lost persistence trajectory before rebuilding its code |
| 2026-08-22 | `0faaaac` | Establish canonical cognition inputs before persistence accepts bytes |
| 2026-08-22 | `90843fc` | Fail closed on authenticated state sidecar drift |
| 2026-08-22 | `71aa4fb` | Keep record keys outside SQLite so deletion has a cryptographic boundary |
| 2026-08-22 | `81cf2a4` | Bind file key-store state to its authenticated filename |
| 2026-08-22 | `43de853` | Make the file key-store namespace exact before recovery |
| 2026-08-22 | `a3a780b` | Close persistence recovery gaps before ledger integration |
| 2026-08-22 | `a974418` | Make authenticated encrypted history authoritative before cognition persists |
| 2026-08-22 | `be4313c` | Harden every ledger connection before reading state |
| 2026-08-22 | `75a930b` | Prevent deleted or rolled-back cognition from being silently reclassified |
| 2026-08-22 | `a69b739` | Reject anchor rollback before recovery mutates external state |
| 2026-08-22 | `9767479` | Serialize same-process ledger file locking |
| 2026-08-25 | `7d4bfd5` | Make record-key updates independent of lifetime history |
| 2026-08-25 | `33e70b7` | Recover persistence bootstrap across atomic write crashes |
| 2026-08-29 | `e63b356` | Add fail-closed OS-keyring record storage |
| 2026-09-01 | `0f76b31` | Avoid re-verifying lifetime history when one ledger object already proved it |
| 2026-09-01 | `f5a30e0` | Measure lifetime-ledger cost before allowing higher cognition to depend on it |

### Task 1 final evidence

- Branch checkpoint: `f5a30e0d7c9e0e95a8d8a5533517a852c77e0d3c`.
- Task 1 progress ledger records Tasks 0–9 CLEAN, including 523/523 tests on
  CPython 3.13.5, Ruff, scoped Pyright, compileall, whole-branch diff review,
  independent code/architecture/completion verdicts, and a real 8,192 x
  512-byte encrypted-ledger scale run.
- Retained scale artifact: `results/cognition_ledger_scale.json`; it reports
  `success: true`, two full verifications, bounded RSS/disk, and no duplicates.
- Honest proof scope: current Windows host. Cross-platform and physical
  power-loss claims remain later gates.

## 2026-09-02 — Task 2 transition resumed

### Request and scope

- Resume exactly at the Task 2 transition and preserve the established roadmap.
- New binding user requirement: keep repository-resident trajectory evidence
  for every change so context loss cannot erase the work path.
- Task 2 remains memory substrate, not final weight learning. Tasks 6–7 own
  plastic proposals/transactional learning; Tasks 10–12 own the native model,
  conversion/training, and real held-out learning experiments.

### State inspected before this change

- Branch: `codex/unified-lifelong-cognition`.
- HEAD: `f5a30e0`; no commits existed after the Task 1 gate.
- The only intended untracked product artifact was the 1,152-line Task 2 plan.
- `.omc/` contained local generated orchestration/session metadata and is now
  excluded together with `.omx/`; nothing in either directory was deleted.
- No Task 2 production or test module existed yet.

### Plan status

- The Task 2 plan specifies Tasks 2.0–2.8: strict observation contracts,
  storage-pure ingestion and direct exact recall, deterministic segmentation
  and replay, bounded approximate recollection, calibrated selective recall,
  immutable reconsolidation, E2E/scale/portability evidence, and a final
  independent gate.
- Earlier conversational reviews were useful context but are not sufficient
  durable proof after this continuity-rule edit. The modified plan must receive
  fresh sequential architect and critic approvals before implementation.

### Verification debt carried into the freeze

- A prior Python 3.12 full-suite attempt exposed a transient keyring test-fixture
  initialization race; targeted reruns later passed. A subsequent Python 3.13
  full run was interrupted before its one visible failure produced a traceback.
- Therefore the Task 2 plan freeze requires a fresh complete CPython 3.13 suite
  and a focused cross-version race audit. An interrupted run is not a pass and
  will not be used as gate evidence.

### This logical change

- Added this tracked trajectory ledger and its append-only continuity contract.
- Added the continuity invariant to the global roadmap and Task 2 execution
  loop.
- Added `.omc/` and `.omx/` to `.gitignore` so local orchestration metadata does
  not become repository evidence by accident.
- No Task 1 implementation file and no Task 2 production file was modified.

### Exact next action

1. Freeze and hash the changed planning set.
2. Obtain a fresh architect approval, then a fresh critic approval in that
   order, against the same hash.
3. Re-run the authoritative CPython 3.13 baseline and diagnose any failure;
   run focused Python 3.12 race evidence without weakening the target.
4. Record results here, commit the Task 2.0 planning checkpoint, and begin Task
   2.1 with real RED observation-contract tests.

### Task 2.0 gate execution started

- Frozen Task 2 plan SHA-256:
  `7E9404D91D41A66AB2B27840AD4A33F4A6DFD9CA2E2EBBE9295E2C68CE24936A`.
- Frozen global roadmap SHA-256:
  `950126478A4198334B71328282A23C404142A8A28BDB7957BC9F997F1DB79050`.
- Autopilot resumed in `ralplan`; its local state records the plan, trajectory,
  hashes, completed requirements clarification, and pending sequential
  consensus gate.
- A fresh requirements mapper and first-stage architect were dispatched against
  the exact frozen hashes. The critic will run only after architect approval.
- A separate test-engineering lane was dispatched for focused Python 3.12/3.13
  keyring/short-write race evidence. The controller owns the full Python 3.13
  baseline so duplicate full-suite processes cannot skew the result.
- No production code was changed. The gate is `IN_PROGRESS`.

### Current host profile captured

- OS: Microsoft Windows 11 Pro, build 26200, AMD64.
- CPU: Intel Core i7-12650H, 10 physical / 16 logical cores.
- RAM: 16,866,508,800 bytes (about 15.7 GiB).
- GPU inventory: NVIDIA GeForce RTX 4050 Laptop GPU, 6,141 MiB, driver
  610.62. Task 2 baseline code does not use the GPU.
- Authoritative interpreter: CPython 3.13.5 with SQLite 3.49.1.
- Diagnostic compatibility interpreter: CPython 3.12.13 with SQLite 3.53.1.
- The hardware profile matches retained Task 1 evidence; the Python 3.12/SQLite
  pair is a distinct software profile and is treated as diagnostic evidence,
  not silently conflated with the accepted 3.13 baseline.

### Task 2.0 requirements review

- Reviewer: native analyst `/root/task2_requirements_gate`.
- Reviewed exact Task 2 plan hash:
  `7E9404D91D41A66AB2B27840AD4A33F4A6DFD9CA2E2EBBE9295E2C68CE24936A`.
- Reviewed exact roadmap hash:
  `950126478A4198334B71328282A23C404142A8A28BDB7957BC9F997F1DB79050`.
- Verdict: `APPROVE`; no material requirements gap.
- Confirmed that the tracked trajectory requirement is binding, Task 2 delivers
  a real observation-to-restart-to-exact-recall path, and permanent learning is
  still owned by Tasks 6–7 and 10–12 rather than silently removed.
- Remaining gate: architect approval, then critic approval against the same
  frozen plan hash, plus clean baseline evidence.

### Task 2.0 architecture review cycle 1

- Reviewer: native architect `/root/task2_architect_gate`.
- Reviewed Task 2 plan hash:
  `7E9404D91D41A66AB2B27840AD4A33F4A6DFD9CA2E2EBBE9295E2C68CE24936A`.
- Verdict: `BLOCK` with one compatibility-critical wording defect. The plan's
  phrase “export the approved Task 2 public types only” could be implemented as
  removing existing Task 1 re-exports from `aluclu.cognition`, which would also
  break top-level package consumers.
- Repair: the plan now requires all Task 1 imports and `__all__` members to be
  preserved behavior-compatibly, with Task 2 exports strictly additive and a
  dedicated RED compatibility oracle.
- Review cleanup: `.superpowers/sdd/` was already ignored locally by its own
  `.gitignore`; root `.gitignore` now records that exclusion durably so a clean
  clone preserves the same evidence boundary.
- Consequence: the previous plan hash and its requirements approval are stale.
  The modified plan must be rehashed and receive fresh requirements, architect,
  then critic review. No critic was started and no production code changed.

### Task 2.0 focused baseline race audit

- Reviewer: native test engineer `/root/baseline_race_audit`; repository files
  were not modified by the reviewer.
- CPython 3.13 and 3.12 each passed current short-write completion/cleanup tests
  and focused two-ledger/keyring process-race tests.
- The strongest combined race commands passed 3/3 under each interpreter in
  148.17 seconds (3.13) and 161.88 seconds (3.12).
- `.pytest_cache` still named
  `test_file_key_provider_posix_short_write_cleans_partial_secret`, but that
  node no longer exists; current split completion/zero-write/write-error/fsync
  tests passed. The cache entry is stale evidence, not a current failure.
- Residual test-health risk: isolated
  `test_two_ledger_objects_sustain_concurrent_append_streams` passed but showed
  a greater-than-five-minute long tail in one repeat. This is not evidence of
  corruption, but final Task 2 gating must improve timeout diagnostics or split
  deterministic and slow stress coverage without weakening the behavior.
- Controller-owned full CPython 3.13 baseline remains live; focused passes do
  not substitute for its final result.

### Task 2.0 protocol freeze audit and repair cycle 2

- A read-only Task 2.1 API mapper confirmed that the intended architecture was
  sound but the prior plan hash still left wire-level choices to an executor.
  Literal fixtures could not honestly be RED until schemas, enum wire values,
  byte bounds, digest domains, deep JSON immutability, feature bytes, whitespace
  handling, and Unicode-profile behavior were frozen.
- A separate pre-freeze critic independently rejected implementation readiness
  for the same class of omissions. This was not the formal post-architect critic
  gate and is recorded as design feedback, not an approval.
- The Task 2 plan now freezes the observation/provenance/boundary wire schemas,
  exact ID and collection limits, null-versus-empty rules, canonical decoder
  discipline, domain-separated hash bytes, 262,144-byte envelope boundary,
  immutable canonical-content wrapper, 4,096-byte raw and normalized text
  boundaries, whitespace-run semantics, signed byte-ngram representation,
  UCD-versioned compatibility IDs, and protocol-manifest structure.
- The plan now assigns `recall_features.py` to Task 2.1 because its literal
  feature-vector RED oracle cannot precede ownership of that implementation.
  `TIME_REVERSED_INVALID` is explicitly a later stateful ingestion rejection,
  never a persisted boundary reason or a Task 2.1 numeric-shape oracle.
- No production or test code changed. All earlier Task 2 plan hashes and review
  verdicts remain stale. A focused state/receipt contract audit is still in
  progress before the next immutable hash is declared.

### Task 2.0 authoritative baseline rerun

- Command: `.venv313\Scripts\python.exe -m pytest
  --junitxml=.superpowers/sdd/2026-09-02-task-2-sensorium-recollection/task-2-0-baseline-py313.xml`.
- Result: `523 passed`, zero failures, zero errors, zero skips, one warning, in
  1,316.09 seconds (`pytest` JUnit time 1,315.930 seconds).
- The sole warning is Pytest's known notice that `record_property` in the real
  platform keyring smoke test is incompatible with JUnit family `xunit2`; it is
  evidence-formatting debt, not a product or test failure.
- The ignored 82,047-byte JUnit artifact records this run. This closes the
  interrupted-baseline uncertainty carried into Task 2.0; the separately noted
  concurrency-test long tail remains test-health debt for the final Task 2 gate.

### Task 2.0 state-contract repair cycle 3

- The focused state-contract audit proved a real construction cycle in the
  superseded plan: a stored `post_state_digest` covered a Task 1 checkpoint whose
  head hash would be the hash of that same encrypted observation record. Task 1
  record hashes also depend on randomized encryption material, so this was not
  computable before append and could not be solved by iteration.
- The plan now separates digestible `SensoriumCoreStateV1` from the outer
  `SensoriumStateV1` Task 1 checkpoint wrapper. Stored observations contain the
  bounded post core plus pre/post core digests; the unpredictable checkpoint is
  bound only after append. The post core is retained so replay can advance from
  surviving authenticated records without reconstructing shredded content.
- A second boundedness defect was closed at the same time: 32 maximum-length
  goal IDs plus 32 participant IDs cannot fit a 4 KiB state. Core state now
  holds fixed-size, domain-separated signal digests while each full ID array
  remains only in its encrypted observation request.
- Episode byte accounting now sums canonical request bytes, not a stored
  envelope containing its own resulting counter; this removes a size
  fixed-point while retaining the independent 262,144-byte envelope ceiling.
- Receipt, accepted/rejected ingest, completed/incomplete replay, core-state,
  and checkpoint-wrapper shapes are explicit closed versioned contracts. The
  duplicate exactly-one-behind rule now states the active-head and pre-append
  hash requirements needed to converge without accepting an arbitrarily stale
  checkpoint.
- Baseline static evidence after these planning-only edits: repository Ruff
  passed and CPython 3.13 `compileall -q src scripts tests` passed. Product code
  remains unchanged; a fresh immutable plan hash and formal reviews are still
  required.
- An initial over-broad Pyright 1.1.413 command omitted the interpreter binding
  and mixed all legacy cognition tests into the scope; it failed with 23
  diagnostics, dominated by unresolved `pytest` plus known baseline fixture
  annotations. This was a command/configuration failure, not a clean signal and
  is not hidden or counted as product regression evidence.
- The corrected pinned command,
  `npx --yes pyright@1.1.413 --pythonpath .\.venv313\Scripts\python.exe
  src\aluclu\cognition`, passed with 0 errors, 0 warnings, and 0 information
  diagnostics. Task 2 implementation gates will scope both new production and
  new test files explicitly with the same bound interpreter.

### Task 2.0 candidate freeze 2

- Decision-complete Task 2 plan SHA-256:
  `196B1FFFFC07B2E163AED536CC50219F461C3FAA5B4C83EDD8B033E9DDAD97E0`.
- Unchanged global roadmap SHA-256:
  `950126478A4198334B71328282A23C404142A8A28BDB7957BC9F997F1DB79050`.
- Pre-freeze checks: balanced Markdown fences, no obsolete pre/post full-state
  digest or self-counting payload field remained, and `git diff --check` found
  no whitespace error (only Git's informational future LF-to-CRLF notices for
  two existing working-copy paths).
- Formal reviews restart from zero on this hash: requirements mapping first,
  architect second, and critic only after an architect approval. Any plan edit
  invalidates all verdicts and requires a new hash/review cycle.

### Task 2.0 requirements review cycle 2

- Reviewer: fresh native analyst `/root/task2_requirements_gate2`.
- The reviewer independently recomputed and matched Task 2 plan hash
  `196B1FFFFC07B2E163AED536CC50219F461C3FAA5B4C83EDD8B033E9DDAD97E0`
  and roadmap hash
  `950126478A4198334B71328282A23C404142A8A28BDB7957BC9F997F1DB79050`.
- Verdict: `APPROVE`; no blocking missing question, guardrail, acceptance
  criterion, scope decision, or Task 2.1/2.2 executor choice remained.
- The review explicitly accepted the non-circular core/checkpoint split,
  surviving-record post-core replay without content resurrection, fixed-size
  signal digests, request-byte episode accounting, strict schema/domain/UCD
  fixtures, platform-claim boundary, early working E2E, and preservation of
  later permanent-learning work.
- Non-blocking execution cautions: keep Task 2.1 fixture-first and small, reach
  the usable Task 2.2 ingest/restart/exact-recall slice quickly, confirm package
  data rather than editing it speculatively, and retain concurrency long-tail
  debt for the final gate.
- Exact next gate: independent architecture review of the same plan hash. The
  formal critic has not started.

### Task 2.0 architecture review cycle 2

- Reviewer: fresh native architect `/root/task2_architect_gate2`.
- The reviewer's first response was only a status summary and contained no gate
  verdict; it was rejected as non-evidence and the same reviewer was explicitly
  reissued the bounded formal assignment. It is not counted as an approval.
- On the completed review, the architect independently recomputed and matched
  Task 2 plan hash
  `196B1FFFFC07B2E163AED536CC50219F461C3FAA5B4C83EDD8B033E9DDAD97E0`
  and roadmap hash
  `950126478A4198334B71328282A23C404142A8A28BDB7957BC9F997F1DB79050`.
- Verdict: `APPROVE`; no architecture blocker remains. The reviewer confirmed
  the acyclic Task 2-over-Task 1 dependency, later learning ownership, live
  non-nestable verified-session/cursor-before-mutation primitives, and additive
  preservation of existing package exports.
- Residual risk is implementation evidence only: the plan is still contracts,
  so real fixture-first RED/GREEN code must prove it. Exact next gate is the
  formal critic on the identical hash; no plan byte changed after approval.

### Task 2.0 formal critic review cycle 2

- Reviewer: fresh native critic `/root/task2_critic_gate2`, dispatched only
  after the architecture approval.
- The critic independently recomputed and matched Task 2 plan hash
  `196B1FFFFC07B2E163AED536CC50219F461C3FAA5B4C83EDD8B033E9DDAD97E0`
  and roadmap hash
  `950126478A4198334B71328282A23C404142A8A28BDB7957BC9F997F1DB79050`.
- Verdict: `APPROVE`. The adversarial review found no material clarity,
  verifiability, completeness, architecture, mathematical-consistency,
  boundedness, no-resurrection, session-lifecycle, calibration/truth, or roadmap
  blocker after checking live Task 1 APIs and representative Task 2.1–2.6 paths.
- Watch items remain explicit and non-blocking: the long-tail concurrency stress
  needs final-gate diagnostics; broad cross-platform claims remain forbidden
  until the full matrix runs; Task 2.1 must stay fixture-first and Task 2.2 must
  follow quickly to deliver the working observation-to-memory path.
- The sequential planning consensus gate is now complete on one unchanged plan
  hash. Next action: controller fingerprint/check, commit Task 2.0, then begin
  Task 2.1 with actual failing contract/vector tests.

### Task 2.0 controller closeout candidate

- Intended tracked checkpoint consists only of `.gitignore`, `TRAJECTORY.md`,
  the global roadmap continuity invariant, and the reviewed Task 2 plan. No Task
  1 implementation/test file and no Task 2 production/test file is part of this
  commit.
- Final candidate hashes still match every cycle-2 reviewer: Task 2 plan
  `196B1FFFFC07B2E163AED536CC50219F461C3FAA5B4C83EDD8B033E9DDAD97E0`;
  roadmap
  `950126478A4198334B71328282A23C404142A8A28BDB7957BC9F997F1DB79050`.
- Controller evidence: CPython 3.13 full suite 523/523; focused CPython
  3.12/3.13 race gates 3/3 each; Ruff clean; compileall clean; corrected pinned
  Pyright production scope 0/0/0; `git diff --check` clean apart from two
  informational future line-ending notices.
- Gate verdict: Task 2.0 is ready to commit under subject `Freeze the Task 2
  sensorium contract before implementation`. The next logical change must first
  record this commit's resulting hash, then create and observe the Task 2.1 RED
  contract/feature fixtures.

## 2026-09-02 — Task 2.1 strict contracts started

- Task 2.0 committed as `bc20605` (`Freeze the Task 2 sensorium contract before
  implementation`), containing exactly the four declared planning/continuity
  files. The reviewed Task 2 plan hash remained `196B1FFF...97E0` at commit.
- Autopilot transitions from `ralplan` to implementation only after this clean
  checkpoint. Task 2.1 begins fixture-first: observation/core contracts and
  deterministic retrieval features are independent owned lanes, while the
  controller owns additive exports, integration, evidence, and this trajectory.
- Current expected state is RED because neither Task 2 production module nor
  its tests/protocol fixture exists yet. The next evidence entry must identify
  the exact failing test commands before any GREEN implementation is accepted.

### Task 2.1 Python signature freeze

- The reviewed plan freezes wire semantics and public operation names but does
  not prescribe two non-wire Python return/signature details needed by literal
  tests. The task brief resolves them without changing any reviewed schema or
  plan hash.
- `derive_boundary_signal_digests(request)` returns frozen, keyword-only,
  slotted `BoundarySignalDigestsV1` with exactly
  `session_signal_digest`, `goal_ids_signal_digest`,
  `participant_ids_signal_digest`, `tool_signal_digest`, and
  `topic_signal_digest` attributes.
- `build_canonical_observation` is keyword-only over `request`,
  `boundary_decision`, `pre_core_state_digest`, `post_core_state`,
  `pre_append_head_sequence`, `pre_append_head_hash`, and
  `boundary_profile_id`; it computes request/content/post-core digests itself.
- `derive_episode_id` is keyword-only over `boundary_profile_id`,
  `first_observation_id`, and `session_id`.
- These choices remove test-author guesswork while preserving the approved wire
  contract. Both RED lanes remain test/fixture-only at this point.
- A feature-bound proof found that 4,096 normalized bytes plus the four framing
  bytes emit at most 12,291 total 3/4/5-grams. Therefore a single bin cannot
  reach the symmetric ±32,767 saturation boundary through any valid v1 public
  input, even under a total collision. The mandated sum-then-clamp rule remains
  a defensive invariant and is tested through private pure helper
  `_saturate_feature_bin(total)`, exactly
  `max(-32767, min(32767, total))`, plus the public 12,291-gram bound oracle.

### Task 2.1 RED fixture exposed plan contradiction

- While materializing the literal protocol JSON, the feature RED lane found a
  real contradiction in reviewed plan hash `196B1FFF...97E0`: a stable search
  vector had one `bins_i16be_digest`, but `feature_vector_digest` intentionally
  binds a `feature_spec_id` whose suffix changes with UCD 13.0/14.0/15.0/15.1.
  Identical bin bytes therefore require four different feature-vector digests.
- No implementation workaround is accepted. The plan now requires
  `feature_vector_digest_by_unidata_version` with all four exact UCD keys for a
  stable vector, and singular `feature_vector_digest` inside each already
  version-scoped assignment case. This preserves the approved feature identity
  definition rather than weakening it to an unversioned raw-bin hash.
- Consequence: Task 2.0 is reopened, all reviews of `196B1FFF...97E0` are stale,
  and implementation is paused. This is the intended value of fixture-first
  RED: the contradiction was discovered before a production API encoded it.
- Next action: compute a new plan hash, repeat requirements -> architect ->
  critic on that exact hash, then resume the two existing RED lanes.
- The feature RED lane found no second contradiction. Its pending literal tests
  distinguish both byte caps with `U+0958`: 682 repetitions are raw 2,046
  bytes/NFC 4,092 bytes and accepted; 683 are raw 2,049/NFC 4,098 and rejected.
  Independent boundary vectors reject 4,097 raw whitespace bytes even though
  search normalization is one byte, and accept exactly 4,096 ASCII bytes.
- The observation RED draft found no second plan contradiction. It locks the
  source, provenance, request, content, boundary, core, digest, persisted
  envelope, and additive-export contracts using the exact Python signature
  brief above; focused RED evidence is still pending.
- Corrected Task 2 plan candidate SHA-256 is
  `01669B9DE8FF941E690FB0624E8611684FCB847692C720539BA615141EC98357`.
  `git diff --check` is clean apart from Git's informational LF-to-CRLF warning.
  The requirements, architecture, and critic gates must each approve this exact
  hash; none of the superseded `196B1FFF...97E0` verdicts carry forward.
- Observation RED lane completed with only
  `tests/test_cognition_observation.py`: 37 test definitions / 1,278 lines.
  CPython 3.13 `py_compile` and `git diff --check` passed. Focused pytest exited
  1 during collection with exactly one expected error and zero tests executed:
  line 15 cannot import the not-yet-created `aluclu.cognition.observation`
  module. This is accepted RED evidence, not a product failure; production code
  remains paused until the corrected plan is reapproved.
- Requirements gate 3 independently matched corrected plan hash
  `01669B9D...8357` and roadmap hash `95012647...9050`, and found the per-UCD
  digest repair implementable, but returned BLOCK because the first trajectory
  entry incorrectly said 1,134 lines. The controller independently counted 37
  `def test_...` definitions and 1,278 physical lines, corrected the evidence
  above, and preserves this failed gate in the history. The plan did not change,
  so the same requirements reviewer must now re-evaluate the same exact hash.
- Requirements gate 3 rerun: APPROVE. The reviewer independently confirmed the
  unchanged full Task 2 hash, roadmap hash, 1,278 physical lines, 37 literal
  tests, clean diff-check/`py_compile`, expected missing-module RED, and the
  corrected stable-vector versus version-scoped assignment digest semantics.
  No requirements ambiguity remains. Architecture review is now authorized on
  this exact hash; critic review remains unauthorized until architecture passes.
- Architecture gate 3 first response is not accepted as a formal verdict. It
  reported architectural status `CLEAR` and useful file/API evidence, but did
  not return the required literal `APPROVE`/`BLOCK` verdict or independently
  state both computed full hashes. As in the earlier architecture cycle, useful
  commentary is not consensus evidence. The same read-only reviewer is reissued
  the gate; critic remains unauthorized.
- Architecture gate 3 reissue: APPROVE. The reviewer independently matched Task
  2 hash `01669B9D...8357` and roadmap hash `95012647...9050`, then verified the
  pure API surface, per-UCD digest repair, Task 2.2--2.8 path, additive Task 1
  exports, caller-owned session/cursor discipline, and RED oracles against live
  files. No structural blocker remains. The final sequential critic gate is now
  authorized on these exact hashes.

## 2026-09-03 — Resume after critic infrastructure interruption

- The first Task 2 critic gate 3 dispatch produced no review verdict or plan
  finding. Its agent turn terminated at the account usage limit, so it is
  recorded as interrupted infrastructure evidence and cannot count as APPROVE
  or BLOCK. The paused feature RED agent ended for the same external reason and
  created or edited no owned file.
- The user-supplied `a2.txt` history and this repository ledger were reread as
  context, with this tracked ledger remaining authoritative. Live Git state is
  still branch `codex/unified-lifelong-cognition` at `bc20605`, with only the
  Task 2 plan repair, this trajectory, and the observation RED test pending.
- The controller recomputed Task 2 plan SHA-256 as
  `01669B9DE8FF941E690FB0624E8611684FCB847692C720539BA615141EC98357`;
  it is unchanged from the requirements and architecture approvals. Roadmap
  hash remains `950126478A4198334B71328282A23C404142A8A28BDB7957BC9F997F1DB79050`.
  `git diff --check` still exits clean with only informational LF-to-CRLF
  notices. Exact next action is a fresh adversarial critic review on these two
  hashes; production remains unauthorized until it explicitly approves.
- Fresh critic `/root/task2_critic_gate3_retry` independently matched the full
  Task 2 and roadmap hashes and returned `APPROVE`; no material blocker was
  found. Representative Task 2.1--2.6 simulations confirmed the closed
  observation contracts, per-UCD digest repair, live caller-owned Task 1 session
  and cursor lifecycle, bounded streaming/replay, fail-closed calibration, and
  immutable/no-resurrection reconsolidation path. The critic also verified the
  37-test/1,278-line RED file and clean diff-check.
- Non-blocking watch items remain: do not claim cross-platform proof from the
  current Windows host; retain the known concurrency long-tail test-health debt;
  and make the observation RED file part of this checkpoint only deliberately.
  The controller chooses that deliberate combined checkpoint: the plan repair
  and its already-reviewed observation RED contract form one logical transition
  into Task 2.1, while no Task 2 production file is included. Consensus is now
  complete and Autopilot may return to `ultragoal` after fresh controller checks.
- Fresh controller checks exposed two non-semantic lint defects in the RED test:
  Ruff initially exited 1 for unsorted imports and importing `Callable` from
  `typing`. The imports were repaired with the exact Ruff-proposed organization;
  no test assertion or protocol fixture changed. A second Ruff pass is clean,
  CPython 3.13 `py_compile` is clean, and the file remains 37 test definitions /
  1,278 physical lines.
- Fresh focused CPython 3.13 pytest remains intentionally RED: exit 1, exactly
  one collection error and zero executed tests, now reported at line 12 as
  `ModuleNotFoundError: No module named 'aluclu.cognition.observation'`. Both
  plan/roadmap hashes remain exact and `git diff --check` exits 0 with only the
  known informational line-ending notices.
- Checkpoint scope is exactly `TRAJECTORY.md`, the corrected Task 2 plan, and
  `tests/test_cognition_observation.py`. This deliberately combines the
  reapproved protocol repair with its observation RED oracle. No Task 1 file,
  Task 2 production module, generated bytecode, or ignored orchestration state
  is part of the commit.

## 2026-09-03 — Task 2.1 deterministic feature RED resumed

- The reapproved plan repair and observation RED committed cleanly as
  `3aa3fd8f235ac2f81e4f88485a8bc2b9555bd813` (`Repair Task 2 vectors and freeze
  observation RED`). Post-commit worktree was clean and the Task 2 plan hash
  remained `01669B9D...8357`.
- Task 2.0 is now CLEAN. Task 2.1 remains RED: observation contracts are frozen
  and fail only because production is absent; deterministic feature contracts
  and the reviewed protocol fixture are the next independent test-only lane.
- The resumed feature lane may own only
  `tests/test_cognition_recall_features.py` and
  `src/aluclu/protocols/task2_determinism_v1.json`. It must bind stable search
  vectors to all four UCD-specific feature digests, retain singular digests for
  version-scoped assignment cases, and prove the independent raw/NFC byte caps.
  It may not modify production, plans, exports, or this trajectory.
- A first read-only implementation-mapping agent failed before inspecting files
  because its role-fixed model was unsupported for the current ChatGPT account.
  This is an orchestration limitation, not code evidence; a default-model
  read-only mapper was dispatched as the bounded retry.
- With Task 2.0 consensus complete, the observation GREEN lane is authorized in
  parallel under strict ownership of only
  `src/aluclu/cognition/observation.py`. It must implement the frozen schemas,
  bounds, domains, deep immutability, core invariants, and encode/decode/build
  surface without altering tests or exports. The controller retains package
  exports and integration ownership; any plan/test contradiction reopens the
  gate instead of being papered over.
- The supported-model mapping retry completed read-only with no file changes.
  It confirmed reuse of Task 1 `InputBoundaryError`, canonical JSON primitives,
  and `validate_event_id`; exact-type validation to reject booleans; fresh
  container reconstruction for `CanonicalJsonValue`; and the permitted one-way
  dependency `observation.py -> recall_features.py`. It also confirmed that only
  `src/aluclu/cognition/__init__.py` needs additive Task 2.1 exports, while
  protocol JSON package data is already configured. The controller relayed the
  no-duplicate-normalization constraint to the observation lane.
- Observation GREEN execution exposed an impossible test-only oracle at the
  maximum goal/participant case. The frozen plan and the same test require exact
  core keys `goal_ids_signal_digest` and `participant_ids_signal_digest`, while
  the old assertions also forbade the byte substrings `goal_ids` and
  `participant_ids` anywhere in that encoding. Production was paused rather
  than weakened. Controller inspection confirmed the contradiction at the live
  test and plan schema.
- The RED oracle is repaired narrowly to forbid the complete raw-field JSON
  keys `"goal_ids":` and `"participant_ids":`; it still checks the exact core
  key set, fixed 3,072-byte cap, and absence of representative maximum-size raw
  IDs. The approved plan and its hash do not change. Observation tests must be
  rerun after the independent feature GREEN module exists.
- Deterministic feature RED lane completed under its exact two-file ownership:
  `tests/test_cognition_recall_features.py` plus canonical protocol fixture
  `src/aluclu/protocols/task2_determinism_v1.json`. It contains five stable
  search vectors, four UCD assignment groups, per-UCD stable-vector digests,
  singular version-scoped assignment digests, framed-domain probes, independent
  raw/NFC caps, the 12,291-gram bound, and private saturation oracle.
- Controller RED reproduction: CPython 3.13 `py_compile`, Ruff, and JSON parsing
  all exit 0; focused pytest exits 1 with exactly one collection error and zero
  tests executed because `aluclu.cognition.recall_features` does not yet exist.
  A GREEN worker is authorized with sole ownership of that production module.

## 2026-09-06 — Resume Task 2.1 integration and independent acceptance

- Previous goal turn made progress: observation and feature production modules,
  deterministic fixture/tests, and additive cognition exports now exist. The
  last controller focused integration run passed; import ordering and formatting
  remained unfinished. The feature author reported 23 tests passing on each of
  CPython 3.12 and 3.13, then hit the usage limit before delivering its final
  independent review. No review verdict is inferred from that interruption.
- Resume checked live Git at `3aa3fd8` against both user-supplied history files
  and this ledger. Seven changed/untracked files comprise the Task 2.1 work.
  The approved Task 2 plan still hashes to
  `01669B9DE8FF941E690FB0624E8611684FCB847692C720539BA615141EC98357`.
- Controller applied Ruff import fixes and formatting only to the five Task 2.1
  Python files. The earlier import-order churn arose while new modules were
  absent; imports are now resolved against the complete implementation. No
  assertions, algorithms, or plan acceptance thresholds changed in this cleanup.
- Next acceptance uses fresh focused/full/static checks and independent
  code/spec and architecture review lanes. Task 2.1 is not CLEAN yet; Task 2.2
  remains pending. Task 1's 523-test historical pass is not a new full-suite pass.
- Fresh controller focused baseline: 142 passed in 8.94 seconds. A subsequent
  repository-wide Ruff scan caught the feature-test import group; it will be
  normalized with explicit first-party classification after new files settle.
- Plan comparison found that the feature manifest and its tests agreed with
  each other but disagreed with the approved schema: dotted instead of hyphenated
  discriminator, extra algorithm metadata instead of the three exact identity
  fields, `domain_hex` instead of `domain_ascii`, and pretty rather than canonical
  bytes. Tests now assert the actual approved contract. The resulting RED is one
  collection error on noncanonical manifest bytes; schema metadata is repaired
  and the fixture will be canonicalized as a formatting operation.
- A separate regression proved that `CanonicalJsonValue()` created an
  uninitialized exact-type instance (1 failed, 118 deselected). An explicit
  constructor guard now requires the existing validating factory methods;
  those factories continue to allocate through `object.__new__` internally.
- Assignment-vector verification now evaluates production accept/reject only
  for the active real UCD. Other profiles' literals are checked from their
  declared bytes, avoiding normalization of future-assigned characters on an
  older runtime. An independent test worker owns subprocess identity proofs
  across hash seeds/timezones; this fills a specified Task 2.1 evidence gap.
- Additional fixture coverage regressions failed for an unregistered
  normalizer-ID digest domain and missing Turkish/Arabic/CJK/composed-text/
  maximum-length literal cases (2 failed, 22 deselected). The fixture now has
  11 stable cases, including 4,096-byte ASCII, and replaces the invented domain
  probe with a registered content-identity probe. Literal outputs were calculated
  using the test-side independent stdlib normalization/gram/digest functions,
  then written via patch and canonically formatted. No production function was
  used to compute those expected values.
- Post-constructor/schema repair focused checks passed on both installed
  runtimes: 142 in 4.66 seconds (3.13) and 142 in 7.82 seconds (3.12).
  Repository Ruff passed and pinned Pyright 1.1.413 on cognition with the 3.13
  interpreter reported 0 errors/warnings/informations. New fixture-coverage and
  subprocess additions will be included in the subsequent combined run.
- Expanded feature suite: 42 passed in 14.53 seconds. Subprocess evidence worker
  initially reported 11 passes per installed interpreter. Controller inspection
  found two proof limitations: synthetic package-loading bypassed normal imports,
  and NFC/NFD content changed a label as well as codepoints. Requested ordinary
  production imports with a compatible child environment and identical metadata
  across Unicode variants; the worker is correcting only its two owned files.

## 2026-09-06 — Resume after status-only pause

- User authorized continuation. Live native-agent inventory contains only the
  controller; prior worker/review sessions cannot be resumed. Worktree remains
  on `3aa3fd8`, with the frozen Task 2 plan hash unchanged. Ordinary-import
  subprocess corrections and identical NFC/NFD metadata survived in both files.
- Prior independent `/root/task21_acceptance_code` returned REQUEST CHANGES on
  one MEDIUM test-helper typing issue. Fresh local Pyright reproduced exactly
  one `fields(object)` error at `tests/test_cognition_observation.py:320`.
  Autopilot records a bounded repair-plan return, without reopening the parent
  protocol decisions. The repair plan also covers a missing explicit 4,096-byte
  exhaustive checkpoint-wrapper size assertion required by Task 2.1.
- Fresh 3.13 process/hash-seed/TZ-setting tests: 11 passed in 69.45 seconds.
  Observation plus expanded feature tests: 161 passed in 3.84 seconds. These
  are focused checks, not full-suite or cross-platform approval.
- Independently recalculated NFC/NFD content hashes using only stdlib canonical
  JSON and domain framing; both match the worker's fixed expected literals.
  Initial console printing failed under cp1254 for a combining character;
  ASCII-escaped diagnostic output succeeded. This was a display issue only.
- New independent code/spec review is active; bounded repair-plan Architect
  review precedes Critic. No Task 2.2 implementation or CLEAN claim is made.
- Sequential repair reviews `/root/task21_repair_arch` then
  `/root/task21_repair_critic` both returned APPROVE. The controller resumed
  implementation under that bounded handoff: explicit dataclass-instance
  narrowing fixes the reproduced static error; the maximum-set test now uses
  maximum core fields and the exact four-field exhaustive Task 1 checkpoint
  wire shape, including worst-case ledger-ID JSON escaping. Read-only pre-edit
  measurement was 1,177 core bytes / 2,964 wrapper bytes. The missing assertion
  is an evidence gap, not a claimed runtime RED failure. Parent plan unchanged.
- Fresh independent code review `/root/task21_code_review` found only those
  same two MEDIUM items (REQUEST CHANGES); no production defect was reported.
  Its 172 focused checks passed. Controller 3.12 subprocess matrix also passed
  11 tests in 74.01 seconds. Required post-repair checks and full suite follow.
- Applied formatting to four changed test/helper files (three production files
  already formatted). The first post-edit static run confirmed the original
  helper error was gone and caught a new test-only `set(JsonValue)` mismatch
  in the added wrapper assertion; an explicit decoded-dict assertion narrows
  that value without suppressions or changing the expected wire contract.
- Post-repair expanded Pyright (all cognition plus all Task 2.1 test/helper
  files) is clean: 0 errors, 0 warnings, 0 informations. Controller observation
  and feature tests: 161 passed in 3.03 seconds. Repository Ruff, seven-file
  format check, compileall over src/tests, and diff check all passed (Git emits
  only its existing CRLF conversion warnings).
- Independent architecture implementation lane `/root/task21_repair_arch`
  returned CLEAR: one-way pure module dependencies, additive exports, no ledger
  or session access, and no checkpoint self-hash cycle. Code reviewer is now
  verifying the repaired two findings. Full 695-test 3.13 suite is running with
  a durable JUnit output path; final 172-test 3.12 focused suite also running.
- Final 3.12 focused rerun: 172 passed in 67.09 seconds. Independent code
  re-review `/root/task21_code_review` now APPROVE with zero findings, including
  its own pinned Pyright0/0/0 and repaired-test rerun. This combines with CLEAR
  architecture for the current candidate; committed-diff refresh/full-suite
  exit evidence are still required before CLEAN.
- Prepared a retained ignored UltraQA matrix/harness for the pure public
  pipeline: hostile model text stays data, mutation isolation, canonical
  observation roundtrips, Unicode feature equivalence, malformed-wire rejection,
  and audit-hook denial of filesystem/network/process effects. No product
  cancel/state/ledger behavior is claimed for these pure Task 2.1 APIs.
- UltraQA dynamic harness exited0 on 3.13 (4.47s) and 3.12 (4.63s): each
  performed50 observation roundtrips with hostile-looking model content,
  original/returned-container mutation, and NFC-equivalent feature checks;
  rejected8 malformed inputs; audited zero filesystem/network/process effects
  during pure operations. No fixes needed. Harness/matrix remain intentionally
  ignored local reproducibility evidence; no child process or external state
  remains from those probes. Full regression is still running.
- The interrupted terminal handle was unavailable after the session/model
  transition, so no terminal-success inference was made. Its durable JUnit
  artifact was parsed directly: the CPython 3.13 full repository suite finished
  with 695 tests, 0 failures, 0 errors, 0 skips in 1,104.465 seconds, timestamped
  2026-09-06T21:01:16.767708+03:00. Task 2.1 now has clean focused, full,
  static, deterministic-process, dynamic-QA, code-review, and architecture
  evidence for the precommit candidate. The next mandatory gate is an owned-file
  commit followed by fresh base-to-head review; Task 2.2 remains unstarted.
