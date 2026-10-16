# Original-deadline shared file exclusion

Baseline b3d14bfd7f54602f8cd7d3e2cfc1d238bda33bc0, clean authoritative Desktop.
Previous goal turn PROGRESS: independent reviews and preservation/push of actual
status-to-owned-stop consumer. Next concrete operator publication depends on
operator-before-reservation exclusion. Existing cognition.persistence lock uses
blocking RLock and LK_LOCK/flock LOCK_EX, without an original-deadline argument.
Do not silently route an accepting operator through that unbounded acquisition.

Add alc_r0.deadline_file_lock.deadline_file_lock(path, deadline_ns) contextmanager.
It shares the existing persistence process-path RLock/weak registry/held-paths
tracking and OS byte0/flock protocol, so bounded and existing callers mutually
exclude. Existing persistence API/callers remain unchanged. This is exclusion
only, NOT source provenance, operator installation, reservation or launch permit.

## Ownership and timing

Validate exact positive signed64 absolute monotonic deadline before path work.
Existing ordinary absolute local namespace only; no parent mkdir or deletion.
Reject links/reparse/unsafe aliases; retain ancestors. Acquire registry guard,
shared RLock, and native file lock with nonblocking attempts, bounded20ms sleeps
limited by remaining original deadline. Only retry recognized lock-contention
errno EACCES/EAGAIN; unknown I/O/native errors deny. Windows LK_NBLCK, POSIX
LOCK_EX|LOCK_NB; existing legacy byte0 file format retained. No timeout reset.
After each potentially blocking path/open/write/fsync/native operation check
the same deadline. Cannot interrupt OS calls; external owned-process cleanup
still required and no hard latency guarantee follows from Python checks.

Before entering user body compare regular single-link opened/path identity and
ordinary ancestors; file has exactly one NUL byte after initialization. Existing
oversized/nonregular/multilink/changed namespace rejects. Open a+b creates only
the lockfile, never truncates/unlinks it. Handle stays open throughout native
ownership. Same-thread nested bounded ownership reuses this helper's retained
handle/ancestors, still validates its bytes/path/deadline and must not remove the
outer marker. A legacy-only held marker has no retained validated handle: bounded
nesting beneath legacy-only ownership MUST reject before body, not weaken the
one-NUL contract. Existing legacy nesting beneath bounded outer ownership still
reuses the shared marker normally, which is the intended reservation integration
direction. No second handle/self-deadlocking native reacquisition. RLock count
released exactly once for each acquisition. Different-thread
contention waits bounded; different-process native contention waits bounded.

Mark held path ONLY after OS lock acquired and postchecks succeeded.
Native byte0 lock may extend beyond EOF: initialize an empty file ONLY after
native ownership, not before. Concurrent legacy empty-file initialization may
fail or yield malformed bytes; deny rather than truncate/repair. Cooperating
operator installation should preinitialize its lock before concurrent users.
This is not a guarantee every legacy contender succeeds; neither may enter
simultaneously. Local same-thread legacy nesting does not reopen a lock handle.
On any exception including cancellation after acquisition: release owned native lock,
close handle, release own RLock; remove only own held marker. Native lock unlock
failure propagates, never reports successful exclusion cleanup. Existing empty
claim due abrupt exit can be initialized by a later lock owner (not scientific
control consumption); consumption files are not these lock files. Same file
namespace must remain present; cooperating-host model, no hostile ABA/replacement
or storage rollback proof. Nested outer legacy acquisition may have been
unbounded; this helper cannot retroactively certify it.

## Verification before operator writer integration

Two independent design reviews then RED/GREEN/regression. Test exactdeadline
types/expiry, normal/nested bounded ownership, legacy-before-bounded rejection
including valid/non-NUL/oversized bytes, and bounded-before-legacy success,
exception cleanup, no premature body on thread/process contention, eventual
success after release with same original deadline, stable lockfile retention,
unsafe paths/link/hardlink/oversize/ancestors. Real subprocess hold-and-contend
diagnostics under owned runner, finite readiness and child cleanup, no model.
Run relevant persistence lock and reservation tests as regressions, not whole
ALUCLU portability claim. Native Windows is current target; POSIX code has no
native execution evidence here. Original scientific guard remains denied.

Official Python3.12 API references inspected: msvcrt locking (LK_NBLCK returns
on contention whereas LK_LOCK retries), fcntl LOCK_NB and threading RLock.
These describe APIs, not evidence that this implementation meets its deadline.

Independent design architecture CLEAR identified ownership bookkeeping and legacy
nesting limits. Code REQUEST CHANGES identified the same nested format conflict.
Resolved explicitly by denying legacy-only nested admission rather than claiming
unobserved exact bytes. Bounded outer->legacy nested remains supported, sufficient
for future bounded admission of global reservation lock before legacy internals.
No existing callers change. Corrected design independently code APPROVE and
architecture CLEAR; final implementation/evidence verdicts are in the separate
deadline-lock-evidence document. No operator-writer/launch gate closure.
