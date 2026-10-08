# Reserved Windows lease output integration evidence

Status: scoped integrated Windows component accepted, independent code APPROVE
and architecture CLEAR. Not scientific launch admission or full-goal completion.
Source parent355568b4f8f4490f3315b32e827070b6f4ac571c.

## Exact inputs

- src/aluclu/alc_r0/reserved_owned_process.py SHA256
  a478edc47f5d01c90fe62ca4fe6257b6e8294744556dfc3d6255940d5795de12.
- tests/test_alc_r0_reserved_owned_process.py SHA256
  d60edddd395cba472e78959f81d3ac63abf19fd138d237d5da1e029edf5f3d9d.
- Unchanged bounded_process_output.py SHA256
  c8f24b9d6e8730878a5e6df556517c0554f1f7af07743c3531f9547c56c471f6.

Both independent lanes admitted these exact source/test bytes before execution.
Earlier intermediate test hashes cb4f/c7117 were reviewed but never executed.
Pinned existing Windows CPython research environment; plugins/usersite/bytecode
disabled, CUDA_VISIBLE_DEVICES=-1, Desktop worktree src explicit PYTHONPATH.
No installation, model, GPU, corpus, held-out access or scientific launch.

## Personally observed executions

Each stem under results/ has stdout.log, stderr.log, exit.json and JUnit xml.
The parent retained each original native process handle in one hidden wrapper,
observed terminal status and actual exit before parsing XML. Stored exit records
corroborate that observation; artifact review does not recreate original handles.

| Stem | Original PID / exit | Tests / failures / errors / skipped | Seconds | XML SHA256 |
| --- | --- | --- | --- | --- |
| alc_r0_reserved_output_cap_red_20261008 | 32216 / 1 | 1 / 1 / 0 / 0 | 1.160 | a3b3c5495a8bda2ea8fbf3ce445a80473ea7a9ede201cf519a1c7301d3da123d |
| alc_r0_reserved_output_green_20261008 | 18684 / 0 | 34 / 0 / 0 / 0 | 48.797 | f71c2ce1496032e3acfb0b40b06fb63e17922b0dda64e79d1c694458a37aa705 |
| alc_r0_reserved_output_regression_20261008 | 32476 / 0 | 187 / 0 / 0 / 0 | 66.368 | 75e9ffa1f13da7b57838f0a3e8f718317b748ed16c76472f59e40a52d320da69 |

All three stderr files are empty; none timed out. RED used unchanged source
7c2661 and testd96e6533: actual persisted1025 bytes violated audited cap1024.
The assertion occurred before accessing the proposed output receipt. Preserve
that negative result; it is an implementation defect, not a training failure.

GREEN exact command: -m pytest -q tests/test_alc_r0_reserved_owned_process.py
--junitxml=results/alc_r0_reserved_output_green_20261008.xml.
Original-handle bound90s split60+30; terminal personally observed tool252295.

Regression exact command: -m pytest -q tests/test_alc_r0_owned_process.py
tests/test_alc_r0_reserved_owned_process.py tests/test_alc_r0_reservation_store.py
tests/test_alc_r0_reservation_state.py tests/test_alc_r0_bounded_process_output.py
--junitxml=results/alc_r0_reserved_output_regression_20261008.xml.
Conditional on actual GREEN exit0, zero issues and unchanged input hashes.
Original-handle bound120s split60+60; terminal personally observed tool19e1ab.
No source or test edits during either live invocation.

## What the evidence covers

Audited declaration-derived independent caps; binary/empty/exact/under-cap output
and digests; first excess byte and sustained stdout/stderr excess; actual exited
root handle observed before releasing a writing descendant; output-triggered
owned job termination distinct from useful timeout; no automatic release.
Original lifecycle, publication/creation faults, timeout/descendants, unrelated
process survival, output collision, durable reservation and abrupt parent-crash
tests now run against integrated pipes. Relevant old process/store/state/sink
regressions are included, not the entire ALUCLU repository suite.

Actual-start partial-entry diagnostics record lease/job/sink/observer deadlines
before releasing the owned read gate, proving equal shared bounds. The explicit
shortened diagnostic expiry branch expects incomplete cleanup, then releases and
joins its own pumps; it does not change the scientific declaration's ten-second
tail. Successful normal useful execution is not bounded to entry-plus-ten-seconds.

## Limits and next dependency

This is not a filesystem sandbox or universal interruptible-I/O guarantee.
Unobserved closure remains incomplete with held reservation. Test-only fault
seams are not production authority or caller-selected public launch callbacks.
Original owned primitive and standalone sink remain unchanged.

Concrete launch authority, numeric historical charge/calendar reconciliation,
scientific declaration ceilings, current memory/storage/resource admission and
pinned real-host qualification are still separate work before the original four
200-update pilots. No ALC-R0 capability, durable neural learning, portability,
final .alc container or full-objective completion follows from these results.
