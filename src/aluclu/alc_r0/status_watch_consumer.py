"""Stateful denial transport; supplied path/pins/clock do NOT prove authority."""
import re
import threading
import time

from .authority_watch_policy import Observation, OBSERVATION_NS, start_watch
from .live_authority_watch import LiveAuthorityWatch
from .operator_status import OperatorStatus, decode_operator_status, read_operator_status
from .reserved_owned_process import OwnedStopSignal

_MAX = 2**63 - 1
_ROOT = re.compile(r'[0-9a-f]{64}\Z')


class StatusConsumerError(ValueError):
    """Sticky observation failure, never an accepting default."""


def _integer(value):
    if type(value) is not int or not 0 < value <= _MAX:
        raise StatusConsumerError('positive signed64 clock value required')


class StatusWatchConsumer:
    def __init__(self, installation_root, generation_root, clock_domain_root, stop_signal):
        for root in (installation_root, generation_root, clock_domain_root):
            if type(root) is not str or _ROOT.fullmatch(root) is None:
                raise StatusConsumerError('exact root required')
        if type(stop_signal) is not OwnedStopSignal:
            raise StatusConsumerError('exact owned signal required')
        self._installation = installation_root
        self._generation = generation_root
        self._clock = clock_domain_root
        self._signal = stop_signal
        self._owner = threading.get_ident()
        self._denied = OwnedStopSignal._requested(stop_signal)
        self._last = None
        self._last_observed = 0
        self._watch = self._policy = None

    def _deny(self):
        # A non-owner never modifies owner state; the one-way signal is sufficient.
        if threading.get_ident() == self._owner:
            self._denied = True
        OwnedStopSignal.request_stop(self._signal)

    def _active(self):
        if threading.get_ident() != self._owner:
            self._deny()
            raise StatusConsumerError('consumer owner thread required')
        if (self._denied or OwnedStopSignal._requested(self._signal)
                or self._watch is not None and self._watch.reason is not None):
            self._deny()
            raise StatusConsumerError('consumer permanently stopped')

    def _bind(self, watch):
        self._active()
        if (type(watch) is not LiveAuthorityWatch or watch._signal is not self._signal
                or watch._policy.generation_root != self._generation
                or watch._policy.clock_domain_root != self._clock):
            raise StatusConsumerError('watch binding mismatch')
        start_watch(watch._policy, time.monotonic_ns())  # validates complete policy
        if self._watch is None:
            self._watch, self._policy = watch, watch._policy
        elif self._watch is not watch or watch._policy != self._policy:
            raise StatusConsumerError('watch rebinding forbidden')
        self._active()

    def consume(self, status, *, observed_monotonic_ns, utc_upper_ns):
        try:
            self._active()
            _integer(observed_monotonic_ns); _integer(utc_upper_ns)
            if type(status) is not OperatorStatus or decode_operator_status(status.data) != status:
                raise StatusConsumerError('unvalidated status metadata')
            if (status.installation_root != self._installation
                    or status.generation_root != self._generation or status.revoked
                    or status.expires_utc_ns <= utc_upper_ns
                    or observed_monotonic_ns < self._last_observed):
                raise StatusConsumerError('changed, revoked, expired or regressed observation')
            if self._last is not None and (
                    status.sequence < self._last.sequence
                    or status.sequence == self._last.sequence and status != self._last
                    or status.expires_utc_ns > self._last.expires_utc_ns):
                raise StatusConsumerError('status sequence/root/expiry regression')
            if self._policy is not None:
                required = utc_upper_ns + self._policy.envelope_deadline_ns - observed_monotonic_ns
                if (observed_monotonic_ns >= self._policy.useful_deadline_ns
                        or required > _MAX or status.expires_utc_ns <= required):
                    raise StatusConsumerError('original deadline or envelope uncovered')
            self._active()
            result = Observation(self._generation, self._clock, False,
                                 observed_monotonic_ns, utc_upper_ns, status.expires_utc_ns)
            self._last, self._last_observed = status, observed_monotonic_ns
            return result
        except BaseException:
            self._deny()
            raise

    def serve_once(self, watch, path, utc_upper_ns, *, utc_anchor_monotonic_ns):
        """Queue one response; not watch acceptance or authenticated clock evidence.

        The supplied anchored UTC envelope must independently justify at most
        one UTC nanosecond growth per elapsed monotonic nanosecond in this domain.
        Caller owns interruption/termination of potentially blocking OS reads.
        """
        try:
            self._bind(watch)
            _integer(utc_upper_ns); _integer(utc_anchor_monotonic_ns)
            if utc_anchor_monotonic_ns > time.monotonic_ns():
                raise StatusConsumerError('future UTC anchor')
            request = watch.wait_request(0.02)
            self._active()
            if request is None:
                return False
            deadline = min(self._policy.useful_deadline_ns,
                           request.started_monotonic_ns + OBSERVATION_NS)
            _integer(deadline)
            status = read_operator_status(path, deadline_ns=deadline)
            captured = time.monotonic_ns()
            if not request.started_monotonic_ns <= captured < deadline:
                raise StatusConsumerError('original observation deadline exceeded')
            advanced_utc = utc_upper_ns + captured - utc_anchor_monotonic_ns
            observation = self.consume(status, observed_monotonic_ns=captured,
                                       utc_upper_ns=advanced_utc)
            self._active()
            if time.monotonic_ns() >= deadline:
                raise StatusConsumerError('late submission')
            watch.submit(request, observation)
            if time.monotonic_ns() >= deadline:
                raise StatusConsumerError('late queued submission')
            self._active()
            return True
        except BaseException:
            self._deny()
            raise
