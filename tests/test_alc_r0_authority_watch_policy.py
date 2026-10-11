"""Pure synthetic timing tests, never authenticated authority or live monitoring."""

import importlib
from dataclasses import FrozenInstanceError, replace

import pytest


def api():
    return importlib.import_module('aluclu.alc_r0.authority_watch_policy')


def setup():
    m = api()
    p = m.WatchPolicy('a' * 64, 'b' * 64, 2_000_000_000, 12_000_000_000)
    s = m.start_watch(p, 1)
    o = m.Observation(p.generation_root, p.clock_domain_root, False, 1,
                      100_000_000_000, 200_000_000_000)
    return m, p, s, o


def test_initial_and_poll_boundaries():
    m, p, s, o = setup()
    assert m.advance_watch(p, s, 1).action == 'observe'
    d = m.advance_watch(p, s, 2, o)
    assert d.action == 'wait' and d.state.next_poll_ns == 250_000_001
    assert m.advance_watch(p, d.state, 250_000_000).action == 'wait'
    due = m.advance_watch(p, d.state, 250_000_001)
    assert due.action == 'observe' and due.state.pending_since_ns == 250_000_001


def test_early_capture_delayed_delivery_does_not_add_poll_delay():
    m, p, s, o = setup()
    d = m.advance_watch(p, s, 249_000_001, o)
    assert d.state.next_poll_ns == 250_000_001
    due = m.advance_watch(p, d.state, 250_000_001)
    revoked = replace(o, revoked=True, observed_monotonic_ns=250_000_001)
    result = m.advance_watch(p, due.state, 499_000_001, revoked)
    assert result.action == 'stop' and result.reason == 'revoked'
    assert 499_000_000 + m.WAIT_NS < 520_000_000


@pytest.mark.parametrize('arrival', [False, True])
def test_timeout_boundary_precedes_response(arrival):
    m, p, s, o = setup()
    d = m.advance_watch(p, s, 250_000_001, o if arrival else None)
    assert (d.action, d.reason) == ('stop', 'timeout')


@pytest.mark.parametrize('field,value,reason', [
    ('generation_root', 'c'*64, 'generation'),
    ('clock_domain_root', 'c'*64, 'clock'),
    ('revoked', True, 'revoked'),
    ('observed_monotonic_ns', 3, 'observation-time'),
    ('expires_utc_ns', 111_999_999_999, 'expiry'),
    ('utc_upper_ns', (1<<63)-1, 'expiry'),
])
def test_terminal_observations(field, value, reason):
    m, p, s, o = setup()
    d = m.advance_watch(p, s, 2, replace(o, **{field: value}))
    assert (d.action, d.reason) == ('stop', reason)


def test_stale_observation():
    m, p, s, o = setup()
    s = m.start_watch(p, 10)
    assert m.advance_watch(p, s, 11, o).reason == 'observation-time'


def test_stop_absorbs_deadline_and_later_good_observation():
    m, p, s, o = setup()
    d = m.advance_watch(p, s, 2, replace(o, revoked=True))
    later = m.advance_watch(p, d.state, p.useful_deadline_ns + 1, o)
    assert (later.action, later.reason) == ('stop', 'revoked')


def test_useful_deadline_precedes_pending_timeout():
    m, p, s, o = setup()
    d = m.advance_watch(p, s, p.useful_deadline_ns, o)
    assert d.reason == 'deadline'
    with pytest.raises(ValueError):
        m.start_watch(p, p.useful_deadline_ns)


@pytest.mark.parametrize('field,value', [
    ('generation_root', 'c'*64), ('clock_domain_root', 'c'*64),
    ('useful_deadline_ns', 2_000_000_001),
])
def test_policy_reuse_rejected(field, value):
    m, p, s, o = setup()
    changes = {field: value}
    if field == 'useful_deadline_ns':
        changes['envelope_deadline_ns'] = value + 10_000_000_000
    with pytest.raises(ValueError):
        m.advance_watch(replace(p, **changes), s, 2)


@pytest.mark.parametrize('value', [True, 0, -1, 1.0, '1', 1<<63])
def test_invalid_now(value):
    m, p, s, o = setup()
    with pytest.raises(ValueError):
        m.advance_watch(p, s, value)


def test_invalid_state_unsolicited_backwards_and_immutability():
    m, p, s, o = setup()
    with pytest.raises(FrozenInstanceError):
        s.last_now_ns = 2
    with pytest.raises(ValueError):
        m.advance_watch(p, replace(s, next_poll_ns=2), 2)
    d = m.advance_watch(p, s, 2, o)
    with pytest.raises(ValueError):
        m.advance_watch(p, d.state, 3, o)
    with pytest.raises(ValueError):
        m.advance_watch(p, d.state, 1)


def test_repeated_polls_do_not_renew_deadlines():
    m, p, s, o = setup()
    for now in (1, 250_000_001, 500_000_001, 750_000_001):
        s = m.advance_watch(p, s, now, replace(o, observed_monotonic_ns=now)).state
        assert s.policy == p
        if now < 750_000_001:
            s = m.advance_watch(p, s, now + m.POLL_NS).state
    assert p.useful_deadline_ns == 2_000_000_000


def test_invalid_policy_and_observation_values():
    m, p, s, o = setup()
    for bad in (replace(p, generation_root='A'*64),
                replace(p, envelope_deadline_ns=p.envelope_deadline_ns+1),
                replace(p, useful_deadline_ns=True),
                replace(p, useful_deadline_ns=(1<<63)-1)):
        with pytest.raises(ValueError):
            m.start_watch(bad, 1)
    for bad in (replace(o, revoked=1), replace(o, utc_upper_ns=True),
                replace(o, clock_domain_root='bad')):
        with pytest.raises(ValueError):
            m.advance_watch(p, s, 2, bad)
