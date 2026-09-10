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
