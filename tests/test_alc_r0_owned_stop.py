"""Harmless native stop diagnostics, no model/GPU or scientific authority."""
import importlib
import os
import ctypes
import subprocess
import sys
import threading
import time

import pytest

from test_alc_r0_reserved_owned_process import ROOT, fixture

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Windows owned lease')


def api():
    module = importlib.import_module('aluclu.alc_r0.reserved_owned_process')
    return module.OwnedStopSignal, module.OwnedStopRequested, module.ReservedOwnedLease


def test_preset_stop_denies_before_outputs_and_creation(tmp_path):
    Signal, Stopped, Lease = api()
    signal = Signal()
    signal.request_stop()
    signal.request_stop()
    arguments, store, reserved, sentinel = fixture(tmp_path)
    lease = Lease(**arguments, stop_signal=signal)
    with pytest.raises(Stopped):
        with lease:
            pytest.fail('preset stop entered')
    assert not sentinel.exists()
    assert not arguments['stdout_path'].exists()
    assert not arguments['stderr_path'].exists()
    assert lease._job is None and lease._lock is None
    assert store.read(reserved.sha256).snapshot.reservations[0].state == 'RESERVED'


def test_signal_public_api_one_way_idempotent_and_latched(tmp_path):
    Signal, Stopped, Lease = api()
    signal = Signal()
    assert not hasattr(signal, 'clear') and not hasattr(signal, 'reset')
    assert not hasattr(signal, '__dict__')
    arguments, _, _, _ = fixture(tmp_path)
    lease = Lease(**arguments, stop_signal=signal)
    lease._check_stop()
    signal.request_stop()
    signal.request_stop()
    with pytest.raises(Stopped):
        lease._check_stop()
    # Diagnostic private corruption cannot undo an ALREADY observed stop.
    signal._event = threading.Event()
    with pytest.raises(Stopped):
        lease._check_stop()


@pytest.mark.parametrize('kind', ['event', 'bool', 'object', 'subclass'])
def test_nonexact_signal_rejected_without_resources(tmp_path, kind):
    Signal, _, Lease = api()
    class Derived(Signal):
        pass
    values = dict(event=threading.Event(), bool=False, object=object(), subclass=Derived())
    arguments, store, reserved, _ = fixture(tmp_path)
    with pytest.raises(TypeError, match='exact OwnedStopSignal'):
        Lease(**arguments, stop_signal=values[kind])
    assert not arguments['stdout_path'].exists()
    assert store.read(reserved.sha256).snapshot.reservations[0].state == 'RESERVED'


@pytest.mark.parametrize('kind', ['object', 'event-subclass', 'flag'])
def test_malformed_signal_denied_before_acquisition(tmp_path, kind):
    Signal, Stopped, Lease = api()
    class DerivedEvent(threading.Event):
        pass
    signal = Signal()
    if kind == 'flag':
        signal._event._flag = 1
    else:
        signal._event = object() if kind == 'object' else DerivedEvent()
    arguments, _, _, _ = fixture(tmp_path)
    with pytest.raises(Stopped, match='signal invalid'):
        Lease(**arguments, stop_signal=signal)
    assert not arguments['stdout_path'].exists()


def test_exact_event_instance_methods_cannot_override_observation(tmp_path):
    Signal, Stopped, Lease = api()
    signal = Signal()
    signal._event.is_set = lambda: pytest.fail('instance callback invoked')
    signal._event.set = lambda: pytest.fail('instance callback invoked')
    signal.request_stop()
    arguments, _, _, _ = fixture(tmp_path)
    with pytest.raises(Stopped):
        with Lease(**arguments, stop_signal=signal):
            pytest.fail('overridden event admitted')


class RetainedHandles:
    """Duplicate exact retained handles, never discover/open a PID."""
    def __init__(self, lease):
        import _winapi
        self.handles = []
        self.kernel = lease._job.kernel
        process = _winapi.GetCurrentProcess()
        try:
            for handle in (lease._information.process, lease._job.handle):
                self.handles.append(_winapi.DuplicateHandle(process, handle, process,
                    0, False, _winapi.DUPLICATE_SAME_ACCESS))
        except BaseException:
            self.close()
            raise

    def drained(self, *, exit_code=124, total=1):
        import _winapi
        from aluclu.alc_r0.checkpoint_owned_process import _Accounting, _checked
        assert _winapi.WaitForSingleObject(self.handles[0], 5000) == 0
        assert _winapi.GetExitCodeProcess(self.handles[0]) == exit_code
        value = _Accounting()
        _checked(self.kernel.QueryInformationJobObject(self.handles[1], 1,
            ctypes.byref(value), ctypes.sizeof(value), None))
        assert value.active_processes == 0 and value.total_processes >= total

    def close(self):
        import _winapi
        for handle in self.handles:
            _winapi.CloseHandle(handle)
        self.handles.clear()


def pending(store, state):
    from aluclu.alc_r0.canonical import sha256_bytes
    from concurrent.futures import ThreadPoolExecutor
    root = sha256_bytes((store.root / 'owner.json').read_bytes())
    # A different owner thread also proves that failure released the store lock.
    with ThreadPoolExecutor(max_workers=1) as executor:
        receipt = executor.submit(store.read, root).result(timeout=3)
    assert receipt.snapshot.reservations[0].state == state
    assert receipt.snapshot.pending_physical_bytes == 4096
    return receipt


def closed(lease):
    assert lease._information.process is None and lease._information.thread is None
    assert lease._lock is None and lease._state == 'CLOSED'
    assert lease._cleanup_deadline == lease._job.cleanup_deadline_ns
    assert lease._cleanup_deadline == lease._output._deadline
    assert lease._cleanup_deadline <= lease._deadline + 10_000_000_000
    before = lease._cleanup_deadline
    lease.__exit__(None, None, None)
    assert lease._cleanup_deadline == before
    for stream in lease._output._streams:
        assert not stream.thread.is_alive()


def test_stop_during_output_acquisition_denies_suspended_creation(tmp_path):
    from aluclu.alc_r0.reserved_owned_process import _LeaseOutputPair
    Signal, Stopped, Lease = api()
    signal = Signal()
    class StopPair(_LeaseOutputPair):
        def __enter__(self):
            result = super().__enter__()
            signal.request_stop()
            return result
    class StopLease(Lease):
        def _new_output(self, **arguments):
            return StopPair(self, **arguments)
    arguments, store, _, sentinel = fixture(tmp_path)
    lease = StopLease(**arguments, stop_signal=signal)
    with pytest.raises(Stopped):
        with lease:
            pytest.fail('precreation stop entered')
    assert not sentinel.exists() and not lease._information.pid
    closed(lease)
    pending(store, 'RESERVED')


@pytest.mark.parametrize('stage,state', [('entered', 'RESERVED'), ('ready', 'READY'),
    ('ready-publication', 'READY'), ('resume-live', 'READY'), ('running-publication', 'RUNNING')])
def test_stop_at_publication_and_resume_boundaries_drains_owned_handles(tmp_path, stage, state):
    Signal, Stopped, Lease = api()
    signal = Signal()
    class StopLease(Lease):
        def _publish_event(self, kind, **fields):
            result = super()._publish_event(kind, **fields)
            if (stage, kind) in (('ready-publication', 'identity_published'),
                                ('running-publication', 'running')):
                signal.request_stop()
            return result
        def _live_identity(self):
            super()._live_identity()
            if stage == 'resume-live' and self._state == 'READY':
                signal.request_stop()
    arguments, store, _, sentinel = fixture(tmp_path, source='import time;time.sleep(60)')
    lease = StopLease(**arguments, stop_signal=signal)
    retained = None
    try:
        with lease:
            retained = RetainedHandles(lease)
            if stage == 'entered':
                signal.request_stop()
            with pytest.raises(Stopped):
                ready = lease.publish_identity(ROOT, ROOT)
                if stage == 'ready':
                    signal.request_stop()
                lease.resume_verified(ready.sha256)
        retained.drained()
        closed(lease)
        pending(store, state)
        assert not sentinel.exists()
    finally:
        if retained is not None:
            retained.close()


def test_stop_after_created_response_failure_preserves_created(tmp_path):
    Signal, _, Lease = api()
    signal = Signal()
    class LostResponse(Lease):
        def _publish_event(self, kind, **fields):
            result = super()._publish_event(kind, **fields)
            if kind == 'child_created':
                signal.request_stop()
                raise OSError('diagnostic durable CREATED response lost')
            return result
    arguments, store, _, sentinel = fixture(tmp_path)
    with LostResponse(**arguments, stop_signal=signal) as lease:
        retained = RetainedHandles(lease)
        try:
            with pytest.raises(OSError, match='CREATED response lost'):
                lease.publish_identity(ROOT, ROOT)
            retained.drained()
            closed(lease)
            pending(store, 'CREATED')
            assert not sentinel.exists()
        finally:
            retained.close()


def test_running_stop_drains_descendant_not_unrelated_process(tmp_path):
    Signal, Stopped, Lease = api()
    signal, observing = Signal(), threading.Event()
    class ObservedLease(Lease):
        def _check_stop(self):
            super()._check_stop()
            if self._state == 'RUNNING':
                observing.set()
    source = ("import subprocess,sys,time;"
        "subprocess.Popen([sys.executable,'-I','-c','import time;time.sleep(60)']);"
        "time.sleep(60)")
    arguments, store, _, _ = fixture(tmp_path, source=source)
    unrelated = subprocess.Popen((sys.executable, '-I', '-c', 'import time;time.sleep(60)'))
    retained = None
    observer_errors = []
    def observe_stop():
        if not observing.wait(5):
            observer_errors.append('wait loop not reached')
        signal.request_stop()
    observer = threading.Thread(target=observe_stop)
    try:
        with ObservedLease(**arguments, stop_signal=signal) as lease:
            retained = RetainedHandles(lease)
            ready = lease.publish_identity(ROOT, ROOT)
            lease.resume_verified(ready.sha256)
            end = time.monotonic() + 5
            while lease._job.accounting().active_processes < 2:
                assert time.monotonic() < end, 'descendant not observed'
                time.sleep(0.01)
            observer.start()
            with pytest.raises(Stopped):
                lease.wait_terminal()
            retained.drained(total=2)
            closed(lease)
        assert unrelated.poll() is None
        pending(store, 'RUNNING')
    finally:
        observing.set()
        if observer.ident is not None:
            observer.join(5)
            assert not observer.is_alive()
        if retained is not None:
            retained.close()
        unrelated.terminate()
        unrelated.wait(timeout=10)
    assert not observer_errors


def test_already_exited_zero_cannot_return_terminal_after_stop(tmp_path):
    import _winapi
    Signal, Stopped, Lease = api()
    signal = Signal()
    arguments, store, _, _ = fixture(tmp_path, source='pass')
    with Lease(**arguments, stop_signal=signal) as lease:
        retained = RetainedHandles(lease)
        try:
            ready = lease.publish_identity(ROOT, ROOT)
            lease.resume_verified(ready.sha256)
            assert _winapi.WaitForSingleObject(lease._information.process, 5000) == 0
            signal.request_stop()
            with pytest.raises(Stopped):
                lease.wait_terminal()
            retained.drained(exit_code=0)
            closed(lease)
            pending(store, 'RUNNING')
        finally:
            retained.close()


@pytest.mark.parametrize('failure', [False, True], ids=['stop', 'cleanup-failure'])
def test_stop_during_output_finish_never_returns_receipt_or_renews_tail(tmp_path, failure):
    from aluclu.alc_r0.reserved_owned_process import _LeaseOutputPair
    Signal, Stopped, Lease = api()
    signal = Signal()
    bounds = []
    class StopPair(_LeaseOutputPair):
        def finish(self, cleanup_deadline_ns=None):
            result = super().finish(cleanup_deadline_ns)
            bounds.append(result.cleanup_deadline_ns)
            signal.request_stop()
            if failure:
                raise TimeoutError('diagnostic output finalization failed')
            return result
    class StopLease(Lease):
        def _new_output(self, **arguments):
            return StopPair(self, **arguments)
    arguments, store, _, _ = fixture(tmp_path, source='pass')
    with StopLease(**arguments, stop_signal=signal) as lease:
        retained = RetainedHandles(lease)
        try:
            ready = lease.publish_identity(ROOT, ROOT)
            lease.resume_verified(ready.sha256)
            with pytest.raises(TimeoutError if failure else Stopped):
                lease.wait_terminal()
            retained.drained(exit_code=0)
            closed(lease)
            assert bounds == [lease._cleanup_deadline]
            pending(store, 'RUNNING')
        finally:
            retained.close()


@pytest.mark.parametrize('acquired', [False, True], ids=['before', 'after'])
def test_missing_flag_exact_event_is_fixed_latched_denial(tmp_path, acquired):
    Signal, Stopped, Lease = api()
    signal = Signal()
    arguments, store, _, _ = fixture(tmp_path)
    if not acquired:
        del signal._event._flag
        with pytest.raises(Stopped, match='signal invalid'):
            Lease(**arguments, stop_signal=signal)
        assert not arguments['stdout_path'].exists()
        pending(store, 'RESERVED')
        return
    with Lease(**arguments, stop_signal=signal) as lease:
        retained = RetainedHandles(lease)
        try:
            del signal._event._flag
            with pytest.raises(Stopped, match='signal invalid'):
                lease.publish_identity(ROOT, ROOT)
            retained.drained()
            closed(lease)
            signal._event = threading.Event()
            with pytest.raises(Stopped):
                lease._check_stop()
            pending(store, 'RESERVED')
        finally:
            retained.close()


def test_malformed_signal_after_acquisition_drains_and_latches(tmp_path):
    Signal, Stopped, Lease = api()
    signal = Signal()
    arguments, store, _, _ = fixture(tmp_path)
    with Lease(**arguments, stop_signal=signal) as lease:
        retained = RetainedHandles(lease)
        try:
            signal._event = object()
            with pytest.raises(Stopped, match='signal invalid'):
                lease.publish_identity(ROOT, ROOT)
            retained.drained()
            closed(lease)
            signal._event = threading.Event()
            with pytest.raises(Stopped):
                lease._check_stop()
            pending(store, 'RESERVED')
        finally:
            retained.close()
