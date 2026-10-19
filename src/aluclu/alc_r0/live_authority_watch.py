"""Live denial transport, NOT authenticated observation or scientific admission.

A separately reviewed trusted producer must supply observations. This watch
executes no producer callback and grants no authority. The scientific worker
remains denied; real coordinators must independently revalidate final authority.
"""
import math
import threading
import time
from dataclasses import dataclass

from .authority_watch_policy import (
    OBSERVATION_NS, WAIT_NS, Observation, advance_watch, start_watch,
)
from .reserved_owned_process import OwnedStopSignal

_MAX = (1 << 63) - 1


class LiveWatchError(RuntimeError):
    """Watch transport/lifecycle failed; no accepting result is produced."""


@dataclass(frozen=True, slots=True)
class ObservationRequest:
    sequence: int
    started_monotonic_ns: int


class LiveAuthorityWatch:
    def __init__(self, policy, stop_signal):
        if type(stop_signal) is not OwnedStopSignal:
            raise TypeError('exact OwnedStopSignal required')
        pre_stopped = OwnedStopSignal._requested(stop_signal)
        self._state = start_watch(policy, time.monotonic_ns())
        self._policy, self._signal = policy, stop_signal
        self._condition = threading.Condition()
        self._owner = threading.get_ident()
        self._thread = None
        self._start_attempted = False
        self._request = self._response = None
        self._sequence = 0
        self._reason = 'stopped' if pre_stopped else None
        self._signal_error = False
        self._close_failed = False
        self._finished_ns = self._close_deadline = None

    @property
    def reason(self):
        with self._condition:
            return self._reason

    def _owner_thread(self):
        if threading.get_ident() != self._owner:
            raise LiveWatchError('watch owner thread required')

    def _deny_locked(self, reason):
        if self._reason is None:
            self._reason = reason
        self._request = self._response = None
        try:
            OwnedStopSignal.request_stop(self._signal)
        except BaseException:
            self._signal_error = True
        self._condition.notify_all()

    def start(self):
        self._owner_thread()
        with self._condition:
            if self._start_attempted or self._reason is not None:
                raise LiveWatchError('watch start is single use')
            self._start_attempted = True
            try:
                self._thread = threading.Thread(target=self._run,
                    name='alc-r0-authority-watch', daemon=False)
                self._thread.start()
            except BaseException:
                self._deny_locked('internal-error')
                raise LiveWatchError('watch thread start failed') from None

    def wait_request(self, timeout_seconds):
        if (type(timeout_seconds) not in (int, float)
                or not 0 <= timeout_seconds <= 1 or not math.isfinite(timeout_seconds)):
            raise ValueError('finite bounded wait required')
        with self._condition:
            self._condition.wait_for(lambda: self._reason is not None
                or (self._request is not None and self._response is None), timeout_seconds)
            return self._request if self._reason is None and self._response is None else None

    def submit(self, request, observation):
        with self._condition:
            if self._reason is not None:
                raise LiveWatchError('watch already stopped')
            if (type(request) is not ObservationRequest
                    or type(request.sequence) is not int or not 0 < request.sequence <= _MAX
                    or type(request.started_monotonic_ns) is not int
                    or not 0 < request.started_monotonic_ns <= _MAX
                    or type(observation) is not Observation
                    or request != self._request or self._response is not None):
                self._deny_locked('invalid-input')
                raise LiveWatchError('invalid observation submission')
            self._response = observation
            self._condition.notify_all()

    def _step_locked(self):
        observation, self._response = self._response, None
        if observation is not None:
            self._request = None
        now = time.monotonic_ns()
        decision = advance_watch(self._policy, self._state, now, observation)
        self._state = decision.state
        if decision.action == 'stop':
            self._deny_locked(decision.reason)
            return
        if decision.action == 'observe':
            if self._request is None:
                if self._sequence == _MAX:
                    raise ValueError('watch sequence exhausted')
                self._sequence += 1
                self._request = ObservationRequest(self._sequence, self._state.pending_since_ns)
            due = self._state.pending_since_ns + OBSERVATION_NS
        else:
            self._request = None
            due = self._state.next_poll_ns
        self._condition.notify_all()
        delay = max(0, min(WAIT_NS, due - time.monotonic_ns()))
        self._condition.wait(delay / 1e9)

    def _run(self):
        with self._condition:
            try:
                while self._reason is None:
                    self._step_locked()
            except ValueError:
                self._deny_locked('invalid-input')
            except BaseException:
                self._deny_locked('internal-error')
            finally:
                self._finished_ns = time.monotonic_ns()
                self._condition.notify_all()

    def close(self, cleanup_deadline_ns):
        self._owner_thread()
        if type(cleanup_deadline_ns) is not int or not 0 < cleanup_deadline_ns <= _MAX:
            raise ValueError('absolute cleanup deadline required')
        with self._condition:
            self._close_deadline = (cleanup_deadline_ns if self._close_deadline is None
                else min(self._close_deadline, cleanup_deadline_ns))
            self._deny_locked('stopped')
            thread = self._thread
            deadline = self._close_deadline
            if thread is None or thread.ident is None:
                if self._finished_ns is None:
                    self._finished_ns = time.monotonic_ns()
        if thread is not None and thread.ident is not None:
            thread.join(max(0, deadline - time.monotonic_ns()) / 1e9)
        with self._condition:
            if (self._close_failed or thread is not None and thread.is_alive()
                    or self._finished_ns is None or self._finished_ns > deadline):
                self._close_failed = True
                raise TimeoutError('watch closure unobserved within original bound')
            if self._signal_error:
                raise LiveWatchError('owned stop signaling unconfirmed')
