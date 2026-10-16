"""Pure watch timing decisions, not authenticated authority or live enforcement."""
import re
from dataclasses import dataclass, replace

POLL_NS = OBSERVATION_NS = 250_000_000
WAIT_NS = 20_000_000
_MAX = (1 << 63) - 1
_ROOT = re.compile(r'[0-9a-f]{64}\Z')
_REASONS = ('deadline', 'timeout', 'generation', 'clock', 'revoked',
            'observation-time', 'expiry')


@dataclass(frozen=True, slots=True)
class WatchPolicy:
    generation_root: str
    clock_domain_root: str
    useful_deadline_ns: int
    envelope_deadline_ns: int


@dataclass(frozen=True, slots=True)
class WatchState:
    policy: WatchPolicy
    last_now_ns: int
    pending_since_ns: int | None
    next_poll_ns: int
    stopped: bool
    stop_reason: str | None


@dataclass(frozen=True, slots=True)
class Observation:
    generation_root: str
    clock_domain_root: str
    revoked: bool
    observed_monotonic_ns: int
    utc_upper_ns: int
    expires_utc_ns: int


@dataclass(frozen=True, slots=True)
class WatchDecision:
    state: WatchState
    action: str
    reason: str | None


def _require(value):
    if not value:
        raise ValueError('invalid pure watch input; operational caller must deny')


def _integer(value):
    _require(type(value) is int and 0 < value <= _MAX)


def _roots(value):
    for root in (value.generation_root, value.clock_domain_root):
        _require(type(root) is str and _ROOT.fullmatch(root) is not None)


def _policy(policy):
    _require(type(policy) is WatchPolicy)
    _roots(policy)
    _integer(policy.useful_deadline_ns)
    _integer(policy.envelope_deadline_ns)
    _require(policy.envelope_deadline_ns == policy.useful_deadline_ns + 10_000_000_000)


def start_watch(policy, now_ns):
    _policy(policy)
    _integer(now_ns)
    _require(now_ns < policy.useful_deadline_ns)
    return WatchState(policy, now_ns, now_ns, now_ns, False, None)


def _validate(policy, state, now, observation):
    _policy(policy)
    _require(type(state) is WatchState)
    _policy(state.policy)
    _require(state.policy == policy and type(state.stopped) is bool)
    for value in (now, state.last_now_ns, state.next_poll_ns):
        _integer(value)
    _require(now >= state.last_now_ns)
    if state.pending_since_ns is not None:
        _integer(state.pending_since_ns)
        _require(state.pending_since_ns <= state.last_now_ns
                 and state.next_poll_ns == state.pending_since_ns)
    elif not state.stopped:
        _require(state.next_poll_ns > state.last_now_ns)
    if state.stopped:
        _require(type(state.stop_reason) is str and state.stop_reason in _REASONS)
    else:
        _require(state.stop_reason is None
                 and state.last_now_ns < policy.useful_deadline_ns
                 and state.next_poll_ns <= policy.useful_deadline_ns)
    if observation is not None:
        _require(type(observation) is Observation and type(observation.revoked) is bool)
        _roots(observation)
        for value in (observation.observed_monotonic_ns, observation.utc_upper_ns,
                      observation.expires_utc_ns):
            _integer(value)


def _stop(state, now, reason):
    return WatchDecision(replace(state, last_now_ns=now, stopped=True,
                                 stop_reason=reason), 'stop', reason)


def advance_watch(policy, state, now_ns, observation=None):
    _validate(policy, state, now_ns, observation)
    if state.stopped:
        return _stop(state, now_ns, state.stop_reason)
    if now_ns >= policy.useful_deadline_ns:
        return _stop(state, now_ns, 'deadline')
    pending = state.pending_since_ns
    if pending is None:
        _require(observation is None)
        if now_ns < state.next_poll_ns:
            return WatchDecision(replace(state, last_now_ns=now_ns), 'wait', None)
        return WatchDecision(WatchState(policy, now_ns, now_ns, now_ns, False, None),
                             'observe', None)
    if now_ns - pending >= OBSERVATION_NS:
        return _stop(state, now_ns, 'timeout')
    if observation is None:
        return WatchDecision(replace(state, last_now_ns=now_ns), 'observe', None)
    for reason, invalid in (
        ('generation', observation.generation_root != policy.generation_root),
        ('clock', observation.clock_domain_root != policy.clock_domain_root),
        ('revoked', observation.revoked),
        ('observation-time', not pending <= observation.observed_monotonic_ns <= now_ns),
    ):
        if invalid:
            return _stop(state, now_ns, reason)
    required = observation.utc_upper_ns + (policy.envelope_deadline_ns
                                          - observation.observed_monotonic_ns)
    if required > _MAX or observation.expires_utc_ns <= required:
        return _stop(state, now_ns, 'expiry')
    due = min(observation.observed_monotonic_ns + POLL_NS, policy.useful_deadline_ns)
    if due <= now_ns:
        return WatchDecision(WatchState(policy, now_ns, now_ns, now_ns, False, None),
                             'observe', None)
    return WatchDecision(WatchState(policy, now_ns, None, due, False, None), 'wait', None)
