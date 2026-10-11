"""Real thread and harmless Windows tree diagnostics, never model authority."""
import importlib
import os
import subprocess
import sys
import threading
import time

import pytest

from aluclu.alc_r0.authority_watch_policy import Observation, WatchPolicy
from aluclu.alc_r0.reserved_owned_process import OwnedStopSignal, OwnedStopRequested, ReservedOwnedLease
from test_alc_r0_owned_stop import RetainedHandles, closed, pending
from test_alc_r0_reserved_owned_process import ROOT, fixture


def api():
    module = importlib.import_module('aluclu.alc_r0.live_authority_watch')
    return module.LiveAuthorityWatch, module.LiveWatchError, module.ObservationRequest


def policy(deadline=None):
    deadline = deadline or time.monotonic_ns() + 5_000_000_000
    return WatchPolicy(ROOT, ROOT, deadline, deadline + 10_000_000_000)


def observation(**changes):
    values = dict(generation_root=ROOT, clock_domain_root=ROOT, revoked=False,
        observed_monotonic_ns=time.monotonic_ns(), utc_upper_ns=time.time_ns(),
        expires_utc_ns=time.time_ns() + 60_000_000_000)
    values.update(changes)
    return Observation(**values)


def finish(watch):
    watch.close(time.monotonic_ns() + 5_000_000_000)
    assert watch._thread is None or not watch._thread.is_alive()


def await_stop(signal):
    assert signal._event.wait(3), 'bounded diagnostic stop observation timed out'


def test_missing_observation_stops_and_joins():
    Watch, _, _ = api()
    signal = OwnedStopSignal()
    watch = Watch(policy(), signal)
    try:
        watch.start()
        request = watch.wait_request(1)
        assert request is not None and request.sequence == 1
        await_stop(signal)
        assert watch.reason == 'timeout'
        assert watch.wait_request(0) is None
    finally:
        finish(watch)
    assert watch.reason == 'timeout'


def test_valid_observation_opens_next_sequence_not_new_deadline():
    Watch, _, _ = api()
    signal = OwnedStopSignal()
    watch = Watch(policy(), signal)
    try:
        watch.start()
        first = watch.wait_request(1)
        watch.submit(first, observation())
        second = watch.wait_request(1)
        assert second.sequence == first.sequence + 1
        assert second.started_monotonic_ns >= first.started_monotonic_ns
        assert not signal._event.is_set()
        assert watch._state.policy == watch._policy
    finally:
        finish(watch)


def test_delayed_start_does_not_renew_initial_acquisition():
    Watch, _, _ = api()
    signal = OwnedStopSignal()
    watch = Watch(policy(), signal)
    initial = watch._state.pending_since_ns
    time.sleep(0.3)
    try:
        watch.start()
        await_stop(signal)
        assert watch.reason == 'timeout'
        assert watch._state.pending_since_ns == initial
    finally:
        finish(watch)


@pytest.mark.parametrize('change,reason', [
    ({'revoked': True}, 'revoked'),
    ({'generation_root': 'b' * 64}, 'generation'),
    ({'clock_domain_root': 'b' * 64}, 'clock'),
    ({'expires_utc_ns': 1}, 'expiry'),
    ({'observed_monotonic_ns': 1}, 'observation-time'),
    ({'revoked': 'not-bool'}, 'invalid-input'),
], ids=['revoked', 'generation', 'clock', 'expiry', 'capture-time', 'malformed'])
def test_invalid_observations_stop_permanently(change, reason):
    Watch, Error, _ = api()
    signal = OwnedStopSignal()
    watch = Watch(policy(), signal)
    try:
        watch.start()
        request = watch.wait_request(1)
        watch.submit(request, observation(**change))
        await_stop(signal)
        assert watch.reason == reason
        with pytest.raises(Error):
            watch.submit(request, observation())
        assert watch.reason == reason
    finally:
        finish(watch)
    assert watch.reason == reason


@pytest.mark.parametrize('kind', ['stale', 'duplicate', 'object', 'request-field', 'subclass'])
def test_bad_submission_is_bounded_absorbing_denial(kind):
    Watch, Error, Request = api()
    class Derived(Request):
        pass
    signal = OwnedStopSignal()
    watch = Watch(policy(), signal)
    try:
        watch.start()
        request = watch.wait_request(1)
        changed = request
        if kind == 'stale':
            changed = Request(request.sequence + 1, request.started_monotonic_ns)
        elif kind == 'object':
            changed = object()
        elif kind == 'request-field':
            changed = Request(True, request.started_monotonic_ns)
        elif kind == 'subclass':
            changed = Derived(request.sequence, request.started_monotonic_ns)
        elif kind == 'duplicate':
            watch.submit(request, observation())
        with pytest.raises(Error):
            watch.submit(changed, observation())
        await_stop(signal)
        assert watch.reason == 'invalid-input'
        assert watch._request is None and watch._response is None
    finally:
        finish(watch)


@pytest.mark.parametrize('timeout', [True, -1, 2, float('nan'), float('inf'), object()])
def test_wait_timeout_type_and_bound(timeout):
    Watch, _, _ = api()
    watch = Watch(policy(), OwnedStopSignal())
    try:
        with pytest.raises(ValueError):
            watch.wait_request(timeout)
    finally:
        finish(watch)


def test_close_before_start_single_use_and_first_deadline_retained():
    Watch, Error, _ = api()
    signal = OwnedStopSignal()
    watch = Watch(policy(), signal)
    first = time.monotonic_ns() + 5_000_000_000
    watch.close(first)
    watch.close(first + 5_000_000_000)
    assert watch._close_deadline == first and watch._thread is None
    assert watch.reason == 'stopped' and signal._event.is_set()
    with pytest.raises(Error):
        watch.start()


def test_preset_stop_and_invalid_signal_never_start_thread():
    Watch, Error, _ = api()
    signal = OwnedStopSignal()
    signal.request_stop()
    watch = Watch(policy(), signal)
    with pytest.raises(Error):
        watch.start()
    finish(watch)
    with pytest.raises(TypeError):
        Watch(policy(), threading.Event())
    signal = OwnedStopSignal()
    del signal._event._flag
    with pytest.raises(OwnedStopRequested):
        Watch(policy(), signal)


def test_wrong_thread_lifecycle_denied_owner_can_close():
    from concurrent.futures import ThreadPoolExecutor
    Watch, Error, _ = api()
    watch = Watch(policy(), OwnedStopSignal())
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            with pytest.raises(Error, match='owner thread'):
                executor.submit(watch.start).result(timeout=2)
        watch.start()
        with ThreadPoolExecutor(max_workers=1) as executor:
            with pytest.raises(Error, match='owner thread'):
                executor.submit(watch.close, time.monotonic_ns() + 1_000_000_000).result(timeout=2)
        with pytest.raises(Error):
            watch.start()
    finally:
        finish(watch)


def test_closure_failure_is_not_silent_or_renewed():
    Watch, Error, _ = api()
    signal = OwnedStopSignal()
    watch = Watch(policy(), signal)
    watch.start()
    signal._event = object()
    with pytest.raises(Error, match='signaling unconfirmed'):
        watch.close(time.monotonic_ns() + 5_000_000_000)
    assert not watch._thread.is_alive()
    signal._event = threading.Event()
    with pytest.raises(Error, match='signaling unconfirmed'):
        watch.close(time.monotonic_ns() + 5_000_000_000)


def test_late_consumption_preserves_timeout_priority():
    Watch, _, _ = api()
    paused, release = threading.Event(), threading.Event()
    class DelayedWatch(Watch):
        """Explicit diagnostic scheduling gate, no production callback."""
        def _step_locked(self):
            if self._response is not None and not paused.is_set():
                paused.set()
                assert self._condition.wait_for(release.is_set, 3)
            super()._step_locked()
    signal = OwnedStopSignal()
    watch = DelayedWatch(policy(), signal)
    try:
        watch.start()
        request = watch.wait_request(1)
        watch.submit(request, observation())
        assert paused.wait(2)
        time.sleep(0.3)
        release.set()
        with watch._condition:
            watch._condition.notify_all()
        await_stop(signal)
        assert watch.reason == 'timeout'
    finally:
        release.set()
        with watch._condition:
            watch._condition.notify_all()
        finish(watch)


def test_join_timeout_then_repeated_close_cannot_renew_deadline():
    Watch, _, _ = api()
    entered, release = threading.Event(), threading.Event()
    class GatedWatch(Watch):
        def _run(self):
            entered.set()
            assert release.wait(3), 'diagnostic run gate expired'
            super()._run()
    signal = OwnedStopSignal()
    watch = GatedWatch(policy(), signal)
    try:
        watch.start()
        assert entered.wait(2)
        first = time.monotonic_ns() + 20_000_000
        with pytest.raises(TimeoutError, match='original bound'):
            watch.close(first)
        assert signal._event.is_set() and watch._thread.is_alive()
        release.set()
        watch._thread.join(3)
        assert not watch._thread.is_alive()
        with pytest.raises(TimeoutError, match='original bound'):
            watch.close(time.monotonic_ns() + 5_000_000_000)
        assert watch._close_deadline == first
    finally:
        release.set()
        if watch._thread is not None:
            watch._thread.join(3)
            assert not watch._thread.is_alive()


@pytest.mark.skipif(os.name != 'nt', reason='Windows owned import trap')
def test_fresh_import_never_loads_scientific_runtime(tmp_path):
    from pathlib import Path
    from aluclu.alc_r0.checkpoint_owned_process import run_owned_process
    source = Path(__file__).resolve().parents[1] / 'src'
    code = ("import sys;import importlib.abc;"
        f"sys.path.insert(0,{str(source)!r})\n"
        "class Trap(importlib.abc.MetaPathFinder):\n"
        " def find_spec(self,fullname,path=None,target=None):\n"
        "  if fullname.split('.')[0] in ('torch','transformers'):raise RuntimeError('heavy import')\n"
        "sys.meta_path.insert(0,Trap())\n"
        "import aluclu.alc_r0.live_authority_watch\n"
        "assert not {'torch','transformers'} & sys.modules.keys()\n"
        "print('lightweight-import')")
    receipt = run_owned_process((sys.executable, '-I', '-c', code), cwd=tmp_path,
        environment=dict(os.environ), stdout_path=tmp_path / 'import.stdout',
        stderr_path=tmp_path / 'import.stderr', deadline_ns=time.monotonic_ns() + 5_000_000_000)
    assert receipt.exit_code == 0 and receipt.active_processes == 0 and not receipt.timed_out
    assert (tmp_path / 'import.stdout').read_text().strip() == 'lightweight-import'
    assert (tmp_path / 'import.stderr').read_bytes() == b''


@pytest.mark.skipif(os.name != 'nt', reason='Windows private-job integration')
@pytest.mark.parametrize('mode', ['timeout', 'revoked'])
def test_live_watch_stops_owned_tree_with_shared_tail(tmp_path, mode):
    Watch, _, _ = api()
    source = ("import subprocess,sys,time;"
        "subprocess.Popen([sys.executable,'-I','-c','import time;time.sleep(60)']);"
        "time.sleep(60)")
    arguments, store, _, _ = fixture(tmp_path, source=source)
    signal = OwnedStopSignal()
    unrelated = subprocess.Popen((sys.executable, '-I', '-c', 'import time;time.sleep(60)'))
    retained = watch = producer = None
    producer_errors = []
    try:
        with ReservedOwnedLease(**arguments, stop_signal=signal) as lease:
            retained = RetainedHandles(lease)
            ready = lease.publish_identity(ROOT, ROOT)
            lease.resume_verified(ready.sha256)
            end = time.monotonic() + 5
            while lease._job.accounting().active_processes < 2:
                assert time.monotonic() < end
                time.sleep(0.01)
            watch = Watch(policy(arguments['deadline_ns']), signal)
            watch.start()
            if mode == 'revoked':
                def provide_revocation():
                    try:
                        watch.submit(watch.wait_request(1), observation(revoked=True))
                    except BaseException:
                        producer_errors.append('producer failed')
                producer = threading.Thread(target=provide_revocation)
                producer.start()
            with pytest.raises(OwnedStopRequested):
                lease.wait_terminal()
            watch.close(lease._cleanup_deadline)
            if producer is not None:
                producer.join(max(0, lease._cleanup_deadline - time.monotonic_ns()) / 1e9)
                assert not producer.is_alive()
            assert watch.reason == ('timeout' if mode == 'timeout' else 'revoked')
            assert watch._close_deadline == lease._cleanup_deadline
            assert not watch._thread.is_alive()
            retained.drained(total=2)
            closed(lease)
        pending(store, 'RUNNING')
        assert unrelated.poll() is None and not producer_errors
    finally:
        if watch is not None:
            watch.close(lease._cleanup_deadline if lease._cleanup_deadline is not None
                else time.monotonic_ns() + 5_000_000_000)
        if producer is not None:
            producer.join(max(0, lease._cleanup_deadline - time.monotonic_ns()) / 1e9)
            assert not producer.is_alive()
        if retained is not None:
            retained.close()
        unrelated.terminate()
        unrelated.wait(timeout=10)
