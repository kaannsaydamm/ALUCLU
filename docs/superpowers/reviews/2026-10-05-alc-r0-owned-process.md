# Checkpoint160: owned Windows process primitive

Scope: trusted Windows10+ x64 OS ownership, not experiment launch admission,
scientific qualification, a security sandbox, or cross-platform acceptance.
Parent source commit: `e2aef2468f542a277943bac52520abea8234d018`.

## Contract and repair

`run_owned_process` accepts an explicit existing absolute executable, immutable
arguments, existing absolute cwd, explicit environment, distinct absolute new
stdout/stderr paths, and an absolute monotonic deadline established by its caller
before preflight. No shell, executable search, overwrite, PID enumeration or
generic process kill is performed. Admission errors launch nothing. Failed setup
can leave empty/partial output files; file presence is never a completion claim.

The first implementation separately assigned a suspended process to a private
job. Both independent reviewers found a genuine interruption interval between
creation and assignment. Two new real, bounded fixtures reproduced an orphaned
suspended root for both helper-return exception and abrupt supervisor exit. An
outer test job owned and terminated the intentionally broken fixture tree.
Earlier passing21/1410-case tests did not override this defect.

The final implementation uses native `CreateProcessW`, a writable Unicode command
buffer and `STARTUPINFOEX`: HANDLE_LIST restricts inherited handles to three
dedicated stdio copies, and JOB_LIST associates the private job at creation time.
The job is unnamed, non-inheritable, KILL_ON_JOB_CLOSE, without breakaway flags.
Windows10+ x64 is explicitly required; unsupported platforms have no fallback
that reintroduces separate assignment. The output PROCESS_INFORMATION exists
before acquisition under a finally guard. Helper return/cleanup interruption
cannot hide its process/thread handles. Resume occurs only after checking the
original deadline. [Microsoft attribute contract](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute),
[extended startup structure](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-startupinfoexw),
[Microsoft SDK constants](https://raw.githubusercontent.com/microsoft/win32metadata/main/generation/WinSDK/RecompiledIdlHeaders/um/WinBase.h).

Completion observes whole-job active-process accounting, not root exit alone.
A root may exit0 while a live descendant causes timeout: both facts remain in
the receipt. Timeout targets only the private owned job. One absolute cleanup
deadline is shared across drain, exit retry and root terminal observation, without
renewal. All ordinary child processes must drain before a success receipt.
On cleanup/accounting API failure the job closes as a fail-safe, but an exception,
not a verified-drain receipt, is returned. Original chained failures must be
preserved by the eventual attempt journal.

The receipt reports root PID/exit, timeout, monotonic start/end, total/active job
processes and kernel/user CPU time in100ns units. PID is diagnostic only. CPU time
is not GPU consumption; root exit0 is not D/E or scientific acceptance.

## Tests and negative evidence

All child fixtures load only stdlib code; no actual model/tokenizer/corpus/CUDA
or task training was launched. The test runner imports existing project/Torch
dependencies for selected component regression. Direct child module loading
avoids importing those dependencies inside crash fixtures.

| Run | Actual pytest exit | Tests/failures/errors/skips | Seconds | Boundary |
| --- | --- | --- | --- | --- |
| REDv1 | 2 | 1/0/1/0 | 11.191 | Missing module collection error |
| Focusv2 | 0 | 18/0/0/0 | 16.591 | Initial separate assignment |
| DeadlineREDv3 | 1 | 21/1/0/0 | 20.038 | Expired deadline still resumed |
| Focusv4 | 0 | 21/0/0/0 | 16.759 | Before atomic ownership repair |
| Regressionv5 | 0 | 1410/0/0/0 | 137.110 | Before atomic ownership repair |
| AtomicREDv6 | 1 | 2/2/0/0 | 95.318 | Two real suspended-orphan reproductions |
| Atomicfocusv7 | 0 | 28/0/0/0 | 33.748 | Before mutable-buffer argument fix/final controls |
| Atomicfocusv8 | 0 | 33/0/0/0 | 42.145 | Final bytes; terminal consumed by root |

Final33 controls include explicit argv/environment/streams, nonzero exit, ordinary
root+descendant timeout, exited-root/live-child timeout, normal descendant finish,
unrelated owned fixture survival, malformed admission, no output overwrite,
attribute/resume errors, deadline expiry after atomic creation, post-resume and
pre-return abrupt owner death. Independent duplicate root handles prove terminal
state on OSError/KeyboardInterrupt at creation/resume and injected cleanup or
accounting failure. Additional controls cover non-renewing cleanup deadline,
native x64 structure sizes, environment key case collisions and no increase in
parent handle count across six repeated successful launches after warmup.

AtomicREDv6 printed Windows exception `0x8007000e` in
`platform._wmi_query -> platform.machine -> torch._load_dll_libraries` during
collection, remained live, then ran the two tests and produced the listed XML.
The same diagnostic appeared during final regressionv9 collection. This is an
observed runtime initialization diagnostic, not evidence of actual model failure
or permission to patch globals/restart a live run. Full raw console stderr was
not persisted as a separate artifact; the observed stack location/code is
recorded honestly. Runtime-health/launch admission is not certified here.

JUnit XMLs and exact SHA256/provenance are under
`results/alc_r0_owned_process_*_20261005.xml` and
`results/alc_r0_owned_process_20261005.provenance.txt`. Selected regression repeats
checkpoint159's47 explicit targets, prepending this new test file; the same three
actual-host/CUDA tests remain explicitly deselected. It is not a whole-repo suite.
Final regressionv9 **CRASHED**: root consumed original session68329 terminal
actual pytest exit `-1073740022` (`0xc000070a`), with the Python stack in
`subprocess._wait` at the unrelated-process survival fixture line98. XML is absent;
no case totals or artifact SHA are invented. Microsoft names this status
STATUS_THREADPOOL_HANDLE_EXCEPTION; that identifies the status class, not its
root cause in this run. [Microsoft NTSTATUS definitions](https://raw.githubusercontent.com/microsoft/win32metadata/main/generation/WinSDK/RecompiledIdlHeaders/shared/ntstatus.h).

A standalone stdlib-only control loaded the exact module with importlib and ran
three iterations of200ms owned timeout plus a separate500ms Popen wait. All
returned timed_outTrue/active0/unrelatedexit0, actual exit0. This narrower control
did not reproduce the broad-context crash and does not replace final regression.
The initial inline launcher had a quoting SyntaxError and PowerShell
command-not-found; corrected literal here-string execution is recorded separately.
Diagnosis and final regression remain OPEN; static approval is not completion.
The same control after a Torch-only import also passed three iterations, actual
exit0, without model/tensors/CUDA operations. This does not identify a repaired
runtime dependency. One identical selected-scope crash reproductionv10, with
stdout/stderr separately captured, is live under original tool session41087.
Latest workerCPU observation advanced35.984375 to42.5625seconds; stdout/stderr
remain0bytes and XML is absent. Buffered console silence is not terminal success
or proof of a hang. No source edits/restart occurred during the live reproduction.

## Independent review and residual limits

### Subsequent terminal evidence and unresolved runtime diagnosis

Original session41087 subsequently terminated with personally consumed
`pytest_exit_code=0`. The v10 XML was independently parsed:1422 tests,0 failures,
0 errors,0 skipped,1177.101seconds. SHA256:
`8705b67128df0d5ef9da8d784f080efe3b7fdf853e4f6f17292ace1a1da5b1e9`.
Stdout1620bytes contains progress through100%; stderr0bytes. The source and test
hashes below were rechecked unchanged. Earlier live observations above describe
their observation time, not current state. This is selected-scope regression
success, not a repaired dependency or a whole-program acceptance verdict.

A read-only Windows Application Error1000 event corroborates v9:2026-10-05
04:57:25.2430872+03:00, PID25056, python.exe, ntdll.dll10.0.26100.9444,
exception0xc000070a, offset0xc87a4, report8f414888-44d0-4494-a13b-b94df7d82376.
The actual interpreter is the uv CPython3.12 installation behind the venv.
The event identifies the native fault, not its origin.

[Official CPython issue125315](https://github.com/python/cpython/issues/125315)
reports nondeterministic Windows crashes from slow WMI calls and caller-stack
data lifetime. In the [3.12.13 source](https://raw.githubusercontent.com/python/cpython/v3.12.13/PC/_wmimodule.cpp),
the query thread retains a pointer to the caller's stack struct; in
[current main](https://raw.githubusercontent.com/python/cpython/main/PC/_wmimodule.cpp)
it copies that struct. Given the preceding WMI warning, this is a plausible
dependency candidate, not a proven cause of v9. Exact uv binary/source
correspondence is unverified. No global monkeypatch, dependency replacement,
system change or scientific threshold change was made. Runtime diagnosis and
actual launch qualification remain OPEN; v9 remains a first-class negative result.

The subsequent preregistered v11 stdlib-only platform control did not reproduce
a native crash. Its100-iteration loop reached38 before the30s absolute deadline;
the personally consumed receipt reports child exit124, timed_outTrue,
30.156seconds,31 total processes and0 active processes. Parent launcher exit0 is
not child success. No WMI permissions/services/runtime were changed and no
project/Torch/model code was imported. This incomplete bounded control neither
establishes the absence of the race nor a causal explanation of v9.
The [3.12 backport126203](https://github.com/python/cpython/pull/126203)
merged4a846f2 with the query-string copy already present in3.12.13. Therefore
the source comparison is not evidence that this interpreter lacks that published
fix. Any remaining struct-lifetime issue and its connection to this native crash
still require stronger evidence; do not label v9 a confirmed upstream bug.

Final source SHA256:
`5265eebafb79f56c57f495e769ce941c2f6eacbfabeef560f52c734d84188565`.
Final tests SHA256:
`bf0f27557efd2b7b31cb1beca55841fd6aa7eae986c5e724656cf811fa228d9b`.

Two independent GPT6.1Sol lanes read both complete final files and personally
verified these hashes. Code/security: APPROVE, contingent on parent terminal
validation. Architecture: CLEAR for this primitive. Original acquisition gap,
deadline renewal and insufficient root observations were explicitly re-reviewed
and resolved. Neither lane executed/imported code/tests/models, edited files, or
consulted the other. Approval does not extend to an actual experiment invocation.
After v10 terminal, both existing lanes independently rehashed final code/tests
and parsed the actual v10 XML/hash. Code lane retained primitive APPROVE;
architecture retained primitive CLEAR with runtime qualification WATCH. Both
explicitly require checkpoint completion to remain OPEN pending diagnosis.
The actual original tool-session exit observation is parent evidence, not an
independent reviewer action. No speculative primitive repair was recommended.

Residual boundaries:

- Ordinary CreateProcess descendants only. Privileged/WMI escape paths are not
  a hostile-process sandbox guarantee. [Microsoft Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).
- Dedicated inheritable stdio copies exist briefly during creation. HANDLE_LIST
  restricts this launch, but cannot prevent a concurrent unrelated launcher in
  the same process from inheriting all process-wide inheritable handles. The
  actual launcher must be a dedicated/cooperating supervisor with explicit launch
  discipline, not a concurrent general-purpose arbitrary-command service.
- Cleanup policy bounds polling/waits, not an OS call that itself stalls. Failed
  accounting/drain returns no success receipt even when kill-on-close is used.
- No actual pinned model D/P11/E, fresh GPU repetitions, Linux/macOS portability,
  GPU consumption ledger, durable interaction learning or ALC proof occurred.

## Remaining launch gates

Exact committed source/runtime/asset authentication, reviewed exact invocation,
reconciled historical600-GPU-hour consumption and first-development date,
program25GiB limit/C20GiB free-space admission, append-only attempt reservation
and terminal journal, complete synchronized GPU/resource measurements and
wrapper-inclusive45min deadline remain mandatory before actual model execution.
The full unified objective remains ACTIVE. These primitive tests do not establish
ALC-R0, neural acquisition, durable generations, preference learning or portable
`.alc`; the dependency roadmap and frozen scientific gates remain unchanged.
