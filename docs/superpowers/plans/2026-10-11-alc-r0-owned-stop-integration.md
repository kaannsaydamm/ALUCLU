# One-way coordinator stop integration in the existing owned lease

Status: implementation and retained final native regression independently closed
code APPROVE / architecture CLEAR; scoped termination plumbing only.
Parent c8d45368f09988d359c886e6dbf6ac9d608b88eb. Reuses existing Windows lease,
owned process handles, private job, reservation lock and shared cleanup tail.
This is necessary termination plumbing, NOT trusted observation/admission or a
live authority monitor. Scientific production worker remains denied.

## Fixed denial-only signal

Add OwnedStopSignal and OwnedStopRequested(RuntimeError) to
reserved_owned_process.py. Signal owns one private threading.Event with no public
clear/reset/reason/callback. request_stop() sets it, repeatedly/idempotently from
any coordinator-owned thread. Internal read uses the exact Event class method,
not an instance-overridable callback; validate exact Event and bool result.
Exact signal type only; reject subclasses, events, booleans and objects before
acquiring resources. Constructor optional keyword stop_signal=None preserves
trusted low-level legacy behavior, not scientific authority. Unset signal is
never evidence of authorized execution. Malformed private internals deny.

Lease retains signal and a local observed-stop latch. _check_stop() raises the
fixed OwnedStopRequested if set, and latches observed stop forever for this lease.
No arbitrary user callback, module selector, PID discovery or cross-thread lease
operation. Owner thread still solely creates/publishes/resumes/waits/closes;
monitor thread can only request stop. Cooperating trusted-host assumptions remain,
not protection against arbitrary Python/OS memory mutation.

## Placement and cleanup

Check inside existing exception-cleanup regions: entry before reservation lock,
again immediately before _create_suspended after output setup; identity publication
before work and after durable READY publication; resume before replay and directly
before _resume, plus after durable RUNNING publication before unlocking. Pre-set
signal denies before output files/child creation. A signal during entry cannot
resume a child; later resume checks deny and close exact retained handles.

wait_terminal checks before looping, on every active-tree iteration, after the
active tree reaches zero and before constructing a terminal receipt, and after
output.finish immediately before returning. Stops raise, never return a successful
terminal receipt even if the root already exited0 at the check. Existing exception
path _close pins the SAME cleanup tail, terminates/drains ONLY retained owned job
and root, closes handles/output and unlocks. Cleanup failure remains failure and
unknown reservation; no inferred release, refund, synthetic terminal charge or
new ten-second tail. Journal state remains as last durably committed, including
RESERVED/CREATED/READY/RUNNING; stop does not roll back durable publication.

Every check is a linearized observation, not atomic with future event setting or
external authority changes. A signal set after final return is not retroactively
observed; real coordinator must separately revalidate final authority before
accepting output. This seam cannot replace precreation/preresume trusted checks
or active observation. Existing20ms polling sleep gives a nominal check cadence,
NOT measured worst-case20ms/520ms host enforcement. No tight timing assertion on
CI scheduling; prove actual bounded cleanup/zero owned members instead.

## Tests and acceptance

TDD tests first: absent stop-signal support produces intended RED. Test immutable
one-way public API/idempotence, exact-type/subclass denial, preset signal before
outputs/creation, stop after entry and before READY/resume, actual running root+
descendant drain with unrelated child surviving, already-exited0 root denied,
stop arriving during bounded output finalization, no terminal receipt or automatic
release, shared cleanup bounds and observer threads joined. Explicit diagnostic
subclasses may gate lifecycle boundaries; no production arbitrary callbacks or
monkeypatch. Use retained duplicated root handle and private job accounting for
terminal proof, never PID lookup/kill or fabricated process receipts.

Focused tests use harmless Python children/synthetic reservations only. Existing
lease, output, reservation-state/store, owned-process, pure authority-watch and
denied-worker relevant regressions run on final source. No source/runtime/assets
operator acceptance, historical numeric/calendar adoption, real model, GPU,
held-out or training invocation. Two independent reviews before implementation
and after actual runtime evidence; trajectory records all changes and failures.

Executed evidence is recorded in 2026-10-11-alc-r0-owned-stop-evidence.md:
initial RED1, GREEN22, pre-repair regression264; reviewer-found missing-flag
defect RED-v2 two intended failures, repaired GREEN-v2 24 and final regression-v2
266 passing. All original failures retained; final source/test/runner pins and
all24 artifacts independently checked. No scientific authority is implied.
