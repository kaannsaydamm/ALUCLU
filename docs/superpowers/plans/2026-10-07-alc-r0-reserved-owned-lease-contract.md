# Reserved suspended Windows lease

Status: PROPOSED, pending independent readiness review.
Parent501485f02711eb394732ab9c2203b8b33e01ad9a.
Required scientific execution connection, NOT training admission or final .alc.

## Concrete boundary

checkpoint_owned_process._execute resumes immediately after atomic job-owned
suspended creation. Keep that trusted primitive API unchanged for its existing
callers/tests; do not use it as a scientific bypass. New reserved_owned_process.py
reuses _validate, _Job, _ProcessInformation, _create_suspended, _resume and handle
accounting. No arbitrary pre-resume callback, OS PID discovery/reopen or old-PID
termination. Exact caller commands/runtime/authority still separately verified.

Proposed ReservedOwnedLease(store, expected_owner_root, reservation_id, command,
cwd, environment, stdout_path, stderr_path, deadline_ns, clock_domain_root).
Store must be exact ReservationStore. Construction validates inputs without I/O;
__enter__ acquires global reservation lock, reads independently current owner,
requires matching RESERVED identity and no overrun. Extract original reserve
event via complete journal/history audit; require exact deadline and clock domain
equal stored reserve values. Runtime clock-domain evidence remains the later
trusted coordinator's obligation; caller string alone does not prove same boot.
No new useful allowance. Reject invalid/stale/mismatched input before artifacts.

Then exclusive output creation, devnull stdin and private kill-on-close job;
allocate _ProcessInformation BEFORE acquisition; atomically create suspended child
with existing JOB_LIST/HANDLE_LIST contract. Read GetProcessTimes using the OWNED
process handle, exact creation FILETIME (uint64); no CPU-time-as-GPU-time claim.
Generate secrets.token_hex(16) owner_nonce. Immutable identity fields are PID,
creation_filetime_100ns, owner_nonce. Identity receipt root is SHA256(RFC8785
object {schema:"alc-r0-owned-child-v1", reservation_id, pid decimalstring,
creation_filetime_100ns decimalstring, owner_nonce}). Fields/root exposed for
coordinator evidence, not interpreted as authorization.

Failure during __enter__, including after CreateProcess but before identity,
must drain/close private job and root/thread handles even if __enter__ cannot
return. No absent identity/no-child inference. Keep reservation held; do not
invent terminal evidence or automatically recover pending storage intent.

## Publication and resume

publish_identity(evidence_root,review_root) ONLY while same context owns global
lock and child remains suspended. Verify exact live handle identity/deadline and
current RESERVED state/root. Commit child_created event through ReservationStore;
then commit identity_published using exact child receipt root and publication_root
= SHA256 child_created owner receipt (already durably published). Use same external
evidence/review roots; they are verified input bindings, not boolean approvals.
Update independently held current owner root ONLY after each returned durable
receipt. Require exact matched pid/FILETIME/nonce/receipt in reopened current view.
Return READY PublishedReservation; persisted pending or raised writes prohibit
resume. Repeated publish rejects; context close drains suspended root, reservations
remain CREATED/READY or held prior/uncertain publication, no false release.

resume_verified(expected_ready_owner_root) verifies exact current receipt and
READY matching identity, original clock/deadline and owned handle identity under
the still-held global lock. Require parameter equals locally retained READY root,
re-read the store rather than accepting a forged dataclass. Check root still
nonterminal, thread suspended, no overrun, unchanged deadline. Caller must have
revalidated concrete authority/resource generation BEFORE this call; this OS
primitive does not implement authority producer or treat a READY root as permit.

Call _resume once; if it succeeds, persist running with resume_receipt_root =
SHA256(RFC8785 {schema:"alc-r0-owned-resume-v1", identity_receipt_root,
ready_owner_root, resumed_monotonic_ns decimalstring}). No second resume. If resume
or running-publication fails, drain only owned job and keep reservation held.
Running-publication failure may leave active child briefly until cleanup, never
return a successful launch acknowledgment. After durable RUNNING publication,
release global lock; do NOT hold it throughout worker execution. Other cooperating
reservations can proceed. New attempt/resume still governed by existing RunSpec.

## Terminal and cleanup

wait_terminal(): only successfully resumed context; same absolute deadline,
existing polling/privatejob accounting, timeout terminates/drains owned tree.
Observe original root handle terminal plus active_processes=0 before receipt;
return existing OwnedProcessReceipt plus retained identity/current owner root.
On exceptions/exit, bounded existing10second cleanup tail, never renew useful
deadline, always close owned process/thread/job/output handles. No swallowing
cleanup/observation failure or labeling reservation released on PID absence.

This component DOES NOT release or reconcile allocation charge automatically:
terminal observation feeds the external coordinator's complete verified terminal,
charge and growth records. Until those are committed, reservation stays held.
Context exit without resume kills suspended root without output-side execution.
Context reuse/re-entry, double publication/resume/wait and use after close reject.
Methods intended for one trusted coordinator thread, not concurrent lease access.

## Tests and complete next dependencies

TDD missing-module RED, then harmless actual Windows subprocess tests with
temporary sentinel. No sentinel before publication/resume; READY proof and exact
handle-derived identity; invalid owner/state/deadline/clock and forged receipt
deny before resume; close-before-resume drains process without sentinel; normal
completion/nonzero/timeout descendants; persisted READY survives close and keeps
charge; running failure cleans owned process; unrelated child survives; fresh
store read verifies identity and ordering. No monkeypatch/global mutation; bounded
test subclass can fail at protected publication boundary for diagnostics only.
Actual parent abrupt termination test must prove privatejob closes before claiming
process-crash orphan prevention. No host/GPU/model/held-out assets in fixtures.

Every exact test/source invocation independently reviewed before execution;
original native handle terminal personally observed, no source edits while live.
Relevant owned-process/store/state regressions and exact stored evidence follow.
Numerical accounting/calendar, authority producer, bounded output sinks/log caps,
concrete q/v/host work ceilings/resources remain actual-launch dependencies.
Then pinned-host qualification and original4x200update pilots; no new method
approval or change to original grid, schedule, thresholds or allowance.

Win32 primary references:
- https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes
- https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-resumethread
