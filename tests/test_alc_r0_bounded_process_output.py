"""Isolated byte-cap fixtures, no child/model/GPU or scientific authority."""

import hashlib
import os
import threading
import time

import pytest

from aluclu.alc_r0.bounded_process_output import BoundedOutputPair, OutputCleanupError


def arguments(tmp_path, *, cap=8, seconds=3):
    return dict(stdout_path=tmp_path / "stdout", stderr_path=tmp_path / "stderr",
        stdout_limit_bytes=cap, stderr_limit_bytes=cap,
        cleanup_deadline_ns=time.monotonic_ns() + int(seconds * 1e9))


def send(stream, data):
    """Own pipe writer, no unbounded buffered file copy or child process."""
    view = memoryview(data)
    while view:
        written = os.write(stream.fileno(), view[:65536])
        assert written > 0
        view = view[written:]


@pytest.mark.parametrize("cap,payload,valid", [(0, b"", True), (0, b"x", False),
    (5, b"abcde", True), (4, b"abcde", False), (8, b"\xff\x00\xfe", True),
    (17, b"z" * 131073, False)],
    ids=["empty-zero", "nonempty-zero", "exact", "cap-plus-one", "binary", "large-excess"])
def test_exact_persisted_cap_and_honest_received_counts(tmp_path, cap, payload, valid):
    with BoundedOutputPair(**arguments(tmp_path, cap=cap)) as pair:
        send(pair.stdout, payload)
        pair.close_parent_writers()
        receipt = pair.finish()
        assert receipt.valid is valid
        output = receipt.stdout
        assert output.limit_bytes == cap and output.received_bytes == len(payload)
        assert output.received_complete and output.eof and output.terminal
        assert output.resources_closed and not output.failure_kinds
        expected = payload[:cap]
        assert output.confirmed_written_bytes == output.persisted_bytes == len(expected)
        assert output.excess is (len(payload) > cap)
        digest = hashlib.sha256(expected).hexdigest()
        assert output.confirmed_prefix_sha256 == output.file_sha256 == digest
        assert output.finished_monotonic_ns <= receipt.cleanup_deadline_ns
        assert receipt.stderr.received_bytes == 0 and receipt.stderr.resources_closed
    assert (tmp_path / "stdout").read_bytes() == expected


def test_independent_stderr_excess_invalidates_pair(tmp_path):
    values = arguments(tmp_path)
    values["stderr_limit_bytes"] = 2
    with BoundedOutputPair(**values) as pair:
        send(pair.stdout, b"normal")
        send(pair.stderr, b"error")
        pair.close_parent_writers()
        receipt = pair.finish()
    assert not receipt.valid and not receipt.stdout.excess and receipt.stderr.excess
    assert (tmp_path / "stdout").read_bytes() == b"normal"
    assert (tmp_path / "stderr").read_bytes() == b"er"


@pytest.mark.parametrize("key", ["stdout_limit_bytes", "stderr_limit_bytes"])
@pytest.mark.parametrize("value", [True, -1, 1.5, 1 << 63])
def test_cap_validation_has_no_output_side_effects(tmp_path, key, value):
    values = arguments(tmp_path)
    values[key] = value
    with pytest.raises((TypeError, ValueError)):
        BoundedOutputPair(**values)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("value", [True, 0, -1, 1.5, 1 << 63])
def test_cleanup_deadline_structural_validation_before_io(tmp_path, value):
    values = arguments(tmp_path)
    values["cleanup_deadline_ns"] = value
    with pytest.raises((TypeError, ValueError)):
        BoundedOutputPair(**values)
    assert list(tmp_path.iterdir()) == []


def test_expired_cleanup_bound_denied_before_artifacts(tmp_path):
    values = arguments(tmp_path)
    values["cleanup_deadline_ns"] = time.monotonic_ns() - 1
    with pytest.raises(TimeoutError):
        with BoundedOutputPair(**values):
            pytest.fail("expired capture entered")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("name", ["stdout", "stderr"])
def test_exclusive_destination_collision_preserves_existing_bytes(tmp_path, name):
    (tmp_path / name).write_bytes(b"preserved")
    with pytest.raises(FileExistsError):
        with BoundedOutputPair(**arguments(tmp_path)):
            pytest.fail("collision entered")
    assert (tmp_path / name).read_bytes() == b"preserved"


def test_finish_can_tighten_but_never_extend_or_repeat(tmp_path):
    values = arguments(tmp_path)
    with BoundedOutputPair(**values) as pair:
        with pytest.raises(ValueError):
            pair.finish(values["cleanup_deadline_ns"] + 1)
        pair.close_parent_writers()
        earlier = values["cleanup_deadline_ns"] - 100_000_000
        receipt = pair.finish(earlier)
        assert receipt.cleanup_deadline_ns == earlier and receipt.valid
        with pytest.raises(RuntimeError):
            pair.finish()


def test_context_exit_observes_eof_and_reentry_rejected(tmp_path):
    pair = BoundedOutputPair(**arguments(tmp_path))
    with pair:
        send(pair.stdout, b"done")
        with pytest.raises(RuntimeError):
            pair.__enter__()
    with pytest.raises(RuntimeError):
        pair.__enter__()
    assert (tmp_path / "stdout").read_bytes() == b"done"


class ShortWrites(BoundedOutputPair):
    def _write(self, destination, data):
        return super()._write(destination, data[:2])


def test_confirmed_short_writes_do_not_drop_bytes_or_corrupt_digest(tmp_path):
    with ShortWrites(**arguments(tmp_path)) as pair:
        send(pair.stdout, b"abcdefg")
        pair.close_parent_writers()
        receipt = pair.finish()
    assert receipt.valid and receipt.stdout.persisted_bytes == 7
    assert (tmp_path / "stdout").read_bytes() == b"abcdefg"
    assert receipt.stdout.file_sha256 == hashlib.sha256(b"abcdefg").hexdigest()


class ReadError(BoundedOutputPair):
    def _read(self, reader):
        raise OSError("diagnostic read failure")


def test_terminal_read_error_without_eof_is_invalid_not_fake_complete(tmp_path):
    with ReadError(**arguments(tmp_path)) as pair:
        pair.close_parent_writers()
        receipt = pair.finish()
    assert not receipt.valid
    for stream in (receipt.stdout, receipt.stderr):
        assert stream.terminal and stream.resources_closed and not stream.eof
        assert not stream.received_complete and stream.received_bytes == 0
        assert "read" in stream.failure_kinds


class UncertainWrite(BoundedOutputPair):
    def _write(self, destination, data):
        super()._write(destination, data[:2])
        raise OSError("diagnostic unknown partial-write effect")


def test_unconfirmed_partial_write_is_not_a_confirmed_full_file_digest(tmp_path):
    with UncertainWrite(**arguments(tmp_path)) as pair:
        send(pair.stdout, b"abcdef")
        pair.close_parent_writers()
        receipt = pair.finish()
    assert not receipt.valid and "write" in receipt.stdout.failure_kinds
    assert receipt.stdout.confirmed_written_bytes == 0
    assert receipt.stdout.file_sha256 is None
    assert receipt.stdout.confirmed_prefix_sha256 == hashlib.sha256(b"").hexdigest()
    assert (tmp_path / "stdout").read_bytes() == b"ab"


class PipeAcquisitionError(BoundedOutputPair):
    def _make_pipe(self):
        raise OSError("diagnostic pipe acquisition failure")


def test_partial_acquisition_closes_only_parent_owned_resources(tmp_path):
    pair = PipeAcquisitionError(**arguments(tmp_path))
    with pytest.raises(OSError, match="diagnostic pipe acquisition"):
        pair.__enter__()
    assert all(item.terminal and item.resources_closed for item in pair.observations())
    assert pair._streams[0].destination.closed
    assert "acquire" in pair.observations()[0].failure_kinds
    assert (tmp_path / "stdout").read_bytes() == b""
    assert not (tmp_path / "stderr").exists()


class StartedThenError(BoundedOutputPair):
    def _start_pump(self, thread):
        super()._start_pump(thread)
        raise OSError("diagnostic error after actual start")


def test_entry_error_after_actual_thread_start_observes_owned_cleanup(tmp_path):
    pair = StartedThenError(**arguments(tmp_path))
    with pytest.raises(OSError, match="after actual start"):
        pair.__enter__()
    assert all(item.terminal and item.resources_closed for item in pair.observations())
    assert not pair._streams[0].thread.is_alive()
    assert "thread_start" in pair.observations()[0].failure_kinds


class HeldRead(BoundedOutputPair):
    def __init__(self, **values):
        super().__init__(**values)
        self.release = threading.Event()
        self.reading = threading.Event()

    def _read(self, reader):
        self.reading.set()
        if not self.release.wait(2):
            raise OSError("diagnostic read gate expired")
        return super()._read(reader)


def test_cleanup_deadline_retains_unobserved_io_and_does_not_renew(tmp_path):
    pair = HeldRead(**arguments(tmp_path))
    pair.__enter__()
    try:
        assert pair.reading.wait(1)
        pair.close_parent_writers()
        # Snapshots must be available while actual pump I/O is blocked.
        assert all(not item.terminal for item in pair.observations())
        with pytest.raises(OutputCleanupError):
            pair.finish(time.monotonic_ns() + 20_000_000)
        assert pair.violated
        assert all(not stream.reader.closed for stream in pair._streams)
        with pytest.raises(RuntimeError, match="single use"):
            pair.finish()
        with pytest.raises(OutputCleanupError, match="no renewed allowance"):
            pair.__exit__(None, None, None)
    finally:
        # This isolated diagnostic owns the gate. It does not forcibly close
        # pump descriptors; release I/O and personally join each original thread.
        pair.release.set()
        for stream in pair._streams:
            stream.thread.join(2)
            assert not stream.thread.is_alive()
    assert all(item.terminal and item.resources_closed for item in pair.observations())


class CloseError(BoundedOutputPair):
    def _close_resource(self, resource):
        super()._close_resource(resource)
        if resource is self._streams[0].destination:
            raise OSError("diagnostic uncertain close")


def test_unconfirmed_close_cannot_return_complete_receipt(tmp_path):
    pair = CloseError(**arguments(tmp_path))
    pair.__enter__()
    pair.close_parent_writers()
    with pytest.raises(OutputCleanupError):
        pair.finish()
    output = pair.observations()[0]
    assert output.terminal and not output.resources_closed
    assert "close" in output.failure_kinds and output.file_sha256 is None
    assert pair._streams[0].destination.closed  # fault fixture avoids real leak
    with pytest.raises(OutputCleanupError):
        pair.__exit__(None, None, None)


@pytest.mark.parametrize("paths", [("relative", "stderr"), ("stdout", "stdout")])
def test_invalid_output_paths_denied_without_acquisition(tmp_path, paths):
    values = arguments(tmp_path)
    values["stdout_path"] = (tmp_path / paths[0] if paths[0] != "relative"
                              else type(tmp_path)("relative"))
    values["stderr_path"] = tmp_path / paths[1]
    with pytest.raises(ValueError):
        BoundedOutputPair(**values)
    assert list(tmp_path.iterdir()) == []


class WriterCloseError(BoundedOutputPair):
    def __init__(self, **values):
        super().__init__(**values)
        self.terminal_observation_attempted = False

    def _close_resource(self, resource):
        super()._close_resource(resource)
        if resource is self._streams[0].writer:
            raise OSError("diagnostic uncertain parent writer close")

    def _observe_terminal(self, deadline):
        self.terminal_observation_attempted = True
        return super()._observe_terminal(deadline)


def test_exit_writer_close_fault_still_observes_pumps_without_new_allowance(tmp_path):
    pair = WriterCloseError(**arguments(tmp_path))
    pair.__enter__()
    try:
        with pytest.raises(OutputCleanupError):
            pair.__exit__(None, None, None)
        assert pair.terminal_observation_attempted
        assert all(item.terminal for item in pair.observations())
        assert "close" in pair.observations()[0].failure_kinds
        assert "cleanup_deadline" not in pair.observations()[0].failure_kinds
    finally:
        # Diagnostic closes the real writer before raising; drain original pumps.
        for stream in pair._streams:
            stream.thread.join(2)
            assert not stream.thread.is_alive()


class PartialWriterCloseError(WriterCloseError):
    def _make_pipe(self):
        if self._streams[0].reader is not None:
            raise OSError("diagnostic second pipe acquisition failure")
        return super()._make_pipe()


def test_partial_entry_writer_fault_still_closes_proven_parent_resources(tmp_path):
    pair = PartialWriterCloseError(**arguments(tmp_path))
    try:
        with pytest.raises(OutputCleanupError) as caught:
            pair.__enter__()
        assert pair.terminal_observation_attempted
        assert all(item.terminal for item in pair.observations())
        assert isinstance(caught.value.__cause__, OSError)
        assert "acquire" in pair.observations()[1].failure_kinds
        assert all("cleanup_deadline" not in item.failure_kinds for item in pair.observations())
    finally:
        # No thread was started in this acquisition fixture. The fixture can
        # therefore safely close resources if pre-fix cleanup omitted them.
        for stream in pair._streams:
            assert stream.thread is None
            for resource in (stream.reader, stream.destination, stream.writer):
                if resource is not None and not resource.closed:
                    resource.close()


def test_late_parent_writer_closure_cannot_fit_earlier_cleanup_bound(tmp_path):
    pair = ReadError(**arguments(tmp_path))
    pair.__enter__()
    try:
        for stream in pair._streams:
            stream.thread.join(2)
            assert not stream.thread.is_alive()
        assert all(item.terminal for item in pair.observations())
        earlier = max(item.finished_monotonic_ns for item in pair.observations())
        # This pinned Windows Python can return the same monotonic clock tick
        # for successive operations. Observe a later tick, bounded by 1 second,
        # rather than pretending that subtraction establishes actual ordering.
        tick_deadline = time.perf_counter() + 1
        tick_wait = threading.Event()
        while time.monotonic_ns() <= earlier:
            assert time.perf_counter() < tick_deadline, "monotonic tick did not advance"
            tick_wait.wait(0.001)
        pair.close_parent_writers()  # confirmation occurs AFTER the effective bound
        with pytest.raises(OutputCleanupError):
            pair.finish(earlier)
    finally:
        pair.close_parent_writers()
        if pair._finish_failed:
            with pytest.raises(OutputCleanupError):
                pair.__exit__(None, None, None)
        else:
            pair.__exit__(None, None, None)


def test_late_observation_accepts_all_actual_closures_within_bound(tmp_path):
    with ReadError(**arguments(tmp_path)) as pair:
        for stream in pair._streams:
            stream.thread.join(2)
            assert not stream.thread.is_alive()
        pair.close_parent_writers()
        earlier = time.monotonic_ns()
        receipt = pair.finish(earlier)
        assert not receipt.valid
        assert all(item.terminal and item.resources_closed
                   for item in (receipt.stdout, receipt.stderr))


class ClosedReaderError:
    def __init__(self, reader):
        self.reader = reader

    def close(self):
        self.reader.close()
        raise OSError("diagnostic reader rollback uncertainty")


class PipeWrapError(BoundedOutputPair):
    def _pipe_stream(self, descriptor, mode):
        if mode == "wb":
            self.writer_descriptor = descriptor
            raise OSError("diagnostic writer wrapping failure")
        self.reader_stream = super()._pipe_stream(descriptor, mode)
        return ClosedReaderError(self.reader_stream)


def test_pipe_rollback_closes_other_owned_end_even_when_reader_close_raises(tmp_path):
    pair = PipeWrapError(**arguments(tmp_path))
    try:
        with pytest.raises(OSError, match="reader rollback"):
            pair._make_pipe()
        assert pair.reader_stream.closed
        with pytest.raises(OSError):
            os.fstat(pair.writer_descriptor)
    finally:
        # The diagnostic owns this never-transferred raw fd, so pre-fix leakage
        # can be closed safely without touching any pump's in-flight resource.
        try:
            os.fstat(pair.writer_descriptor)
        except OSError:
            pass
        else:
            os.close(pair.writer_descriptor)
    assert list(tmp_path.iterdir()) == []


def test_pipe_rollback_uncertainty_is_not_complete_public_entry_cleanup(tmp_path):
    pair = PipeWrapError(**arguments(tmp_path))
    with pytest.raises(OutputCleanupError) as caught:
        pair.__enter__()
    assert isinstance(caught.value.__cause__, OSError)
    assert pair.reader_stream.closed
    with pytest.raises(OSError):
        os.fstat(pair.writer_descriptor)
    output = pair.observations()[0]
    assert output.terminal and not output.resources_closed
    assert "acquire" in output.failure_kinds and "close" in output.failure_kinds
