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
