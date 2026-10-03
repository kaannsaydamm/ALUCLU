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
| 2 — sensorium/recollection | TASK 2.0–2.2 CLEAN / 2.3 NEXT | `be08f41`; corrected plan hash `01669B9D...8357` | Write deterministic segmentation/bounded replay RED oracles |
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
- Task 2.1 implementation was committed as
  `03a2792ddd7ca1d385932ad611746ca1acbeb060` (`Establish deterministic Task 2
  observation contracts`), containing exactly nine owned files. The worktree
  was clean immediately after the commit.
- Fresh postcommit review used the exact diff
  `3aa3fd8f235ac2f81e4f88485a8bc2b9555bd813..03a2792ddd7ca1d385932ad611746ca1acbeb060`.
  Independent code/spec/security reviewer `/root/task21_code_review` returned
  APPROVE with zero CRITICAL/HIGH/MEDIUM/LOW findings after independently
  confirming the plan hash, wrapper sizes, canonical manifest, Pyright, Ruff,
  compileall, clean worktree, and retained full/QA evidence. Independent
  architecture reviewer `/root/task21_repair_arch` returned CLEAR: pure one-way
  module boundaries, additive exports, no ledger/session coupling, no checkpoint
  self-hash cycle, and no Task 2.2 compatibility blocker. Its only articulated
  tradeoff is duplicate frozen 4,096-byte caps, intentionally pinned by tests.
- Controller synthesis is therefore `APPROVE + CLEAR`; every Task 2.1 exit gate
  is clean. Task 2.1 is marked CLEAN at code checkpoint `03a2792`. No later
  functionality is inferred: storage-pure ingestion and direct exact recall are
  still unimplemented and become Task 2.2's next fixture-first RED story.

## 2026-09-07 — Task 2.2 first ingest-to-recall vertical slice

- Task 2.1 CLEAN evidence was committed in trajectory-only checkpoint
  `7c55ec030f6f60df7cf5b48ffa8311a610912581`. The Task 2.2 ignored execution
  brief freezes ownership and copies only the already-approved parent oracles;
  plan hash and architecture remain unchanged.
- Added three fixture-first RED suites for sensorium contracts/storage-pure
  receipt classification, idempotent ingestion/stale-state branches, direct ID
  exact recollection, bare-ledger rejection, and close/reopen lost-return E2E.
  Production `sensorium.py` and `recollection.py` do not exist yet; the next
  command must demonstrate the expected missing-module collection RED before
  any implementation begins.
- Controller reproduced the intended RED: three collection errors, one for
  missing `aluclu.cognition.sensorium` and two for missing recollection imports;
  no tests executed. Test-only Ruff then identified three missing-module import
  groupings and one unused variable; mechanical import repair and removal kept
  the product RED unchanged.
- Implemented the minimum first vertical slice in new `sensorium.py` and
  `recollection.py`: immutable baseline profile/state/receipt/result contracts,
  real Task 1 tail checkpoints, pure boundary transition, storage-pure receipt
  classification, one-append NEW ingestion, duplicate convergence, typed
  conflict/tombstone/state/replay rejection, and direct authenticated ID recall.
  Initial focused GREEN was 12 passed in 21.10 seconds.
- Adversarial acceptance was then extended RED-first for exact returned wire
  schemas, forged populated core state, a single request larger than its episode
  budget, caller-owned-session verification reuse, and a valid-looking
  observation stored at the wrong ledger sequence. The missing converter import
  produced the expected one collection error. Production now validates live
  state lineage against its last authenticated observation, binds stored
  observation pre/post sequences to the enclosing ledger record, enforces the
  per-request profile byte limit, and serializes exact receipt/accepted/rejected/
  bootstrap shapes. Additive root exports are included.
- Current Task 2.2 focused suite: 17 passed in 26.29 seconds. This is a GREEN
  implementation checkpoint, not CLEAN: scoped static checks, broader Task 2
  regression, full suite, crash-process evidence, and independent review remain.
- Static checkpoint after root exports: repository Ruff and six-file format
  checks passed; scoped Pyright 1.1.413 reported 0 errors/warnings/informations;
  compileall passed. Added a real subprocess-loss oracle: a child process loads
  the pre-append state, performs normal ingestion, and exits with code 91 only
  when constructing the post-append return value. The parent must reopen, retry
  from the same old state, observe DUPLICATE, retain one live event, and recall
  identical canonical content. Its result is pending; no crash-pass claim yet.
- Controller RED run produced exactly three collection errors: missing
  `aluclu.cognition.sensorium` and `aluclu.cognition.recollection`; no tests
  executed. Pre-implementation Ruff found three import-order defects (fixed
  mechanically) and one unused test variable (removed). These are test hygiene
  corrections only; the intended missing-production-module RED remains valid.
- The real subprocess lost-return oracle passed: the child completed the normal
  append path and exited with code 91 before returning acceptance; the parent
  reopened the ledger, retried from the original state, received DUPLICATE,
  retained exactly one live event, and recalled identical canonical content
  (1 passed in 10.67 seconds). No mocked persistence boundary is claimed.
- Added the second sequential NEW observation acceptance case. It proves the
  same episode advances to observation count 2, emits the CONTINUE boundary
  reason, keeps the encoded continuation state within 4,096 bytes, and stores
  exactly two events. A patch-placement defect initially split the existing
  duplicate-retry test; inspection caught and mechanically repaired it before
  execution. The combined CPython 3.13 Task 2 suite is now 191 passed in 92.87
  seconds, including the subprocess crash/reopen oracle. Task 2.2 remains GREEN,
  not CLEAN, pending the 3.12 mirror, full repository suite, and independent
  review.
- The CPython 3.12 interpreter survived the reboot under `.venv` rather than
  the stale `.venv312` path. The stale command failed before test collection;
  after resolving the actual runtime as Python 3.12.13, the same 191-test Task
  2 suite passed in 98.83 seconds. This is environment-path evidence, not a
  product failure.
- Repository Ruff, seven-file format check, compileall over `src`/`tests`,
  `git diff --check`, and scoped Pyright 1.1.413 all passed; Pyright reported 0
  errors, 0 warnings, and 0 informations. Added two focused fail-closed oracles:
  wrong-position valid-looking observations classify as CONFLICT as well as
  failing exact recall, and an exactly-one-behind duplicate with a forged
  pre-core digest returns STATE_CONFLICT without a second write. Both targeted
  tests passed (2 passed in 6.65 seconds). The dual-runtime combined rerun is
  next; independent architecture review is CLEAR and code review is pending.
- Final expanded Task 2 focused reruns are clean on both installed interpreters:
  CPython 3.13 passed 192 tests in 114.60 seconds and CPython 3.12.13 passed 192
  tests in 116.63 seconds. Independent code/spec/security review returned
  APPROVE with zero CRITICAL/HIGH/MEDIUM/LOW findings and independently reran
  the 20 Task 2.2 tests (20 passed in 43.12 seconds), Pyright 0/0/0, Ruff,
  compileall, and diff-check. Independent architecture review returned CLEAR:
  session ownership remains caller-controlled, sensorium/recollection ownership
  is one-way, root exports are additive, and no Task 2.3+ blocker was found.
  The final precommit full CPython 3.13 repository regression is now running
  with retained JUnit output; no CLEAN claim is made until it exits successfully.
- The first full repository run was not clean: 714 passed and one pre-existing
  Task 1 process-race fixture failed in 1,248.03 seconds. The failure was outside
  Task 2.2: two child processes concurrently initialized the same fake keyring
  SQLite vault and one received `database is locked` at `PRAGMA
  journal_mode=WAL`. The failed run's JUnit artifact is retained. An immediate
  isolated rerun passed, followed by six unchanged isolated repetitions, which
  established a low-probability fixture-startup race rather than a sensorium or
  recollection semantic failure. CLEAN remained blocked.
- Applied a narrowly scoped test-infrastructure repair in
  `tests/_keyring_master_race_worker.py`: fake-vault connection setup now retries
  only SQLite `locked`/`busy` errors with the fixture's existing bounded deadline,
  closes each failed connection, and re-raises every other OperationalError or
  deadline expiry. Production keyring/persistence code is unchanged. Ruff,
  format, compileall, and Pyright 1.1.413 (0/0/0) passed for the helper; the
  repaired real two-process race passed eight consecutive isolated runs. A fresh
  full-suite pass and independent review of this additional file are mandatory.
- The second full repository run again finished 714 passed/1 failed, this time
  in 1,200.74 seconds and at a different pre-existing Task 1 harness boundary.
  The repaired keyring race passed. One bootstrap-crash child exceeded its fixed
  20-second `subprocess.run` budget under full-suite load and raised
  `TimeoutExpired`; the exact parameter passed in 3.79 seconds immediately when
  isolated. No recovery-state, exit-code, integrity, or Task 2.2 assertion
  failed. This second failed JUnit artifact is retained separately.
- Centralized the nine duplicated 20-second subprocess limits in
  `tests/test_cognition_crash_recovery.py` as a 60-second test-only budget. This
  accommodates slower Windows/OneDrive/antivirus scheduling while preserving a
  finite deadlock detector and every semantic crash-recovery assertion. Ruff
  also mechanically normalized three pre-existing formatting sites now that the
  file is in the candidate diff. The combined crash-recovery plus keyring-race
  package passed all 33 tests in 108.25 seconds; Ruff, format, compileall, and
  Pyright 0/0/0 are clean. A third full-suite pass remains mandatory.
- The third CPython 3.13 full repository run is clean: 715 passed, 0 failed,
  0 errors, and 0 skipped in 1,070.14 seconds. The retained JUnit was parsed
  independently as 715/0/0/0 with suite time 1,067.358 seconds, timestamp
  2026-09-07T22:13:43.480623+03:00, host `Kaan`. The only warning is the
  pre-existing pytest xunit2 `record_property` compatibility warning; it is not
  a failed product or acceptance assertion.
- Final candidate static gates are clean: repository Ruff, nine-file format
  check, compileall over `src`/`tests`, and `git diff --check` passed (Git emits
  only existing CRLF conversion notices); scoped Pyright 1.1.413 reports 0
  errors/warnings/informations. The repaired crash-recovery plus keyring-race
  package also passed all 33 tests under CPython 3.12.13 in 122.07 seconds.
  Task 2.2 is precommit-green; owned-file commit plus fresh committed-diff review
  remain before CLEAN.
- Final precommit independent code/spec/security re-review returned APPROVE with
  zero findings across the ten-file candidate. It specifically confirmed that
  fake-vault reconnect is limited to bounded `locked`/`busy` setup errors,
  failed connections close, other/deadline errors re-raise, and the centralized
  60-second child timeout preserves every crash exit/state/integrity assertion.
  The reviewer independently obtained Pyright 0/0/0, Ruff/compileall/diff clean,
  and 33/33 affected crash/keyring tests in 115.25 seconds. Architecture remains
  CLEAR. The candidate is approved for an exact owned-file commit; postcommit
  base-to-head review is still required before marking Task 2.2 CLEAN.
- Task 2.2 implementation was committed as
  `be08f4122643314029a0455e3d4459e25196ff5d` (`Build Task 2 ingest and exact
  recall slice`): exactly ten expected files, 2,235 insertions/18 deletions, and
  a clean worktree. Fresh review used the immutable exact range
  `7c55ec030f6f60df7cf5b48ffa8311a610912581..be08f4122643314029a0455e3d4459e25196ff5d`.
- Exact postcommit code/spec/security review returned APPROVE with zero findings,
  independently confirmed the ten-file scope/no drift/plan hash, and reran the
  committed Task 2.2 focused suite (20 passed in 22.47 seconds), Pyright 0/0/0,
  Ruff, and diff-check. Exact postcommit architecture review returned CLEAR:
  caller-owned session and one-way sensorium/recollection ownership remain
  intact; checkpoint/digest guards, additive exports, and test-infrastructure
  repairs create no Task 2.3 blocker.
- Controller synthesis is `APPROVE + CLEAR` on the exact committed diff, with
  dual-runtime Task 2 evidence, retained RED artifacts, a clean 715-test full
  suite, and clean static gates. Task 2.2 is therefore CLEAN at `be08f41`.
  Task 2.3 is next: fixture-first deterministic boundary precedence, typed time
  reversal, bounded paged replay, frozen-head continuation, 8,192-observation
  state bounds, shred-safe replay, and partition/restart byte identity. No Task
  2.3 implementation is claimed yet.

## 2026-09-07 — Environment attribution correction

- User clarified that the repository's `OneDrive\Desktop` path is a historical
  Windows Desktop redirection artifact caused by an old configuration mistake;
  it is not evidence that OneDrive synchronization is active or contributed to
  test latency. Earlier trajectory wording that listed OneDrive as a possible
  scheduling/load factor was unsupported and must not be treated as a root-cause
  finding. The evidence supports only this narrower conclusion: one child
  process exceeded a fixed 20-second harness budget during a full-suite Windows
  run, passed in 3.79 seconds when isolated, and the finite 60-second test budget
  subsequently passed the full suite. No specific external load source is
  established. Future portability/runtime reporting will distinguish filesystem
  path location from verified sync-provider activity.

## 2026-09-07 — Task 2.3 deterministic segmentation and bounded replay

- Task 2.2 CLEAN marker is `5c3d46b`; environment-attribution correction is
  `34c3382`. The unchanged parent plan authorizes Task 2.3. An ignored execution
  brief freezes its scope and records one plan gap: the parent names a frozen
  replay page policy but specifies no type/fields, while the public Task 1 cursor
  exposes no pre-read payload-size peek. The minimal honest Task 2.3 policy is
  therefore exact `max_records` in 0..8,192; its hard bound composes with Task 1's
  existing 2 MiB payload cap, while actual canonical bytes remain exact work
  telemetry. No finer byte-admission or Task 1 API claim is made.
- Added fixture-first Task 2.3 RED suites. Boundary oracles freeze first/continue,
  combined reason precedence, deterministic literal episode IDs, profile-change
  ingest, exact integer time-gap/reversal behavior, strict count/request-byte
  limits, and duplicate counter idempotence. Replay oracles import the missing
  closed policy/work/continuation/complete/incomplete contracts and require
  zero-budget INCOMPLETE, exact resume, frozen wire shapes, a 5,120-byte
  continuation cap, and empty-snapshot completion. The next command must capture
  boundary results separately from the expected missing replay API collection
  RED; no Task 2.3 production implementation exists yet.
- First boundary-only RED run executed five tests: three passed and two failed.
  One failure is the intended production gap: ingesting a new observation under
  a new profile returns STATE_CONFLICT instead of applying a PROFILE_CHANGED
  boundary. The other exposed a test-author literal typo; the episode domain
  hash was recomputed from the frozen profile/session/first-observation inputs
  and the fixture was corrected to `episode:7c8a...3310`. No production code has
  changed and the profile-change RED remains.
- Corrected boundary rerun is the intended product RED: four passed and only
  `test_profile_change_precedes_other_reasons_and_ingest_accepts_it` failed,
  because current ingest returns STATE_CONFLICT. Separate replay collection
  produced exactly one expected ImportError for missing
  `SensoriumReplayCompleteV1` (the replay contract family/API is unimplemented).
  Both new test files are Ruff-clean. Independent Task 1 mapping confirmed no
  persistence change is needed: fresh `cursor`, mid-snapshot `suspend`, exact
  `resume_verified`, and propagated `LedgerSnapshotChanged` supply the full
  frozen-head lifecycle. This tests-only RED checkpoint is ready; no GREEN or
  Task 2.3 behavior is claimed.
- Implemented the first bounded replay candidate and removed the unreachable
  profile-transition guard. New observations may now change boundary profiles;
  the transition is still canonicalized against the caller-supplied immutable
  profile and records `PROFILE_CHANGED` before every other applicable reason.
  Duplicate retry branches validate the stored observation's profile rather
  than incorrectly requiring its predecessor core to already use that profile.
- Added immutable replay page-policy, page-work, continuation, incomplete, and
  complete records plus exact canonical wire projections. The frozen minimal
  policy is `max_records` in `0..8192`; zero work on a nonempty snapshot returns
  a distinct continuation, while an empty snapshot completes immediately.
  Continuations carry the exact Task 1 frozen-head checkpoint and cumulative
  work counters, are capped at 5,120 canonical bytes, and resume only through
  `VerifiedLedgerSession.resume_verified`.
- The initial Task 2.3 implementation rerun is GREEN for nine focused oracles:
  the five deterministic boundary tests, three initial replay lifecycle/wire
  tests, and the additive root-export check all passed. Ruff found only import
  ordering while the behavior tests passed; that mechanical ordering issue was
  corrected before continuing. Task 2.3 remains uncommitted and not CLEAN.
- Expanded replay validation with frozen-head mutation, page partition,
  shred-gap, malformed-record, and restart cases. Fourteen focused Task 2.3
  tests now pass: a changed head raises `LedgerSnapshotChanged`; one-shot and
  page sizes 1/2/3/7/16 produce identical completed state; shredding the first
  observation never resurrects it and surviving authenticated post-core state
  is adopted; a payload that claims the Task 2 observation schema but is
  malformed raises `LedgerIntegrityError` and releases the cursor; and reopen
  replay at the same head is byte-identical. Independent validator dispatch was
  attempted but its model quota expired before inspection, so no independent
  approval is claimed and that gate remains mandatory.
- Added strict JSON-value decoders for every new Task 2.3 replay record. Policy,
  page-work, continuation, incomplete, and complete values now round-trip their
  exact versioned schemas; unknown fields, boolean-as-integer counters, invalid
  checkpoint relationships, and constructor bounds fail closed. Root exports
  remain additive. Added an unbroken-predecessor integrity oracle proving a
  stored but forged boundary decision is rejected after deterministic
  recomputation. The focused Task 2.3 package passed 17 tests; Ruff and
  compileall passed. Pyright 1.1.413 was no longer present in either active venv
  or PATH after reboot, so that static gate remains pending restoration rather
  than being reported as clean.
- Executed the real 8,192-observation Task 2.3 scale oracle through the
  production encrypted ledger, canonical ingest, and frozen-head replay paths.
  It passed all assertions in 6,705.19 seconds (1:51:45): exactly 8,192 records
  were examined and applied, the replayed completed state equalled the live
  ingest state, its last observation sequence was 8,192, and its canonical
  encoding remained at or below the 4,096-byte hard limit. Process counters
  showed the durable ingest write phase complete before the replay-only read
  phase; no deadlock or retry was observed. Because this is intentionally
  expensive evidence, the oracle is moved into the plan-designated dedicated
  `test_cognition_task2_scale.py` lane rather than the fast replay test module.
  Task 2.3 remains GREEN, not CLEAN, pending post-move focused reruns, dual
  runtime/full regression, and independent review.
- A post-scale semantic-forgery oracle exposed a real replay classification
  defect before commit: the fail-closed `claims_observation` branch compared
  against a non-wire literal (`aluclu.canonical-observation.v1`) while canonical
  Task 2 records actually use `aluclu.observation.v1`. Consequently a malformed
  record with the real Task 2 schema, including a valid-looking envelope whose
  post core named a different last observation ID, could be skipped as
  unrelated instead of rejected. The first focused rerun was intentionally RED
  on that case. The implementation now uses one internal canonical-observation
  schema constant matching the frozen observation codec, and replay also
  requires post-core `last_observation_id` to equal the ledger event/request ID.
  A corrected focused rerun is mandatory before this repair is GREEN.
- Corrected the real-schema classification defect and reran the complete fast
  Task 2.3 package: 18/18 tests passed. Ruff passed, the three focused
  shred/malformed/post-core integrity cases passed, and Pyright 1.1.413 was
  restored through a pinned ephemeral runner with the active CPython 3.12
  interpreter; after one real optional-string narrowing repair it reported 0
  errors, 0 warnings, and 0 informations. The runner generated an unrelated
  root `uv.lock`; creation time proved it was a tool artifact from this gate,
  so it was removed without changing project dependency declarations.
- The wider non-scale Task 2 suite contains 199 tests across observation,
  recall-feature, sensorium, boundary, replay, recollection, and E2E modules.
  All 199 passed under CPython 3.12.13 and all 199 passed under CPython 3.13.5.
  The 8,192 scale oracle remains separate and already passed on CPython 3.12.13;
  it was not silently skipped inside either 199-test claim. Both attempted
  independent review agents exhausted their external quota before reading the
  candidate, so no independent verdict is claimed; retry is scheduled after
  their reported 07:50 reset.
- Expanded the deterministic boundary suite from combined precedence coverage
  to an isolated literal matrix. Forced, session, time-gap, goal, tool-phase,
  participants, topic-key, profile, observation-count, and request-byte
  boundaries each now produce exactly one expected reason and a hard-coded
  episode ID; FIRST and CONTINUE remain covered separately. The byte fixture
  also freezes the two-request canonical threshold at 1,198 bytes. All seven
  boundary tests passed and scoped Pyright remained 0/0/0. A CPython 3.13
  mirror and repository-wide regression are still required after this final
  oracle expansion.
- The isolated boundary matrix passed 7/7 under CPython 3.13.5 as well as
  CPython 3.12.13. A fresh repository-wide CPython 3.13.5 regression then
  passed all 734 non-scale tests with 0 failures, 0 errors, and 0 skips. The
  retained xUnit2 JUnit reports 1,098.208 seconds, timestamp
  `2026-09-08T16:12:58.808539+03:00`, and host `Kaan`. The sole warning is the
  pre-existing pytest `record_property`/xUnit2 compatibility warning in the
  real keyring smoke test. The deliberately separate 8,192 scale oracle is not
  included in the 734 count; its 1:51:45 PASS remains separate evidence.
  Task 2.3 is pre-review GREEN, not CLEAN.
- Independent review then found a composite replay hole not covered by the
  direct shred or partition tests: observation sequence 1 can be shredded,
  an unrelated live record can remain at sequence 2, and a surviving
  observation at sequence 3 can cross a page boundary after that unrelated
  record. The current loop advances its local expected sequence across the
  unrelated record and then rejects the authenticated surviving post core as
  though history were unbroken. Added one exact regression that requires both
  one-shot and one-record pages to adopt the same surviving bounded core. This
  is an intentional post-review RED checkpoint; no repair or CLEAN verdict is
  claimed yet. The finding also disproves the initial architecture review's
  claim that the frozen continuation alone preserves enough gap provenance.
- Ran the new composite oracle alone under CPython 3.12.13 and observed the
  intended RED failure in production code: even the one-shot replay raises
  `LedgerIntegrityError: Task 2 replay predecessor core digest does not match`
  at the surviving sequence-3 observation. This confirms the defect is not a
  test-only page-serialization artifact. The repair must distinguish an
  authenticated shredded append from merely interleaved unrelated live
  records, and that distinction must remain available after restart.
- Implemented the narrow repair boundary without changing the frozen Task 2
  continuation wire: an active `VerifiedLedgerSession` can now answer whether
  its already-verified snapshot proves a genuinely shredded append in one
  caller-bounded open sequence interval. The query is read-only, certificate-
  fenced, transactionally cleaned up, and rejects booleans, reversed/empty
  ranges, and bounds beyond the snapshot. Sensorium replay now relaxes a
  predecessor-core mismatch only when that proof exists between the last
  adopted observation and the current surviving observation; unrelated live
  records alone cannot open the integrity gate. Added direct Task 1 session
  tests, including use while a cursor is active. This is a candidate GREEN
  repair pending focused execution and independent review; Task 1's change is
  an additive read-only exception justified by the concrete RED regression.
- Added the complementary fail-closed oracle: a live predecessor observation,
  then an unrelated live record, then a well-formed observation envelope with
  a forged predecessor-core digest must still raise. This freezes the security
  distinction that motivated the repair: sequence distance or unrelated live
  traffic is never treated as shred evidence. The nine initial repair-focused
  cases passed on CPython 3.12.13 before this complementary oracle was added.
- The complete focused segmentation/replay package is GREEN at 21/21, including
  the composite recovery and complementary forged-predecessor cases. The new
  verified-session primitive plus all seven strict bound variants passed 8/8.
  Ruff, compileall, `git diff --check`, and pinned Pyright 1.1.413 over the
  changed production/test surface passed; Pyright reported 0 errors, 0
  warnings, and 0 informations. A broader combined Task 2 plus Task 1 session
  regression passed 314/314 independently under CPython 3.12.13 in 221.798s
  and CPython 3.13.5 in 211.391s, with zero failures, errors, or skips in both
  JUnit reports. Task 2.3 returns to review-ready GREEN, not CLEAN; the new
  cross-layer exception and exact security distinction still require fresh
  independent code and architecture review, followed by a repository-wide
  controller rerun.
- Extended the established Task 1 lifecycle/ownership oracles to the additive
  range-proof method: it fails after session close and cannot be invoked from a
  non-owner thread, including while the owning thread holds a live cursor. This
  closes the method-surface gap before review; focused rerun is pending.
- Independent code re-review rejected the first repair with one HIGH finding:
  the new range proof authenticates that an append was shredded, but not that
  the shredded append was a Task 2 observation. A valid observation followed
  by a shredded unrelated record can therefore authorize a later well-formed
  envelope whose predecessor-core digest was forged. Added the exact public-
  API reproduction as a fail-closed oracle. It must raise
  `LedgerIntegrityError`; the current generic proof is expected to make this
  test RED. Task 2.3 is reopened and no prior CLEAR/CLEAN claim survives this
  semantic blocker.
- Executed that oracle alone under CPython 3.12.13 and observed the intended
  RED result: replay completed instead of raising. This independently confirms
  the reviewer's reproduction. A usable repair therefore needs authenticated,
  content-free record-kind provenance that survives key destruction; event-ID
  shape or the existence of a generic tombstone is not sufficient evidence.
- Removed one validator-written trajectory paragraph that violated its
  read-only assignment and contradicted the live RED security oracle. Its
  unsourced claim of a new scale pass and manually interrupted full-suite run
  is not accepted as controller evidence. The earlier controller-owned 8,192
  PASS remains valid for the pre-repair replay path; the current candidate is
  RED solely on the authenticated lineage-witness blocker above.
- Architecture and code review now agree that the v2 ledger projection cannot
  soundly satisfy both shred-safe replay availability and fail-closed Task 2
  integrity: after key destruction it retains no authenticated semantic link
  from a shredded observation's pre/post core digests. The repair boundary is
  therefore frozen as a narrow Task 1 schema-v3 exception. Observation ingest
  will atomically add an HMAC-authenticated, content-free append witness bound
  to ledger ID, event ID, append sequence, append record hash, witness schema,
  and link digest; generic `append_once` will not mint one. Replay will accept
  a predecessor mismatch only when the same verified snapshot contains the
  tombstoned Task 2 witness whose post-core link digest exactly equals the
  surviving observation's pre-core digest and whose append sequence lies
  strictly after the current core and before that observation. The frozen
  Task 2 continuation wire remains unchanged. History/AAD chain framing stays
  v2 so schema-v3 creation does not silently redefine record cryptography;
  pre-existing schema-v2 ledgers fail with explicit migration-required rather
  than being mutated without a separately reviewed crash-safe migrator.
- Added the issuance-boundary RED oracle before implementation: a canonical-
  looking Task 2 envelope inserted through generic `session.append_once`, then
  shredded, must not become a lineage bridge for a later envelope. Only the
  private atomic path reached by validated `ingest_observation` may mint the
  authenticated witness. This prevents strict payload shape alone from being
  laundered into proof of a previously validated cognition transition.
- Ran the issuance-boundary oracle under CPython 3.12.13 and observed the
  intended RED failure: the generic shredded Task 2-shaped append currently
  bridges replay and completes instead of raising. The new v3 witness path
  must turn this exact case GREEN without weakening legitimate ingested-shred
  recovery.
- Resumed after the host reboot and audited the partially written schema-v3
  ledger diff before trusting it. Compileall passed, while the first focused
  session run exposed a mechanical v2-to-v3 fixture drift: the external
  metadata touch helper was restoring byte `2` and consequently triggered the
  new migration guard. Updated that fixture and the exact schema-creation
  oracle to v3. Hardened the unfinished witness value object so its HMAC is
  always computed from the frozen canonical body bytes rather than a caller-
  mutable JSON reference, and restricted generic witness schema tokens to the
  canonical lowercase ASCII alphabet. This is still implementation-in-
  progress: sensorium has not yet switched from the rejected generic shred
  boolean, and no CLEAN claim is made.
- Replaced that rejected boolean gate in production. Validated
  `ingest_observation` now uses the private atomic append-with-witness path;
  generic append remains witness-free. The content-free Task 2 witness carries
  only canonical IDs, digests, profile identity, and append/core lineage
  counters. Replay asks for an HMAC-verified, tombstoned witness whose exact
  post-core link equals the missing predecessor digest, validates the complete
  ledger-supplied append binding plus the strict Task 2 body, and walks
  backwards until it reaches the currently adopted core. That backwards walk
  deliberately supports multiple consecutive shredded observations and
  rejects a chain containing any raw/unwitnessed Task 2-shaped append. The
  ledger query now returns authenticated append sequence/event/hash metadata
  alongside the body, and the overly weak generic shred-range API has been
  removed from production and its direct tests. Focused RED-to-GREEN execution
  and dedicated witness tamper/atomicity coverage are still pending.
- First post-integration execution is GREEN: the existing ledger package
  completed 40/40, the verified-session package completed 72/72, and the
  sensorium replay package completed 16/16. The latter includes both security
  RED oracles that previously completed incorrectly: an unrelated shredded
  append and a generic raw Task 2-shaped shredded append can no longer bridge
  a forged predecessor digest. Ruff over the touched implementation/tests and
  cognition compileall also passed. These are focused results only; the new
  witness primitive still needs its own atomicity/tamper/idempotency oracles,
  multi-witness recovery, dual-runtime and full-repository gates before review.
- Tightened the candidate after identifying a second issuance-boundary nuance:
  proving the missing predecessors is insufficient if the first surviving
  observation itself came through generic raw append, because replay cannot
  recompute a transition whose predecessor body was shredded. Gap recovery
  now requires both (a) an exact backwards chain of tombstoned ingest
  witnesses to the adopted core and (b) an exact live ingest witness bound to
  the surviving event ID, sequence, record hash, post-core link and all of its
  non-content observation digests/append metadata. Added an oracle preventing
  a raw successor from borrowing a valid missing witness, plus a positive
  two-consecutive-shred/page-boundary oracle. Added Task 1 coverage for private
  issuance versus generic append, live/tombstoned visibility, active-cursor
  reads, exact idempotency conflicts, pre-commit fault rollback including key
  cleanup, body/MAC/history-binding tamper rejection, schema-v2 no-mutation
  migration refusal, and exact schema-v3 table creation. Execution of this
  expanded set is pending; no GREEN claim applies to these new assertions yet.
- The expanded witness security set is now focused GREEN. The complete replay
  file passed 18/18, including the new raw-successor rejection and the positive
  two-consecutive-shred chain under one-record pages. Fourteen witness-focused
  session cases passed, covering lifecycle/thread ownership, strict ranges,
  private versus generic issuance, live/tombstoned visibility, exact
  idempotency, injected pre-commit rollback, and three external SQL tamper
  classes. The three schema-v1/v2/v3 compatibility/exactness cases passed.
  Ruff and `git diff --check` are clean (Git reports only the repository's
  existing LF-to-CRLF checkout warnings). Broader dual-runtime and repository
  gates remain outstanding, so this checkpoint is GREEN but not CLEAN.
- Extended Task 1 witness coverage again before broad gates: direct lookup now
  proves an exact witnessed live append and returns no proof for a generic live
  append. Three post-SQLite-commit interruption boundaries now require
  recovery-forward to preserve both the encrypted record and its authenticated
  witness: before key-store commit, before anchor publication, and after anchor
  publication but before certificate refresh. These new recovery assertions
  are not counted GREEN until their focused run completes.
- The extended recovery set passed 17/17 together with the other witness-
  focused cases. Pinned Pyright 1.1.413 over the changed cognition production
  package and all Task 2/witness test files passed with 0 errors, 0 warnings,
  and 0 informations after one test-local invariant dictionary was explicitly
  typed as JSON-compatible. Ruff and `git diff --check` remain clean apart
  from Git's informational line-ending notices. The earlier broad dual-runtime
  processes began before this final test addition and therefore will not be
  used as final evidence; fresh candidate-wide runs are still required.
- Amended the frozen Task 2.3 plan instead of leaving a silent cross-task
  deviation. The amendment records the schema-v3 Task 1 exception, explicit
  no-mutation handling for schema v2, unchanged history/AAD framing version,
  private issuance trust boundary, tombstoned-chain plus live-successor proof,
  unchanged continuation wire, 8,192 bound, and the honest residual that
  isolated witness deletion is fail-closed denial of service rather than a
  detected rollback. New Task 2 plan SHA-256:
  `2C0BFE51FC5DA06EAE88581F0F2303948BC2CD0BD73B98553F0187227017E65F`.
  The global roadmap remains byte-identical at SHA-256
  `950126478A4198334B71328282A23C404142A8A28BDB7957BC9F997F1DB79050`.
  All remaining review and CLEAN gates are against this amended plan hash.
- Added an executable oracle for the plan's deletion residual: the raw
  schema-v3 witness body must not contain the observation's retrieval text or
  canonical content, and externally deleting the only missing-predecessor
  witness may pass structural ledger verification but must make replay fail
  closed rather than guess or resurrect data. This assertion is pending its
  first run and is explicitly an availability guarantee, not rollback
  detection.
- The deletion/no-content oracle passed as part of the complete 19/19 replay
  file. Pinned Pyright remained 0/0/0. Ruff correctly flagged only a newly
  introduced local import-order issue; it was repaired by ordering the
  contracts import after the package import. A clean post-repair Ruff rerun is
  still required and no test or static failure was hidden.
- Added the final mixed-history discriminator requested by the security model:
  an unrelated generic append may be shredded near a real missing Task 2
  observation, but replay must ignore it and recover only through the exact
  Task 2 witness, identically in one-shot and one-record pages. This new case
  is pending execution. Broad runs already in flight predate it and remain
  diagnostic rather than final candidate evidence.
- The mixed-history discriminator passed and the complete replay file is now
  20/20. Post-import-fix repository Ruff, compileall, and `git diff --check`
  also passed; only informational line-ending warnings remain. The test surface
  is frozen for fresh dual-runtime and repository-wide execution unless review
  produces a new valid finding.
- Controller security inspection found one additional missing-profile trust
  edge before freeze: when the predecessor core matched but replay could not
  reconstruct the exact boundary profile, the old branch skipped recomputation
  and could accept a raw, unwitnessed transition. Replay now requires the same
  exact live ingest witness whenever the profile object is unavailable. Added
  a raw custom-profile rejection oracle and a positive ingested profile-change
  one-shot/page-1 equivalence oracle. The plan amendment now states this rule;
  it supersedes the immediately prior Task 2 plan hash. Current Task 2 plan
  SHA-256 is
  `7C695BD60355C21FE181AB8A89F165A3D63E203BB9220DE16DC96C11F0D88200`;
  global roadmap hash remains
  `950126478A4198334B71328282A23C404142A8A28BDB7957BC9F997F1DB79050`.
  These two new assertions are pending execution and broad runs already in
  flight remain non-final evidence.
- Both missing-profile assertions passed and the complete replay file is now
  22/22. Repository Ruff and compileall passed, and pinned Pyright 1.1.413
  again reported 0 errors, 0 warnings, and 0 informations over the changed
  production and test scope. This is the final focused candidate pending fresh
  broad execution and independent review.
- Stopped the two superseded broad Python 3.12/3.13 processes explicitly after
  the missing-profile production edit; both therefore exited 1 by controller
  interrupt and neither is counted as a regression or as evidence. Fresh runs
  will start from the final candidate rather than spend further time testing a
  pre-fix import snapshot.
- Independent code/security re-review is APPROVE with zero CRITICAL, HIGH,
  MEDIUM, or LOW findings on the current live diff. The review re-ran
  repository Ruff, both missing-profile cases, the complete 22-case replay
  file, scoped Pyright 1.1.413, compileall, and base-to-head diff-check; all
  passed. Its initial report had correctly withheld approval for the transient
  import-order failure it observed, then the reviewer re-read the repaired live
  state and cleared that sole blocker. Residuals remain explicit and accepted:
  private underscore issuance is not a hostile same-process boundary, isolated
  witness deletion is fail-closed availability loss rather than rollback
  detection, and the reviewer did not rerun the 8,192 lane. Controller-owned
  fresh dual-runtime/full/scale gates remain required before CLEAN.
- Fresh final-candidate Task 1 plus Task 2.3 execution passed independently on
  both local runtimes: CPython 3.12 completed 193/193 with zero failures,
  errors, or skips in 403.817s; CPython 3.13 completed the same 193/193 with
  zero failures, errors, or skips in 388.610s. Controller parsed the persisted
  JUnit reports from the OS temporary directory rather than inferring counts
  from progress dots. Architecture-review delegation could not return a
  verdict because that agent exhausted its account usage; this is recorded as
  unavailable evidence, not an approval. Repository-wide and real 8,192-scale
  controller gates remain before CLEAN.
- Fresh Python 3.13 repository-wide execution, intentionally excluding only the
  separately controlled 8,192 scale file, passed 762/762 with zero failures,
  errors, or skips in 840.430s. The sole warning is the pre-existing Pytest
  compatibility notice that `record_property` is incompatible with JUnit
  xunit2 in the real platform keyring smoke; the smoke itself passed and this
  warning does not affect product behavior. Controller parsed the OS-temporary
  JUnit report. The dedicated real 8,192 observation gate is now the remaining
  execution blocker before final static rerun, commit, and CLEAN review record.
- The dedicated final-candidate scale lane passed on CPython 3.13: one real
  test created and ingested 8,192 canonical observations through the production
  encrypted directory-backed ledger and schema-v3 witness path, replayed all
  8,192 from the same verified snapshot, matched the exact final
  `SensoriumStateV1`, reported 8,192 examined/applied records, and kept the
  encoded completed state within 4,096 bytes. JUnit reports 1/1 with zero
  failures, errors, or skips in 2290.723s (about 38m11s). Progress was observed
  only via record-key file counts and process metrics; the controller never
  opened the live SQLite database or disturbed its verification certificate.
  This is materially faster than the earlier pre-witness 6705.19s host run,
  but no general performance claim is made from two differently timed local
  executions. Final static/diff gates, architecture review, and commit remain.
- Final post-scale static gates passed on the unchanged candidate: repository
  Ruff, compileall over `src scripts tests`, and `git diff --check` are clean;
  pinned Pyright 1.1.413 over the changed cognition package plus Task 2.3/
  witness tests reports 0 errors, 0 warnings, and 0 informations. Task 2 plan
  SHA-256 rechecks as
  `7C695BD60355C21FE181AB8A89F165A3D63E203BB9220DE16DC96C11F0D88200`
  and global roadmap SHA-256 remains
  `950126478A4198334B71328282A23C404142A8A28BDB7957BC9F997F1DB79050`.
  The only outstanding gate is the final independent architecture/threat
  verdict, after which controller will record CLEAN and commit the exact owned
  surface if no finding reopens the candidate.
- Final independent architecture/threat review returned APPROVE with zero
  CRITICAL, HIGH, MEDIUM, or LOW findings. The reviewer independently reran 33
  architecture-critical assertions (33/33 passed in 34.33s), verified the
  schema-v3/history-format split, authenticated and transition-bound append
  witnesses, crypto-shred bridge rules, exact live-witness requirement,
  missing-profile fail-closed behavior, witness atomicity/recovery, bounded
  frozen continuations, and explicit schema-v2 migration refusal. Repository
  diff-check passed and both the Task 2 plan and global roadmap hashes matched
  the controller values above. Accepted residuals remain documented: private
  underscore APIs are not a hostile same-process security boundary, and
  deleting authenticated witness rows causes fail-closed availability loss
  rather than furnishing rollback-detection evidence.
- **Task 2.3 deterministic segmentation and bounded replay: CLEAN.** The final
  acceptance record is: Task 1 plus Task 2.3 passed 193/193 on both CPython
  3.12 and 3.13; the Python 3.13 repository-wide non-scale lane passed 762/762;
  the dedicated production-backed 8,192-observation lane passed 1/1 with exact
  final-state equivalence and a completed encoded state no larger than 4,096
  bytes; repository Ruff, compileall, diff-check, and scoped pinned Pyright all
  passed; independent code/security and architecture/threat reviews both
  returned APPROVE with zero findings. The next implementation unit is Task
  2.4: bounded streaming approximate recollection, beginning with a fresh
  contract/plan read and RED acceptance oracles.
- Task 2.4 execution began from clean commit `244ebe0`. Live-plan and code
  mapping confirmed that Task 2.1 already freezes normalization/feature-vector
  construction while Task 2.2 exposes only direct-ID exact recall; Q32 feature
  comparison, exact cross-product ranking, content-digest scans, and bounded
  streaming text recall remain the new Task 2.4 surface. The first RED slice
  adds literal feature-math oracles for nonpositive and zero dots, exact
  `2^32` identity, floor-before-`isqrt`, symmetry, and an adversarial pair whose
  quantized Q32 scores tie while its exact rational cosine ordering differs.
  The expected new public contracts are `FeatureSimilarityV1`,
  `measure_feature_similarity`, and `compare_feature_similarity_exact`; no
  production implementation exists yet, so focused collection must fail at
  import before the GREEN step.
- The first Task 2.4 RED execution behaved as intended on CPython 3.13: test
  collection failed because `FeatureSimilarityV1` and the two comparison APIs
  did not exist. The attempted CPython 3.12 command did not start because the
  assumed worktree-local `.venv312` path is absent; this is environment-path
  evidence, not a test failure, and the interpreter will be resolved before
  cross-runtime acceptance. The GREEN implementation now adds immutable,
  self-validating integer similarity statistics, exact dot/norm accumulation,
  the specified floor-before-`isqrt` Q32 calculation clipped to `[0, 2^32]`,
  and exact rational cross-product comparison without floating point.
- The first Task 2.4 GREEN slice passed: the complete feature test file is
  50/50 on both CPython 3.12.13 (`.venv`) and CPython 3.13.5 (`.venv313`), and
  focused Ruff is clean. The large-bin adversarial fixture confirms two
  candidates can both quantize to `2^32 - 1` while exact integer
  cross-products still order the closer vector correctly. The next RED slice
  freezes content-digest query/result types and paged duplicate accumulation
  before implementing text top-k.
- Independent Task 2.4 read-only mapping confirmed the current implementation
  gap and found no Task 1 redesign need, but identified decision blockers in
  fixture ownership, scan-result compatibility, filter semantics, threshold
  equality, continuation forgery, and incomplete-page behavior. The Task 2
  plan now freezes those points: a companion recollection determinism manifest
  preserves the CLEAN Task 2.1 manifest; the two-argument direct-ID API remains
  unchanged; provenance filters are inclusive and separate from the preferred
  time-window tie breaker; score eligibility is `>=` while margin passage is
  strict `>`; scan absence is a distinct closed type; and page continuation is
  a query/policy/profile/snapshot-bound process-local authenticated capability.
  The plan also makes malformed claimed observations fail closed, requires
  cursor closure before payload reads, and defines exact output/work accounting.
  The first requested architecture agent was unavailable because its fixed
  model is unsupported on this account; the successful explorer report is the
  independent evidence used for this amendment.
- Added the frozen canonical Task 2.4 companion determinism fixture rather than
  mutating Task 2.1's already-CLEAN manifest. Its literal sparse cases cover
  dot/norm products, the quotient before integer square root, exact Q32 values,
  and the large-bin Q32 collision whose exact cross-products differ. Tests
  independently reconstruct vectors and arithmetic from the fixture; the file
  is not generated from production code.
- First companion-fixture execution produced the intended strict byte-level
  failure on both runtimes: only the trailing newline introduced while adding
  the file differed from canonical JSON bytes; all arithmetic assertions and
  focused Ruff/diff checks otherwise passed. The canonical-byte requirement is
  retained and the file will be normalized without weakening the oracle.
- After removing only that terminal LF, the companion manifest is canonical
  byte-for-byte and the complete feature suite passes 57/57 on both CPython
  3.12.13 and 3.13.5. Focused Ruff and diff-check also pass. Task 2.4's pure
  feature mathematics and independent protocol fixtures are now GREEN; public
  root exports and the first paged content-digest RED contract follow.
- Added the three feature-similarity symbols to the additive root cognition
  surface and preserved every earlier export. The combined
  `test_cognition_recall_features.py` plus `test_cognition_sensorium.py` command
  passes 72/72 on both CPython 3.12.13 and 3.13.5, and focused Ruff is clean
  after correcting export order. A fresh independent code/security review plus
  scoped type/compile/diff checks are the remaining gates for this pure-feature
  checkpoint.
- The worktree-local Pyright executable probe was unavailable and is not
  counted as a type-check result. The corrected pinned ephemeral Pyright
  1.1.413 command, bound to `.venv313`, reports 0 errors, 0 warnings, and 0
  informations for the changed feature production/root/test scope. Compileall
  and diff-check pass; only the independent review remains before checkpoint.
- Independent feature-checkpoint code/security review returned APPROVE with no
  CRITICAL, HIGH, or MEDIUM findings. Its sole LOW traceability note was that
  the 72-test trajectory wording could be misread as naming a nonexistent
  public-surface test file; the sentence now names the two files actually run.
  The reviewer independently passed 57 feature tests on both runtimes, 156
  observation/sensorium/replay regressions and 14 contract tests on CPython
  3.12, root import probes on both runtimes, Ruff, compileall, and diff-check.
  The pure feature/Q32/companion-fixture slice is accepted for checkpoint.
- Task 2.4 binding-plan SHA-256 at this checkpoint is
  `16938F0BB27A4546659E9D5F74F5F366623544EACC676FFD752A205D434FF158`.
  The global roadmap remains unchanged. Exact staged scope is the Task 2 plan,
  trajectory, feature implementation/root exports, companion protocol JSON,
  and feature tests only.
- Task 2.4 content-digest RED work resumed from clean commit `64ef402`, after
  the accepted pure feature/Q32 checkpoint. The first reduced RED slice now
  lives in `tests/test_cognition_recollection.py` only and freezes strict
  `RecallFiltersV1`, `ContentDigestRecallQuery`, and
  `RecallExecutionPolicyV1` boundaries plus exhaustive zero/one/two
  content-digest scan outcomes, zero-record non-final pages, no-continuation
  work-budget abstention, and one duplicate-accumulating continuation page.
  The policy fixture deliberately binds to the live `active_normalizer_id()` and
  `active_feature_spec_id()` helpers instead of invented IDs, and filter tuples
  are strict sorted-unique inputs: unsorted or duplicate IDs/source kinds are
  rejected rather than silently canonicalized. Syntax and focused Ruff over the
  touched recollection test file pass on CPython 3.13.
- The intended RED signal is confirmed on both local runtimes. CPython 3.13
  (`.venv313`) and CPython 3.12 (`.venv`) both fail collection of
  `tests/test_cognition_recollection.py` because the new Task 2.4 recollection
  contracts are not implemented yet:
  `ImportError: cannot import name 'AbstainedRecollection' from
  'aluclu.cognition.recollection'`. This is the expected next GREEN target, not
  a syntax/lint failure. The next implementation step is to add the immutable
  scan contracts/results/work accounting and route `recall(..., policy=...)`
  through a bounded verified-ledger cursor while preserving the existing
  two-argument direct-ID behavior.
- Checkpoint commit `64ef402` (`Add deterministic Task 2 recall scoring`)
  records the reviewed Task 2.4 pure-feature slice. The next owned change is
  the content-digest/paged-continuation RED suite; production scan code remains
  absent at this point.
- The initial content-digest RED slice now freezes strict sorted/unique filter
  inputs, exact active-runtime policy IDs and bounds, exhaustive scan absence,
  unique exact digest recall, ambiguous duplicate results without content,
  accumulator preservation across a one-record page split, zero-work
  incompleteness, and no-continuation abstention. Controller corrected the test
  continuation to reuse the exact frozen one-record policy rather than expand
  its per-call budget. CPython 3.13 collection is RED because the new closed
  query/policy/result contracts do not yet exist; existing direct-ID tests
  remain in the same file as compatibility oracles.
- The first content-digest GREEN attempt exposed two import-time integration
  defects before behavioral execution: `validate_event_id` was imported from
  `contracts` instead of its owning `codec` module, and a default filter object
  was constructed before a later validation helper existed. Both were repaired
  at the cause (owner-correct import and dataclass `default_factory`), with no
  fallback or relaxed validation. The complete recollection file then passed
  19/19 on CPython 3.13. The implementation now provides strict filters and
  policy bounds, closed exact/ambiguous/absent/incomplete/abstained results,
  a query/policy/profile/snapshot-bound HMAC continuation, cumulative work,
  bounded exact summaries, stable cursor paging, fail-closed claimed-observation
  parsing, and post-cursor direct-read revalidation. Combined recollection plus
  sensorium compatibility passed 34/34; only root-export ordering remained a
  static finding and was corrected before the next gate.
- Added the second content-digest adversarial test layer before checkpoint:
  33 live same-digest occurrences must retain an exact scalar count while
  capping summaries at 32; hard filters must run before uniqueness; continuation
  must reject changed query, changed policy, field tampering, and a changed
  Task 1 head; unrelated schemas are skipped but a malformed payload claiming
  `aluclu.observation.v1` raises integrity failure; and selected direct reads
  must observe zero active cursors before a subsequent mutation succeeds.
- The strengthened content-digest slice passes all 25 focused recollection
  tests on both CPython 3.12.13 and 3.13.5. The combined recollection plus
  sensorium compatibility lane passes 40/40 on both runtimes. Focused Ruff,
  compileall, and `git diff --check` are clean; the diff remains restricted to
  the recollection implementation, additive root exports, recollection tests,
  and this trajectory. These tests include process-local continuation HMAC
  coverage over the complete retained provenance identity, exhaustive-result
  validators, exact output/work accounting, and the cursor-before-direct-read
  discipline.
- Pinned Pyright 1.1.413 initially found that the static flow could not prove a
  one-match accumulator contained exactly one retained summary. The controller
  repaired the invariant at runtime rather than masking it with a cast: an
  exhaustive `exact_match_count == 1` state now raises `LedgerIntegrityError`
  unless the bounded summary tuple also has length one. After that change,
  focused Ruff and the 25/25 CPython 3.13 recollection suite pass again, and
  Pyright reports 0 errors, 0 warnings, and 0 informations for the modified
  implementation, root exports, and tests. The first independent review
  attempt could not run because the reviewer agent hit its account usage
  window; that is recorded as infrastructure evidence rather than a code
  verdict, and the review has been retried before CLEAN/commit.
- The retried independent content-digest code/spec/security review returned
  APPROVE with zero CRITICAL, HIGH, MEDIUM, or LOW findings. The reviewer
  independently reran the focused recollection suite on both runtimes, the
  recollection-plus-sensorium compatibility lane, Ruff, compileall, pinned
  Pyright 1.1.413, and diff-check. Review specifically confirmed direct-ID
  compatibility, bounded verified-cursor scanning, honest incomplete results,
  process-local authenticated continuation binding, fail-closed accumulator
  and claimed-observation invariants, exact/ambiguous/no-scan separation,
  cursor closure before selected payload reads, and live identity revalidation.
  Accepted residual scope is explicit: this checkpoint does not yet implement
  approximate text recall, calibration, plasticity, or the later 2,048/8,192
  scale gate. The Task 2.4 content-digest sub-slice is CLEAN and ready for its
  exact-scope checkpoint commit.
- Checkpoint commit `8f19d83` (`Add bounded content digest recollection`)
  records the reviewed content-digest sub-slice. Task 2.4 then moved directly
  to text/approximate recall. Before RED, the binding plan was made literal for
  the previously underspecified result shapes: one strict candidate record;
  exhaustive approximate, conflict, and text-absence result records; top-two
  margin behavior including a missing-second zero score; conflict precedence;
  exact content-omission consistency; and an explicit
  `APPROXIMATE_DISABLED` abstention. This amendment changes no completed
  content-digest behavior and is the contract for the next failing tests.
- The first text-recall RED layer is test-only and intentionally exercises the
  new public surface before implementation: raw query-size rejection; a Q32
  identity score with different stored content remaining approximate; a
  distinct-content top-score tie becoming a metadata-only conflict; a
  same-content tie remaining individually preserved candidates; bounded
  top-candidate continuation across one-record pages; unscored
  `retrieval_text=None`; deterministic content omission under a zero-byte
  output budget; and `APPROXIMATE_DISABLED` abstention. Existing policy helpers
  were only parameterized to express these literal boundaries. Production code
  is unchanged in this RED step.
- Focused Ruff is clean and both CPython 3.12.13 and 3.13.5 produce the intended
  RED collection failure: `ApproximateCandidates` is absent from the committed
  recollection module. This is the literal missing production surface rather
  than an incidental syntax/import-order defect. A read-only independent map
  corroborated the RED matrix and highlighted the continuation boundary: retain
  compact ranking identity, exact similarity statistics, and a feature-vector
  digest, not plaintext content or full provenance; authenticate the ordered
  accumulator; then live-read and recompute the selected records only after the
  cursor closes. This keeps content-digest continuations additive and prevents
  Q32-only resume ordering from losing exact cross-product information.
- Pre-GREEN review found a real `top_k=1` contract contradiction: text recall
  cannot compute a top-two margin or return two conflict witnesses with a
  one-slot accumulator. The shared policy still accepts one for content-digest
  compatibility, while the text query-policy boundary now explicitly requires
  at least two. A RED assertion freezes that fail-closed behavior; no runner-up
  will be silently treated as absent.
- The first text/approximate GREEN implementation now passes all 34 focused
  recollection tests on both CPython 3.12.13 and 3.13.5. It adds a bounded text
  query, strict candidate/approximate/conflict/text-absence records, exact
  cross-product-first ordering, inclusive score eligibility, strict margin
  conflict, additive top-candidate continuation state, HMAC coverage over the
  ordered compact accumulator, output-budget omission, and post-cursor live
  record/feature/similarity revalidation. Candidate content is direct-read only
  once per final result. Focused Ruff is clean, pinned Pyright 1.1.413 reports
  0 errors, 0 warnings, and 0 informations, and diff-check is clean. This is an
  initial GREEN, not yet the text-recall checkpoint; adversarial ranking,
  continuation-tamper, top-k, cursor-lifecycle, and exhaustive-reference tests
  still follow.
- Added the second text-recall adversarial layer before checkpoint. It drives
  the companion fixture's Q32 collision through the production recall path and
  requires exact cross-product similarity to beat a newer timestamp; proves the
  preferred-time tie breaker precedes recency; mutates a continuation's raw
  feature vector to test its independently authenticated digest; compares
  one-shot and one-record-paged final candidates; scans 33 eligible records
  while retaining exactly 32; proves hard filters run before scoring; and
  instruments approximate direct reads to require zero active cursors before a
  later append. The existing malformed-observation test now also appends after
  the raised integrity error to prove exception-path cursor cleanup.
- The first adversarial execution had one failure after all preceding cases
  passed: feature-vector mutation was correctly rejected, but the test expected
  an internal candidate-specific phrase while the continuation validator
  deliberately normalizes malformed nested state to the public message
  `recall continuation is malformed`. The test now asserts that stable public
  boundary. No production check was removed or weakened.
- After that expectation repair, all 41 focused recollection tests pass on both
  CPython 3.12.13 and 3.13.5, with focused Ruff clean. The Q32-collision case
  proves exact rational order wins even against the newer-timestamp tie breaker;
  text continuation mutation is rejected; one-shot and paged results agree;
  33 scored records retain/return exactly the configured 32; and success plus
  integrity-exception paths leave no cursor that blocks mutation. Broader
  feature/sensorium regressions, static gates, and independent review remain
  before this text-recall slice can be checkpointed.
- The broader text-slice compatibility lane passes 113/113 on both CPython
  3.12.13 and 3.13.5 across recollection, deterministic feature math/fixtures,
  and sensorium ingestion. Compileall, diff-check, and pinned Pyright 1.1.413
  are clean, with Pyright reporting 0 errors, 0 warnings, and 0 informations.
  The candidate is now entering independent code/spec/security review; Task
  2.4 text scale/reference expansion and any review findings still precede a
  CLEAN declaration.
- Independent text-recall code/spec/security review returned REQUEST CHANGES
  with one HIGH correctness finding: two same-digest observations could fill a
  small observation-level top-k and hide an equally scored distinct-digest
  candidate, incorrectly returning approximate candidates instead of conflict.
  The reviewer supplied a live three-record reproducer. The binding contract
  now defines conflict margin over the best two distinct content identities and
  requires at most two compact conflict witnesses alongside the returned
  observation top-k. Raw vectors are removed from continuation state in favor
  of exact similarity statistics plus a feature digest, with final direct-read
  re-encoding. A literal regression is added before the production repair.
- The first regression attempt was blocked earlier than recall because its
  newest-to-oldest ingestion order correctly triggered sensorium's
  `TIME_REVERSED_INVALID` guard. The fixture now appends the same three records
  in causal timestamp order while preserving the intended retrieval ranking;
  production behavior remains untouched for the actual RED check.
- With the causal fixture corrected, the reviewer reproducer is now a literal
  RED: three equally scored observations with two newer same-digest rows and
  one older distinct digest return `ApproximateCandidates` under `top_k=2`,
  while the contract requires `ConflictedRecollection`. The failure is at the
  intended result-type assertion and precisely demonstrates duplicate crowding.
- The production repair now retains observation-level top-k plus at most two
  best distinct-content witnesses, both as compact exact-statistics/digest
  metadata without raw vectors. The focused HIGH reproducer and continuation
  tamper check pass. The same-content-only test then exposed its intentionally
  changed margin oracle: with one distinct content identity, the absent second
  identity has score zero, so an identity-score candidate has margin `2^32`
  rather than the old duplicate-row margin zero. The test is aligned to that
  binding content-identity definition; no uncertainty check is weakened.
- The HIGH regression now also executes the three-record duplicate-crowding
  case as three one-record continuation pages and requires its final conflict
  witnesses to equal the one-shot result. This specifically guards HMAC-bound
  preservation of the distinct-content accumulator rather than proving only
  the in-memory one-call path.
- A broad test-edit hunk initially renamed the result variable in the preceding
  identity-firewall case instead of the intended duplicate-crowding case. The
  variable-only mistake was found by immediate source inspection and corrected
  before execution; no assertion or production behavior changed.
- A second targeted inspection found the same overly broad context had touched
  the adjacent two-content conflict test as well. Function-scoped patch context
  now restores that local `result` and names only the duplicate-crowding call
  `one_shot`; the suite was not run in the inconsistent intermediate state.
- The HIGH repair is now independently APPROVED on static code/spec/security
  re-review. The reviewer confirmed the distinct-digest accumulator is updated
  for every eligible observation, keeps only the best representative per digest
  and at most two digests, survives continuation under HMAC, drives final
  conflict selection, and retains no plaintext or raw feature vector. The full
  focused suite passes 42/42 on both CPython 3.12.13 and 3.13.5 after the fix;
  compileall and diff-check pass, and pinned Pyright 1.1.413 again reports 0
  errors, 0 warnings, and 0 informations. The original reviewer reproducer is
  therefore closed with both one-shot and paged runtime evidence.
- Final post-fix compatibility evidence for the text-core checkpoint is 114/114
  on both CPython 3.12.13 and 3.13.5 across recollection, feature mathematics/
  protocol fixtures, and sensorium ingestion. Focused Ruff, compileall,
  diff-check, and pinned Pyright 1.1.413 are clean; Pyright reports 0 errors, 0
  warnings, and 0 informations. The Task 2 binding-plan SHA-256 is
  `4F43006B2CC4E38B70B40A50BA7904236F182F0B8F954873FFC4F8FBEC373B7B`.
  The reviewed Task 2.4 text-query/streaming-ranking correctness core is CLEAN
  for an exact-scope checkpoint. This does not close Task 2.4: dedicated
  structural memory accounting, independent exhaustive-reference coverage, and
  2,048/8,192 scale evidence remain the next sub-slice.
- Checkpoint commit `05427f9` (`Add bounded approximate text recollection`)
  records the reviewed text-query/streaming-ranking correctness core. Task 2.4
  scale work begins from that clean boundary. The next RED must prove bounded
  continuation state without raw vectors, exact work growth at 2,048 versus
  8,192 live observations, one-shot/paged result identity, and production-backed
  cursor scanning while retaining raw timing/memory evidence. The existing
  8,192 sensorium scale fixture is being mapped first so authenticity is not
  weakened merely to shorten the run.
- The first delegated read-only scale-fixture mapping attempt could not start
  because that agent lane had reached its account usage window; this is recorded
  as orchestration infrastructure, not as a code or test failure. Work continues
  locally from the verified checkpoint, while the already available independent
  reviewer lane has been asked to challenge the scale oracle without editing or
  launching the long-running fixture.
- The Task 2.4 scale RED design is frozen before implementation: extend the one
  production-backed 8,192-observation fixture rather than duplicate its costly
  ingestion; take a real exhaustive recall measurement at 2,048, then measure
  one-shot and four 2,048-record continuation pages at 8,192. Blocking oracles
  cover exact 4x scan/score work, one-shot/paged result identity, top-k and
  two-digest continuation bounds, absence of raw vectors, a fixed authenticated
  continuation-payload ceiling, and fixed traced-memory ceilings. Raw elapsed
  time and traced peaks remain evidence rather than a flaky wall-clock ratio.
  A separate small production-ledger fixture will compare streaming selection
  with an independently written exhaustive exact-cross-product sorter.
- The scale RED is now implemented in `test_cognition_task2_scale.py`. The
  bounded reference fixture independently reimplements positive-cosine
  cross-product ordering and the deterministic tie breakers active under its
  default filters, then requires a
  production one-shot scan and four streaming pages to select the same top-k.
  The 8,192 fixture now captures a completed 2,048-record snapshot measurement,
  continues ingestion to 8,192, compares one-shot with four-page recall, checks
  the exact work ratio, and inspects every non-final continuation for top-k,
  two-distinct-digest, raw-vector-absence, authenticated-state-size, and traced
  memory bounds. Pytest properties retain all raw elapsed/peak measurements.
  No production code changed in this RED step; static collection and execution
  have not yet been claimed.
- First static collection succeeds on both installed CPython 3.12 and 3.13 and
  compileall/diff-check are clean. Ruff correctly rejected only import grouping:
  `Callable` must come from `collections.abc`, and the two first-party
  `aluclu.cognition` import forms must share one group. The imports are repaired
  without changing either oracle; the static gate will be rerun rather than
  treating the mechanical fix as presumed clean.
- The first bounded reference execution is RED on both runtimes for a fixture
  defect, not production ranking: the attempted `index % 4` timestamp variety
  makes the fifth causal ingest older than the fourth, so the sensorium correctly
  returns `TIME_REVERSED_INVALID`. The reference fixture now uses strictly
  monotonic nanoseconds; exact-cosine ordering remains independently computed,
  while dedicated correctness tests continue to own isolated tie-break vectors.
  Ruff is already clean after the import repair. The bare global `pyright`
  command is absent from PATH, so the previously pinned invocation must be
  recovered before the type gate is claimed.
- The corrected independent exhaustive-reference oracle is GREEN on both
  CPython 3.12 and 3.13. The reviewer independently agrees with the production-
  backed 2,048/8,192 design and warns against hard wall-clock ratios on this
  Windows/SQLite/OneDrive host. Its strongest raw-vector recommendation is now
  incorporated: every retained continuation candidate must expose the compact
  `feature_digest`, no dataclass field name may contain `vector` or `bins`, and
  the authenticated payload separately rejects vector/bin keys. The scale query
  deliberately keeps a zero score floor so all 32 top-k slots are stressed;
  result-type assertions permit explicit conflict at 2,048, while the exact
  8,192 text supplies a unique top candidate for final identity comparison.
- Pinned Pyright 1.1.413 then found one honest test-contract omission: the new
  reference fixture passed the bootstrap union directly to ingestion without
  proving its empty-ledger result is `SensoriumStateV1`. Runtime execution had
  taken that branch on both interpreters, but the test now binds it explicitly
  with the same type assertion as the production scale fixture; no cast or type
  suppression is used. Ruff, compileall, and diff-check remain clean; Pyright
  must be rerun after this invariant repair.
- The invariant repair is clean: the independent reference fixture passes again
  on CPython 3.12 and 3.13, Ruff passes, and pinned Pyright 1.1.413 reports 0
  errors, 0 warnings, and 0 informations. Plan reinspection confirms that
  512-byte-class payloads, the 2,048/4,096/8,192 RSS delta, restarted-result
  digest, direct-read p95, and blocking wall-clock ratio belong to the later
  Task 2.7 full scale/restart gate. Task 2.4's binding RED remains the narrower
  production-backed 2,048-versus-8,192 bounded-candidate and approximately
  linear-work proof. The existing expensive fixture is therefore not silently
  expanded into Task 2.7; its Task 2.4 long run is ready on the current host.
- The frozen production-backed 8,192 scale candidate passes on CPython 3.13.5:
  1/1 in 3,668.71 seconds. Its blocking assertions prove an exact 2,048-to-8,192
  4x increase in both records scanned and candidates scored, identical 8,192
  one-shot/four-page results, exactly three non-final continuations, and all
  structural/traced-memory ceilings. Raw evidence records 119.061 seconds and
  460,134 traced bytes at 2,048; 464.904 seconds and 8,130,012 traced bytes for
  the 8,192 one-shot; 476.082 seconds and 8,174,819 traced bytes for the paged
  8,192 scan; and authenticated continuation sizes of 19,556, 19,559, and
  19,562 bytes. The one-shot wall time scales by approximately 3.904x for 4x
  work; that is retained evidence, not a new hard ratio gate.
- Pytest emitted one metadata-only warning because `record_property` is not
  xUnit2-compatible, although the completed XML did retain every property.
  The evidence hook is narrowed to pytest's suite-level
  `record_testsuite_property`, which is xUnit2-compatible and does not alter any
  scale assertion or measured code path. The reviewer's only LOW is also closed
  by describing the independent sorter as covering tie breakers active under
  default filters, rather than claiming its no-preference fixture exercises the
  separate temporal-preference branch. Fresh fast/static gates and re-review
  remain required after these non-behavioral repairs.
- Post-repair fast/static evidence is clean: the independent exhaustive fixture
  passes on CPython 3.12 and 3.13; Ruff passes on both; compileall and diff-check
  pass; pinned Pyright 1.1.413 reports 0 errors, 0 warnings, and 0 informations.
  Direct inspection of the installed pytest fixture confirms
  `record_testsuite_property` is explicitly xUnit2-compatible and converts each
  `(name, value)` pair into suite-level XML metadata when JUnit output is active.
- The first parallel compatibility invocation outlived its 30-second capture,
  and the controller accidentally omitted the returned session IDs while
  formatting its partial output. Both processes completed, but their final exit
  output was therefore unavailable and is not counted as evidence. The exact
  same frozen package was rerun with retained session IDs: 115/115 tests pass on
  both CPython 3.12 and 3.13 (57 recall-feature, 42 recollection, 15 sensorium,
  and one non-8,192 scale reference test). Both retained executions exited zero.
  Final independent zero-finding re-review is now the remaining checkpoint gate.
- Final independent re-review returns APPROVE / CLEAR with zero unresolved
  findings. It confirms the prior temporal-preference wording LOW is closed,
  the suite-property change is metadata-only and xUnit2-compatible, every
  blocking scale assertion still precedes evidence recording, and both the
  2,048 snapshot plus 8,192 one-shot/four-page paths use real encrypted-ledger
  ingestion and public recall/resume. Reviewer static evidence independently
  reports Ruff clean, Pyright 1.1.413 at 0/0/0, and diff-check clean apart from
  expected LF-to-CRLF notices. Task 2.4's dedicated scale/reference sub-slice is
  CLEAN and ready for a checkpoint commit; broader Task 2.7 RSS/restart/p95 and
  portability evidence remains explicitly open.
- Checkpoint commit `96b24a9` (`Add Task 2.4 recollection scale gate`) records
  the CLEAN bounded streaming recollection scale/reference slice. Task 2.4 is
  now complete across deterministic Q32 scoring, content-digest exact scans,
  approximate/conflicted text retrieval, authenticated bounded continuation,
  independent exhaustive selection, and the current-host 8,192 evidence. Task
  2.5 calibrated selective recall begins from this clean commit; no calibration
  threshold or personal-memory production enablement is inferred from the
  synthetic Task 2.4 fixtures.
- Task 2.5 mapping confirms `calibration.py` and its dedicated tests do not yet
  exist. The work is split into pure calibration mathematics/schema, artifact
  selection/disabled states, and only then recollection authority integration;
  the first slice imports no ledger code and cannot mint production authority.
  Two initially requested specialized agent roles failed before work because
  their fixed model is unsupported on this ChatGPT Codex account; supported
  default-agent retries completed the same bounded architecture/statistics work.
- The Task 2.5 numerical freeze uses canonical decimal input, an exact rational
  Bonferroni tail `delta/m`, a 36-place decimal lattice, directed lower/upper
  binomial-CDF enclosures, exact-integer fallback for unresolved comparisons,
  and minimal upper serialization on a frozen 24-place lattice. Task 2 runtime
  code gains no SciPy/mpmath dependency; independent 60-place reference brackets
  were generated outside production with 160-digit regularized-beta inversion
  and cross-checked by a separate arbitrary-precision binomial recurrence.
- The first Task 2.5 RED adds only `test_cognition_calibration.py`. It binds nine
  literal boundary/interior/8,192-count results, five conservative reference
  brackets, the Bonferroni-family distinction, exact `n=0`/all-error behavior,
  and strict rejection of bool integers or noncanonical decimal inputs. The
  production module is intentionally absent at this point; the expected initial
  failure is import/collection of `aluclu.cognition.calibration`, not an unrelated
  runtime failure.
- The initial Task 2.5 RED is reproduced on both installed runtimes at the exact
  intended boundary: collection fails only because
  `aluclu.cognition.calibration` does not exist. The minimal GREEN now creates
  that pure module with no ledger or external numerical dependency. It validates
  exact non-bool counts/family bounds and canonical open probabilities, keeps
  `delta/m` as a reduced integer ratio, brackets the monotone binomial CDF with
  fresh directed Decimal contexts, falls back to an exact integer recurrence
  only when all precision tiers straddle the tail, and upper-rounds the proven
  36-place root enclosure onto the canonical 24-place output lattice. Artifact
  schema, deployment status, and recollection authority remain out of this
  numerical-kernel GREEN until the literal fixtures pass.
- Before executing the numerical GREEN, its internal Decimal multiplication
  callback is given an explicit callable type and the invalid-input test crosses
  the deliberately untyped API boundary through an explicit `Any` cast. This
  removes a broad type-ignore without changing numerical behavior; both runtime
  fixtures and the pinned static gates still have to prove the implementation.
- The first numerical GREEN run is identical on CPython 3.12 and 3.13: 30/31
  cases pass and only the uncorrected `k=0,n=100,delta=0.05,m=1` literal differs.
  Production returns `0.029513049607039934500476`, while the test expected
  `0.029513049607039932209963`; all independently bracketed cases, including the
  corrected `m=10` value and both 8,192-count cases, pass. No value is changed
  until the disputed literal is checked against the independent closed form.
- A separate 100-digit Decimal evaluation of the exact zero-error closed form,
  `1 - 0.05^(1/100)`, yields
  `0.029513049607039934500475785607...`; directed upper rounding to the frozen
  24-place lattice is exactly production's
  `0.029513049607039934500476`. The lone test literal was therefore wrong and is
  repaired; the solver is unchanged. Both runtimes must now rerun the full file.
- The repaired Task 2.5 numerical file is GREEN on both CPython 3.12 and 3.13:
  31/31 tests pass independently on each runtime. Static/style/compile gates and
  adversarial review remain open before this mathematical kernel can be called
  CLEAN.
- The first static pass reports no type, compile, or whitespace error: pinned
  Pyright 1.1.413 is 0/0/0, compileall passes, and `git diff --check` exits zero
  apart from the existing Windows LF-to-CRLF notice. Ruff alone requests two
  mechanical import-layout changes; its exact dry-run diff is applied with no
  behavioral edit, after which every fast gate will be rerun.
- After the import-only repair, both focused files remain 31/31 GREEN; Ruff,
  compileall, diff-check, and pinned Pyright 1.1.413 are all clean. The broader
  Task 2 compatibility package also exits zero on both CPython 3.12 and 3.13,
  excluding only the already-completed one-hour 8,192 scale case. No existing
  recall-feature, recollection, sensorium, or fast scale-reference behavior is
  regressed by the new pure numerical module.
- Two requested independent post-GREEN review turns failed before inspection
  because the collaborating account hit its usage limit. They produced no
  technical verdict and are not counted as review evidence. Local adversarial
  inspection therefore continues and the independent-review gate stays open.
- Local adversarial inspection finds a proof-level gap before declaring CLEAN:
  the 36-digit lattice candidate and its complement are currently constructed
  just before the fresh directed contexts, so a caller-mutated ambient Decimal
  precision can round the supposedly exact candidate. A new RED compares two
  distinct argument tuples with the same exact tail under normal versus hostile
  ambient contexts; production must be invariant to all caller Decimal state.
- The ambient-context RED fails identically on both runtimes at the intended
  boundary: a hostile six-digit/limited-exponent caller context raises
  `decimal.InvalidOperation` while scaling the first 36-digit lattice midpoint.
  The candidate and exact complement are moved inside each fresh 80+-digit,
  wide-exponent directed context. No solver, statistical, or serialization rule
  changes; the new invariant and full fixture file must now rerun.
- The ambient-context repair makes the complete numerical file 32/32 GREEN on
  both runtimes. The numerical contract is further bounded to at most the frozen
  36 fractional input digits so canonical validation cannot feed unbounded
  attacker-sized integers into Bonferroni arithmetic. The independent
  near-one `n=8192,k=8191` 60-place bracket is also promoted into the blocking
  fixture set after a direct CPython 3.13 probe returned its expected 24-place
  upper value in 8.81 seconds. These additions require a fresh two-runtime run.
- The near-one bracket and bounded-input additions pass with the rest of the
  file on both runtimes (35/35 each). Boundary coverage is extended once more
  to prove that exactly 36 fractional digits, `family_size=256`, and the
  no-evidence return remain accepted, while selected/error count 65,537 and
  family size 257 fail closed. These are contract-boundary tests, not a widening
  of the frozen solver limits.
- Final fast/static evidence for the expanded A1 kernel is clean: 39/39 focused
  tests pass on each of CPython 3.12 and 3.13; Ruff and compileall pass;
  `git diff --check` exits zero apart from the Windows line-ending notice; and
  pinned Pyright 1.1.413 reports 0 errors, 0 warnings, 0 informations. The final
  two-runtime Task 2 compatibility rerun is also 154/154 on each interpreter
  (57 recall-feature, 42 recollection, 15 sensorium, one fast scale reference,
  and 39 calibration cases); only the already-completed one-hour 8,192 scale
  fixture is excluded. Independent review remains the sole A1 CLEAN gate.
- Independent code/security review and independent mathematical review both
  return APPROVE with zero findings. The mathematical reviewer reproduces
  directed enclosure containment and exact-fallback direction against 250
  independent `Fraction` cases, confirms hostile ambient-context identity, and
  verifies the lattice upper-rounding proof. Before checkpointing, its
  nonblocking hardening suggestion is adopted: a new RED forces the exact
  symmetry root `n=101,k=50,tail=0.5` and requires the fallback to reduce the
  decimal lattice probability ratio before big-integer exponentiation. The
  ambient regression is also anchored to the already independently verified
  zero-error closed-form literal rather than a production-derived new value.
- The forced-fallback RED fails identically on both runtimes while still
  returning the correct root: only the tail reduction calls `gcd`; the lattice
  probability remains unreduced. The exact comparator now reduces its
  probability numerator/denominator before complement construction or any
  exponentiation. For the symmetry fixture this changes the big-integer basis
  from `5*10^35 / 10^36` to exact `1/2` without changing the comparison.
- The first post-repair test still fails because its `n=101` case is classified
  exactly by the directed Decimal path and therefore never enters the fallback;
  this is a test-oracle error, not a production error. A cache-cleared runtime
  probe finds `n=501,k=250` is the smallest sampled symmetry case that reliably
  invokes the exact comparator on the current frozen precision tiers. The RED is
  narrowed to that case; the `gcd` call itself remains the blocking assertion.
- The corrected `n=501,k=250` forced-fallback oracle and the strengthened
  ambient-context literal both pass on CPython 3.12 and 3.13. This proves the
  exact fallback is actually exercised and ratio reduction occurs; the full
  numerical/static suite and a delta re-review remain required.
- Final hardened A1 evidence is CLEAN: 40/40 calibration tests pass on each of
  CPython 3.12 and 3.13; Ruff, compileall, and diff-check are clean; pinned
  Pyright 1.1.413 remains 0/0/0. Both independent reviewers re-review the exact
  delta and retain APPROVE with zero findings. The mathematical reviewer also
  matches the reduced exact comparator against 100 additional deterministic
  `Fraction` cases and measures the `n=5001` symmetry probe improving from about
  4.75 to 2.18 seconds. Task 2.5-A1's pure conservative numerical kernel is
  ready for its checkpoint; calibration records/artifact authority are still
  deliberately absent and begin in A2.
- Checkpoint commit `ffaa47f` (`Add conservative calibration risk bounds`)
  records the CLEAN Task 2.5-A1 kernel. Task 2.5-A2 now begins with immutable
  calibration spec, label-provenance, and derived-label example schemas plus
  strict canonical codecs/digests. Artifact selection and runtime recall
  authority remain later sub-slices; this schema step cannot enable production.
- Task 2.5-A2's first RED defines three narrow immutable records and their
  domain-separated canonical codecs: label provenance, calibration spec, and a
  labeled example whose `error` bit is derived only from target/prediction IDs.
  The spec binds the exact label-provenance manifest digest so a threshold-grid
  mutation after labels are frozen changes the spec digest. Structural tuple
  errors fail at construction, while empty calibration sets and cross-set
  fit/calibration overlap remain representable evidence so the later builder can
  emit the plan-required explicit `DISABLED` artifact rather than losing the
  reason in a constructor exception. No artifact or recall code is touched.
- The A2 RED reproduces identically on CPython 3.12 and 3.13 at collection:
  `CalibrationPurpose` and the new schema surface do not yet exist in the
  committed A1 module. This is the intended missing-contract failure; the 40
  numerical tests were clean immediately before the schema RED and no unrelated
  runtime failure is being masked.
- Independent A2 architecture ruling confirms the frozen schema boundary: the
  spec binds both a distinct scorer ID and the label-provenance manifest digest,
  but no invented wall-clock validity fields; a labeled example does not repeat
  the stratum because its spec digest already binds the sole declared stratum.
  The RED is aligned to that minimal non-cyclic contract before GREEN. Because
  Task 1 canonical JSON is capped at 2 MiB, the implementation will also enforce
  a combined manifest-ID count that guarantees every constructible V1 manifest
  can actually round-trip through the required Task 1 codec.
- The minimal A2 schema GREEN passes 76/76 tests on each of CPython 3.12 and
  3.13. This proves current runtime construction, derived-error enforcement,
  strict object decoding, canonical round trips, frozen/slotted shape, digest
  stability, and structural/semantic boundary separation. Static typing/style,
  public package exports, deeper malformed-wire cases, and independent review
  remain open; this is not yet a CLEAN checkpoint.
- The first A2 static pass is behaviorally clean: compileall/diff-check pass and
  pinned Pyright 1.1.413 reports 0/0/0. Ruff requests only three deterministic
  import-order/source fixes (Enum ordering, `Callable` from `collections.abc`,
  and one merged calibration import); they are applied without changing the
  schema or wire behavior, and all gates must rerun.
- Before calling the schema public, a package-surface RED requires every A2 type
  and codec/digest function to be deliberately re-exported through
  `aluclu.cognition.__all__`. A separate binding oracle proves any post-label
  threshold-grid mutation changes the spec digest while the frozen example
  retains the original digest. Only the export oracle is expected to fail now.
- The package-surface RED fails at the first absent name,
  `CalibrationPurpose`, exactly as intended. The complete A1/A2 public surface
  is now explicitly imported and listed in `aluclu.cognition.__all__`; no
  wildcard or dynamic export is introduced. The focused export test and full
  schema file must rerun before the API is considered GREEN.
- After explicit exports, the complete calibration file passes 78/78 on both
  installed runtimes. The grid-mutation binding and package-surface oracles are
  GREEN alongside all A1 math and A2 codec cases. Static gates and additional
  boundary review remain open.
- The post-export static pass keeps compileall/diff-check clean and Pyright at
  0/0/0. Ruff's only finding is deterministic ordering in the expanded
  `__all__`; the exact suggested ordering is applied with no API membership or
  runtime change. All fast gates will be repeated after this mechanical repair.
- Pre-review adversarial coverage now binds strict enum identity, bool-versus-int
  boundaries, wrong schema/key sets, invalid observation/digest IDs, forged
  eligibility/error inputs, optional evidence limits, and the manifest's exact
  4,096 combined-ID round-trip ceiling. That V1 ceiling is intentionally below
  the pure A1 aggregate-count limit: it guarantees every constructible manifest,
  even with maximum 256-byte IDs, remains encodable by Task 1's mandatory 2 MiB
  canonical JSON boundary. These tests must pass on both runtimes before review.
- The expanded A1+A2 calibration file passes 97/97 tests on both CPython 3.12
  and 3.13, including the 4,096-ID boundary round trip and all new malformed
  cases. Static checks are now rerun across the implementation, package export,
  and tests before independent review.
- Final local/static A2 evidence is clean: Ruff and compileall pass,
  diff-check exits zero apart from Windows line-ending notices, and pinned
  Pyright 1.1.413 reports 0 errors, 0 warnings, 0 informations. The broader
  Task 2 compatibility package then passes 212/212 on each of CPython 3.12 and
  3.13 (57 recall-feature, 42 recollection, 15 sensorium, one fast scale
  reference, and 97 calibration tests); only the already-completed one-hour
  8,192 scale fixture is excluded. Independent A2 review remains open.
- Independent A2 review returns APPROVE with zero findings. It confirms strict
  canonical decoding, non-cyclic domain-separated bindings, derived-label
  construction, evidence-preserving semantic failures, the 4,096-ID payload
  boundary, Python 3.10 compatibility, public exports, and the forbidden-ledger
  dependency edge. Task 2.5-A2 is CLEAN and ready for checkpoint; no artifact,
  profile activation, recall authority, or production risk claim exists yet.
- Checkpoint commit `de4d74a` (`Add immutable calibration schemas`) records the
  CLEAN Task 2.5-A2 records/codecs. Task 2.5-B now begins with per-threshold
  counts, conservative coverage/risk gates, deterministic artifact selection,
  explicit disabled reasons, and self-verifying artifact encoding. The Task 2
  builder will be hard-wired to `TEST_ONLY`; production acceptance remains
  impossible in this slice.
- Task 2.5-B's artifact RED now binds per-grid selected/error counts, conservative
  coverage, maximum-coverage/higher-threshold selection, permutation-stable
  example/artifact digests, strict artifact round trips, digest-tamper rejection,
  and explicit reasons for zero data, overlap, label leakage, dataset/example or
  digest mismatch, insufficient selection, and no passing threshold. It also
  blocks any Task 2 production-promotion API and requires the artifact surface
  to be explicit in `aluclu.cognition.__all__`. Production types are absent, so
  collection should fail at the new contract before any old test runs.
- The B RED reproduces identically on both runtimes at collection because
  `CalibrationArtifactV1` does not exist in the CLEAN A2 checkpoint. The minimal
  GREEN now adds immutable threshold/artifact records, a pure builder that
  canonicalizes example order, evaluates every frozen threshold with A1's
  Bonferroni-corrected bound, selects by coverage then higher threshold, retains
  explicit semantic failure reasons, and emits only `TEST_ONLY`. Artifact bytes
  include a self-verifying domain-separated digest; no activation authority or
  recollection dependency is introduced.
- The first B GREEN runtime pass reaches 110/111 cases: every builder, disabled
  reason, selection, permutation, count, and digest-tamper oracle passes; only
  the deliberately absent package export fails at `CalibrationArtifactV1`.
  Artifact and nested-threshold JSON conversion/codec functions are now added to
  the explicit cognition API as well, and the full file must rerun on both
  runtimes before static validation.
- With explicit artifact exports, the full A1/A2/B calibration file is GREEN at
  111/111 on both CPython 3.12 and 3.13. This is runtime evidence only; the new
  artifact implementation and export list now enter Ruff, compile, diff, and
  pinned Pyright gates before any review or checkpoint.
- The first B static pass reports Pyright 0/0/0 and clean compile/diff behavior.
  Ruff finds only deterministic import/`__all__` ordering plus one test-only
  unused type import; its exact reorder/removal is applied without changing any
  artifact field, decision, digest, or API membership. Runtime and static gates
  must rerun after the mechanical repair.
- Post-repair B evidence is clean: 111/111 tests pass independently on CPython
  3.12 and 3.13; Ruff and compileall pass; diff-check exits zero apart from the
  Windows line-ending notice; and pinned Pyright 1.1.413 reports 0/0/0. The
  exact artifact/authority boundary and threshold-selection math now enter two
  independent reviews while the broader Task 2 compatibility package runs.
- The post-repair broader Task 2 compatibility gate completes at 226/226 on
  each of CPython 3.12 and 3.13 with exit code zero. It covers recall features,
  recollection, sensorium, the fast scale reference, and all 111 calibration
  cases; only the already-completed one-hour 8,192-observation fixture is
  excluded. This establishes no regression across the current Task 2 surface,
  but Task 2.5-B remains uncommitted until both independent reviews are clean.
- Independent B reviews do not yet accept the checkpoint. The statistical
  review finds the implementation equations correct but identifies four
  surviving test mutants: builder-level Bonferroni wiring, eligibility
  exclusion, observed-error counting, and conservative non-terminating Q24
  coverage rounding are not bound by adversarial artifact fixtures. The
  code/authority review additionally demonstrates that a self-consistent
  `DISABLED + PRODUCTION_ACCEPTED` wire can currently decode when supplied an
  arbitrary acceptance digest. Five regression oracles are added before the
  narrowest GREEN repair: bind the four already-correct statistical paths and
  reject production deployment status unless the artifact is a clean
  statistical pass with a chosen passing threshold and no disabled reasons.
- The five new adversarial cases run first on CPython 3.12: all four statistical
  wiring oracles pass unchanged, while the crafted, freshly re-digested
  `DISABLED + PRODUCTION_ACCEPTED` artifact is accepted and produces the sole
  expected RED. This reproduces the authority review's HIGH finding without a
  stale-digest shortcut. The minimal GREEN is confined to the artifact relation
  validator; no builder threshold, count, bound, selection, or digest algorithm
  changes.
- The minimal relation repair turns all five review regressions GREEN on both
  CPython 3.12 and 3.13. A disabled artifact can no longer carry production
  deployment status even when an attacker recomputes its public self-integrity
  digest; production acceptance still grants no runtime authority in Task 2,
  and the later activation boundary must require separately trusted exact
  evidence. The full calibration and static gates now rerun before re-review.
- Post-review-repair validation is locally clean: the expanded calibration file
  passes 116/116 on both CPython 3.12 and 3.13; Ruff and compileall pass;
  diff-check exits zero apart from the Windows line-ending notices; and pinned
  Pyright 1.1.413 reports 0 errors, 0 warnings, 0 informations. The reviewers
  now re-evaluate the exact regression/validator delta; B remains uncommitted
  until both replace their prior REQUEST CHANGES verdicts with approval.
- Both independent re-reviews now return APPROVE with zero remaining findings.
  The statistical reviewer confirms that all four new builder oracles kill the
  exact Bonferroni, eligibility, error-count, and coverage-rounding mutants. The
  code/authority reviewer independently recomputes the crafted artifact digest
  and confirms decode now rejects the prior HIGH case with `production artifact
  requires statistical pass`. The expanded broader Task 2 compatibility gate
  also passes 231/231 on each of CPython 3.12 and 3.13. Task 2.5-B is CLEAN for
  deterministic `TEST_ONLY` artifact construction; activation, process-local
  tightening, recollection `ProfileUnavailable`, and Task 12 acceptance remain
  explicitly outside this checkpoint.
- Checkpoint commit `a22fee5` (`Add deterministic calibration artifacts`)
  records the CLEAN Task 2.5-B builder, immutable artifact wire, explicit
  disabled evidence, conservative simultaneous-risk selection, authority
  invariant repair, and adversarial tests. Task 2.5-C now begins at this exact
  base: strict compatible-profile activation and recollection integration must
  fail closed unless every frozen scorer/normalizer/feature/boundary/dataset,
  purpose, stratum, threshold, deployment, and trusted-evidence binding agrees.
- Task 2.5-C is split into three independently reviewable slices so authority
  cannot be smuggled into the scan path: C1 prepares an authenticated
  process-local profile only after recomputing the artifact against its exact
  spec and explicit trust scope; C2 adds monotone policy tightening and binds
  effective policy/profile digests; C3 integrates the closed
  `ProfileUnavailable`/calibrated-exact state machine after cursor suspension
  and direct-read revalidation. C1 REDs first cover TEST_ONLY harness gating,
  production trust separation, every runtime compatibility field, disabled
  artifacts, grid/gate/selection revalidation, and authority lookalikes.
- The C1 RED stops identically at collection on the first absent contract,
  `ActiveCalibrationProfileV1`; none of the new activation tests can fall
  through to the already-green B implementation. The V1 purpose enum currently
  has only `PERSONAL_MEMORY_TEXT`, so there is no constructible valid-but-
  different purpose fixture; the mismatch reason remains reserved for a future
  enum expansion, while all currently representable compatibility axes receive
  executable REDs.
- After the host reboot, the global Python launcher no longer resolves the
  former `py -3.12` registration, but the repository-local interpreters remain
  intact at `.venv` CPython 3.12.13 and `.venv313` CPython 3.13.5. The C1 import
  RED is reproduced with the local 3.12 interpreter before implementation; this
  is recorded as an environment-path change, not a product failure or a reason
  to discard the checkpoint.
- The first C1 GREEN adds immutable profile/compatibility records, closed typed
  unavailable reasons, a non-serializable TEST_ONLY capability, and a
  process-local authenticated active profile. Activation round-trips the spec
  and artifact through their strict codecs, checks self-integrity, recomputes
  the frozen threshold grid, exact coverage/risk values, pass predicates, and
  deterministic winning threshold, then resolves every representable runtime
  compatibility field before granting authority. TEST_ONLY requires a genuine
  live harness instance; production requires a separately presented exact
  acceptance digest and cannot infer trust from the artifact's public digest.
- Adversarial C1 expansion now rejects a dict lookalike, an exact-type cloned
  harness carrying a stolen authenticator, ambiguous test-plus-production
  authority, spec rebinding, label-manifest rebinding, a re-digested false risk
  row, a re-digested grid mutation, a forged gate bit, and a non-winning passing
  selection. The active handle's profile digest is independently reproduced
  from its domain-separated scope/spec/artifact frame; exact-type clones and
  post-creation field mutation fail its process-local authenticator/identity
  check. The expanded calibration suite passes 134/134 on both CPython 3.12.13
  and 3.13.5; Ruff 0.16.6, cognition compileall, and pinned Pyright 1.1.413 are
  clean at 0 errors, 0 warnings, 0 informations. Broader Task 2 regression and
  independent C1 review remain open, so this slice is GREEN but not CLEAN.
- Independent C1 review returns REQUEST CHANGES/BLOCK rather than accepting the
  first GREEN. Two authority reviewers identify one HIGH flaw: the public
  `trusted_production_acceptance_digest` string lets a caller echo an arbitrary
  digest embedded in a freshly re-digested artifact, after which the activation
  layer itself signs the untrusted claim. They also identify bounded CPU
  amplification because unauthorized calls reach full Clopper-Pearson replay,
  and malformed exact-type active objects can leak raw attribute/type errors.
  The statistical reviewer finds the implementation math correct but rejects
  acceptance evidence until false-positive fixtures separately kill removal of
  the minimum-selected, minimum-coverage, and maximum-risk conjuncts and until
  disabled-reason sorted/unique validation is mutation-bound.
- The review repair removes the raw production-trust parameter entirely.
  `PRODUCTION_ACCEPTED` remains parseable future evidence but cannot produce an
  active profile in Task 2; it returns `PRODUCTION_ACCEPTANCE_UNTRUSTED` until a
  non-serializable artifact-bound trust capability is supplied by the later
  Task 12/host trust boundary. Cheap TEST_ONLY/production authority rejection
  now follows strict spec/artifact self-integrity checks and precedes expensive
  statistical replay. Active/test capability validation checks live identity
  before field access, validates every digest/ID/enum/Q32/deployment relation,
  and normalizes damaged exact-type handles to `InputBoundaryError`.
- New regression oracles forge validly re-digested single-threshold artifacts
  where exactly one of minimum selected count, Q24 coverage, or exact
  Clopper-Pearson risk fails, then set `passed=true`; all three are rejected as
  `ARTIFACT_GATE_MISMATCH`. Reversed and duplicate disabled reasons are rejected
  by the wire boundary. A semantically forged artifact without a TEST_ONLY
  capability proves cheap authority denial precedes replay, and malformed spec,
  artifact, active-handle, and harness fields expose only controlled boundary
  errors. The repaired calibration suite passes 145/145 on CPython 3.12.13 and
  3.13.5; the broader Task 2 package passes 260/260 with the completed one-hour
  8,192 fixture deliberately deselected on each runtime (95.20 s and 90.68 s).
  Ruff 0.16.6, cognition compileall, git diff-check, and pinned Pyright 1.1.413
  are clean. Reviewer re-approval remains mandatory before C1 is CLEAN.
- All three independent C1 re-review lanes now approve with zero findings. The
  statistical lane independently verifies the three isolated false-positive
  conjunct mutants and both disabled-reason ordering/uniqueness mutants. The
  code/security and authority/architecture lanes each confirm the prior HIGH
  raw-digest self-authorization path is absent, unauthorized work is rejected
  before numerical replay, damaged handles expose controlled boundary errors,
  and the active handle authenticates the full C1 field set while its public
  digest binds scope/spec/artifact. Task 2.5-C1 is therefore CLEAN for
  TEST_ONLY process-local activation and typed fail-closed compatibility.
  Production activation deliberately remains unavailable until Task 12 supplies
  a separately reviewed artifact-bound trust capability; C2 policy tightening
  and C3 recollection integration remain outside this checkpoint.
- Checkpoint commit `5757cc5` (`Add authenticated calibration profile
  activation`) records the CLEAN C1 boundary. Autopilot state is advanced to
  `C1_CLEAN_C2_RED_NEXT` with the two-runtime, static, broad-regression, and
  three-review evidence preserved. C2 now begins fixture-first: a process-local
  tightening must bind the exact active profile, base policy, runtime scorer,
  normalizer, feature spec, and derived effective policy digest. It may only
  reduce record/top-k/output budgets, raise score/margin floors, revoke
  approximate/incomplete permissions, or force abstention. A base below either
  calibrated floor, any authority-expanding request, serialized lookalike,
  exact-type clone, field mutation, algorithm rebinding, or malformed handle
  must fail closed. Recall state transitions remain deliberately untouched
  until the independently reviewed C3 integration.
- The C2 RED reproduces on the repository-local CPython 3.12.13 interpreter at
  collection: `active_scorer_id` is absent from the CLEAN C1 code, so none of
  the new tightening, digest-binding, monotonicity, algorithm-compatibility, or
  anti-forgery tests can fall through to old green behavior. Minimal GREEN is
  now limited to the scorer identity, authenticated tightening capability, its
  validation boundary, and explicit package exports; C3 recall behavior remains
  out of scope.
- The first C2 GREEN passes the expanded calibration/policy file at 165/165 on
  CPython 3.12.13 and 3.13.5, and the unchanged recollection regression on
  CPython 3.12. Ruff initially reports only import/export ordering and fixes
  both mechanically; compileall and diff-check are clean. Pinned Pyright finds
  13 static argument-type errors at one dynamic `dict[str, object]` expansion
  into the private handle constructor. Runtime values are correct, but the
  checkpoint is not statically clean: construction is changed to explicit
  typed arguments, while additional REDs bind the handle to its original base
  policy/profile and preserve the text-recall `top_k >= 2` margin invariant.
- After the typed-construction repair and rebinding/top-k additions, the focused
  C2 file passes 167/167 on both runtimes, Ruff is clean, and pinned Pyright
  reports 0/0/0. The broader Task 2 package passes 282/282 with only the
  previously completed one-hour 8,192-observation replay deselected on each
  runtime (206.26 s on 3.12, 201.06 s on 3.13). Independent architecture review
  returns APPROVE/CLEAR with zero findings and confirms C3 must apply this
  handle before opening a cursor. Before accepting C2, self-review adds literal
  scorer-ID, equality/no-op, false-versus-true force-abstain digest, exact-bool,
  and public-boundary lookalike oracles so shared helpers cannot mask a protocol
  identity mutation or ignored conservative control.
- The final self-review expansion passes 175/175 on CPython 3.12.13 and 175/175
  on CPython 3.13.5; Ruff, cognition compileall, diff-check, and pinned Pyright
  1.1.413 remain clean at 0 errors, 0 warnings, 0 informations. Three independent
  C2 lanes approve the current live diff with zero findings: architecture marks
  the boundary CLEAR, code/security finds no masking fallback or authority
  expansion, and adversarial mutation review finds no surviving mutant across
  all three budget ceilings, both calibrated floors, both permissions,
  force-abstain identity, algorithm/profile/base/effective-digest binding,
  top-two margin viability, or process-local anti-forgery behavior. Task 2.5-C2
  is therefore CLEAN as an authenticated effective-policy capability. It does
  not yet alter recall results; C3 must validate and freeze the active profile,
  base policy, and tightening before opening a cursor, bind continuations to the
  effective/profile digests, and implement typed fail-closed calibrated recall.
- C2 mutation audit adds a surviving base-policy oracle: a calibrated text
  tightening must also reject an already-constructed base policy with
  `top_k=1`, even when the caller does not request a `top_k` change. The RED
  fails because the earlier implementation only enforced the floor on requested
  values; the GREEN keeps the broad `RecallExecutionPolicyV1` contract intact
  for older exact-recall paths and enforces `top_k >= 2` only at the calibrated
  tightening boundary.
- Checkpoint commit `bd6590d` (`Add authenticated recall policy tightening`)
  records the CLEAN C2 capability after the added base-policy `top_k` repair,
  two-runtime focused/broad regression gates, static gates, and three
  independent approvals. Task 2.5-C3 starts from this exact base; C2 still
  grants no recollection authority by itself.
- C3 freezes the public state machine before implementation: legacy text recall
  remains approximate only when no calibration pair is supplied and the caller
  explicitly allows approximate output. A personal/answer-authority path with
  approximation disabled and no pair returns typed `MISSING` before encoding or
  opening a cursor. Calibrated exact recall requires both a live
  `ActiveCalibrationProfileV1` and its live bound `RecallPolicyTighteningV1`;
  partial, cloned, mutated, forged, or rebound pairs fail closed rather than
  falling back. The private scan snapshot copies every effective field before
  cursor creation, and continuations bind the effective-policy digest plus
  active-profile digest.
- The calibrated completion contract reuses `ExactRecollection` with basis
  `CALIBRATED_TEXT_MATCH` and a conditional frozen evidence record binding the
  profile digest, effective-policy digest, score, and margin. Same-content
  occurrences remain one content identity for conflict detection and the
  deterministic observation order selects the winning occurrence; only exact
  content-digest queries produce occurrence ambiguity. Before exact promotion,
  both the winner and any distinct-digest runner-up responsible for the margin
  are direct-read and revalidated after cursor suspension. Margin equality is
  conflict, score equality is eligible, and the effective output budget can
  still force payload abstention.
- After an interrupted agent turn, the worktree retained both the partial C3
  implementation and fixture additions. The first recovered full recollection
  run produced four honest failures: the prior uncalibrated
  `APPROXIMATE_DISABLED` assertion had not yet adopted the new typed missing-
  profile boundary; two agent assertions incorrectly treated the nested
  evidence record as the top-level result; and a runner-up fixture used equal
  retrieval text, correctly yielding conflict at zero margin. The tests were
  repaired to the frozen contract rather than changing production semantics.
  The expanded focused matrix now covers legacy compatibility, missing-profile
  pre-scan behavior, partial/forged capabilities, forced abstention, every
  effective budget/threshold/permission, inclusive score and strict margin,
  continuation cross-mode binding, same-digest deterministic selection,
  post-cursor winner/runner-up reads, runner-up mutation, non-text argument
  rejection, and pre-cursor policy freezing. Final broad regression and
  independent review gates remain open, so C3 is GREEN but not CLEAN.
- Independent architecture review then finds and reproduces one HIGH authority
  defect in the first GREEN: the conflict branch checked a nonpassing margin
  only when two distinct content identities existed, so a lone candidate whose
  defined margin (`score - 0`) exactly equalled the calibrated floor was still
  promoted to exact. A new isolated fixture fixes both values at
  `3108237854` and fails with `ExactRecollection` where approximate/fail-closed
  output is required. The minimal repair makes every calibrated promotion,
  including the one-identity case, require
  `margin_q32 > effective.minimum_margin_q32`; equality now returns
  `ApproximateCandidates` only when explicitly permitted and otherwise
  `APPROXIMATE_DISABLED`. Both parameterized boundary cases pass on CPython
  3.12.13 and 3.13.5. Architecture, code/security, and adversarial mutation
  re-review all approve the repaired decision tree with zero remaining
  findings. The complete repaired recollection file has 66 collected tests;
  static and broad Task 2 gates are rerun from this exact state before CLEAN.
- Final C3 validation on the repaired state passes the 66-test recollection
  file on both CPython 3.12.13 and 3.13.5. The expanded Task 2 package selects
  475 tests across observation, sensorium, boundary, replay, recall features,
  recollection, calibration, determinism, end-to-end, and scale, and passes
  475/475 on each runtime. Only the previously completed approximately
  one-hour `test_8192_observation_replay_keeps_completed_state_bounded` fixture
  is explicitly deselected for this repeat; the other scale test runs. Ruff
  0.16.6, cognition/test compileall, `git diff --check`, and pinned Pyright
  1.1.413 pass at 0 errors, 0 warnings, 0 informations. Architecture,
  code/security, and adversarial mutation lanes each return APPROVE with zero
  unresolved findings after the exact-margin repair. C3 is CLEAN for the
  TEST_ONLY mechanical calibrated-recollection state machine; it does not
  assert real held-out calibration accuracy or production activation, which
  remain dependent on Task 12 evidence. Task 2.6 reconsolidation is next;
  Task 2 as a whole is not yet CLEAN and ALC-R0 cannot start yet.
- Checkpoint commit `350317d` (`Add calibrated selective recollection`)
  records the independently reviewed C3 implementation and evidence. The
  tracked worktree is clean after this commit. Task 2.6 now starts from this
  exact base, not from the interrupted uncommitted C3 snapshot. Its first RED
  must establish a content-free immutable lineage record, deterministic
  proposal identity, same-session verified parent/trigger hash checks,
  append-once crash retry, explicit correction reason, no read-triggered
  mutation, and no resurrection after either endpoint is shredded. Task 2.7
  vertical E2E/scale/portability and Task 2.8 final independent gate remain
  downstream; no Task 2 or ALC capability claim is opened by C3 alone.
- Task 2.6 starts fixture-first from clean handoff commit `79afc42`.
  `tests/test_cognition_reconsolidation.py` first pins a deterministic pure
  `recon:` proposal, one content-free append-only correction child, unchanged
  parent/trigger hashes, lost-return/reopen idempotence, rejection of nonexact
  or self-parent inputs, and no parent-content resurrection after shred. The
  initial CPython 3.12.13 run is the expected RED at collection:
  `ModuleNotFoundError: No module named 'aluclu.cognition.reconsolidation'`.
  No existing Task 2 test was weakened to reach this RED. Before GREEN, the
  remaining explicit oracles must expand to tombstoned/stale/cross-ledger
  endpoint rejection, malformed lineage wire, cursor-before-commit,
  conflicting observations, and a real subprocess lost-return boundary.
- Task 2.6 first implementation adds a content-free `ReconsolidationRecordV1`,
  deterministic framed-SHA256 `recon:` identity, pure proposal, live
  parent/trigger read-back under one passed `VerifiedLedgerSession`, and one
  `append_once`. The first five fixtures pass on CPython 3.12.13, but this is
  GREEN only, not CLEAN. An expanded decoder fixture then produces a second
  isolated RED at collection because the strict V1 JSON decoder is missing.
  The decoder now accepts exactly the twelve permitted schema/lineage fields,
  reconstructs enum and hash-bound identity, and rejects extra content fields.
  Stale hash, shredded endpoint, active cursor, and cross-ledger provenance
  checks expand the focused set to 9/9 GREEN. A real subprocess appends the
  lineage and exits with code 93 before caller-visible completion; reopen and
  retry return duplicate with exactly one lineage record, making 10/10 GREEN.
  Reverse edges, excessive-parent wire fields, bool-as-sequence, changed
  reason identity, and malformed calibrated evidence then expand the focused
  matrix to 12/12 GREEN on CPython 3.12.13. Wider Task 2 regression, both
  runtime/static gates, independent review, and final Task 2.6 handoff remain
  open; no native model or production learning claim follows from this fixture.
- The focused Task 2.6 matrix expands to 15/15 on both CPython 3.12.13 and
  3.13.5 after parameterizing parent/trigger shredding, proving two
  contradictory correction observations remain distinct, and rejecting a bare
  ledger or closed verified session. Ruff, compileall, `git diff --check`, and
  pinned Pyright 1.1.413 are clean on this final source snapshot (Pyright:
  0 errors, 0 warnings, 0 informations). The final 11-file Task 2 regression
  package passes 490/490 selected tests on CPython 3.12.13 and 3.13.5 from
  this source snapshot. Only the already-completed approximately one-hour
  8192-observation replay fixture is explicitly deselected for this repeat;
  the other scale tests run. Until independent review accepts the slice, Task
  2.6 remains GREEN, not CLEAN.
  Calibration/profile digests in a lineage edge are metadata copied from the
  supplied exact-recollection object; endpoint read-back authenticates the
  observations, but cannot itself attest that a caller-produced calibration
  execution really occurred. Downstream code must not treat this metadata as
  a signed calibration authority or factual-truth certificate. A real held-out
  calibration/release decision remains Task 12 evidence.
- Checkpoint commit `9da4188` (`Add reconsolidation lineage green checkpoint`)
  records the Task 2.6 implementation, RED/GREEN fixtures, two-runtime 490-test
  regression result, and exact remaining independent-review gate. The tracked
  worktree is clean at this checkpoint. The commit name deliberately says
  GREEN: Task 2.6 is not CLEAN, Task 2.7 cannot yet consume it as an accepted
  upstream gate, and Task 2 as a whole remains open.
- Task 2.6 independent review attempts at clean HEAD `04acc16`: the
  code/spec/security lane inspects the five changed files plus the Task 2 plan
  and supporting recollection/ledger contracts, reruns 15 focused tests on
  CPython 3.13.5, Ruff, compileall, pinned Pyright, and diff-check, and returns
  COMMENT with zero Critical/High/Medium findings and one Low acceptance-
  wording ambiguity. The pure proposal API cannot read ledger tombstones or
  live hashes, although commit already rejects those endpoints before append.
  The Task 2.6 RED oracle is clarified to distinguish proposal-time typed/
  malformed-input rejection from commit-time live-endpoint rejection; the
  no-invalid-lineage threshold is unchanged. The separate architect lane
  fails before review with HTTP 400 because its fixed `gpt-5.4-mini` model is
  unsupported on this Codex account. The authoring lane does not replace this
  missing independent evidence. Combined review is UNAVAILABLE/NOT APPROVED;
  Task 2.6 remains GREEN, not CLEAN, and Task 2.7 implementation waits for a
  supported independent architecture path.
- Documentation repair commit `5abfdb8` clarifies pure-proposal versus
  commit-time liveness rejection. The same focused Task 2.6 suite reruns 15/15
  on CPython 3.13.5; the code/spec/security lane re-reviews the sole Low
  finding and returns APPROVE with zero remaining issues. A separate supported
  `project-architect` lane independently runs 15/15 focused tests on CPython
  3.12 and returns WATCH, not BLOCK: a caller can construct a well-formed
  calibrated `ExactRecollection`, so its profile/policy digests in lineage
  cannot attest actual calibration execution. The trajectory had already
  documented this, but normative Task 2 plan §6.6 did not. The plan/API
  docstrings now explicitly mark these tags as caller-declared,
  non-authoritative metadata and Task 2.7 gains a lineage-consumer oracle that
  forbids promotion to selection proof, activation authority, or truth. This
  is a specification/contract repair, not a claim that the Task 2.7 oracle has
  run. Independent re-review of the amended snapshot, relevant static/focused
  tests, and exact checkpoint commit remain open before Task 2.6 CLEAN.
- Final independent re-review on exact clean commit `86d5468` closes both Task
  2.6 lanes. The code/spec/security lane reports APPROVE with zero findings,
  confirms the post-`5abfdb8` diff is limited to the restrictive authority
  contract/docstrings/trajectory, reruns 15/15 focused tests, Ruff, compileall,
  pinned Pyright (0/0/0), and diff-check, and finds no lowered numeric,
  statistical, rejection, or production-activation threshold. The independent
  architecture lane reports CLEAR with no remaining blocker or watch item,
  independently runs 15/15 focused tests on CPython 3.12 plus scoped Ruff and
  diff-check, and confirms the caller-constructible recall tags are now an
  explicit non-authoritative representation choice. It assigns the forged-tag
  no-promotion test to the mandatory Task 2.7 consumer gate, without claiming
  that gate has run. Both lanes see an empty tracked/untracked status on the
  reviewed commit. Task 2.6 explicit immutable reconsolidation gate: CLEAN for
  the bounded TEST_ONLY mechanical slice. This grants no production
  calibration, factual-truth, neural-learning, ALC-R0, or whole-Task-2 claim.
  Task 2.7 full vertical/restart/scale/portability evidence is next.
- Task 2.6 final review evidence is checkpointed by commit `558f7f8` (`Close
  Task 2.6 reconsolidation gate`) on top of normative-authority repair
  `86d5468`. The tracked worktree is clean before Task 2.7 begins.
- Task 2.7 starts with a new small full-vertical fixture rather than treating
  prior unit/regression success as integration evidence. Early REDs expose
  fixture/contract misunderstandings without changing production semantics:
  participant IDs must be sorted; successful new ingest is `APPLIED`, not an
  invented `NEW`; a duplicate retried against a much older state correctly
  returns replay-required, so lost-return duplicate proof runs immediately
  against its matching pre-state; replay reproduces the observation core while
  advancing its exhaustive checkpoint across the non-observation lineage
  record; and a `recon:` ID is rejected when constructing an observation-only
  direct-recall query. After repairing the fixture to those existing
  contracts, the vertical scenario passes 1/1 on CPython 3.12.13 and 3.13.5,
  with Ruff, compileall, and pinned Pyright 1.1.413 at 0 errors/warnings/info.
  The scenario exercises typed user/model/tool ingestion and explicit
  boundaries, storage-pure duplicate retry, direct and TEST_ONLY calibrated
  exact recall with observation-not-fact status, an equal-score near-tie
  conflict, forced abstention, content-free correction lineage, reopen,
  one-record replay pages, endpoint hash stability, strict lineage decoding,
  no lineage-to-observation promotion, and parent shred/no-resurrection. This
  is Task 2.7 GREEN slice 1 only: real process-restart page splitting, final
  scale benchmark/evidence artifact, and portability scope remain open.
- User-requested future neural-host research is recorded without starting
  ALC-R0 before Task 2 CLEAN. The current machine is an i7-12650H (10 cores/16
  logical), 16 GB RAM, RTX 4050 Laptop GPU with 6141 MiB reported VRAM, NVIDIA
  driver 610.78, and about 80.8 GB free on C:. The primary ALC-R0 candidate
  remains the preregistered `HuggingFaceTB/SmolLM2-135M`, current Hub revision
  `93efa2f097d58c2a74874c7e644dbc9b0cee75a2`: ungated Apache-2.0 base weights,
  `LlamaForCausalLM`/`model_type=llama`, safe 269 MB BF16 safetensors, and an
  official open SmolLM repository with Nanotron pretraining/checkpoint paths.
  It is selected as the first dissectible host/teacher because its full forward
  can be reimplemented and weight-parity checked locally within this hardware
  class. This is a host-selection research note, not a downloaded-model,
  training, ALC-0 capability, or native-ALUCLU claim; exact artifact hashes and
  local fit must still be frozen and executed only after Task 2 CLEAN.
- Task 2.7 GREEN slice 2 strengthens the vertical fixture at the actual process
  boundary. The first RED invokes a not-yet-existing replay worker and fails
  with exit code 2 / missing `tests/helpers/task2_vertical_worker.py`; no
  production behavior is changed to obtain the failure. The worker then opens
  the same encrypted ledger for exactly one bounded replay page per invocation.
  Incomplete pages emit only the public strict-JSON
  `SensoriumReplayContinuationV1`; every next page runs in a fresh Python
  process and resumes through Task 1's verified checkpoint. Process-local
  `RecallContinuationV1` is never serialized: direct, calibrated, conflict,
  and forced-abstention queries restart and complete from sequence zero in the
  final fresh process.
- The pre-shred vertical result is identical for six one-record processes, two
  three-record processes, and one 64-record process: final sensorium-state
  hash, all episode IDs and authenticated record hashes, calibrated selected
  observation, ordered conflict candidates, forced-abstention reason, and
  decoded lineage metadata all agree. The lineage parent is deliberately a
  caller-fabricated `CALIBRATED_TEXT_MATCH` recollection with fixed `e...`
  profile and `f...` effective-policy tags. Fresh-process decoding preserves
  those exact annotations but the `recon:` child remains unqueryable as an
  observation, carries no content, and exposes no verified-fact field. This is
  the mandatory non-authority consumer oracle, not evidence that the fabricated
  calibration ran or is trustworthy.
- After parent shredding, a new process-per-page replay starts from the baseline
  profile rather than reusing a pre-shred continuation. It matches a fresh
  one-shot process, returns `NoRecollection` for the parent, retains the
  tombstone, and strictly decodes the still content-free lineage without
  resurrecting parent plaintext. The final vertical fixture passes 1/1 on
  CPython 3.12.13 and 3.13.5. The 99-test related package spanning vertical,
  prior E2E, sensorium, recollection, and reconsolidation passes 99/99 on
  CPython 3.13.5. Scoped Ruff, compileall, `git diff --check`, and pinned
  Pyright 1.1.413 pass at 0 errors, 0 warnings, 0 informations. This remains a
  Task 2.7 GREEN checkpoint: the real 8,192-observation machine-readable scale
  artifact and honest multi-OS/Python portability evidence are still open, so
  neither Task 2.7 nor Task 2 is CLEAN.
- Task 2.7 scale runner implementation checkpoint (not the final scale PASS):
  the first focused RED was a missing `aluclu.cli.benchmark_cognition_task2`
  module on CPython 3.13. The runner now fixes public counts at
  2,048/4,096/8,192 and exact 512-byte canonical content, grows one physical
  encrypted ledger to each exact checkpoint, samples fresh-process streaming
  recall against an empty-session RSS worker, compares direct-ID p95 with a
  Task 1 `session.read` baseline, measures logical/persistent bytes and
  one-shot/paged/fresh-process result digests, and atomically records canonical
  JSON including environment, seed, raw samples, exact git SHA, and checks.
  A private 4/8/16 and 64-byte fixture tests the real ledger path without
  claiming the fixed gate. The first implementation was corrected before this
  checkpoint: scans now occur at exact-N heads rather than after all 8,192
  appends, and small-fixture RSS keys follow its counts rather than fixed keys.
- Independent code review requested changes in three measurement defenses:
  unknown RSS could have been clamped to zero, fresh restarted scan's extra
  full-verification count was not aggregated, and plaintext scanning covered
  only the query marker. Regressions now require nonzero/comparable raw RSS
  peaks alongside deltas, fail on restarted-worker verification, and scan
  actual canonical/raw observation content plus the retrieval marker across
  the work directory. The first broad digest sentinel produced an intentional
  RED in the healthy encrypted ledger: Task 2's authenticated append lineage
  witness stores the content digest as integrity metadata in SQLite, not the
  observation plaintext or a retrieval index. The leak oracle therefore
  excludes the digest but retains actual content bytes; the earlier false
  positive is recorded rather than hidden. A targeted diagnostic found digest
  sentinels in `cognition.sqlite3`, not canonical/raw content or the marker.
  This is an explicit privacy-boundary distinction for later review.
- Post-repair focused scale tests pass 17/17 on CPython 3.12.13 and 3.13.5.
  The related Task 1/2 benchmark and Task 2 scale regression package passes
  with its existing hour-scale 8,192 pytest case explicitly deselected (the
  separate normative 8,192 artifact has not yet run). Ruff, compileall,
  diff-check, and pinned Pyright 1.1.413 with the 3.13 interpreter pass at
  0 errors, 0 warnings, 0 informations. A second independent reviewer and
  verifier pass was attempted but both agents stopped on usage-limit errors;
  no approval is inferred. The next gate is a clean-SHA full 8,192/512 run,
  followed by artifact audit, independent re-review when available, and
  cross-platform portability evidence. Task 2.7 and Task 2 remain OPEN.
- Task 2.7 portability work is isolated on `codex/task27-portability` while the
  clean `000e259` scale run continues in the main cognition worktree. A 256-
  observation public-API smoke now ingests deterministic user/model/tool
  observations with explicit episode boundaries, verifies a storage-pure first
  duplicate, closes the encrypted ledger, and uses a fresh Python process to
  compare one-shot and seven-page replay state, direct exact recall, and
  one-shot/paged text candidate ordering. The first RED was the deliberately
  missing `tests/helpers/task2_portability_worker.py` (subprocess exit 2),
  after the 256 real appends passed. The worker is now implemented and the
  smoke passes 1/1 on local Windows CPython 3.12.13 and 3.13.5. The other
  frozen determinism and recall-feature vector tests pass 68/68 on both
  runtimes; the combined selected portability group is 69 tests. Ruff,
  compileall, and pinned Pyright 1.1.413 report clean/0 errors, 0 warnings,
  0 informations for the two new Python files. No production semantics are
  changed by this smoke.
- A manual `workflow_dispatch` GitHub Actions matrix is prepared for Windows
  x64, Linux x64, and macOS arm64, each under CPython 3.10–3.13. It runs the
  frozen vector files and the 256-observation fresh-process smoke and retains
  per-lane JUnit output. GitHub's hosted-runner and setup-python documentation
  was checked when selecting current runner labels; no workflow has run or
  been pushed, so neither its twelve lanes nor broad portability is claimed
  PASS. The accepted Task 1 static test-key profile is used rather than
  pretending this exercises the separate OS-keyring E2E gate. Cross-platform
  evidence remains OPEN until actual CI or equivalent host results exist.
- Additional local portability probing: CPython 3.11.13 in an isolated
  `.venv` passes the complete 69-test selected vector/smoke group. CPython
  3.10.21 was installed into a separate local research environment, and its
  68 frozen determinism/feature tests passed, but the first 256-observation
  smoke timed out at the test harness's 180-second fresh-process boundary.
  This is a recorded negative run, not a platform PASS or a production
  correctness failure: all 256 ingests completed, and the fresh-process
  worker was still consuming CPU when the subprocess cap fired.
- The failed test's own encrypted ledger was reopened with that same CPython
  3.10 worker for a stage-level reproducer. It completed correctly with
  one-shot replay 16.102 s, paged replay 15.461 s, direct recall 0.059 s,
  one-shot text recall 15.769 s, and paged text recall 15.796 s. The first
  interruption was therefore a host-load-sensitive harness duration; the
  acceptance criteria contain no 180-second portability threshold. The
  worker now reports per-stage elapsed values in its result, and the test
  records them in JUnit evidence while retaining every semantic assertion.
  Its subprocess safety timeout is expanded to 600 seconds without changing
  any Task 2 RSS, scan-ratio, p95, or logical-cap threshold. The 3.10 full
  smoke rerun remains pending until the concurrent 4,096 benchmark scan
  finishes, to avoid contaminating its wall-clock ratio. The manual CI
  workflow also adds Task 1 codec and Task 2 observation protocol tests to
  its vector lane; this workflow has still not run externally.
- The clean CPython 3.10.21 rerun completes the expanded local Windows lane:
  Task 1 codec, Task 2 observation protocol, frozen determinism, recall-
  feature vectors, and the 256-observation fresh-process smoke pass 215/215
  with zero failures, errors, or skips in 333.785 seconds. JUnit records the
  smoke itself at 221.210 seconds and its worker stages as direct recall
  0.052 s, one-shot replay 15.439 s, paged replay 16.535 s, one-shot text
  recall 14.511 s, and paged text recall 14.776 s. This closes the earlier
  180-second harness RED without hiding it or changing a product acceptance
  metric. Local Windows now has executable selected evidence on CPython
  3.10.21, 3.11.13, 3.12.13, and 3.13.5; only 3.10 ran the subsequently
  expanded 215-test lane, so the exact expanded final snapshot must still be
  rerun on 3.11-3.13 after integration. Linux, macOS, and arm64 remain OPEN
  until the prepared CI matrix actually executes.
- The first clean-SHA full scale attempt ran from implementation commit
  `000e2591aaf02508278ca9fee700d3f720a3c5b6` in the unsynchronised work root
  `task2-20260916-175803-316-ffa0bab9`. Live evidence showed exact 2,048 and
  4,096 checkpoint workers complete and the ledger later reached all 8,192
  records. A machine/reboot interruption then ended the process before the
  final scans and atomic result write. Post-interruption inspection proves the
  ledger still contains exactly 8,192 history records and SQLite
  `integrity_check` returns `ok`, but `results/cognition_task2_scale.json` was
  never created and the earlier raw timing/RSS samples existed only in process
  memory. This is an interrupted negative run, not Task 2.7 scale PASS; its
  work directory is retained for audit and no missing metrics are inferred.
- A reboot-evidence hardening slice starts with a RED where the small real
  scale fixture passes an unsupported `progress_output` and the runner raises
  `TypeError`. The runner now writes a distinct canonical, atomic progress
  protocol after the empty-session baseline, after every exact count scan,
  and after completion. Each checkpoint binds stage, completed counts,
  parameters, partial raw measurements, environment, exact git state, and the
  unsynchronised work path. It deliberately does not implement cross-reboot
  resume: the plan's 8,192/4,096 timing ratio must come from one same-host/run,
  so a later process may audit partial evidence but cannot relabel it as a
  completed acceptance artifact.
- The new small-fixture progress GREEN exposed a second honest measurement
  RED: an empty-process peak RSS may be slightly higher than a tiny scan's
  peak, so requiring every scan peak to be greater than the baseline made the
  base gate nondeterministically false. The repair does not lower the 64 MiB
  or 16 MiB limits. RSS increments are now signed raw `scan_peak - baseline`
  values; all baseline/scan probes must remain nonzero, and a fail-closed check
  requires every reported delta to exactly match its raw peak and baseline.
  Thus missing probes or clamped/forged deltas still fail while a legitimate
  negative incremental measurement is preserved instead of rewritten to
  zero. A mutation regression proves inconsistent delta evidence fails.
- Post-hardening Task 2 scale-runner tests pass 17/17 on CPython 3.12.13 and
  3.13.5. The targeted RED/threshold/progress set passes 11/11; Ruff,
  compileall, diff-check, and pinned Pyright 1.1.413 are clean at 0 errors,
  0 warnings, 0 informations. The real 8,192 gate must be rerun from a clean
  commit; progress checkpoints increase evidence durability but grant no
  performance or completion claim.
- Two independent read-only gates reviewed exact commit
  `608ed516096efa9113fd5238d4a608f9c4194001`. The code reviewer reports
  APPROVE with zero critical/high/medium/low findings after independently
  rerunning 17/17 focused tests under CPython 3.12 and 3.13, Ruff,
  compileall, diff-check, and pinned Pyright. The verifier separately reports
  CLEAR to start the real 8,192/512 run after checking the clean SHA, the
  fixed public parameters, a real small-fixture final/progress artifact pair,
  the retained interrupted ledger's 8,192 records and SQLite integrity, and
  the absence of any final Task 2 scale result. Both gates explicitly reject
  a scale PASS claim before a fresh final
  `aluclu.cognition.task2.scale.v1` artifact reports `success: true`.
- The expanded Windows portability lane was then rerun against that exact
  integrated source snapshot on CPython 3.11.13, 3.12.13, and 3.13.5. Each
  lane passes all 215 selected codec, observation, frozen determinism,
  recall-feature, and 256-observation fresh-process tests with zero failures,
  errors, or skips. JUnit totals are respectively 206.963 s, 198.326 s, and
  194.580 s; the portability smoke cases are 150.235 s, 148.512 s, and
  139.875 s. The committed raw JUnit files complement the earlier CPython
  3.10.21 215/215 artifact. This establishes executable local Windows x64
  evidence for Python 3.10-3.13, not Linux, macOS, arm64, or the prepared
  twelve-lane workflow: those external portability claims remain OPEN until
  their actual lanes execute.
- A second full-scale attempt started from clean evidence commit
  `b82f845353f1c5722082b60db44949e6a9b84cd2`, seed `20260918`, and a fresh
  unsynchronised NVMe work root. It durably completed the exact 2,048
  checkpoint: all three scans covered 2,048 records in 99.8438465 s,
  96.03294 s, and 106.7919441 s; the isolated empty/scan RSS peaks were
  413,945,856 and 425,189,376 bytes, so the recorded signed delta is the exact
  11,243,520-byte raw difference. During the subsequent 4,096 ingest the
  controller's foreground command session disappeared with no final result
  artifact. The benchmark process and its command-session handle are both no
  longer present. Read-only immutable SQLite inspection proves the retained
  ledger is internally sound (`integrity_check=ok`) but contains only 2,994
  history rows, records, and append witnesses, with no tombstones. Therefore
  this is another interrupted negative run, not a scale PASS and not a valid
  resume source: the required 8,192/4,096 ratio must be measured within one
  uninterrupted same-host run. Its atomic progress JSON and work root are
  retained for audit. The next attempt must run as a detached hidden process
  whose lifetime is independent of an individual controller turn/session.
- The third full-scale attempt ran detached from clean commit
  `1150a30e105b5a05408bbe22e74c648af66932b8`, seed `20260918`, three samples,
  and the fixed public 2,048/4,096/8,192 counts with exact 512-byte content.
  It used the unsynchronised local-NVMe work root
  `task2-20260918-163828-11772-dbe8def9`; the detached controller remained
  alive from 16:38:20 through terminal completion at 19:41:47, emitted no
  stderr, atomically advanced the progress protocol through all three exact
  checkpoints to `stage=complete`, and wrote the final normative
  `aluclu.cognition.task2.scale.v1` artifact. This is the first uninterrupted
  completed Task 2.7 public scale run after the two retained interruption
  negatives.
- The final artifact is `results/cognition_task2_scale.json`, 6,177 bytes,
  SHA-256
  `fbfe72dd9458b27755a0a8e503a2599c6a00c72501efa70626482d3f721bfb6d`.
  It binds the clean launch SHA, Windows 11 / CPython 3.13.5 / SQLite 3.49.1,
  i7-12650H, 16 GB RAM, local NTFS/NVMe storage, dependency inventory, seed,
  sample count, raw peaks, and raw timings. Torch 2.6.0+cu124 is below the
  declared `torch>=2.10` inventory requirement, but the artifact marks Torch
  and the RTX 4050 as inventory-only and the measured persistence/recollection
  loop uses neither; this mismatch is retained rather than hidden and grants
  no neural/GPU claim.
- Exact scan samples were 174.1469283/189.2963480/203.4790805 seconds at
  2,048, 430.7994885/508.1370472/498.2259318 seconds at 4,096, and
  454.5412157/594.0896569/458.2759604 seconds at 8,192. The median
  8,192-to-4,096 ratio is 0.9198155518407722 against the fixed 2.75 maximum.
  Empty/2,048/4,096/8,192 isolated peak RSS values were respectively
  410,320,896 / 421,089,280 / 426,504,192 / 433,975,296 bytes; their exact
  signed increments are 10,768,384 / 16,183,296 / 23,654,400 bytes. Thus the
  8,192 delta is below 64 MiB over empty and only 12,886,016 bytes above the
  2,048 delta, below the fixed 16 MiB limit.
- The one-shot, 2,048-page, and fresh-process-restarted 8,192 result digests
  are all
  `485e4249d8e528e55b900cab5db70f63848700b0541812a5d278808a1442b94c`.
  Direct-ID p95 is 0.0669355 seconds versus the same-process Task 1 read p95
  of 0.0644965 seconds, within the fixed 2x limit. Exactly 8,192 records were
  scanned/scored, 32 candidates returned, full-verification delta stayed zero,
  duplicate detection stayed false, and the plaintext-sidecar scan found
  nothing. Persistent bytes are 81,132,810 total: 76,075,008 database,
  5,057,802 record-key store, and zero WAL. Every one of the 28 named fixed
  checks is true, `thresholds.passed` is true, and `success` is true.
- Immediate post-artifact validation reruns the focused benchmark suite at
  17/17 PASS on CPython 3.13.5. Scoped Ruff and compileall pass, pinned Pyright
  1.1.413 reports 0 errors/0 warnings/0 informations, and `git diff --check`
  passes. An independent code reviewer recomputed every resource ratio, checked
  the retained work root and plaintext sentinels, reran 17/17 focused tests,
  Ruff, and compileall, found zero Critical/High/Medium/Low issues, and returned
  APPROVE for the scale artifact only. A separate completion verifier checked
  the terminated launcher/controller, nonempty success stdout, zero-byte
  stderr, terminal progress artifact, retained ledger/key material, raw
  arithmetic, threshold/source/test mapping, and returned CLEAR for the same
  scale-only scope. The verifier stopped an optional additional direct cursor
  enumeration after several minutes when asked to return the verdict; that
  redundant audit produced no evidence and is not represented as a pass.
  Together the normative artifact and two independent verdicts close the
  local Windows x64 Task 2.7 scale sub-gate. They do not make Task 2.7 or Task
  2 CLEAN: Linux, macOS, and arm64 execution evidence plus the Task 2.8
  three-way final gate remain open.
- Commit `ca80f05` freezes the final/progress artifacts and trajectory, and the
  feature branch is pushed to `origin/codex/unified-lifelong-cognition`.
  Attempting the prepared manual portability dispatch immediately returns
  GitHub API 404 because `workflow_dispatch` only receives events when its
  workflow file already exists on the repository default branch. No absent run
  is relabelled as evidence. The workflow therefore adds a normal
  `pull_request` trigger targeting `main` while preserving manual dispatch;
  opening the branch PR can execute the same twelve hosted lanes from the PR
  revision without first merging unverified code. This is CI reachability
  plumbing only and changes no Task 2 protocol, threshold, or test selection.
- PR #2 (`https://github.com/kaannsaydamm/ALUCLU/pull/2`) was opened against
  `main` at exact head `866c6d075cd64e4f956011703964e988ec26bdc7`.
  GitHub Actions run `35371322774` expanded all twelve intended jobs but every
  job failed before runner allocation with zero steps and no logs. The check-run
  annotations say verbatim: "The job was not started because your account is
  locked due to a billing issue." This is a reproducible external CI account
  blocker, not a product-test failure or an executed macOS/arm64 lane. No
  hosted matrix PASS is inferred.
- A local alternative ran the identical 215-test selected portability group
  from a clean clone of that exact SHA on a real WSL2 Linux x86_64 guest
  (Kali 2026.1, Linux 6.18.33.2-microsoft-standard-WSL2, glibc 2.42). Each
  interpreter had its own isolated virtual environment and the declared
  `numpy>=2.0`, `torch>=2.10`, `cryptography>=43`, `pytest>=8.3` dependency
  installation; Torch 2.14.0, cryptography 50.0.1, and pytest 9.1.1 were
  present in all four. Exact interpreter/numpy/UCD versions and JUnit evidence:

  | Linux lane | numpy | UCD | Tests | Fail/Error/Skip | JUnit seconds | JUnit SHA-256 |
  | --- | --- | --- | ---: | --- | ---: | --- |
  | CPython 3.10.21 | 2.2.6 | 13.0.0 | 215 | 0/0/0 | 63.435 | `758ae7cddf87d2f05ccea4e13701633bdc4723b3059f6cafa2705cce5c847ea8` |
  | CPython 3.11.16 | 2.4.6 | 14.0.0 | 215 | 0/0/0 | 66.675 | `9c0613f92446ca76974f68ec2c0ca2fcef38dc0570cac54c183c8927b9365bfb` |
  | CPython 3.12.14 | 2.5.3 | 15.0.0 | 215 | 0/0/0 | 93.917 | `ac12ae90bf8511359812b39e4e21896da424c9ba71fa89a92d0f51948a7d0396` |
  | CPython 3.13.12 | 2.5.3 | 15.1.0 | 215 | 0/0/0 | 71.197 | `84ad4f529b2158e51086a04af29162885ec18a107d791bd1b99aac95d4d98b25` |

  All four XML files are retained under `results/cognition_task2_portability_linux_x64_py3*.xml`.
  This closes the selected Linux x64 3.10-3.13 lane evidence, not macOS or
  arm64. WSL's `/dev/sdd` advertised 911 GiB free as a virtual-filesystem
  capacity; a separate Windows `Get-PSDrive C`/`Win32_LogicalDisk` check showed
  only 39.65 GiB physically free on C:. The earlier conflation of the WSL
  virtual free-space report with host free space was incorrect and is corrected
  here. Isolated Linux research environments and package cache occupy host
  disk and are candidates for safe cleanup after evidence capture.
- On the user's explicit disk-space correction and cleanup request, a separate
  cleanup agent measured C: at 39.65 GiB physically free and removed only
  rebuildable Windows package caches: `uv cache clean` reduced the measured
  `C:\Users\kaann\AppData\Local\uv\cache` content from 2,137,125,917 bytes
  to zero, and `npm cache clean --force` reduced
  `C:\Users\kaann\AppData\Local\npm-cache\_cacache` from 745,600,548 bytes
  to zero. The agent did not delete repository material, benchmark artifacts,
  documentation, or unrelated user files. Logical cache bytes removed were
  2,882,726,465 (about 2.68 GiB); measured host free-space improvement was
  smaller amid concurrent disk activity, and no byte-for-byte physical saving
  is claimed from those logical totals.
- After the four Linux JUnit artifacts and dependency lock were committed,
  the exact isolated WSL test tree
  `/tmp/aluclu-task2-linux-py313-866c6d0` was checked to be the clean clone
  at `866c6d0` plus four rebuildable virtual environments, with no active
  processes, then deleted. It was approximately 22 GiB inside the WSL
  filesystem. This permanent deletion affects only the session's temporary
  test environment; the committed evidence remains and the environment can
  be rebuilt from the recorded revision and lock. WSL's virtual free space
  increased, but C: did not gain approximately 22 GiB: the exact Kali
  `ext4.vhdx` remained 51,444,187,136 bytes (47.91 GiB), while the latest
  observed C: free space was 43,503,247,360 bytes (40.52 GiB). The distros
  were stopped when inspected. `Optimize-VHD` was unavailable and querying
  Hyper-V's optional feature required elevation, so no VHD compaction was
  attempted and no further physical recovery is asserted. Do not interpret
  WSL `df` capacity as host disk capacity.
- Post-cleanup local Task 2.8 preparation on Windows CPython 3.13.5 reran Ruff
  over `src`, `tests`, and `scripts` (PASS); compileall over
  `src/aluclu/cognition` and `tests` (PASS); scoped Pyright 1.1.413 over the
  cognition source, Task 2 cognition tests, and Task 2 helper workers (0
  errors, 0 warnings, 0 informations); and `git diff --check` (PASS). A first
  foreground full-suite pytest run was deliberately interrupted during the
  expensive 8,192-observation test so its lifetime would not depend on this
  controller terminal; it produced no JUnit and is not a test PASS or product
  failure. The identical complete pytest command was restarted in a detached
  hidden process at 21:43:44 local, process ID 29648, with stdout/stderr and
  JUnit targets under `results/cognition_task2_full_py313_detached_20260918.*`.
  This run was alive and producing progress when recorded, but has no final
  verdict yet. Do not count it toward Task 2.8 until its exit/result counts,
  skips, and artifact hash are inspected. The macOS/arm64 portability lanes
  remain blocked by the GitHub account billing state regardless of local
  Windows suite outcome.
- Detached full-suite execution was observed alive again after controller-turn
  rollover: launcher PID 29648 and worker PID 6292 were still running, stdout
  advanced through 27% and into the next test group, stderr remained empty,
  and C: stayed near 40.44 GiB physically free. A hidden process-handle watcher
  (PID 22260) now waits for the existing launcher and will write its actual
  exit code to `results/cognition_task2_full_py313_detached_20260918.exit.log`;
  this does not restart or alter the test. The pending JUnit and exit code must
  both be checked before any full-suite verdict. GitHub Actions run
  `35381922237` at `1ad506a` again created twelve zero-step failed jobs; its
  macOS annotation repeats the account billing-lock message, so none is
  platform execution evidence. The Task 2 plan explicitly distinguishes
  local/host-scoped completion from the broad portability claim reserved for
  Task 14; whether this allows a scoped Task 2 CLEAN will be decided by the
  required final independent gate, not silently assumed here.
- The detached run subsequently reached the final Task 2 test group with no
  reported failure so far. Because the real 8,192-observation case previously
  required tens of minutes, an app heartbeat named
  `ALUCLU Task 2 full-suite takip` (automation ID
  `aluclu-task-2-full-suite-takip`) now checks this exact run every 30 minutes.
  It is instructed to stay quiet on unchanged state, verify the process and
  exit/JUnit evidence before reporting terminal status, record the outcome in
  this trajectory, and stop the single-test monitor afterward. Scheduling a
  check is not evidence that the run has passed or finished.
- The detached CPython 3.13 full suite reached terminal output at 23:23:55
  local. Its persisted JUnit report contains 1,051 test cases with zero
  failures, zero errors, zero skips, and suite time 6,007.673 seconds; SHA-256
  is `fe257e1e98732d126791e5f98be56d212e87dab4c71eb9b7a253c12979872156`.
  Stdout reached 100%, is 1,660 bytes, and hashes to
  `4b015d1b727b3766ef9763141a107b2a515dab49174823f27ec0a26e78e63630`.
  Stderr is empty with the empty-file SHA-256
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
  The only warning is the already known pytest xunit2 incompatibility for
  `record_property` in the real-platform keyring smoke; the smoke itself is a
  passed test. The handle watcher wrote `exit_code=` without a value, so an
  exact process exit code is unavailable and is not invented. The complete
  JUnit case counts, 100% stdout, empty stderr, terminal processes, and report
  hashes are retained as the evidence actually observed. The run's production
  and pre-existing test inputs are byte-identical to current HEAD; intervening
  commits changed trajectory only.
- The fresh Task 2.8 architecture reviewer found no current source violation
  but correctly REOPENED on a binding missing oracle: plan Section 5 says the
  forbidden dependency graph is tested, yet no AST/source guard froze Task 1
  to Task 2 direction, Task 2 internal edges, or the no-`EncryptedLedger` /
  no-nested-session boundary across all Task 2 modules. Added the test-only
  `tests/test_cognition_architecture.py`. It parses the six Task 2 modules and
  five Task 1 persistence modules, freezes their allowed local graph, requires
  ledger-dependent Task 2 modules to import only `VerifiedLedgerSession`, and
  rejects `EncryptedLedger`, `verified_session`, `unlock`, later-task imports,
  and reverse Task 1-to-Task 2 edges. A synthetic mutation fixture proves the
  detector rejects forbidden ledger/sensorium imports, constructor reference,
  and nested-session access. Its first mutation run was RED because the
  synthetic input imported but did not reference `EncryptedLedger` while the
  assertion expected both; adding an actual synthetic constructor reference
  repaired the oracle without touching production code. The final focused run
  is 2/2 PASS; Ruff and compileall pass; pinned Pyright 1.1.413 reports 0
  errors, 0 warnings, and 0 informations; `git diff --check` passes. Because
  this test was added after the 1,051-case suite collected, that JUnit does not
  cover it. A fresh full suite including the new architecture oracle is the
  next execution gate; Task 2.8 and Task 2 remain REOPEN until it and renewed
  independent verdicts are clear.
- The first architecture-inclusive detached Windows CPython 3.13 suite was
  deliberately interrupted while still near its start after independent
  reviewers found bypasses in the newly added architecture test. Its stdout
  ended with `pytest_exit_code=-1`, stderr was empty, and no JUnit XML was
  produced. This is an intentionally aborted invalid-candidate run, neither
  a product test failure nor a full-suite PASS. The exact wrapper/worker
  processes were verified and stopped; no unrelated process was touched.
  This run must not be counted toward Task 2.8.
- Independent Task 2.8 architecture and code/security review REOPENED the
  regression oracle, not the inspected production architecture. Valid Python
  imports `from . import observation` and
  `from aluclu.cognition import observation` escaped the Task 1-to-Task 2
  reverse-edge check; package-form ledger imports could evade the Task 2
  check. The oracle also missed construction of an imported or aliased
  `VerifiedLedgerSession`, caller-session `close`/context ownership, and
  aliases that could obscure the close receiver. New synthetic tests first
  reproduced those gaps as 2 focused failures (2 existing tests passed).
  The test-only repair normalizes package-form imports, rejects session
  constructors including aliases, permits `close` only on locally proven
  verified cursor variables, rejects other close/context ownership, and
  freezes the Task 1 reverse-edge helper. Expanded focused tests are now
  4/4 PASS; Ruff over `src`, `tests`, and `scripts`, Ruff format check for the
  changed test, compileall over cognition and tests, pinned Pyright 1.1.413
  with the `.venv313` interpreter (0 errors/warnings/informations), and
  `git diff --check` all PASS. The first Pyright invocation omitted the venv
  and reported four missing `pytest` imports; rerunning with the explicit
  interpreter resolved these environment-only diagnostics. Independent
  re-review and an architecture-inclusive full suite remain pending, so
  neither Task 2.8 nor Task 2 is CLEAN yet.
- GitHub Actions run `35391775413` at `da979bc` reported twelve failed
  portability matrix jobs (Ubuntu, Windows, macOS; Python 3.10-3.13), but
  GitHub's annotation says every job was **not started** because the account
  is locked due to a billing issue. These are zero-execution CI failures,
  not product test failures or platform PASS evidence. The user explicitly
  deferred Linux/macOS execution for now; local Windows Task 2.8 validation
  proceeds separately. WSL2/Kali can provide Linux userspace evidence later,
  but it is not bare-metal or macOS evidence.
- Two further independent re-review cycles were treated as blockers rather
  than waived. First, the oracle globally counted a local `cursor` assignment,
  allowing `cursor.close()` in a different function, and missed valid
  `from ..cognition import observation` / `from ..cognition.observation import`
  reverse edges. Both were reproduced as focused RED, then fixed with
  scope-local cursor binding and level-2 relative import normalization. The
  architecture reviewer then found that the newly accepted level-2 ledger
  import spelling was not recognized by the session-constructor alias check;
  direct and `as VLS` mutations reproduced RED and were fixed. The code/
  security reviewer found one more literal `getattr(session, "close")()`
  lifecycle bypass; direct `close` and `__exit__` mutations reproduced RED,
  and the guard now rejects literal dynamic lifecycle access including
  `verified_session` and `unlock`. One-hop/chain constructor aliasing is also
  tracked. Current architecture reviewer verdict is CLEAR for this scoped
  oracle and inspected production graph. After the latest repair, focused
  architecture pytest is 4/4 PASS, Ruff and compileall PASS, pinned Pyright
  1.1.413 is 0/0/0, and diff-check PASS. The separate final code/security
  re-review and the new full suite are still pending. This is not Task 2
  CLEAN or broad portability PASS.
- The final independent code/security re-review of the repaired architecture
  oracle returned CLEAR with zero critical/high/medium/low findings. It
  rechecked the prior cross-function cursor, constructor-alias, package and
  parent-relative import, and literal-`getattr` lifecycle probes; the
  legitimate local cursor close still passes. This is a scoped test/code
  review verdict only. Its reviewer explicitly notes that the AST oracle is
  syntactic, not a complete Python interpreter/dataflow proof. The final
  architecture-inclusive full suite and completion-evidence verdict are
  still required before a host-scoped Task 2.8 decision.
- The repaired oracle and this trajectory were committed as `0c5c48b` and
  pushed to `codex/unified-lifelong-cognition`. A fresh Windows CPython 3.13
  full `pytest -q` suite including that commit was started detached at
  2026-09-19 02:19:11 +03:00 with wrapper PID 14932 and Python worker PID
  32748 (IDs are startup hints, not future authority). Its three authoritative
  targets are `results/cognition_task2_full_py313_architecture_oracle_v2_20260919`
  with `.stdout.log`, `.stderr.log`, and `.xml` suffixes. The wrapper writes
  `pytest_exit_code=<number>` after pytest returns, avoiding the prior blank
  exit-watcher ambiguity. The processes were alive and stdout had begun
  advancing when recorded; no JUnit or final verdict exists yet. The old
  single-run monitor was no longer present in the app, so a new quiet-on-
  unchanged 30-minute heartbeat named `ALUCLU Task 2 final full-suite takip`
  (automation ID `aluclu-task-2-final-full-suite-takip`) now watches the new
  evidence and will stop after the terminal result is processed. Scheduling
  is not a test PASS. The user has deferred Linux/macOS; their absence and the
  GitHub Actions billing lock remain separately visible, not silently passed.
- At the user's request to retry after a possible billing correction, GitHub
  Actions portability run `35405342625` for the latest pushed commit
  `de7898b` was rerun as attempt 2. GitHub accepted the rerun request, but
  every one of the twelve Windows/Ubuntu/macOS matrix jobs again ended before
  executing any steps. The attempt-2 job annotations still say the account is
  locked due to a billing issue. This is renewed external blocker evidence,
  not a failed product test or successful platform execution. Do not keep
  rerunning the same workflow until GitHub billing/Actions availability has
  actually changed. The detached local Windows full suite remained alive with
  empty stderr when this was recorded.

## 2026-09-20 Task 2.8 whole-branch review blockers and lifecycle/position repair

- Three independent GPT-5.6 Sol reviewers examined the same frozen
  `f5a30e0..d2b5ab3841a4e3ddf29a5b4654b9cf3da7cfed08` range rather than the
  earlier test-only patch. The architecture verdict was BLOCK because
  missing-profile and forced-abstention early returns could accept a closed
  or foreign-thread `VerifiedLedgerSession`. The code/security verdict was
  REQUEST CHANGES because direct-ID recall and reconsolidation endpoint
  validation omitted the authenticated
  `post_core_state.last_observation_id == record.event_id` relation, and the
  architecture oracle missed annotated and derived constructor aliases. The
  completion map remained INCOMPLETE pending these repairs, current full-suite
  evidence, a hashed final review package, and three clear final verdicts.
- The old full-suite candidates are explicitly non-evidence. The v2 run was
  interrupted by a machine restart near 75% and produced neither JUnit nor an
  exit record. The v3 launcher split the `--junitxml` option and terminated
  with pytest exit 4 before collection. The correctly launched v4 run reached
  47% with empty stderr, but was deliberately stopped after the independent
  blockers made its old-code result obsolete; its wrapper recorded
  `pytest_exit_code=-1` and produced no JUnit. None of v2/v3/v4 is a product
  PASS or FAIL. The obsolete v4 heartbeat was deleted.
- RED was reproduced before production repair: five focused targets all
  failed. They covered closed-session no-scan recall, foreign-thread no-scan
  recall, direct-ID acceptance of a forged post-core observation ID,
  reconsolidation acceptance of the same malformed endpoint, and annotated /
  tuple-derived / named-expression `VerifiedLedgerSession` constructor aliases
  plus a shadowed safe-name control.
- The repair adds one shared
  `canonical_observation_matches_position()` predicate for all four canonical
  slot relations and uses it consistently in sensorium replay validation,
  scan recall, direct-ID recall, and reconsolidation endpoint validation.
  Task 2 session entry checks now call Task 1 `_ensure_active()` before policy,
  profile, continuation, cursor, or mutation work, so closed, poisoned, and
  foreign-thread sessions fail with Task 1 lifecycle authority even on
  no-scan terminal paths. The architecture oracle now performs lexical-scope
  aware alias propagation across plain, annotated, tuple/subscript, and named
  expression assignments while respecting parameter shadowing.
- The exact RED targets became 5/5 GREEN. The expanded post-repair suite over
  `test_cognition_recollection.py`, `test_cognition_reconsolidation.py`,
  `test_cognition_sensorium.py`, and `test_cognition_architecture.py` produced
  `results/cognition_task28_blocker_repair_focused_20260919.xml`: 104 tests,
  0 failures, 0 errors, 0 skipped, 142.643 seconds; SHA-256
  `5d6d510b1b1cc253fe35fcc109902714e03f9055fcf8307602fc42fa42b804fd`.
  Ruff 0.16.6 lint over `src`, `tests`, and `scripts` passes; Ruff format check
  for the newly expanded architecture oracle passes; cognition/test
  compileall and `git diff --check` pass; pinned Pyright 1.1.413 with the
  `.venv313` interpreter reports 0 errors, 0 warnings, and 0 informations.
  A whole-file Ruff format check was not claimed: several large pre-existing
  files still have unrelated formatter deltas, and they were deliberately not
  mechanically reformatted into this security repair.
- Task 2.8 and Task 2 remain OPEN. The repaired diff still requires a new
  frozen commit/range, fresh whole-branch architecture and code/security
  verdicts, a new architecture-inclusive terminal full suite, final review
  package hash, completion-verifier remap, clean tracked tree, and only then
  the controller's literal host-scoped CLEAN record. macOS/arm64 evidence and
  broad portability remain separately deferred and must not be inferred from
  this Windows-host repair.

## 2026-09-20 Task 2.8 final-review oracle reopen

- Commit `3fc1063af0a5f0ae170b05c91268da8190826298` and frozen review package
  SHA-256 `b87be7ec5fb1fe56d2307dd3a8f2a1626e0319bf1e4eaa45ca1a45c32e13e1ff`
  received conflicting final independent outcomes. The architecture reviewer
  returned the exact verdict `FULL-BRANCH ARCHITECTURE VERDICT: CLEAR`, after
  independently exercising the poisoned-session early-return paths. The
  code/security reviewer returned `REQUEST CHANGES`: the no-nested-session
  acceptance oracle missed constructor flow through attribute/subscript
  stores, helper returns, and containers, and Task 2 did not explicitly freeze
  the poisoned-session member of the no-scan lifecycle family. The stricter
  finding controls, so Task 2.8 remains OPEN even though no current production
  nested-session construction or poisoned-session behavior defect was found.
- The then-running v5 full suite was no longer capable of becoming final
  evidence because the required acceptance tests must change. It was therefore
  stopped rather than consuming the remaining host resources on obsolete
  code. Its stdout had reached the 88% marker and continued emitting passing
  dots, stderr was empty, the wrapper recorded `pytest_exit_code=-1`, and no
  JUnit XML exists. This is an intentionally interrupted obsolete run, not a
  product PASS or FAIL. Its quiet heartbeat
  `aluclu-task-2-v5-final-suite-takip` was deleted.
- RED was reproduced before changing the oracle. The four reviewer-provided
  attribute, subscript, helper-return, and container fixture families caused
  `test_architecture_guard_rejects_session_ownership_mutations` to fail, while
  the new poisoned-session no-scan regression passed against the already-correct
  production lifecycle enforcement. The poisoned regression covers both the
  missing-profile and forced-abstention paths and makes cursor creation and text
  encoding fatal if either occurs before lifecycle rejection.
- The architecture oracle now uses a conservative runtime allowlist instead of
  attempting incomplete Python taint propagation: an imported
  `VerifiedLedgerSession` constructor may appear only in annotations and
  explicit `type`/`isinstance`/`issubclass` checks. Every other unshadowed
  runtime load is a violation, which covers assignment to attributes and
  subscripts, storage in containers, helper/closure returns, and default
  arguments without pretending to model arbitrary Python dataflow. Annotation
  references are exempt only when the module explicitly enables postponed
  annotations; a constructor call inside an eagerly evaluated annotation is a
  violation. The four exact reviewer mutations, closure/default/eager-
  annotation mutations, postponed-annotation/type-check controls, and
  closed/poisoned/foreign-thread lifecycle targets pass together.
- The final-source focused regression over recollection, reconsolidation,
  sensorium, and the architecture oracle produced
  `results/cognition_task28_oracle_repair_focused_20260920.xml`: 105 tests,
  0 failures, 0 errors, 0 skipped, 91.871 seconds; SHA-256
  `afd64cd336e61b6dec67e1cb4ce79367f2b7a3fa78aa3580946c1306ff180049`.
  Repository Ruff lint, architecture-oracle Ruff format, compileall over
  `src`/`tests`/`scripts`, and `git diff --check` pass. Pinned Pyright 1.1.413,
  bound to `.venv313` and scoped over the cognition package plus both changed
  tests, reports 0 errors, 0 warnings, and 0 informations. A new frozen
  package, fresh independent reviews, and a terminal full suite remain
  required before any CLEAN claim.
- The first post-repair frozen package covered
  `f5a30e0d7c9e0e95a8d8a5533517a852c77e0d3c..5bba379f95936ff5dcaca1ce20aff2b58a01009f`
  (46 commits, 58 files, 1,740,903 bytes) with SHA-256
  `21e56a5ed10f2ee11c4dce73b044735510c1756ee73f0366274145c29af42979`.
  Its independent architecture review returned
  `FULL-BRANCH ARCHITECTURE VERDICT: CLEAR`, but code/security again returned
  `REQUEST CHANGES`: a same-named parameter incorrectly remained exempt after
  an in-scope import rebound it to `VerifiedLedgerSession`. The exact valid
  Python mutation reproduced RED. A deeper nested-function variant, where an
  inner import was incorrectly hidden by an outer parameter, was then derived
  and also reproduced RED before the repair.
- Parameter shadowing is now exempt only while name resolution reaches a
  genuinely un-rebound parameter. Imports, assignments/deletions, loop/with/
  comprehension stores, exception targets, nested definition names, and match
  captures in the active lexical scope stop that exemption; class and nested
  function boundaries are handled explicitly. The exact reviewer mutation and
  the derived nested-scope mutation are GREEN while the original un-rebound
  parameter control remains allowed. The final-source 105-test JUnit numbers
  and hash above were regenerated after this repair, and Ruff, format,
  compileall, diff-check, and pinned Pyright 1.1.413 all pass again. Because
  this changed the reviewed oracle, another frozen package and two fresh
  independent reviews are still mandatory.
- The next frozen package covered
  `f5a30e0d7c9e0e95a8d8a5533517a852c77e0d3c..d3fadf9e05b71219903f8fba91fe0b003e23088d`
  (47 commits, 58 files, 1,744,730 bytes) with SHA-256
  `58c9107b764396b34d6cf49b80d5bb382ab62ed749932424cc7e22244b4d27ab`.
  Both independent rereviewers blocked it. A nested function or directly
  evaluated class body could declare `global VLS`, redirecting the name away
  from an outer shadowing parameter to the module-level imported constructor;
  the oracle incorrectly kept the parameter exemption. The architecture
  reviewer also demonstrated the inverse precision defect: a class attribute
  named `VLS` was incorrectly treated as a lexical binding visible inside a
  method, although Python method bodies do not close over class namespaces.
  Both compile-valid examples were reproduced before repair. No current
  production nested-session construction or lifecycle/slot defect was found;
  the BLOCK was the mandatory no-nested-session acceptance oracle.
- Scope resolution now models `global` and `nonlocal` declarations separately
  from ordinary local bindings. A `global` declaration stops ancestor-
  parameter lookup and leaves the module constructor load forbidden;
  `nonlocal` continues to the relevant enclosing function binding. Class
  namespace rebinding applies only to expressions evaluated directly in that
  class body and is not propagated through a method, lambda, comprehension, or
  nested-scope boundary. Exact nested-function and class-body `global`
  mutations are GREEN; safe `nonlocal` and class-method/outer-parameter
  controls remain allowed. The final-source focused JUnit and static evidence
  above were regenerated after this repair. The source must now be frozen,
  independently rereviewed again, and covered by a terminal full suite before
  Task 2.8 can close.
- The fourth frozen package covered
  `f5a30e0d7c9e0e95a8d8a5533517a852c77e0d3c..fddd2d4c801d18f7acc6f4494d1b5d474d8a3948`
  (48 commits, 58 files, 1,749,453 bytes) with SHA-256
  `7b37ef8e186e9223d090ba2b22cabcba9b0bf77509b3977dfd14c51fd55d3288`.
  The code/security reviewer returned `REQUEST CHANGES`: direct module-
  namespace lookup through `globals()["VLS"]`, including a default-argument
  capture hidden behind an outer same-named parameter, bypassed the constructor
  guard. The architecture reviewer classified a separate precision issue as
  WATCH: a comprehension-local target named `VLS` was incorrectly treated as
  the imported constructor. Exact reviewer probes established both results;
  prior `global` bypasses were independently confirmed closed.
- Task 2 now deliberately forbids runtime loads of the namespace-introspection
  built-ins `globals`, `locals`, `vars`, `eval`, `exec`, `compile`, and
  `__import__`. This is a conservative architecture policy, not a partial
  attempt to propagate reflection taint; direct calls, `__getitem__`, default
  capture, and function-alias variants are blocked under the same rule.
  Comprehension scope handling now models generator targets and Python's
  evaluation order: the first iterable remains in the enclosing scope, while
  element/key/value expressions, filters, and later generators see the
  applicable comprehension-local targets. Safe local-target and unsafe
  imported-constructor controls are both frozen. The final-source focused
  result and SHA-256 above were regenerated after these changes; Ruff, format,
  compileall, diff-check, and pinned Pyright 1.1.413 remain clean. Another
  immutable review package and two fresh clear verdicts remain mandatory.
- The fifth frozen package covered
  `f5a30e0d7c9e0e95a8d8a5533517a852c77e0d3c..d5c3368b98880061e240955dfc576724d8d908e0`
  (49 commits, 58 files, 1,754,980 bytes) with SHA-256
  `bb2b9b403702e0cd2444530cd8cca51a2f168b278c0e42bbc94e8be926305833`.
  Both independent reviewers blocked release. Code/security classified the
  `builtins` namespace escape HIGH and nested-comprehension precision LOW;
  architecture classified the same release blocker HIGH and the precision
  defect MEDIUM. `import builtins` attribute, `__dict__`, `getattr`, and
  `from builtins import globals as ...` variants all recovered the protected
  constructor without a violation. The inner-comprehension resolver also
  stopped at the nearest comprehension instead of continuing to an enclosing
  target binding, rejecting valid nested list-comprehension code. These were
  acceptance-oracle defects; neither reviewer found a current production
  nested-session, lifecycle, canonical-slot, concurrency, or parsing defect.
- The exact reviewer probes supplied RED evidence before this repair. Task 2
  modules now conservatively reject any `builtins` import and any runtime
  `__builtins__` load, closing module aliases, from-import aliases, `getattr`,
  and `__dict__` access as a single fail-closed policy. Comprehension scope
  resolution now continues through enclosing comprehensions when the nearest
  evaluation point does not bind the constructor name. Exact nested-first-
  iterable and result-expression controls plus list/set/dict/generator
  variants remain allowed when an enclosing generator shadows the alias; an
  unshadowed nested constructor call remains forbidden.
- The regenerated final-source focused result is
  `results/cognition_task28_oracle_repair_focused_20260920.xml`: 105 tests,
  0 failures, 0 errors, 0 skipped, 83.240 seconds; SHA-256
  `2401c905feaf29222333cf9e2f7b800fdac3da3a5af9df56900db7d0b94c9a53`.
  The architecture/lifecycle subset is 7/7 PASS. Repository Ruff lint,
  architecture-oracle Ruff format, compileall over `src`/`tests`/`scripts`,
  `git diff --check`, and pinned Pyright 1.1.413 with `.venv313` all pass (0
  errors, 0 warnings, 0 informations). This source still requires a fresh
  immutable package and two independent CLEAR verdicts before starting the
  terminal full suite; Task 2.8 and Task 2 therefore remain OPEN.
- The sixth frozen package covered
  `f5a30e0d7c9e0e95a8d8a5533517a852c77e0d3c..8d750c2cca2c156b2a6aa04b5f4b0713def25ecb`
  (50 commits, 58 files, 1,760,924 bytes) with SHA-256
  `be4f34792fa06a7d86eaabcc27c24b4f9bb36162afaf6edd39b74d04045204b3`.
  Both independent reviewers again blocked release. They independently
  reproduced HIGH constructor recovery through function `.__globals__`;
  literal `getattr(..., "__globals__")`, `sys.modules`, and `importlib` paths
  also bypassed the syntactic boundary. Code/security additionally found a
  LOW precision defect: in a multi-generator comprehension every target is
  local throughout the implicit function after the first iterable, so a
  later target can make an earlier read a local read-before-assignment rather
  than an imported-constructor call. Prior `builtins` and enclosing-
  comprehension repairs were independently confirmed closed.
- The exact reviewer mutations supplied RED evidence. The repaired oracle now
  gives ledger-dependent Task 2 modules an explicit per-module external-import
  allowlist; `sys`, `importlib`, `inspect`, and other undeclared imports fail
  closed. Runtime namespace/reflection built-ins, including dynamically named
  `getattr`, are forbidden. Runtime dunder and frame-namespace attributes are
  also forbidden except the two production-required `object.__new__` and
  `object.__setattr__` operations. This explicitly bounds the oracle as a
  conservative syntactic policy instead of claiming whole-Python reflection
  or taint proof. Comprehension resolution now models the first iterable as
  enclosing-scope code and all remaining expressions as one implicit function
  whose complete generator-target set is local from entry. Exact reviewer
  list/set/dict/generator examples and an additional dynamically composed
  `__globals__` attribute probe are frozen as regressions.
- The latest regenerated focused result is
  `results/cognition_task28_oracle_repair_focused_20260920.xml`: 105 tests,
  0 failures, 0 errors, 0 skipped, 80.078 seconds; SHA-256
  `769376675e650457e0f85763d0b069f34cc648b89e7ffe985a7a030e56f8d7b8`.
  The architecture/lifecycle subset remains 7/7 PASS. Repository Ruff lint,
  architecture-oracle Ruff format, compileall over `src`/`tests`/`scripts`,
  `git diff --check`, and pinned Pyright 1.1.413 with `.venv313` all pass (0
  errors, 0 warnings, 0 informations). A fresh frozen package and two new
  independent zero-finding verdicts are still mandatory before the terminal
  full suite; Task 2.8 and Task 2 remain OPEN.
- The seventh frozen package covered
  `f5a30e0d7c9e0e95a8d8a5533517a852c77e0d3c..345e475b5570aa39fdf08dc6bca4a4ccd9c928d3`
  (51 commits, 58 files, 1,770,419 bytes) with SHA-256
  `5c0cd6efc6357563ae7f8b1bff0af5cb7bc5c811c001faa71b9e208f4042e0c0`.
  Both independent reviewers returned HIGH release blockers against the same
  root-only external-import policy. An otherwise allowed module such as
  `typing`, `dataclasses`, `enum`, or `weakref` could re-export the real `sys`
  module, so both `from <allowed> import sys` and `<allowed>.sys.modules`
  recovered the Task 2 module namespace. Architecture also identified the
  omitted frame member `f_builtins` and `_getframe` path. All sixth-round
  direct namespace and comprehension regressions were independently confirmed
  closed; the new block was the precision of the declared import policy.
- The exact seventh-round probes supplied RED evidence. The root allowlist has
  been replaced by two exact policies per ledger-dependent module: permitted
  `from`-import symbols and permitted members of directly imported modules.
  For example, `from typing import cast` and `weakref.WeakValueDictionary` are
  allowed because production uses them, while `from typing import sys`,
  `weakref.sys`, a renamed direct-module import, or passing an imported module
  object into other runtime flow is rejected. The policy now also blocks
  `f_builtins`, `_getframe`, `.sys`, and `.modules`. Tests cover the re-export
  paths across all three governed modules, the current direct-module surface,
  and the frame-builtins path.
- The regenerated focused result is
  `results/cognition_task28_oracle_repair_focused_20260920.xml`: 105 tests,
  0 failures, 0 errors, 0 skipped, 85.044 seconds; SHA-256
  `e5fa152498fa6368e46e21d664c82c0db85c510bc90b28642a4ab26f5e0c388a`.
  Repository Ruff lint, architecture-oracle Ruff format, compileall over
  `src`/`tests`/`scripts`, `git diff --check`, and pinned Pyright 1.1.413 with
  `.venv313` all pass (0 errors, 0 warnings, 0 informations). The repaired
  source still needs a fresh immutable package and two independent CLEAR
  verdicts before the terminal full suite; Task 2.8 and Task 2 remain OPEN.
- The eighth frozen package covers
  `f5a30e0d7c9e0e95a8d8a5533517a852c77e0d3c..934dc97bab40d34642f632429c3b3e120f380cdf`
  (52 commits, 58 files, 1,776,542 bytes) with SHA-256
  `24b4c7ed902218ee2a2f7f60e1671484c3c34ff43c4724a8783b9a6c09c2297f`.
  Independent GPT-5.6 Sol rereviews of that exact immutable package returned
  the literal zero-finding verdicts `FULL-BRANCH CODE/SECURITY VERDICT: CLEAR`
  and `FULL-BRANCH ARCHITECTURE VERDICT: CLEAR`. The first attempts were
  interrupted by reviewer usage limits and produced no verdict; only the
  successful reruns count. These review verdicts do not replace a terminal
  full-suite result or completion evidence.
- With source HEAD and origin both at `934dc97`, no tracked changes, no active
  older pytest process, and 48.02 GiB free on the host drive, a fresh detached
  Windows CPython 3.13 full suite was started at 2026-09-20 04:38:11 +03:00.
  Startup PID hints are wrapper 23940, pytest 4520, and child 22976. The
  authoritative artifacts are
  `results/cognition_task2_full_py313_final_v6_20260920` with `.stdout.log`,
  `.stderr.log`, `.exit.log`, and `.xml` suffixes. The launch passed the
  absolute JUnit target as one `--junitxml=...` argument. Process start is not
  PASS evidence; Task 2.8 and Task 2 remain OPEN until terminal validation and
  the independent completion-verifier gate.
- The v6 run terminated normally at 2026-09-20 05:55:05 +03:00. The wrapper
  recorded `pytest_exit_code=0`; JUnit independently parses as 1 suite and
  1,060 testcases, 0 failures, 0 errors, 0 skipped, 4,611.033 seconds, with
  exactly 1,060 testcase nodes and no failure/error/skipped child nodes. The
  XML is 170,325 bytes with SHA-256
  `5c067f7385ba599d617c8d7dcd594194b6268abc88a730ac4eb442a043266da4`.
  Stdout reached 100% and contains only the expected pytest warning that
  `record_property` is incompatible with JUnit `xunit2`; it is 3,322 bytes
  with SHA-256
  `c3bbd0115107906b1fe3f908751b08c3cc9d5b1f1e14fc828a3cda764bf106dd`.
  Stderr is empty (0 bytes; SHA-256
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`).
  The 20-byte exit record has SHA-256
  `f9703120c10d0a5f1412f37914637ef68757293a74cdf0ab518f0dd4f865a2fd`.
  This is terminal Windows CPython 3.13 whole-suite PASS evidence for frozen
  source `934dc97`; it is not macOS/arm64 or broad-portability evidence. Task
  2.8 and Task 2 remain OPEN until the independent completion-verifier remaps
  every required gate against the final committed evidence.
- A controller audit then found that the previously tracked formal scale JSON
  embedded source commit `1150a30`, which predates the final recall-session and
  position-integrity production repair in `3fc1063`. The v6 whole-suite PASS
  includes the 8,192-record test, but it does not replace the plan's separate
  process-isolated RSS, scan-ratio, direct-ID, restart, and canonical-JSON
  benchmark. Task 2 therefore remained OPEN and the formal scale gate was
  rerun without changing any threshold.
- The replacement benchmark ran from a separate clean checkout of evidence
  commit `fc6d2f57d256c4daca7c6735ec5d21797a3550b7` (`dirty: false`) using
  Windows CPython 3.13.5, fixed counts `[2048, 4096, 8192]`, 512-byte content
  payloads, three samples, and seed `20260916`. It terminated normally with
  `benchmark_exit_code=0` and `success: true`. Every one of the 28 recorded
  threshold checks is true. Scan medians were 98.5522623, 428.9717467, and
  835.014083 seconds; the 8,192/4,096 ratio is 1.9465479706381792 against the
  fixed maximum 2.75. Peak-RSS increments over the empty-process baseline were
  11,931,648, 13,172,736, and 23,293,952 bytes; the 8,192 increment is below
  64 MiB over empty and only 11,362,304 bytes above the 2,048 result, below the
  16 MiB delta limit. Direct-ID p95 was 0.1047515 seconds versus Task 1 read
  p95 0.1013534 seconds, within the fixed 2x limit. Full-verification delta is
  zero, no duplicate records or plaintext sidecars were observed, and the
  one-shot, paged, and fresh-process restarted digests are all exactly
  `ca2c299cd49cb22f9bd51053ae04b485281b7ec62f03d1bbca7ad9813e1eb3b6`.
  The canonical final artifact is
  `results/cognition_task2_scale_final_fc6d2f5_20260920.json`,  with SHA-256
  `54410023f6bf20caadda50c7dc6aa473a1321c7a168d161d5c775c74279a6e11`.
  The progress, stdout, stderr, and exit evidence SHA-256 values are
  `36ef5761ecdbe547215ee8511285aa898d3b0af3d7a32f6a23c807dfcf2ea4be`,
  `29401f5dcbae4edfb3f04bd61ee81ae97c20048495ea118e844e2c88933262d8`,
  `a3639af5e23464fc391dae127fd5493f02c8178068a35866d9c7fdd35dcd623f`,
  and `5f25b143bea6eb808bc0aa481709af1ab26c17e5c212234c3aeb75727fc40c52`.
  Stderr contains only PowerShell's CLIXML first-use progress record, not a
  benchmark error. This closes the final-source Windows scale-evidence gap;
  Task 2.8 and Task 2 remain OPEN until the independent completion-verifier
  reviews the final committed evidence package.
- The final independent GPT-5.6 Sol completion verifier reviewed immutable
  package `f5a30e0d7c9e0e95a8d8a5533517a852c77e0d3c..10bd426b45219e07e814e01fab6a2f6da9453e2f`
  (54 commits, 67 files, 1,978,347 bytes; SHA-256
  `8dea5c92770a239599109c2b9e737ca716a86305e3bf224b24f17c3044986baa`).
  Reverse-apply and stable-patch-ID checks matched the live range exactly.
  The verifier independently reparsed the 1,060-test v6 JUnit and the new
  terminal scale artifacts, reran Ruff, pinned Pyright 1.1.413, in-memory
  compilation of all 81 Python files, and Git diff checks, and remapped every
  Task 2.0--2.8 acceptance gate. It found no Critical, High, Medium, or Low
  completion issue and returned the exact verdict
  `TASK 2 COMPLETION VERDICT: CLEAR`. Code/security and architecture had
  already returned their exact CLEAR verdicts for the unchanged production
  source. The tracked candidate was clean and HEAD equaled origin; the 16
  historical untracked logs/`uv.lock` remain excluded and untouched. This is
  a current-host Windows/x64 Task 2 result only: macOS, arm64, and broad
  portability remain explicitly deferred and unclaimed.

Task 2 sensorium/recollection gate: CLEAN

## 2026-09-20 — ALC-R0 preregistration begins after Task 2 CLEAN

- The required roadmap dependency is now active: ALC-R0/ALC-0 is the blocking
  phase between the completed Task 2 gate and Task 3. No later ALC container,
  enterprise, marketplace, serving, compiler, or accelerator investment is
  authorized by this transition.
- The research-only host is pinned to
  `HuggingFaceTB/SmolLM2-135M` revision
  `93efa2f097d58c2a74874c7e644dbc9b0cee75a2`. Upstream metadata declares
  Apache-2.0 and a 30-layer, width-576 `LlamaForCausalLM`. The expected
  `model.safetensors` SHA-256 is
  `80521b40281d6ce74e35c9282c22539e75aa0ac8578892b2a59955ef78d55da1`.
  These are acquisition expectations, not yet locally verified model evidence.
- The new durable plan draft is
  `docs/superpowers/plans/2026-09-20-alc-r0-neural-capability-proof.md`. It
  proposes the `ResearchCapsuleV0` same-width residual update, zero-based port
  sets `{14}`, `{29}`, and `{14,29}`, ranks `{4,8,16}`, and an exact
  parameter-matched non-merged `q_proj` LoRA comparator. This is intentionally
  a same-base proof and does not claim a general Neural ABI or cross-model
  portability. It becomes experiment-authoritative only after preregistration
  review and the R0.0 machine-freeze validator pass.
- The two blocking real-data capability families are Banking77 intent routing
  and CodeXGLUE/Devign defect detection. Frozen-base, bounded textual-context,
  BM25 RAG, matched LoRA, capsule, zero, shuffled-label, wrong-family,
  attach/detach, and fresh-process retrieval-off arms are required. WikiText-2
  and LAMBADA are retention gates. A mechanistic diagnostic cannot substitute
  for either capability family.
- Development uses the complete 9-configuration grid and two seeds;
  confirmation uses five untouched seeds after a committed freeze receipt.
  P1--P14 are conjunctive blocking conditions, including paired confidence
  intervals, positive-control validity, retention, byte/hash identity,
  fresh-process isolation, artifact size, VRAM, latency, and complete evidence
  validation. Thresholds cannot be softened after observation.
- Current-host feasibility evidence is limited to hardware and import probes:
  i7-12650H, 15.71 GiB RAM, RTX 4050 Laptop GPU with 6,141 MiB VRAM, driver
  610.78, and successful CUDA BF16 matrix multiplication. The existing global
  and `.venv313` packages are not a reproducible environment; the model is not
  yet in the local HF cache. A separate Python 3.12 environment and research
  tree under `%LOCALAPPDATA%\ALUCLU\research` are mandatory.
- Upstream dataset identities were checked before freezing the plan:
  Banking77 raw data at
  `PolyAI-LDN/task-specific-datasets@9d081458ff52e53cf7e848f414e6e9344e4e6696`
  plus the card snapshot
  `PolyAI/banking77@90d4e2ee5521c04fc1488f065b8b083658768c57`
  (declared CC-BY-4.0),
  `google/code_x_glue_cc_defect_detection@69bd48c03223c2104342acd9a807caf61ac3efb8`
  (declared C-UDA),
  `Salesforce/wikitext@b08601e04326c79dfdd32d625aee71d232d685c3`,
  and
  `EleutherAI/lambada_openai@900124bf3b8235c6daf21033af9948b3f07346c4`.
  Exact consumed-byte and split hashes remain an R0.0 prerequisite; no dataset
  or capability PASS is claimed here.
- The first source audit caught a reproducibility trap before acquisition: the
  pinned Hugging Face Banking77 loader itself downloads CSV files from a moving
  GitHub `master` URL. The plan therefore makes the exact upstream Git commit
  and three Git blob identities authoritative and treats the Hugging Face
  revision only as dataset-card/schema provenance. Devign similarly retains
  both its pinned Parquet-mirror identity and its Microsoft CodeXGLUE upstream
  provenance. No moving branch is permitted in a scientific run.
- The research loop has selected `mission-validator-script` mode, but its
  validator is not implemented yet. Completion will require a machine-readable
  validator artifact, not an agent assertion or a promising run. Paid external
  compute remains prohibited without explicit user approval.
- The first independent GPT-5.6 Sol preregistration review returned
  `REQUEST CHANGES`, with no Critical finding but five High blockers: the test
  sealer contradicted the held-out counter, optimizer/LoRA tuning was not
  symmetric, the bootstrap hypotheses were underspecified, the 512-token
  controls exceeded the declared total length, and offline/filesystem denial
  was only self-attested. Medium findings required a standard q+v LoRA reference,
  a frozen resource harness, broader official-forward parity, exact negative
  controls, crash-safe scoring transactions, and an explicit serialized dtype.
  This verdict is retained; the draft was not frozen or used for training.
- The draft has been repaired for rereview. It now separates sealing access from
  scoring transactions, hides test content/labels behind AES-GCM and a
  freeze-receipt key broker, and specifies a WSL2 user/mount/network/PID namespace
  worker. A live host probe confirmed `kali-linux` WSL2, GPU exposure, and that
  the worker can cover `/mnt/c` with an empty tmpfs while DNS is unavailable.
  This is feasibility evidence for the isolation mechanism, not a completed
  evaluator gate.
- Optimization is now fixed rather than deferred: AdamW at `3e-4`, zero weight
  decay, three epochs, cosine schedule, 5% warmup, effective batch 16, and
  independent dev checkpoint selection. Development now includes 72 symmetric
  capsule/q-only-LoRA runs plus four non-blocking all-layer q+v-LoRA reference
  runs. The confirmatory count is 30 blocking train runs plus 10 non-blocking
  q+v reference runs. Exact hierarchical bootstrap pairing, Holm families,
  retention resampling, negative-control derangements, resource timing, and
  official-forward conformance tolerances are declared.
- Target-task length is now a total 1,024-token limit: at most 512 for the common
  interface/query/answer and at most 512 for textual or RAG control content.
  Banking split construction and Devign exact/near-clone filtering are now
  deterministic and fixture-gated. The canonical capsule tensor dtype is FP32,
  making the maximum raw tensor payload 147,456 bytes while retaining the
  256-KiB artifact cap. No training or held-out scoring has started.
- The first rereview still returned `REQUEST CHANGES`: same-user Windows
  Credential Manager was not a process authorization boundary, the ordinary
  bootstrap tail fractions were not calibrated p-values, Banking77 exact
  duplicates were not governed, and the latency harness lacked arm-order and
  exact tax arithmetic. No training was authorized on that draft.
- The next repair requires a distinct non-interactive
  `ALUCLU_R0_SEALER` Windows principal and ACL-restricted broker pipe; same-user
  key custody is removed. If that principal cannot be created without weakening
  policy, local confirmation is blocked rather than self-attested. Statistical
  p-value labels and Holm gates are removed; P1--P8 now use explicitly sized
  Bonferroni simultaneous one-sided percentile bounds, while ordinary 95%
  intervals remain descriptive. Banking77 exact duplicates/conflicting labels
  and train/test overlap are now governed with minimum post-filter count/class
  coverage. Resource order is fixed to `B/A, A/B, B/A, A/B, B/A`, with literal
  pooled-quantile tax formulas. This repaired draft awaits another independent
  rereview and remains non-authoritative.
- A second independent GPT-5.6 Sol reviewer read the broader design before the
  latest repair and returned `REQUEST CHANGES`. It found arm-specific isolation,
  true rootfs replacement, arm-neutral topology selection, Devign clone-group
  units, executable retention metrics, exact textual/RAG controls, validator
  schemas, runtime ceilings, state-digest framing, failure-status wording, and
  the zero control still incomplete. These findings were accepted despite the
  narrower rereviewer subsequently clearing its own prior list.
- The draft now uses separate retrieval-off/profile/RAG rootfs policies and a
  `pivot_root` isolation transition that unmounts the old root, allowlists CUDA
  nodes, closes inherited descriptors, drops capabilities, and verifies the
  complete in-namespace inventory. Grid selection maximizes the minimum gain
  across both capsule and q-only LoRA on both families; a capsule-only optimum
  can no longer under-select the comparator.
- Devign union-find roots are now the retained data/statistical unit with
  conflicting-label fail-closed behavior and minimum sealed-test coverage.
  WikiText-2 perplexity and LAMBADA last-word accuracy now have exact split,
  masking, windowing, generation, normalization, exclusion, and bootstrap-unit
  definitions. Textual profiles and BM25 tokenization/scoring/rendering are
  deterministic rather than R0.0 placeholders.
- The local envelope is capped at four two-hour pilot jobs, 600 valid GPU-hours,
  45 calendar days, and a 25-GiB research root while preserving 20 GiB free.
  Exceeding it records a measured local blocker and requires explicit authority
  for external compute; it does not narrow the experiment. The base digest now
  frames every sorted persistent `state_dict()` entry, the all-zero control is
  a distinct never-trained FP32 artifact, and the failure-status wording
  distinguishes development-search exhaustion from held-out failure.
- Evidence now requires RFC-8785 canonical JSON, versioned JSON Schemas, an
  enumerated run/artifact matrix, primary/foreign-key integrity, append-only
  state transitions, duplicate/orphan rejection, and a deterministic root claim
  digest with negative fixture packages. This expanded draft still awaits final
  independent rereview; no model acquisition, training, or held-out access has
  begun.
- A live read-only principal probe found the current process is not elevated:
  `kaan\kaann` has the local Administrators SID present only as deny-only in this
  token, and `ALUCLU_R0_SEALER` does not yet exist. Therefore R0.0 can implement
  and test development lanes normally, but the distinct-principal sealer/broker
  prerequisite will require a narrowly scoped elevated installation step before
  sealing/confirmation. No account, service, credential, or ACL was created or
  changed during this probe.
- Two broader independent GPT-5.6 Sol preregistration reviews were retained as
  `REQUEST CHANGES`, not treated as approval. The scientific review found that
  retention data could influence development, WikiText units were inconsistent,
  the later ALC program was absent from the master roadmap, the development
  failure string did not match the required terminal status, confirmatory corpus
  construction and the exact scoring/invariant matrix were incomplete, sealed
  overlap identities could leak, the pilot was not literally 200 successful
  updates, and the roadmap still called a fixed optimizer an optimization
  candidate. The execution review of plan SHA-256
  `00c713f5fd250416c19f5cca92f4425b23233f916497e2cc91f2ba4e800e2206`
  confirmed earlier broker, statistic-edge, attempt-ledger, resource-accounting,
  and completion-root fixes, then found three remaining Medium gaps: canonical
  base/alias digest bytes, split Windows/Linux platform locks and transfer
  provenance, and this trajectory's stale account of the repairs.
- The live draft was repaired without opening held-out data or starting model
  acquisition/training. Retention test suites are now sealed confirmatory-only;
  WikiText uses one row-document unit consistently; the exact top-level failure
  remains `ALC-R0 FAILED IN TESTED SCOPE` with a separate frozen failure stage;
  and the master roadmap now places ALC-R1/R2/R3/R4, ALC-S0/S1, ALC-E0/E1, and
  ALC-L in dependency order before Tasks 13–14. Confirmatory retraining now uses
  only the original frozen training IDs, exact seed shuffle, no drop-last,
  `ceil(N/16)` updates per epoch, actual-count normalization, and the frozen
  warmup equation. The normative matrix fixes 40 trainable artifacts, 2 zero
  artifacts, 58 held-out target rows, 22 retention rows, all-capsule remount and
  size/resource gates, and all-artifact base-digest coverage.
- Pre-score disclosure is reduced to aggregate counts plus one whole-shard
  ciphertext commitment; per-group/linkable roots and identities remain sealed.
  Each pilot job must produce exactly 200 successful journaled updates. The
  600-GPU-hour cap now charges every valid, invalid, failed, retried, and resumed
  attempt, correcting the older historical `600 valid GPU-hours` wording above.
  Logical-run and attempt IDs, append-only transitions, exact-resume boundaries,
  and total resource accounting are validator-enforced.
- The base-state proof now has a versioned `ALCBASE` binary domain, a closed
  dtype-ID table, tagged length framing, little-endian raw bytes, and stable
  state-dict-name/offset/stride alias groups that forbid process addresses. A
  shared-storage known-answer fixture and independent-load equality are required.
  Separate hashed Windows-training and Linux-evaluator locks, a rootfs manifest,
  an immutable phase/platform contract, broker-hashed SafeTensor/JSON transfer,
  and explicit P9/P10/P11 reference sides now bind the two runtimes. The claim
  ledger excludes both itself and the post-ledger completion artifact, while the
  validator emits the completion artifact hash out of band, removing the former
  self-hash cycle.
- The repaired preregistration plan SHA-256 is
  `686335eb416480604efbb34fe0e57443b601b8a40f650019c7051d64d3f8153f`.
  It remains a draft pending fresh independent scientific and execution CLEAR
  verdicts. R0.0 is not open yet; no model/dataset acquisition, training, or
  held-out access is claimed.
- A same-pass consistency scan found two residual singular/legacy phrases after
  that hash: the freeze receipt still named opaque test roots and R0.0 still
  named one environment lock. They were repaired to permit only aggregate
  counters plus the whole-shard ciphertext commitment and to require both
  platform locks with the evaluator-rootfs/transfer manifests. The superseding
  plan SHA-256 submitted for fresh rereview is
  `5a743de4493ab1b8e184bf2e1be8cf537fcb0f853c4c7dd2e964eb33eb5e0064`;
  the status remains preregistration draft.
- The fresh execution rereview then found two further serialization/boundary
  ambiguities before verdict. The R0 non-goal now excludes product/capsule
  encryption and end-user signing while explicitly classifying experimental
  AES-GCM/HMAC as held-out custody only. The transfer intent is RFC-8785 JSON
  authenticated with domain-separated HMAC-SHA-256 under a distinct sealer-only
  key and bound to the broker launch receipt. The alias digest grammar now has
  explicit group/member tags, group/member counts, UTF-8 name length, unsigned
  scalar encodings, and two's-complement little-endian stride encoding. The
  superseding plan SHA-256 is
  `02bbb0570a5696bdd38fd013dce70e094fc15cdd7984893b3705c85c7b0efef9`;
  independent review remains open and no execution gate is claimed.
- The same rereview found that generic `acquisition` wording still placed public
  confirmatory test bytes in the Windows development environment. Acquisition is
  now split by actor and platform: model/card/license plus target train/dev bytes
  use the hashed Windows environment, while every target and retention test
  split is fetched only by `ALUCLU_R0_SEALER` in its dedicated evaluator distro
  and streamed through one audited normalize/filter/encrypt command with no
  development-readable path, cache, descriptor, or artifact. The sealer's
  source-only network namespace is destroyed before shard commit; held-out
  scoring remains networkless. The master roadmap was also tightened so a
  falsification/blocker terminates or pauses its branch; only PASS unlocks a
  dependent phase. The superseding plan SHA-256 is
  `fc219ae22c62ffe5fb3f5108e7d9eb1b347eb648f454be7892165cd1929997b9`.
- Two independent GPT-5.6 Sol reviewers then reread the exact stable
  `fc219ae22c62ffe5fb3f5108e7d9eb1b347eb648f454be7892165cd1929997b9`
  plan bytes plus the master roadmap and trajectory. The final scientific
  preregistration verdict was `CLEAR` with Critical 0, High 0, Medium 0, Low 0.
  The final execution/reproducibility preregistration verdict was also `CLEAR`
  with Critical 0, High 0, Medium 0, Low 0. Both independently confirmed the
  acquisition boundary, exact matrices, statistics, digest grammar, dual
  platform locks, broker/sealer design, evidence closure, terminal taxonomy,
  and rule that only PASS unlocks dependent work. Neither reviewer edited the
  repository; `git diff --check` passed with only existing LF/CRLF warnings.
- The only post-review change was the preregistration status line: the design is
  now approved and R0.0 freeze/acquisition implementation is open. This is not a
  development-training or held-out-scoring authorization; those remain blocked
  until the R0.0 machine validator passes on a committed tracked-clean state.
  The resulting status-only plan SHA-256 is
  `0564ee0415e8fa0cb0b0563587ea767fb3bd48b45c5cd3561d7d0c51497cbcbc`;
  the master-roadmap SHA-256 is
  `fb2ab85d761ef0ab72f96f20337c3677339b3c1aad3b839ee35eeb71d5bf05aa`.

## 2026-09-20 — ALC-R0 R0.0 implementation checkpoint 1

- Commit `917387ee75d37b1fb46f4d0192ef0e4b64a24693` containing the approved
  preregistration, unified roadmap, and full review chronology was pushed to
  `origin/codex/unified-lifelong-cognition`. The historical untracked Task 2 logs
  and root `uv.lock` were not staged, changed, or deleted.
- A read-only R0.0 repository-layout audit found that Task 2 canonical JSON,
  `tensor_tree_bytes`, the release validator, and the untracked project `uv.lock`
  do not implement the R0 scientific contracts and must not be reused as if they
  did. It also found three preregistration gaps before implementation: no legal
  namespace for R0.0 control receipts, no exact non-contiguous/zero-size storage
  span rule, and ambiguity over whether the alias bytes belong to the P10 digest.
  The plan now freezes one combined `ALCBASE` stream, exact offset/span/stride
  handling with negative-stride rejection, explicit `control` and `final`
  evidence namespaces, and a fully clean dedicated scientific checkout. The
  amended plan SHA-256 is
  `0493eeed795dbf089babe54bc14204e30d82c7381c4b819afdf986c0baff6c9b`.
- The first external runtime mutation is isolated outside OneDrive at
  `C:\Users\kaann\AppData\Local\ALUCLU\research\alc-r0-smollm2-135m-v1`.
  `uv 0.12.5` created a non-system-site-packages Windows environment with managed
  CPython 3.12.13; its `python.exe` SHA-256 is
  `5731ffcb818b3868c98038171d06c7c9571c975d6cf335634d7a4748ce3f84c7`.
  No model or dataset bytes have been acquired and no training or held-out
  scoring has begun.
- Separate pinned dependency inputs were created for Windows training and Linux
  evaluation. Their SHA-256 values are respectively
  `45beaa397ebafb0f61dd1c88de912ace7b449b57574fa848ae0b0e091b2f458c`
  and `56add7a92c2921e3ae50721257d61e5484382271616517f86c7a7e5e72223f68`.
  Both use official CPython-3.12 CUDA-13.0 Torch 2.14.0 wheel URLs with explicit
  upstream hashes and pin the complete R0 user-space stack. The generated Linux
  lock is 80,958 bytes with SHA-256
  `4b6bb24c97a1accd301856f253957ded0fd3b8fed465c79f2bf37beafb3e1c65`;
  it remains provisional until reproduced inside and bound to the dedicated
  evaluator rootfs. Windows lock generation is still an observed live resolver,
  not yet a completed artifact. Free `C:` space was 45,324,226,560 bytes, above
  the mandatory 20-GiB floor.
- The first R0.0 implementation slice adds an isolated `aluclu.alc_r0` package.
  Its canonical layer enforces strict UTF-8/no-BOM, duplicate-key and nonfinite
  rejection, RFC-8785 byte equality, LF-only canonical JSONL, exact SHA-256, and
  normalized relative evidence paths including Windows-casefold collision
  rejection. The `ALCBASE` layer implements the version-1 combined binary stream,
  closed dtype map, deterministic tensor ordering, raw no-cast bytes, stable
  name/offset/span/shape/stride alias groups, and diagnostic alias digest without
  serializing process pointers. The acquisition layer inventories an absolute
  local snapshot, rejects unsafe weights/symlinks/path escape, verifies all four
  preregistered SmolLM2 hashes, and produces a canonical-ready receipt; normal
  tests use fake local snapshots and perform no network download.
- Focused RED-to-GREEN verification now reports 46 passing tests across canonical
  evidence bytes, JSONL/path failures, hand-calculated tensor stream bytes,
  aliases/disjoint views/non-contiguous/zero/BF16 cases, unsupported tensor
  failures, exact snapshot inventory, pinned revision, missing/tampered files,
  unsafe weight formats, symlink denial, and absolute-root enforcement. Ruff and
  compileall pass for the new files, and `git diff --check` reports only the
  existing Markdown/pyproject LF-to-CRLF warnings. This is an R0.0 implementation
  checkpoint, not an R0.0 validator PASS or capability result.
- Both dependency resolvers then terminated successfully. The Windows lock is
  73,416 bytes with SHA-256
  `a7a921f7b095b0329fbb7df6a25612c6e8a1f160122f853a6a159d8478946615`;
  the Linux lock remains the 80,958-byte provisional artifact above. Their
  RFC-8785 lock manifest is 1,030 bytes with SHA-256
  `1756f42033d4de2f5d2944fc7a95a4e324665a26f54c0679bb757658fc91abaf`.
  The Windows environment was synced from its lock with `--require-hashes` and
  `uv pip check` reports all 50 packages compatible.
- The locked Windows environment independently reports CPython 3.12.13, Windows
  11 build 26200, Torch `2.14.0+cu130`, CUDA runtime 13.0, Transformers 5.17.0,
  Hugging Face Hub 1.32.0, SafeTensors 0.8.0, Tokenizers 0.23.2, NumPy 2.5.3,
  pytest 9.1.1, and Ruff 0.16.8. A real RTX 4050 CUDA BF16 matrix multiply
  completed and synchronized. The same environment reran all 46 new focused
  tests successfully and Ruff remained clean. Free `C:` space after lock sync
  was 43,809,165,312 bytes, still above the fixed floor. This proves the Windows
  user-space environment and first implementation slice fit; it does not prove
  model acquisition, the Linux evaluator rootfs, the sealer principal, the R0.0
  closed-world validator, or any neural capability.
- Pinned Pyright 1.1.413 initially found one test-only typing mismatch in the
  sparse-layout negative fixture. The fixture was repaired to pass explicit
  tensor indices/values rather than list literals. The full new R0.0 slice then
  returned Pyright `0 errors, 0 warnings, 0 informations`, 46/46 pytest PASS,
  and Ruff PASS in one rerun.
- The evidence-path boundary was then tightened for the actual Windows/Linux
  interchange: alternate-data-stream colons, ASCII controls, trailing dot/space,
  and Windows device names are now rejected in addition to traversal, absolute,
  backslash, NUL, duplicate, and casefold-collision cases. The expanded final
  checkpoint rerun is 50/50 pytest PASS, Ruff PASS, Pyright 0/0/0, compileall
  PASS, and diff-check clean apart from the known line-ending warnings.
- Repository attributes now pin every R0 lock/input/schema/experiment/result
  evidence family to LF checkout bytes. The staged Git blobs, rather than only
  the Windows working-tree views, were hashed after targeted renormalization:
  the Windows lock is 73,416 bytes and
  `a7a921f7b095b0329fbb7df6a25612c6e8a1f160122f853a6a159d8478946615`,
  the provisional Linux lock is 80,958 bytes and
  `4b6bb24c97a1accd301856f253957ded0fd3b8fed465c79f2bf37beafb3e1c65`,
  and both contain LF with no CRLF. The staged RFC-8785 manifest remains exactly
  1,030 bytes, has no final newline or CRLF, and hashes to
  `1756f42033d4de2f5d2944fc7a95a4e324665a26f54c0679bb757658fc91abaf`;
  both staged requirement-input hashes also match the manifest. This closes the
  cross-platform byte-identity defect for these artifacts, not the still-open
  R0.0 schema, closed-world validator, evaluator-rootfs, sealer, or acquisition
  gates.
- The first post-renormalization pytest invocation omitted `PYTHONPATH=src` for
  the deliberately non-editable external research environment and therefore
  stopped during collection with three `ModuleNotFoundError: aluclu` errors.
  This was classified as an invocation/configuration failure, not a test or
  implementation failure. Repeating the same three-file suite under the same
  locked CPython 3.12 interpreter with the explicit source root returned 50/50
  PASS. In the same checkpoint Ruff passed, pinned Pyright 1.1.413 remained
  0/0/0, compileall passed, and the staged diff-check exited zero.

## 2026-09-20 — ALC-R0 R0.0 implementation checkpoint 2

- Freeze-foundation checkpoint
  `5fa4b63077cf2594d8133a270c2b780d6ac5f278` was committed and pushed to
  `origin/codex/unified-lifelong-cognition`. It is explicitly an implementation
  checkpoint, not an R0.0 validator PASS. Historical untracked Task 2 logs and
  the root `uv.lock` remain untouched and outside the commit.
- The next TDD slice began with an expected RED collection failure because
  `aluclu.alc_r0.schema_validation` did not yet exist. Versioned Draft 2020-12
  schemas and a fail-closed validator were then added for the two currently
  materialized R0.0 documents: `lock-manifest` and `acquisition-receipt`.
  Unknown schemas, noncanonical evidence, noncanonical/symlinked schema roots,
  unknown fields, moving model revisions, reordered platform locks, unsafe or
  colliding inventory paths, pinned model-file mismatches, and inventory-root
  mismatches now fail validation.
- Both schema sources are exact RFC-8785 JSON with no BOM, CRLF, whitespace, or
  final newline. The acquisition schema is 1,095 bytes with SHA-256
  `6b08e0be6a4713c9afff8ff51fcb792a5ce8b24110ea442bb27f2661eaec7735`;
  the lock-manifest schema is 2,064 bytes with SHA-256
  `9cc92a3e41dc845da357067b6e13c31c88e6b47fc6631764027dce0ad7e2db2f`.
  A checked-in canonicalizer performs atomic exact-byte rewrites for future R0
  JSON source files. The R0 optional dependency surface now names both pinned
  RFC-8785 and JSON-Schema implementations explicitly.
- The tracked real lock manifest, not only a synthetic fixture, validates as the
  expected ordered Windows-training/Linux-eval pair. Focused schema validation
  reached 12/12 PASS; the combined R0.0 slice reached 62/62 PASS. Ruff, pinned
  Pyright 1.1.413 at 0/0/0, and compileall passed. A newly added format check
  initially found six line-wrapping-only differences; targeted formatting made
  the repeated check 10/10 files formatted, after which all 62 tests and every
  static gate passed again. Diff-check exits zero with only Git's known
  working-tree LF/CRLF notices.
- An idempotence run of the checked-in canonicalizer reproduced both schema
  files byte-for-byte and left no schema diff. A subsequent package check was
  first invoked incorrectly as `python -m pip check`; the deliberately minimal
  uv-managed environment contains no `pip` module, so that command exited 1
  with `No module named pip`. Reissuing the check through the environment's
  actual manager, `uv pip check --python <locked-python>`, inspected 50 packages
  and reported all installed packages compatible.
- This checkpoint does not yet enumerate the machine preregistration artifact
  matrix, validate closed-world result packages, provision/bind the dedicated
  Linux evaluator rootfs and sealer principal, or acquire the pinned model and
  data. Development training and held-out scoring therefore remain unauthorized.

## 2026-09-20 — ALC-R0 R0.0 implementation checkpoint 3

- Schema checkpoint `815f9cbf526c26cd243271dd5071bdb2806ad4dc` was
  committed and pushed. The exact SmolLM2 revision was then queried with the
  locked Hugging Face CLI in dry-run mode: it declared 10 files and about 272 MB,
  with SafeTensors as the only weight format. The first real-download invocation
  combined `--local-dir` and `--cache-dir`; Hugging Face Hub 1.32.0 rejects that
  combination, so it exited 1 before downloading model content. The corrected
  exact-revision invocation retained the dedicated `HF_HOME`, removed only the
  incompatible flag, and completed successfully.
- The packaged Windows runtime maps the requested external LocalAppData path to
  its physical Codex `LocalCache` path; both names resolve, and the CLI reported
  the physical location. Hugging Face added 13 local cache-metadata files beside
  the 10 declared repository files. A new final snapshot directory was created
  from only the 10 declared files, excluding all downloader metadata. No model
  byte entered OneDrive or the Git repository. Free `C:` space after acquisition
  was 43,499,671,552 bytes.
- The final snapshot contains 10 files and 272,445,324 bytes. Every file was
  inventoried and hashed. The four preregistered binding hashes for
  `config.json`, `model.safetensors`, `tokenizer.json`, and
  `tokenizer_config.json` all match exactly. The canonical inventory SHA-256 is
  `d9db0058a63990399f26b53ff7480f2e67bd5ef9a0398797fecfeb4ed9732b0e`;
  its current 1,616-byte acquisition receipt hashes to
  `2a4baddc2bb8451811e199e7dd6f91512fad73d367083c833e117c3e4d09984a`
  and passes the frozen acquisition schema plus semantic validator. This receipt
  is not yet committed as authoritative evidence because the host-loader source
  commit was still being formed.
- The offline host-loader slice began with the expected missing-module RED. Its
  implementation now requires all three offline flags, re-verifies the complete
  snapshot, uses only an absolute local directory with
  `local_files_only=True`, `trust_remote_code=False`, and
  `use_safetensors=True`, checks the frozen architecture/config identity, loads
  BF16, switches to eval mode, and freezes every base parameter. Dependency
  injection keeps normal tests networkless without global monkeypatching.
- A real offline load from the final snapshot returned
  `transformers.models.llama.modeling_llama.LlamaForCausalLM`, exactly
  134,515,008 base parameters, zero trainable parameters, eval mode, CPU BF16,
  and all frozen config fields equal. Two separate fresh Python processes then
  independently loaded the model and encoded `state_dict(keep_vars=False)`.
  Both produced 273 entries, 272 storage groups, 325,706,271 combined stream
  bytes, ALCBASE SHA-256
  `ce7e8dd6a97ac4cc56bf4f1e38625817386e27af58f1ed63377741f7f2aab1ba`,
  and alias-section SHA-256
  `8efcc3120c19a1a0784811d4ae95d327849ad8e7bd9176d45c3a6b9b7f067a84`.
- Six host contract tests pass and the combined R0.0 slice is 68/68 PASS. The
  first static pass found two import/export-order lint findings and two
  line-wrapping-only format findings; targeted mechanical fixes were applied.
  The repeated gate is 68/68 tests, Ruff PASS, seven files already formatted,
  pinned Pyright 1.1.413 at 0/0/0, compileall PASS, and diff-check exit zero with
  only the known line-ending notice. R0.0 still lacks committed acquisition/base
  receipts, the machine preregistration matrix, closed-world validator, datasets,
  Linux evaluator rootfs, and sealer/broker proof; training remains blocked.

## 2026-09-21 — ALC-R0 R0.0 implementation checkpoint 4

- Host-loader checkpoint `176d37652a857f4aabd230190e4cf71c0dca6fcb` was
  committed and pushed. The prior GPT-5.6 Sol layout reviewer was then asked for
  an independent read-only code/security rereview of `5fa4b63..176d376`, but the
  agent terminated at the account usage limit before reviewing any code. No
  independent CLEAR is claimed; the rereview remains open.
- Receipt TDD began with the expected missing `host_evidence` module RED. During
  implementation, the real acquired inventory exposed a contract weakness: the
  first acquisition verifier bound the four preregistered core hashes but still
  allowed drift in the other six exact-revision files or an eleventh file. R0 v1
  now pins all 10 upstream files and rejects any missing, changed, colliding, or
  extra path. Generic test expectations may still opt out of an exact file set;
  the production SmolLM2 expectation cannot.
- The acquisition schema is correspondingly closed to exactly 10 UTF-8-sorted
  records. Its earlier 1,095-byte
  `6b08e0be6a4713c9afff8ff51fcb792a5ce8b24110ea442bb27f2661eaec7735`
  form is superseded before development training by the 1,110-byte schema with
  SHA-256
  `d54d253f04c451556bbd58699cafe585f07ad176b316a1ac490e673a67c8ba42`.
  The acquisition receipt bytes themselves remain unchanged because the real
  verifier had already inventoried those same 10 files.
- A new 2,968-byte canonical base-digest receipt schema with SHA-256
  `9280147b0183906f27d19d69daebf22e4d8ce01d314318c761abf44e9b21e1da`
  freezes the observed model/config/runtime/count/digest identity, requires two
  equal fresh-process observations, binds the acquisition receipt and Windows
  lock/manifest hashes, and explicitly sets `training_authority=false`. Schema
  loading now rejects every nonlocal `$ref` before JSON Schema resolution, so a
  schema cannot introduce a network fetch. A dedicated host-evidence harness
  will refuse tracked source changes, verify the expected HEAD, spawn two fresh
  offline workers, validate both receipts, and create outputs without overwrite.
- The first combined test run correctly failed one fixture because it still used
  placeholder digest values while the new schema required the real ALCBASE and
  alias hashes. Updating only that fixture to the already observed values made
  the repeated R0.0 slice 76/76 PASS. Ruff passes, all 15 scoped files are
  formatted, pinned Pyright 1.1.413 is 0/0/0, compileall passes, and diff-check
  exits zero apart from known line-ending notices. The harness has not yet been
  run as committed source, so no generated control receipt is claimed here.

## 2026-09-21 — ALC-R0 R0.0 implementation checkpoint 5

- Host-evidence source checkpoint
  `4efd7d5a1958abacea93a4bac664c0674cd678b8` was committed and pushed. The
  committed harness then ran with that exact expected HEAD and no tracked or
  staged diff. The checkout still contains historical untracked Task 2 logs and
  root `uv.lock`, so this is intentionally a control proof with
  `training_authority=false`, not the later fully untracked-clean R0.0 release
  gate.
- The harness spawned two fresh CPython processes under all three offline flags.
  Each independently reverified the exact 10-file snapshot, loaded only local
  SafeTensors with remote code disabled, froze the base, and recomputed the full
  ALCBASE stream. Both observations are byte-identical and match the previously
  observed 273 entries, 272 storage groups, 325,706,271 bytes, combined digest
  `ce7e8dd6a97ac4cc56bf4f1e38625817386e27af58f1ed63377741f7f2aab1ba`,
  and alias digest
  `8efcc3120c19a1a0784811d4ae95d327849ad8e7bd9176d45c3a6b9b7f067a84`.
- The generated model-acquisition control receipt is exact canonical JSON, 1,616
  bytes, no final LF/CRLF, and SHA-256
  `2a4baddc2bb8451811e199e7dd6f91512fad73d367083c833e117c3e4d09984a`.
  The base-digest control receipt is 2,040 canonical bytes, no final LF/CRLF,
  and SHA-256
  `6d260faac2e527e34fe21a112e338be034e0b32894cf6e15c1c84f08fa6ff4e1`.
  A separate post-run process rehashed both files and reran their schema plus
  semantic validation successfully. These public metadata receipts contain no
  model weights, local paths, credentials, or held-out data.
- Regression coverage now loads both tracked control receipts through their
  frozen schemas. The resulting R0.0 slice is 78/78 PASS; Ruff passes, all 15
  scoped files are formatted, pinned Pyright 1.1.413 remains 0/0/0, compileall
  passes, and diff-check exits zero with only known line-ending notices. Their
  existence closes the model acquisition and same-host
  base-identity control artifacts only; it does not close the machine
  preregistration matrix, dataset freeze, Linux evaluator/sealer isolation,
  closed-world package validator, or any neural-capability threshold.

## 2026-09-21 — ALC-R0 R0.0 implementation checkpoint 6

- The first machine-run-matrix TDD slice began with the expected collection RED:
  `aluclu.alc_r0.run_matrix` did not yet exist. The implemented matrix now emits
  280 unique UTF-8-run-ID-sorted logical rows: four pilot trains, 76 development
  trains, 40 confirmatory trains, 58 held-out target-score rows, 22 retention
  rows, ten attach/detach rows, ten fresh-remount rows, 40 base-digest rows, ten
  capsule-size rows, and ten resource rows. Tests mechanically check the full
  72-row development Cartesian product, four q+v development references, arm
  cardinalities, frozen seeds/grid markers, unique normative run-ID grammar,
  deterministic reconstruction, and closed sorted artifact contracts. Its
  first focused GREEN was 4/4 PASS. This is the logical preregistration matrix,
  not yet the complete machine preregistration or closed-world validator.
- A subsequent attempt to select all R0 tests with the literal native-command
  argument `tests/test_alc_r0*.py` exited 4 before collection because PowerShell
  does not expand that wildcard for the Python process. The corrected command
  materializes the test-file array with `Get-ChildItem`; no implementation
  failure was inferred from the bad invocation.
- An independent GPT-5.6 Sol read-only review of exact committed HEAD
  `177ab33090fdbfbfd3a3b82dea267d0152757280` returned **BLOCKED**, not CLEAR.
  It confirmed the 78 committed tests, Ruff, receipt canonicality, exact model
  file set, ALCBASE grammar, and honest `training_authority=false` boundary, but
  found three high and two medium defects: acquisition semantics did not pin
  byte lengths; Draft 2020-12 `$dynamicRef` could escape the local-reference
  guard; the two host workers imported mutable worktree source after only one
  cleanliness check; evidence paths allowed Win32-illegal/glob characters; and
  the `alc-r0` optional extra omitted the exported Transformers/SafeTensors host
  runtime. The reviewer also reiterated that the matrix, datasets, Linux
  evaluator/sealer, closed-world validator, and final fully clean checkout gate
  remain open.
- Regression tests reproduced those boundary failures before repair. A receipt
  with `.gitattributes.byte_length = 999999` plus a recomputed inventory root was
  wrongly accepted; a malicious remote `$dynamicRef` reached the resolver and
  attempted DNS resolution; and all six of `<`, `>`, `"`, `|`, `?`, and `*`
  were accepted in evidence paths. The targeted run therefore failed eight
  cases exactly as expected. Production snapshot expectations now pin both
  SHA-256 and byte length for all ten files, and semantic validation rejects a
  false length even when the attacker recomputes the inventory root. Schema
  loading rejects non-fragment `$ref` and `$dynamicRef` recursively, while an
  explicit no-retrieval registry makes the network boundary independent of the
  keyword scan. Evidence paths reject every Win32-invalid filename character
  and device names after the relevant basename-space normalization, including
  `CON .json` and `lpt1 .txt`.
- Host proof workers no longer execute from the mutable working tree. The parent
  verifies the expected clean HEAD, exports that exact commit once to an
  ephemeral `.git`-free tree, derives the schema and lock inputs from the same
  export, and launches both fresh offline workers with only that export on
  `PYTHONPATH`. A new harness test first RED-failed because the export API did
  not exist. Its initial exact-byte assertion then exposed Git archive's
  deterministic checkout EOL conversion; the test was corrected to compare two
  independent exports of the same commit rather than incorrectly equating
  checkout bytes with Git blob bytes. Both harness tests now pass and verify one
  shared ephemeral commit export, deterministic tracked content, cleanup, and no
  `.git` directory. Existing control receipts remain non-authorizing; a new
  committed-source run will be required after this repair is committed.
- The `alc-r0` optional extra now explicitly provisions the pinned
  `transformers==5.17.0` and `safetensors==0.8.0` runtime in addition to the
  schema/canonical dependencies. The existing scientific Windows lock remains
  the authoritative executable environment; its 50-package `uv pip check` is
  clean. A later isolated-install fixture is still required as part of the
  closed-world package validation rather than being inferred from metadata.
- After the repairs and targeted formatting, the complete current R0 slice is
  94/94 pytest PASS. Ruff passes, all 17 scoped files are formatted, pinned
  Pyright 1.1.413 reports 0 errors/0 warnings/0 informations, compileall passes,
  and diff-check exits zero with only known LF-to-CRLF working-tree notices.
  R0.0 and all development training remain blocked on the rest of the machine
  preregistration, dataset/split freeze, Linux evaluator and sealer isolation,
  closed-world evidence validator, authoritative freeze receipt, and final
  independent CLEAR verdicts.

## 2026-09-21 — ALC-R0 R0.0 implementation checkpoint 7

- Run-matrix/security-repair checkpoint
  `6ad99656be57771515335cd6dfdccdef0eeadc9c` was committed and pushed to
  `origin/codex/unified-lifelong-cognition`. The first real host-proof launch
  supplied a manually expanded commit hash whose short prefix was right but
  remaining digits were wrong; the fail-closed expected-HEAD check rejected it
  before either model worker ran and created no receipt. The launch was repeated
  with `git rev-parse HEAD` as the exact authority, without weakening the check.
- The corrected committed-source run completed both fresh offline SmolLM2 loads
  from one ephemeral export of exact commit `6ad9965`. Both observations again
  agree on 273 entries, 272 storage groups, 325,706,271 encoded bytes, base
  digest `ce7e8dd6a97ac4cc56bf4f1e38625817386e27af58f1ed63377741f7f2aab1ba`,
  and alias digest
  `8efcc3120c19a1a0784811d4ae95d327849ad8e7bd9176d45c3a6b9b7f067a84`.
  This directly exercises the immutable-source repair rather than inferring it
  from unit tests.
- The regenerated acquisition receipt is byte-identical to the tracked artifact:
  1,616 canonical bytes, no CRLF/final LF, SHA-256
  `2a4baddc2bb8451811e199e7dd6f91512fad73d367083c833e117c3e4d09984a`.
  The regenerated base-digest receipt is 2,040 canonical bytes, no CRLF/final
  LF, SHA-256
  `d963fd85b5a3defd90391646323d6a3878e4f0dcb4c068e3e77a057990d4aa09`,
  and differs from the previous control only by its new exact source commit.
  A separate process revalidated both receipts against the frozen schemas and
  semantic checks; it confirmed the inventory root, fresh-process equality,
  `training_authority=false`, and source commit. The tracked base receipt is now
  advanced to this new control proof. This remains a host/source binding
  checkpoint, not R0.0 PASS or permission to train.

## 2026-09-21 — ALC-R0 R0.0 implementation checkpoint 8

- Canonical logical-matrix evidence began with four expected RED failures because
  `experiments/alc_r0/v1/logical-run-matrix.json` did not yet exist. The matrix
  builder is now bound to the exact 62,429-byte source plan SHA-256
  `0493eeed795dbf089babe54bc14204e30d82c7381c4b819afdf986c0baff6c9b`;
  changed plan bytes abort generation rather than silently producing a matrix
  from a different preregistration.
- The tracked matrix is 92,969 exact RFC-8785 bytes with no CRLF/final LF and
  SHA-256
  `56c18ae9b43137015c266e204a7c35e30cb77ff5b7dd401fb6014a232e7e1877`.
  It records all 280 closed logical rows, the source-plan path and digest,
  schema/matrix versions, exact expected artifacts per row, and
  `training_authority=false`. The build script requires an absolute new output,
  verifies the source-plan digest, and creates the file exclusively so it cannot
  overwrite prior evidence.
- The corresponding Draft 2020-12 schema is 1,883 canonical bytes with no
  CRLF/final LF and SHA-256
  `b768793250368533a5c44a7c41b9c3582a83817d85909ab24bd0aaa3233e5c64`.
  It closes top-level and row fields, count, enums, seed set, run-ID grammar,
  source plan, and non-authorizing status. Semantic validation then compares the
  complete row objects byte-for-meaning against the programmatically frozen
  expected matrix. Missing rows, added artifact contracts, and changed plan
  hashes are all negative fixtures and fail closed.
- The artifact is reproducible byte-for-byte from the committed source plan and
  builder. After two formatting-only findings were repaired, the full current
  R0 slice is 100/100 pytest PASS; Ruff passes, all 18 scoped Python files are
  formatted, pinned Pyright 1.1.413 is 0/0/0, compileall passes, and diff-check
  exits zero apart from known working-tree line-ending notices. This closes the
  logical-run-matrix component only. The full machine preregistration, package
  state machine/claim ledger, datasets, Linux evaluator/sealer, and final R0.0
  validator authority remain blocked and no training command is unlocked.

## 2026-09-21 — ALC-R0 R0.0 implementation checkpoint 9

- The independent GPT-5.6 Sol rereview of exact committed checkpoint `8810e0e`
  returned **BLOCKED**, not CLEAR. It verified the prior byte-length,
  `$dynamicRef`, common Win32-character, dependency-extra, row-count, seed,
  grid, and receipt-consistency repairs, but found four remaining contract
  defects: parent-side receipt code was imported from the launching worktree
  before commit export; ZIP extraction did not reject Windows drive-qualified
  members; attach/remount matrix rows omitted the plan-required stdout/stderr
  artifacts; and Windows reserved-device checks omitted the `COM¹/²/³` and
  `LPT¹/²/³` aliases. The review separately confirmed that the remaining
  dataset/evaluator/sealer/validator work is an open future gate, not a defect
  misrepresented as complete.
- The host harness is now a standard-library-only bootstrap until it exports the
  exact expected commit. It re-executes the **entire parent proof**, not only the
  two model workers, from that Git-free export with an export-only `PYTHONPATH`
  and commit-binding environment token. The committed parent and workers verify
  every imported R0 module origin is under the export root before acquisition,
  canonicalization, schema validation, observation, or receipt construction.
  Direct invocation of the hidden committed-parent mode without the bootstrap
  binding fails closed. The regression exercises the actual bootstrap command,
  cwd, environment, and hidden parent transition.
- Archive extraction now treats members as POSIX paths, rejects colon/drive,
  rooted, backslash, dot traversal, controls, Win32-invalid characters,
  reserved devices including superscript aliases, symlinks, and casefold
  collisions, and additionally proves each resolved target remains under the
  resolved export root. Drive, ADS-like, traversal, rooted, backslash,
  wildcard, and superscript-device malicious fixtures are all rejected.
- Both attach/detach and fresh-remount logical rows now include exact
  `stdout.log` and `stderr.log` requirements in addition to their receipts,
  exits, events, and remount predictions. Tests compare the complete per-kind
  artifact tuples rather than merely checking nonempty sorted lists. The
  canonical matrix was regenerated atomically from the still-frozen plan and is
  now 93,489 bytes with SHA-256
  `bcc21a94b66f19ecd2796e4263b497c772e9990977e57b66f6aa0b9c04c736b1`;
  this supersedes checkpoint 8's matrix hash before any development training.
- The expanded repair gate is 114/114 pytest PASS. Ruff passes, all 18 scoped
  files are formatted, and pinned Pyright 1.1.413 reports 0 errors, 0 warnings,
  and 0 informations. A new exact-commit real host proof is still required
  after committing these repairs; the previous receipt remains honestly
  non-authorizing and no R0.0/training claim is made.
- A read-only platform probe then confirmed WSL 2.7.12, kernel
  `6.18.33.2-microsoft-standard-WSL2`, systemd, and the RTX 4050 visible inside
  WSL with driver 610.78 and 6,141 MiB. The existing Kali 2026.1 distribution
  is general-purpose, Python 3.13, and has no sealer account, so it was not
  repurposed. A separate `ALC-R0-Evaluator` Ubuntu 24.04.5 LTS distribution was
  installed outside OneDrive under LocalAppData. It currently has Python 3.12.3,
  systemd, the same visible GPU, and a roughly 1.46 GB VHDX. Actual Windows `C:`
  free space after installation is about 36.9 GB; WSL's sparse virtual 978 GB
  figure is explicitly not treated as physical free disk. This is only a
  dedicated evaluator-environment foundation. The current non-elevated Windows
  token cannot create or ACL the required `ALUCLU_R0_SEALER` principal, and no
  key, held-out data, scoring authority, or scientific result has entered the
  new distribution.

## 2026-09-21 — ALC-R0 R0.0 implementation checkpoint 10

- Commit-pure host-harness checkpoint
  `526786fea7c4a4a9ed459a18b99eee2c646ea24f` was committed and pushed. The
  harness was then launched from the normal checkout with that exact expected
  HEAD. Its standard-library bootstrap exported `526786f`, re-executed the
  complete parent receipt builder/validator from the Git-free export, and the
  exported parent launched two further fresh offline workers from the same
  export. The end-to-end run exited zero, directly proving that the parent and
  worker provenance repair functions on the real pinned SmolLM2 snapshot.
- Both fresh observations again report 273 state entries, 272 storage groups,
  325,706,271 encoded ALCBASE bytes, combined digest
  `ce7e8dd6a97ac4cc56bf4f1e38625817386e27af58f1ed63377741f7f2aab1ba`,
  alias digest
  `8efcc3120c19a1a0784811d4ae95d327849ad8e7bd9176d45c3a6b9b7f067a84`,
  134,515,008 frozen parameters, zero trainable parameters, and eval mode. The
  real run therefore reproduces the prior numerical/model observation under the
  stronger complete-parent commit binding.
- The acquisition receipt remains byte-identical: 1,616 canonical bytes,
  SHA-256
  `2a4baddc2bb8451811e199e7dd6f91512fad73d367083c833e117c3e4d09984a`.
  The new base receipt is 2,040 canonical bytes, no CRLF/final LF, SHA-256
  `3bc973d0003160ab24f2b26c519129d48d7094a025381b41b1ffe152645d1953`,
  and binds source commit `526786f`. A separate schema/semantic test run is
  21/21 PASS after advancing the tracked control receipt. It remains explicitly
  `training_authority=false`; this closes the rereview's complete-parent
  provenance defect for the control proof, not the broader R0.0 gate.

## 2026-09-22 — ALC-R0 R0.0 implementation checkpoint 11

- The independent GPT-5.6 Sol rereview of exact checkpoint `addd213` returned
  **CLEAR for that checkpoint**. It independently recomputed the 2,040-byte
  base receipt and SHA-256
  `3bc973d0003160ab24f2b26c519129d48d7094a025381b41b1ffe152645d1953`,
  verified every receipt dependency against the `526786f` Git blobs, reproduced
  the 280-row logical-matrix counts and canonical hash, and ran the exact R0
  slice at 114/114 PASS. This closes the prior two HIGH and two MEDIUM review
  findings; it is not an R0.0 or training-authority verdict.
- The dedicated Ubuntu evaluator distribution was transferred to the plan's
  literal name `ALUCLU-R0-EVAL`; Kali and `docker-desktop` were not modified.
  The obsolete `ALC-R0-Evaluator` registration was removed only after the new
  distro booted and its Ubuntu 24.04.5, Python 3.12.3, WSL2 kernel, and GPU
  visibility were rechecked. Its temporary 1.25 GB transfer archive was moved
  to the Windows Recycle Bin rather than irreversibly deleted. Consequently it
  may still consume physical space until the user empties that bin; no claim of
  recovered space is made.
- Official `uv` 0.12.5 was installed at `/opt/aluclu-r0/tools/uv` from the
  retained 71,225-byte installer whose SHA-256 is
  `504511fbbbd811aeaba6738abc79408956b6c7da0ca35437b3dcc24a41efc111`.
  The executable SHA-256 is
  `b65f23a420c4acc96427efb30e5ed9bc0f7e25d2d712000f6ede77c1a0de5f46`.
  The first sync command was invalid before package installation because a
  PowerShell-to-WSL quoting error erased its shell variables. The corrected
  literal-path command then resolved, hash-verified, and installed all 68
  packages from `linux-eval.lock` in 10m48s. The lock itself remains 80,958
  bytes with SHA-256
  `4b6bb24c97a1accd301856f253957ded0fd3b8fed465c79f2bf37beafb3e1c65`.
- The resulting isolated venv is CPython 3.12.3 with system site packages
  disabled. `uv pip check` reports all 68 packages compatible. Critical pinned
  versions are Torch `2.14.0+cu130`, Transformers `5.17.0`, SafeTensors `0.8.0`,
  jsonschema `4.26.0`, and RFC 8785 `0.1.4`; inspected imports resolve under
  `/opt/aluclu-r0/linux-eval`. A live RTX 4050 probe reports driver 610.78,
  6,141 MiB, compute capability 8.9, CUDA runtime 13.0, cuDNN 92400, and BF16
  support. An actual CUDA BF16 matrix multiplication returned
  `[[5.0,-4.5],[2.0,15.0]]` with deterministic algorithms enabled and cuDNN,
  matmul, and cuDNN TF32 disabled. The now-redundant dedicated uv download cache
  was cleaned after installation; the venv remains 5.6 GiB and passes the same
  dependency check. The ext4 filesystem was trimmed. Windows `C:` physical free
  space measured about 30.43 GiB after these operations; WSL's sparse virtual
  terabyte figure is still not treated as physical free disk.
- TDD for a machine-readable Linux bootstrap receipt began with the expected
  collection RED because `aluclu.alc_r0.linux_environment` did not exist. The
  new builder, closed Draft 2020-12 schema, schema semantics, capture command,
  and negative fixtures now pass 34 focused tests; the expanded R0 slice is
  127/127 PASS, and scoped Ruff, pinned Pyright 1.1.413 (0/0/0), and compileall
  also pass. The contract records exact distro/kernel/package/lock/runtime/GPU/
  resource evidence and requires a real BF16 probe, sorted full package
  inventories, dependency consistency, and import confinement. Crucially it
  hard-codes `training_authority=false`, `sealer_authority=false`,
  `held_out_data_present=false`, `dedicated_windows_principal_present=false`,
  `immutable_rootfs_present=false`, and `rootfs_manifest_present=false`.
  Therefore this checkpoint can prove a reproducible evaluator bootstrap only;
  the Windows sealer principal/ACL boundary, immutable minimal rootfs and
  transfer manifest, held-out sealer, and final R0.0 validator remain blocking.
- The first exact-commit capture attempt from a Git archive of `b4c42f4` failed
  before writing a receipt. `uv pip check` exited zero but emitted its status on
  stderr, while the capture code incorrectly searched stdout for a success
  phrase. This was classified as an evidence-capture implementation bug, not an
  environment or dependency failure. The check is now bound to the command's
  zero exit status, with a regression fixture proving that empty stdout after a
  successful invocation remains success; nonzero exit still raises and aborts.
- The repaired capture was committed as `ad5190d` and executed from a clean Git
  archive of that exact commit under `/var/tmp`, with only the archive's `src`
  on `PYTHONPATH`. Two preceding orchestration-only extraction attempts produced
  no receipt: WSL path conversion lost Windows backslashes, then a `/tmp` export
  disappeared across distro restarts; the final persistent `/var/tmp` export
  eliminated both conditions without changing the scientific contract.
- The resulting tracked bootstrap receipt is 33,885 canonical bytes, has no
  CRLF or final LF, and has SHA-256
  `f3eb83630369a7b71f08005ed69648eb0007143cbd911be45b5cb556cab1208a`.
  Independent Windows-side schema and semantic validation recomputed both
  sorted inventory roots, the exact 80,958-byte Linux lock hash, and the lock
  manifest hash. It records 68 venv distributions and 523 Ubuntu packages;
  Python inventory SHA-256 is
  `c1bbf35a04beb289acaf2098ccd3eac3a5dec7ecdaf6db5928e8d75891199739`
  and distro inventory SHA-256 is
  `ee10f55873b0921dbab0d21c2ac1195705f4c360cb54435d0650d1497a091494`.
  The receipt binds Ubuntu 24.04.5, kernel
  `6.18.33.2-microsoft-standard-WSL2`, ext4, CPython 3.12.3, the exact uv
  installer/executable hashes, and the live RTX 4050 BF16 observation to source
  commit `ad5190d`. All six authority/rootfs/held-out booleans remain false by
  schema and semantic contract. `linux-eval.lock` therefore remains honestly
  `provisional-until-rootfs-reproduced`; this receipt does not rename it
  `reproduced`.

## 2026-09-22 — ALC-R0 R0.0 implementation checkpoint 12

- Closed-world run-artifact work began with a new RED invariant: all 120 pilot,
  development, and confirmatory training rows lacked the SafeTensors output
  that later scoring/remount runs must consume. Without an allowed binary path,
  the planned orphan detector would either reject the learned artifact or force
  it outside the evidence graph. The fix adds exactly one
  `learned-artifact.safetensors` to every training row and to no non-training
  row. Pickle/Python/native payload extensions remain forbidden.
- The 280 logical run IDs and every prior row cardinality are unchanged. The
  regenerated canonical matrix is now 97,209 bytes with SHA-256
  `07dbe9cd100846ffa4acffe60f847cc0c9d0cdf7ff8756524621492f6023c2ee`;
  this pre-training repair supersedes the earlier 93,489-byte matrix before any
  development command is authorized.
- A new matrix-derived run-artifact contract freezes the run namespace to 20
  exact filenames/extensions and 1,922 expected files. It binds the new matrix
  bytes/hash, the approved source-plan hash, the exact run-path template, media
  types, per-kind occurrence counts, and primary key
  `(run_id, artifact_type, logical_id)`. JSONL records require explicit
  `event_id`, `example_id`, or `sample_id`; singleton JSON, logs, and selected
  SafeTensors receive closed constant logical IDs. The 6,732-byte canonical
  contract has SHA-256
  `604b961272040fe929ffa137be06a7d9e18d7265faf0e33a3282fee0aa362100`
  and `training_authority=false`.
- Exact regeneration plus dropped, renamed, extra-authority, wrong-count, and
  missing-SafeTensor fixtures fail closed. The focused matrix/contract/schema
  set is 39/39 PASS; the expanded R0 slice is 139/139 PASS. Scoped Ruff,
  pinned Pyright 1.1.413 (0/0/0), compileall, canonical-schema checks, and
  diff-check pass. This freezes only the **run** namespace. Control/final
  namespace allowlists, state/attempt transitions, foreign keys, orphan scan,
  claim ledger, completion artifact, datasets, sealer, and rootfs remain open;
  no R0.0 or training authority is claimed.

## 2026-09-25 — ALC-R0 R0.0 implementation checkpoint 13

- Independent GPT-6 Sol code/security and architecture reviews of `741b60f`
  both found a blocking run-path contract defect: the descriptor extension
  already included the leading dot, while the path template inserted a second
  dot. Literal expansion produced `metrics..json` and other paths outside the
  declared 20-filename allowlist. The preceding 139 PASS tests did not exercise
  template expansion and therefore did not clear this issue.
- A new RED test reproduced the double-dot path. The template now uses
  `{artifact_type}{extension}`; the canonical run contract and its closed schema
  were regenerated. The test expands every one of the 1,922 expected file slots
  across all 280 matrix rows and checks each against the declared filename.
  A negative mutation explicitly rejects the old double-dot template.
- The repaired canonical run contract is 6,731 bytes, SHA-256
  `e53a8c31d522afb51ab4ad218dd4ea606a681f56fe3e61a414df763725601ded`;
  its canonical schema is 3,268 bytes, SHA-256
  `f41e1069679dcef4c5ad0afab631cb1bbfe497d8283c231bcd403d42f263c6cb`.
  The logical matrix itself is unchanged. The R0 test slice is 141/141 PASS on
  CPython 3.13; scoped Ruff, Pyright 1.1.413 (0/0/0), compileall, and
  `git diff --check` pass. Both independent reviewers returned CLEAR for this
  four-file repair; those verdicts cover this defect, not the full R0.0 gate.
- `training_authority=false` remains fixed. The control/final allowlists,
  attempt/state and foreign-key validation, orphan scan, claim ledger,
  completion artifact, datasets, sealer, immutable rootfs, and clean-checkout
  R0.0 machine gate remain open. The worktree's pre-existing untracked Task 2
  logs and root `uv.lock` remain untouched; this worktree is not clean-checkout
  training evidence.

## 2026-09-25 — ALC-R0 reference neural math checkpoint 14

- Implemented only the preregistered ResearchCapsuleV0 **reference factor math**:
  width 576; port sets `{14}`, `{29}`, `{14,29}`; ranks `{4,8,16}`; per-port
  FP32 factors `A[rank,576]`, `B[576,rank]`; local-seeded Kaiming-uniform A;
  exact-zero B; RMS normalization with `1e-5`; and the `alpha=rank` residual
  multiplier of one. Factor initialization uses a private CPU generator and
  leaves global Torch RNG unchanged. The distinct P6 all-positive-zero control
  zeros **and freezes** both factors at every selected port.
- TDD began with the expected missing-module collection RED. The first GREEN
  passed basic shape/count/no-op/gradient/math tests, but independent GPT-6 Sol
  review reproduced two real scientific bugs: inherited BF16 autocast made
  both linear intermediates BF16 instead of FP32, and the never-trained P6
  zero control still had `requires_grad=True`. New RED tests reproduced both.
  The repair disables autocast around normalization and both linear operations,
  casts only the completed delta to the host activation dtype, and freezes P6
  factors. Targeted independent rereview returned CLEAR for this narrow math
  slice; host wrapping and training were explicitly outside its verdict.
- The focused capsule file is 16/16 PASS on Windows CPython 3.13 with Torch
  2.6.0+cu124, including an actual RTX 4050 CUDA BF16 forward under enabled
  autocast. The expanded R0 test slice is 157/157 PASS. Scoped Ruff, Pyright
  1.1.413 (0/0/0), and compileall pass. A separate CPython 3.12/Torch
  2.14.0+cpu direct-module smoke confirmed a 4,608-parameter no-op; its full
  pytest collection was unavailable because that existing environment lacks
  `rfc8785`, so it is **not** claimed as a Torch 2.14 regression PASS. Neither
  existing environment was changed to work around this limitation.
- This is not a trained artifact or neural capability result. The official
  SmolLM2 host wrapper and no-capsule forward conformance, parameter-matched
  LoRA comparator, immutable manifest/SafeTensors serializer, trainer,
  control/final artifact namespaces, data/sealer/rootfs, and R0.0 machine gate
  remain open. `training_authority=false` remains in force; no training was run.

## 2026-09-25 — ALC-R0 pinned host-wrapper checkpoint 15

- TDD began with the expected missing-wrapper collection RED under the isolated
  Windows research environment. The real pinned snapshot was reverified and
  loaded through `load_verified_host` with offline flags, local SafeTensors,
  remote code disabled, exact SmolLM2-135M config, eval mode, and frozen base.
  The tested environment is CPython 3.12.13, Torch 2.14.0+cu130, and
  Transformers 5.17.0; model bytes stayed outside the repository.
- The reference wrapper explicitly iterates the pinned 30 decoder blocks and
  applies a mounted ResearchCapsuleV0 only after its declared block-output
  ports. It shares the existing verified base rather than instantiating another
  model; it uses no monkeypatch or forward hook. The same decoder path runs
  mounted and unmounted. On the real pinned host, unmounted CPU FP32 logits
  matched the official `LlamaForCausalLM.forward` **bitwise** for batch 1 at
  unpadded lengths 1, 8, 127, and 512; batch 2 with left/right EOS padding,
  unequal masks, and explicit/inferred positions; and initial plus one-token
  incremental cache decoding. A nonzero mounted capsule changed logits, while
  detach restored the exact baseline. An RTX 4050 BF16 real-host case also
  matched official logits at `rtol=atol=1e-3` with identical argmax tokens.
- Independent GPT-6 Sol review caught a genuine mode bug: ordinary
  `wrapper.train()` recursively turned the frozen base back to training mode.
  A RED real-host test reproduced it. The wrapper now keeps the base in eval
  mode through train/eval propagation, aligns the capsule's mode on mount, and
  fail-closes on later external base-mode or `requires_grad` drift. A second RED
  test reproduced the external-drift omission before the forward guard was
  added. The independent reviewer returned CLEAR for this **narrow wrapper
  slice**, and separately observed finite capsule gradients with zero base
  gradients in a no-update backward probe.
- Final pinned-environment R0 regression: 171/171 PASS; scoped Ruff PASS,
  pinned Pyright 1.1.413 0/0/0, and diff-check PASS. The 14 wrapper tests
  require the external pinned model and Transformers 5.17.0; they are skipped
  when those prerequisites are absent, so this is not a generic CI portability
  claim. No optimizer step or learning experiment was run.
- Full section-3 conformance remains open: GPU BF16 parity over the complete
  batch/length/padding/position/cache matrix, two fresh GPU processes, Linux
  evaluator parity, manifest/SafeTensors round-trip, and the exact matched
  native LoRA comparator are unproven. Control/final artifact namespaces and
  the R0.0 validator/sealer/rootfs are also open. `training_authority=false`;
  no ALC-0 neural-capability claim is authorized.

## 2026-09-25 — ALC-R0 no-capsule GPU forward checkpoint 16

- Extended the pinned SmolLM2-135M wrapper comparison on the real RTX 4050
  CUDA BF16 host. The matrix now exercises 20 non-cache cases: batch 1 at
  lengths 1/8/127/512 with explicit/inferred positions, and batch 2 at
  lengths 8/127/512 with left/right padding, unequal attention masks, and
  explicit/inferred positions. Four further cases exercise initial plus
  one-token cache decoding at lengths 1/8/127/512. Every case compares the
  official and unmounted wrapper logits at `rtol=atol=1e-3` and checks exact
  argmax equality. This is forward parity, not learning or quality evidence.
- Added a fresh-process worker that checks the same 24-case GPU matrix and
  emits canonical per-case SHA-256 logits digests with
  `training_authority=false`. The test starts two independent pinned-Python
  processes and requires byte-identical canonical output. A first pinned run
  passed with the host's unset cuBLAS setting; independent review reproduced
  a deterministic-cuBLAS failure under a *different* Torch 2.6+cu124 runtime.
  To make the child configuration explicit, the test now sets
  `CUBLAS_WORKSPACE_CONFIG=:4096:8` before launching each child, and the worker
  fail-closes if it is absent and records the value. This does not claim
  portability to the reviewer's different runtime.
- The final pinned Windows environment (CPython 3.12.13, Torch 2.14.0+cu130,
  Transformers 5.17.0) completed the expanded R0 regression with **195/195
  PASS, exit 0, 94.33 s** after that repair. Scoped Ruff and formatting pass;
  Pyright 1.1.413 reports 0 errors, 0 warnings, 0 informations; diff-check
  passes. Independent GPT-6 Sol rereview returned CLEAR for this *narrow*
  no-capsule GPU forward slice and withdrew the earlier pinned-lane blocker.
- P11 as a whole remains **OPEN**. The in-process GPU fixture may set the
  cuBLAS variable after another fixture initializes CUDA; the fresh child
  processes, not that fixture, provide the before-initialization guarantee.
  The full CPU FP32 matrix, detached-cycle repetitions, independent hashed
  Windows/Linux run manifests and claim-ledger evidence, exact matched native
  LoRA comparator, and later training gate are not discharged by this test.
  No optimizer step was run; `training_authority=false` remains in force.

## 2026-09-25 — ALC-R0 CPU FP32 forward checkpoint 17

- Expanded the same pinned real-host no-capsule CPU comparison from a partial
  sample to 20 static cases: batch 1 at lengths 1/8/127/512 with
  explicit/inferred position IDs, and batch 2 at lengths 8/127/512 with
  left/right padding, unequal masks, and explicit/inferred positions. Added
  four one-token incremental-cache comparisons at initial lengths
  1/8/127/512. Official `LlamaForCausalLM.forward` and the unmounted wrapper
  must produce **bitwise identical FP32 logits** in every asserted step; the
  cache length must advance exactly by one.
- The focused real-model CPU selection completed **24/24 PASS** in 74.69 s.
  The full pinned Windows R0 regression, including the prior 24-case GPU
  matrix and two-fresh-process check, completed **210/210 PASS, exit 0,
  140.82 s** on CPython 3.12.13 / Torch 2.14.0+cu130 / Transformers 5.17.0.
  Scoped Ruff, format, and Pyright 1.1.413 checks passed.
- This strengthens local no-capsule CPU conformance only. It does not by itself
  test every batch/padding combination under incremental cache, the complete
  ten-cycle detach matrix on final artifacts, independent Linux evaluator
  parity, or durable hashed run/claim-ledger evidence. P11 and R0.0 remain
  **OPEN**; no training or neural-capability claim is authorized.

## 2026-09-25 — ALC-R0 canonical capsule artifact checkpoint 18

- Started R0.1 serialization with a collection RED for the missing artifact
  module. Added an in-memory reference encoder/decoder for the pinned
  `ResearchCapsuleV0` factor set: RFC-8785 canonical JSON manifest plus
  SafeTensors FP32 factors. The manifest binds the exact SmolLM2-135M
  repository/revision/weight digest, identity-576 bridge, selected ports/rank,
  `alpha=rank`, epsilon, initialization seed, control kind, factor count,
  tensor byte length and SHA-256, and `training_authority=false`. The seed is
  canonical decimal text so the signed 63-bit range survives RFC-8785 JSON
  without IEEE-754 integer loss. The closed Draft 2020-12 schema is 1,549
  bytes, SHA-256
  `c81e55e0c4814a1737591fa63c7978f6cf86b0c872f34d34530b882f15dc4c82`.
- The decoder rejects noncanonical/extra-field/wrong-host manifests, wrong
  hashes or byte lengths, malformed/noncanonical SafeTensors, wrong factor
  names/shapes/dtypes, nonfinite factors, and artifacts over 256 KiB. The
  separate never-trained P6 zero control additionally requires frozen factors
  whose every FP32 element is **positive zero**; negative zero is rejected.
  The maximum grid's zero-control fixture has a 674-byte manifest and
  147,776-byte SafeTensors payload. Their SHA-256 values are respectively
  `c2dfcb53668db046195eda97a721cd43a49ebf5fbbd3ef6f3fa150d357d02084`
  and `f251ab9a14f995dc446b90dc1873c3fa7745f5df5f29994c09dca9c124125800`;
  these exact bytes matched local SafeTensors 0.7.0 and the pinned 0.8.0.
- The focused artifact/schema group passed **30/30**, and the added real
  SmolLM2 host integration test confirmed that a serialized-and-remounted
  zero control leaves official CPU FP32 logits bitwise unchanged. The final
  pinned Windows R0 regression incorporating that test passed **220/220,
  exit 0, 109.80 s** on CPython 3.12.13 / Torch 2.14.0+cu130 /
  Transformers 5.17.0. Scoped Ruff/format, pinned Pyright 1.1.413 (0/0/0),
  and diff-check passed. Prior 219/219 was run before this last integration
  test and is not used as final coverage evidence.
- This is a non-authorizing reference serializer, not a trained or activated
  neural identity. It does not establish a final learned-artifact namespace,
  full manifest/host approval for future hosts, the matched LoRA arm, Linux
  evaluator parity, claim ledger, sealer, or the R0.0 clean-checkout gate.
  `training_authority=false`; no optimizer step was run.

## 2026-09-25 — ALC-R0 exact matched q-only LoRA checkpoint 19

- Began the preregistered section-3.2 comparator with a collection RED for
  the absent LoRA module. Implemented an explicit **non-merged** q-only path
  at the selected decoder block outputs `{14}`, `{29}`, or `{14,29}` and
  ranks `{4,8,16}`. It uses the pinned Transformers 5.17.0 attention
  primitives without replacing/monkeypatching `q_proj`, changing base
  weights, or installing forward hooks. Its FP32 `A[rank,576]` and
  `B[576,rank]` per port have exactly `1,152 * rank` trainable parameters,
  local-seeded Kaiming A identical to the capsule arm at the same seed,
  exact-zero B, and `alpha=rank` multiplier one. FP32 factor math casts the
  completed delta to the host q-projection dtype. The wrapper rejects capsule
  co-mounting so this scientific control arm cannot silently combine methods.
- On the real pinned SmolLM2 host, focused tests passed **12/12**: zero-init
  CPU FP32 logits match official forward bitwise, nonzero LoRA changes logits,
  detach restores baseline, mask plus one-token incremental cache preserves
  bitwise parity, the base `q_proj` module identity is unchanged, gradients
  reach only LoRA factors, and a real RTX 4050 BF16 no-op matches official
  logits at `rtol=atol=1e-3` with identical argmax. Base parameters remained
  frozen and in eval mode. No optimizer step was run.
- The first expanded full R0 run reported **231 PASS / 1 FAIL** in 258.75 s:
  the pre-existing two-fresh-GPU-process test saw its first child exit 1.
  Its old `check=True` traceback did not expose the child stderr, so the
  root cause is **unknown**, not classified as a LoRA failure. Worse, copying
  the entire parent environment into that child caused pytest's traceback to
  print an unrelated API credential from the environment. The credential
  value is not recorded here; the user was advised to revoke/rotate it. The
  child now receives only an explicit non-secret environment allowlist, and
  a nonzero exit reports bounded child stderr. The isolated GPU subprocess
  test then passed **1/1**, and the complete final pinned Windows R0 suite
  passed **232/232, exit 0, 83.92 s**. The intermittent first failure remains
  a recorded unresolved observation; one clean rerun does not prove it can
  never recur.
- Scoped Ruff/format and pinned Pyright 1.1.413 (0/0/0) passed. This is
  structural and forward-equivalence evidence for the matched control, **not**
  LoRA training/evaluation, matched optimizer-budget proof, P11 Linux parity,
  or R0.0 authority. `training_authority=false` remains in force.

## 2026-09-25 — ALC-R0 non-authorizing claim-ledger candidate checkpoint 20

- Began the evidence-root algorithm with a collection RED for a missing
  ledger module. The reference candidate accepts an **exact caller-declared**
  R0 evidence path/media set; rejects missing/extra, unsafe, case-colliding,
  self-referential claim-ledger or completion paths; sorts files by UTF-8 path
  bytes; records exact byte length, media/schema type, and SHA-256; then
  computes `root_digest = SHA-256(RFC-8785 ledger without root_digest)`. Its
  own canonical JSON has `claim=null`, `status=candidate-non-authorizing`,
  and `training_authority=false`. Byte-for-byte verifier checks the candidate
  against actual input evidence and cannot grant ALC-0 or issue completion.
- Added a filesystem scanner for the same candidate: it checks the R0 tree
  for missing/orphan/nonregular/symlink entries and hashes each declared file.
  JSON must be canonical; JSONL records and UTF-8 logs are validated and
  hashed in a streaming pass, while SafeTensors bytes are hashed as opaque
  payloads at this layer. The closed Draft 2020-12 candidate schema is 1,246
  bytes, SHA-256
  `aef47f22b7e7eb5f1a7322acb29dc5f398f4a849ac53ee1ce60597548b60f0d9`.
  Tests cover digest/ordering tamper, wrong length/media, duplicate entry,
  malformed canonical bytes, case collision, orphan/missing file, symlink,
  invalid JSONL newline, and invalid UTF-8 log.
- Focused ledger/schema tests passed **33/33**. Full pinned Windows R0
  regression passed **244/244, exit 0, 82.65 s**; scoped Ruff/format,
  Pyright 1.1.413 (0/0/0), and diff-check passed. These tests prove the
  candidate algorithm and fixture scanner only. The authoritative machine
  preregistration still lacks the complete control/final artifact allowlist,
  attempt/state and foreign-key validator, P1–P14 completion gate, and sealed
  data/runtime receipts. Therefore no final claim ledger was generated,
  `training_authority=false`, and R0.0 remains **OPEN**.

## 2026-09-25 — ALC-R0 Banking77 development preprocessing checkpoint 21

- After checking the section-4.1 frozen plan, began with a collection **RED**:
  the Banking77 preprocessing module was absent. A separate SHA-256 calculation
  corrected the fixture's expected first dev ID to `intent_00-3` before the
  implementation. No raw dataset or official test split was opened.
- Added a pure official-*train*-row reference preprocessor. It applies Unicode
  NFC, CRLF-to-LF, and outer whitespace stripping; groups globally by
  normalized-utterance SHA-256; fails on conflicting labels or a hash
  collision; retains the UTF-8 lexicographically smallest source ID for a
  same-label duplicate; and records removed count plus a canonical JSON root
  over removed/retained ID pairs and normalized digests. It then sorts unique
  records independently within each of the 77 caller-declared labels using
  `SHA-256(20260916 || NUL || label || NUL || normalized_utterance_UTF8)`;
  the first `floor(0.20 * label_count)` are dev, the rest train. The supplied
  label order defines the cross-label output order. Ordered train/dev source
  ID lists each have their own RFC-8785 JSON SHA-256 root. No RNG or library
  split is involved.
- Synthetic fixtures cover Unicode/newline policy, frozen ID/root values,
  input-order independence, duplicate retention/root, cross-label conflict,
  malformed rows, invalid UTF-8 text, duplicate source IDs, and incomplete
  label vocabulary. Focused tests passed **9/9**. The complete pinned Windows
  ALC-R0 regression passed **253/253, exit 0, 81.89 s**. Scoped Ruff check,
  Ruff format check, Pyright 1.1.413 (0/0/0), and diff-check passed.
- This is algorithm/fixture evidence only. The pinned Banking77 source bytes,
  license and source manifests, train/dev receipt, sealed official test,
  independent sealer, full preregistration and validator are still pending.
  No model was trained or evaluated by this slice; `training_authority=false`
  and R0.0 remains **OPEN**.

## 2026-09-25 — Banking77 pinned development-source inspection checkpoint 22

- Inspected the upstream Git tree at pinned commit
  `9d081458ff52e53cf7e848f414e6e9344e4e6696`. Its Banking77 subtree
  contains `categories.json`, `train.csv`, and `test.csv`; the first two Git
  blob IDs match the preregistered values. Downloaded **only** categories and
  official train into the external local research cache (not this repository).
  The official test file was neither downloaded nor opened in this checkpoint.
- Verified exact raw bytes with `git hash-object --no-filters` because the
  Windows Git text filter changes the default `train.csv` hash. Categories:
  2,036 bytes, blob `cdd2a5c77a4079a455f8fb7e751d1ecee0e2a5a4`,
  SHA-256 `53261da888122daf2d120d925458631d9619e15d82e56052e7a42e535ce32b63`.
  Train: 839,073 bytes, blob `98e2543cf482d0dca7bfb175ebe35d98efad95be`,
  SHA-256 `b06e26ac675513959a63135f11b94ea7786ed02da65db93a5650d8838cbc664b`.
- A strict CSV parse observed **77 labels and 10,003 official-train rows**.
  Using provisional stable IDs `train:<zero-padded eight-digit row ordinal>`,
  the new reference preprocessor produced **8,030 train / 1,969 dev** and
  removed **4** same-label duplicate rows; no conflicting-label digest was
  encountered. Exploratory roots: duplicate
  `f789c0fd606467ed0daab68ebe370a9733189b964865b2e1ce8115fccd9036e8`,
  ordered train IDs
  `4b03398873873f7fb84cd3b3efd750d50354d7e28d990ef9ea904e05d6fb41f0`,
  ordered dev IDs
  `86da488d849d0fd4193f45bc2e2cde0b96066d5b3634c945939350b08e1231ea`.
- This one-off inspection is **not yet** a committed dataset acquisition
  command/receipt or frozen split manifest. The source-ID convention, parser,
  byte checks, license provenance, and roots must become tested machine-readable
  artifacts before any R0.0 validator or training authority can use them.
  `training_authority=false`; R0.0 remains **OPEN**.

## 2026-09-25 — Banking77 verified development-source receipt checkpoint 23

- Began with a collection **RED** for absent source verifier. Implemented a
  fail-closed loader for exactly `categories.json` and official `train.csv`
  outside the repository. It rejects an extra `test.csv`, symlinks/nonregular
  files, wrong byte lengths, SHA-256 or raw Git blob IDs, invalid UTF-8/BOM,
  malformed JSON/CSV, wrong CSV header/column count, invalid categories, and
  source categories missing from the pinned list. The CLI emits only canonical
  JSON metadata, never raw utterances or a local absolute path. It does **not**
  download, read, or seal an official test split.
- The first real-data run failed: upstream labels include
  `Refund_not_showing_up` and `reverted_card_payment?`, contradicting an
  overly strict `[a-z0-9_]+` parser assumption. Added a failing fixture,
  retained exact raw-category membership, then canonicalized by ASCII
  lowercasing while preserving terminal `?`; collisions fail closed. This
  clarifies the frozen plan's “canonical lowercase label” phrase without
  changing its thresholds or seed. The original plan bytes are immutable and
  SHA-256 `0493eeed795dbf089babe54bc14204e30d82c7381c4b819afdf986c0baff6c9b`;
  the explanation is in a separate development-source addendum. The raw-label
  exploratory train/dev ID roots in checkpoint 22 are **superseded**.
- On the pinned real source, the non-authorizing candidate receipt reports
  77 labels, 10,003 source rows, 4 removed same-label duplicates, 8,030 train
  and 1,969 dev. Canonical-label ordered ID roots are train
  `919ff91cb563d343fded98bef53cbb7b11f6510390b54d6c1c0ba196ba6223a6`
  and dev
  `e79ce9e072cb79d512fc2dd992cad87706a7916301f1692184752139e1e48627`.
  Ordered ID+label+normalized-digest roots are train
  `abef9ee5d2090eff6e01e63f3e849231b80e80d0639d5ad66d27a32012cab26c`
  and dev
  `6821b3458a5519df1122b2e0cf1cc821bf103961665f8ee215148693cb0eff5d`.
  The receipt is byte-for-byte reproducible from the locally verified source,
  is canonical JSON plus LF, and has SHA-256
  `398523ad80917277be7b1a94d6db4c26d86f403d12ec75559909af6408c60028`.
  No dataset bytes are committed.
- Focused source tests passed **8/8**. The first complete R0 run had **259
  PASS / 2 FAIL**: one was caused by my temporary edit to the byte-frozen
  source plan, the other was a first-child CUDA out-of-memory in the existing
  two-fresh-process forward test. I restored the exact plan bytes, moved the
  clarification to an addendum, and verified both failed tests **2/2** in a
  targeted rerun. The second complete pinned Windows R0 run passed
  **261/261, exit 0, 137.28 s**. Scoped Ruff/format, Pyright 1.1.413
  (0/0/0), and diff-check passed. The intermittent GPU OOM remains a recorded
  observation with undetermined cause; a later clean pass does not erase it.
- After the staged diff review, the receipt's source-ID description was made
  explicit about the zero-based data-row ordinal; this changed receipt bytes
  but not IDs, split membership, or roots. The final receipt was verified
  byte-for-byte against regenerated local source output (**1,494 bytes**),
  focused source tests passed **8/8**, and the complete pinned Windows R0
  regression on these final bytes passed **261/261, exit 0, 576.24 s**.
- This receipt binds the **development** source and split only. No model
  optimizer step or held-out evaluation occurred. The sealer/key broker,
  complete preregistration and validator, acquisition receipts for other data,
  Linux/Windows execution parity, and R0.0 clean-checkout gate remain open.
  `training_authority=false`; R0.0 is **OPEN**.

## 2026-09-25 — Local Desktop migration and Banking77 scoring checkpoint 24

- Per owner direction, active work moved out of the OneDrive Desktop tree to
  `C:\Users\kaann\Desktop\03_Projeler_Arge\ALUCLU\.worktrees\unified-lifelong-cognition-local`.
  This is a new worktree backed by the local Desktop repository, on
  `codex/unified-lifelong-cognition-desktop` at source HEAD `61202ae` before
  this checkpoint. The pre-existing similarly named local worktree had a stale
  `.git` pointer to OneDrive and many tracked deletions; it was left untouched.
  The former OneDrive worktree was also left untouched as a recoverable copy.
- Copied the two in-progress Banking77 scoring files into the local worktree;
  source/destination SHA-256 matched exactly. Preserved the other 16 untracked
  OneDrive files (old Task 2 logs and `uv.lock`, 212,074 bytes) under local
  `.migration-preserve/onedrive-untracked-20260925`, with per-file SHA-256
  comparison. The ordinal-sorted relative-path/hash inventory root was
  `d526ba6b85648722614db6c44d5f3277ccf6b8d02d2a9d30a56ec535defba659`.
  This is a copy-and-verify migration, not authorization to delete either old
  tree or the separate external model/dataset cache.
- Added fail-closed reference helpers for exact leading-space, no-special
  candidate tokenization, ordered token-map hashing, candidate-only training
  masks, separate full-candidate forward scores, conditional mean log
  probability, and UTF-8 byte tie-breaking. On the pinned real tokenizer the
  77-label candidate map root is
  `ce33efdc137af58036402da1fff96ccdcea9663843fa564c6f64def7d0e31878`.
  These helpers do not train a model or authorize the held-out evaluator.
- A prompt-length feasibility inspection using a *tentative*, non-frozen
  space-delimited 77-label template found 1,575 of 9,999 unique development
  rows above the 512-token cap (max 589 including the longest candidate).
  This is a design warning, not an accepted prompt/truncation policy or an
  R0.0 result. The official held-out test split was not accessed.
- First complete test run in the new local checkout: **268 PASS / 1 FAIL**.
  Git global `core.autocrlf=true` had changed the byte-frozen plan and
  candidate receipt to CRLF, breaking the exact-plan-byte oracle. Added
  explicit `text eol=lf` attributes for those two files and restored their
  checked-out LF bytes without changing the frozen content. Their SHA-256s
  again match `0493eeed795dbf089babe54bc14204e30d82c7381c4b819afdf986c0baff6c9b`
  (plan) and
  `398523ad80917277be7b1a94d6db4c26d86f403d12ec75559909af6408c60028`
  (receipt). Targeted rerun: **9/9 PASS**. Complete pinned Windows R0
  regression on the local checkout: **269/269 PASS, exit 0, 81.45 s**.
- This checkpoint establishes a usable local Desktop checkout and one Windows
  regression result, not cross-platform parity, training, or R0.0 PASS.
  `training_authority=false`; R0.0 remains **OPEN**.

## 2026-09-25 — OneDrive deletion-safety audit checkpoint 25

- Before advising any OneDrive cleanup, compared the old and local ALUCLU
  repository trees. The old `.worktrees/task27_portability` is a separate clean
  branch at `e4dea6e03344f8da199a6c4a05a4f0cfba9a7b88`, not present on
  the remote. Fetched that branch into the local Desktop Git repository and
  verified both sides resolve to the identical commit object. The roughly
  596 MiB ignored `.venv` in that old worktree was *not* copied.
- Preserved all 74 files under the old active worktree's ignored
  `.superpowers`, `.omx`, and `.omc` directories at local
  `.migration-preserve/onedrive-ignored-active-20260925`; every copied file
  matched its source SHA-256. Also copied the old repository's entire `.git`
  directory (1,091 files, 9.56 MiB) to
  `.migration-preserve/onedrive-git-20260925` and verified every file hash.
  The old main worktree's `.omc` files already matched the local main copy.
- Did **not** copy ignored virtual environments, Python bytecode or tool
  caches. Did not delete the OneDrive tree, the stale local worktree, or the
  separate `.codex` worktree still registered against the old Git directory.
  Therefore this is a verified source/history/evidence preservation step,
  **not** a claim of a byte-for-byte clone of every regenerable environment.

## 2026-09-25 — Banking77 common-prompt reference checkpoint 26

- Before touching held-out data or training, tested a small set of interface
  separators on the pinned development tokenizer. Space-separated canonical
  labels fit best among the tested delimiters; newline/comma/pipe variants
  exceeded the 512-token common budget even for a short query. Chose a
  development-only reference with ordered labels before the query, explicit
  `Intent:` boundary, separately tokenized prefix/query/suffix, and separately
  encoded leading-space candidate IDs. The original byte-frozen plan is not
  changed. The exact candidate rule and limitations are documented in
  `docs/superpowers/plans/2026-09-25-alc-r0-banking77-prompt-candidate.md`.
- Initial focused collection was **RED** (`ModuleNotFoundError` for the absent
  prompt module). Implemented a fail-closed template with a longest-candidate
  reserve and deterministic query-ID head/tail truncation. The first fake-only
  focused run was 4 PASS / 1 SKIP (real source paths not supplied); the pinned
  real-source/tokenizer run on final fixture bytes was **6/6 PASS**. The
  actual template measured prefix 472 IDs, suffix 4, maximum candidate 17,
  leaving 19 query IDs. Across all 9,999 unique official-train-derived rows,
  min/median/p95/p99/max query lengths were 3/11/34/49/96 IDs and
  **1,483/9,999 (14.83%)** required truncation. Every built prompt plus
  longest candidate was at most 512 IDs. This substantial truncation rate is
  a recorded capability-quality risk, not a threshold relaxation or PASS.
- Scoped Ruff check and format passed; Pyright 1.1.413 reported 0 errors,
  0 warnings, 0 informations. A full Windows R0 run before the last fixture
  assertion/formatting edit passed 275/275 in 121.60 s; it was not used as
  final-byte evidence. The repeat on final source/test bytes passed
  **275/275, exit 0, 80.29 s**. No model optimizer step, held-out split
  access, or confirmatory evaluation occurred. The prompt candidate still
  needs machine-readable R0.0 freeze/validator binding before it can authorize
  training. `training_authority=false`; R0.0 remains **OPEN**.

## 2026-09-25 — Banking77 prompt-token receipt checkpoint 27

- Began with a collection **RED** for missing `banking_prompt_receipt`.
  Implemented a development-only candidate receipt that hashes the source
  receipt, ordered labels, complete candidate-token map, fixed prefix/suffix
  token IDs, and ordered per-row prompt-token streams for train and dev. The
  stream roots bind source ID, canonical label, normalized-utterance digest,
  and exact prompt IDs, with a canonical JSON+LF record separator. The receipt
  stores no raw utterances or token lists. The verified-development loader in
  the CLI accepts only the pinned `categories.json` and `train.csv`; no official
  test split is read or acquired.
- The actual candidate receipt is
  `results/alc_r0_banking77_prompt_candidate_20260925.json` with SHA-256
  `0a2c08ef5dee37e9a75e8fe088a05be36392a696c1bf63bc82c5341256874661`.
  Its train/dev prompt roots are
  `8575d83d2f2356807bd35a51d7e6e02cfc47ee4da2c5c68d9715a443e368686a`
  and
  `3885747387075700f6b292c55d66669bc607c425fcc6cd0a10642727a76d3cc4`.
  The train/dev truncation counts are 1,207/276, summing to the previously
  observed 1,483. Added `text eol=lf` for this byte-identity artifact.
- Focused fake-only tests first passed 3/3 with one optional real-asset skip;
  with pinned development source and tokenizer supplied, final focused tests
  passed **5/5**, including a subprocess CLI byte-for-byte comparison against
  the tracked canonical receipt. Ruff check/format passed, Pyright 1.1.413
  reported 0 errors/warnings/informations, and the complete pinned Windows
  R0 regression passed **280/280, exit 0, 108.72 s**.
- This receipt is still **candidate/non-authorizing**. It does not independently
  verify tokenizer acquisition bytes, bind the complete multisuite R0.0
  preregistration, seal held-out data, or implement the R0.0 validator. No
  training or confirmatory evaluation occurred. `training_authority=false`;
  R0.0 remains **OPEN**.

## 2026-09-25 — Devign development-source acquisition checkpoint 28

- Moved beyond the Banking-only development lane to the second blocking real
  target family. Queried the official Hugging Face dataset repository at the
  plan-pinned commit `69bd48c03223c2104342acd9a807caf61ac3efb8` and
  acquired **only** `data/train-00000-of-00001.parquet` (17,847,670 bytes,
  SHA-256 `e319c83e2e816a10aeeebe78668aa95b757b04e555700bf5f826766b0e80bb06`)
  and `data/validation-00000-of-00001.parquet` (2,214,315 bytes,
  SHA-256 `a17a76ed040d7f8657d1ff741f967b44704c008101ac958e2990ad468203cfa4`)
  into the frozen non-OneDrive research data tree. The source `data/`
  directory contains exactly those two files; no official test file was
  downloaded or read. The upstream card declares C-UDA, so no dataset bytes
  are committed. C: free space after acquisition was about 39.17 GiB.
- Started with test collection **RED** for absent `devign_source`. The first
  implementation produced **2 FAIL / 3 PASS / 1 SKIP** because it incorrectly
  assumed `pyarrow.Table.null_count` exists; fixed this by checking each
  column's null count. The final verifier binds exact byte lengths/SHA-256,
  Parquet schema and row counts, nonnull fields, permitted project names,
  commit IDs, and globally distinct official IDs. A source ID is
  `devign:<zero-padded eight-digit official id>`. It rejects a test/extra file,
  same-length byte mutation, malformed schema, nulls, and cross-split ID
  collision. The verified real source has 21,854 train and 2,732 validation
  rows, 10,018/1,187 positive labels, and no source-ID overlap.
- The canonical non-authorizing receipt is
  `results/alc_r0_devign_development_candidate_20260925.json`, SHA-256
  `09926c5742825b274efb9e00fb536c2950811c8c01615cf5ef8ad1826c1e7d73`.
  The pinned-source test and subprocess CLI reproduce its exact bytes; the
  artifact has an explicit LF checkout attribute. Added the already-locked
  PyArrow 25.0.1 dependency to the `alc-r0` optional extras. Final focused
  real-source tests passed **9/9**; scoped Ruff/format and Pyright 1.1.413
  (0 errors/warnings/informations) passed. Complete pinned Windows R0
  regression passed **289/289, exit 0, 112.01 s**.
- This closes only a development-source acquisition slice. The plan's code
  normalization, 256-permutation MinHash/LSH and Jaccard clone filtering,
  independent test sealer, prompt and metrics contracts, full R0.0 validator,
  training, and held-out evaluation remain open. `training_authority=false`;
  R0.0 is **OPEN**.

## 2026-09-26 — Devign normalization and shingle candidate checkpoint 29

- Continued in the local Desktop worktree from source HEAD `bd24f76`, preserving
  the earlier uncommitted normalization/receipt files. The byte-frozen R0 plan
  still requires strict UTF-8, NFC, CRLF/lone-CR to LF, trailing ASCII
  whitespace removal per line, outer blank-line removal, C-like tokenization,
  five-token shingles, and later 256-permutation MinHash/LSH with exact Jaccard
  confirmation. This checkpoint implements **only** the deterministic
  normalization/token/shingle primitives and their development-source roots.
- Tests began RED for absent `devign_preprocess` and
  `devign_preprocess_receipt`. An initial hand-written normalization fixture
  SHA-256 was incorrect and the receipt initially exposed a different root
  field name than the fixture; both were repaired and the failures retained as
  development observations. Adversarial fixtures cover invalid UTF-8, empty
  code, wrong input type, NFC/LF/whitespace handling, literal/number and
  individual-punctuation tokens, shingle invariance under token whitespace,
  row-order mutation, code mutation, empty split, and authorizing-source
  rejection. The regex SHA-256 is
  `dd2d786ac51ead8d75adc5e22d5b7b06f1a5a398dd31f74b685384f704b93d8d`.
- Ran the primitives across all 21,854 train and 2,732 validation functions
  from the verified development source only. Normalization changed 20,442
  train and 2,566 validation rows; token ranges were 7–25,024 and 7–10,464.
  No row had an empty five-token shingle set. The canonical metadata-only
  candidate receipt is
  `results/alc_r0_devign_preprocess_candidate_20260925.json`, SHA-256
  `c23f2fd2c54a0fe648d8a08092b0bf9469b39444e47d0a1897b4d003edfe7e9f`.
  Its ordered normalized roots are train
  `f72efab00d173c14de86d0bccefb06423a23281a4fc9daabab4c807048474a14`
  and validation
  `37687d42fffdbbd6e0a1c31a33818902267c29bf7b1bc99a89edcbeaeea80c4f`.
  CLI regeneration matched its tracked canonical LF bytes; no code text or
  official-test data was committed or read.
- Final focused real-data tests passed **9/9**; scoped Ruff check/format and
  Pyright 1.1.413 passed (0 errors/warnings/informations). The final-byte
  pinned Windows R0 regression passed **298/298, exit 0, 255.22 s**. This is
  not a clone-filtering PASS. MinHash coefficients/LSH rule, Jaccard/union-find,
  validation root exclusion, independent test sealer, complete R0.0 validator,
  training, and held-out evaluation remain open. `training_authority=false`;
  R0.0 remains **OPEN**.

## 2026-09-26 — Devign exact-clone label-conflict preflight checkpoint 30

- Continued in the local Desktop worktree from clean source HEAD `4d2e809`;
  the old OneDrive checkout and official held-out test split were not touched.
  Tests were first RED because the new `devign_clone` module was absent. An
  initial test invocation without `PYTHONPATH=src` failed at collection for
  the environment, not the implementation; the corrected invocation exposed
  the intended missing-module RED. A later PowerShell `test_alc_r0_*.py`
  wildcard launcher did not expand and ran no tests; the actual regression
  used `pytest tests -k alc_r0`.
- Implemented fixture-tested development-only 256-permutation affine-32
  MinHash (seed `20260916`), 0.85 soft-threshold LSH candidate bands
  `13 x 19`, exact five-shingle Jaccard `>= 0.90` confirmation, transitive
  lexicographic union-find roots, conflicting-label fail-closed behavior,
  one member per split, and train-root exclusion from validation. The fixed
  coefficient digest is
  `08ed1ca23b267dc9f06267b318f2e95990c72c0f2b06480647afcd79aeaf9e42`.
  The adversarial fixtures include exact clones, formatting-only clones,
  conflicting labels, transitive A-near-B-near-C, and exact 0.90 boundary.
- The first full 24,586-row development-only filter stopped on a conflicting
  label root. Independent exact normalized-SHA-256 audit then found **54**
  duplicate groups and **54** opposite-label conflicts (108 members) among
  24,532 exact groups. Direct byte comparison confirmed one pair,
  `devign:00000817` and `devign:00015755`, has identical normalized UTF-8
  but labels `False` and `True`. This is a source-label contradiction, not an
  LSH false positive or threshold decision. No source code text was committed.
- Canonical non-authorizing receipt
  `results/alc_r0_devign_exact_conflict_preflight_20260926.json` regenerated
  byte-identically from only the pinned train/validation source; SHA-256
  `6741671a84c511179e666b21ef89e80fcc11607b10829b9bbb86c82e0675f0d9`.
  Its conflict-ledger commitment is
  `31ba36366cb0a11d0d56c77a8a6800a62587d2d9cc8a6a6f5caf0a06c3557390`.
  The negative result and next decision boundary are documented in
  `docs/superpowers/plans/2026-09-26-alc-r0-devign-exact-conflict-addendum.md`.
- Final focused clone tests passed **7/7**; scoped Ruff check/format and
  Pyright 1.1.413 passed with zero errors/warnings. Final Windows ALC-R0
  regression after the last source/test edit passed **305 tests, 0 failures,
  0 errors, 7 skipped, exit 0**, JUnit time `139.270 s`; XML SHA-256
  `16f7dd454abf014f16d8e87e41ce7746c8f529e4daac2d1b96394b6353c75fc7`.
  The earlier 304-test run was superseded by this final-byte run.
- **Gate outcome:** the frozen plan explicitly says any conflicting-label
  clone root fails R0.0. This Devign development source therefore fails data
  qualification before training; the full-corpus LSH filter, independent test
  sealer, training, and held-out evaluation were not run. This does not
  falsify the capsule hypothesis or authorize a revised dataset. An explicit
  preregistration amendment with an untouched confirmatory split is required
  before trying another data protocol. `training_authority=false`; no ALC-0
  claim is opened.

## 2026-09-28 — PrimeVul development-source candidate checkpoint 31

- Continued from local Desktop worktree clean HEAD `447d8d8`; did not change
  the OneDrive checkout, frozen Devign plan, or any official held-out test
  content. The prior Devign exact-label contradiction remains a failed data
  qualification gate, not a neural-capability result. Investigated the
  authors' original PrimeVul release as a possible replacement code task,
  acquiring **only** its train and validation JSONL files into a separate
  local research directory outside the repository. Their source folder ID is
  `19iLaNDS0z99N8kB_jBRTmDLehwZBolMY`; train file ID
  `1qRO_Qdy7KXcZbJJAu5J3VZWkRVvT4Kbu`, validation file ID
  `1CMQ185Ww_bsBWGbJe4sZW0vzceWnmNE7`. The test file was not downloaded
  or inspected. Dataset-specific license scope is not yet resolved.
- Added a development-only verifier with pinned raw SHA-256/byte length,
  JSONL/UTF-8/field/label/source-ID validation, strict two-file directory
  boundary, and exact normalized-code conflict audit. It emits a canonical
  metadata-only receipt, explicitly `training_authority=false`,
  `held_out_data_present=false`, and `lsh_executed=false`. RED began with the
  absent module; two subsequent focused failures were fixture mistakes
  (expected one positive where the fixture had two, and an accidental JSON
  key mutation instead of code mutation), corrected without weakening source
  validation. Final focused tests passed **7/7**, including extra test-file,
  same-length byte mutation, malformed JSON/UTF-8/label, and cross-split ID
  rejection.
- Real development-only source: train **184,427** rows/**5,574** positive,
  raw SHA-256 `9fea452f1b7c7ffafb28d6131789f722ad820c1032d3bcd90b7fc17da3d9b117`;
  validation **25,430** rows/**699** positive, raw SHA-256
  `56b91474fb7d75b313013766e0f5d1d8150c98e70961cf2b26df93875e87fb27`.
  Across 209,857 source IDs, the verifier found **201,484** exact normalized
  groups, **8,338** duplicate groups, **1,237** groups spanning
  train/validation, and **0** exact opposite-label groups. CLI regeneration
  matched `results/alc_r0_primevul_development_candidate_20260926.json`
  byte-for-byte; receipt SHA-256
  `9c7af77f1bedd6b73729df6d3907c510cc67379c8f6a74a52705b7abb191153c`.
  No raw code or dataset rows were committed.
- Scoped Ruff check/format passed; Pyright 1.1.413 with the pinned research
  interpreter reported **0 errors/warnings/informations**. Final Windows
  ALC-R0 regression after the last source/test edit passed **312 tests,
  0 failures, 0 errors, 7 skipped, exit 0**, JUnit time `182.817 s`;
  `results/alc_r0_primevul_candidate_regression_20260928.xml` SHA-256
  `b6e856cb852960a4f44d3d1c8f0cdc6c0f7948811a44b94c93ccaaa3c5d7ea9b`.
  Exact LF checkout rules were added for both canonical evidence files.
- **Gate remains open:** PrimeVul is a non-authorizing *candidate*, not a
  silent substitute for the frozen Devign task. The full development LSH and
  exact-Jaccard connected-component audit, retained-validation counts,
  dataset-specific license review, explicit preregistration amendment,
  independent test sealer, R0.0 validator, training, and confirmatory
  evaluation remain undone. The decision boundary is documented in
  `docs/superpowers/plans/2026-09-28-alc-r0-primevul-candidate-note.md`.
  ALC-0 remains **OPEN**.

## 2026-09-28 — PrimeVul near-clone negative witness checkpoint 32

- Continued from clean, pushed local-Desktop source HEAD `8224185` with the
  frozen Devign/PrimeVul receipts intact. No official held-out test file was
  downloaded, read, or included in the worktree. The PrimeVul exact-code
  preflight had zero conflicting groups but explicitly had not run LSH.
- Measured the existing frozen MinHash/LSH implementation on development-only
  PrimeVul samples before attempting a full 209,857-row run: the first 200
  rows took 1.507 s for signatures (132.68 rows/s; shingle range 38–4,377);
  a 2,000-row clone-filter pilot took 18.271 s, with 205 candidate pairs,
  165 near joins, and no conflict. A 10,000-row train-only pilot took
  47.115 s and failed on a conflicting-label clone root. These are resource
  and counterexample diagnostics, **not** a full-corpus performance or
  clone-filtering PASS. Host physical RAM was approximately 16 GiB.
- Isolated a direct train/train witness: `primevul:7` has label 1 and
  `primevul:11213` has label 0. Their normalized SHA-256 values are distinct
  (`1b432cf2eb9bea6865e9edda1ee2adc7da376f62c999396a95a884ae842d65c5`
  and `98d84b9c9bb9ccad14d9d33fb16cdd7cf25eba1579c3039e10f7855869017629`).
  Under the frozen five-token-shingle rule, intersection/union is
  **339/358** (greater than 0.90), and the deterministic 256-permutation
  MinHash signatures share **four** of the 13 LSH bands. This is an
  exact-Jaccard-confirmed *near* clone with opposite labels, not an
  exact-hash duplicate or an LSH false positive.
- Added a metadata-only, development-only witness verifier that revalidates
  both pinned source files, locates the pair, recomputes normalization,
  shingles, MinHash/bands and exact Jaccard, and refuses same-label,
  below-threshold, missing, exact-conflict, or mutated-source witnesses.
  TDD began RED with the absent module; final focused PrimeVul tests passed
  **12/12**. The canonical receipt
  `results/alc_r0_primevul_near_conflict_witness_20260928.json` regenerated
  byte-identically, SHA-256
  `4af94b174d6596494ee7aa5b2e9b91dd5f5932dd82b3e590cfc7aa1d360e0fc0`.
  No raw code text was committed.
- Scoped Ruff check/format and Pyright 1.1.413 passed with zero reported
  issues. Final Windows ALC-R0 regression passed **317 tests, 0 failures,
  0 errors, 7 skipped, exit 0**, JUnit time `147.263 s`;
  `results/alc_r0_primevul_near_conflict_regression_20260928.xml` SHA-256
  `13eadc95bc928d1ae23c4cc35d5a7f9115e5d303bdd5573ad6a6fc985de3564c`.
- **Gate outcome:** under the unchanged frozen rule, any connected clone root
  containing opposite labels fails R0.0. One verified violating edge is
  sufficient; a full-corpus LSH run was **not** performed or claimed.
  Original PrimeVul therefore also fails data qualification. This is a
  dataset/protocol failure, not a falsification of the neural-capsule
  hypothesis. PrimeVul is not silently promoted, `training_authority=false`,
  and ALC-0 remains **OPEN**. The negative result and alternative-source/
  preregistration decision boundary are documented in
  `docs/superpowers/plans/2026-09-28-alc-r0-primevul-candidate-note.md`.

## 2026-09-28 — PrimeVul paired-development source and recovery design checkpoint 33

- Continued from clean/pushed local Desktop source HEAD `6607879` after both
  Devign and original PrimeVul had failed the **unchanged** conflicting-label
  clone-root rule. Reviewed the PrimeVul authors' paper/repository: closely
  related vulnerable/patched code and pair-wise evaluation are an intended
  challenge, so the PrimeVul failure is an evaluation-design/data-protocol
  mismatch, not evidence that all such opposite-label pairs are mislabeled.
  The witness `primevul:7`/`primevul:11213` was **not** asserted to be one of
  the authors' adjacent pairs; its two records have different commits.
- Inspected only the authors' original-release folder metadata and acquired
  **train/validation paired files only**, in a separate local research
  directory outside Git. The paired test file was listed by name/ID but was
  **not downloaded or read**, nor was the full test file. The first `gdown`
  folder-list call used an unsupported argument and exited before acquisition;
  the corrected metadata-only listing and two explicit-ID downloads succeeded.
  Pair file IDs are train `1CYE_AZdZTIHPepOIxmPNZtMPdwB6cEt1` and
  validation `1UBoDzBD9tXAieRlXYjjB-2HpPf9I83mg`.
- Pinned paired train at **52,076,348 bytes**, SHA-256
  `22d2f27ffda164d7de81f870f6a4907c66df2338f6a9fd01ee2300d7fb34f965`;
  paired validation at **5,867,872 bytes**, SHA-256
  `33b18631d7b5c075ee143527176fddf2180648901ed40952553d99f744c6c74f`.
  Added a fail-closed development-only verifier for exact file set/hashes,
  strict JSONL, ordered opposite-label same-commit/project pair edges,
  repeated-ID consistency, and full-row equality against the already pinned
  original development source. Every paired row matched its full-source row.
- The train paired file has **4,354 edges** but **8,703 unique source IDs**:
  4,344 pair-graph components of size 2 and five of size 3. Validation has
  **562 edges** but **1,120 unique IDs**: 557 components of size 2 and one
  of size 6. Thus pair edges cannot be treated as independent bootstrap
  observations. These are author-pair **graph** counts only; the full
  pair-plus-near-clone dependency graph has not been computed.
- TDD started RED at the missing `primevul_pairs_source` module. Focused
  PrimeVul tests passed **18/18** after implementation, covering malformed
  duplicate keys, wrong labels/code, repeated-ID inconsistency, extra test
  file, and source mutation. Ruff check/format and Pyright 1.1.413 passed
  with zero reported issues. The first hand-copied receipt omitted
  `validation_paired_sha256`; byte-for-byte regeneration detected it and the
  artifact was corrected before commitment. Canonical receipt
  `results/alc_r0_primevul_pairs_development_20260928.json` now regenerates
  identically, SHA-256
  `93d1c1dea9c30b6b4259830f158e2060797c16ac9f5a6e7b05f236fe943187e2`.
  No raw function/code text was committed.
- Final Windows ALC-R0 regression passed **323 tests, 0 failures, 0 errors,
  7 skipped, exit 0**, JUnit time `189.085 s`;
  `results/alc_r0_primevul_pairs_regression_20260928.xml` SHA-256
  `e281dbf003fd300fe1ffa2026a60254a0d6796659d9fbc382edcaa2c24c33950`.
- The comparative decision record
  `docs/superpowers/plans/2026-09-28-alc-r0-code-task-recovery-decision.md`
  rejects training despite the old fail gate and rejects discarding/relabeling
  hard mixed-label components. It selects a **pair/clone-component-aware
  PrimeVul protocol for next design work**, with another dataset/task reserved
  as fallback. This is **not** a frozen preregistration amendment: dataset
  license scope, full graph, explicit statistical/sealer changes, machine
  validator, environment gates, and untouched confirmatory split remain open.
  Frozen numeric P1–P14 floors are not lowered. `training_authority=false`;
  ALC-0 remains **OPEN**.

## 2026-09-28 — Pair/clone dependency reference and bounded pilot checkpoint 34

- Continued from clean/pushed local Desktop HEAD `d235cfe` with both negative
  data-source outcomes and the non-authorizing recovery decision intact.
  No official full or paired test split was downloaded/read. The controlling
  2026-09-20 frozen plan remains unchanged; no v2 preregistration amendment
  or training authority was created.
- Implemented a **reference-only** pair-plus-clone development graph with the
  frozen normalization, exact normalized SHA-256, 256-permutation MinHash,
  13-by-19 LSH candidate bands, exact five-shingle Jaccard >= 0.90, and
  lexicographically minimal union-find roots. Explicit author pair edges
  connect repeated source IDs transitively. Different-code opposite-label
  near clones retain both labeled observations within one dependency root;
  identical normalized code with opposite labels still fails. One
  representative per identical normalized code/label is kept within a split;
  any validation component connected to train is removed in full. Inputs
  with malformed IDs/edges, cross-split pair edges, or over **4,096** rows
  fail closed. This bound is a reference resource limit, **not** a relaxed
  scientific acceptance threshold or a full-corpus implementation.
- TDD began RED at the absent graph module. Final focused graph+pilot tests
  passed **17/17** across mixed-label near clones, exact conflicts,
  transitive shared pair endpoints, full-component validation exclusion,
  duplicate representative selection, canonical IDs, malformed edges, and
  resource bound. Ruff check/format and Pyright 1.1.413 reported no issues.
- Added a reproducible non-authorizing pilot CLI that first re-verifies both
  pinned development source directories, then selects the **first 50** train
  pair edges by author file order, not by an observed metric. On those 100
  unique source IDs it found **49** dependency components, **40** LSH
  candidate pairs, **29** exact-Jaccard-confirmed near edges, **25** pair
  edges that caused additional unions, and **0** exact duplicate joins.
  The metadata-only source/edge/root-committed receipt
  `results/alc_r0_primevul_pair_clone_pilot50_20260928.json` regenerated
  byte-identically, SHA-256
  `90e5cb18add2eef4f04da51de5d919502dac39765aa7c2509ff9d2b93ace9c60`.
  This is a bounded integration pilot, **not** a representative full-data
  estimate or a qualified training split. No raw code was committed.
- Final Windows ALC-R0 regression after the last source/test edit passed
  **340 tests, 0 failures, 0 errors, 7 skipped, exit 0**, JUnit time
  `182.962 s`; `results/alc_r0_pair_clone_reference_regression_20260928.xml`
  SHA-256 `dd07b8c290ad3ea2a6b9b5977ef3e1388f7e2220c002b5a9ea8589ab49c23b35`.
  LF checkout rules were added for both byte-bound evidence files.
- **Next gate:** implement a resource-bounded full 209,857-row graph and prove
  parity against this reference on adversarial/sampled development fixtures;
  then measure retained validation support. The pair-aware source/protocol
  still needs a versioned preregistration amendment, license review,
  independent sealer, R0.0 validator, and untouched confirmatory evaluation.
  `training_authority=false`; ALC-0 remains **OPEN**.

## 2026-09-28 — Scalable pair/clone graph preflight checkpoint 35

- Continued from pushed local Desktop commit `a1bd8d1`. The new scalable
  development graph has the same frozen normalization, exact hash, 256-permutation
  MinHash, 13-by-19 LSH, exact five-shingle Jaccard >= 0.90, lexical root,
  pair-edge, duplicate-representative, and train/validation exclusion rules
  as the bounded oracle. It uses compact bucket indices and a 512-row shingle
  cache rather than retaining all shingle sets. Its explicit 250,000-row and
  10,000,000-candidate caps are resource guards; they do not relax the
  scientific threshold. No full-data graph has been run yet.
- RED was observed at the absent scalable module. GREEN parity tests compare
  the complete result object against the independent 4,096-row oracle for
  cross-split overlap, author pair edges, duplicates, and repeated near-clone
  candidates; exact conflicts and candidate-budget violations fail closed.
  A 4,097-row exact-duplicate fixture passed beyond the oracle's row bound.
  Focused tests **5/5**, Ruff check/format clean, Pyright 1.1.413 0 errors.
- Windows ALC-R0 regression after the final source/test edit: process exit 0;
  JUnit **345 tests, 0 failures, 0 errors, 7 skipped**, time `180.936 s`.
  `results/alc_r0_pair_clone_scalable_regression_20260928.xml` SHA-256
  `d704afb8244d10ba62db9a1d88e86fd7e06950b839a4986d8bc032a95c19ea67`.
- **Next gate:** bind the pinned verified development files and pair edges to
  the backend, prove stronger parity, execute all 209,857 development rows,
  measure retained validation support and resource fit, and record graph
  commitments. No paired/full test source was read. This preflight neither
  freezes a v2 protocol nor authorizes training: `training_authority=false`;
  ALC-0 remains **OPEN**.

## 2026-09-28 — Full-development graph runner preflight checkpoint 36

- Continued from clean/pushed local Desktop `95ae96d`. Added a runner that
  invokes the pinned development-source and author-pair verifiers, then
  replays train/validation and pair-file SHA-256 while loading only their
  development rows/edges. It passes the verified 209,857-row input shape to
  the scalable graph and emits a canonical metadata-only receipt containing
  input/retained counts, component-class support, exact/near/pair joins, and
  source/edge/root/retained-ID commitments. Held-out test files remain outside
  this path. It prints periodic graph progress without touching semantics.
- RED at absent runner module preceded GREEN fixture integration. Focused
  scalable+runner tests **8/8** cover source binding, metadata-only receipt,
  progress, and mutation rejection. Ruff check/format clean; Pyright 1.1.413
  0 errors. Windows ALC-R0 regression after final source/test edit: exit 0;
  JUnit **348 tests, 0 failures, 0 errors, 7 skipped**, time `152.863 s`.
  `results/alc_r0_pair_clone_full_runner_regression_20260928.xml` SHA-256
  `a9748af607ff3a0e5a6b598b3ecab42bdc3aecd8357168d1f87b3535ada9459c`.
- **Not yet run:** the pinned full development graph and its resource fit. A
  passing fixture is not the full-data evidence. Next: freeze this code in a
  clean commit, run the real 209,857-row development graph, inspect process
  exit/receipt/resource use, then review retained validation support. No v2
  preregistration amendment, training, or confirmatory test access has occurred.
  `training_authority=false`; ALC-0 remains **OPEN**.

## 2026-09-28 — PrimeVul license-scope preliminary review checkpoint 37

- While clean commit `101c302` ran the pinned full development graph, checked
  the authors' current repository, root MIT LICENSE, and original-release README
  (https://github.com/DLVulDet/PrimeVul). The repository license text covers
  software/associated documentation; the README links dataset bytes externally
  and says the dataset combines/reconstructs earlier sources. An explicit
  separate grant for the external JSONL bytes was not identified in these
  primary pages. This is a **scope uncertainty**, not a claim of prohibition.
- The recovery decision now keeps dataset/underlying-code redistribution and
  commercial-training rights unresolved pending release/upstream license or
  author-rights review. Local development-only graph analysis does not settle
  that question. No raw code or held-out test data was committed/read; no
  license or training PASS has been asserted. `training_authority=false`.

## 2026-09-28 — Mixed-component scalable/reference parity checkpoint 38

- Continued while the full pinned development graph from code commit `101c302`
  remained live. Added a deterministic 72-record adversarial development
  fixture combining 1/0 author pair edges, distinct-code near clones, exact
  same-label duplicates, outliers, and train/validation overlap. The entire
  scalable result object matched the bounded reference result; exact joins,
  near joins, and validation overlap removal were all nonzero. This proves
  another bounded parity case, **not** full-source parity or full-data PASS.
- Focused scalable tests **7/7** passed after formatter-only cleanup; Ruff
  check/format and Pyright 1.1.413 clean. The full Windows ALC-R0 regression
  before that formatter-only change exited 0 with JUnit **349 tests, 0
  failures, 0 errors, 7 skipped**, time `247.670 s`.
  `results/alc_r0_pair_clone_mixed_parity_regression_20260928.xml` SHA-256
  `01a827d09de4639eba2c05322a0fec2a29969f22cb8fba4fd430732f8e0bcfe2`.
- The separate real-data process was observed at **128,001 / 209,857** rows
  with 9,982 LSH candidate pairs, live worker PID 23928, and observed peak
  working set ~1.35 GB. It had no terminal receipt/exit yet. `training_authority`
  remains false; no held-out test data was accessed.

## 2026-09-28 — Pinned full PrimeVul development graph result checkpoint 39

- Frozen graph-source commit `101c3026736c62ce0a16bc7d80fd4bc1a198c153`
  ran the complete authors' pinned train+validation original release and their
  paired development files; the held-out test files were absent/not read.
  Detached wrapper/worker status was rechecked live, and the terminal
  `results/alc_r0_primevul_full_graph_101c302_20260928.exit.log` records
  `python_exit_code=0`. The canonical JSON stdout and 206 monotone stderr
  progress events were independently parsed; final progress was
  **209,857/209,857** with **19,874** LSH candidate pairs, matching receipt.
- Receipt input: **184,427** train rows, **25,430** validation rows, **4,916**
  author pair edges; source scope `pinned-original-development`; pair-source
  receipt SHA-256 `e3d92be86e8f4e44c4db7c5afe3cc47ab3beeec89d5540c34dbcef4e562cbd5f`.
  Graph: **8,373** exact joins, **13,229** exact-Jaccard-confirmed near joins,
  **2,206** additional pair joins; **166,525** train components. Retained
  **177,291** train rows and **22,772** validation rows in **22,157**
  validation components; **2,658** validation rows in **2,524** train-overlap
  roots were excluded. Retained validation has **552** components containing
  positive examples and **22,087** containing negative examples; mixed-label
  components contribute to both counts, so those figures are not additive.
- The receipt binds pair edges, component roots, and retained ID ledgers by
  SHA-256 and explicitly has `training_authority=false` and
  `held_out_data_present=false`. Raw stdout SHA-256
  `e54c729d9c7d3ccaa3f50efcb6edcfc492c880131f0c5cf61df1db9714533243`;
  raw stderr SHA-256
  `e3dd4fd47dff466370bec4ade4ed1910e57993e964612b54ebbd8352113b52b2`;
  exit log SHA-256
  `56b9a9582f37a38a8b037c8285a27b40b509df1bc0bc54e3adb84a65d10fa790`.
- Approximate elapsed wall time from wrapper start to exit-log write was
  **14m24s**. Sampled Windows process reports observed a peak working set of
  about **1.35 GB** before termination; no continuous peak capture was made,
  so this is not a proven all-time RSS upper bound. Free C: space after the run
  was about **43.1 GB**. This evidence qualifies a development graph result,
  **not** confirmatory test support, dataset rights, preregistration, training,
  neural capability, or ALC-0. Next: independent graph/receipt audit,
  reproducibility check, v2 protocol/license/sealer/R0.0 gates. ALC-0 OPEN.

## 2026-09-28 — Family-B pair-aware v2 protocol draft checkpoint 40

- Read frozen 2026-09-20 ALC-R0 plan sections 4.2, 8.1, 8.4, 8.6, P1–P14,
  and R0.0 alongside the negative Devign/PrimeVul development outcomes.
  Drafted `docs/superpowers/plans/2026-09-28-alc-r0-primevul-v2-amendment-draft.md`
  as **non-authorizing**, with exact proposed family-B-only source/graph change,
  mixed-label observation vote, component-cluster bootstrap, whole-component
  sealer exclusion, component/class support rule, unchanged numeric floors,
  and independent review/rights/sealer/validator prerequisites.
- Development evidence of 22,157 validation components, 552 positive-containing
  and 22,087 negative-containing implies 482 mixed-label components by
  inclusion-exclusion. The draft makes this counting rule explicit before any
  held-out test access. It does **not** modify the frozen v1 plan, inspect test
  data, create a v2 machine preregistration, or grant training authority.
  A byte-identical second full-development run was live when drafted; its
  terminal outcome is a separate pending checkpoint. ALC-0 remains OPEN.

## 2026-09-28 — Component-vote arithmetic reference checkpoint 41

- Added a non-authorizing, exact-Fraction reference for proposed PrimeVul
  component-class support and fixed-label macro-F1. It keeps one vote per
  distinct normalized-code/label observation, rejects an identical code in
  multiple roots or with opposite labels, and rejects duplicate prediction
  disagreement. A bootstrap draw repeats **all** observations of each sampled
  component, so mixed labels cannot be sampled independently.
- RED was observed at the absent module; focused hand fixtures passed **7/7**.
  The mixed-root fixture counts 3 total roots, 1 positive-containing, 3
  negative-containing, and 1 mixed; exact duplicate contributes no vote.
  Point macro-F1 is exactly `11/15`; drawing roots `(A,A,C)` yields exactly
  5 scored observations and macro-F1 `1`. Ruff check/format and Pyright
  1.1.413 passed. Windows ALC-R0 regression exited 0; JUnit **356 tests,
  0 failures, 0 errors, 7 skipped**, time `231.775 s`;
  `results/alc_r0_primevul_component_metric_regression_20260928.xml`
  SHA-256 `5acecb0b33bf59039c42d4342b0e24ad789d804a9321ba3a4f8b5c8d44e19d34`.
- This validates only arithmetic mechanics. It is not the final evaluator,
  10,000-replicate bootstrap, uncertainty bound, independent sealer, training
  permit, or ALC-0 capability evidence. The second full graph run was still
  live at 193,537 / 209,857 when this checkpoint was prepared. ALC-0 OPEN.

## 2026-09-28 — Full-development graph deterministic replay checkpoint 42

- The second complete PrimeVul development-only graph run terminated with
  `python_exit_code=0`; its parsed canonical receipt again records scope
  `pinned-original-development`, **22,157** retained validation components,
  **482** mixed-label validation components, and `training_authority=false`.
  Its 206 monotone progress events end at **209,857/209,857** rows and
  **19,874** LSH candidate pairs. The held-out test files were not read.
- Raw second-run stdout is byte-identical to the first run. Both stdout
  SHA-256 values are
  `e54c729d9c7d3ccaa3f50efcb6edcfc492c880131f0c5cf61df1db9714533243`.
  Second-run stderr SHA-256 is
  `e3dd4fd47dff466370bec4ade4ed1910e57993e964612b54ebbd8352113b52b2`,
  and exit-log SHA-256 is
  `56b9a9582f37a38a8b037c8285a27b40b509df1bc0bc54e3adb84a65d10fa790`.
  Raw evidence is in
  `results/alc_r0_primevul_full_graph_repeat2_101c302_20260928.*`.
  Source graph code blobs were unchanged from frozen `101c302`; the second
  run began after the first evidence commit. Byte-identical replay proves
  determinism for these inputs/environment, not algorithmic or scientific
  correctness. Independent audit and v2 protocol gates remain open.

## 2026-09-28 — Component-vote reference final regression checkpoint 43

- Added a second distinct, same-label observation within one component to
  the hand fixture. It stays one bootstrap cluster; when that root is drawn
  twice, both observations are repeated and exact macro-F1 is `1/3`.
  Focused tests passed **8/8**. Ruff check/format and Pyright 1.1.413 were
  clean after the implementation; the added test changed no production code.
- After the added test, full Windows ALC-R0 regression exited 0 with JUnit
  **357 tests, 0 failures, 0 errors, 7 skipped**, time `344.907 s`.
  `results/alc_r0_primevul_component_metric_regression_v2_20260928.xml`
  SHA-256 is
  `34670b0cfea38b1e1f9b529d418a776de913fb3b39ad806eac696b72df112088`.
  The earlier 356-test XML is retained as the preceding checkpoint, not
  substituted for this final run. This is reference arithmetic evidence only;
  no final 10,000-replicate evaluator, sealer, rights review, training, or
  ALC-0 completion is implied. ALC-0 OPEN.

## 2026-09-28 — Pair/clone structural audit harness checkpoint 44

- Added `primevul_pair_clone_audit.py` as an independent *structural* checker
  over a graph result: every input ID has one root; each root is its group's
  lexicographically minimal ID; identical normalized-code hashes stay in one
  same-label root; explicit author pairs stay in one component; validation
  components touching train are fully excluded; retained per-root/code/label
  representatives and reported overlap/exact/component counts agree with
  independently recomputed expectations. It emits only metadata and hashes.
- TDD RED: the absent audit module failed import/collection. GREEN: focused
  **7/7** tests passed on both bounded reference and scalable backends and on
  tampered root, representative, pair, overlap, and exact-count examples.
  Ruff check/format passed; Pyright 1.1.413 reported 0 errors. Windows ALC-R0
  regression exited 0 with JUnit **364 tests, 0 failures, 0 errors, 7 skipped**,
  time `208.841 s`; XML SHA-256
  `ba308afb24dc045a7ba9dc67d57a240a0632ffa25bc3a645ca4c6e1185f57377`
  at `results/alc_r0_primevul_structural_audit_regression_20260928.xml`.
- This checker has **not yet been applied to the full 209,857-row result** and
  does not independently discover or refute omitted LSH near-clone edges.
  Deterministic graph replay and structural audit are data/protocol evidence,
  **not deterministic model output or proof of persistent neural learning**.
  Model training, sealed held-out evaluation, independent scientific review,
  and ALC-0 remain OPEN.

## 2026-09-28 — Receipt-bound full-graph structural audit runner checkpoint 45

- Added `primevul_structural_audit_run.py` to verify the same pinned
  development-only source and pair bytes, rebuild the graph, run the separate
  structural checker, and compare its root/retained-ID ledger hashes plus
  every prior graph count with a supplied canonical prior receipt. The CLI
  requires that receipt's expected raw SHA-256 before any data processing;
  output is metadata-only and never authorizes training or opens test files.
- Tests were written first. The initial ordinary pytest RED attempt was
  interrupted by Windows `0x8007000e` during Torch import under measured
  ~115 MiB free RAM, so it was **not** a meaningful code-failure RED. After
  memory recovered, the same focused fixture tests passed **2/2** under
  standard pytest (and also 2/2 under a low-memory import-isolated run).
  They cover a matching prior receipt and a tampered ledger receipt.
  Ruff check/format and Pyright 1.1.413 (0 errors) passed. Full Windows
  ALC-R0 regression exited 0: JUnit **366 tests, 0 failures, 0 errors,
  7 skipped**, time `224.805 s`; XML SHA-256
  `cb419f815de06a0e07fa47729852544233775d85598d03a1f813528d592059ca`
  at `results/alc_r0_primevul_structural_audit_run_regression_20260928.xml`.
- This checkpoint freezes a fixture-validated runner, **not** a real-corpus
  audit result. Real 209,857-row execution must follow on the frozen commit;
  omitted near-clone discovery, scientific review, rights, sealer, and neural
  learning gates remain open. ALC-0 OPEN.

## 2026-09-28 — Full PrimeVul development structural audit result checkpoint 46

- Frozen audit-runner code commit `323e1ea5c7e902e331e8fe1dda588523d8f83f0e`
  read only the pinned original train/validation and paired-development files.
  It used a low-memory Python launch that skipped unused top-level ALUCLU and
  ALC-R0 package initializers (not the graph/audit modules); this prevented
  an unrelated Torch import while preserving the graph's exact code path.
  The process terminated with **exit code 0**. Raw evidence:
  `results/alc_r0_primevul_structural_audit_full_323e1ea_20260928.stdout.log`
  SHA-256 `a55ea520bfa43a055639f2e06e9b9292a41e56e74c25e01c71cb0ee59dcc6d51`;
  corresponding stderr SHA-256
  `f377b197ad54b7f8bd782011a16f5f74f22077aa91af01450fe11cfd21597925`.
- Independently parsed the canonical JSON output: status
  `full-graph-structural-audit-clear-non-authorizing`, source scope
  `pinned-original-development`, `training_authority=false`, and
  `held_out_data_present=false`. It checked **209,857** rows, **4,916** pair
  edges, **8,373** exact duplicate rows, **177,291** retained train rows,
  **22,772** retained validation rows, and **2,658** validation rows removed
  for train overlap. Its prior-receipt SHA, root ledger SHA, retained-train-ID
  SHA, and retained-validation-ID SHA match the committed first full-run
  receipt. All **206** progress events are monotone, with no extra stderr
  lines; terminal progress is **209,857/209,857** and **19,874** candidates.
- This establishes the checked structural invariants on the full development
  corpus, not independent discovery of all potential near-clone edges, rights
  clearance, sealed-test support, a frozen v2 amendment, model training, or
  persistent neural learning. Independent code/science review and all R0.0
  blocking gates remain open. ALC-0 OPEN.

## 2026-09-29 — Frozen-host synthetic capsule trainability checkpoint 47

- Code commit `642bdc2707e3e79272fe943dd420a9e307bf9aca` adds a
  **non-authorizing synthetic mechanism diagnostic** on the pinned, locally
  verified SmolLM2-135M CUDA/BF16 host. The base stays frozen/eval; only a
  `ResearchCapsuleV0` at ports `(14, 29)`, rank 8, initialization seed
  `20260916`, receives 40 AdamW updates (learning rate `3e-4`, zero weight
  decay, global gradient clipping 1.0). One fixed synthetic token sequence
  `[2,3,5,7,11,13,17,19]` predicts fixed token ID `23`. This uses no
  Banking77, PrimeVul, WikiText, LAMBADA, or held-out samples.
- The final test measured synthetic cross-entropy **9.252828598022461 ->
  6.193796157836914**. After serialization to canonical manifest plus
  SafeTensors, both in-process and a separate fresh Python process produced
  the trained logits byte-identically. Detach restored baseline logits
  exactly. The canonical full base-state SHA-256 before training, after
  training, and in the fresh process was
  `ce7e8dd6a97ac4cc56bf4f1e38625817386e27af58f1ed63377741f7f2aab1ba`.
  The diagnostic output explicitly has `training_authority=false` and
  `held_out_data_present=false`.
- Initial attempts exposed setup-only issues: global `py -3.13` lacked test
  packages, then pytest collection lacked `PYTHONPATH=src`; neither was a
  model or code failure. An initial passing JUnit run used `record_property`
  and emitted a pytest xunit2 compatibility warning. That reporting choice
  was removed, along with an unnecessary global RNG seed mutation, before
  the final suite. Earlier passing XMLs are retained as intermediate evidence,
  not substituted for the final source state: focused v1/v2 were each 1/1
  (SHA-256 `727de856e20d34c395df6e467f6ec26e07a9330228d16e984ba778326a4b2e4b`
  and `976b05a8bae3de530b7d8c5d8bea0af9866db0b1f961b5d5964c05b91a78194c`),
  and the prior regression was 367 tests, 0 failures/errors, 7 skipped
  (SHA-256 `aa3e84736c9e2fbcc47fb532472abb556049761d689ad990ffda1dff70bc1521`).
- On the final source state, Ruff check/format and Pyright 1.1.413 passed
  (0 errors/warnings). The Windows ALC-R0 regression exited **0** with JUnit
  **367 tests, 0 failures, 0 errors, 7 skipped**, time `174.004 s`. Final XML
  `results/alc_r0_synthetic_trainability_final_regression_20260928.xml`
  SHA-256 is
  `608c97d6cc6a245f25f95f7ece5ed5e0c74f6141e0bc31457e7520d9e57fefce`;
  its captured stdout contains the numeric loss and non-authorizing status.
- This proves a bounded capsule can be optimized and persist its effect on
  **the same synthetic training prompt** on this host. It does **not** prove
  held-out generalization, learning of either required real-data family,
  longitudinal learning, portability, or ALC-0. R0.0 development-artifact
  and sealed-shard receipts, independent scientific/data review, formal
  200-step resource pilots, the full preregistered development grid, and
  held-out confirmation remain open. No real target-data training was run.

## 2026-09-29 — Independent near-edge audit implementation checkpoint 48

- Code commit `0235af6bf2eda624a42f1420261e4d1ac2d07a48` adds a separate
  development-only 256-permutation MinHash, 13-by-19-band LSH candidate,
  and exact five-shingle Jaccard >= 0.90 edge rediscovery pass. It does not
  call the graph builder's MinHash, band, candidate, Jaccard, or union
  functions; it **does** share the frozen code normalization/tokenization
  contract. Every independently found near edge must land in one reported
  component, and the independently counted candidates/near edges must match
  the graph receipt. It emits an ordered near-edge ledger hash, no source text,
  and `training_authority=false`.
- TDD RED: the new test module could not import the absent auditor. GREEN:
  focused **10/10** tests passed after implementation. These include a scalar
  MinHash arithmetic check, a near clone plus exact duplicate, a missing
  component join, wrong candidate/near counts, a candidate resource cap, and
  a prior-receipt-bound runner fixture. Ruff check/format and Pyright 1.1.413
  passed with 0 errors/warnings. Windows ALC-R0 regression exited **0**:
  JUnit **375 tests, 0 failures, 0 errors, 7 skipped**, time `303.531 s`.
  `results/alc_r0_near_edge_audit_regression_20260929.xml` SHA-256 is
  `6f2baed09ca947e99a149785990af969c3be8da0d2d0715296df0db6ade65c1c`.
- This is **fixture and regression evidence only**. The new independent pass
  has not yet traversed all 209,857 pinned PrimeVul development rows; do not
  infer a full-corpus near-edge audit or R0.0 PASS. The only accessible source
  files are the pinned train/validation and their paired-development files;
  no held-out test file is present or read. Source rights, scientific review,
  v2 amendment, independent sealer, and model training remain open. ALC-0 OPEN.

## 2026-09-29 — Full PrimeVul independent near-edge result checkpoint 49

- From frozen code HEAD `322cc738a3c8895be185f525534c090a3abbcb23`
  and a tracked-clean checkout, reran the pinned original PrimeVul
  train/validation plus paired-development files. The prior graph receipt's
  raw SHA-256 was required as
  `e54c729d9c7d3ccaa3f50efcb6edcfc492c880131f0c5cf61df1db9714533243`.
  A low-memory child-process launch omitted only the heavy top-level ALUCLU
  package initializers; the graph, source verifiers, structural checker, and
  independent near-edge auditor code paths were unchanged. The terminal
  `python_exit_code=0` was recorded in
  `results/alc_r0_primevul_near_edge_full_322cc73_20260929.exit.log`.
- Parsed and independently checked the canonical JSON+LF stdout: source scope
  `pinned-original-development`, `training_authority=false`,
  `held_out_data_present=false`; **209,857** source rows, **4,916** author pair
  edges, **8,373** exact duplicate rows, **177,291** retained train rows,
  **22,772** retained validation rows, and **2,658** validation rows removed
  for train overlap. The previous receipt SHA, source-pair receipt SHA,
  component-root ledger SHA, retained-train-ID SHA, and
  retained-validation-ID SHA all match the committed prior full-graph receipt.
- The separate implementation independently rediscovered **19,874** LSH
  candidate pairs and **13,229** exact-Jaccard-confirmed near edges. All
  discovered near edges stayed within the graph's component roots; its
  candidate/edge counts equal the prior graph's counts. Ordered near-edge
  ledger SHA-256 is
  `3ba8af8d535502e31451f67d061f4e82f968f72fe2bfc428366aa9d79096b068`.
  Both graph and independent-audit phases have **206** monotone progress
  events, each ending at **209,857/209,857** and **19,874** candidates;
  stderr has no extra lines. The approximate wrapper wall time was **34 min**
  (01:15:02 to 01:49:02 local). No continuous all-time RAM peak was measured.
- Raw stdout SHA-256 is
  `f19d5131253ce853adad4cdee75da36660e13b2e4bb5dea8138097f78d3526e1`;
  stderr SHA-256 is
  `3a7c6da33a56b74351a5d0e29088aad3cbb95b8cb6075a886d459a848fece478`;
  exit-log SHA-256 is
  `0c86842e0db90458dfda6a814ad055f061ce033213e06f59a5f69386e7e38d97`.
- Rechecked the authors' [README](https://github.com/DLVulDet/PrimeVul/blob/main/README.md)
  and [MIT repository LICENSE](https://github.com/DLVulDet/PrimeVul/blob/main/LICENSE).
  README links the original release and describes model training; the LICENSE
  text describes software and associated documentation. Explicit scope over
  the external Drive JSONL files and third-party embedded source snippets was
  not found in these sources. This is **not** a legal clearance or a basis to
  authorize training. The independent near pass shares normalization and
  tokenization with the graph; code/science review, a frozen v2 amendment,
  rights resolution, sealer/isolation, R0.0 validator, and held-out evidence
  remain open. No target model training or confirmatory evaluation was run.
  ALC-0 OPEN.

## 2026-09-29 — R0.0 committed-source freeze prerequisite checkpoint 50

- Added a read-only `source_checkout` verifier for a future R0.0 freeze
  validator. It requires an absolute repository root; empty Git porcelain
  status with all untracked files and submodule changes visible; no
  `assume-unchanged` or `skip-worktree` index flags; stable full HEAD before
  and after inspection; safe, case-collision-free tracked paths; and supported
  regular/symlink Git blob modes. It computes SHA-256 over RFC 8785 canonical
  records of every committed blob's normalized path, Git mode, exact byte
  length, and content SHA-256. Gitlinks fail closed until a separate submodule
  state contract exists. An expected commit and tree digest must both match
  for `verify_frozen_source_checkout` to return evidence. The module provides
  **no training authority** and is not the full R0.0 validator.
- TDD RED first observed missing module import. After initial GREEN, two new
  negative tests demonstrated that Git `assume-unchanged` and `skip-worktree`
  can conceal changed working bytes from ordinary porcelain status; the
  implementation was tightened to reject those index flags. Final focused
  tests **11/11** passed, including staged/unstaged/untracked rejection,
  wrong commit/digest, same-tree and changed-tree commits, actual initialized
  submodule rejection, and nested-root rejection. Ruff check and format check
  passed on both new files; `git diff --check` passed. No Pyright result is
  claimed for this checkpoint.
- Windows ALC-R0 regression on this source state exited **0**: JUnit **386
  tests, 0 failures, 0 errors, 7 skipped**, time `256.725 s`.
  `results/alc_r0_source_checkout_regression_20260929.xml` SHA-256 is
  `10bda54b817fc767b905cc6f7e64002c657c277b8f7ae272b050ba615e14adc1`.
  This fixture/regression result does not itself inspect the eventual frozen
  research checkout; that live check requires a committed clean source commit
  and a separately frozen expected digest.
- The freeze receipt still needs the exact machine preregistration, full
  cross-artifact validator, independent sealer and isolated held-out state,
  source-rights resolution, and scientific review. No target-data model
  training, held-out evaluation, or ALC-0 capability claim occurred. ALC-0
  remains OPEN.
- After committing the code/tests/regression in
  `595cfaeb9f8d954abba5497745243a3ae4650ebc`, ran
  `inspect_clean_source_checkout(Path.cwd())` from this exact clean local
  worktree. It exited 0 and returned **302** tracked blobs and source-tree
  SHA-256
  `3905e9cdee79abd0b2f9e930afecfac4d13626ce0b21b19cb87d06681d8eea72`.
  A separate call to `verify_frozen_source_checkout` with that explicit commit
  and digest also exited 0 and returned the same evidence. This records a
  live self-consistency smoke for commit `595cfae`, not an independently
  frozen R0.0 receipt or permission to train. This later trajectory commit
  necessarily has a different source-tree digest.

## 2026-09-29 — Family-B candidate prompt and actual-model inference checkpoint 51

- Added `src/aluclu/alc_r0/defect_prompt.py`, a non-authorizing candidate
  reference for the code-defect target shared by the frozen Devign plan and
  proposed PrimeVul replacement. It uses the existing strict UTF-8/NFC/LF
  code normalization, fixed ordered `safe/vulnerable` labels, no-special-token
  candidate IDs with one leading ASCII space, head-ceil/tail-floor code token
  truncation after reserving the answer boundary and longest candidate within
  the 512-token common budget, candidate-only masked loss labels, and one
  complete forward per candidate through the existing reference scorer. The
  live model callback explicitly used `use_cache=False`; the reference API
  relies on callers to preserve that setting. No source or held-out file is
  read by this module. The exact prompt
  format is a **candidate**, not a frozen machine preregistration.
- TDD RED was module-import failure. Focused unit/negative coverage then
  passed **9 tests, 1 optional model test skipped** without a snapshot path.
  Cases include exact normalized prompt bytes, label order and token IDs,
  budget/truncation, prompt/padding masking, separate full candidate forwards,
  invalid/empty code, insufficient budget, and special-token rejection. Ruff
  check and format check passed on both new files.
- Separately supplied the pinned local SmolLM2-135M snapshot under offline
  Hugging Face flags and ran the optional model test. It loaded through
  `load_verified_host`, verified the pinned snapshot, kept all base parameters
  frozen, and obtained finite scores for both full defect-label candidates
  without training. Terminal pytest exit **0**; JUnit **1 test, 0 failures,
  0 errors, 0 skipped**, time `28.508 s`.
  `results/alc_r0_defect_prompt_model_smoke_20260929.xml` SHA-256 is
  `3b3cf719a6e4af25e5662c92c860aabcd9878bf71989d428ca81feb87624ee6e`.
- Windows ALC-R0 regression on the final source state exited **0**: JUnit
  **396 tests, 0 failures, 0 errors, 8 skipped**, time `330.150 s`.
  `results/alc_r0_defect_prompt_regression_20260929.xml` SHA-256 is
  `8ee52c4848b7c10141da5962e26ee48ce74482e5d5be5a0042096df3109dd2a7`.
  The eighth skip is the separately executed snapshot-gated model test.
- This proves only prompt/scoring-path integration and frozen-base inference
  on one synthetic C-function input. It proves no real-data training, target
  accuracy, held-out transfer, persistent neural capability, longitudinal
  learning, or ALC-0 PASS. The family-B source amendment, full-data prompt-ID
  receipt, independent review, source rights, R0.0 freeze, and sealed evaluator
  remain open. `training_authority=false`; ALC-0 OPEN.

## 2026-09-29 — Family-B retained prompt-ID receipt implementation checkpoint 52

- Added a non-authorizing `defect_prompt_receipt` builder and optional
  `--tokenizer-snapshot` branch in the existing PrimeVul structural-audit
  runner. The runner first verifies the pinned local model snapshot and
  train/validation-plus-pair source bytes, rebuilds and structurally audits
  the dependency graph against the prior receipt, then binds only the retained
  ordered train/validation rows to the fixed candidate prompt and tokenizer.
  Metadata includes the verified model inventory hash, label/candidate/prefix/
  suffix token-ID roots, row/label/truncation counts, and separate ordered
  SHA-256 roots over source ID, component root, target, normalized-code hash,
  prompt token IDs, and token counts. Raw function text and individual source
  IDs are not emitted. The caller-supplied inventory hash alone is not proof;
  the CLI recomputes it from the pinned snapshot. No held-out file is read and
  the receipt fixes `training_authority=false`.
- TDD RED: the missing helper module failed import; then two runner fixture
  tests failed on the absent optional arguments. GREEN: **11/11** focused
  helper/runner fixture tests passed. They cover mutation of code, label,
  component root and tokenizer; malformed inventory hash; cross-split root
  overlap; missing option pairing; and absence of raw source in the receipt.
  Ruff check/format and `git diff --check` passed. Windows ALC-R0 regression
  exited **0**: JUnit **404 tests, 0 failures, 0 errors, 8 skipped**, time
  `139.485 s`; XML
  `results/alc_r0_defect_prompt_receipt_regression_20260929.xml` SHA-256
  `fc46dc4c04a5250e7f6ec6b745629e6f0e45a04df347a81f75e1d9ef56a7687e`.
- This is **implementation and fixture/regression evidence only**. A full
  pinned PrimeVul development prompt-ID pass has not yet finished at this
  checkpoint. The exact prompt and family-B source amendment are still
  candidate/non-frozen; rights, independent review, sealer, R0.0 validator,
  and real-data model training remain open. No ALC-0 PASS.

## 2026-09-29 — Full PrimeVul retained prompt-ID result checkpoint 53

- Froze code/tests at clean commit `ef37754` and ran the optional prompt
  branch of `primevul_structural_audit_run` on only the pinned original
  PrimeVul train/validation and paired-development files. The prior full
  graph receipt was required by its exact raw SHA-256
  `e54c729d9c7d3ccaa3f50efcb6edcfc492c880131f0c5cf61df1db9714533243`.
  The local SmolLM2-135M snapshot was rehashed by `verify_model_snapshot`;
  its model inventory root is
  `d9db0058a63990399f26b53ff7480f2e67bd5ef9a0398797fecfeb4ed9732b0e`.
  The command returned terminal `python_exit_code=0` in
  `results/alc_r0_primevul_prompt_full_ef37754_20260929.exit.log`.
- Independently parsed the canonical JSON+LF stdout and checked status
  `full-graph-structural-audit-clear-non-authorizing`, source scope
  `pinned-original-development`, and both `training_authority=false` and
  `held_out_data_present=false`. It traversed **209,857** source rows and
  **4,916** author pair edges, retained **177,291** train and **22,772**
  validation rows, and removed **2,658** validation rows for train overlap.
  Component-root, retained-train-ID, retained-validation-ID, counts, and pair
  source roots matched the prior full-graph receipt. This run did not repeat
  the separate independent near-edge pass; that remains the earlier
  `322cc73` evidence.
- Candidate prompt-ID SHA-256 roots over ordered retained rows are train
  `0204d3eb3fa281ac557d88527d22ea9cbbae346e7e8d3a7af943304426f767c4`
  and validation
  `4bbf8797819d4d583a0ac5ba9d9a775181963be8e57e3c1dc9cc11b838bcd0bc`.
  Candidate token-map root is
  `e67b580805bae7a375285282d7f63057290ce19d0b26fee90a50575a9dea58c1`.
  Fixed prompt budget: prefix **8**, suffix **4**, longest candidate **1**,
  code budget **499**, total **512** tokens. Retained label counts: train
  safe **171,717** / vulnerable **5,574**; validation safe **22,210** /
  vulnerable **562**. Head/tail truncation affected **39,076** retained
  train rows and **4,662** retained validation rows. The longest original
  code-token sequences were **272,858** train and **30,934** validation,
  before deterministic truncation. This is material task information-loss
  risk for later model performance, not a license to alter the frozen rule.
- Stderr contains exactly **206** monotone graph progress events, first
  1/209857 and final **209857/209857** with **19,874** LSH candidates, plus
  one Transformers warning that one original tokenization exceeded the host
  8192-token maximum (`10382 > 8192`). The builder keeps final prompt plus
  candidate within 512 tokens; the warning concerns pre-truncation
  tokenization and is preserved as a warning, not suppressed or presented as
  a model-forward failure. Raw stdout SHA-256 is
  `eac59636e90c4a2f24b5dfc8d27cf1f6a878fe485b5eae4b1741e7841500f1b8`,
  stderr SHA-256
  `33ac93ce1867c81ec43a6c5ef4a4f710ce42bd587015d17ee95ae226747dc7b8b`,
  and exit-log SHA-256
  `56b9a9582f37a38a8b037c8285a27b40b509df1bc0bc54e3adb84a65d10fa790`.
  Approximate wall time was **14 min 12 s** (02:43:26–02:57:38 local).
  No continuous peak-RAM measurement is claimed.
- This is a **development-only candidate prompt receipt**, not a frozen
  machine preregistration, training permission, target accuracy, or neural
  capability result. The high truncation share deserves scientific review;
  do not tune the prompt after seeing held-out results. PrimeVul v2 amendment,
  data rights, independent reviewer, isolated sealer, R0.0 cross-artifact
  validator, real-data training, and held-out confirmation remain open.
  ALC-0 OPEN.

## 2026-09-29 — Family-B class-conditional truncation audit checkpoint 54

- Extended the non-authorizing defect-prompt receipt to version 2 with
  `train_truncated_labels` and `validation_truncated_labels`. These aggregate
  counts expose whether the fixed 499-code-token head/tail rule removes a
  disproportionate share of either class without emitting raw code or IDs.
  The ordered prompt-ID roots and prompt policy are unchanged. This is a
  development-data diagnostic, not a revised token budget or acceptance floor.
- Added a synthetic mixed-length/label fixture. The focused receipt and runner
  tests passed **12/12**. Ruff check and format check passed on the two changed
  Python files. The broader Windows ALC-R0 `pytest tests -k alc_r0 -q
  --disable-warnings` run exited **0** and reached 100%; it was not emitted as
  JUnit, so no exact suite count is claimed here.
- Full pinned-corpus v2 aggregate values are not yet established at this
  checkpoint. The earlier version-1 full receipt remains valid historical
  evidence but cannot answer the class-conditional truncation question.
  `training_authority=false`; held-out data was not accessed; ALC-0 OPEN.

## 2026-09-29 — Full class-conditional PrimeVul prompt audit checkpoint 55

- Ran the v2 candidate receipt after a session-level clean-status check at
  source commit `f1b15e38c5d5b07a7211b57c12b593d48c14d412`
  against only the same pinned original PrimeVul train/validation, paired
  development files, prior full-graph receipt (raw SHA-256
  `e54c729d9c7d3ccaa3f50efcb6edcfc492c880131f0c5cf61df1db9714533243`),
  and verified local SmolLM2 tokenizer snapshot. Terminal exit was **0**;
  the committed stdout/stderr/exit files do not themselves bind the exact
  command, runtime HEAD, or clean status, so the clean-commit statement is
  an operator observation rather than independently replayable provenance.
  A future formal run must capture a bound launch manifest.
  Stdout status is `full-graph-structural-audit-clear-non-authorizing`, source
  scope `pinned-original-development`, `training_authority=false`, and
  `held_out_data_present=false`. All 206 monotone graph progress events ended
  at **209857/209857** with **19,874** candidates. The original-tokenization
  >8192 Transformers warning appeared once; no 512-token forward failure is
  claimed.
- The v1 and v2 ordered train and validation prompt-ID roots, verified model
  inventory root, total/label row counts, and total truncation counts matched.
  This run changes only aggregate diagnostics, not prompts or data splits.
  New class-conditional counts: train safe **35,468/171,717 (20.65%)** and
  vulnerable **3,608/5,574 (64.73%)** truncated; validation safe
  **4,363/22,210 (19.64%)** and vulnerable **299/562 (53.20%)** truncated.
  Both per-label sums exactly equal the preexisting total truncated rows
  (**39,076** train; **4,662** validation).
- Evidence files are
  `results/alc_r0_primevul_prompt_class_audit_f1b15e3_20260929.stdout.log`
  (SHA-256 `c00ac48e2b3d3591d8f39d1fe47df56b4eaf5ad7bf962cd3e3464315ca085dac`),
  `.stderr.log` (SHA-256
  `33ac93ce1867c81ec43a6c5ef4a4f710ce42bd587015d17ee95ae226747dcb8b`),
  and `.exit.log` (`python_exit_code=0`). The prior v1 receipt is retained.
- The substantially higher vulnerable-class truncation rate is a **blocking
  scientific review concern**, not proof that the defect location was cut or
  that the model will fail. The v2 amendment draft now requires an explicit
  pre-held-out reviewer decision; no threshold or prompt policy was silently
  changed. Rights, independent review, sealer, R0.0 validation, and model
  training remain open. ALC-0 OPEN.

## 2026-09-29 — Independent prompt-audit review checkpoint 56

- Two independent GPT-6 Sol read-only lanes reviewed diff `84c0503..34bc559`:
  a code/security lane returned **COMMENT** (no new counter correctness or
  security defect; one medium evidence-provenance issue and one low test-gap),
  and an architecture/science lane returned **WATCH** for the diagnostic code
  but **BLOCK** for family-B prompt freeze/training as-is. Combined review of
  this diagnostic diff is **COMMENT**, not merge-ready scientific authority.
- The code lane observed that the committed run files do not independently
  prove the exact invocation or runtime clean commit. Checkpoint 55 is now
  explicitly qualified as a session-level operator observation; future formal
  evidence requires a bound launch manifest. The fixture now exercises
  nonzero safe and vulnerable truncation in both train and validation. Focused
  receipt/runner tests passed **12/12**; Ruff check/format and diff check
  passed. This test-coverage repair does not alter receipt generation.
- The science lane found no reason to reject the diagnostic code, but the
  measured class-correlated truncation cannot establish whether the actual
  vulnerable/patched distinction survives. Authors' 512 block-size example is
  not proof for this tokenizer/head-tail rule. A development-only pair-contrast
  diagnostic is the next safe step; it can identify identical prompts after
  truncation but cannot prove semantic sufficiency where prompts differ.
  The v2 draft, rights, sealer, machine preregistration, R0.0 validator and
  training authority remain OPEN. No held-out access or model training.

## 2026-09-29 — Development pair-prompt contrast diagnostic checkpoint 57

- Before any full-data execution, the non-authorizing v2 draft now defines a
  narrowly interpretable author-pair diagnostic: compare complete vulnerable
  and patched-safe prompt token IDs under the unchanged 512-token candidate
  rule. Exact equality proves that pair cannot be distinguished from this
  prompt alone; inequality does **not** prove the security-relevant difference
  survived. Counts are split by author train/validation and both/one/neither
  code-truncation state. The author-pair population is not automatically the
  final retained graph population; no acceptance threshold was added.
- TDD RED was the missing `paired_prompt_contrast` module. Implemented a
  bounded metadata-only reference plus a CLI that re-verifies the pinned
  train/validation and paired-development bytes and model snapshot, requires
  a clean committed source checkout before and after its run, and emits the
  source commit/tree digest, exact invocation paths, aggregate counts, and
  ordered pair-prompt root. It never opens held-out data and always emits
  `training_authority=false`.
- Focused synthetic/source-fixture tests passed **7/7**, including a pair
  whose distinct raw functions collapse to identical prompt IDs, a pair whose
  distinction survives, invalid/identical-code rejection, metadata-only
  output, and source-byte tampering. The combined focused set (new diagnostic,
  earlier prompt receipt and paired-source tests) passed **20/20**; Ruff check
  and format passed. The broader Windows ALC-R0 regression exited **0**:
  JUnit **412 tests, 0 failures, 0 errors, 8 skipped**, time **353.156 s**.
  `results/alc_r0_pair_prompt_contrast_regression_20260929.xml` SHA-256 is
  `61eda6fcf3af11968bdcc2d614d87348bc1ee4d5206a8ed03b4060241fbe53a5`.
- This checkpoint is implementation plus fixture/regression evidence only.
  The pinned full development pair diagnostic has not run yet; no learning,
  confirmatory score, v2 amendment approval, or ALC-0 PASS is claimed.

## 2026-09-29 — Pinned PrimeVul author-pair prompt collapse checkpoint 58

- Ran the predeclared development-only pair diagnostic from clean source
  commit `4bc8160a8b18786b76a264b3f125a9c105d5f80b`, source-tree SHA-256
  `5f1d3f3c23cda992453a48f86c00c95dac2e31e7cc131cfb8daf8af7f8e6cef7`
  (318 tracked files). The canonical stdout embeds this source checkout and
  invocation, pinned original-development source scope, verified model
  inventory root
  `d9db0058a63990399f26b53ff7480f2e67bd5ef9a0398797fecfeb4ed9732b0e`,
  and pair-source receipt root
  `e3d92be86e8f4e44c4db7c5afe3cc47ab3beeec89d5540c34dbcef4e562cbd5f`.
  The checkout was required clean before and after execution. Terminal Python
  exit was **0**; `training_authority=false` and
  `held_out_data_present=false`.
- Among **4,354** author train vulnerable/patch pairs, **1,284 (29.49%)**
  became *identical complete prompt token-ID sequences* under the candidate
  512-token rule. Train truncation states were both **2,808**, one **126**,
  neither **1,420**. Among **562** author validation pairs, **160 (28.47%)**
  collapsed; truncation states were both **334**, one **24**, neither **204**.
  Both partitions sum exactly to their respective pair counts. Ordered
  pair-prompt roots are train
  `2aec0e6843562b6bbee1a72b6bbdbe17e60fa4c4827687c63dc66791f6f61ae6`
  and validation
  `88752db8ef06fc014cad185612190d61c6bd0830afd55a89253e68140a912bc6`.
- Evidence files `results/alc_r0_paired_prompt_contrast_4bc8160_20260929.stdout.log`
  and `.stderr.log` have SHA-256 respectively
  `9cb57a61cb14feb4c79aed58d81772c732fb3e3058fb9bbb7b43a6573659c3e6`
  and `8685701b3daed0865b3e927f67cdb47f6fa3444d782a19ce29e445f65fc65e84`;
  `.exit.log` records `python_exit_code=0`. Stderr has one original-tokenization
  warning (`8733 > 8192`) before truncation, not evidence of an over-budget
  model forward. Exact stdout bytes were copied from an external run directory
  after terminal success and rehashed; no raw code or source IDs are emitted.
- Different normalized code becoming identical prompt IDs proves that those
  author pairs are non-identifiable to a retrieval-off model using this input.
  It does **not** prove that every non-collapsed pair retains the vulnerability
  signal, that the final retained train/validation cohort has the same rate,
  or that ALC-0's overall neural-capability hypothesis is false. This is a
  serious blocker to freezing the **current** family-B prompt unchanged;
  independent code/science review and an explicit pre-held-out v2 decision are
  pending. No threshold, data split, or prompt was silently changed; no
  held-out access or model training occurred. ALC-0 OPEN.

## 2026-09-29 — Pair prompt review and provenance repair checkpoint 59

- Independent GPT-6 Sol code/security review returned **COMMENT** for source
  commit `4bc8160`: no demonstrated count, source-boundary, held-out-access or
  raw-code disclosure defect, but model snapshot was only verified before
  several thousand tokenizer operations and tests lacked pair-order and
  one-sided truncation coverage. Independent architecture/science review
  returned **CLEAR** for the diagnostic itself, **WATCH** that author pairs are
  not automatically the final retained cohort, and **BLOCK** for freezing the
  unchanged 512-token family-B prompt. The v2 draft now records that negative
  decision without changing any acceptance threshold or test split.
- The CLI now re-verifies the model inventory after all pair tokenization and
  fails if it changed. Tests now assert an order-sensitive prompt root and the
  one-sided truncation branch. Focused diagnostic/prompt/paired-source tests
  passed **21/21**; Ruff check/format and diff check passed. A full pinned
  development-data rerun from this repaired code is still required, so the
  previous `4bc8160` receipt remains valid historical evidence only.
- Post-review Windows ALC-R0 regression exited **0**: JUnit **413 tests,
  0 failures, 0 errors, 8 skipped**, time **628.315 s**. XML
  `results/alc_r0_pair_prompt_contrast_postreview_regression_20260929.xml`
  SHA-256 is
  `7ab9d437220d5215ab92a8bb16cd605e654bc6ea55e076549b2e11a03ee4c58c`.
  No real-data training, held-out access, or ALC-0 PASS occurred.

## 2026-09-29 — Repaired PrimeVul pair prompt rerun checkpoint 60

- Re-ran the complete pinned original-development author-pair diagnostic from
  clean source commit `f42ac6dda90b43ea7d717f96d14a31a220357bf7` after the
  end-of-run tokenizer-snapshot re-verification repair. The receipt embeds
  source-tree SHA-256
  `f0b93ba2f5cd424ecf552b94bc214213b964c336c5fb7647252c98ec3ec61acf`
  (322 tracked files), unchanged model inventory root
  `d9db0058a63990399f26b53ff7480f2e67bd5ef9a0398797fecfeb4ed9732b0e`,
  and pinned pair-source root
  `e3d92be86e8f4e44c4db7c5afe3cc47ab3beeec89d5540c34dbcef4e562cbd5f`.
  CLI Python exit was **0**; checkout remained clean until evidence was copied
  after the terminal result. `training_authority=false` and
  `held_out_data_present=false`.
- Train again had **1,284/4,354** collapsed pairs and truncation partition
  **2,808 both / 126 one / 1,420 neither**. Validation again had
  **160/562** collapsed pairs and **334 both / 24 one / 204 neither**.
  Ordered pair-prompt roots exactly match checkpoint 58: train
  `2aec0e6843562b6bbee1a72b6bbdbe17e60fa4c4827687c63dc66791f6f61ae6`,
  validation
  `88752db8ef06fc014cad185612190d61c6bd0830afd55a89253e68140a912bc6`.
  This reproduces the negative development-only finding under the repaired
  provenance check; it is not an ALC-0 neural result or final retained-cohort
  rate.
- Canonical evidence is
  `results/alc_r0_paired_prompt_contrast_f42ac6d_20260929.{stdout,stderr,exit}.log`.
  Stdout SHA-256 is
  `d4101fc7549924284d81462b7f05d4344a5ec2e6b58da660af5625005ef37077`,
  stderr SHA-256 is
  `8685701b3daed0865b3e927f67cdb47f6fa3444d782a19ce29e445f65fc65e84`;
  stderr contains only the same 8,733-versus-8,192 original-tokenization
  warning, not a model forward. No prompt/budget or acceptance threshold was
  altered. The unchanged 512-token family-B prompt remains **BLOCK** for
  freeze, and the v2 draft, rights, sealer, and learning gates remain open.

## 2026-09-29 — Predeclared prompt-budget sensitivity implementation checkpoint 61

- Before running any new full-development comparison, the non-authorizing v2
  draft declared the exact common-budget grid **512, 1024, 2048, 4096, 8192**
  tokens, evaluated in that order with the same pinned original author pairs,
  tokenizer, normalization, head/tail rule, and label candidates. This is a
  mechanistic input-availability diagnostic, not a prompt freeze, training
  authorization, acceptance-threshold change, or held-out evaluation. The
  model snapshot declares 8,192 maximum positions; local machine observation
  was RTX 4050 Laptop GPU (6,141 MiB reported total) and 16 GiB RAM. Larger
  forward/training feasibility has **not** been demonstrated.
- TDD RED: the fixture test for a declared 1,024-token common budget failed
  with `TypeError: ... unexpected keyword argument 'max_common_tokens'`.
  The pinned runner now accepts only the five declared values, preserves 512
  as its default, passes the selected value to both train and validation pair
  audits, and records it in the receipt. The CLI exposes the same constrained
  option. Tests also require default-512 parity, reject non-grid/bool/string
  values, and demonstrate a synthetic middle-only difference recovered by
  larger context.
- Focused prompt/pair-source regression exited **0**: JUnit **27 tests,
  0 failures, 0 errors, 1 skipped**, time **6.152 s**; XML
  `results/alc_r0_prompt_budget_grid_focus_20260929.xml` SHA-256
  `3d4217482164e3dd58eb293eb703a6a823b65ca8b7a73669d56f661bea261a11`.
  Broader `pytest tests -k alc_r0 -q --disable-warnings` exited **0**:
  JUnit **420 tests, 0 failures, 0 errors, 8 skipped**, time **318.844 s**;
  XML `results/alc_r0_prompt_budget_grid_regression_20260929.xml` SHA-256
  `0bdee327d4c17635c1fa63b7382bd9f0a9e785e5d80bcf54d0c7111600d119b5`.
  Ruff check/format and diff check passed. Full pinned grid runs remain to be
  executed from a clean committed source checkout. ALC-0 remains OPEN.

## 2026-09-29 — Full development-only prompt-budget grid checkpoint 62

- From clean source commit `e316531689f5db93a1667479e24907d3683e14ee`,
  source-tree SHA-256
  `396cbd65e38ee26df69201d815df827e337decca3ae2489ace7ae54f6215a627`
  (327 tracked files), ran the complete predeclared **512, 1024, 2048, 4096,
  8192** common-token grid in order. Each CLI receipt verifies the pinned
  original train/validation and paired-development bytes, model snapshot
  before/after, and clean checkout before/after. The pair-source root remained
  `e3d92be86e8f4e44c4db7c5afe3cc47ab3beeec89d5540c34dbcef4e562cbd5f`;
  model inventory root remained
  `d9db0058a63990399f26b53ff7480f2e67bd5ef9a0398797fecfeb4ed9732b0e`.
  Every Python exit code was **0**. All receipts say
  `training_authority=false`, `held_out_data_present=false`; no model forward
  or training occurred.
- Complete prompt-ID collision and truncation results among **4,354** author
  train pairs and **562** author validation pairs:

  | Common budget | Train collisions | Train both / one / neither truncated | Validation collisions | Validation both / one / neither truncated | Wall seconds |
  | ---: | ---: | ---: | ---: | ---: | ---: |
  | 512 | 1,284 | 2,808 / 126 / 1,420 | 160 | 334 / 24 / 204 | 134.278 |
  | 1,024 | 671 | 1,820 / 88 / 2,446 | 88 | 222 / 9 / 331 | 159.902 |
  | 2,048 | 311 | 941 / 44 / 3,369 | 41 | 110 / 5 / 447 | 389.632 |
  | 4,096 | 124 | 418 / 10 / 3,926 | 14 | 40 / 1 / 521 | 294.029 |
  | 8,192 | 37 | 155 / 3 / 4,196 | 4 | 16 / 0 / 546 | 173.897 |

  Every truncation partition sums to its pair count. The 512 train and
  validation ordered prompt-ID roots exactly match checkpoints 58 and 60;
  larger-budget roots are in their canonical stdout receipts. The 8,192 point
  is the pinned SmolLM2 snapshot's `max_position_embeddings`, not a proven
  local training configuration.
- Canonical metadata-only receipts are
  `results/alc_r0_prompt_budget_grid_e316531_20260929_<budget>.stdout.log`
  with corresponding `.stderr.log`; exact SHA-256s, wall times, exit codes,
  command template, offline variables, and GPU start/end snapshots are in
  `results/alc_r0_prompt_budget_grid_e316531_20260929.execution.log`.
  All five stderr files contain the same original-tokenization warning
  (`8733 > 8192`), not a model forward. GPU free memory read 5,920 MiB at
  both start and end on a 6,141 MiB RTX 4050 Laptop GPU; peak GPU or process
  RSS was not continuously measured. Timing is diagnostic only, not a
  monotonic performance benchmark. Source checkout remained clean until
  terminal results were verified and copied into the repository.
- `.gitattributes` pins these generated grid logs as byte-preserved (`-text`)
  because the host has `core.autocrlf=true`; this protects the listed raw
  SHA-256s across clean clones. All eleven staged grid-log blob OIDs matched
  `git hash-object --no-filters` on the copied files; each copied stdout/stderr
  SHA-256 also matched its external-run source before staging.
- The mechanism is now clear within this scope: raising available context
  reduces exact vulnerable/patch prompt collisions, yet **37 train and 4
  validation author pairs still collide at the model's maximum one-pass
  context**. This is not a final retained-cohort rate or proof that all
  non-collapsed pairs retain vulnerability semantics. The PrimeVul authors
  caution that some vulnerabilities span multiple functions
  ([paper](https://arxiv.org/html/2403.18624v2)); that reinforces the
  single-function scope limit but does not change this experiment's declared
  task. No budget, threshold, or prompt is selected for freeze. Independent
  scientific review, rights, sealer, training feasibility, and the actual
  neural capability test remain open; ALC-0 is **not PASS**.

## 2026-09-29 — Synthetic real-host context-gradient probe implementation checkpoint 63

- After the non-authorizing pair-prompt grid, the v2 draft explicitly declared
  a separate synthetic-only resource probe at lengths **512, 1024, 2048**, in
  that order, with both `ResearchCapsuleV0` and matched q-only LoRA at ports
  (14, 29), rank 8, batch 1, BF16 pinned SmolLM2 host and FP32 factors. It
  permits one final-token backward and **zero optimizer updates** per fresh
  process, with no PrimeVul rows, held-out data, retrieval, or capability
  claim. The frozen v1 target-task sequence/budget is not amended by this
  probe; the declared v2 decision remains pending.
- TDD RED: new tests failed collection because
  `aluclu.alc_r0.context_gradient_probe` did not exist. Implemented a guarded
  standalone CLI that accepts only the six declared arm/length cells, checks
  clean committed source and >=20 GiB free space, verifies the pinned local
  snapshot before/after, uses offline BF16 real-host loading and deterministic
  eager CUDA math, performs one synthetic final-token cross-entropy backward,
  and emits metadata-only loss/gradient/time/CUDA-memory and canonical
  frozen-base pre/post digest evidence. OOM and nonfinite outcomes are explicit
  failures; no optimizer is constructed. The source snapshot remains unchanged.
- Focused JUnit `results/alc_r0_context_gradient_probe_focus_20260929.xml`
  exited **0** with **15 tests, 0 failures, 0 errors, 0 skipped**, time
  **29.734 s**, SHA-256
  `3a7d146d47d8db5eb5856b58b69cdbbe3781d143a7f986143da28fa65cebe729`.
  Broader `pytest tests -k alc_r0 -q --disable-warnings` exited **0**:
  JUnit `results/alc_r0_context_gradient_probe_regression_20260929.xml`
  **435 tests, 0 failures, 0 errors, 8 skipped**, time **294.676 s**,
  SHA-256 `44f58afea177258222718c5865d8cf9d47eb0da1d273051f7e86501ad7d0f36d`.
  Ruff check/format and diff check passed. `.gitattributes` preserves these
  generated evidence bytes under Windows `core.autocrlf=true`.
- This checkpoint proves implementation and regression only. No six-cell
  real-host resource result has been executed yet, no 200-update pilot was
  run, and ALC-0 remains OPEN.

## 2026-09-29 — Six-cell real-host synthetic gradient resource checkpoint 64

- Ran all six predeclared cells in separate processes from clean source commit
  `d4fb2d1bc166b74c38e27424585f43059025777e`, source-tree SHA-256
  `11b4300847051169928e1ce1e57b9073b1fe29c5a0624d8bcd05e436b79486d9`
  (342 tracked files). All receipts share pinned model inventory SHA-256
  `d9db0058a63990399f26b53ff7480f2e67bd5ef9a0398797fecfeb4ed9732b0e`
  and frozen-base canonical digest
  `ce7e8dd6a97ac4cc56bf4f1e38625817386e27af58f1ed63377741f7f2aab1ba`.
  Every base digest matched before/after, `training_authority=false`,
  `held_out_data_present=false`, `synthetic_only=true`, and
  `optimizer_updates=0`. The pinned Windows research environment reports
  Python 3.12.13, Torch 2.14.0+cu130, Transformers 5.17.0, and an RTX 4050
  Laptop GPU with 6,438,780,928 physical GPU bytes.
- Every cell had terminal Python exit **0**, finite positive loss and gradient
  norm, and no OOM. CUDA peak measured by PyTorch after allocator-cache clear
  and peak reset, around one final-token cross-entropy backward, was:

  | Sequence tokens | Capsule allocated / reserved MiB | Matched q-only LoRA allocated / reserved MiB |
  | ---: | ---: | ---: |
  | 512 | 683.1 / 706.0 | 696.6 / 730.0 |
  | 1,024 | 1,483.3 / 1,510.0 | 1,535.4 / 1,564.0 |
  | 2,048 | 4,423.5 / 4,522.0 | 4,602.0 / 4,810.0 |

  These are one-shot observations, not continuous driver/process VRAM maxima
  or multi-step benchmarks. Wall times including model load and digest checks
  were respectively **81.819, 71.809, 73.893, 70.416, 71.628, 96.023 s**
  in ascending length and capsule-then-LoRA order; they are not performance
  rankings. The loss supervises only a single final token, so this is **not**
  a full label-sequence training-memory upper bound. At 2,048, the measured
  one-backward allocated peak is close to the 6-GiB hardware envelope; no
  optimizer step, 200-step stability, full task training, or retention was
  demonstrated. No prompt/budget selection is made.
- Canonical metadata-only stdout receipts and model-loading-only stderr logs
  are `results/alc_r0_context_gradient_probe_d4fb2d1_20260929_<length>-<arm>.*.log`.
  `results/alc_r0_context_gradient_probe_d4fb2d1_20260929.execution.log`
  records exact per-cell exit codes, wall times, stdout/stderr SHA-256s, source,
  model, base, environment, and measurement limits. The external-run bytes
  were copied with SHA-256 equality; `.gitattributes` preserves committed log
  bytes. The wall times in the execution index were transcribed from terminal
  stopwatch output, not emitted by the probe itself. A first index-validation
  attempt caught a manually mistyped 1,024-capsule stderr hash; it was corrected
  from the actual file before commit, and all six rows then passed exact
  SHA-256/format checks. This resource evidence informs an independent v2
  decision only.
  The frozen v1 protocol is unchanged; ALC-0 remains OPEN.

## 2026-09-29 — Retained author-pair prompt audit implementation checkpoint 65

- Before inspecting a graph-cleaned prompt result, the non-authorizing v2
  draft fixed the population and analysis: classify every pinned development
  author pair by both / vulnerable-only / safe-only / neither endpoints
  retained, then run the unchanged 512/1024/2048/4096/8192 prompt-ID grid
  only on both-retained pairs. This is conditional on author-pair survival;
  it does not measure all retained observations, select a prompt, authorize
  training, or touch held-out files.
- TDD RED: the new focused test failed collection because
  `retained_paired_prompt_contrast` did not exist. The implementation verifies
  original train/validation and pair bytes, rebuilds the development graph,
  requires all four pinned graph ledgers to equal the prior full-graph run,
  and emits only aggregate survival/collision/truncation counts plus roots.
  It checks clean source and pinned tokenizer inventory before/after its CLI
  run. An empty both-retained subset is an explicit zero-count diagnostic.
- Focused tests passed **5/5**. Broader ALC-R0 regression exited **0**:
  `results/alc_r0_retained_pair_regression_20260929.xml` has **440 tests,
  0 failures, 0 errors, 8 skipped**, time **209.695 s**, SHA-256
  `887298c0dd99d92c30aeaca05600b59f626532afbf8a087399af15a338492cf8`.
  Ruff check/format and diff check passed after formatting. The pinned
  full-development survivor-pair run has **not yet executed** at this
  checkpoint; no survival fraction or graph-cleaned collision result is
  claimed. Source rights, v2 prompt review, sealer, training, and ALC-0
  capability proof remain OPEN.

## 2026-09-29 — Full retained author-pair prompt audit checkpoint 66

- From clean source commit `c1996d21537e582ec4491634f210351bfbe7536e`
  (source-tree SHA-256
  `bfcdd088515a13f6b372d5c6c07e0a44b39695c2788c044b9209db5c0c4ddd98`,
  358 tracked files), ran the development-only pinned original graph and
  complete predeclared **512, 1024, 2048, 4096, 8192** retained-author-pair
  prompt grid. Terminal Python exit was **0**. Source pair root
  `e3d92be86e8f4e44c4db7c5afe3cc47ab3beeec89d5540c34dbcef4e562cbd5f`
  and model inventory root
  `d9db0058a63990399f26b53ff7480f2e67bd5ef9a0398797fecfeb4ed9732b0e`
  matched prior evidence. All four graph ledgers matched the pinned prior
  full-graph receipt exactly; it retained **177,291** train and **22,772**
  validation observations. The 206 graph progress events reached
  **209,857/209,857** rows and **19,874** candidates.
- Author-pair survival partition was exhaustive: train **4,344 both**, **10
  vulnerable-only**, **0 safe-only**, **0 neither** out of 4,354; validation
  **482 both**, **0 vulnerable-only**, **0 safe-only**, **80 neither** out of
  562. The validation loss of complete pairs is consistent with whole
  train-overlap component exclusion, but this audit does not assign a causal
  reason to each pair. Both-retained prompt results were:

  | Common budget | Train collisions / 4,344 | Train both / one / neither truncated | Validation collisions / 482 | Validation both / one / neither truncated |
  | ---: | ---: | ---: | ---: | ---: |
  | 512 | 1,283 | 2,800 / 126 / 1,418 | 109 | 260 / 22 / 200 |
  | 1,024 | 671 | 1,815 / 88 / 2,441 | 56 | 157 / 9 / 316 |
  | 2,048 | 311 | 941 / 44 / 3,359 | 26 | 73 / 5 / 404 |
  | 4,096 | 124 | 418 / 10 / 3,916 | 7 | 23 / 1 / 458 |
  | 8,192 | 37 | 155 / 3 / 4,186 | 3 | 10 / 0 / 472 |

  Each truncation partition sums to the both-retained denominator. At 512,
  the conditional exact-collision rates are **29.53% train** and **22.61%
  validation**. The earlier all-author-pair grid had 1,284/4,354 and
  160/562; its validation fraction must not be called the final retained
  pair rate. These are conditional author-pair diagnostics, not collision
  rates among all retained single-function observations or evidence that
  non-collapsed prompts contain learnable vulnerability signal.
- Canonical metadata-only stdout receipt
  `results/alc_r0_retained_pair_c1996d2_20260929.stdout.log` has SHA-256
  `9811197222444ab6a2bb3f5889d0b187805cb4aae3ad88ad1b9ae095d4e236d8`;
  stderr progress/warning log
  `results/alc_r0_retained_pair_c1996d2_20260929.stderr.log` has SHA-256
  `cc802def1ec4295470c2412c15a60d00c1cc94ebd056e72bbec9cd0430c58dec`.
  External-run and copied bytes matched exactly; `.gitattributes` preserves
  committed log bytes. Stderr's original-tokenization warning (`8733 >
  8192`) is the same kind observed in the prior grid; no model forward,
  optimizer update, real-data training, or held-out access occurred.
  `training_authority=false`; the v2 prompt, rights, sealer, and actual
  ALC-0 neural capability proof remain **OPEN**.

## 2026-09-29 — Synthetic optimizer-update diagnostic implementation checkpoint 67

- After the retained author-pair analysis, explicitly predeclared a separate
  non-authorizing, synthetic-only **16-update** execution diagnostic for the
  pinned SmolLM2-135M host. It holds ports `(14, 29)`, rank 8, seed
  `20260916`, 512 synthetic tokens, target token ID 23, BF16 frozen/eval
  base, FP32 factors, and existing AdamW values fixed. Capsule and exactly
  parameter-matched q-only LoRA are separate fresh-process cells. The
  capsule's learned SafeTensors artifact must then survive a separate-process
  remount with target log-probability agreement within `1e-4` and detached
  base-score agreement within `1e-4`. This does **not** replace R0.4's
  200-step, real-data, effective-batch-16 feasibility pilot.
- TDD RED: focused tests failed collection at missing
  `aluclu.alc_r0.synthetic_update_probe`. Added a bounded AdamW update loop,
  finite loss/gradient/factor checks, frozen-base and deterministic-CUDA
  checks, before/after target-token log probability, factor/base digests,
  memory/runtime measurements, and canonical capsule serialization/remount
  CLI. No PrimeVul, Banking77, or held-out data are read by this diagnostic;
  `training_authority=false`, `synthetic_only=true`, and retrieval is off.
- Focused JUnit `results/alc_r0_synthetic_update_focus_20260929.xml` exited
  **0** with **29 tests, 0 failures, 0 errors, 0 skips**, time **12.788 s**,
  SHA-256
  `07a34c91deff7e331d539f5310b4b8d99f0e36652e1eb9d376134cbbd43f111c`.
  Broader ALC-R0 regression
  `results/alc_r0_synthetic_update_regression_20260929.xml` exited **0**:
  **445 tests, 0 failures, 0 errors, 8 skips**, time **194.126 s**, SHA-256
  `0b6320c935a1503da5ee76d2a35aa13621520f5dd64092b105314b6b3245c84d`.
  Ruff check/format and diff check passed. Pyright was unavailable in the
  locked research environment (`No module named pyright`), so no static-type
  PASS is claimed. At this checkpoint the real-host 16-update cells and
  fresh-process remount have **not yet run**; ALC-0 remains OPEN.

## 2026-09-29 — Real-host synthetic neural update and remount checkpoint 68

- From clean source commit `c4f147ca1cb9e3a88c651133dbf5ca229a1fdf56`,
  ran the predeclared capsule and matched q-only LoRA cells in **separate
  processes**, followed by a **third fresh-process** capsule remount. All
  three Python processes exited **0**. The pinned model inventory root was
  `d9db0058a63990399f26b53ff7480f2e67bd5ef9a0398797fecfeb4ed9732b0e`.
  Receipts record `training_authority=false`, `held_out_data_present=false`,
  `synthetic_only=true`, `retrieval_enabled=false`, 512 synthetic tokens,
  fixed target ID 23, frozen BF16/eval base, FP32 rank-8 factors at ports
  `(14, 29)`, eager attention, and exact optimizer settings. No task dataset
  was opened; no R0.4 authority or held-out evaluation was invoked.
- Each training process performed exactly **16** AdamW updates, with 16 finite
  losses and nonzero finite pre-clip gradient norms. The capsule's target-token
  log probability changed **-6.6672158241272 → -6.34233427047729**
  (`+0.324881553649902`); q-only LoRA changed **-6.6672158241272 →
  -6.5954794883728** (`+0.0717363357543945`). Both factor-state hashes
  changed, while each frozen-base canonical state hash stayed identical
  before/after and received no gradient. Detaching each arm returned exactly
  to the original base score. Measured CUDA peak allocated/reserved was
  **683.3/706.0 MiB** for capsule and **696.7/730.0 MiB** for LoRA;
  update-loop elapsed times were **3.83 s** and **3.66 s**, excluding model
  loading/digest verification. These are observed resource points, not
  comparative throughput rankings.
- The learned capsule serialized as a **676-byte canonical manifest** and a
  **74,040-byte SafeTensors** payload. Artifact SHA-256s were respectively
  `425dc4a852df8a24f79b66e3d16d7ad15becdef8072aaf67a65836cbdca715cc`
  and
  `d0da43da78b1d1a0f8258729bed91aff67fd30fb23d051e32d882567029f651a`.
  The third process loaded the pinned base anew and remounted those exact
  bytes: mounted score **-6.34233427047729** matched the training post-score
  exactly; detached score **-6.6672158241272** matched the training
  pre-score exactly. Both absolute differences are **0**, under the
  predeclared `1e-4` tolerance. The fresh base digest remained unchanged.
- Canonical metadata-only receipt SHA-256s (capsule, LoRA, remount) are
  `dca7d0bf198fa4d3f771078023ae14f2c9e7f20936ecd795d68f8e665577a082`,
  `4418f92e703a257de8b84290b2bacd5fe322db7ac60a1980aded8559fbf3bcc0`,
  and `f68e10aae6702cf5c983d76c0917f5ac1fd98604284e0c662576dd708638cc1f`.
  Stderr hashes are
  `2fa348f5ac534fa7d941726275eb457af2092256e32d41cdf4a34e699f40fd20`,
  `6dfb9e0345562dbb034cb07d2b7ea712dcdfdeb8e5225b7b1ca2e7cbab6f3b1a`,
  and `059f6a4418556f9810c96ca3c198a1c103884cdbccb2957aea2fde07b7120d56`.
  External-run and copied bytes matched; an initial PowerShell evidence-copy
  mapping had a syntax error and created **no** target files, then the
  corrected explicit eight-file copy passed SHA-256 equality. A separate
  read-only receipt audit checked commit/model roots, all 16 finite updates,
  unchanged bases, changed factors, detach/remount equality, artifact hashes,
  and scope flags: PASS for this narrow diagnostic.
- This is the first observed optimizer update stored in a remountable neural
  capsule on the real host, but it is **one fixed synthetic next-token
  example**, not a real capability suite. It does not prove generalization,
  200-step stability, actual Banking77/PrimeVul learning, old-skill retention,
  or ALC-0. The v2 prompt/rights/independent review, R0.0 freeze, real-data
  R0.4 pilot, and confirmatory neural capability gate remain **OPEN**.

## 2026-09-29 — Predeclared 2,048-token update-cell implementation checkpoint 69

- The earlier 512-token synthetic update did not establish feasibility at the
  longer family-B context. Before a new real-host run, extended the
  non-authorizing diagnostic declaration to exactly **2,048 synthetic tokens**,
  same capsule/matched q-only LoRA arms, 16 updates each, and third-process
  capsule remount. Every other pinned hyperparameter, factor/base rule,
  source/model check, and 20-GiB free-space floor remains unchanged. OOM or
  failure will remain a negative result; no fallback length or smaller step
  count is allowed. This still does not measure full label-sequence training,
  effective batch 16, or the 200-step real-data R0.4 pilot.
- TDD RED: the explicit `length=2048` fixture and six invalid-length cases
  failed because the probe did not accept a length. The CLI now admits only
  512 (preserved default) or 2,048, records the selected length in train and
  remount receipts, and keeps the existing deterministic token-ID rule.
  Focused JUnit `results/alc_r0_synthetic_update_long_focus_20260929.xml`
  exited **0** with **36 tests, 0 failures, 0 errors, 0 skips**, time
  **10.342 s**, SHA-256
  `b9736944923f1cad255b47a52a3bd5fa3106bc597e609583678e0296d63ec6d6`.
  Broader ALC-R0 regression
  `results/alc_r0_synthetic_update_long_regression_20260929.xml` exited
  **0** with **452 tests, 0 failures, 0 errors, 8 skips**, time **173.443 s**,
  SHA-256
  `e86e8b5e2650dcd30bab0be27579beac4da39c78114bfa9328b7f51efc601988`.
  Ruff check/format and diff check passed. The 2,048-token real-host cells
  have **not yet run** at this checkpoint.
- Rechecked the [PrimeVul authors' README](https://github.com/DLVulDet/PrimeVul/blob/main/README.md)
  and [repository MIT file](https://github.com/DLVulDet/PrimeVul/blob/main/LICENSE).
  The README describes a research train/evaluate purpose and provides training
  commands, but no explicit grant covering the separately hosted original
  JSONL and embedded third-party code was found. This is not a legal ruling;
  rights/provenance remain unresolved and `training_authority=false`.

## 2026-09-29 — Real-host 2,048-token synthetic update checkpoint 70

- Ran all three predeclared fresh processes from clean source commit
  `3966c90ad67eb92c8035d1eaf94f57cbb494d463`: 2,048-token capsule,
  2,048-token matched q-only LoRA, and canonical capsule remount. Each Python
  process exited **0**; no OOM or retry occurred. The model inventory root
  remained
  `d9db0058a63990399f26b53ff7480f2e67bd5ef9a0398797fecfeb4ed9732b0e`.
  All receipts report `training_authority=false`, `held_out_data_present=false`,
  `synthetic_only=true`, `retrieval_enabled=false`; no real task data, held-out
  data, or optimizer policy amendment was used.
- Both arms performed exactly **16** successful AdamW updates with 16 finite
  losses and positive finite pre-clip gradient norms. Capsule target-token
  log probability changed **-6.94224405288696 → -6.530837059021**
  (`+0.411406993865967`); matched q-only LoRA changed from the same baseline
  to **-6.83657646179199** (`+0.105667591094971`). Each factor hash changed;
  each frozen-base canonical digest remained identical and received no
  gradient. Detached scores returned exactly to the baseline. CUDA peak
  allocated/reserved was **4,424.6/4,522 MiB** for capsule and
  **4,603.1/4,810 MiB** for LoRA. Update-loop elapsed time was **9.75/10.02
  s**, excluding model load and digest checks; these are not arm rankings.
- The new learned capsule artifact is a **676-byte canonical manifest** and
  **74,040-byte SafeTensors** payload with SHA-256
  `75c1638c77aba79cc6e0c0fb5a05556f06bb7e9fcd586ad1a71889a6523b3da9`
  and
  `e5990f6d90a29a72f1df1b7dc82e1242a3078f781d6af7221cdfc453975dad16`.
  Fresh-process mounted score equaled the capsule training post-score and
  detached score equaled the pre-score; both absolute differences were **0**,
  below the predeclared `1e-4` tolerance. The fresh base digest was identical
  before/after. A separate read-only receipt script checked exact
  source/model identity, 16-step trajectories, scope flags, factor/base
  hashes, copied artifact bytes, and remount equality: narrow audit PASS.
- Metadata-only stdout SHA-256s (capsule, LoRA, remount) are
  `03083a385dddf625af3c7acb5e724f94f43d03edfa1f12d40644bee18473e00d`,
  `e0cae21caab3a0d6925bfa9a1709d70c5b16130de9add7db82f8e7a51c82ecc8`,
  and `6ff92634fa1fd56daed0e1213a840e2f9dc0e16fc34455e09c6cdcf220317b7c`.
  Stderr SHA-256s are
  `0f94630a6f42fe65b0c5595a7f32ec353f94dd2b7f5a71cf754f0f4d494c5ad8`,
  `419b108dcb2cc4051e5ecb8b2130016a38493a98febeaf7a6458b17e42e42761`,
  and `5be770d6bd4adf51ff65ccaf2fc0353a9bb761d5fcdfaf8dee6b370f3beafc26`.
  External-run and copied bytes matched by SHA-256; `.gitattributes` pins
  committed raw bytes. C: free space was **27.57 GiB** after the cells.
- This validates only local 16-update **synthetic** fit at 2,048 tokens on
  this host. It does not exercise full label-sequence loss, batch-16 gradient
  accumulation, 200 updates, real-data learning, held-out generalization,
  or a complete R0.4 feasibility envelope. The family-B prompt/budget is
  **not frozen**; source-rights, independent science review, R0.0, R0.4,
  and ALC-0 remain **OPEN**.

## 2026-09-30 — Full retained-cohort information audit implementation checkpoint 71

- An independent GPT-6 Sol scientific read-only review classified freezing
  the unchanged **2,048-token single-function family-B prompt as BLOCK**.
  The retained author-pair grid still has **311/4,344 train** and **26/482
  validation** opposite-label pairs with identical complete prompt IDs at
  2,048 tokens; at 8,192 tokens the counts are still **37/4,344** and
  **3/482**. This proves indistinguishability for those *pairs* under that
  input, not a final-cohort macro-F1 ceiling or learnability verdict. The
  2,048-token synthetic optimizer/remount result is resource/mechanism
  evidence only. The reviewer recommended an actual graph-retained full-cohort
  information audit before choosing a versioned pair-blind prompt candidate;
  no held-out data, real training, or source-rights conclusion was involved.
- Before full-data execution, added the exact non-authorizing diagnostic
  specification to the v2 draft. For unchanged source/graph/prompt and budgets
  **512, 1,024, 2,048, 4,096, 8,192**, the new tool computes complete prompt-ID
  equivalence classes on every retained train/validation observation, per-label
  truncation, opposite-label classes, affected components, and the exact
  prompt-only minimum classification error `sum(min(n_safe,n_vulnerable))`.
  It checks actual token-ID equality on repeated SHA-256 digests; source IDs,
  code, prompt IDs, and class membership are not emitted. This error count is
  **not** a macro-F1 bound, P1–P14 change, prompt selection, or training gate.
- TDD RED: the new fixture suite initially failed collection because the
  module did not exist. A later after-scan source-mutation fixture failed
  because the runner did not reverify source bytes. Both were followed by
  implementation and GREEN. Final focused JUnit
  `results/alc_r0_retained_prompt_information_focus_v2_20260930.xml` exited
  **0**, **19 tests, 0 failures/errors/skips**, time **3.394 s**, SHA-256
  `d6452ec6d5edcc930935f5970a75ab4ffdd57e20156bec264703312506c904c4`.
  Final broad ALC-R0 JUnit
  `results/alc_r0_retained_prompt_information_regression_v2_20260930.xml`
  exited **0**, **464 tests, 0 failures/errors, 8 skips**, time **218.710 s**,
  SHA-256
  `22e6230617f93b35bc77528313eccb1dc5b25c6b1f6865e0cbfcc33930b9f30b`.
  Ruff check/format and diff check passed. The superseded pre-recheck XMLs
  were local intermediate outputs and were removed before this checkpoint.
- Independent GPT-6 Sol read-only code/method review found **no correctness
  BLOCK** for the new exact-class/error arithmetic or pinned CLI provenance
  checks. It marked the unmeasured 200,063-row × five-budget runtime/peak-RAM
  as **WATCH** and noted that the direct Python helper accepts a caller-supplied
  tokenizer/digest: provenance assurance belongs to the CLI. The pinned
  full-development cohort tool has **not run** at this checkpoint; its receipt
  cannot yet support an empirical error-bound claim. A clean-code commit and
  fresh-process full-data CLI execution are next. R0.0, R0.4, and ALC-0 remain
  **OPEN**.

## 2026-09-30 — Bounded edit-token visibility reference checkpoint 72

- Implemented only in isolated Desktop worktree
  `.worktrees/alc-r0-edit-visibility-reference`, branch
  `codex/alc-r0-edit-visibility-reference`, starting from clean
  `66355527f9321b235084587855c23e3ec909fd30`. The separate live full-cohort
  audit checkout was not edited. No commit, push, or merge was performed by
  this implementation task; integration remains with the root coordinator.
- Wrote the fixture-only specification before implementation/execution in
  `docs/superpowers/plans/2026-09-30-alc-r0-edit-token-visibility-reference.md`.
  New pure helper `src/aluclu/alc_r0/edit_token_visibility_reference.py` computes
  all-shortest unit insertion/deletion distance, retained-edit endpoint marginal
  extrema, **directly optimized total extrema**, and four-bit reachable joint
  visibility signatures. Equal-token insertion/deletion alternatives remain
  eligible; no arbitrary diff traceback, prefix stripping, or substitution
  pairing is used. Both packed rows are reused; masks are exact-length buffers.
  Huge positive budgets take an all-one-mask early return, avoiding unbounded
  temporary-integer arithmetic. Returned metrics do not contain token tuples.
- Hard ceilings are **32,768 tokens per endpoint**, **4,194,304 DP cells**
  including boundaries, **five increasing positive code budgets**, and
  **64 MiB** conservative helper-owned scratch estimate. Per-call limits can
  only tighten them. Preflight cap failures return explicit resource-unresolved
  results with no partial distance/bounds; hard-oversized endpoints have null
  allocation estimates. Caller-owned inputs and whole-process RSS are outside
  this scratch accounting. Full-cell runtime and full-development practicality
  remain unmeasured; this helper contains no source-data runner or total-run cap.
- The independent fixture oracle recursively enumerates legal edit paths and
  filters complete paths to minimum distance; it shares neither DP recurrence
  nor retention/signature helpers. Exhaustive binary tuples of lengths 0..4
  give **961 endpoint pairs x five budgets = 4,805 comparisons**. Tests also
  cover hand changes, insertion/deletion, repeated-token ambiguity, endpoint
  symmetry, empty mathematical states, identity, full/nested retention,
  budget/input/cap validation, scratch arithmetic, byte-tokenizer prompt parity,
  and a million-bit positive budget. The decisive `[1,2]` versus `[2,1]` at
  code budget 1 gives marginal intervals `[0,1]`, total `[1,1]`, and signatures
  `{01,10}`: marginal maxima cannot establish simultaneous endpoint visibility.
- An initial environment attempt used older `research-envs/task27-py310` and
  failed collection on missing `rfc8785`; it was not a diagnostic RED or PASS.
  No dependency installation occurred. Switched to existing locked Python
  **3.12.13** at
  `C:\Users\kaann\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\ALUCLU\research\alc-r0-smollm2-135m-v1\windows-training\.venv\Scripts\python.exe`,
  with `PYTHONPATH=src`, `PYTHONDONTWRITEBYTECODE=1`, and pytest cache disabled.
  Intended RED then failed because the new module did not exist: exit **1**,
  one collection error, JUnit time **9.210 s**, `red.xml` SHA-256
  `e8c8e7643d75a43f5e9db7a65ea29d56a616b78cc3466204aa6195adf60c4b83`.
- Final focused GREEN command was
  `python -m pytest tests/test_alc_r0_edit_token_visibility_reference.py
  --junitxml=<external>/focused.xml -p no:cacheprovider`: exit **0**, **43
  tests**, no failures/errors/skips, JUnit **10.365 s**. SHA-256:
  `a42a4aa31501e30e774c91f000ca7ca4ad952ee5042ae3c6d060191f7249732f`.
  Final broad command was `python -m pytest tests -k alc_r0
  --junitxml=<external>/regression.xml -p no:cacheprovider`: exit **0**, **507
  tests**, **499 passed / 8 skipped**, no failures/errors, 1,060 deselected,
  JUnit **449.312 s** (pytest summary **449.47 s**). SHA-256:
  `786142468199c05286fe5a1cf9247b22988e8d21b1bdd5b67fd378c9707a98a7`.
  These external XMLs are under
  `C:\Users\kaann\AppData\Local\ALUCLU\evidence\edit-visibility-reference-20260930`.
  The earlier **498-pass / 8-skip** broad run preceded the final mask hardening
  and is preserved as `regression_pre_hardening.xml`, explicitly superseded.
  Final source/test bytes stayed fixed throughout the serial final runs.
- Final helper/test SHA-256s respectively are
  `e89334ccf8bd35a32fbca97075c9d3d082a3c2c1119f14d690b956cf28114072`
  and `217c5163e5d1a001539b49cca880bf35a0c5d32a05bcb0a57e0a4bcc92a0ecf8`.
  Ruff check, Ruff format check, and Git diff check passed on final files.
- Root's supplementary standard-library-only allocation probe loaded the
  final helper bytes directly, avoiding package/Torch integration. Its Python
  **3.12.13** metadata log was inspected and hash-verified: a two-million-bit
  budget with 2/2 tokens peaked at **3,412 traced bytes** versus **67,172**
  estimated; 0/32,768 tokens with five budgets peaked at **9,611,628** versus
  **9,673,408** estimated. Both were exact results with false authority/scope
  flags. Log:
  `C:\Users\kaann\Desktop\03_Projeler_Arge\ALUCLU\.research-evidence\edit_visibility_memory_probe_20260930\stdout.log`,
  SHA-256 `fc85072da2699f6a0e96e21b7c6887ba35f39d72a441785dca8be9311d6ba343`.
  This checks helper allocations in two fixtures, not process RSS, maximum-cell
  runtime, tokenizer/graph memory, or full-development feasibility.
- Root completion audit on 2026-10-02 re-read final helper/test bytes and
  personally verified the RED/focused/regression JUnit counts and SHA-256s
  above. Final XMLs are preserved byte-for-byte under
  `results/alc_r0_edit_token_visibility_{red,focused,regression}_20260930.xml`;
  the superseded pre-hardening broad XML is not promoted as final evidence.
  The allocation probe is reproducible with
  `scripts/alc_r0_edit_visibility_allocation_probe.py`; its aggregate stdout
  is `results/alc_r0_edit_token_visibility_allocation_20260930.stdout.log`.
  Independent GPT-6.1 Sol read-only code/method review returned **CLEAR** for
  the final bounded fixture helper. Four supplementary selected helper checks
  passed in 2.50 s using isolated module loading; ordinary reviewer package
  collection hit Windows `WinError 1455` loading Torch during memory pressure.
  That failed collection is not a helper-test result. Normal package execution
  is evidenced separately by the final 43-test and 507-test runs above.
- No raw development source or held-out data was accessed by this task; no
  source-data acquisition, tokenizer/prompt modification, real model forward,
  training, new dependency, threshold change, or final-budget choice occurred.
  This is token-position exposure, not vulnerability localization, semantic
  sufficiency, a macro-F1 bound, or learnability. A future both-retained-author-
  pair development runner and versioned equalized-arm prompt policy require
  separate review. Current family-B freeze remains **BLOCK**; P1-P14 are
  unchanged and R0.0, R0.4, and ALC-0 remain **OPEN**.

## 2026-10-02 — Full retained-cohort information audit terminal checkpoint 73

- Resumed by reading the full user objective and rechecking both Desktop
  worktrees, current command lines and durable artifacts. The 2026-09-30
  detached v3 audit was already terminal; no duplicate run was started.
  Root personally verified `status=python-exited`, `python_exit_code=0`, UTC
  start `2026-09-30T00:35:19.9471382Z`, end
  `2026-09-30T01:29:28.6304973Z` (about 54 minutes 9 seconds), every terminal
  split/budget progress line, and the complete canonical receipt.
- The receipt binds frozen source
  `66355527f9321b235084587855c23e3ec909fd30`, source-tree SHA-256
  `a22ef067d19fd7aba19f8c70c7a8b85418e0eef9359327cbf2241f1b169eb4c7`
  and 387 tracked files. The source checkout was still clean at that commit
  before evidence integration. Pinned source/pair/model and all four graph
  ledger hashes match earlier evidence. Graph progress ended at **209,857**
  rows and **19,874** candidates; retained populations are **177,291 train**
  (171,717 safe / 5,574 vulnerable) and **22,772 validation**
  (22,210 safe / 562 vulnerable). All ten ordered budget cells are present.
- Exact deterministic prompt-only minimum errors across the full retained
  populations, with complete-prompt opposing-label class counts in parentheses:

  | Common budget | Train minimum errors (classes) | Validation minimum errors (classes) |
  | ---: | ---: | ---: |
  | 512 | 1,463 (1,368) | 113 (112) |
  | 1,024 | 769 (728) | 56 (55) |
  | 2,048 | 353 (336) | 26 (26) |
  | 4,096 | 141 (135) | 7 (7) |
  | 8,192 | 41 (39) | 3 (3) |

  All per-label truncation, conflicting-observation/component counts and
  ordered-record roots are in the raw aggregate receipt. Root checked fixed
  budgets, population/label arithmetic, scope flags, digest format, terminal
  progress, and nonincreasing truncation/error counts. No raw code, IDs or
  prompt token sequences were emitted. `training_authority=false` and
  `held_out_data_present=false` throughout.
- Preserved byte-identical terminal evidence under
  `results/alc_r0_retained_prompt_information_6635552_20260930.*`:
  stdout SHA-256
  `9f2a0bec51c102be9c8588e9494f4b96013e56b9996aeb6b8eda45c4e9f0576c`;
  stderr SHA-256
  `c10ffe7be3b58beefb3824eb34ff2c8d1d1e811d079250f7120ea1fc779b7cbe`;
  exit-log SHA-256
  `f65721c0a2dd600cf9685be55a7f2628cedf2446df3ca4dff6d0f6c80d6afb8b`.
  The actual Windows launcher is archived as `.run.ps1`. The tokenizer's
  original-sequence warning `10382 > 8192` preceded the frozen head/tail
  retention; this diagnostic ran no model forward and terminal exit was 0.
- Evidence diff inspection reported the native v2 launcher error's preserved
  blank line at EOF. The existing raw-log attribute excluded line-end whitespace
  but not EOF whitespace. Added a narrow attribute for that exact archived log
  to preserve its original bytes; no log content was reformatted and source-code
  whitespace checks remain active. The full source/evidence diff check was then
  rerun before integration.
- Preserved unsuccessful execution attempts separately. The first session-
  coupled attempt produced empty stdout/stderr and no exit/receipt; its Python
  process vanished during a Codex sandbox-service interruption. A contemporaneous
  sandbox-service event was observed, but does not prove the termination cause.
  Its empty logs are `..._interrupted_20260930.*`. Detached v2 stopped at the
  first graph progress message because PowerShell `ErrorActionPreference=Stop`
  treated native stderr as `NativeCommandError`; its recorded launcher code
  **125** is not a pytest/model/scientific failure. Exact v2 logs and launcher
  are `..._launcher_v2_20260930.*`. Corrected v3 redirected native stdout/stderr
  directly, waited for the worker and captured its actual exit code; stdout-
  plus-stderr and intentional exit-3 probes had verified the launcher behavior.
- Independent GPT-6.1 Sol terminal/code/scientific-interpretation review returned
  **CLEAR for recording this diagnostic**, with **WATCH** on class imbalance
  and subsequent resource coverage. Safe observations comprise about 96.86%
  train / 97.53% validation: small overall error floors do not prove minority
  recall, macro-F1, semantic sufficiency, learnability or a preferred budget.
  This audit bounds deterministic same-prompt classification only. No new
  prompt policy, numerical threshold, test acquisition or training was approved.
- The fixture helper and final test evidence from checkpoint 72 were committed
  separately as `060d8bbec64781d8c29998a2112653b0938c708d`. Root reproduced its
  allocation probe from the committed script with exit 0 and byte-identical
  aggregate stdout. Explicit LF attributes now preserve helper/test/script
  executed byte identity across checkouts; raw evidence remains unfiltered.
  Relevant source/test hashes and final JUnit values remain those in checkpoint
  72. No helper logic or test was changed after those final runs.
- Next prerequisite is a separately declared metadata-only full-token length/
  cell-cost census of the same **4,344 train / 482 validation** both-retained
  author pairs, plus exact admission/unresolved semantics before a full edit-
  exposure runner. The 4,194,304-cell helper cap and proposed 100-million-cell
  total cap cannot be presumed to cover this population. Poor coverage must
  lead to an exact scalable method or explicit unresolved reporting, not silent
  subset selection or full-endpoint truncation. The family-B prompt freeze
  remains **BLOCK**; R0.0, R0.4 and ALC-0 remain **OPEN**.

## 2026-10-02 — Main-worktree integration checkpoint 74

- Fetched the exact remote work branch before integration: local and remote
  were both `66355527f9321b235084587855c23e3ec909fd30`, with the main Desktop
  worktree clean. Fast-forwarded `codex/unified-lifelong-cognition-desktop`
  through fixture commit `060d8bb`, full-audit evidence commit `304d3db`, and
  raw-log attribute fix `8fb745c`. No user changes were overwritten, and no
  live scientific process was stopped or replaced.
- Personally rehashed the integrated helper/test and full-data stdout: exact
  executed SHA-256s from checkpoints 72–73 were preserved. Explicit LF source
  attributes prevented platform checkout conversion from changing helper bytes.
- Main-worktree normal-package integration command on source commit
  `8fb745c8e80a86395bdf2efa1c2cbc4a976317e1`:
  `python -m pytest tests/test_alc_r0_edit_token_visibility_reference.py
  tests/test_alc_r0_retained_prompt_information.py --junitxml=<external>/focused.xml
  -p no:cacheprovider`, existing locked Python 3.12.13, `PYTHONPATH=src`.
  Exit **0**, **55 tests, 0 failures/errors/skips**, JUnit **12.118 s**
  (pytest summary 13.99 s). Byte-identical artifact:
  `results/alc_r0_edit_token_visibility_integration_20261002.xml`, SHA-256
  `6c5b04800fbaf84f572dd366afb235e9f95f6ee6505ae0d789c13b57f0b83eea`.
  The final broad 507-test receipt remains the unchanged-helper regression
  evidence from checkpoint 72; this integration check is additional evidence.
- Ruff check/format on final helper, tests, and committed allocation script
  passed. Root's allocation script reproduction exited 0 and reproduced the
  earlier aggregate stdout byte-for-byte. Full source/evidence diff check and
  staged byte identity checks passed after the narrow raw-EOF attribute fix.
- Rechecked the current unified plan's literal Task 2 CLEAN record at commit
  `4dca292`; the active dependency is still ALC-R0. The preceding diagnostics
  neither close R0.0/ALC-0 nor permit downstream product phases. Next work is
  the separately declared exact-DP resource-coverage census/protocol described
  in checkpoint 73, while prompt/rights/sealer/freeze gates remain open.

## 2026-10-02 — Retained pair resource census prerequisite checkpoint 75

- Implemented only in isolated Desktop checkout
  `.worktrees/alc-r0-edit-visibility-reference`, branch
  `codex/alc-r0-pair-resource-census`, base
  `59c936a4623e37dc215c67211e61944154cf92da`. The main
  `unified-lifelong-cognition-local` checkout was not edited. No commit, push,
  dependency installation, network, held-out acquisition, full-data census,
  dynamic program, model forward or training was performed by this work lane.
- Wrote the separate declaration
  `docs/superpowers/plans/2026-10-02-alc-r0-pair-resource-census.md` before code or
  fixture execution. It fixes the unchanged common grid and helper ceilings,
  complete normalized endpoint lengths/cell costs, and prospective global cap
  **100,000,000 cells**. Admission is train then validation, author-file order;
  the first locally eligible nonfitting pair permanently stops global admission.
  Every later locally eligible pair has `total-cell-budget-exhausted`, even if
  smaller than the remaining cap; local reasons retain endpoint/cell/scratch
  precedence. This is a simulation, not executed or resolved edit evidence.
- Added aggregate-only `src/aluclu/alc_r0/retained_pair_resource_census.py` and
  focused fixtures. The runner binds pinned development and paired bytes,
  rebuilds the unchanged graph, and requires all four prior ledgers. It keeps
  all survival categories and selects only both original endpoints retained.
  Full costs never truncate endpoints. Receipts preserve split-level universe,
  eligible/admitted/unresolved pair counts and cell sums, reason strata,
  disjoint fixed histograms and distinct-root unions. Component strata may
  overlap, while unresolved uses their union. Ordered internal digests bind
  source IDs/root, complete token commitments, lengths/cost and classification;
  raw records/code/IDs/token sequences/length vectors are not emitted.
- Independent GPT-6.1 Sol review fixes are incorporated: all author endpoints,
  including unselected categories, fail closed on malformed normalization;
  shared endpoints retain consistent content/label/split; full census cost
  dimensions must be exact positive integers. The helper's empty mathematical
  fixture support is unchanged, and an empty census universe has null coverage
  fractions. CLI checks the actual module `__file__` belongs to the recorded
  checkout both before work and before output; model bytes and clean Git state
  are reverified through an explicit fixture-testable terminal seam. Source and
  paired bytes are reverified after scanning. Synthetic snapshot/checkout
  fixtures use no monkeypatch or implicit global mutation.
- Preserved the actual absent-module RED and unsuccessful implementation-test
  attempts. Root copied each available receipt/log byte-for-byte into
  `results/alc_r0_pair_resource_census_*_20261002.*`, retaining these cases:

  | Evidence | Python exit | Cases | Failures | Errors | Skips | JUnit seconds |
  | --- | ---: | ---: | ---: | ---: | ---: | ---: |
  | `red` | 1 | 1 | 0 | 1 | 0 | 6.525 |
  | `green_v1` | 1 | 48 | 1 | 0 | 0 | 6.731 |
  | `green_v2` | 1 | 58 | 1 | 5 | 0 | 105.388 |
  | `green_v3` | 0 | 58 | 0 | 0 | 0 | 53.529 |

  RED is `ModuleNotFoundError` for the absent census module. Initial GREEN-v1
  had 47 passing fixtures and one overbroad no-leak assertion: `tokens_` also
  matched an allowed aggregate key. GREEN-v2 had 52 passing fixtures; Ruff's
  removal of an unused imported fixture caused five missing-repository setup
  errors, and a whitespace fixture expected a later error message although the
  input was already rejected earlier. Fixed the assertion to forbid actual
  fixture code strings, created an owned explicit repository fixture, and
  asserted malformed-input rejection without depending on incidental wording.
  These failures remain visible; they are not omitted from the evidence chain.
- Exact preserved JUnit SHA-256s:
  RED `0cae87c710afd4bcdbc438170a9e2cdaa945417e6aacf18eb8c29144ab0c76ab`;
  GREEN-v1 `0c8c5a90e6d3bb545bca037f43cb859abd0e08b657da1ea3c730a1849a6d7ab9`;
  GREEN-v2 `4fefc1396267b99ceb11651bfc3ba33399d1e77e4b174318a3ac0037fd08ca9b`;
  final focused GREEN-v3
  `74ba3b7ce25e0c541998e0d6b3a60e08dc5b2cc13d833e0a611bec9a815581ac`.
  GREEN-v2 stdout SHA
  `326681c68cf4720ed77ba52e2b1ff52ecc78b977e10aabce6909f3fe41189a91`;
  GREEN-v3 stdout SHA
  `9fcd4b5ed7d937389875c180a309e2fbc92b18e0220565e87e9509b479894f36`;
  both stderr files are empty, SHA
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
  Original external artifacts are under `C:\Users\kaann\AppData\Local\Temp`
  with the `alc-r0-pair-resource-census-...-20261002` prefix. Terminal exits were
  captured from returned process results; later external `.exit.log` notes
  transcribe those verified values and are not original launcher-generated logs.
- Focused GREEN-v3 used the existing locked Windows Python 3.12 environment,
  `PYTHONPATH=src`, `PYTHONDONTWRITEBYTECODE=1`, pytest cache disabled, and no
  concurrent test workers. All 58 fixtures passed (pytest 54.04 seconds),
  including exact 2047x2047/2048x2048 cell boundary, resource-reason precedence,
  total-cap equality/exhaustion through validation, shared-endpoint root unions,
  all survival categories, empty-universe null fractions, histogram boundaries,
  ordered commitment/no raw leakage, source/pair/model changes and changed
  source bytes/HEAD, normalization and module-origin rejection. Ruff check and
  format check passed on final source/test bytes before this run.
- Source SHA-256
  `31c6bea82c5599f397e75351bb6cd845d6075f5fd960fdff7a5a587951308df5`;
  test SHA-256
  `36c8c1a1442afb5d87a0d2eb898c9920475f714fdcb60daeae606ab2e435689d`;
  preregistration SHA-256
  `f46f336b8c841248521801288e747c31abb837e99193ad13d72de3294f017480`.
  Two independent GPT-6.1 Sol lanes returned final source **APPROVE** and
  architecture **CLEAR** at these hashes, limited to this no-DP prerequisite.
  Root personally checked final focused JUnit/hash evidence. Root added narrow
  LF attributes for new source/test/preregistration and raw `-text` attributes
  for census XML/log evidence without changing these executed source bytes.
- Serial broad `python -m pytest tests -k alc_r0 -p no:cacheprovider
  --junitxml=<external>/alc-r0-pair-resource-census-broad-v1-20261002.xml`
  completed with actual process-handle Python exit **0**. Terminal JUnit has
  **565 cases: 557 passed, 8 skipped, 0 failures/errors**, 346.243 seconds
  (pytest 346.34 seconds; 1,060 deselected). No census fixture skipped. The
  eight existing conditional skips require unspecified pinned Banking77/Devign
  development assets or the real offline SmolLM2 snapshot; this regression
  evidence makes no full-model or full-source execution claim. Worker command
  line was revalidated while live (start local 18:48:24, Python PID 30688,
  venv launcher PID 10508), with no restart or overlapping Torch-heavy tests.
  Root personally checked the terminal JUnit and byte-copied broad receipts to
  `results/alc_r0_pair_resource_census_broad_v1_20261002.*`. Broad XML SHA
  `87c7abed8a00be6d1b46f9a14946bbf7c5b7765606977a1322af92696555d1d2`;
  stdout SHA
  `900960420d13d33a91a63ddd20438ca8eb7d5d2c703c50d9a7ec001ccd489e4b`;
  empty stderr SHA
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
  Source/test bytes remain the final reviewed/focused-run hashes above; final
  source/evidence diff whitespace check passed before handoff.
- Root separately prepared an external production launcher under
  `.research-evidence/alc_r0_pair_resource_census_20261002`. Supplementary review
  found/fixed a preflight-versus-actual-commit receipt race: the final launcher
  parses the successful stdout source commit and rechecks terminal HEAD/clean
  state, distinguishing requested/receipt commit and Python/launcher exits.
  Updated script SHA
  `f39994cd9d0b7f24ef14d772e4eb975cce53e126233e867d64ac820e1aa2fd75`
  has PowerShell parser PASS and final supplementary rereview **APPROVE**. Root
  archived it byte-identically as
  `results/alc_r0_pair_resource_census_launcher_20261002.ps1` with a raw `.ps1`
  attribute. The prior
  script SHA `bd8d9af0c03b93bd07875e9261bd136a905301baf36b1eb3898f6f342f5f1301`
  was preserved with a requested-zero-commit rejection probe: launcher exit 125,
  no worker launched, no scientific result. This census has not been executed
  on development data. Launcher preparation/rejection evidence is distinct
  from the focused fixture evidence above.
- This prerequisite cannot authorize training or prompt freeze, choose a budget,
  alter P1-P14, claim an admitted cohort representative, or resolve code-task
  prompt sufficiency, rights/provenance, sealer, versioned validator or learning
  gates. The census fixes prospective denominator/admission reporting only;
  `training_authority=false`, `held_out_data_present=false`. Family-B prompt
  freeze remains **BLOCK**; R0.0, R0.4 and ALC-0 remain **OPEN**.

## 2026-10-02 — Census integration and execution freeze checkpoint 76

- Root committed the reviewed census, preregistration, checkpoint 75, narrow
  byte-preservation attributes and exact RED/failed/focused/broad evidence as
  `139f62f890d7f20d22d79e3c20a69c8014707cb2`. Fetched the remote work branch
  and fast-forwarded the clean main Desktop worktree from `59c936a` to this
  commit; no reset, force push, unrelated changes or live-process replacement.
- Personally rehashed the integrated module/test: executed reviewed bytes remain
  `31c6bea82c5599f397e75351bb6cd845d6075f5fd960fdff7a5a587951308df5`
  and `36c8c1a1442afb5d87a0d2eb898c9920475f714fdcb60daeae606ab2e435689d`.
  Main-worktree normal-package integration covered census, exact edit helper
  and retained-prompt information tests together, using the existing locked
  Python 3.12 environment, `PYTHONPATH=src`, bytecode/cache disabled, serial
  native stdout/stderr capture. Actual process exit **0**; **113 tests,
  0 failures/errors/skips**, JUnit **9.684 s**, pytest **9.71 s**.
- Preserved byte-identical integration evidence in
  `results/alc_r0_pair_resource_census_main_integration_139f62f_20261002.*`.
  XML SHA-256 `4205911ecfb28e365945db5ad1dfc690860b79a84b381753a60d9394f5723d9c`;
  stdout SHA-256 `20ba154bf659887828701927b279c4aab7f84d30ee102c4aacc2ca32380c5fbf`;
  stderr is empty. This is additional integration evidence, not a full-model
  execution or neural capability result.
- The isolated `codex/alc-r0-pair-resource-census` checkout remains clean at
  `139f62f890d7f20d22d79e3c20a69c8014707cb2` for the forthcoming development
  census. Main integration/evidence updates do not mutate that frozen checkout.
  Final launcher SHA-256
  `f39994cd9d0b7f24ef14d772e4eb975cce53e126233e867d64ac820e1aa2fd75`
  has parser PASS and independent code-review APPROVE; it binds actual successful
  receipt commit and terminal clean state, not merely a requested commit. No
  full-data result exists at this checkpoint. The prospective policy stays fixed;
  no DP, training, held-out access, prompt selection or threshold change is granted.

## 2026-10-02 — Frozen development resource census launched checkpoint 77

- After final focused/broad/integration verification and independent code,
  architecture and launcher approval, launched the prospective full-development
  census from the clean isolated checkout at
  `139f62f890d7f20d22d79e3c20a69c8014707cb2`. The main evidence/integration
  commit `00122cf16398ef779f1f7b2dad24806dea0d158d` was pushed and its remote
  ref independently matched before launch. No source file in the scientific
  checkout is modified during execution.
- Actual detached launch UTC `2026-10-02T15:59:55.1817867Z`; wrapper PID 512,
  venv launcher PID 18292, Python worker PID 33728. Root revalidated full process
  command lines and the launch record, not merely saved PID hints. The command
  is `python -m aluclu.alc_r0.retained_pair_resource_census` with only the pinned
  original train/validation directory, adjacent paired development directory,
  and pinned offline SmolLM2 tokenizer snapshot. Native output redirects,
  offline flags, bytecode disabled and expected-commit/clean-source checks are
  active. No test split, model forward, edit DP or training is admitted.
- Authoritative external evidence directory:
  `C:\Users\kaann\Desktop\03_Projeler_Arge\ALUCLU\.research-evidence\alc_r0_pair_resource_census_20261002`.
  Inspect `stdout.log`, `stderr.log`, `launch.log`, and eventual `exit.log`.
  At launch verification stdout/stderr were empty and no exit receipt existed;
  this is **LIVE / PENDING**, not PASS. Terminal acceptance requires actual
  Python and launcher exit values, receipt commit/tree identity, four graph
  ledgers, expected survival counts, fixed prospective cap/admission accounting,
  false authority flags, exact aggregate commitments and SHA-256 verification.
  A resource-unresolved population must remain explicit; no coverage claim is
  inferred from the fixture pass. Keep the frozen checkout untouched and do not
  restart this attempt because an observation times out.

## 2026-10-02 — Terminal resource census and negative coverage checkpoint 78

- The frozen development census completed, not restarted: UTC
  `2026-10-02T15:59:55.1817867Z` to `2026-10-02T16:08:04.7823639Z`
  (489.601 s). Personally read the terminal receipt: Python exit **0**, launcher
  exit **0**, requested and actual receipt source commit both
  `139f62f890d7f20d22d79e3c20a69c8014707cb2`. The isolated checkout remains
  clean at this commit; receipt source tree is
  `d05ff530d4ec580653966c39150eb2631b8678466134e2063d37c7647b168cb8`
  over 423 tracked files. No edit DP or neural model forward was executed.
- Preserved raw terminal artifacts byte-identically as
  `results/alc_r0_pair_resource_census_full_139f62f_20261002.*`.
  SHA-256: stdout `f22d2ca92f9a012b6d2d1cea012b5d74649c2816b983825fa68f91bab1809aae`,
  stderr `16b465baa4133be1dcdc062d5560d0e0b97478ab4598fca02bfb49ddae348438`,
  exit `7017e6a46932ab52137496b9c3101345dd44c536060c454725b24a4f954f568c`,
  launch `2f5ca77f364e1d96f0ce41184d343b90d04c787e2ab1fbf626e9553efdf83191`.
- Both-original-endpoints-retained universes are **4,344 train / 482 validation**,
  from 4,354 / 562 author pairs. Locally eligible counts are **3,384 / 408**.
  Prospective admission is **137 / 0**; unresolved is **4,207 / 482**.
  Unresolved reasons (train / validation): endpoint ceiling **7 / 0**, rectangular
  cell ceiling **953 / 74**, scratch ceiling **0 / 0**, permanent global
  exhaustion **3,247 / 408**. Admitted cells **99,371,935**, remaining
  **628,065**, sum exactly the preregistered **100,000,000**; exhaustion is true.
  Zero validation admission follows train-first ordering, not zero eligibility.
- The complete rectangular universe totals **137,599,268,320 cells**. Maximum
  endpoint lengths are **272,858 train / 24,941 validation**. Train component
  unions: universe 4,129, admitted 135, unresolved 3,999; validation universe
  and unresolved 476. These unions overlap and are not independent votes.
  Only 137/4,826 pairs (approximately 2.839%) are prospectively admitted;
  there is no representative-subset or whole-universe exposure claim.
- Root terminal bookkeeping independently rechecked canonical RFC8785 bytes,
  clean source identity, pinned model/pair commitments, all four graph roots,
  policy hash `050b4dc1e7ec6164f510340adf60d838e9039b765adf97a2e556f8ae86cda815`,
  survival/count/cell/histogram accounting, fractions and resource-cap totals.
  External supplementary verifier (not a production or scientific gate),
  `.research-evidence/alc_r0_pair_resource_census_terminal_verify_20261002.py`,
  SHA-256 `cc359414888380c4a35bab1556ddcde65fd5b53377a64123ee76ea6a7770785a`,
  reran with enabled-assertion guard and actual exit **0**. Independent GPT-6.1
  Sol evidence review returned **CLEAR for recording the diagnostic** after
  separate receipt/hash/arithmetic/source checks, without raw-data rebuild.
- Stderr includes an 8,733-token tokenizer length warning against 8,192;
  this execution encodes full endpoints only, never forwards them through the
  model. It is not a model execution failure. All endpoint totals completed.
- This is a negative **resource-coverage** result, not hypothesis falsification,
  edit resolution, semantic visibility, prompt sufficiency, budget selection,
  freeze permission or learning PASS. `training_authority=false` and
  `held_out_data_present=false`. Family-B freeze remains **BLOCK**; R0.0,
  R0.4 and ALC-0 remain **OPEN**. Do not spend an exposure run on the admitted
  train prefix and infer population coverage from it.
- Next: preregister and fixture-validate a separate exact indel-distance plus
  all-optimal-path banded exposure method. The original rectangular policy and
  negative evidence remain intact; new band/distance resource accounting is a
  new method, not reinterpretation of the old cap. Corpus distance/exposure
  execution, native execution and enlarged endpoint ceilings remain separately
  unapproved until their prerequisites and independent reviews are satisfied.

## 2026-10-02 — Exact bounded-band fixture preregistration checkpoint 79

- Before new helper code, tests or fixture execution, declared the separate
  threshold-K reference in
  `docs/superpowers/plans/2026-10-02-alc-r0-banded-edit-visibility-reference.md`,
  SHA-256 `3cfe062e9cdcfdd0a4b46e8c106e6462d110f4feebdc3a2b9375a01b03dec611`.
  Root read the full declaration and preserved its bytes with narrow LF
  attributes. Both independent GPT-6.1 Sol lanes returned exact-byte design
  **APPROVE / architecture CLEAR**. This is design readiness, not helper PASS.
- Every path of cost <=K must satisfy |i-j|+|n-m-(i-j)|<=K. The clipped
  parity-safe band therefore preserves all global optimal paths when the
  computed terminal distance is <=K. Preserve all tied primary-optimal edges,
  even at equal-ID cells; propagate marginal/direct-total bounds and genuine
  joint signatures separately. No prefix/suffix stripping, selected traceback,
  full-DP fallback or adaptive retry is permitted.
- New per-call semantics: threshold 0..512, exact scheduled band cells <=
  4,194,304, endpoints <=32,768, <=5 budgets, conservative scratch <=64 MiB.
  The old rectangular helper/census remains unchanged. Compact two-row packed
  buffers use guarded global-column intervals; scheduled versus visited work,
  allocated payload versus scratch estimate, and preflight versus terminal
  threshold failure remain explicit. Unresolved results disclose no partial
  distance or exposure. No corpus-coverage or process-RSS claim follows.
- Preregistered synthetic long cases include length-10,000 identity K=0
  (10,001 cells versus 100,020,001 rectangular cells), a unique insertion K=1
  (20,002 cells), and repeated-token all-alternative exposure. Independent
  exhaustive path enumeration, unchanged-reference parity, geometric/resource
  boundaries, allocation checks and targeted mutations are required before
  validation. Next is absent-module RED, then implementation and focused/broad
  regressions plus independent final source review, with all outcomes preserved.
- No new test/code execution at this checkpoint; no dataset/tokenizer/model,
  training or held-out access. This diagnostic prerequisite does not satisfy
  Family-B freeze, R0.0, R0.4 or ALC-0; those remain BLOCK/OPEN as recorded.

## 2026-10-02 — Bounded-band implementation checkpoint 80, validation OPEN

- The implementation agent remained pending-init without creating code/test
  files; a separate reviewer attempt returned a usage-limit infrastructure
  error. Root verified the empty implementation state, interrupted the pending
  agent and explicitly took ownership. No live pytest was replaced. Independent
  final source review remains required; design approval is not source approval.
- Root wrote the new test first and ran the absent-module RED in the existing
  locked Windows Python 3.12 environment. Actual pytest exit **2**, expected
  ModuleNotFoundError, one collection error. Only afterward wrote
  `src/aluclu/alc_r0/banded_edit_token_visibility_reference.py`: compact packed
  rolling rows, exact clipped parity-safe band, all primary-optimal ties,
  direct totals and reachable signatures. The old helper remains unchanged.
- Initial focused run: actual exit **0**, 10 cases passed. Then expanded tests
  before rerunning to binary lengths 0..4, five budgets and all small thresholds
  against both a separate recursive all-path oracle and the rectangular helper.
  Added independently counted small band geometry, long length-10,000 identity,
  repeated-token insertion, unique insertion, giant budgets and malformed inputs.
  A traced five-budget unique-insertion fixture checked helper peak <= declared
  scratch estimate; this is not process-RSS or corpus-resource evidence.
- Expanded focused run actual exit **0**, 18 cases passed. Raw RED and v1/v2
  stdout/stderr/XML/exit records are external under
  `.research-evidence/alc_r0_banded_edit_visibility_20261002`. Root observed
  process completion and read terminal outputs. Current source SHA-256
  `dff2a30af16daa97dd0acd1ab39fe89403b35b6a4b181c95f7bf5db21f707f8d`;
  tests `61e54792fb630a4edb898b1fae7b69dd516525ec315c0e1a70677615fc9ea9b1`.
  Ruff formatting and lint passed after one import-order correction.
- Root added narrow LF/source and raw XML/log Git attributes, and synchronized
  the non-authorizing PrimeVul v2 draft with the completed census and pending
  band-reference status. No thresholds, corpus authority or old policy changed.
- Validation remains **OPEN**: independent implementation code/architecture
  rereviews, serial relevant regressions, remaining preregistered boundary/
  ternary/swap/allocation cases and targeted mutation checks are not yet fully
  satisfied. No native backend or corpus DP, tokenizer/model call, training,
  held-out access, prompt-freeze or learning PASS follows from these 18 cases.
- Independent code review initially requested completing preregistered fixtures;
  architecture found no source blocker but WATCH on validation. Root therefore
  added ternary oracle, endpoint swaps/signature remapping, nested/all-retained
  checks, invalid/relaxed limits, K=512, tighten-to-zero, endpoint 32,768/+1,
  exact payload and traced empty/giant-budget/maximum-width-513 cases, without
  changing implementation or preregistration. Expanded GREEN-v3 actual exit
  **0**, **28 cases, zero failures/errors/skips**, JUnit **136.460 s**;
  XML SHA-256 `76bf6a8dc4311904d375acf581202819d63cb2ab50b1bf13cba2a8bf5ec0b0b9`.
  Final expanded test SHA-256
  `338605d6d18c584e830305d24e22c85c2bd42d10a7519a3f07bd8af376835a79`.
- The new isolated fixture mutation probe, SHA-256
  `e3c90674dcaa0927e661a2b240d1a9773a71d03e6999c3a48f2ca3f1b05365f1`,
  completed with actual exit **0**: unmodified control **1,470** cases and
  all **nine** declared mutants killed. Each replacement anchor is checked
  exactly once; malformed harness/import/infrastructure failure is not accepted
  as a kill. It alters only in-memory, uniquely named disposable modules, never
  production files, and compares dimensions/distance/complete exposure fields
  against a recursive oracle. Stale-column mutation's observed first killer
  is `(0,) / (1,1), K=2`. Output SHA-256
  `33c17f29dfdd01ebc43fba5091260b8ecfea226883553073ebdba0797ec0b086`.
- Preserved RED, GREEN-v1/v2/v3 and mutation raw XML/log/exit bytes as
  `results/alc_r0_banded_edit_visibility_*_20261002.*`. RED XML
  `28bbc0e3a38e2bcdc978031c690a1851c4a950de4a0c2bdc4ef76bb5e9fe563a`;
  GREEN-v1 XML `91190684a897f63cf24d20f56a9586ce9a01ffd4cf94eb537b35d4b69931a696`;
  GREEN-v2 XML `5d131fdc0de6a8de68a8c076e1f8ab1b32ee7a6fd476ac0aee3e981d8e63e545`.
  Superseded smaller runs remain evidence, not final regression certification.
- Serial relevant `pytest tests -k alc_r0` regression launched after focused and
  mutation processes terminated, wrapper session **63515**, initial venv PID
  **18456**; inspect actual processes and external `regression-v1.*` artifacts.
  Final source/evidence independent rereviews requested. Broad regression and
  final review completion are **PENDING**, not PASS; preserve the live run.
- Final exact-byte independent GPT-6.1 Sol source/test/harness reviews returned
  **APPROVE / architecture CLEAR**. The code lane also independently inspected
  terminal focused/mutation receipts and hashes; the architecture lane inspected
  source/hashes but did not inspect runtime artifacts. Its interpretation limit
  remains explicit: an IndexError-killed parity mutant proves detection of that
  concrete corruption, not every similar incorrect algorithm. Broad regression
  is still pending, so this checkpoint is not overall validation completion.

## 2026-10-02 — Banded reference terminal regression checkpoint 81

- Preserved the same serial regression session 63515 until terminal completion;
  root observed actual pytest exit **0**, then personally read stdout/stderr and
  JUnit. **593 cases: 585 passed, 8 skipped, 0 failures/errors**, JUnit
  **223.344 s**. The 8 skips are existing Banking77/Devign/real-model tests whose
  asset paths were not supplied, not new-helper skips. The run includes all
  28 banded tests plus the old rectangular helper, retained-pair census and
  retained-prompt information tests. This is relevant ALC-R0 regression,
  not the full project suite, model capability, corpus visibility or portability.
- Archived exact terminal evidence as
  `results/alc_r0_banded_edit_visibility_regression-v1_20261002.*`:
  XML SHA-256 `43472ed12a6198ceeb314c24d756680364c09ea2ff5cee02fe6f561af5aeb32e`,
  stdout `6212f8bc782f174d29b88fda955e6b7573cfadd511090e19aa4c0a81a85b4262`,
  empty stderr `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
  Root recorded actual exit in the external receipt before copying. No
  restarted/partial run is substituted for this completed attempt.
- The regression started before checkpoint-80 commit, so it is not claimed as
  a clean-start frozen-checkout run. Root rehashed source, tests and mutation
  probe before/after terminal: reviewed bytes remained dff2a30a / 338605d6 /
  e3c90674 respectively and were committed/pushed in
  `cce8cbf1509f2c9e392a65c54e83344d9f883bd8`. No code/test change occurred
  during execution; checkpoint/evidence commit did not replace their bytes.
- Focused oracle/full-reference/geometric/allocation evidence, nine mutation
  kills, relevant regression and exact-byte independent code/architecture
  reviews support the **synthetic mathematical reference** only. Final terminal
  evidence rereview is requested separately before recording its completion.
  No inference of full-development coverage, semantic sufficiency, prompt
  budget selection, freeze authority or neural learning follows.
- Read-only native tooling preflight found Visual Studio 2022 Build Tools and
  MSVC `14.44.35207/bin/Hostx64/x64/cl.exe`, file version `19.44.35228.0`.
  This is installation evidence, not a successful compilation or performance
  claim. A separately owned fixture-only native design is being prepared;
  no compiler installation, native build or corpus/model execution occurred.
- Independent GPT-6.1 Sol terminal evidence reviewer returned **CLEAR** after
  personally checking exit, XML counts/included modules, all skip reasons,
  logs/hashes and unchanged reviewed source bytes. The reviewer checked a clean
  cce8cbf snapshot before root added this checkpoint/evidence; this is not a claim
  that the later bookkeeping changes were absent. The fixture-only reference
  validation scope is now complete. Source/evidence provenance retains the
  pre-commit launch limitation above. ALC-R0/ALC-0 and the whole program remain
  **OPEN**; source rights, sealer, prompt sufficiency and versioned freeze are
  not satisfied by completing this helper.

## 2026-10-02 — Native fixture design revision checkpoint 82, no implementation

- After the Python mathematical reference completed its declared synthetic
  validation, drafted a CPU-native optimization slice before any native code,
  tests, build or timing. The initial process-per-fixture standalone proposal
  was challenged by root and independent review: thousands of fixture process
  launches and bounded wire/capture machinery add avoidable overhead/surface
  for a locally authored trusted analysis kernel. No timing outcome was used
  to choose the revision; no speedup is presumed.
- Preserved the original draft byte-for-byte as
  `docs/superpowers/plans/2026-10-02-alc-r0-banded-native-standalone-draft-superseded.md`,
  SHA-256 `eaf55dd06e82a4e51108b3f42051ba034d28c59b96e5ddda64f17cc8e6233a8f`.
  Revised declaration
  `docs/superpowers/plans/2026-10-02-alc-r0-banded-native-fixture-design.md`,
  SHA-256 `0cac0b1ac5f70bc7a3167a43d232672d90aed5eec168d0bd1fd150380fa3e3f3`,
  selects one locally built trusted DLL, a fixed C ABI and explicit ctypes
  adapter. Root read the full final declaration. Independent GPT-6.1 Sol code
  review returned **APPROVE for design readiness only**, after resolving exact
  build-ID export, workspace alignment/capacity, empty-rank and no-write rejection
  contracts. This is not native source/build or execution approval.
- Preserve all existing endpoint/K/budget/cell/scratch ceilings and the reference
  result semantics. Rank-map arbitrary Python integers bijectively, saturate
  giant budgets without merging original slots, keep all shortest-path ties,
  and validate checked ABI buffers/workspace/output independently. Unsafe
  pointer/crash probes are child-isolated; no foreign artifact or arbitrary
  native payload is accepted. Source/build/DLL/load identity and all overhead
  exclusions must be explicit. The DLL is not a sandbox or host-compromise defense.
- Declared RED-before-implementation, complete oracle/reference parity,
  negative ABI/artifact/resource checks, and four fixed synthetic timing cases
  (2 warmups / 5 measured repetitions). Kernel, mapping, marshalling, load and
  end-to-end costs must remain separate; no corpus/learning/portability or
  speedup claim exists before actual evidence and independent final review.
- Local read-only tooling evidence: compiler file SHA-256
  `88c8344236a27a6e727e0a8edc49aaa2690bdc7a9464b9d18cc7abe70a9f1c0d`,
  linker `ca11e6c45debd34bf652dfe984c5360a531a005ed78bf72852330c9c2590cf0d`,
  versions 19.44.35228.0 / 14.44.35228.0; Windows SDK include/lib 10.0.26100.0
  directories exist. No compilation or installation was performed. Native
  implementation/execution remains **PENDING** and has no corpus, tokenizer,
  model, training, held-out or prompt-freeze authority.
- Architecture final design verdict **CLEAR** applies to the same 0cac0b1a
  bytes. Explicit implementation traps retained: endpoint rejection before
  rank/buffer allocation, native oversized transport counts before scans,
  pointer accessibility not inferred from count validation, and mathematical
  signed floor/ceil rather than C++ negative division truncation. These require
  actual RED/parity/negative-test evidence; they are not waived by design approval.

## 2026-10-02 — Native fixture implementation RED checkpoint 83, not acceptance

- Continued from clean design commit `7db18f8e4450d029feea70df2ffd8df1d0e0ffb7`
  in the authoritative non-OneDrive Desktop worktree. GPT-6.1 Sol implementation
  ownership is restricted to the native translation unit, explicit Python
  adapter, build script and fixture tests. No native compilation is authorized
  before independent source review and a clean source commit.
- Initial absent-backend test invocation had a package-path infrastructure
  error; retain it as infrastructure evidence, not the intended RED. Corrected
  `PYTHONPATH=src` invocation produced the intended missing
  `aluclu.alc_r0.banded_edit_token_visibility_native` import error. Worker reports
  actual pytest exit 2; root independently read stdout and JUnit XML: 1 case,
  1 collection error, 0 failures/skips, time 2.549 seconds. Exit provenance is
  worker-observed, not an independent exit watcher.
- Raw RED evidence remains external in
  `C:/Users/kaann/Desktop/03_Projeler_Arge/ALUCLU/.research-evidence/alc_r0_banded_native_20261002/`.
  Corrected `native-red-v2.xml` SHA-256 is
  `2ea7a02d00f84d09a992fd766cda8bad77e3a7ac511e0b738aeddc86bd1fb347`.
  Preserve both attempted runs; do not replace the first with a fabricated
  successful launch or reuse this collection failure as native parity evidence.
- Added narrow LF attributes for the four authored source/test/build files and
  raw-byte attributes for prospective native XML/log evidence. `git diff --check`
  passed. This bookkeeping prevents checkout newline conversion from silently
  changing source/build or evidence identity; no DLL receipt exists yet.
- C++ and adapter implementation is in progress and is not review-ready.
  Loader identity, impossible-output rejection, complete oracle/parity,
  negative ABI/resource tests and mutation coverage remain required. No build,
  native execution, benchmark, corpus access, model run or learning result is
  claimed. Family-B freeze and ALC-R0/ALC-0 remain OPEN/BLOCK as previously recorded.
- Root ran two Python-only prebuild tests against the in-progress adapter:
  arbitrary-integer rank bijection and missing-receipt infrastructure rejection.
  Actual pytest exit 0; independently read XML: 2 passed, 0 failures/errors/skips,
  time 1.906 seconds; external `native-python-prebuild-v1.xml` SHA-256
  `08bf9cbe5ed564970754aebf5c1353b34be0978b1c946267e15b28ee3173f88a`.
  Command: locked Windows Python 3.12, `PYTHONPATH=src`,
  `PYTHONDONTWRITEBYTECODE=1`, pytest `tests/test_alc_r0_banded_native.py`
  `-k 'rank_bijection or missing_receipt' -q -p no:cacheprovider`, external
  `--junitxml` path above. No native receipt/DLL was supplied or loaded. This
  small check does not satisfy the still-pending native parity/security gates,
  and its source was not frozen at launch.
- Root explicitly probed the in-progress build script's dirty-checkout rejection
  with `--output-dir` pointing to external `dirty-preflight-probe`. Observed
  Python exit 1 and `RuntimeError: clean committed reviewed source required
  before build`; output directory still did not exist afterward. The script
  rejected before directory creation or compiler invocation. This proves that
  particular dirty-launch guard, not build success or mid-build consistency.
  Source review additionally requires start/end commit/tree/source-byte
  consistency and complete compiler/linker/log/environment provenance.

## 2026-10-02 — Native prebuild source review and decoder repairs checkpoint 84

- Implementation worker stopped four authored files without compilation/load.
  Root confirmed initial source hashes: C++ `c577846b7f5de113230b89224d96a707eceecaf7659cad2b316d2138201f96ad`,
  adapter `892ea1d0803a9ffefaec973d0799b9b68c077c17c0650c1eb7925130f9d951b7`,
  build script `8f83edff73ba8d82bc03f33b49df7e802abe19c631177fa7c44a01c58b0f7770`,
  tests `3e706895de9ce6debbb1ce05e8faedba5f940bc04bbb0ea8b555b20264a606d7`.
  Intended RED exit2/provenance files now exist externally and were read by root.
- Independent GPT-6.1 Sol code review returned **REQUEST CHANGES** for prebuild
  readiness: decoder lacked D<=n+m and independently bound preflight status/
  reason precedence. Root reproduced impossible exact D=2 for two empty inputs
  with a private fake transport, without a DLL/build/load. Architecture dispatch
  failed with `agent thread limit reached`, including after idle phantom-agent
  interruption. Independent architecture review is unavailable, not CLEAR;
  first build/source acceptance remains gated, with no self-review fallback.
- Root added data-only private-response decoder tests: 7 RED cases failed at
  exit1 (0 errors/skips, 2.309 seconds), XML SHA-256
  `f806f8a6911419263ae22983af19ee9190da4507b51dbc93444d5b3151207b56`.
  Patched independently expected endpoint/threshold/cells/scratch rejection,
  exact implies admission, admitted unresolved allows completed threshold only,
  and D<=min(K,n+m). Intermediate GREEN passed9, exit0, time2.645 seconds,
  XML `d75e0fd48bb416976b698fc512b8efbd0ee2f109178382b93cd7dad6c866adaa`.
- Three additional exposure corruption tests failed before their fix (exit1,
  3 failures, 0 errors/skips, 2.339 seconds), XML
  `c6655f98dfaa80ae4210628fc498b26e212d3b3c474e01fa2c902606364b6691`.
  Added necessary total/marginal and distance upper-bound constraints, not
  inferred exact totals or joint signatures. Final data-only GREEN passed13,
  exit0, 0 errors/failures/skips, 2.753 seconds, XML
  `c7bba1e5bf7dde015b53ba9e8e117ebd4c1124635b0d38f7cae567a59854c5c7`.
  Includes unmodified binary length0..3 response controls across thresholds,
  preventing a reject-everything validator from satisfying only corruptions.
- Tests/receipts remain external under the native evidence directory from
  checkpoint83. Runs used locked Python3.12, PYTHONPATH=src, bytecode/cache off,
  pytest selection `data_only or rank_bijection or missing_receipt`. Actual
  exit codes were observed directly; XML counts/hashes independently reread.
  After Ruff formatting/check success, repaired adapter SHA-256
  `b1210fbdef91f53b0fa5dc485f9922aefe36e13b7069ec88059e5b5a4c219983`,
  tests `38095b5505221c4df12acef3f3905796f327ea2089ed2ca732790877fe8d7ad4`.
  C++/build hashes unchanged; exact-byte code rereview requested. Build start/
  end identity checks detect persistent changes, not necessarily transient
  changed-and-restored compiler input; do not claim stronger provenance.
- Native nine semantic mutations, timing instrumentation, fuller ABI/resource/
  corner tests, actual parity and broad regression remain OPEN. No native
  acceptance, learning, corpus coverage, prompt-freeze or portability claim.
- Independent code/spec/security rereview returned **APPROVE for prebuild
  readiness only** on the repaired hashes above; both validator blockers are
  resolved. Architecture remains unavailable, so combined approval is withheld.
  Root launched a serial prebuild regression including all28 banded reference
  tests plus13 selected data-only native-adapter tests, with no DLL receipt/load.
  Session94507 was observed live; terminal outcome is not yet recorded here.

## 2026-10-02 — Native prebuild regression terminal checkpoint 85

- Resumed the same session94507 rather than restarting. Root confirmed actual
  live Python command lines and unchanged reviewed source hashes before the
  terminal check. Final shell output recorded `pytest_exit_code=0`; session
  completed normally with exit0. Root then read the completed XML independently:
  **41 passed, 0 failures/errors/skips, 80.929 seconds**. Module counts are
  exactly28 banded reference tests and13 selected data-only native-adapter tests.
  XML SHA-256 `2acdba2fa72955f2f662fc7e85568954081ae56c9087ea249ceaff96671d6483`.
- Canonical external evidence is `native-prebuild-regression-v1.xml` under
  checkpoint83's evidence directory. Selection was
  `test_alc_r0_banded_edit_token_visibility_reference or data_only or
  rank_bijection or missing_receipt`, cache/bytecode off, locked Python3.12.
  This is a prebuild reference/decoder regression, not actual DLL parity or
  the entire ALUCLU suite. No native receipt/DLL was supplied or loaded.
- Independent GPT-6.1 Sol architecture lane successfully launched on the same
  corrected source hashes after previous agent-thread-limit dispatch failures.
  Its verdict is pending. Preserve the earlier unavailable state as historical
  evidence; successful dispatch alone is not CLEAR. No native build started.
- Root preserved 15 raw RED/GREEN/regression/provenance artifacts in `results/`
  under prefix `alc_r0_banded_native_`, verifying each copy's SHA-256 against
  the external original. Added raw-byte attributes for the provenance `.txt`.
  Initial package-path failure is retained separately; later successful tests
  do not overwrite RED evidence. Regression exit record SHA-256
  `9c1b214135fe0e1519ffeb9d3a57b48192be2a354b09660a92112dab17ef53da`
  explicitly identifies a root-witnessed terminal record, not a separate watcher.

## 2026-10-02 — Independent native architecture WATCH checkpoint 86

- Independent GPT-6.1 Sol architecture reviewer read design, all four source/test/
  build files and immutable Python reference; hashes matched checkpoint84's
  repaired bytes. Verdict: **WATCH scoped first synthetic build readiness**,
  no architectural blocker in all-ties mathematics, ABI, checked workspace or
  caller-owned buffer path. This is not CLEAR or native acceptance. Combined
  code-review skill verdict is **COMMENT**, not APPROVE, while WATCH remains.
- Three explicit residuals: successful backend instances retain Windows handles
  and locks for process lifetime without a release API; loader validates fewer
  receipt provenance fields than build records; compiler/linker hash sampling
  occurs after execution. Trusted local DLL loading is not a sandbox or safe
  acceptance of arbitrary external DLLs. No administrator-compromise guarantee.
- Root resumed the GPT-6.1 Sol implementation worker on the same four-file scope
  to document bounded fixture-process lifetime, validate strict required build
  provenance before native load, and capture/compare tool identity before/after
  build. An external exact-byte C++ source snapshot can close the reviewed
  transient-input ambiguity without changing kernel semantics or ceilings.
  Require data-only RED/GREEN tests and fresh exact-byte independent reviews.
  No build/load/commit/push is authorized in that worker handoff. Root retains
  trajectory ownership. Native acceptance and all scientific gates remain OPEN.

## 2026-10-02 — Receipt validation RED checkpoint 87, bookkeeping only

- Root read the new external `receipt-red.stdout.log` and JUnit XML. Collection
  failed on absent `read_build_receipt`, before native build/load: 1 case,
  1 error, 0 failures/skips, time1.994 seconds, XML SHA-256
  `e44c3615b0be33f98fb5e51d5e091a763526edb50a231a4ec1243cf9706077d5`.
  Actual worker exit/provenance still needs separate verification; XML alone
  is not proof of that exit code. This RED is distinct from the old absent
  adapter RED and does not establish successful provenance validation.
- Receipt/tool-source snapshot repairs are still authored in the four owned
  files. Root requested private per-test native proxies instead of mutating the
  shared module-scoped DLL function. No worker trajectory edits or native build.
- Preserve prior completed reference/decoder test evidence and checkpoints83–87
  in a bookkeeping-only commit, excluding all four in-progress source/test/build
  files. This changes HEAD but is not a clean native source freeze, approval,
  native acceptance, model run or prompt/training authority. Re-run current
  data-only tests and exact-byte independent review after the repairs stabilize.

## 2026-10-02 — Native provenance repairs and Windows byte-format checkpoint 88

- Worker completed strict data-only receipt parsing/provenance validation before
  loading; exact source allowlist/current and committed bytes/tree, false flags,
  snapshot/include/tool/log/command/environment/status binding. Bounded fixture
  process retains one backend (including post-load failures); no premature close.
  Private per-test proxy replaced shared DLL monkeypatch. Build compiles an
  external exact-byte C++ snapshot with snapshot/include deny-write/delete read
  handles and compares compiler/linker hashes/versions before/after execution.
- Root read worker exit records, stdout/provenance and XML: receipt RED exit2,
  1 collection error1.994s, e44c3615 hash from checkpoint87; first GREEN exit0,
  18 passed4.008s, XML `90b31fdd38b6838ed80c716628fb37777253f5c18f1db04adec8cedeef53200a`;
  final worker GREEN exit0,26 passed3.209s, XML
  `dbe39beda1418a3d3a0260418600bd3acf03196919ed36e07bd44352483af120`.
  Zero failures/errors/skips for GREEN. Malformed/basic full-key receipts exercise
  early rejection only: no complete successful receipt positive control exists
  before the actual first build. Do not infer deep acceptance from those tests.
- Both independent review lanes found a new Windows producer/consumer mismatch:
  default Path.write_text generated CRLF while receipt validator required LF.
  Root extracted the unchanged production writer into write_build_exit and
  reproduced actual temporary-file mismatches for exit codes0 and4: RED exit1,
  2 failures,0 errors/skips,3.831s, XML
  `e26a53f969dccfab96295380626bc7fba4433fc0ba6ed2a5d59df1ea48539885`.
  Fixed explicit ASCII write_bytes plus LF; main calls the tested helper.
  After Ruff format/check passed, root independently ran all28 Python controls:
  exit0,28 passed,0 failures/errors/skips,2.996s, XML
  `289305ad7ea7863fe1b7f75e0421e2cf088b2e3daef457f936f1243c0a40555c`.
- Final source hashes: C++ `c577846b7f5de113230b89224d96a707eceecaf7659cad2b316d2138201f96ad`;
  adapter `a8dec598fb796b2703d8bfe01d7358e43edb90f9c85c4e58d2a276a9949452d2`;
  build `b6b541aebbd0840104cbba9b50dd3992b8b536c0c64c1c2ff4719871dbba8620`;
  tests `8c7ea654f67584be1665b54f5d094d028a127f9b094a0560fe8d7e7a005c79e9`.
  Independent GPT-6.1 Sol code rereview **APPROVE**, architecture **CLEAR** on
  these exact bytes, scoped first synthetic build readiness only. Previous
  REQUEST CHANGES/BLOCK remain historical evidence, not erased by this repair.
- Root launched serial final prebuild regression session52551: all28 immutable
  banded reference tests plus28 selected Python adapter/build controls. No DLL
  receipt supplied or loaded; terminal result pending. First build additionally
  requires clean committed source, fresh external output directory, explicit
  process-local CL/_CL_ clearing and recorded launch provenance. Validate actual
  complete receipt data-only immediately after build and before native loading.
  No full-environment reproducibility, native correctness/performance, learning,
  corpus sufficiency or prompt/training authority claim follows.

## 2026-10-02 — Final native source prebuild regression checkpoint 89

- Session52551 completed normally, actual `pytest_exit_code=0` observed by root.
  Root reread final XML: **56 passed,0 failures/errors/skips,93.820 seconds**;
  exactly28 immutable banded reference cases plus28 selected Python adapter/
  build cases. XML SHA-256
  `8c6cd571a645e9b2fdef727f6be7aebaf3eb87c1975142ed356fabd55784e45e`.
  Source hashes still match independently reviewed checkpoint88 bytes.
- Preserve regression XML and explicit root-witnessed exit record. Commit the
  reviewed four source/test/build files with related test evidence/trajectory
  as the initial native source freeze. This is a build-readiness checkpoint,
  not a claim that a DLL exists or native acceptance passed. Confirm clean
  status before the builder's own clean-source checks. First build uses a fresh
  external directory and clears process-local CL/_CL_; complete receipt must
  validate data-only before any load. Native mathematical and resource gates,
  mutations, further negatives and timing remain required.

## 2026-10-02 — First real native build and runtime checkpoint 90

- Reviewed source freeze `d739a35dc7d184c77fec893a22c972fb5d40cf34`
  was clean and pushed before compilation. Fresh external output directory:
  `.research-evidence/alc_r0_banded_native_20261002/build-d739a35-v1`.
  Root cleared process-local CL and _CL_ and ran the locked Windows CPython
  3.12 builder. Actual compiler, dependency inspection and launcher exits were0.
  Receipt records source tree `8b7ff05b6d6fe5868116a2e5e6c1ab89ca2a698e`,
  dirty-at-start/end false, MSVC19.44.35228.0 and SDK10.0.26100.0.
  Dependency inspection lists KERNEL32.dll only; this is Windows evidence,
  not native Linux/macOS portability or general environment reproducibility.
- Before DLL loading, root successfully validated the complete real receipt
  with read_build_receipt, exit0 (data-only positive control). Receipt SHA-256
  `ec5463427664884af4c2315031733fe3eb9a496abc84322b5fefba46db4e8d61`;
  DLL size106496, SHA-256
  `d8d680420698a30d863748943d5b000d38facafc56b7081eb1dbfe004af0161a`.
  Preserve raw receipt and build/dependency logs byte-for-byte; compiled binary
  and intermediate objects remain external, not repository evidence artifacts.
- Root then ran the original complete native test module with that exact receipt,
  locked Python, PYTHONPATH=src and cache/bytecode disabled. Session96042 finished
  normally; actual pytest_exit_code=0 observed. Independently reread XML:
  **53 passed,0 failures/errors/skips,23.047 seconds**, SHA-256
  `97f02c8089e2ecae9b6754bb04eb9e1cec0cb95764938fe854b60006bfa99130`.
  This includes real native/reference/oracle parity, long synthetic fixtures,
  resource cases, transport no-write negatives, corruption/receipt rejection and
  an isolated unsafe-pointer rejection. Pytest console output was tool-captured;
  do not claim raw persisted stdout/stderr files for this particular root run.
- New contract-edge tests are being added in a separate module; they are NOT
  covered by the original receipt's fixed source allowlist or the53-case result.
  Native semantic mutation acceptance, remaining edge tests, final independent
  review/regression and fixed synthetic timing remain OPEN. No corpus processing,
  prompt sufficiency, training authority, model learning or ALC-0 PASS follows.

## 2026-10-02 — Additional contract crash and mutation design checkpoint 91

- Worker extra-contract run ended with actual Windows access violation
  -1073741819 (0xC0000005),41 progress dots and no final XML. This is not PASS.
  Candidate cause found in NEW test harness: empty-input direct ABI test discarded
  the backing workspace/output owners while retaining non-owning offset pointers.
  Worker corrected lifetime in its new test module only; isolated rerun and
  independent exact-byte review pending. Frozen production files remain unchanged.
  Do not classify the crash conclusively until corrected terminal evidence exists.
- Independent architecture lane specified a separate closed native nine-mutation
  harness; root read original full fixture plan and Python mutation probe, and
  recorded implementation detail in
  docs/superpowers/plans/2026-10-02-alc-r0-native-mutation-fixture-gate.md.
  Keep unchanged control and independent oracle; crashes/build/transport/invariant
  failures do not count as semantic kills. No arbitrary DLL loader or product
  trust-boundary change. Harness implementation/review/execution still pending.

## 2026-10-02 — Corrected native contract edges checkpoint 92

- Worker retained all owning arrays across every direct ABI call and documented
  the helper's non-owning offset-pointer contract. Frozen C++/adapter/builder
  SHA-256 hashes independently rechecked by root: unchanged checkpoint88 bytes.
  New separate test module stopped at SHA-256
  `322513f39cd23f0e572ce381ec40192b9224f9a3f06062b6c6e6a109d2bfc9cb`.
- Root independently read corrected isolated lifetime/receipt XML:22 passed,
  0 failures/errors/skips,28.200s, SHA-256
  `fd2eea68f1cadf6ebff958a33c0f44bf2d7283053dcc530518176f1c94f4a3f6`;
 40 deselected, worker actual exit0 persisted. Complete corrected module v3:
  **62 passed,0 failures/errors/skips,40.149s**, SHA-256
  `2d3925254d0138814e40b2cfdf7edd00b457bfacd5e5db76af63fc17dd82b0d7`.
  Root read persisted actual exit0, stdout and provenance. First crash remains
  failed raw evidence; corrected success does not erase it. Concrete cause was
  caller-owned-buffer lifetime in the new test, not a frozen-kernel code repair.
- Covers ternary/swap/nested/all-retained/crossed mathematics, endpoint/K bounds,
  accepted logical/rounded workspace and output guards, safe ABI/null/count
  rejections and build ID guards.18 deep negatives each start with full valid
  actual receipt;3 copied-artifact semantic tamper cases establish a full valid
  relocated clone before mutation. Original external artifacts preserved.
- Independent GPT-6.1 Sol code lane APPROVE exact new-module bytes, scoped source
  review (reviewer did not execute tests). Independent architecture rereview
  **CLEAR** on the same stopped bytes; scoped this module only, not execution
  or overall native acceptance. Combined final native gate remains open.
  Worker has begun separate pure-layer
  closed mutation harness implementation; real mutant compilation/loading waits
  for independent review. No benchmark/corpus/model/training authority follows.

## 2026-10-02 — Closed native mutation pure-layer RED checkpoint 93

- Re-read the full unified ALUCLU/ALC goal, latest source/evidence and fixture
  mutation declaration; continue the existing dependency chain, not a restart.
  Worker owns only new mutation generator/classifier script and its unit tests.
  No mutated DLL is compiled or loaded at this stage.
- Root read the absent-module RED stdout/XML: FileNotFoundError for the not-yet
  implemented script,1 collection error,0 failures/skips,0.323s. Worker reports
  actual process exit2; its persisted exit/provenance and GREEN are pending root
  validation. Preserve this negative attempt, not a native execution failure.
- Initial pure layer generates unchanged control plus nine independent checked
  substitutions and separates semantic disagreement from build/crash/transport/
  invariant/canary failures. Source generation is explicitly unbuilt; classifier
  unit tests cannot prove native mutants are detected. Complete fixed-schedule
  oracle/metadata controls, strict provenance pins and independent reviews remain
  required before generation/build/child-loader execution acceptance.

## 2026-10-02 — Pure classifier independent prefreeze findings checkpoint 94

- Root subsequently read actual persisted RED exit2 and copied raw RED XML/logs
  into results with byte-identity checks. XML SHA-256
  `53e46f13e278b3175bf92281bb60679f5737101f7d5cc9b4c8cb8293a5163572`.
  This closes checkpoint93's exit-record observation gap, not the mutation gate.
- Worker expanded controls to the complete1470-case binary grid plus declared
  witnesses, independent original-position recursive oracle and all64 expected
  output words. Strict case/observation typing excludes boolean-as-integer input;
  plan/reference/Python-probe/detail-plan hashes are pinned before generation.
  GREEN still awaits terminal validation and exact-byte independent reviews.
- Architecture lane's preliminary inspection found that illegal presence bits,
  unused/absent nonzero slots or inconsistent method/reason/presence could be
  classified as semantic kills. Worker is adding RED/GREEN structural ABI checks:
  invalid responses must never substitute for completed mathematical disagreement.
  Preserve mathematical mutant differences (including over-threshold acceptance)
  without applying baseline mathematical bounds that would hide them as invalid.
  Pure local classification cannot establish aggregate control/artifact coverage;
  future execution must revalidate provenance and all closed IDs/schedules.

## 2026-10-02 — Reviewed pure mutation layer checkpoint 95

- Worker STOP at script SHA-256
  `466742508428b1d2cdadda088bab27429795d5dbe2faa4c4a312baa99ac6f6f7`
  and tests `d432ea9f96c1cbc29e59402b7c805b53247174004ce1d96de1d004c4847992b6`.
  Root read initial GREEN18 passed,0 failures/errors/skips,3.313s, exit0, XML
  `82c8ac6c41043b980496767d136c55a63e15861805ec5b6e2f0ed5937792bcfb`.
  Structural RED9 failed,0 errors/skips,3.668s,18 deselected,actual exit1, XML
  `e91d22760768940a5678c778929fd346892a6a4e15dcac2c49d6df23e849bdc5`.
  Final worker GREEN28 passed,0 failures/errors/skips,5.147s,exit0, XML
  `c63e8f92882588936d979ea26ae46cf2cb99364ac5074c7ff77a3823855f966e`.
- Root independently reran the stopped28 cases: actual exit0,28 passed,
  0 failures/errors/skips,5.837s, XML SHA-256
  `f88d441139364bc70d0c7f02d6961b83a82435c4467be16471eff7e945ccd50d`.
  Independent GPT-6.1 Sol code lane APPROVE / architecture CLEAR exact stopped
  bytes, scoped pure stage only. Full1470-grid plus3 distinct witnesses validate
  reference/recursive oracle/geometry expectations, not actual native kills.
- Root launched reference-plus-pure regression session3843 (28 reference plus28
  pure cases); terminal result pending. Original native files remain unchanged.
  Recorded next execution-layer implementation detail separately, leaving pinned
  original/detail mutation plans unchanged. Build/isolated loader/aggregate
  provenance implementation and independent review are required before actual
  mutant compilation/loading. No CLI generation/build/load/timing/model claim.

## 2026-10-02 — Pure-layer regression and execution design checkpoint 96

- Session3843 completed normally, root observed actual pytest_exit_code=0.
  Root reread XML: **56 passed,0 failures/errors/skips,137.660s**, SHA-256
  `f739518c547c791324a38ddfc0b88269215d17aa032cdfd2ff0c7fb9d94fb146`.
  Exactly28 immutable banded reference plus28 pure mutation cases; hashes of
  both new files and immutable reference remain unchanged. This is relevant
  pure/reference regression, not whole-project or native mutation acceptance.
- Independent architecture design lane CLEAR next execution detail SHA-256
  `041d8150f2035984ed8729d926a68bd4a53fda8892aaf1cd228d7a7677e5a723`.
  Separate script/tests will implement closed build/child-load/aggregate logic;
  implementation review precedes all new native compilation/loading. Native
  source freeze, receipt source allowlist, ceilings and scientific gates unchanged.
- Commit reviewed pure sources/tests and raw RED/GREEN/regression evidence plus
  records/design. Next execution work is not completed by this commit and cannot
  inherit the pure-stage APPROVE/CLEAR as its own implementation approval.

## 2026-10-02 — Actual pure generation CLI checkpoint 97

- Root re-read full goal, current clean tracked HEAD5ed52f4, complete reviewed
  generator and execution/detail declarations. Ran locked Python -B generator
  with PYTHONPATH=src and bytecode disabled, actual generator_exit_code=0.
  --baseline-receipt points to original build-d739a35-v1/receipt.json;
  --output-dir fresh external mutation-sources-5ed52f4-v1 under the existing
  .research-evidence/alc_r0_banded_native_20261002 directory. This command
  validates full baseline receipt data-only; it never loads or compiles a DLL.
- Independently checked manifest stage generated-only-unbuilt, literal false
  authority flags, exactly10 closed IDs in declared order,10 distinct source
  hashes matching actual files, unchanged control c577846b hash,1473 control
  cases and11 files total (10 source snapshots plus manifest). Manifest SHA-256
  `9e7b7168903640c5b2c94626877a375e503c9bc87f9c9080b5f0a63937b3eaca`;
  original receipt ec546342 and generator46674250 hashes unchanged.
- Preserve raw manifest and root-witnessed exit, leaving mutant source files
  external. Worker continues separate execution script/tests; it may use this
  manifest as a real data-only positive control but must independently regenerate
  and verify it. No actual native mutant build/load/kill, timing, corpus/model,
  learning evidence or prompt/training authority follows from source generation.

## 2026-10-02 — Execution absent-module RED and manifest bytes checkpoint 98

- Execution worker added new tests before its implementation. Root read actual
  absent-script RED stdout/XML:1 collection error,0 failures/skips,0.243s,
  XML SHA-256 `9d474f2d16705ba468872a6b636baf2f9edf53e90bcec2fd7416f12b1fa53e6b`.
  Persisted process exit/provenance and completed GREEN await root validation.
  In-progress source implements closed generation/build verification; no native
  compilation/loading is permitted before its independent implementation review.
- Root inspection found a prebuild byte-binding defect: the initial build code
  compared raw manifest SHA with freshly canonicalized JSON plus LF, although the
  reviewed Windows generator had written CRLF. Root independently demonstrated
  unchanged raw manifest hash9e7b7168 versus normalized-LF hash
  `0f8d14d61573b2f85a879f4d99270b5b0af6ccde0f0c6ae65e15f1559373ea36`;
  exactly1 CRLF and unequal hashes. Original manifest/source artifacts untouched.
  Worker was directed to reproduce/check real data-only manifest binding and
  compare captured original byte hash before/after, separately from regenerated
  semantic document equality. This is a prebuild implementation defect, not a
  native experiment result or reason to rewrite original evidence.

## 2026-10-02 — Reviewed closed execution layer checkpoint 99

- Root read both complete stopped execution files and independently reread all
  worker exit logs, JUnit XML, stderr lengths and provenance. Absent-module RED:
  exit2,1 collection error. New raw-binding helper RED: exit1,1 failure; new
  allocation/history helper RED: exit1,5 failures. These are missing-helper TDD
  failures, not actual native compiler/runtime failures. All original records
  preserved byte-for-byte in results/alc_r0_banded_native_mutation-execution-*.
- Worker final GREEN: exit0,36 tests,0 failures/errors/skips,23.328s XML time;
  XML SHA256 c47470bd66ae7f56bbd3501167334be49bd4f9698a3c1518382dda48eed77a6e.
  Root independently ran pure generator plus execution tests in session70255:
  actual terminal exit0,64 passed,0 failures/errors/skips,20.737s XML time;
  XML SHA256 9632051bb11e900a91695780ae5dbda0e16d6d3eba60072ef126a5fd124b5168.
  Root session output was tool-captured, not redirected stdout/stderr files;
  exit receipt is root-witnessed, not an independent watcher receipt.
- Independent GPT-6.1 Sol code lane APPROVE and architecture lane CLEAR for
  first synthetic build readiness only, both inspected complete files and hashes:
  execution48f3b4350e02b37674efb16f944aef7e06f29bdb03d3e0230869867b598a7d44;
  tests8c7c7f3735dec6725d291f1cf4f8cc2dabfc3601620a9b6b51e23e7bd63a3637.
  Exact reference allocation checks and prior guard/no-write failure rejection
  are included; raw CRLF manifest remains untouched. LF attributes bind new
  committed sources to reviewed working bytes. Current free disk66,172,030,976B.
- No real native mutation build/child/aggregate positive has happened yet.
  Freeze clean reviewed sources before first build; subsequently verify all
  actual compiler/dependency exits, control1473 and nine categories. Earlier
  nonsemantic detections remain visible even if a later semantic kill occurs.
  Fixture evidence never confers timing, corpus, held-out or training authority.

## 2026-10-02 — Genuine native mutation run checkpoint 100

- Reviewed execution source freeze ed3cfb6 and separate worker-provenance record
  c5d0f02 were pushed explicitly to origin/codex/unified-lifelong-cognition;
  default git push rejected the differently named upstream, not the commit.
  Actual execution provenance is clean c5d0f02ea876356d281a3d18343ca8e86b17d34e,
  tree4d43f2c3d667730994651958316386cf4d88e545, distinct from baseline d739a35.
- First real ten-artifact build at fresh external mutation-build-c5d0f02-v1:
  all10 actual compiler exits0 and dependency exits0. Original manifest9e7b7168
  and all reviewed sources preserved. Start-Process -Wait launcher stalled after
  Python/compiler completion; root verified/stopped only its orphan console19732
  and stale wrapper19544. Tool session42762 exited-1 after that intervention;
  overall build CLI exit is UNAVAILABLE, never inferred0. No build retried.
  Separate full data-only verify_build on all10 actual records in session20164
  exited0. Raw launcher diagnostic/logs preserve this infrastructure limitation.
- Direct run session2548 completed normally with actual_run_exit_code=0.
  Control1473 ordered cases survived; allnine isolated mutant children exit0,
  no timeout, each has a semantic counterexample with intact guards/no-write.
  Inward-parity reaches its kill at row72; stale-column at row93; other seven
  at row1. Preserve earlier18 invariant-detected and145 survived mutant rows;
  these are not semantic kills and are not erased by terminal classifications.
- Aggregate SHA256 cb3385f954aa6792429318fae3a2ddbf5c928690fecddd188bb99c62f24dc53d,
  status all-nine-semantic-killed-non-authorizing; training_authority=false,
  held_out_data_present=false. Root independently read category counts, allnine
  exits/timeouts/witnesses and zero guard/no-write violations. Preserve all110
  build/process/child/observation/log artifacts, aggregate, launcher diagnostic
  and root-witnessed run exit. JSONL raw-byte attributes prevent normalization.
- Independent actual-evidence code/architecture rereviews are pending. Final
  partitioned regressions and fixed synthetic timing remain OPEN. This closes
  neither native acceptance nor neural learning/family-B/prompt/training gates.

## 2026-10-02 — Mutation evidence rereview and regression checkpoint 101

- Independent actual-artifact code lane APPROVE and architecture lane CLEAR,
  each reread build/process/child/JSONL/aggregate identities, control1473 ordered
  coverage, allnine completed semantic witnesses, guards and preserved prior
  observations. Both explicitly retain unavailable outer build-launcher exit;
  neither calls wrapper termination-1 compiler failure or invents build CLI0.
- Final immutable native-source regression at tracked bf08b1c: original native
  module separately executed session74778 actual_pytest_exit_code=0,53 passed,
  0 failures/errors/skips,29.042s XML time, SHA256
  10ca2b73e2be681569d6676d69a8c0ffe48477081fbeb454d9acf6a015801adf.
  Extra native contract module in separate process session21080 actual exit0,
  62 passed,0 failures/errors/skips,34.046s XML time, SHA256
  a4336fae176b8e9c7b9a940f2a0d52179325627d882b9899835f19b4738108ad.
  One-backend-per-process contract preserved, no combined native pytest claim.
- Remaining48 ALC-R0 non-native modules running in session20756, explicit sorted
  test-file list excludes exactly the above two native modules. No final broad
  result inferred from progress. No source code changed after execution freeze.
- Root declared separate fixed timing operational detail before timer code:
  docs/superpowers/plans/2026-10-02-alc-r0-native-fixture-timing-detail.md SHA256
  e21ee7e7caacfbd91a3caecfd3b11f924a34e6cafb28b90d5a8c198145d0820e.
  Original cases/B5/warmup2/samples5 unchanged; public end-to-end includes its
  per-call overhead, load reported separately, ctypes kernel not pure C++ time,
  component timings not additive. Independent design review pending. No timing
  code or measurement yet; full regression and implementation reviews precede
  execution. No corpus/model/learning authority granted by any of these gates.

- Timing-detail independent architecture design lane CLEAR on unchanged e21ee7e7
  plan. Existing GPT-6.1 Sol worker assigned only separate timer script and its
  data-only test module, with TDD and STOP for two independent implementation
  reviews. No timing, DLL loading or native build authorized to that worker.
  The live48-module run is bf08b1c pre-timer regression and cannot claim coverage
  of tests/scripts added afterwards; new timer evidence and final source scope
  must be recorded separately before overall native acceptance.

## 2026-10-02 — Partitioned ALC-R0 regression terminal checkpoint 102

- Root observed session20756 terminal actual_pytest_exit_code=0,649 passed,
  8 skipped,380.14s stdout. Independently reread JUnit657 total,0 failures,
  0 errors,8 skipped,379.853s; XML SHA256
  daecd99e9560e3214967f72c72ebf7b3f2667bc84e391089c1534f51edae2ae4.
  Combined explicit disjoint partitions at bf08b1c source stage:764 passed,
  8 skipped,772 total (53 original native +62 native edges +657 other cases).
  This is ALC-R0 coverage, not whole-project pytest or later timer coverage.
- All8 skips are asset-gated optional tests:3 BANKING development source/tokenizer,
  1 defect-prompt snapshot path,4 Devign development source path. Do not infer
  corpus/model proposal or acceptance from missing asset tests. Existing broad
  suite also invokes verified local SmolLM2-135M host/wrapper CPU/GPU synthetic
  conformance, capsule/LoRA update/remount contracts. These are existing regression
  controls, not a new authorized corpus training/evaluation or learning claim.
  Native mutation/timing fixture scope remains separate, CPU synthetic only.
- Root compared working versus committed Git blob identities for all115 mutation
  evidence files, exact matches; execution script/test SHA48f3b435/8c7c7f37 remain
  unchanged. Initial a3fc294 push hit transient GitHub443 network failure; one
  retry succeeded, verified remote bf08b1c..a3fc294. Free disk65,893,109,760B.
- Timer worker has preserved absent-module RED and is implementing its separate
  script/tests. No timer compilation/load/measurement has occurred. Retain the
  independent two-lane implementation gate and final timer-inclusive source
  regression before any native acceptance or renewed family-B research step.

## 2026-10-03 — Timer publication RED/GREEN/review checkpoint 103

- Previous turn made concrete progress: targeted publication repair and tests,
  not a status-only wait. Resumed goal read in full; source hashes/live session
  revalidated, no test restarted merely because the turn was interrupted.
- Original timer author remained pending_init after one interruption request;
  root took ownership of the targeted repair and notified it not to edit.
  Original absent-module RED raw logs/XML preserved:1 collection error,
  0.396s XML time, SHA256 dcaff5ae8108c095be0199fcb070af923e6e4bf42db482727c620fe397bf8b3e.
  Author process exit receipt unavailable; do not invent exit2. Root first
  data-only test run session46669 exit0:18 passed,20.939s XML time, SHA256
  194dc685056869c1e1a8d51c72d71630fdc63d95bf1da6a6c5e27abab5b1b816.
- Two fresh independent GPT-6.1 Sol reviews REQUEST_CHANGES/BLOCK original
  timerbc106a4f/tests6115a869: success report publication preceded a fallible
  finally artifact verification; direct final writes could also leave partial
  files. No actual timer/DLL load was allowed under those verdicts.
- Root added4 data-only publication tests before repair. Actual RED exit1,
  4 failures/18 deselected,0.609s XML time, SHA256
  e09ed79274d6fa27d9ed5576d29c8535ca0d06faad936793d0cc33447ac184cc.
  Three failures are missing new publication helper; one AST test specifically
  detects the old publish-before-finally ordering. This is static/control-flow
  regression, not a claimed actual timed experiment failure.
- Publication now occurs outside verified try/finally. The helper performs final
  verification and serialization before private staged write/flush/fsync/close,
  then exclusively os.link publishes complete bytes without overwrite.
  Stage-name cleanup is nonmandatory best-effort, never a later acceptance check.
  Real filesystem data-only tests cover verify/serialization failures leaving
  no final file, complete publication and preservation of an existing target.
- GREEN session42945 actual exit0:22 passed,17.925s XML time (21.48s stdout),
  SHA256 96bfbdfbb0708774d28bafbb26317d1d1cad8915c30f7c4b0824d5e18aec5a3f.
  Ruff format/check --no-cache exit0; final stopped script518291e03b29594998ea77ef00b6242ad93f7b75b4eb160ccefb77f48482c7d6,
  tests1f1f64cbcbac59291cdee635a8794d82a7a41adf865343742db63ed6281dfd34.
- Post-format pure generator/execution/timer regression session13516 terminal
  actual exit0:86 passed,0 failures/errors/skips,40.794s XML time, SHA256
  cb81922445733b309e01970bfd2089ea78039a686cb98e303a4ed08bc31d0f8e.
  Independent code rereview APPROVE final bytes. Architecture rereview was
  interrupted and has been resumed; CLEAR not inferred. Clean source freeze,
  timer-inclusive broad regression and genuine fixed measurement remain OPEN.

## 2026-10-03 — Timer first-measurement review checkpoint 104

- Interrupted architecture lane resumed and independently reread complete final
  script518291e0/tests1f1f64cb, returned CLEAR. Separate code lane APPROVE;
  no author/root fallback was used. Both prior publication findings resolved.
  Successful exclusive hard-link publication was exercised by data-only tests;
  unsupported filesystem linking remains infrastructure failure with no final
  report. Stage-name cleanup is not an acceptance check after publication.
- Preserve all RED/GREEN/raw records and root-witnessed exits; original absent
  RED's missing author exit remains explicitly unavailable. Freeze reviewed timer
  code/tests with LF attributes before the actual run. Final timer-inclusive
  ALC-R0 regression uses distinct original-native and native-edge processes plus
  all49 other modules, with new committed source provenance. Do not reuse the
  pre-timer764-pass result as final timer-inclusive evidence.
- Genuine fixed timing has not run. No measured benefit, optimization acceptance,
  corpus, neural capability, portability or training authority follows from these
  static/code/unit gates. Full roadmap remains active in dependency order.

## 2026-10-03 — Final timer-inclusive regression checkpoint 105

- Frozen clean source968e92f7ec198bd095ecc607d9e8e7383836d3cd, tree
  82ef4029def5c23964670e57f5d7fdb50613a20b. First v1 launcher exited4 before
  any tests: PowerShell if-expression unrolled the one-file array and splatting
  supplied invalid test path `t`. Preserve empty XML and honest failure note.
  Direct branch array assignments repaired launcher only; no implementation,
  test, threshold, fixture or artifact changes. Corrected run uses fresh v2 paths.
- Root session43194 terminal shell0; independently witnessed actual pytest0
  for each disjoint process. Native53 passed,21.199s XML time, SHA256
  ac45253dcada57f6b441f4b40cafd0b535b9c82e7395cbd2453301b12c081898.
  Edges62 passed,33.833s, SHA256
  4d7dc41879a08ec215ab7c9292e50646b2060fd0828893c5448ef8c50b692a74.
  Other49 modules671 passed/8 skipped,679 cases,360.392s, SHA256
  82fb3d96fee384b7cb188a2be36ce7940c4db66e824564f6694dccc74edbde32.
  Total786 passed/8 skipped/794 cases,0 failures/errors. Root personally read
  all JUnit counts and SHA256s. Existing optional-asset skips remain limitations.
  This is final ALC-R0 subset regression, not full-project or portability PASS.
- Tool-captured stdout is not a redirected raw log. Separate root-witnessed exit
  notes say so explicitly. Original two native modules remain process-isolated;
  no retained DLL owner workaround or repeated run was introduced.

## 2026-10-03 — Genuine fixed native timing checkpoint 106

- After all final-source regression partitions succeeded, actual fresh timer
  session71675 ran once on the same clean968e92f source. Root witnessed CLI0
  and shell0. No edit, commit, corpus read or heavy parallel execution occurred
  during measurement. Output published successfully through reviewed exclusive
  hard-link path. Original build d739a35/DLLd8d68042 remained unchanged.
- Raw report SHA256 d51b92889bb0469cab39e01465d35f09a542166728a804cbcf2cf96d81a8d13f.
  Four exact cases/B5/K0,1,1,512;2 warmups and5 measured repetitions for each
  of5 methods. Root separately recomputed all100 retained integer-ns sample
  statistics and verified all140 actual schedule entries, source pins,64-word
  outputs, false authority/held-out flags, cells/scratch limits and clean freeze.
- Python/public-native median milliseconds respectively:
  unique identity10000/K0:185.1969/14.2545, native/Python0.07696943091380039;
  unique insertion10000/K1:549.0741/16.4394,0.02994022118326106;
  repeated insertion10000/K1:467.9574/19.6668,0.04202690244881265;
  identity600/K512:4991.7213/32.1125,0.006433151626474018.
  Public native was faster in each declared fixture. One-time constructor
  validation plus load431.9715ms is separate. All samples, including variability,
  remain visible; no exclusion, subtraction or heterogeneous global speed ratio.
  Raw ctypes timing is not pure C++ compute; component intervals are nonadditive.
- Independent GPT-6.1 Sol code and architecture actual-evidence rereviews are
  running. Their verdicts are not inferred from pre-execution readiness reviews.
  Until terminal verdicts, fixture evidence final synthesis stays OPEN. No
  corpus coverage, family-B prompt freeze, model kernel, training authority,
  portability or neural learning claim follows from this local timing result.

## 2026-10-03 — Actual fixture evidence independent gate checkpoint 107

- Separate GPT-6.1 Sol code lane APPROVE and architecture lane CLEAR actual
  timing evidence d51b9288, not just implementation readiness. Both independently
  read the complete report, recomputed all20 statistics and140-entry schedule,
  inspected source/receipt/DLL provenance and parsed final regression XML.
  Code lane also verified all794 test identities are disjoint. Root-observed
  process exits were not represented as independent reviewer executions.
- Architecture initially described CLEAR with a measurement WATCH; root requested
  exactly one contract status rather than inferring approval. Clarified terminal
  status CLEAR: variability/causal limits are qualifications of the accurately
  bounded observation, not unresolved architecture findings. Deterministic
  two-lane final synthesis APPROVE for local synthetic fixture evidence only.
- Keep all sample variability: K512 raw ctypes median37.1447ms is greater than
  separately sampled full-public median32.1125ms. Independent intervals are not
  additive; fixed serial order/one run/five samples cannot isolate scheduling,
  thermal/cache effects or establish repeatability. No inferred component
  subtraction, causal kernel-only speed claim or global/corpus ratio is valid.
- Original native fixture correctness/resource/mutation/timing evidence now has
  final-source ALC-R0 regression and independent scoped review. This closes this
  fixture-validation substep, NOT ALC-R0 or a research/native-product acceptance.
  Next: separately preregister/review bounded full-token band-geometry census
  before any corpus edit DP; retain full retained-pair universe denominators,
  fixed K/endpoint/cell/scratch limits and explicit unresolved counts. Existing
  rectangular137-train/0-validation first-fit result stays immutable. The
  family-B amendment/prompt freeze, corpus rights and full neural experiment
  prerequisites remain OPEN. Full roadmap goal remains active.

## 2026-10-03 — Banded prospective census declaration checkpoint 108

- Previous goal turn was progress: final regression/timing evidence checkpoint
  105-107 committed0279cec and remote hash personally matched. Current worktree
  revalidated clean at that commit; full user goal reread before continuing.
- Declared new bounded full-token geometry census before implementation or data
  execution. Same complete both-retained author-pair denominators, pinned sources,
  tokenizer, graph ledgers and template provenance. Production K512/B5 and fixed
  local limits; global100M band-cell prospective simulation with permanent
  first-nonfit. This does not amend the immutable rectangular policy/result.
- Explicit distinction: eligible geometry is not a resolved edit, distance or
  exposure. Endpoint-rejected geometry is null/unknown; length-gap rejection has
  known C0. Full population, root unions, known/unknown cost accounting and ordered
  digests prevent subset/null-cost reinterpretation. No native load, edit DP,
  model forward, training or held-out access is permitted by this declaration.
- Reuse immutable cohort/tokenization/template helpers with explicit source pin
  rather than replacing normalization or graph semantics. Independent design
  reviews required before RED/implementation; code/regression/clean-source and
  exact invocation review required before any pinned execution. Design gates
  pending, no new module or census exists yet. All scientific gates remain OPEN.

## 2026-10-03 — Banded census design and RED checkpoint 109

- Independent GPT-6.1 Sol design code APPROVE / architecture CLEAR exact
  declarationa14ed9fcc5ee018699e50249a55d1be5962d902045d3b779ec65aac4f9daf0b8;
  frozen declaration committedf95812f before implementation. Both lanes
  explicitly require distinguishing hypothetical payload from reference actual
  allocated payload on rejected inputs. No implementation/data acceptance.
- Root owns new module/tests. Absent-module RED session69944 actual pytest2 and
  shell2,1 collection error; XML SHA256
  585b42631e6351b34e19131d58079c9e0efc53ff38fad45bee468f2e9eb9f37c.
  Only afterward implemented full-token geometry, aggregate cohort accounting,
  immutable helper reuse, verified development reader/graph and guarded CLI.
  No frozen native/reference/rectangular files changed; no real data run.
- First implementation check session19953 actual pytest1/shell1:33 passed,
  1 failed; XML SHA256
  198cd783bb2754b22637d2ab5493c11868a44b44ef079df53a628434d7321044.
  Failure was overbroad raw-leak fixture search `tokens_`, matching allowed
  endpoint_tokens_sum aggregate key. Repair searches a JSON string value prefix
  instead. No raw code/token/ID output permission was widened. Preserve v1.
- Ruff format/check succeeded. Added explicit rejected hypothetical-vs-allocated
  payload test, known-zero/unknown histogram accounting, shared-root unions,
  callback metadata snapshot, source and paired-byte terminal mutation,
  frozen token validation and dependency-pin mutation coverage. Final GREEN,
  relevant regression and independent implementation gates still pending.

## 2026-10-03 — Banded census fixture and implementation gate checkpoint 110

- Corrected focused GREEN session50379 actual pytest0/shell0:44 passed,
  0 failures/errors/skips,16.033s XML time, SHA256
  39c7d1ba6ad3b6acfd7252e34f3be2351dd8d62646ca8d29251bc9ec3d6bbced.
  Root personally parsed terminal JUnit, not progress or anticipated count.
- Relevant nine-module regression session74155 actual pytest0/shell0:
  175 passed/1 skipped,176 total,312.257s XML time, SHA256
  3ab26d6dc0e00ad3e916d10a8f959703e81825e19e8b193796056141417ccfb1.
  Covers new/rectangular census, banded reference, scalable/full graph, paired
  source, source-checkout/model-inventory mutation controls, acquisition and
  defect prompt. Only skip is optional pinned offline model path not supplied
  for defect candidate scoring. No claim from that skipped integration control.
  Traced reference allocation control was CPU-active while terminal output was
  quiet; root verified live process16000 and continued same session, no restart.
- Separate GPT-6.1 Sol implementation code APPROVE and architecture CLEAR:
  module4e21e3f544f9e7e7d6a948dc564fe26e4c4b4d0824edb4b57479483c41fce230,
  tests157315b772ffc00c6df1ef1b4587d8aace2341236198b431ba2738270012cece.
  Full files inspected independently; no reviewer-executed tests were invented.
  Root rehashed final bytes after regression, unchanged. Frozen reference,
  native, builder, timing and rectangular census files have no diff.
- Architecture notes actual run must verify4344/482 emitted universes even
  though input/graph commitments plus deterministic selection bind them. Code
  review requires retaining old terminal inventory/checkout/shared-cohort tests;
  the relevant regression does so. Both scope geometry only, no distance proof.
- Preserve all four raw XMLs byte-for-byte plus root-witnessed exit notes,
  including absent-module RED and overbroad fixture assertion failure. Test
  sources were uncommitted working bytes during these runs; do not invent an
  already-clean committed-source provenance. Freeze these exact reviewed and
  tested bytes now. Exact pinned CLI launch review and subsequent verified
  full-development receipt remain OPEN; no real census or edit DP has run.
  Free disk60,138,205,184B; free physical memory3776MiB at inspected snapshot.

## 2026-10-03 — Full development band geometry census checkpoint 111

- Exact CLI launch on clean frozenf7af513 was independently code APPROVE /
  architecture CLEAR before execution. Same original development/paired sources,
  SmolLM2 tokenizer snapshot and fixed K512/B5/local ceilings/100M prospective
  cap; only length/geometry accounting. No corpus edit DP or model forward.
- Preserved live session9009 across continuation; wrapper22688, launcher26376
  and worker2192 were inspected as hints, not evidence of completion. Graph
  finished209857/209857,candidates19874; pair progress4344/4344train and482/482
  validation. Actual terminal session exit0 and persisted actual_census_exit_code0
  sourcef7af51351cd66017a3c438af473b9eb17b0b7839, not inferred from process death.
  Started20:58:44+03:00; terminal stdout last-write21:21:13+03:00. Tokenizer
  overlength warning is preserved; no model forward/truncation occurred.
- Root read full JSON, canonical bytes and actual exit. Independent read-only
  verification session57547 exit0 checked clean exact source/tree721files,
  source/pair/model/template/four-graph commitments equal rectangular metadata,
  fixed policy, false authority flags, every accounting partition, histogram,
  fraction and total cap balance. Source tree
  cae2990a5ac4c73bc7af7c5351a7b2f27b9298e01536e77a8725bceea629f17e.
  Raw stdout SHA256
  6ffd5f601d2aef5df092307b24dc21a7aefc12b211e849fadd4042d87e28adc7.
- Complete universe4344train/482validation; preflight eligible4160/469;
  admitted169/0; unresolved4175/482. Local rejections184/13, including7train
  endpoint-unknown geometries,34/3 known-C0 length-gap rejections and143/10
  band-cell rejections. No scratch rejection. Unknown is not zero cost/distance.
  Full eligible work2705212284known band cells across4629pairs. Ordered100M
  simulation admits99685082cells and leaves314918, permanently exhausted;
  global-cap unresolved3991train/469validation. Only3.8904%train/0%validation
  admitted; this prefix is not representative and no exposure has been resolved.
- Two independent GPT-6.1 Sol terminal reviews returned code APPROVE and
  architecture CLEAR, scoped receipt synthesis APPROVE. Both personally read
  full artifacts and reconciled evidence; neither reopened corpus/tokenizer or
  reconstructed hidden ordered rows. Root preserved exact raw stdout/stderr,
  actual exit and launcher byte-copy plus explicit verification notes in results.
- This closes only prospective geometry-census implementation/terminal evidence.
  Old rectangular negative evidence is unchanged. No prompt freeze, rights,
  sealer, training or learning acceptance; ALC-R0 and the full goal remain OPEN.
  Next corpus edit-exposure execution/new cap must be separately preregistered
  and independently reviewed before any DP outcomes. Disk snapshot59097690112B
  free; no cleanup or unrelated process intervention was needed.

## 2026-10-03 — Prospective full development edit-exposure checkpoint 112

- Prior turn completed actual geometry evidence, not an unexecuted plan. Root
  re-read full user goal and inspected cleancaea70d before new changes.
- Added separate development-only full-token banded edit-exposure proposal,
  before runner/tests/corpus DP. Proposed NEW3B scheduled-cell envelope derives
  from geometry-only2705212284cell workload rounded to next billion; previous
  100M receipts/policies and169/0 plus137/0 negative results stay immutable.
  K512/B5 and all per-pair limits stay unchanged. No scientific gate weakened.
- Proposal binds complete4344/482universes, exact same geometry prepass,
  original sources/tokenizer/graph, existing trusted native artifact and serial
  named-owner lifetime. Exhaustive unresolved/D0/Dpositive/component strata,
  full denominators and all-optimal-path direct exposure/signature aggregates
  are explicit. No semantic vulnerability localization or prompt sufficiency.
- Independent GPT-6.1 Sol design code APPROVE and architecture CLEAR on final
  declaration SHA256
  db2ca120d692222e6527fbaa9e73aa1e69c063771f485fc50dae28c595309132.
  Root applied explicit review clarifications before final exact-byte rereview:
  original native receipt hash, second-pass full-token/old100Mrecord digest
  reconciliation, complete prepass before native construction/load, per-pair
  conditional ratio interpretation and fresh-child real backend checks at
  production499/1011/2035/4083/8179budgets,D0,D=K,D>K and saturation.
  Added LF attribute to preserve declaration bytes. Design-only APPROVE; no
  runner implementation, RED/GREEN, corpus DP, model forward or training.
  Freeze declaration before absent-module RED. Source rights, scientific prompt
  freeze, machine validator and sealer remain separate OPEN.

## 2026-10-03 — Edit-exposure fixture core checkpoint 113

- Root re-read full user goal and inspected3f5f8f7 plus clean state before new
  runner/tests. Absent-module RED actual pytest/shell exit2,1 collection error,
  XMLd00af38952f8b5a7ef1a922f4351f51a7e66934e221c48ec537cb1d8588c5940.
  Only then implemented explicit fixture aggregation/backend-factory seams,
  result validation, complete strata, independent global admission states and
  full second-pass token/geometry commitments. Production source reader, native
  wrapper and CLI still missing; this core is not a completed corpus runner.
- First focused GREEN actual exit0:23tests,2.851s JUnit,
  XMLb314be1398a63c07a858877a86e2554730c6020fda3df4bef091e59aac8aa2c7.
  Added four meaningful controls. RED actual exit1:25passed/2failed,27tests,
  10.457s,XML2c888fb42f04ad18a5e35ad2a69495afc0b5ccd1ac99e601091467d69afea6e2.
  Reproduced missing tuple contract on unresolved output and false D>K for
  identical endpoints. Repair requires tuple before status branching and rejects
  terminal threshold claims for identical pairs or n+m<=K. Terminal artifact
  failure and all four survival categories/overlapping-root controls also tested.
- Ruff format/check passed. Same-session core plus frozen geometry regression
  session70020 actually exit0:71passed,0failures/errors/skips,48.513s,
  XML7a232ffcbdfbdc5df8384c25aa6cc02e6022db9f8b20f1c9fe2167ed66e260ec.
  Root personally parsed all four terminal XMLs and hashes. A read-only
  PowerShell foreach-pipeline parser error during reporting was corrected;
  it did not launch or change tests. Raw test output is tool-captured, not
  redirected stdout/stderr files. Existing raw XMLs stay external unchanged.
- Current core SHA256ff1daa8e04848f4b7fb086ca81cbb278d2126c9cc78a85dc60f14033aa95f700;
  tests a59fbd1be0aded3bd86181335dca3c0f39f19fee43bf135a6f8b3e88dcdab32b.
  Independent two-lane GPT-6.1 Sol intermediate core review pending. No native
  load, corpus DP, model forward/training or whole-runner acceptance occurred.

## 2026-10-03 — Edit-exposure retained-mask repair checkpoint 114

- Intermediate code review REQUEST CHANGES found missing retained-mask capacity
  validation; architecture CLEAR applied only to previous core bytes. Root
  reproduced upper/lower impossibility with disjoint length3 endpoints and
  budget1 returning2 or0 visible edits per endpoint. Actual RED session59817
  exit1,27passed/2failed,29cases,12.198s; XML
  41efdd71a77de3908ad1d35048fe9b0d3d0d159644ee68d9269fabebb8a7ecfb.
- Added bounds max(0,edit_count-unretained_positions)<=minimum<=maximum<=
  retained_positions for each endpoint, in addition to existing edit-count,
  direct-total, signature, saturation and monotonicity constraints. A failed
  apply_patch due to formatted context changed no bytes; retried exact context.
- Ruff format/check passed. Corrected core plus geometry regression actual
  pytest/shell exit0:73passed,0failures/errors/skips,3.085s; root personally
  parsed XML37b22444b67c249676c25e950f20041b2fe0ced8c8cf263784a8ab9ebf4f6aa9.
  Moduleb66beaef7626570309ac93c5f51f79d26052f78d45576cb0ed3bc146792674e3;
  tests6a347bbffb88677ae5d26fc1bdec04a449abf0e65cd377ef20dcd2424e6ba559.
  Independent GPT-6.1 Sol repaired-byte code APPROVE / architecture CLEAR,
  synthesis APPROVE for fixture core only. Both inspected exact hashes and
  closed retained-mask finding; no reviewer-executed tests were claimed.
- Preserve six actual raw XMLs, including both negative bug checkpoints, as
  byte copies in results. No redirected raw test stdout/stderr existed; exits
  were witnessed in tool output. Added LF source/test and binary XML attributes.
  Production reader/native-wrapper/CLI and later integration/freeze/launch gates
  remain OPEN. No corpus edit DP or neural training executed; full goal ACTIVE.

## 2026-10-03 — Verified development reader checkpoint 115

- Continued from38d33ac in authoritative Desktop local worktree; preserved
  frozen native/geometry/reference sources. Added explicit verified development
  reader, one source load/one graph build, canonical prior-receipt provenance
  comparison before the backend factory and terminal source/pair revalidation.
  Pinned production policy, four graph ledgers, retained rows, author counts and
  both-retained universe must match; fixture expectations remain explicit.
- Absent-reader API RED actual exit2,1collection error,8.504s; raw XML
  5d87183f7e408def574abd5ba7e2378ad1241f58e9e61ea39dcbf9d8c1b721a2.
  The first artifact named reader-green-v1 actually FAILED: exit1,37cases,
  36passed/1failed,2.361s; XML
  d8dc95f18511c19c2a4ffef9e7539afda81d9f88b370c3261decd84ab5c4d98d.
  Root misplaced the prior retained-mask test tail inside a new test, causing
  NameError; restored the original test body and removed the misplaced tail.
  Preserve this implementation/test-edit failure without relabeling it PASS.
- Corrected Ruff format/check passed. New reader/core, geometry, paired source,
  scalable graph and full-development graph regressions actual exit0:
  96passed,0failures/errors/skips,4.658s; XML
  9924c675d51c46001c75c699f0c57de31250fb0ac91b6e7b4d3c0fb46a5a34cd.
  Root parsed all three XMLs and verified byte-identical results copies. Raw
  stdout/stderr was tool-captured only; no redirected logs are claimed.
- Reader module SHA85fcaaee45d74b46c2956a55d2b5eddf7f62694ad3e49b1794b499d9d767b301;
  tests d59b84545f5203b78f3adaf24c1e430d227daed77b224a5598169a5d4bb781a2.
  Independent GPT-6.1 Sol code APPROVE and architecture CLEAR for these exact
  reader bytes; scoped synthesis APPROVE. Neither reviewer reran tests.
  Reader approval does not cover production CLI/native wrapper,
  receipt-byte/model/origin/clean-checkout binding or fresh-child native checks.
  These implementation and final launch gates remain OPEN; no corpus edit DP,
  model forward, training, held-out access or neural learning PASS occurred.

## 2026-10-03 — Pinned execution boundary checkpoint 116

- Reader checkpoint committed/pushed8d4ce14c4d6ace544debc8e9910721fcc04e72d5;
  root verified remote branch matches local HEAD. Then added the five-path CLI,
  exact committed geometry-byte/source-freeze pin and original native-receipt
  pin, data-only native validation and one retained lazy public backend owner.
  No import-time DLL construction, compilation or Python fallback. Core prepass
  still completes before native construction. Terminal held-artifact, ABI/build
  ID, source/receipt, model inventory, module/dependencies and clean-checkout
  verification all precede canonical output; original native sources unchanged.
- Missing boundary API RED: shell exit1,1collection error,2.296s,XML
  cc993a2207a91b734f5acd99ea74fe89cdfbf268262e5418a5b430a372060da7.
  The first artifact named boundary-green-v1 also FAILED: actual pytest2,
  1collection error,2.389s,XML
  f56a6ab29a5da7faff10dbd48f0a78f869504218ff90541a6e26e379bdf6cb76.
  Root used a nonexistent model_snapshot import; corrected to the actual
  acquisition module after checking the existing census import. An intermediate
  unexecuted model_source spelling was immediately corrected too. Shell0 after
  Write-Output is not pytest success; preserve printed pytest_exit_code=2.
- Corrected focused pytest0:44passed,0failures/errors/skips,3.968s,XML
  bdfcafe94f8e41e56465d7123a168f078edf771ef29810b63b97f4fcf6943411.
  Added terminal ABI/build-ID verification. Nine relevant regression modules
  actual pytest/shell0:224passed,0failures/errors/skips,11.259s,XML
  e5fbc65e88eeb8d7dafd41e74a9f10fd2764c0eda365bd5a38841f131f60d902.
  Root personally parsed terminal XMLs and hashes; Ruff format/check passed.
- Implementation source0e14a062d61d88e9412840f52dae7cde1f8768e8c0880ccb790a33e18a7415fe;
  tests at reviewbd8e92452fc811c6946c56b9d55c26bb0ad4b775e5f3e867c007cca227e25b2f.
  Independent GPT-6.1 Sol code APPROVE / architecture CLEAR; implementation
  synthesis APPROVE, with actual native integration and final launch OPEN.
- Added explicit synthetic integration target; final tests
  dc80d31c317cd4394cfa642da451d8fb8781ca035b1c0cd99d6b21d2ae49b571.
  Both independent lanes separately approved its isolated fresh-child launch:
  one pinned native owner, production budgets499/1011/2035/4083/8179,
  D0,D2 partial/saturation,D=K512,D513>K, full reference/result parity and
  terminal verification. Its absent-env skip is explicitly not gate evidence.
  Launched only this target with explicit original receipt in fresh CPython
  child session75589; currently awaiting terminal result, not claiming PASS.
  No corpus DP, model forward, training or held-out access authorized/executed.

## 2026-10-03 — Native integration and final-byte regression checkpoint 117

- Isolated native session75589 terminal actual pytest/shell0:1passed,
  0failures/errors/skips,22.737s; root parsed XML and SHA256
  04e498378780bc8e36766f621dc7b9c50466580e5abf5b510e90b24ef90f6431.
  All four synthetic cases matched frozen reference including all metadata/
  exposure slots and terminal artifact/ABI/build identifier. One named backend
  in a fresh process, explicit original build receipt, no corpus/model access.
  This result supersedes checkpoint116's awaiting-terminal state.
- Final exact test bytes were rerun in separate pure regression session71627,
  explicitly deselecting the separately executed native target, not counting
  its absent-env skip as success. Actual pytest/shell0:224passed,0failures/
  errors/skips,11.385s; XML
  6e8cb73510f5cfdfaf924ecede53c15cab15385631bce628cb0cb39c6e53fdd7.
  Model acquisition and clean-source checkout helper regressions session50915
  actual pytest/shell0:21passed,0failures/errors/skips,14.640s; XML
  bf47e2377ac0dd8d5f75d9421bd0021a19d61d7e555f61c51b1d9d4921cb9e05.
  These are relevant suites, not a whole-project/full-platform PASS.
- Root rechecked exact implementation/test hashes, parsed all seven boundary/
  integration XMLs, copied them byte-identically into results including both
  negative collection-error artifacts, and verified diff whitespace. Test
  stdout/stderr is tool-captured only; no redirected raw logs claimed. Required
  independent code APPROVE / architecture CLEAR cover the exact source and
  final integration test; implementation/synthetic-integration gates passed.
- Freeze this checkpoint before separate full-development launch review. No
  full-development edit DP has started. The new prospective3B workload is
  distinct from the preserved original100M geometry negative result. Actual
  corpus receipt, runtime/memory observations, scientific prompt review, source
  rights, machine preregistration/validator and sealer are still OPEN. No
  training, held-out, neural learning, ALC-R0 or later phase acceptance follows.

## 2026-10-03 — Actual full-development edit-exposure checkpoint 118

- Checkpoint117 committed/pushed62b5c7b6577078db5aa79fd2822a9b2381286597.
  Separate GPT-6.1 Sol code/security APPROVE and architecture CLEAR accepted
  the exact launch boundary before execution. Frozen design SHA256
  db2ca120d692222e6527fbaa9e73aa1e69c063771f485fc50dae28c595309132;
  source0e14a062d61d88e9412840f52dae7cde1f8768e8c0880ccb790a33e18a7415fe;
  testsdc80d31c317cd4394cfa642da451d8fb8781ca035b1c0cd99d6b21d2ae49b571.
  Original native build receipt ec5463427664884af4c2315031733fe3eb9a496abc84322b5fefba46db4e8d61
  and DLLd8d680420698a30d863748943d5b000d38facafc56b7081eb1dbfe004af0161a
  stayed unchanged. No recompile, fallback, trimming or threshold relaxation.
- Ran the full original development graph once, using the prospectively frozen
  3B-cell cap, K512, five code budgets499/1011/2035/4083/8179 and original
  source/pair/tokenizer/native/geometry receipts. The old100M geometry prepass
  remains unchanged, exhausted and negative; it is not relabeled as this run.
  Second-pass split geometry digests and all four graph ledgers match that
  prior receipt. Policy SHA256
  dcfbd0362527fb04af203c0aa918c6dec4256b286c8023c1b5eb4f7cb0077c7a;
  exposure ordered digest18d583777e9dbab3df7379994f6dea4ec91779681133fae2a4d23969d90ea1c9.
- Original live session84878 was followed to terminal shell0, never restarted.
  Wrapper32516/venv30076/module8972 were subsequently verified absent.
  Start2026-10-03T19:28:23.9315987Z; finish19:59:57.5374821Z;
  persisted actual_exposure_exit_code=0; elapsed1893.5970206s.
  Root independently parsed terminal JSON, canonical stdout, source/hash pins,
  counts and logs, and ran the unchanged prospective data-only verifier:
  actual shell0. HelperSHA256
  76ceba70a58a6549569e7beaeb4db5b83c449b8bf7036ba3624701a95035d0d8.
  This is aggregate/canonical validation, not an independent whole-corpus DP
  oracle. Native correctness rests on prior reference/mutation/integration gates.
- Pair accounting (no global-budget unresolved pairs):

  | Split | Universe | Attempted | Exact positive | D0 | Local unresolved | D>K |
  | --- | ---: | ---: | ---: | ---: | ---: | ---: |
  | Train | 4344 | 4160 | 4118 | 0 | 184 | 42 |
  | Validation | 482 | 469 | 464 | 0 | 13 | 5 |

  Local train184 =7 endpoint-unknown +34 length-gap +143 band-cell rejection;
  local validation13 =3 length-gap +10 band-cell rejection. Scratch rejection0.
  Attempted scheduled cells equal visited cells: train2494753540,
  validation210458744, total2705212284. Remaining294787716; exhausted=false.
  Exact-positive cells2458465820/204606926; D>K cells36287720/5851818.
  Known full-universe hypothetical cells3498941446/281217858 are not visited
  work. Root strata are overlapping unions and must not be summed as partitions.
- Conditional changed-token exposure (denominators4118 train/464 validation):

  | Total/code budget | Train all optima hide all | Validation all optima hide all | Train mean min retained/D | Validation mean min retained/D |
  | --- | ---: | ---: | ---: | ---: |
  | 512/499 | 1148 | 100 | 0.6135911530873144 | 0.6847882693202717 |
  | 1024/1011 | 546 | 48 | 0.8076943486965632 | 0.8577118181102484 |
  | 2048/2035 | 205 | 18 | 0.9285704922953121 | 0.9452048570582654 |
  | 4096/4083 | 48 | 2 | 0.983010352596865 | 0.9927056987389569 |
  | 8192/8179 | 0 | 0 | 1.0 | 1.0 |

  At8179 all4582 resolved-positive pairs expose every edit along every optimum,
  but244/4826 universe pairs remain unresolved:197 local +47 terminal D>K.
  Outcome-dependent resolution prevents whole-population sufficiency claims.
  Changed tokens are not established vulnerability-bearing edits. No budget
  selection, new information-loss acceptance threshold or prompt freeze follows.
- Sampled exact-module worker maxima: working-set1476063232B,
  private3011993600B; last observed CPU1537.796875s. These exclude Git children,
  are not guaranteed OS peaks and last CPU is not guaranteed final CPU time.
  Terminal unavailable observation reflects worker exit, not zero memory.
  Stderr contains progress and tokenizer8733>8192 warning: full tokens retained,
  no model forward, so not a model-execution failure. No error traceback.
- Before results were available, verifier failed as expected on absent terminal
  artifacts. An inline PowerShell/Python quoting self-test failed with SyntaxError;
  explicit --parser-self-test subsequently exited0. These transport/control
  outcomes are preserved in monitoring-note, not misreported as corpus results.
- Independent final GPT-6.1 Sol code/security APPROVE and architecture CLEAR
  each read complete terminal artifacts, independently reconciled provenance,
  partitions, histograms, predicates, ratio means and resource sample scope,
  and verified clean62b5c7b source before documentation/evidence edits.
  Scoped synthesis APPROVE for this completed DEVELOPMENT DIAGNOSTIC only.
  Neither reviewer reran corpus DP or reopened raw corpus/model files.
- Raw artifacts are copied byte-identically under
  results/alc_r0_full_edit_exposure_development_62b5c7b_v1.* with -text attributes.
  StdoutSHA2568bc7eb3e96d96a1292181557dd6e44d46de6d00a857c188dafccc48c67b50a46;
  stderr c6b8e66951862a6a98da4bcd920130b8d998c2e297f16e56ff88a1d6e0a32b77;
  exit f4937fa7b69688f6f4a8388518f01281abf652416e5e75f5b861815963f3d056;
  launch e6cd56f0c1fb4579393321da79e951e579b46e70aacdc2fa04dadda34a27ba77;
  observations c6c71a08d938058980e51db54b9030707de83c94d2f72ffdc8061fe26755aa39;
  launcher255d73c3bc5da7a5cf165d935938b6a4fd62bd26fff90caa218b1d68603dd9ad.
  Current evidence-only commit is not a rerun at its new HEAD; source stays62b5c7b.
- Scientific family-B512 remains BLOCK from prior class-conditional truncation
  and prompt contradictions. Existing five-budget contradiction evidence is
  not superseded by these conditional changed-token results. Next: independent
  scientific prompt reassessment before any prospective amendment/freeze.
  Source rights, machine preregistration/validator, independent sealer and real
  training feasibility remain OPEN. training_authority=false and held-out=false;
  no learning, R0.0/ALC-0, broad portability or later phase PASS is claimed.

## 2026-10-03 — Evidence publication and scientific handoff checkpoint 119

- Checkpoint118 committed9be86615fddebf57876fa1db9a4d84cd6f991480.
  Root verified every staged raw artifact blob equals its unfiltered working
  bytes; diff whitespace passed. Initial push failed to connect to GitHub443
  after21.220s. One unchanged retry succeeded; root independently queried
  remote ref and verified exact9be86615 HEAD equality with clean local tree.
  Network failure was publication infrastructure, not a diagnostic failure.
- Updated the NON-AUTHORIZING v2 draft with the new terminal development result
  and explicit supersession of its historical no-corpus-DP statements. Kept
  original negative resource censuses, all prior prompt/contradiction results,
  conditional/unresolved limits and family-B512 BLOCK. No budget, threshold,
  prompt construction, training/test authority or scientific freeze changed.
- Next independent scientific reassessment is scoped to these retained
  aggregate artifacts and the proposed decision boundary. Existing GPT-6.1 Sol
  lanes are reused; no corpus/native/model/training execution is requested.
  Their evidence acceptance verdicts at118 are not reused as prompt approval.
  Scientific outcome remains pending until both lanes return this new scope.
- Both new scoped reviews subsequently returned: evidence/spec APPROVE for
  draft interpretation; architecture CLEAR for its decision boundary. Exact
  reviewed v2 draft SHA256
  ca72c59c62cef563bfb15455add7742b9a64c17dca04375f0e1777d30d18abc8.
  Synthesis APPROVE for recording the non-authorizing interpretation only.
  Both separately BLOCK freezing unchanged512 family-B; future amendmentOPEN.
  Full verdicts/limits and actionable next requirements are recorded in
  docs/superpowers/reviews/2026-10-03-alc-r0-family-b-scientific-reassessment.md.
- Next implementation-independent task is one versioned prospective pair-blind
  single-function prompt-and-resource amendment with matched query/control
  allocations, total sequence ceiling and actual loss/optimizer qualification.
  It must explicitly amend original512+512 within1024 contracts if changed,
  not mechanically select8192 or add generic infrastructure. No new budget,
  acceptance threshold, prompt freeze, rights/sealer or training authority
  was adopted. Existing R0.0 validator and four-job200-update pilot remain gates.

## 2026-10-03 — Prospective prompt/resource candidate checkpoint 120

- Re-read full user objective and verified clean authoritative Desktop worktree
  HEAD5fc0056, preserving the complete roadmap and prior checkpoints. Previous
  goal turn was progress (actual terminal evidence, independent scientific
  decision and two published commits), not a wait or status-only turn.
- Read actual prompt, wrapper, matched-LoRA, gradient-probe and frozen v1
  query/control/optimizer/resource contracts. Resolved retained-information
  receipt grid directly. First PowerShell foreach pipeline parse failed before
  any command ran; assigned emitted rows then formatted, actual0. This transport
  error is not a corpus/model failure. No model/native/corpus execution occurred.
- Checked primary PyTorch2.14 checkpoint and official Transformers explanatory
  documentation. Explicit custom block traversal means an HF flag alone cannot
  checkpoint our wrappers. Proposed non-reentrant block recomputation preserves
  eager attention; local fit/gradient fidelity remains unproven.
- Added NON-AUTHORIZING v3 prompt/resource draft: propose one4096 common query,
  unchanged512 control allowance/4608 total for familyB, Banking unchanged.
  This explicitly amends v1 common/total contracts if later adopted; no automatic
 8192 selection, scoring/threshold/grid changes, pair-aware input, example drops,
  hidden attention replacement, training or held-out authority. Documented
  residual minority-class contradictions/truncation and244 unresolved pairs.
- Proposed explicit checkpoint parity/TDD and full-candidate/accumulation/
  optimizer resource qualification gates, separated from dataset learning and
  original R0.4 pilot. Implementation/execution detail must freeze exact synthetic
  state, update count and runtime before runs. New independent dual review of
  actual candidate risk/allocation is pending; prior draft approval does not
  approve this new candidate. Current unchanged512 scientific BLOCK remains.
- First candidate review: scientific architecture CLEAR for prospective
  synthetic qualification only; code/spec COMMENT identified too-weak absolute
  gradient tolerance and pending control/state-guard detail. Initial reviewed
  draft SHA838e85ab84eedfc5343146bbef0f194711de9cbb59d383fc59056bb11b4ce943.
  Tightened per-factor/accumulated gradient relative-norm and direction checks,
  explicit zero patterns and optimizer-state comparison; require killing a
  small-gradient mutation that passes ordinary allclose. Added proposed explicit
  control-before-common ID composition with separator/framing within512 and
  whole-prefix stop, without query retokenization. State guards must cover
  outstanding graphs and execute before recomputation, including early-stop.
  One doc-only patch attempt failed context matching without changes; corrected
  after reading actual lines. No tests/model/resource run was attempted.
  Exact revised-byte independent re-review is pending before draft acceptance.
- Revised-byte rereview returned code/spec APPROVE and scientific architecture
  CLEAR, with residual risk accepted for prospective synthetic qualification
  only. Final candidate SHA256
  3c7e56cd33ffa6aaec0a5baa7cead146bc7a0ca2688c447c1ecf63424e0cdf38.
  Scoped synthesis APPROVE for detailed specification, not prompt adoption,
  actual-host execution or scientific freeze. Added exact review record under
  docs/superpowers/reviews/2026-10-03-alc-r0-family-b-prompt-resource-candidate.md
  and eol=lf attribute for byte-stable candidate replay. Existing control framing
  is retained as independently encoded ID blocks, not decode/re-encoded text.
- Next available safe step: freeze exact checkpoint implementation/parity/
  resource detail (fixtures, factor states, lengths, update counts, complete
  matrix, runtime/receipt policy), then TDD. No extra generic corpus audit is
  required to specify that detail. Dataset rights/sealer/R0.0 gates remain open,
  actual host fit is unmeasured, unchanged512 freeze BLOCK, full roadmap ACTIVE.

## 2026-10-03 — Checkpoint implementation detail checkpoint 121

- Re-read complete user objective (truncated combined output repaired with EOF
  tail), candidate, actual wrapper tests and frozen optimizer/q+v contracts.
  Clean Desktop HEAD2b716a5 confirmed. Previous turn changed authoritative
  reviewed candidate/state and published evidence, so classified progress.
- Added prospective implementation/parity/resource detail: first pure tensor
  fidelity arithmetic, then explicit leased wrapper replay/ticket lifetime,
  fixed actual-host CPU/GPU synthetic parity and full-loss16-accum/two-update
  resource qualification. Frozen small-gradient mutation/zero patterns and
  base/optimizer-state parity; default/cache evaluation path remains unchanged.
- Primary resource matrix18cells plus two distinct profile/RAG inference cells;
  all-layer q+v reference is separately OPEN, never inferred from q-only. Actual
  host runs require future exact-byte/invocation review and source freeze plus
  existing resource budget journal; no model/task/training run authorized now.
  Detail independent code/science review is pending before implementation.
- Independent detail code APPROVE and architecture CLEAR for SHA256
  9eedbade26957c0105841ca5438abb75162db80fcfb4369cc27f810bc0ca4a1e.
  First pure fidelity TDD may proceed; later wrapper/model gates remain separate.
  Review clarifications: scaled ratios/cosine avoid reconstructed subnormal
  norm errors; exact mode compares original contiguous logical bytes. Resource
  peaks are absolute with separate baseline, never baseline added twice.
- Added first pure CPU fidelity RED tests before module implementation, covering
  small-gradient mutations, signed zero/layout, subnormals, invalid tensors,
  exhaustive named gradients and accumulated-gradient failure. No model,
  checkpoint execution, optimizer update or corpus access is in these fixtures.
  Actual RED execution is the next step, not yet claimed passed.
- Actual RED session23470 terminated pytest/shell2 with one collection error:
  checkpoint_fidelity module missing, as intended. Added model-free implementation
  afterwards. Relative/cosine arithmetic uses separately scaled vectors, not
  rounded reconstructed subnormal norms; original logical bytes preserve signed
  zero under exact mode. First GREEN/regression execution remains pending.
- First GREEN actual0:38passed,0failures/errors/skips,2.940s; XML
  acc2ef5ff771c78cfd06e6bdc34ecd18aa1537e4b18e92b876b406ccb84883b3.
  RED XML1collection error/8.863s,
  1411d2029a2a332a1090ae2df4ccaec98eae64a4d8259adf45c4f20def9798e2.
- First regression actual0:131passed,0failures/errors/skips,28.586s; XML
  a110208a736726938860678fea338e0912e0ac3856be18aafdf04b021e5ac96c.
  Important scope exception: an existing Banking-scoring real-tokenizer case
  was inadvertently included. It read the pinned Banking development labels
  and local tokenizer; it actually passed, not skipped. No host forward,
  optimizer step or held-out access occurred, but do NOT label that entire
  regression model/asset-free. The first new component fixtures remain pure.
  A corrected explicit deselection is required for the intended pure boundary.
- Expanded pure negative tests for reference validation, supported dtypes,
  finite-input/nonfinite-difference and malformed named containers; sparse
  fixture explicitly checks its construction invariants to remove the warning.
  Final-byte pure GREEN/regression and independent code review are next.
- Final-byte pure regression actual pytest/shell0:143passed,0failures/errors/
  skips,3.052s, one real-tokenizer asset test explicitly deselected, not skipped.
  Root personally parsed XML/hash474c4ccf48485f611e4ad3c5beefd61b1136b55bcbd68321369aaf12ed6ca910;
  Ruff format/check passed. Source SHA256
  1a847beb3f7d6da8c9d6e74baf3ed150e972a823f5c1802973d7c0c4b2c675fb;
  test8a9d90af58e26f138df4b86aeeed02b0d3fa118d0cbcf370eb98f66720bafac4.
  Both independent exact-byte implementation review lanes dispatched. This
  component implements compare_tensor/named_tensors only; canonical AdamW state
  adapter, session/wrapper and actual-host runs remain separate unfinished work.
  XMLs are persisted; stdout/stderr are tool-captured, not redirected raw logs.
- Exact-byte implementation reviews returned independent code/spec APPROVE and
  architecture CLEAR; synthesis APPROVE only compare_tensor/named_tensors.
  No actionable findings; both did read-only inspection without rerunning tests.
  Recorded verdicts and strongest residual caller/snapshot/lifecycle objection
  in docs/superpowers/reviews/2026-10-04-alc-r0-checkpoint-fidelity-pure.md.
  Added LF attributes for source/test/detail and -text XML evidence; verify
  staged byte identity before publication. Scope is not whole-checkpoint PASS.
- Next: canonical complete AdamW state/name/step/hyperparameter adapter TDD,
  then outstanding-graph/session replay implementation and wrapper integration.
  Actual-host parity/resource invocation, v3 adoption, source rights, sealer,
  R0.0 validator and real neural capability remain OPEN. Full goal ACTIVE.

## Checkpoint 122 — 2026-10-04 — canonical AdamW adapter TDD

- Continued from clean published3fda5eb in the authoritative Desktop local
  worktree. Added prospective model-free AdamW comparison tests BEFORE code.
  Fixtures construct AdamW and manually populate synthetic moments; no step,
  model/assets, task data or checkpoint execution. Complete caller-owned factor
  and frozen-base bindings are required; one fixed parameter group, canonical
  name bijection, populated state for every factor and required step1/2.
  Cross-arm shared factors cannot masquerade as independent parity evidence.
  Tests exercise every moment/factor, invalid bindings, base leakage, state
  cardinality and fixed hyperparameter drift. Actual RED execution is next.
  This does not authorize later model/update runs or claim optimizer parity.
- RED v1 produced the expected missing-module collection error but PowerShell
  surfaced shell1 without preserving pytest's native code. Repeated the same
  pre-implementation RED with explicit LASTEXITCODE: actual pytest/shell2 and
  one collection error in v2. Both XML attempts retained. Added read-only
  canonical adapter afterwards; it clones factors/moments, rejects aliased
  arm/state/base storage and pins the locked Torch2.14 group schema. Caller
  completeness/concurrency and actual step execution remain runner obligations.
  GREEN and independent exact-byte review are pending.
- First GREEN actual pytest/shell0,103 tests passed. Expanded negatives for
  distinct objects sharing storage, cross-arm aliasing, explicit zero moments,
  malformed containers, wrong step on both sides and complete shape mismatch.
  Added explicit adapter contract documenting pinned schema, caller completeness,
  quiescence and CPU exact-mode obligation. Final-byte regression/review pending.
- First-byte pure regression actual0:267passed (124 adapter cases),0 failures/
  errors/skips,4.212s; XMLa205ec168e5d13ea6c5160c69ffb880da69351fd49143b88b59a77213b9304fd.
  Root personally parsed counts/hash and confirmed excluded asset case absent.
  Independent code lane REQUEST CHANGES: a factor/moment/step can alias the
  opposite arm's base, escaping local-base and owned/owned checks. This is a
  real unresolved adapter defect despite green tests, not an accepted PASS.
  Added eight symmetric negative fixtures before repair; actual failing run next.
- Both independent lanes rejected first bytes (code REQUEST CHANGES, architecture
  BLOCK). Actual alias REDv3 pytest/shell1: all eight fixtures failed because
  expected rejection did NOT occur, confirming factor/moment/step opposite-base
  aliases in both directions. Retained failed XML. Repaired snapshots to retain
  base storage and validate all comparison-owned storage against both bases'
  union. Base/base sharing remains allowed. Final corrected regression next.
- Corrected v4 actual pytest/shell0:275passed,0failures/errors/skips,4.530s;
  Ruff format check still flagged one line, so this was not called final-byte.
  Applied format then reran v5: actual0,275passed (132 adapter cases including
  all8 cross-base regressions),0failures/errors/skips,4.058s. Ruff check passed.
  Root parsed XML/hash3744ae4716f55b0e9e4798b856078384714a8744ed013183e1179f84ec933525,
  confirmed all8 cases present and excluded asset case absent; v3 RED XML
  2b943b86b68fbb5cf8b57bc4aa6a53259f8f3904a4fd2662c2d2d51f0a5ad6ba.
  Exact-byte repaired source6d36db5abe0a57693db894f733e4c2ed384d90e0fb1a434e6b216f8a40f29726,
  testsceee10e977f123c563d68030fc9a8d2ba85ba7c81e714bd542e621095ce9bbfd,
  contractbd62dee04f5d98268cddb726ca7e5000c8b16ef2702db6f8b175dabe4e634c48.
  Both GPT-6.1 Sol lanes rereview dispatched; no self-approval substitution.
  Added LF/raw-XML attributes for byte-preserving publication. All seven run
  XML attempts retained; stdout/stderr remain tool-captured, not raw log files.
- Final exact-byte rereview returned code APPROVE and architecture CLEAR, both
  confirming cross-base blocker closure; scoped synthesis APPROVE only this
  comparison adapter. Recorded initial rejection, actual eight RED failures,
  repair and final evidence/limits in the independent review record. No real
  optimizer step/model/corpus execution occurred. Remaining strongest objection:
  runner must prove complete bindings, real updates, correct lifecycle snapshot,
  quiescence and explicit CPU exact=True. Next implementation is explicit scoped
  session/outstanding graph tickets/replay guards, then wrapper integration.
  All real-host parity/resource, adoption/rights/sealer/validator and neural
  learning gates remain OPEN. Preparing byte-verified commit/push; full goal ACTIVE.

## Checkpoint 123 — 2026-10-04 — explicit checkpoint session engine TDD

- Prior checkpoint122 is published as feff85153d8ceac12f621af54bd586a17068299b,
  remote equality and clean Desktop worktree verified. Last goal turn PROGRESS.
  Reread full active objective and prospective detailC; continue reusable session
  engine first, preserving actual wrappers/default path unchanged. Added explicit
  engine contract and RED fake-block tests BEFORE implementation. Tests will run
  tiny CPU autograd/checkpoint only, no host/assets/optimizer.step/corpus/training.
  Tickets require ordered layers, final and gradient-bearing block traversal;
  caller-owned complete bindings and correct port placement remain later wrapper
  review requirements. Entry/exit fingerprints do not claim hostile-host security.
  Actual missing-module RED and implementation are next; full goal ACTIVE.
- Actual missing-module REDv1 pytest/shell2,one collection error. Added explicit
  controller/session/ticket engine after RED. No wrapper/global monkeypatch;
  nonreentrant calls bind entry guards/private metadata and layer traversal hooks.
  Failure invalidates/release and clears factor gradients; fingerprints stream
  parameter bytes at lease boundaries. GREEN/regression/review remain pending.
- First attemptv2 actual pytest/shell1:21passed/1failed. The failing fixture
  incorrectly expected normal exit after catching consumed-graph reuse; the
  preregistered contract already requires invalidation on that owner operation.
  Strengthened test to require invalid exit/cleared gradients, plus a separate
  successful-close old-graph denial. No engine denial/threshold was weakened.
  Added foreign raw-backward lease isolation, retired graph/fresh gradient
  isolation and actual recompute-entry drift counterexamples before further run.
- Actual foreign raw-backward REDv3 pytest/shell1:1 failure, pending_count became
  0 after a foreign thread's rejected backward. Root identified the hook's catch
  path incorrectly aborted the owner lease. Moved thread/active precondition
  outside hook abort handling; owner-thread lifecycle violations still invalidate.
  Corrected GREEN/regression and independent review remain pending.
- Corrected focused GREENv4 actual pytest/shell0:25passed. Expanded tests before
  final regression for output unrelated to executed blocks, raw intermediate
  backward, prior accumulated gradients cleared on failure, private metadata
  mutation, invalid entry bindings and nongrad early frozen blocks without an
  input-grad workaround. Pure relevant regression/review are next; not model
  parity, resource qualification or neural capability evidence.
- Pure regressionv5 actual0:320passed including45session cases,0failure/error/
  skip,4.280s, XML4ae8a1739e532a3bd2e219b786e8bdb70d8e788293d85730e047c808f3c503b8.
  Root parsed counts/hash and excluded asset fixture absence. First independent
  code lane APPROVE but architecture BLOCK: registered buffers absent from
  replay stamps/byte fingerprints can drift via ordinary in-place mutation.
  Combined review therefore REQUEST CHANGES, not approved. Added buffer version/
  replacement/data counterexamples and an empty gradient-block traversal case
  identified by root; actual RED reproduction precedes repairs.
- Actual binding REDv6 pytest/shell1:all4 counterexamples failed DID NOT RAISE,
  proving ordinary buffer version/replacement/unversioned bytes and vacuous
  no-gradient-block output acceptance. Added full registered-buffer roster/stamps
  and boundary bytes, storage stride/offset stamps, nontrainable buffer constraint,
  and mandatory at-least-one gradient-bearing block at output binding. No wrapper
  integration or acceptance criterion was removed. Final regression/rereview next.
- First repaired regressionv7 actual0:324passed,0failures/errors/skips. Added
  positive scalar/integer/bool buffer coverage and negative trainable buffer/
  factor alias to frozen-base buffer cases before final byte review. Base-buffer
  alias must not allow later outside-lease factor updates to alter frozen state.
  Alias RED is next; registered state expansion preserves real-host integration
  as a separate gate, including unregistered attributes and full base inventory.
- Actual buffer-alias REDv8 pytest/shell1:1failure DID NOT RAISE. Extended base
  storage separation to registered base buffers with device-aware allocation
  identities; factor parameter aliases are denied at lease entry. Positive
  static buffers remain allowed. Final formatted regression/review next.
- Finalv9 actual0:327passed/52session,0failure/error/skip,4.659s, XML
  451fbcda71abf8d3818f0011c245b79ef14bf2c2cb733222b9db9c114355712a.
  Independent repaired-byte code APPROVE/architecture CLEAR. Before publication
  root found one additional engine configuration drift risk: mutable controller
  layer_count could shrink inside a lease and accept a shortened traversal.
  Added explicit negative test before repair; prior byte approval remains scoped
  to its reviewed bytes and does not automatically approve upcoming changes.
- Actual layer-count REDv10 pytest/shell1:1failure DID NOT RAISE. Captured and
  revalidated declared count at entry/replay/completion; ticket bounds use the
  captured count, never mutable controller state. Final regression and both
  independent final-byte rereviews required before publication.
- Final formatted pure regressionv11 actual pytest/shell0:328passed including
  53session cases,0failures/errors/skips,6.264s. Root personally parsed XML/hash
  82ccbf84f5ddd7d327e6c29417bb27bf29b1adbb82cc514fe08b5b43ad831288,
  confirmed53cases and absent explicitly deselected real-tokenizer asset case.
  Ruff check passed; sourceba0cbbbb3a1a1109439d7a9220e154620839217130d9e2782c3af50fba886d6a,
  tests492ac5aa6c81d9d2db1d8f45b40e411e48606e1edb3ff0be6a3d12629fbaff6b,
  contractc28d8382da909df010315e9c1ec9d96b53433210aa212bb7962ba74d3ea2d4ea.
  Both independent final-byte rereviews dispatched. Added LF/raw XML attributes;
  all11 attempts retained, stderr/stdout tool-captured only. No real wrapper,
  assets/corpus, model/update, resource qualification or learning run occurred.
- User reaffirmed durable learning from personal interactions and learned state
  in future .alc, not manual whole-base fine-tuning per message. Existing unified
  objective retains bounded neural updates/frozen base plus governed generations;
  this explanation does not adopt v3, authorize dataset training, bypass R0 or
  claim implemented online learning. Active program still requires real neural
  capability evidence before dependent product/container investment.
- Final exact-byte rereviews returned independent code APPROVE and architecture
  CLEAR for ba0cbbbb source, closing captured-layer-count gap and preserving all
  prior buffer/alias/nonvacuous-traversal repairs. Synthesis APPROVE ENGINE ONLY.
  Added full review/11-attempt evidence record and residual integration limits.
  Next: opt-in host_wrapper/matched_lora integration TDD and complete computational
  inventory/port/cache/input/mutation/autograd audit. This is not learned neural
  capability, actual-host checkpoint PASS or resource fit. Preparing exact-byte
  stage/commit/push of this checkpoint; full unified objective remains ACTIVE.

### Checkpoint 124 — captured factor operations (2026-10-04)

- Previous goal implementation turn made PROGRESS (session engine); intervening
  user question was explanation only, not implementation progress. Revalidated
  clean authoritative Desktop worktree at c3e185f and reread full objective.
- Added CPU-only binding counterexamples before implementation: exact live math/
  gradients, first/last ports, FP32/BF16, same-module parameter replacement,
  q-projection replacement and nonreentrant replay with frozen input. No model
  assets, corpus, optimizer update or neural capability claim. Actual RED run
  currently observed through exec session30706; result not yet assumed.
- Binding captures actual A/B references and q-projection module for later wrapper
  checkpoint callables. It is NOT a lease, mutation guard or immutable snapshot;
  checkpoint-session identity/version guards remain mandatory at integration.
  Default host forward/cache paths remain unchanged. Full objective stays ACTIVE.
- Actual REDv1 pytest/shell1:21 failures,0errors/skips,32.125s; all missing
  bind APIs. Root parsed XML SHA256
  863e8a37b78bd23579532eee1e8580fa258a320fcdd8c7183528fb2bee49df3a.
  Added bind_port/bind_q_projection with actual tensor/module captures, delegating
  existing live APIs to the same math. No host loop/cache/session integration yet.
  Revalidation occurs against captured factors at execution. GREEN next.
- GREENv2 actual pytest/shell0:21passed. Added independent (not shared bound/live)
  formula and gradient comparisons under CPU BF16 autocast, plus device mismatch
  denial before math. Relevant final CPU regression and dual review next.
- Final formatted regressionv3 actual pytest/shell0:374passed,27binding cases,
  0failures/errors/skips,13.954s. Root parsed XML and excluded-case absence,
  SHA256999283ebecd5abb940efd617c1795f578f67d821b146ee0bd0fe1b4b6b8c687d.
  Ruff passed after test-only lambda replacement/formatting. Both independent
  GPT-6.1 Sol lanes dispatched on fixed source/test bytes. Added exact artifact
  record and raw XML attributes. Review pending; no actual-host/learning PASS.
- Both independent exact-byte lanes returned: code/security APPROVE, architecture
  CLEAR, all3source/test hashes independently verified. Synthesis APPROVE BINDING
  PREREQUISITE ONLY. Added full reproduction command and captured-reference limits
  to review record. This is implementation PROGRESS, not neural capability or
  whole-goal completion. Next: opt-in wrapper/session integration and host inventory,
  then separately reviewed actual-host parity/resource invocation. Preparing scoped
  evidence/source/trajectory commit and remote publication; objective ACTIVE.
- Publication precheck detected source CRLF-to-LF index normalization, so no
  commit/push occurred. Mechanically normalize both reviewed source files to LF
  and pin attributes; semantics unchanged, but final byte hashes/review references
  and regression artifact must be refreshed before publication.
- Final LF regressionv4 actual pytest/shell0:374passed,0failure/error/skip,19.033s;
  root parsed XML SHA07a7f6c241732a8c4148ca1a231f06a62148e42c8c370644a332bafec726e7d1.
  Source hashes updated in review; both lanes revalidating final LF bytes.
- Final LF exact-byte rereviews returned code APPROVE and architecture CLEAR.
  Ruff passed; root reconfirmed27binding cases and zero excluded cases in v4.
  All four attempts retained. Publishing only checkpoint124 changes; full unified
  learning/ALC objective remains ACTIVE and actual-host integration remains next.

### Checkpoint 125 — wrapper checkpoint lifecycle bridge (2026-10-04)

- Prior goal turn PROGRESS: binding prerequisite committed/pushed5bc1118.
  Revalidated clean authoritative Desktop checkout and full unified objective.
- Added fake-base CPU wrapper lifecycle RED tests before implementation: one
  controller, live capsule/LoRA getters, nested denial, pre-mutation checks for
  train/eval/_apply/mount/detach/replacement/controller, no default-forward bypass,
  release and missing-arm denial. Fixtures bypass host constructor explicitly;
  they certify NO VerifiedHost/model/parity/resource/learning behavior.
- Scope is lifecycle portion of detail section C. Actual opt-in forward loop and
  complete host computational inventory remain subsequent integration obligations;
  no checkpoint forward authorization is inferred from a session factory.
- Actual REDv1 pytest/shell1:25 failures,0errors/skips,11.837s, missing initializer;
  root parsed XML SHA60132eef624976b82d229b5ca06760b770ebcf1f871aaea57820d6c91f85610b.
  Added one persistent owner controller, arm-specific factor getters, explicit
  session factory and pre-mutation guards including protected attribute deletion/
  replacement. Default forward denies active lease; opt-in path not implemented.
  GREEN and relevant regression/review remain pending, full goal ACTIVE.
- GREENv2 actual pytest/shell0:25passed,0failure/error/skip,10.108s, XML
  0efe2c0426e5055909d96ce9712478a7fc3adfff7f476562c33f2d2a4f5a5824.
  Added direct state-load/requires-grad/zero-grad/module/parameter/buffer mutator
  counterexamples plus protected deletion and closed-controller preservation.
  Actual expanded-mutator RED precedes repairs; no host run or forward PASS.
- Actual mutator REDv3 pytest/shell1:12 failures DID NOT RAISE,0errors/skips,
  9.985s, XML0448a93cd2e84d628df824d7b294c37b55337b03139ce7b58a9802dcccde0668.
  Added prechecks on state load/requires_grad/zero_grad/module registration and
  parameter/buffer registration, plus register_module alias/set_submodule bypass
  prevention. Expanded alias tests before final regression. Raw child/.data writes
  still rely on engine guards; hostile Python interception not claimed.
- Regressionv4 actual0:419passed,45lifecycle cases,0failure/error/skip,16.038s,
  root parsed XML61ac84469eb70eb51829f3e58665e213a1d951badd734037adb55bce5039b4a4.
  Independent code review identified ordinary nonprotected Module assignment/
  deletion bypassing add_module override via nn.Module.__setattr__. Added six
  arbitrary module/parameter/buffer/plain-attribute counterexamples before repair.
  Prior regression not final; approval withheld pending RED/repair/rereview.
- First review synthesis REQUEST CHANGES (code REQUEST CHANGES despite architecture
  CLEAR). Actual attribute REDv5 exit1:4failures/2passes,0errors/skips,12.819s,
  XMLd43e8a2ff9d2060c9a0aaf1240efbab6abc92d95dca718d76d3f1bd173a28662.
  Parameter/buffer setters already delegated to guarded registration; module/plain
  setters and module/buffer deletion did not. Guard all ordinary wrapper attribute
  writes/deletes before nn.Module implementation. Final regression/rereview next.
- Added positive no-lease delegation fixtures for both arms (state loading,
  gradients/dtype changes, register_module/set_submodule strict flag, nonpersistent
  buffers, parameters and attribute deletion) to check compatibility as well as
  rejection. Existing v6 running attempt remains separate; finalv7 will include
  these additions. No recorded artifact is overwritten/reinterpreted.
- Final formatted regressionv7 actual pytest/shell0:427passed,53lifecycle,
  0failures/errors/skips,41.449s. Root verified counts and absent excluded assets,
  XML2ae67e256a61b943134ec494c42354066c266337e1782b83917872e09c2b3b61.
  Both repaired-byte independent reviews dispatched; added seven-attempt evidence
  and reproduction record plus LF/rawXML attributes. Not wholewrapper/learning
  PASS. Full objective ACTIVE; opt-in loop and host inventory are next.
- Final exact-byte rereviews: code APPROVE, architecture CLEAR; synthesis APPROVE
  LIFECYCLE BRIDGE ONLY. Reviewer findings/first rejection/repairs retained in
  evidence record. Root will verify staged source/test/XML bytes before scoped
  commit/push. This turn PROGRESS; full neural/portable/longitudinal goal remains
  ACTIVE with actual forward/inventory/parity/resource/scientific gates still OPEN.
- Publication raw-byte precheck stopped before commit: host_wrapper retained CRLF
  despite formatting, while new LF attribute normalizes index bytes. Mechanically
  normalize host_wrapper only to LF; final source hash/rereview/regressionv8 refresh
  required before publication. No semantic change or prior attempt deletion.
- FinalLFv8 actual pytest/shell0:427passed,53lifecycle,0failure/error/skip,13.100s,
  XML9ea94d45d88b6db68400b85fced2cf1c15443484a3e4919ec106303f2e12057c.
  Both finalLF byte rereviews returned code APPROVE/architecture CLEAR on host
  8ac521e9eaa7265b9a801ad2d5517450320c8fd943d66be53219a990859e36fa.
  Root parsed terminal counters/hash/excluded cases; raw staged verification and
  scoped publication next. No actual-host forward/learning claim; objective ACTIVE.

### Checkpoint126 — computational-state fingerprint bridge (2026-10-04)

- Prior goal turn PROGRESS: lifecycle bridge4fd9468 committed/pushed. Current
  authoritative checkout clean and objective reread. Pinned Transformers source
  confirms original_inv_freq is registered Buffer in5.17; no stale unregistered
  tensor claim. Epsilon/scaling/config/callables/hooks still require state binding.
- Added CPU computational-state RED fixtures before implementation. Prospective
  optional immutable SHA256 getter on engine binds caller-owned additional state;
  module attribute fingerprint rejects unsupported/cyclic/unbounded state, hooks,
  dynamic RoPE and implicit HF checkpointing. Real host completeness/parity and
  opt-in forward remain separate OPEN gates; no host assets/corpus/update executed.
- Actual REDv1 pytest/shell2:missing checkpoint_state module,one collection error.
  Added bounded fingerprint helper and optional getter/identity binding in engine;
  every existing guard compares immutable digest. Defaults preserve old pure engine.
  Helper covers actual attributes/config/forward identities/small nontrainable
  tensors and rejects unsupported objects/hooks/implicit HF checkpoint/dynamicRoPE.
  Full host coverage/wrapper attachment not yet established. GREEN next.
- GREENv2 actual0:23passed,0failure/error/skip,9.139s, XML
  dc5bc8b818f76176b1ea73e5eb60ecebde1d9966e7c118bedc31604a11107dac;
  REDv1 XML e0615e3f33f09592c05b644d93ff5007f432b198c5795d8bb262919c7253302b.
  Root found ephemeral bound-method IDs could enter memo references, and foreign
  bound methods hide untracked self state. Added stable-many-method and foreign
  callback rejection tests before repair; initial Ruff lambda issue fixed in tests.
- Actual methodREDv3 exit1:1foreign-methodfailure/1stabilitypass,0errors/skips,
  10.671s, XMLb7e88cc8cb11a7f9613fcc9bd504d4a5181cddb17407db9dac16769487337295.
  Ephemeral-method issue was static risk, NOT claimed reproduced failure. Removed
  ephemeral method memo identities, bound methods restricted to inventoried module
  self IDs. Added positive owned fake forward/backward+reacquisition and global-hook
  denial/cleanup, invalid getter-construction fixtures before final regression.
- Regressionv4 actual0:457passed,30state cases,0failure/error/skip,12.751s,
  root parsed XML5605054e49b10c723688f744f567cfbb14a5c8332fc6cd3d4af668ecbc92578b.
  First independent code COMMENT/architecture CLEAR: callable globals outside
  inventory; root/module enumeration and scalar/serialized bytes not bounded by
  existing counters. Added explicit known-global-limitation fixture (not acceptance)
  and five fixed bound negatives before repair. Full host audit still OPEN.
- Actual boundsREDv5 exit1:all5failures,0errors/skips,9.690s, XML
  170c53e3b4e6f316075e434762b0df0ce139f57ff7219ca68a62acdd7f4eaed7.
  Replaced unbounded recursive module enumeration with iterative roots16/modules
  4096/depth64/children2048 checks; scalar64KiB/256bit bounds and16MiB streaming
  serialization. These component caps are not measured peak RSS/latency guarantees.
  Documented excluded function globals/class/property/external state explicitly;
  known-global fixture records counterexample, not complete inventory acceptance.
- Continuation: removed temporary one-iteration indentation scaffold from bounded
  module recording before validation. No host/corpus/optimizer execution; final
  bounded-state regression and independent rereviews remain required.
- BoundsGREENv6 actual pytest/shell0:36passed,0failure/error/skip,9.833s,
  XML0d0f5b44c693bca725c6e5af27bb3792ab16aa07d3807828a85a4730063d7b94.
  Regressionv7 actual0:463passed,36state cases,0failure/error/skip,13.981s,
  XMLf1ac790ffcc6f9a27db8002edb4f5512f5b3ae5d1bb9333be53462a1f2bce2cf.
  Root independently parsed counters/hashes and confirmed excluded real-host/
  tokenizer cases absent. Ruff clean; repaired-byte dual rereviews dispatched.
  Added attempt/reproduction record and raw-XML/LF attributes. No complete-host
  coverage, resource-fit or learning claim; full program remains ACTIVE.
- Final exact-byte code APPROVE and architecture CLEAR; synthesis APPROVE
  PREREQUISITE BRIDGE ONLY. Both lanes verified source/test hashes independently,
  with no execution. Actual host-global/class/property/external audit, opt-in loop,
  parity/resource and scientific gates remain OPEN. Scoped raw-byte verification
  and publication next; this continuation is PROGRESS, not full completion.
