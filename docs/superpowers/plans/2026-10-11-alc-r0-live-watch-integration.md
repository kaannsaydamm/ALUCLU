# Live denial watch connecting timing policy to the owned stop signal

Status: implemented and final relevant native regression independently closed
code APPROVE / architecture CLEAR; no trusted producer or scientific admission.
Parent4548421110857c05164662988087531acfed9e00. This composes the accepted
authority_watch_policy and OwnedStopSignal, not a new launch framework. No
scientific worker is enabled, no source/history/resource facts are adopted.

## Exact responsibility

Implement live_authority_watch.py, stdlib-only, with one owner-controlled
LiveAuthorityWatch(policy, stop_signal). Both arguments exact existing types;
validate policy via existing start_watch at actual time.monotonic_ns before any
thread starts; validate the exact signal's existing private read contract too.
The watch owns one non-daemon thread, bounded internal request/
response state and a Condition. No callbacks, caller-supplied clocks, arbitrary
module/function, file discovery, subprocess, assets or model imports.

The trusted coordinator's separately reviewed producer obtains observations.
This component only transports exact Observation values and applies existing
policy. An observation is a cooperating-host claim, not authenticated authority.
Synthetic tests cannot install an accepting production producer. Existing worker
entrypoint stays unconditionally denied. This is actual thread/signal/owned-child
integration, NOT a complete trusted observer or measured520ms enforcement.

## Request, response and one-way lifecycle

Immutable ObservationRequest(sequence, started_monotonic_ns), exact integer fields,
is created for each policy pending acquisition. At most ONE request and ONE
response exist. Sequence starts1 and increases at most once per newly started
policy acquisition, including an immediately due repoll. Captured monotonic start
comes from the policy's pending_since_ns. No arbitrary IDs or strings retained.

start() is single-use and owner-thread-only. It starts the fixed private loop.
wait_request(timeout_seconds) permits the cooperating producer thread to wait for
the current unfilled request; timeout is an exact finite nonnegative int/float
excludingbool, at most1second. It returns the immutable exact request or None,
never an authorization value. Predicate is notified on new request/response/stop.
Concurrent readers do not grant separate response capacity.

submit(request, observation) permits a cooperating producer thread to provide
one exact request and existing exact Observation. Exact retained request equality
and one outstanding response required; stale, duplicate or malformed inputs
signal permanent denial and raise LiveWatchError. No dictionary or wire parser.
Exact Observation field validation is existing policy's responsibility in the
loop; structural/value errors stop, never keep running. Submission after terminal
raises without restarting/replacing terminal reason. Producer origin verification
and bounded actual acquisition remain external duties; queue freshness is not
authentication. The watch does not execute or block on the producer.

The loop alone advances WatchState with actual time.monotonic_ns. First acquisition
is pending immediately from original constructor start; delayed start consumes
that allowance, not a fresh250ms. Consume at most one pending observation, call
advance_watch, retain its state/action; on observe expose request, on wait clear
completed request and wait until next_poll or at most existing WAIT_NS20ms. On
stop call exact OwnedStopSignal.request_stop and notify all waiters. Scheduling
uses existing capture-time policy, not response consumption as a fresh cadence.
Never silently drop/replace a response or return a successful authority receipt.

Any loop exception permanently denies with fixed bounded diagnostic reason,
including thread-start failure, malformed observation and clock/policy error.
No exception repr or unbounded producer payload retained. Diagnostic reason is
one of existing policy reasons plus invalid-input, stopped, internal-error.
No reason can override a prior terminal reason. Shutdown signals stop first,
notifies loop, and joins only until an exact caller-provided absolute monotonic
cleanup deadline. close(cleanup_deadline_ns) is owner-thread-only; original shared
lease tail must be supplied by actual coordinator, never a fresh10second budget.
First supplied cleanup deadline is retained; repeated close cannot extend it.
Signal-setting failure also raises at closure, never claims successful stop.
Failure to observe joined thread raises; no successful closure claim. close is
safe before start and idempotent after terminal; start after close is denied.
No daemon thread or infinite producer wait may be left behind.

All public state/lifecycle changes are under Condition ownership. Never hold that
condition during thread.join. Fixed signal calls have no lease/file/authority
callbacks or cross-thread lease operations. Last terminal reason is diagnostic
only; real coordinator still revalidates final authority independently.

## Native acceptance

TDD intended missing-module RED then real-thread tests: initial timeout; delayed
start does not renew acquisition; valid observation schedules another request;
generation/clock/revocation/expiry invalidation; malformed/stale/duplicate response
denies and bounded one-slot behavior; terminal remains absorbing; bounded producer
wait; wrong-thread start/close; close-before-start and repeated close; exact types;
no heavy imports. No brittle worst-case scheduler assertions; wait with generous
test envelopes then inspect joined state and permanent stop.

Integrate with actual ReservedOwnedLease harmless running root+descendant: monitor
acquisition timeout and revoked response must stop the owned tree; retained root/
job handle accounting proves terminal/zero members, pending journal remains,
unrelated process survives, monitor and producer threads join under supplied
existing cleanup deadline. Relevant watch-policy/stop/lease/output/reservation/
owned-process/denied-worker regressions run on final pins. No model/GPU/learning
PASS, no history/calendar adoption, no threshold/seed/grid/phase changes.

Execution: 2026-10-11-alc-r0-live-watch-evidence.md retains intended missing-module
RED, original27/293 successes and strengthened29/295 final successes. Both closing
lanes independently verified all20 artifacts and final pins. Thread-start failure
is source-inspected but unexecuted; one-slot capacity is not arbitrary-field byte
bounding. Real coordinator producer/provenance/admission and final authority
verification remain required; this checkpoint grants no scientific authority.
