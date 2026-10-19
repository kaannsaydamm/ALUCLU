# Bounded scientific process output

Status: PROPOSED; pending independent readiness review, no implementation/launch.
Parent364c257d69623d88e5ba98d59965f1c50209d527. Required research-launch boundary,
not final .alc/product infrastructure. Original scientific limits unchanged.

## Gap and design choice

The accepted Windows lease exclusively opens stdout/stderr files but does not
enforce declaration byte caps. Polling file size after writing cannot enforce an
exact disk-output upper bound. Use owned binary pipes and two bounded parent
reader threads, with exclusive destination files. The child receives only pipe
write handles through the existing HANDLE_LIST/JOB_LIST creation path. It never
receives destination file handles. Trusted worker/path assumptions remain; this
is not a filesystem sandbox or protection from a hostile privileged host.

First isolated component: bounded_process_output.py with BoundedOutputPair(
stdout_path,stderr_path,stdout_limit_bytes,stderr_limit_bytes,cleanup_deadline_ns).
The required cleanup deadline is an explicit absolute monotonic positive int
<=2^63-1, excluding bool, structurally validated without I/O. Constructor is
structural/no I/O; exact ints excluding bool in0..2^63-1, absolute distinct paths.
No cap allocation: each of exactly two pump threads reads at most65536 bytes per
iteration. Fixed buffer bound is at most131072 payload bytes across both pumps,
not a whole-process RSS claim. Values come from the audited reservation declaration
in later lease integration, never invented defaults or scientific budget changes.

Context enter requires the pinned deadline unexpired BEFORE artifacts. Acquire
both exclusive destinations and both pipe pairs before starting either pump;
retain each pump/thread and its handle ownership before attempting start.
On partial entry failure, first close every parent writer, then observe started
pumps against the SAME constructor-pinned deadline. Parent closes only proven
not-transferred handles; started pumps finally-close their readers/destinations.
An uncertain start is not proof no thread acquired handles: retain unknown facts
and deny complete cleanup if original thread termination cannot be observed.
Preserve existing files and causal acquisition/cleanup failures.
Expose stdout/stderr writer streams for the existing creation helper. After
CreateProcess, close_parent_writers() closes the parent's original writer copies,
in finally even if creation/identity fails. Only the child retains those pipe
writers. No inheritance of job, read or destination file handles.

## Exact caps and failure facts

Each pump writes at most its cap. Count actual received/written bytes with checked
integer arithmetic; update the written count/digest only for confirmed successful
write slices (handle short writes). Zero cap permits only empty output. The first
received byte beyond cap marks excess/INVALID. Continue draining/discarding to
avoid backpressure deadlock until the coordinator terminates its owned job. A
write/read error marks output incomplete/INVALID, never a valid partial receipt.
Unknown counts after an observation failure are unknown, not silently zero.
No unbounded line reads, decoding, queued chunks or in-memory output retention.

Pair exposes thread-safe immutable per-stream observations with EXACT fields:
limit_bytes; received_bytes (int or null on arithmetic/observation uncertainty);
received_complete; confirmed_written_bytes (sum of confirmed successful writes);
persisted_bytes (int or null if write effects/close are unconfirmed); excess;
eof; terminal; resources_closed; failure_kinds (sorted unique tuple from read,
write,close,acquire,thread_start,overflow,cleanup_deadline); confirmed_prefix_sha256
(null until a destination/prefix is established); file_sha256 (null unless entire
persisted contents are known); finished_monotonic_ns (null until pump terminal).
Counters are0..2^63-1 excluding bool, no overflow clamp; digest roots are64hex.
All live snapshots acquire only a short bookkeeping lock, NEVER hold it across
read/write/close/join or other potentially blocking I/O. No exception messages or
tracebacks/unbounded error data are retained in these observations. Its
violation/error signal is used by the lease's original-deadline wait loop to
terminate/drain only its owned job. A worker may briefly run until that check,
but persisted output cannot exceed the cap. Publication/resume overhead remains
charged; no observer thread authorizes resume or changes reservation state.

received_bytes counts bytes actually returned by successful parent reads, NOT
attempted child output. Read failure means received_complete=false, without
erasing already observed bytes. Write failure leaves confirmed prefix/count
honest, persisted_bytes/file_sha256 unknown when effects cannot be established;
no digest covers unconfirmed bytes. A read error can leave a known persisted
prefix/file even though the child's complete stream was never observed.

## Terminal ordering and incomplete cleanup

Sink pair alone has no authority to discover or kill processes. Coordinator must
close parent writers and drain its private job/root BEFORE final sink observation.
Constructor pins a complete cleanup upper-bound deadline before entry. For later
lease integration that bound is the already reserved original useful deadline
plus declared10second tail; it does not renew useful work. finish(optional earlier
cleanup_deadline_ns) may tighten that retained bound to the job's SAME existing
tail deadline, NEVER accept a later one. Partial-entry and __exit__ paths use the
same retained bound; isolated tests supply their own explicit bounded fixture
deadline before entry, never an implicit new10seconds. Validate lifecycle/value
before waiting. Sequential joins use remaining time from that one bound.

Return immutable BoundedOutputReceipt with EXACT fields stdout,stderr (the above
stream observations),cleanup_deadline_ns,valid. Require both pumps terminal and
resources_closed; finished timestamps must fit the retained bound. An already
terminal pump observed after deadline is acceptable only if its captured finish
timestamp fits. A terminal read/write-error pump without EOF may return an
explicitly INVALID diagnostic receipt if owned resources are confirmed closed;
EOF is required for valid=true, not for a truthful invalid failure receipt.
valid=true requires both EOF/received_complete,known file digests/persisted counts,
no failure_kinds,no excess and complete resource closure. Exit0/JSON parsing never
overrides invalidity. A resource-close error or unobserved terminal raises cleanup
failure rather than returning a supposedly complete pair receipt.

finish is single-use; repeated calls reject and cannot grant a later deadline.
__exit__ first closes parent writers, then finishes if not already observed;
successful cached terminal facts may be reused only for idempotent cleanup,
not a second execution receipt. After failed finish, exit retains/reports the
failure and original bound without another wait allowance. No unbounded join.

Failure to observe pump termination raises bounded cleanup failure and retains
the reservation/unknown cleanup facts. Do not forcibly close another thread's
in-flight file descriptor, kill unrelated threads, silently abandon a thread or
return success. Each started pump owns/finally-closes its reader and destination
handles. Parent writer handles close even on failure. A daemon pump that cannot
be observed terminal by the bound may still own those handles until its I/O ends;
that is explicitly incomplete cleanup, not a proven leak-free/fully terminal
receipt. Complete resource reconciliation/release is forbidden in that case.
Filesystem I/O is not guaranteed interruptible by this design; if tests establish
a real missing bounded-cleanup capability, implement an owned cancelable I/O path
or report the concrete limitation before scientific adoption, not a fake PASS.

## Isolated TDD then lease integration

Missing-module RED; isolated GREEN uses only temporary files/owned pipe writes:
exact cap,zero cap,first excess byte,one excess stream,short writes/fault boundary,
partial construction failure,EOF,deadline expiry,closed/reused contexts and fixed
buffer behavior. Diagnostic seams are protected bounded methods, not monkeypatch
or arbitrary callbacks in production. All exact invocations independently admitted.

After isolated acceptance, integrate audited declaration caps into the Windows
lease. Existing APIs/legacy primitive remain trusted-only; no scientific bypass.
Store caps in the lease on enter under the global lock. Close parent writer copies
after creation; check sink failure during RUNNING wait and around terminal. Reuse
job's single cleanup tail. Terminal receipt includes output validity/facts while
preserving original process identity/current reservation root. No automatic charge
release. Required real subprocess tests: exact/empty/cap+1/spam/binary stdout and
stderr,exited root with live writing descendant,nonzero/timeout,creation/publication
failure,no unrelated termination and original source/test/worker regression.

Operator authority/revocation, fixed scientific declarations/ceilings, current
memory/storage/peak growth, historical numeric charge/calendar and pinned real
host qualification remain separate prerequisites. Original four200-update pilots
follow those gates. No model/GPU/assets/held-out work is admitted by this proposal.
