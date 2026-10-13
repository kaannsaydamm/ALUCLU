"""Status consumer denial tests, no installed authority or scientific execution."""
import importlib
import os
import subprocess
import sys
import threading
import time
from dataclasses import replace

import pytest

from aluclu.alc_r0.canonical import canonical_json_bytes
from aluclu.alc_r0.operator_status import decode_operator_status
from aluclu.alc_r0.authority_watch_policy import WatchPolicy
from aluclu.alc_r0.live_authority_watch import LiveAuthorityWatch
from aluclu.alc_r0.reserved_owned_process import OwnedStopSignal

ROOT = 'a' * 64
EXPIRY = 2**63 - 1


def api():
    module = importlib.import_module('aluclu.alc_r0.status_watch_consumer')
    return module.StatusWatchConsumer, module.StatusConsumerError


def status(**changes):
    value = dict(schema='alc-r0-operator-status-v1', installation_root=ROOT,
                 generation_root=ROOT, sequence='1', revoked=False,
                 expires_utc_ns=str(EXPIRY))
    value.update(changes)
    return decode_operator_status(canonical_json_bytes(value))


def fixture():
    Consumer, _ = api()
    signal = OwnedStopSignal()
    return Consumer(ROOT, ROOT, ROOT, signal), signal


def consume(consumer, record=None, **changes):
    values = dict(observed_monotonic_ns=time.monotonic_ns(), utc_upper_ns=time.time_ns())
    values.update(changes)
    return consumer.consume(status() if record is None else record, **values)


def test_first_equal_and_increasing_status():
    consumer, signal = fixture()
    for record in (status(), status(), status(sequence='2', expires_utc_ns=str(EXPIRY-1))):
        observation = consume(consumer, record)
        assert observation.generation_root == ROOT and observation.clock_domain_root == ROOT
        assert observation.expires_utc_ns == record.expires_utc_ns
    assert not signal._event.is_set()


@pytest.mark.parametrize('changes', [
    {'sequence': '1'}, {'sequence': '2', 'expires_utc_ns': str(EXPIRY-2)},
    {'sequence': '3', 'expires_utc_ns': str(EXPIRY)},
    {'sequence': '3', 'installation_root': 'b'*64},
    {'sequence': '3', 'generation_root': 'b'*64},
    {'sequence': '3', 'revoked': True},
])
def test_state_violation_is_sticky(changes):
    consumer, signal = fixture()
    consume(consumer, status(sequence='2', expires_utc_ns=str(EXPIRY-1)))
    with pytest.raises(ValueError):
        consume(consumer, status(**changes))
    assert signal._event.is_set()
    with pytest.raises(ValueError):
        consume(consumer, status(sequence='4', expires_utc_ns=str(EXPIRY-3)))


@pytest.mark.parametrize('changes', [dict(root='b'*64), dict(sequence=99),
    dict(revoked=True), dict(data=b'{}'), dict(expires_utc_ns=1)])
def test_forged_dataclass_fields_are_not_observations(changes):
    consumer, signal = fixture()
    with pytest.raises(ValueError):
        consume(consumer, replace(status(), **changes))
    assert signal._event.is_set()


@pytest.mark.parametrize('value', [True, 0, -1, 2**63, 1.0, None])
@pytest.mark.parametrize('field', ['observed_monotonic_ns', 'utc_upper_ns'])
def test_invalid_clock_transport_denies(field, value):
    consumer, signal = fixture()
    with pytest.raises(ValueError):
        consume(consumer, **{field: value})
    assert signal._event.is_set()


def test_wrong_thread_denies_owner_too():
    consumer, signal = fixture()
    errors = []
    def other():
        try: consume(consumer)
        except ValueError as error: errors.append(error)
    thread = threading.Thread(target=other)
    thread.start(); thread.join(2)
    assert not thread.is_alive() and len(errors) == 1 and signal._event.is_set()
    with pytest.raises(ValueError): consume(consumer)


@pytest.mark.parametrize('kind', ['revoked', 'generation', 'missing', 'corrupt'])
def test_real_slot_watch_updates_stop(kind, tmp_path):
    consumer, signal = fixture()
    deadline = time.monotonic_ns() + 5_000_000_000
    watch = LiveAuthorityWatch(WatchPolicy(ROOT, ROOT, deadline, deadline+10_000_000_000), signal)
    path = tmp_path/'status.json'
    path.write_bytes(status().data)
    try:
        watch.start()
        assert consumer.serve_once(watch, path, time.time_ns(),
                                   utc_anchor_monotonic_ns=time.monotonic_ns())
        if kind == 'missing': path.unlink()
        elif kind == 'corrupt': path.write_bytes(b'{}')
        else: path.write_bytes(status(sequence='2', **(
            {'revoked': True} if kind == 'revoked' else {'generation_root': 'b'*64})).data)
        # Wait is bounded20ms per call; the watch preserves its original poll.
        observed_error = False
        stop_by = time.monotonic() + 2
        while not signal._event.is_set() and time.monotonic() < stop_by:
            try: consumer.serve_once(watch, path, time.time_ns(),
                                     utc_anchor_monotonic_ns=time.monotonic_ns())
            except (ValueError, OSError): observed_error = True
        assert signal._event.is_set() and observed_error
    finally:
        watch.close(deadline+10_000_000_000)
    assert not watch._thread.is_alive()


@pytest.mark.parametrize('kind', ['signal', 'generation', 'clock', 'object'])
def test_wrong_watch_binding_denies(kind, tmp_path):
    consumer, signal = fixture()
    deadline = time.monotonic_ns()+5_000_000_000
    watch = LiveAuthorityWatch(WatchPolicy('b'*64 if kind=='generation' else ROOT,
        'b'*64 if kind=='clock' else ROOT, deadline, deadline+10_000_000_000),
        OwnedStopSignal() if kind=='signal' else signal)
    try:
        with pytest.raises(ValueError):
            consumer.serve_once(object() if kind=='object' else watch,
                                tmp_path/'missing.json', time.time_ns(),
                                utc_anchor_monotonic_ns=time.monotonic_ns())
        assert signal._event.is_set()
    finally: watch.close(deadline+10_000_000_000)


@pytest.mark.parametrize('kind', ['expired', 'monotonic-regression', 'revoked-first'])
def test_known_invalid_observation_stops(kind):
    consumer, signal = fixture()
    values = {}
    record = status()
    if kind == 'expired': values['utc_upper_ns'] = EXPIRY
    elif kind == 'revoked-first': record = status(revoked=True)
    else:
        consume(consumer, observed_monotonic_ns=100)
        values['observed_monotonic_ns'] = 99
    with pytest.raises(ValueError): consume(consumer, record, **values)
    assert signal._event.is_set()


@pytest.mark.parametrize('kind', ['future', 'overflow', 'elapsed-expiry', 'rebind'])
def test_anchor_and_original_watch_are_enforced(kind, tmp_path):
    consumer, signal = fixture()
    now = time.monotonic_ns()
    deadline = now+5_000_000_000
    watch = LiveAuthorityWatch(WatchPolicy(ROOT, ROOT, deadline, deadline+10_000_000_000), signal)
    second = None
    path = tmp_path/'status.json'
    path.write_bytes(status().data)
    utc, anchor = time.time_ns(), now
    if kind == 'future': anchor = now+60_000_000_000
    elif kind == 'overflow': utc, anchor = EXPIRY, now-1_000_000_000
    elif kind == 'elapsed-expiry':
        anchor = now-2_000_000_000
        path.write_bytes(status(expires_utc_ns=str(utc+16_000_000_000)).data)
    try:
        watch.start()
        if kind == 'rebind':
            assert consumer.serve_once(watch, path, utc, utc_anchor_monotonic_ns=anchor)
            second = LiveAuthorityWatch(watch._policy, signal)
        with pytest.raises(ValueError):
            consumer.serve_once(second if second else watch, path, utc,
                                utc_anchor_monotonic_ns=anchor)
        assert signal._event.is_set()
    finally:
        watch.close(deadline+10_000_000_000)
        if second: second.close(deadline+10_000_000_000)


@pytest.mark.skipif(os.name != 'nt', reason='Windows owned job integration')
@pytest.mark.parametrize('kind', ['revoked', 'generation'])
def test_slot_consumer_stops_actual_owned_tree(tmp_path, kind):
    from test_alc_r0_owned_stop import RetainedHandles, closed, pending
    from test_alc_r0_reserved_owned_process import fixture as lease_fixture
    from aluclu.alc_r0.reserved_owned_process import ReservedOwnedLease, OwnedStopRequested
    source = ("import subprocess,sys,time;"
        "subprocess.Popen([sys.executable,'-I','-c','import time;time.sleep(60)']);time.sleep(60)")
    arguments, store, _, _ = lease_fixture(tmp_path, source=source)
    signal = OwnedStopSignal()
    path = tmp_path/'status.json'
    path.write_bytes(status().data)
    watch = retained = producer = None
    first = threading.Event()
    producer_errors = []
    unrelated = subprocess.Popen((sys.executable,'-I','-c','import time;time.sleep(60)'))
    try:
        with ReservedOwnedLease(**arguments, stop_signal=signal) as lease:
            retained = RetainedHandles(lease)
            ready = lease.publish_identity(ROOT, ROOT)
            deadline = arguments['deadline_ns']
            watch = LiveAuthorityWatch(WatchPolicy(ROOT,ROOT,deadline,deadline+10_000_000_000),signal)
            watch.start()
            def provide():
                Consumer, _ = api()
                consumer = Consumer(ROOT,ROOT,ROOT,signal)
                try:
                    while not signal._event.is_set():
                        if consumer.serve_once(watch,path,time.time_ns(),
                                utc_anchor_monotonic_ns=time.monotonic_ns()):
                            first.set()
                except BaseException as error:
                    producer_errors.append(error)
            producer = threading.Thread(target=provide)
            producer.start()
            assert first.wait(2)
            lease.resume_verified(ready.sha256)
            until = time.monotonic()+3
            while lease._job.accounting().active_processes < 2:
                assert time.monotonic() < until
                time.sleep(0.01)
            path.write_bytes(status(sequence='2', **({'revoked':True} if kind=='revoked'
                              else {'generation_root':'b'*64})).data)
            assert signal._event.wait(2)
            with pytest.raises(OwnedStopRequested): lease.wait_terminal()
            watch.close(lease._cleanup_deadline)
            producer.join(max(0,lease._cleanup_deadline-time.monotonic_ns())/1e9)
            assert not producer.is_alive() and len(producer_errors)==1
            assert isinstance(producer_errors[0],ValueError)
            retained.drained(total=2)
            closed(lease)
        pending(store,'RUNNING')
        assert unrelated.poll() is None
    finally:
        if watch: watch.close(lease._cleanup_deadline)
        if producer:
            producer.join(max(0,lease._cleanup_deadline-time.monotonic_ns())/1e9)
            assert not producer.is_alive()
        if retained: retained.close()
        unrelated.terminate(); unrelated.wait(timeout=10)
