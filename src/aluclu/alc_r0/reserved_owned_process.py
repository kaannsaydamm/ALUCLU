"""Trusted Windows lease: durable identity before resume, never training authority.

Only the creating coordinator thread may use a lease. Reservation roots bind
storage, not permission. Clock-domain proof, numeric budgets and output caps are
external admission obligations. No PID discovery, implicit recovery or release.
"""

from __future__ import annotations

import ctypes
import os
import re
import secrets
import threading
import time
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path

from .canonical import canonical_json_bytes, parse_canonical_json, sha256_bytes
from .checkpoint_owned_process import (
    OwnedProcessReceipt, _Job, _ProcessInformation, _checked,
    _create_suspended, _resume, _validate,
)
from .reservation_store import ReservationStore

_ROOT = re.compile(r"[0-9a-f]{64}\Z")
_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")


@dataclass(frozen=True, slots=True)
class OwnedChildIdentity:
    pid: int
    creation_filetime_100ns: int
    owner_nonce: str
    receipt_root: str


@dataclass(frozen=True, slots=True)
class ReservedTerminalReceipt:
    process: OwnedProcessReceipt
    identity: OwnedChildIdentity
    owner_root: str


class _FileTime(ctypes.Structure):
    _fields_ = [("low", ctypes.c_uint32), ("high", ctypes.c_uint32)]


def _creation_time(handle):
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    function = kernel.GetProcessTimes
    function.argtypes = [ctypes.c_void_p] + [ctypes.POINTER(_FileTime)] * 4
    function.restype = ctypes.c_int
    values = [_FileTime() for _ in range(4)]
    _checked(function(handle, *(ctypes.byref(value) for value in values)))
    value = values[0].low | (values[0].high << 32)
    if not value:
        raise RuntimeError("owned creation FILETIME missing")
    return value


def _root(value):
    if type(value) is not str or not _ROOT.fullmatch(value):
        raise ValueError("exact root required")
    return value


class ReservedOwnedLease:
    def __init__(self, store, expected_owner_root, reservation_id, command, *, cwd,
                 environment, stdout_path, stderr_path, deadline_ns, clock_domain_root):
        if type(store) is not ReservationStore:
            raise TypeError("exact ReservationStore required")
        _root(expected_owner_root)
        _root(clock_domain_root)
        if type(reservation_id) is not str or not _ID.fullmatch(reservation_id):
            raise ValueError("reservation ID required")
        if (type(command) is not tuple or not command
                or any(type(item) is not str or "\x00" in item for item in command)):
            raise ValueError("immutable NUL-free command required")
        if any(not isinstance(path, Path) or not path.is_absolute()
               for path in (cwd, stdout_path, stderr_path)):
            raise ValueError("absolute paths required")
        if type(environment) is not dict or any(type(key) is not str or type(value) is not str
                                               for key, value in environment.items()):
            raise ValueError("explicit string environment required")
        if type(deadline_ns) is not int or not 0 < deadline_ns <= (1 << 63) - 1:
            raise ValueError("absolute deadline required")
        self._store, self._owner_root, self._id = store, expected_owner_root, reservation_id
        self._command, self._cwd, self._environment = command, cwd, dict(environment)
        self._stdout_path, self._stderr_path = stdout_path, stderr_path
        self._deadline, self._clock = deadline_ns, clock_domain_root
        self._thread = threading.get_ident()
        self._state = "NEW"
        self._stack = ExitStack()
        self._lock = None
        self._job = None
        self._information = _ProcessInformation()
        self._identity = None
        self._ready_root = None
        self._evidence = self._review = None
        self._resume_attempted = self._wait_attempted = False

    def _require(self, *states):
        if threading.get_ident() != self._thread or self._state not in states:
            raise RuntimeError("lease lifecycle/thread mismatch")

    @property
    def identity(self):
        self._require("SUSPENDED", "READY", "RUNNING", "TERMINAL")
        return self._identity

    def _view(self, receipt, expected_state):
        views = [view for view in receipt.snapshot.reservations if view.reservation_id == self._id]
        if len(views) != 1 or views[0].state != expected_state or receipt.snapshot.overrun:
            raise ValueError("reservation state/overrun mismatch")
        view = views[0]
        if self._identity is not None and expected_state != "RESERVED":
            if (view.pid, view.creation_filetime_100ns, view.owner_nonce, view.identity_receipt_root) != (
                self._identity.pid, self._identity.creation_filetime_100ns,
                self._identity.owner_nonce, self._identity.receipt_root):
                raise ValueError("reservation identity mismatch")
        return view

    def _unexpired(self):
        if time.monotonic_ns() >= self._deadline:
            raise TimeoutError("original reservation deadline expired")

    def __enter__(self):
        self._require("NEW")
        self._state = "ENTERING"
        try:
            lock = self._store._lock()
            lock.__enter__()
            self._lock = lock
            owner, replay, _ = self._store._read_locked(self._owner_root)
            self._view(self._store._receipt(owner, replay), "RESERVED")
            events = [parse_canonical_json(event) for event in replay._events]
            reserves = [event for event in events
                        if event["reservation_id"] == self._id and event["kind"] == "reserve"]
            if len(reserves) != 1:
                raise ValueError("single original reserve required")
            reserve = reserves[0]
            if (reserve["clock_domain_root"] != self._clock
                    or int(reserve["useful_deadline_monotonic_ns"]) != self._deadline):
                raise ValueError("original clock/deadline mismatch")
            self._unexpired()
            _validate(self._command, self._cwd, self._environment,
                      self._stdout_path, self._stderr_path, self._deadline)
            stdout = self._stack.enter_context(self._stdout_path.open("xb"))
            stderr = self._stack.enter_context(self._stderr_path.open("xb"))
            stdin = self._stack.enter_context(open(os.devnull, "rb"))
            self._job = self._stack.enter_context(_Job())
            self._started = time.monotonic_ns()
            _create_suspended(self._command, self._cwd, self._environment, stdin, stdout,
                              stderr, self._deadline, self._job, self._information)
            created = self._observe_creation_time()
            nonce = secrets.token_hex(16)
            root = sha256_bytes(canonical_json_bytes(dict(schema="alc-r0-owned-child-v1",
                reservation_id=self._id, pid=str(self._information.pid),
                creation_filetime_100ns=str(created), owner_nonce=nonce)))
            self._identity = OwnedChildIdentity(self._information.pid, created, nonce, root)
            self._state = "SUSPENDED"
            return self
        except BaseException:
            self._close()
            raise

    def _observe_creation_time(self):
        """Narrow owned-handle observation boundary, also usable by diagnostics."""
        return _creation_time(self._information.process)

    def _live_identity(self):
        import _winapi
        self._unexpired()
        if (_winapi.WaitForSingleObject(self._information.process, 0) != 258
                or _creation_time(self._information.process) != self._identity.creation_filetime_100ns):
            raise RuntimeError("owned handle no longer live/matching")

    def _publish_event(self, kind, **fields):
        receipt = self._store.read(self._owner_root)
        event = canonical_json_bytes(dict(sequence=str(receipt.snapshot.event_count + 1),
            previous_root=receipt.snapshot.root, reservation_id=self._id, kind=kind,
            evidence_root=self._evidence, **fields))
        intent = self._store.prepare(self._owner_root, event, self._review)
        published = self._store.commit(intent)
        self._owner_root = published.sha256
        return published

    def publish_identity(self, evidence_root, review_root):
        self._require("SUSPENDED")
        _root(evidence_root)
        _root(review_root)
        self._evidence, self._review = evidence_root, review_root
        try:
            self._live_identity()
            self._view(self._store.read(self._owner_root), "RESERVED")
            identity = self._identity
            created = self._publish_event("child_created", pid=str(identity.pid),
                creation_filetime_100ns=str(identity.creation_filetime_100ns),
                owner_nonce=identity.owner_nonce, identity_receipt_root=identity.receipt_root)
            ready = self._publish_event("identity_published", identity_receipt_root=identity.receipt_root,
                                        publication_root=created.sha256)
            self._view(self._store.read(ready.sha256), "READY")
            self._ready_root = ready.sha256
            self._state = "READY"
            return ready
        except BaseException:
            self._close()
            raise

    def resume_verified(self, expected_ready_owner_root):
        self._require("READY")
        if expected_ready_owner_root != self._ready_root:
            raise ValueError("locally retained exact READY root required")
        if self._resume_attempted:
            raise RuntimeError("resume already attempted")
        try:
            self._view(self._store.read(self._ready_root), "READY")
            self._live_identity()
            self._resume_attempted = True
            _resume(self._information.thread)
            resumed = time.monotonic_ns()
            root = sha256_bytes(canonical_json_bytes(dict(schema="alc-r0-owned-resume-v1",
                identity_receipt_root=self._identity.receipt_root, ready_owner_root=self._ready_root,
                resumed_monotonic_ns=str(resumed))))
            running = self._publish_event("running", resume_receipt_root=root)
            self._view(self._store.read(running.sha256), "RUNNING")
            self._unlock()
            self._state = "RUNNING"
            return running
        except BaseException:
            self._close()
            raise

    def wait_terminal(self):
        import _winapi
        self._require("RUNNING")
        if self._wait_attempted:
            raise RuntimeError("terminal wait already attempted")
        self._wait_attempted = True
        try:
            timed_out = False
            while self._job.accounting().active_processes:
                remaining = self._deadline - time.monotonic_ns()
                if remaining <= 0:
                    timed_out = True
                    self._job.terminate_and_drain()
                    break
                time.sleep(min(0.02, remaining / 1e9))
            accounting = self._job.accounting()
            if (accounting.active_processes or _winapi.WaitForSingleObject(
                    self._information.process, self._job.remaining_cleanup_ms()) != 0):
                raise TimeoutError("owned root/tree terminal unobserved")
            receipt = OwnedProcessReceipt(self._information.pid,
                _winapi.GetExitCodeProcess(self._information.process), timed_out,
                self._started, time.monotonic_ns(), accounting.total_processes,
                accounting.active_processes, accounting.user_time, accounting.kernel_time)
            self._state = "TERMINAL"
            return ReservedTerminalReceipt(receipt, self._identity, self._owner_root)
        except BaseException:
            self._close()
            raise

    def _unlock(self):
        if self._lock is not None:
            lock, self._lock = self._lock, None
            lock.__exit__(None, None, None)

    def _close(self):
        self._state = "CLOSED"
        # Validation can fail before acquiring any Windows resource, including
        # on unsupported hosts. Do not mask that error with a _winapi import.
        if self._job is None and not self._information.process and not self._information.thread:
            try:
                self._stack.close()
            finally:
                self._unlock()
            return
        import _winapi
        try:
            if self._job is not None:
                if self._job.accounting().active_processes:
                    self._job.terminate_and_drain()
                if self._information.process and _winapi.WaitForSingleObject(
                        self._information.process, self._job.remaining_cleanup_ms()) != 0:
                    raise TimeoutError("cleanup root terminal unobserved")
        finally:
            try:
                try:
                    if self._information.thread:
                        _winapi.CloseHandle(self._information.thread)
                        self._information.thread = None
                finally:
                    if self._information.process:
                        _winapi.CloseHandle(self._information.process)
                        self._information.process = None
            finally:
                try:
                    self._stack.close()
                finally:
                    self._unlock()

    def __exit__(self, *exception):
        if threading.get_ident() != self._thread:
            raise RuntimeError("lease coordinator thread mismatch")
        if self._state != "CLOSED":
            self._close()
