"""Bounded binary capture, not process control or scientific launch authority.

Two readers own their destinations until terminal cleanup. A missed deadline is
incomplete cleanup, not permission to close another thread's in-flight handle.
"""

from __future__ import annotations

import hashlib
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path

_MAX = (1 << 63) - 1
_CHUNK = 65536


class OutputCleanupError(RuntimeError):
    """Owned output resources could not be observed completely closed in time."""


@dataclass(frozen=True, slots=True)
class StreamObservation:
    limit_bytes: int
    received_bytes: int | None
    received_complete: bool
    confirmed_written_bytes: int
    persisted_bytes: int | None
    excess: bool
    eof: bool
    terminal: bool
    resources_closed: bool
    failure_kinds: tuple[str, ...]
    confirmed_prefix_sha256: str | None
    file_sha256: str | None
    finished_monotonic_ns: int | None


@dataclass(frozen=True, slots=True)
class BoundedOutputReceipt:
    stdout: StreamObservation
    stderr: StreamObservation
    cleanup_deadline_ns: int
    valid: bool


class _Stream:
    def __init__(self, path, limit):
        self.path, self.limit = path, limit
        self.reader = self.writer = self.destination = self.thread = None
        self.lock = threading.Lock()
        self.received = 0
        self.written = 0
        self.digest = hashlib.sha256()
        self.established = False
        self.persisted_known = True
        self.excess = self.eof = self.terminal = False
        self.reader_closed = self.destination_closed = self.writer_closed = False
        self.writer_finished = None
        self.pipe_closure_unknown = False
        self.errors = set()
        self.finished = None

    def snapshot(self):
        with self.lock:
            prefix = self.digest.hexdigest() if self.established else None
            closed = self.reader_closed and self.destination_closed and self.writer_closed
            known = self.established and self.persisted_known and self.destination_closed
            return StreamObservation(self.limit, self.received,
                self.eof and self.received is not None, self.written,
                self.written if known else None, self.excess, self.eof,
                self.terminal, closed, tuple(sorted(self.errors)), prefix,
                prefix if known else None, self.finished)


def _integer(value, minimum=0):
    if type(value) is not int or not minimum <= value <= _MAX:
        raise ValueError("bounded exact integer required")
    return value


class BoundedOutputPair:
    def __init__(self, stdout_path, stderr_path, stdout_limit_bytes,
                 stderr_limit_bytes, cleanup_deadline_ns):
        if any(not isinstance(path, Path) or not path.is_absolute()
               for path in (stdout_path, stderr_path)):
            raise ValueError("absolute output paths required")
        if os.path.normcase(os.path.normpath(stdout_path)) == os.path.normcase(
                os.path.normpath(stderr_path)):
            raise ValueError("distinct output paths required")
        self._streams = (_Stream(stdout_path, _integer(stdout_limit_bytes)),
                         _Stream(stderr_path, _integer(stderr_limit_bytes)))
        self._deadline = _integer(cleanup_deadline_ns, 1)
        self._entered = self._finish_attempted = self._finish_failed = False
        self._owner_thread = None
        self._receipt = None
        self._pipe_cleanup_uncertain = False
        self._uncertain_pipe_ownership = None

    def _owner(self):
        if not self._entered or threading.get_ident() != self._owner_thread:
            raise RuntimeError("creating context thread required")

    @property
    def stdout(self):
        self._owner()
        return self._streams[0].writer

    @property
    def stderr(self):
        self._owner()
        return self._streams[1].writer

    def observations(self):
        """Short immutable snapshots; bookkeeping locks never cover I/O."""
        return tuple(stream.snapshot() for stream in self._streams)

    @property
    def violated(self):
        return any(item.excess or item.failure_kinds for item in self.observations())

    def _open_destination(self, path):
        return path.open("xb", buffering=0)

    def _make_pipe(self):
        reader_fd, writer_fd = os.pipe()
        reader = None
        try:
            reader = self._pipe_stream(reader_fd, "rb")
            writer = self._pipe_stream(writer_fd, "wb")
            return reader, writer
        except BaseException as acquisition:
            try:
                try:
                    if reader is None:
                        os.close(reader_fd)
                    else:
                        reader.close()
                finally:
                    os.close(writer_fd)
            except BaseException as cleanup:
                # Retain bounded ownership uncertainty; do not retry a raw fd
                # whose close effect is unknown (it may already be reused).
                self._pipe_cleanup_uncertain = True
                self._uncertain_pipe_ownership = (reader, reader_fd, writer_fd)
                raise cleanup from acquisition
            raise

    def _pipe_stream(self, descriptor, mode):
        """Narrow actual fd-to-stream acquisition boundary for diagnostics."""
        return os.fdopen(descriptor, mode, buffering=0)

    def _start_pump(self, thread):
        thread.start()

    def __enter__(self):
        if self._entered:
            raise RuntimeError("output context is single use")
        self._entered = True
        self._owner_thread = threading.get_ident()
        if time.monotonic_ns() >= self._deadline:
            raise TimeoutError("output cleanup deadline expired before acquisition")
        try:
            for stream in self._streams:
                try:
                    stream.destination = self._open_destination(stream.path)
                    stream.established = True
                    stream.reader, stream.writer = self._make_pipe()
                except BaseException:
                    with stream.lock:
                        stream.errors.add("acquire")
                        if self._pipe_cleanup_uncertain:
                            stream.errors.add("close")
                            stream.pipe_closure_unknown = True
                    raise
            for stream in self._streams:
                # Retain potential ownership BEFORE start: even a start error
                # cannot prove that no thread acquired these handles.
                stream.thread = threading.Thread(target=self._pump,
                    args=(stream,), daemon=True, name="aluclu-bounded-output")
                try:
                    self._start_pump(stream.thread)
                except BaseException:
                    with stream.lock:
                        stream.errors.add("thread_start")
                    raise
            return self
        except BaseException as cause:
            try:
                self._close_writers_then(self._partial_observation)
            except BaseException as cleanup:
                raise cleanup from cause
            raise

    def _partial_observation(self):
        for stream in self._streams:
            if stream.thread is None:
                self._close_read_side(stream)
        self._observe_terminal(self._deadline)

    def _close_writers_then(self, observation):
        closure_failure = None
        try:
            self.close_parent_writers()
        except BaseException as failure:
            closure_failure = failure
        try:
            observation()
        except BaseException as failure:
            if closure_failure is not None:
                raise failure from closure_failure
            raise
        if closure_failure is not None:
            raise closure_failure

    def _read(self, reader):
        return os.read(reader.fileno(), _CHUNK)

    def _write(self, destination, data):
        return destination.write(data)

    def _close_resource(self, resource):
        resource.close()

    def _close_read_side(self, stream):
        for name in ("reader", "destination"):
            resource = getattr(stream, name)
            try:
                if resource is not None:
                    self._close_resource(resource)
            except BaseException:
                with stream.lock:
                    stream.errors.add("close")
                    if name == "destination":
                        stream.persisted_known = False
            else:
                with stream.lock:
                    setattr(stream, name + "_closed", True)
        with stream.lock:
            if stream.pipe_closure_unknown:
                stream.reader_closed = False
            stream.finished = time.monotonic_ns()
            stream.terminal = True

    def _persist(self, stream, data):
        view = memoryview(data)
        with stream.lock:
            remaining = stream.limit - stream.written
            allowed = min(remaining, len(view))
            writable = "write" not in stream.errors
        if not writable:
            return
        view = view[:allowed]
        while view:
            try:
                count = self._write(stream.destination, view)
                if type(count) is not int or not 0 < count <= len(view):
                    raise OSError("unconfirmed output write")
            except BaseException:
                with stream.lock:
                    stream.persisted_known = False
                    stream.errors.add("write")
                return
            with stream.lock:
                stream.digest.update(view[:count])
                stream.written += count  # bounded by the previously validated cap
            view = view[count:]

    def _pump(self, stream):
        try:
            while True:
                try:
                    data = self._read(stream.reader)
                    if type(data) is not bytes or len(data) > _CHUNK:
                        raise OSError("invalid bounded read")
                except BaseException:
                    with stream.lock:
                        stream.errors.add("read")
                    break
                if not data:
                    with stream.lock:
                        stream.eof = True
                    break
                with stream.lock:
                    if stream.received is not None:
                        if stream.received > _MAX - len(data):
                            stream.received = None
                            stream.errors.add("overflow")
                            stream.excess = True
                        else:
                            stream.received += len(data)
                            stream.excess |= stream.received > stream.limit
                self._persist(stream, data)
                del data  # release the old payload BEFORE allocating the next read
        finally:
            self._close_read_side(stream)

    def close_parent_writers(self):
        self._owner()
        failed = False
        for stream in self._streams:
            with stream.lock:
                already_closed = stream.writer_closed
            if already_closed:
                continue
            try:
                if stream.writer is not None:
                    self._close_resource(stream.writer)
            except BaseException:
                with stream.lock:
                    stream.errors.add("close")
                failed = True
            else:
                with stream.lock:
                    stream.writer_closed = True
                    stream.writer_finished = time.monotonic_ns()
        if failed:
            raise OutputCleanupError("parent output writer closure unconfirmed")

    def _observe_terminal(self, deadline):
        failed = False
        for stream in self._streams:
            thread = stream.thread
            if thread is not None:
                try:
                    thread.join(max(0, deadline - time.monotonic_ns()) / 1e9)
                except RuntimeError:
                    # An uncertain start cannot justify closing retained handles.
                    failed = True
                if thread.is_alive():
                    failed = True
            item = stream.snapshot()
            with stream.lock:
                writer_finished = stream.writer_finished
            unobserved = (not item.terminal or item.finished_monotonic_ns is None
                          or writer_finished is None)
            late = ((item.finished_monotonic_ns is not None
                     and item.finished_monotonic_ns > deadline)
                    or (writer_finished is not None and writer_finished > deadline))
            if late or (unobserved and time.monotonic_ns() >= deadline):
                with stream.lock:
                    stream.errors.add("cleanup_deadline")
            if late or unobserved or not item.resources_closed:
                failed = True
        if failed:
            raise OutputCleanupError("output cleanup incomplete within original bound")

    def finish(self, cleanup_deadline_ns=None):
        self._owner()
        if self._finish_attempted:
            raise RuntimeError("output finish is single use")
        deadline = self._deadline if cleanup_deadline_ns is None else _integer(
            cleanup_deadline_ns, 1)
        if deadline > self._deadline:
            raise ValueError("output cleanup deadline cannot extend")
        self._deadline = deadline
        self._finish_attempted = True
        try:
            self._observe_terminal(deadline)
        except BaseException:
            self._finish_failed = True
            raise
        stdout, stderr = self.observations()
        valid = all(item.eof and item.received_complete and not item.excess
            and not item.failure_kinds and item.persisted_bytes is not None
            and item.file_sha256 is not None for item in (stdout, stderr))
        self._receipt = BoundedOutputReceipt(stdout, stderr, deadline, valid)
        return self._receipt

    def __exit__(self, *exc):
        self._close_writers_then(self._exit_observation)
        return False

    def _exit_observation(self):
        if self._finish_failed:
            raise OutputCleanupError("previous output finish failed; no renewed allowance")
        if not self._finish_attempted:
            self.finish()
