# Bounded binary output: isolated runtime evidence

Parent364c257d69623d88e5ba98d59965f1c50209d527.
Status: scoped isolated component accepted, code APPROVE / architecture CLEAR.
Both independent lanes verified exact final inputs, all ten artifact groups and
their honest lineage. Parent native-handle observations remain distinct evidence.
Scope: isolated reference capture component on Windows x64, not scientific lease
integration, model training, R0 capability or whole-program completion.

## Exact final inputs and execution

- Contract: 0d67a133c8ec271557909abe90f3a32f665fcb3373929ca0a0d593b0bee24764.
- Source: c8f24b9d6e8730878a5e6df556517c0554f1f7af07743c3531f9547c56c471f6.
- Tests: 37d4ccd1945ac5ac50014a29285aa601e8631075e609c6830800c004461ad98c.

Existing CPython3.12 Windows research venv:
`C:\Users\kaann\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\ALUCLU\research\alc-r0-smollm2-135m-v1\windows-training\.venv\Scripts\python.exe`.
Authoritative cwd is Desktop `.worktrees/unified-lifelong-cognition-local`, not
the old OneDrive checkout. Environment: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1,
CUDA_VISIBLE_DEVICES=-1, PYTHONNOUSERSITE=1, PYTHONDONTWRITEBYTECODE=1,
PYTHONPATH=<authoritative worktree>/src. No installs/assets/corpus/model/GPU work.

Final isolated args:
`-m pytest -q tests/test_alc_r0_bounded_process_output.py --junitxml=results/alc_r0_bounded_output_final_green_v2_20261008.xml`.
Then, only after observed exit0/zero issues and rechecked exact input hashes:
`-m pytest -q tests/test_alc_r0_bounded_process_output.py tests/test_alc_r0_reserved_owned_process.py tests/test_alc_r0_owned_process.py tests/test_alc_r0_reservation_store.py tests/test_alc_r0_reservation_state.py --junitxml=results/alc_r0_bounded_output_final_regression_v2_20261008.xml`.

Both original hidden native handles were retained. Isolated wait bound60s;
regression total90s as60+30 on its same original handle, not a restarted job.
No edits while live. Parent personally observed PID29444 exit0 (toolf46394), then
PID23416 exit0 (native session46395, tool96f09a), both without timeout. Stored
exit.json retains original_handle_terminal=true; that record is supplementary,
not a substitute for the parent observation. All ten stderr files are empty.

## Preserved experiment lineage

Every stem below is under results and has stdout.log,stderr.log,exit.json,xml.
JUnit order is tests/failures/errors/skips; times are JUnit durations, not a
scientific GPU allocation charge. Names are artifact identifiers, not clock proof.

| Stem | Native PID / exit | JUnit | Seconds | Interpretation |
| --- | --- | --- | --- | --- |
| alc_r0_bounded_output_red_20261007 | 3920 / 2 | 1/0/1/0 | 0.452 | Expected absent-module collection error |
| alc_r0_bounded_output_cleanup_red_20261007 | 8980 / 1 | 36/3/2/0 | 0.735 | Three source failures; two Windows pytest-ID fixture errors |
| alc_r0_bounded_output_green_20261007 | 20316 / 0 | 36/0/0/0 | 0.505 | Intermediate source, not final |
| alc_r0_bounded_output_regression_20261007 | 18444 / 0 | 174/0/0/0 | 76.638 | Intermediate source, not final |
| alc_r0_bounded_output_writer_time_red_20261007 | 6100 / 1 | 1/1/0/0 | 0.541 | Clock-ordering fixture failure, NOT source reproducer |
| alc_r0_bounded_output_writer_time_red_v2_20261007 | 28724 / 1 | 1/1/0/0 | 0.424 | Actual late-writer DID NOT RAISE |
| alc_r0_bounded_output_final_green_20261008 | 2968 / 0 | 38/0/0/0 | 0.596 | Before pipe-rollback repair, not final |
| alc_r0_bounded_output_pipe_rollback_red_20261008 | 25928 / 1 | 1/1/0/0 | 0.403 | Actual open-writer descriptor DID NOT RAISE |
| alc_r0_bounded_output_final_green_v2_20261008 | 29444 / 0 | 40/0/0/0 | 0.390 | Final isolated bytes |
| alc_r0_bounded_output_final_regression_v2_20261008 | 23416 / 0 | 178/0/0/0 | 47.169 | Final five-file relevant regression |

XML SHA-256, in table order:

1. d18bf7d11e2d359483f40679f24d86de4174ff51b7bd661f9569446eca91c99d
2. a96ee5cdc3ec801ed552cf4a33b6bc0652287441b274b280829e69db5c77c202
3. da2736c1b3b795d5d4eb6ab33cd2bae26d3742dbe23ca7b3a62e0e81270c0fda
4. 2ee0af5a1261044f19b29139f2d22483966d2de17c8e0634d46a7d72ab07786d
5. 9c1e28ab56b390c612e27cf2b65ba591bd8180067230ed015fb6ff3984dd86d5
6. f52094db69f407d813e33378697f86b502fbaa02786f490219abbd8c022593b8
7. eadabf5cc6040d5f31cb89a83a093ac920cdf04c308bf42dc6005ee2a97a3c51
8. e948ed36b57bfb384e69e7fb40cfbc4fa844ed7cb36f452624b21a992f77e68b
9. c3a5663deb85018d2864833a1652aabe92f2a30ba310864c71b3ea832e40f5e4
10. 95660ea18b66f5b17dd507cf6c813d90c6a1ae1bb54b44016b46e277ed47c572

## What the final evidence establishes

40 isolated cases cover zero/exact/cap+1/binary/131073-byte output, independent
stderr limits, checked structural values and paths, expired entry, exclusive
file preservation, single-use lifecycle, tighten-only cleanup, short writes,
terminal read errors without EOF, uncertain partial writes and file digests,
partial acquisition and failure after actual thread start, blocked-I/O observations,
uncertain reader/destination/writer closure, retained failed finish, actual late
parent-writer closure rejection and delayed observation of timely closures.
Internal pipe rollback closes the other known-owned end even if reader rollback
raises; public acquisition retains unknown close effects instead of inferring
complete cleanup from absent stream fields. No uncertain raw-fd retry is used.

The 131073-byte payload was never reduced: short pytest IDs fixed a Windows
32767-character environment-variable error. Writer timing uses an observed later
monotonic tick rather than subtraction pretending to establish event ordering.
These fixture failures are retained separately from genuine source failures.

Two fixed65536-byte pump reads and release-before-next-read establish a structural
payload-buffer ceiling of131072 bytes, not a measured whole-process RSS ceiling.
The receipt is frozen and separates received/confirmed/persisted bytes, known
digests, output invalidity, EOF, terminal observations and resource closure.
Early writer-close errors do not bypass remaining cleanup. Both pump completion
and first confirmed parent-writer closure must fit one retained effective bound.

## Claims still closed

Five-file regression includes harmless owned Windows children for the previously
accepted lease/store primitives. Combining them with sink tests is NOT proof
that this sink is integrated into the lease. Integrate audited declaration caps,
creation-path writer closure and violation checks next, then execute actual
binary/spam/descendant/failure/timeout subprocess tests on that final source.

Arbitrary filesystem I/O is not guaranteed interruptible. Unobserved pump or
uncertain pipe cleanup remains incomplete and cannot support release/reconcile.
This reference component is not a filesystem sandbox or hostile-host guarantee.
No native macOS/Linux portability, capacity benchmark, host qualification,
learning, restart/remount capability or ALC-R0 PASS follows from these results.
Operator authority, scientific declarations/resource admission, historical numeric
charge/calendar, pinned-host qualification and the original four200-update
pilots remain subsequent requirements. Full original objective remains active.
