# Fixed D active-authority watch timing policy

Status: pure policy implementation accepted with independent code APPROVE and
architecture CLEAR after native RED/GREEN/relevant-regression evidence.
Parent b9ddb511b2cdcc31ed76b68fe4fae70a4794f5b1. This implements one necessary
part of the fixed-worker monitor, not the trusted observer, live monitor or
lease integration. Production worker remains unconditionally denied.

## Exact API and ownership

New authority_watch_policy.py imports only dataclasses and re. No clocks, OS,
thread, file, process, model, network or callback access. Constants POLL_NS and
OBSERVATION_NS are 250000000; WAIT_NS is 20000000. These preserve the existing
worker-design proposal, not a measured host latency guarantee.

WatchPolicy(generation_root, clock_domain_root, useful_deadline_ns,
envelope_deadline_ns) is an immutable exact-type checked input. Roots are64lower
hex; times are exact non-bool integers in [1,2**63-1], envelope is exactly useful
deadline +10000000000 with overflow rejected. This represents previously verified
inputs but does NOT verify or grant authority. It has no permit/approved field.

WatchState(policy, last_now_ns, pending_since_ns, next_poll_ns, stopped,
stop_reason) is frozen
output state bound by exact immutable policy equality, with no accepting parser.
start_watch(policy, now_ns) returns a
state pending observation immediately (pending_since=now, next_poll=now). Starting
at/after useful deadline rejects. No child may resume because a watch was started.

Observation(generation_root, clock_domain_root, revoked, observed_monotonic_ns,
utc_upper_ns, expires_utc_ns) is a plain typed observation, NOT authenticated
evidence. revoked must be exact bool; numeric values are positive signed64.
Only the future concrete trusted observer may supply it operationally. Test
fixtures cannot be selected by a CLI or production entrypoint.

advance_watch(policy, state, now_ns, observation=None) returns WatchDecision
(state, action, reason), with actions observe/wait/stop. It never sleeps, invokes
the observer, starts/stops a process or releases accounting. Caller must invoke
within WAIT_NS and owns bounded acquisition/termination, still unimplemented.

## Transition rules and boundaries

All exact types/roots/time ranges and state invariants validate; bool times,
malformed state, a state for which pending/next/last ordering is impossible,
and backwards time raise ValueError. Invalid input must be treated by the future
coordinator as terminal denial, not caught and retried. Pending state requires
pending_since <= last_now and next_poll == pending_since. Nonpending state has
next_poll >= last_now unless a later tick makes the next observation due.
Stopped is absorbing: a later valid observation cannot restore running. Stopped
states allow a past next_poll; their original stop reason is retained. Live
nonpending states require next_poll > last_now, as a due poll is made pending
immediately. Policy mismatch rejects, including changes of deadlines or roots.

stopped is exact bool. stop_reason is None for live states and a closed reason
for stopped states: deadline, timeout, generation, clock, revoked,
observation-time, expiry. After validation and nondecreasing time, stopped states
return their stored stop reason BEFORE any new deadline/observation transition.
Test revocation then a tick beyond useful expiry still retaining revoked.
For live states useful expiry is checked first (now >= useful -> stop deadline).
Observation arrival requires an outstanding pending observation; unsolicited
arrival rejects. A pending observation times out at elapsed >= OBSERVATION_NS,
even if a valid observation arrives at that boundary. This prevents accepting
late data. Missing result while pending and younger -> observe. Nonpending
before next_poll -> wait; at/after next_poll -> begin pending at now, observe.

A timely supplied observation must match generation and clock roots, revoked
false, and pending_since <= observed_monotonic_ns <= now. Otherwise stop with
closed reason generation/clock/revoked/observation-time. To cover ENTIRE remaining
envelope, require expires_utc_ns > utc_upper_ns +
(envelope_deadline_ns - observed_monotonic_ns). utc_upper_ns is already a trusted
conservative upper UTC bound at observation time; uncertainty establishment is
external. Signed64 addition overflow denies with reason expiry. Equality denies.
Do NOT shorten the envelope, renew the original deadline or reset it on a poll.

Success schedules next_poll = observed_monotonic_ns + POLL_NS, capped at useful
deadline. If next_poll <= now, immediately begin a new pending observation at
now, action observe, without another tick; otherwise clear pending, action wait.
Do not schedule from consumption time: a249ms-old result followed by a250ms wait
would silently increase the proposed520ms detection allowance to about770ms.
Addition is computed in Python integers then capped by the signed64 deadline;
no wrapped integer arithmetic. A late tick begins observation at that tick but
does not erase the fact that scheduler latency was not enforced. The pure
function cannot prove the proposed520ms real observation-to-termination bound.
Missing/pending timing, changed roots, revoked and insufficient expiry all stop
permanently with no grace, fallback, reservation release or refund.

## Required RED/GREEN/regression evidence

Tests cover immediate observation, normal polling, exact poll/timeout/useful
boundaries, response at timeout, revoked/root/domain changes, stale/future
observation timestamps, signed64 overflow, exact expiry boundary, immutable
inputs/state, invalid bool/type/range/state, backwards time, unsolicited data,
absorbing stop, policy mismatch and repeated polls preserving original deadlines.
Include early capture at t0, consumption at t0+249ms, next due t0+250ms, then
revoked response at t0+499ms. No extra250ms after consuming the old observation.
Use deterministic numeric fixtures without monkeypatch/clocks or real children.
Import must remain scientific-runtime free. Relevant regressions include existing
fixed D worker/wire/projection tests; GPU recording tests are still not GPU proof.

Independent review precedes implementation and follows actual test evidence.
Concrete observer/provenance, worker handoff, lease precreation/preresume seams,
active scheduling/owned termination, numeric history/calendar coverage, current
resource bounds and GPU2 stability remain separate unresolved gates. No actual
model, qualification or training execution is enabled by this policy.
