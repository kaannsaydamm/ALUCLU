# Reserved lease bounded-output integration

Status: revised design readiness APPROVE / CLEAR from independent code and
architecture lanes. No implementation acceptance or scientific launch admission.
Source parent: 355568b4f8f4490f3315b32e827070b6f4ac571c.
This is a launcher dependency, not model training or a scientific PASS.

## Authority and budget preservation

The owner's accounting-method and local-training direction are already recorded
in 2026-10-07-alc-r0-owner-accounting-decision.md. Do not re-request that decision,
erase earlier local control runs, reset the 600 GPU-hour allowance or 45-day clock,
or infer numeric accounting from that approval. Original model, grid, thresholds,
four 200-update feasibility jobs and held-out boundaries remain unchanged.

## Integration interface

Keep ReservedOwnedLease constructor and the legacy checkpoint-owned primitive
unchanged. Add a mandatory output: BoundedOutputReceipt field to the immutable
ReservedTerminalReceipt. Exit zero is not output validity or learning success.

Under the existing reservation lock, retain the audited RESERVED view and parse
its canonical declaration. Use its stdout_limit_bytes, stderr_limit_bytes and
cleanup_ceiling_ns; no caller overrides or invented caps. Check that the original
useful deadline plus the declared cleanup tail fits the supported integer range
before creating output artifacts. The declaration already requires a 10-second
cleanup tail; this integration must not allocate another tail.

Acquire the private job, stdin and BoundedOutputPair using exclusive destinations.
Retain ownership before acquisition can fail. Pass only the binary pipe writers
to the existing atomic suspended CreateProcess HANDLE_LIST/JOB_LIST path. Close
parent writer copies in a finally surrounding creation, including a partial
creation failure. Never pass destination files or pipe readers to the child.

## Lifecycle and terminal ordering

Check output violations around publication and immediately before resume. The
child stays suspended if output admission fails. Check again after RUNNING
publication and during the original-deadline wait loop. A RUNNING output violation
terminates only the owned private job; it must not be labeled a deadline timeout.
An already exited child can still have invalid output, discovered during final
drain. Return honest invalid output facts only when complete cleanup is proven.

Pin one effective cleanup deadline at the first cleanup/terminal observation:
min(original useful deadline + declared cleanup tail, now + declared cleanup tail).
Retain it in the lease and assign it to the private job before its first cleanup
operation. Tighten the sink's constructor-pinned upper bound to this same deadline
at final observation. Never renew it on retries, exceptions or context exit.

Partial sink entry must obey that same early-failure bound BEFORE its internal
wait, not after the exception reaches the lease. Use a private fixed integration
subclass _LeaseOutputPair in reserved_owned_process.py, constructed only by the
lease with its own retained ownership. Its protected _partial_observation override
first invokes the lease's idempotent _pin_cleanup_deadline, tightens its retained
sink deadline to that value, then calls the existing superclass partial observer.
No arbitrary public callback or caller-selected subclass. At this acquisition
stage child creation has not begun, so there is no running child to drain first.
The job already exists and receives the same deadline before observation begins.
Standalone BoundedOutputPair behavior stays unchanged. Successful entry keeps
the original useful-plus-tail upper bound until real cleanup begins; do not pin
entry-time-plus-ten-seconds for a legitimate long useful run.

Close parent writers, drain/observe the entire private job and original process
handle, then observe both original pump threads and their resource closure within
that shared bound. Preserve process identity and current owner root. No automatic
reservation release, charge reconciliation or inference from PID absence.

Required partial-entry diagnostic: a protected test-only subclass starts an
actual owned pump whose read waits on a bounded gate, then raises on the second
start. Record the effective job and sink deadlines BEFORE releasing that gate;
prove they are equal and pinned before internal observation. A separate bounded
fixture observer releases only that owned gate so the test cannot leave an
unbounded live pump. An elapsed bound must remain incomplete cleanup, not PASS;
fixture timing may be shortened only as an explicit diagnostic seam, never by
changing the audited scientific cleanup declaration.

Failure cleanup must attempt owned thread/process/job handles and lock release
even if output cleanup raises. Do not forcibly close a pump's in-flight descriptor
or terminate unrelated processes/threads. Unknown pump/handle closure remains a
cleanup failure with held reservation, not a complete terminal receipt. Partial
sink acquisition retains its original uncertainty; no fabricated valid receipt.
Filesystem I/O is not universally interruptible; integration acceptance must not
claim universal cancellation or unrestricted-host sandboxing.

## Required execution evidence

Use real temporary Windows child processes, never model/GPU/corpus/held-out data:
exact and empty output, zero cap, first excess byte, independent stdout/stderr,
binary output, sustained excess, exited root with live writing descendant,
normal/nonzero/timeout, creation and publication failures, unrelated-child
survival and abrupt parent-crash regression. Verify actual file bytes and digest,
declaration-derived caps, validity, original owned terminal and active-job zero.

First reproduce the current missing cap enforcement with a narrowly bounded
cap+1 RED on unchanged production bytes. Review exact source/tests and invocation
independently before running. Then implement, run GREEN and relevant unchanged
owned-process/reservation/output regressions. Personally observe original native
test handle termination; stored XML/exit records are corroborating evidence only.
Preserve negative artifacts and every material step in TRAJECTORY.md.

## Remaining after this checkpoint

Concrete launch authority, numeric historical charge/calendar reconciliation,
fixed scientific declarations, current resource admission and pinned real-host
qualification remain separate prerequisites. Only then launch the original local
feasibility pilot; no paid external compute or silent CPU/GPU fallback.
