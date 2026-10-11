from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import FrozenInstanceError, replace

import pytest

from aluclu.alc_r0.attempt_journal import (
    AttemptJournal,
    JournalConflict,
    JournalError,
    JournalHead,
)

ROOT = "a" * 64


def journal(tmp_path):
    return AttemptJournal(tmp_path / "attempts.jsonl", ROOT)


def test_explicit_create_restart_and_frozen_head(tmp_path):
    store = journal(tmp_path)
    head = store.create()
    assert head.count == head.byte_length == 0
    next_head = store.append(head, b'{"state":"INTENT"}')
    fresh = journal(tmp_path)
    snapshot = fresh.read(next_head)
    assert snapshot.head == next_head
    assert snapshot.events == (b'{"state":"INTENT"}',)
    with pytest.raises(FrozenInstanceError):
        head.count = 8
    with pytest.raises(FileExistsError):
        fresh.create()


def test_compare_and_append_stale_head_is_not_automatically_retried(tmp_path):
    store = journal(tmp_path)
    old = store.create()
    current = store.append(old, b'{"state":"INVALID"}')
    before = store.path.read_bytes()
    with pytest.raises(JournalConflict):
        store.append(old, b'{"state":"PASS"}')
    assert store.path.read_bytes() == before
    assert store.read(current).events == (b'{"state":"INVALID"}',)


@pytest.mark.parametrize("data", [b"{}", b"\n", b'{"a":1}\n', b"\xff\n"])
def test_corrupt_or_truncated_tail_never_repaired(tmp_path, data):
    store = journal(tmp_path)
    head = store.append(store.create(), b'{"state":"INTENT"}')
    with store.path.open("ab") as handle:
        handle.write(data)
    before = store.path.read_bytes()
    with pytest.raises(JournalError):
        store.read(head)
    with pytest.raises(JournalError):
        store.append(head, b"{}")
    assert store.path.read_bytes() == before


def test_rollback_and_cross_identity_rejected(tmp_path):
    store = journal(tmp_path)
    old = store.create()
    head = store.append(old, b'{"n":1}')
    saved = store.path.read_bytes()
    store.path.write_bytes(b"")
    with pytest.raises(JournalConflict):
        store.read(head)
    store.path.write_bytes(saved)
    with pytest.raises(JournalError):
        AttemptJournal(store.path, "b" * 64).read(head)


@pytest.mark.parametrize(
    "event",
    [
        b"",
        b"[]",
        b'{"a":1,"a":2}',
        b'{ "a":1}',
        b"{}\n",
        b'{"x":NaN}',
        b"x" * 8193,
        "{}",
    ],
)
def test_event_rejected_before_write(tmp_path, event):
    store = journal(tmp_path)
    head = store.create()
    with pytest.raises(JournalError):
        store.append(head, event)
    assert store.path.read_bytes() == b""


@pytest.mark.parametrize(
    "changes",
    [
        {"count": True},
        {"count": -1},
        {"byte_length": 1.0},
        {"digest": "x"},
        {"count": 65537},
    ],
)
def test_malformed_heads_rejected(tmp_path, changes):
    store = journal(tmp_path)
    head = store.create()
    with pytest.raises(JournalError):
        store.read(replace(head, **changes))


def test_fsync_failure_never_returns_acknowledged_head(tmp_path, monkeypatch):
    store = journal(tmp_path)
    head = store.create()
    import aluclu.alc_r0.attempt_journal as implementation

    def fail_sync(_fd):
        raise OSError("injected fsync failure")

    monkeypatch.setattr(implementation.os, "fsync", fail_sync)
    with pytest.raises(OSError, match="injected fsync"):
        store.append(head, b'{"state":"INTENT"}')
    # Bytes may have reached the OS. No new head was acknowledged; old owner
    # must not launch/retry as if the operation had no side effect.
    with pytest.raises(JournalConflict):
        store.read(head)


def test_two_process_writers_only_one_acknowledges_same_head(tmp_path):
    store = journal(tmp_path)
    head = store.create()
    child = """
import sys
from pathlib import Path
from aluclu.alc_r0.attempt_journal import AttemptJournal, JournalHead, JournalConflict
store = AttemptJournal(Path(sys.argv[1]), sys.argv[2])
head = JournalHead(0, 0, sys.argv[3])
try:
    store.append(head, b'{"state":"INTENT"}')
except JournalConflict:
    sys.exit(3)
"""
    processes = []
    try:
        for _ in range(2):
            processes.append(
                subprocess.Popen(
                    [
                        sys.executable,
                        "-B",
                        "-c",
                        child,
                        str(store.path),
                        ROOT,
                        head.digest,
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            )
        outcomes = []
        for process in processes:
            stdout, stderr = process.communicate(timeout=60)
            assert not stdout
            assert not stderr, stderr.decode(errors="replace")
            outcomes.append(process.returncode)
        assert sorted(outcomes) == [0, 3]
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=10)
    line = store.path.read_bytes()
    current = JournalHead(
        1, len(line), hashlib.sha256(b"ALC-R0-JOURNAL-RECORD-V1\0" + line).hexdigest()
    )
    assert len(store.read(current).events) == 1


def test_existing_empty_file_not_reinitialized(tmp_path):
    store = journal(tmp_path)
    store.path.touch()
    with pytest.raises(FileExistsError):
        store.create()


def test_missing_journal_read_does_not_create_journal(tmp_path):
    store = journal(tmp_path)
    head = JournalHead(0, 0, "a" * 64)
    with pytest.raises(FileNotFoundError):
        store.read(head)
    assert not store.path.exists()


def test_full_head_identity_includes_byte_length(tmp_path):
    store = journal(tmp_path)
    head = store.append(store.create(), b"{}")
    with pytest.raises(JournalConflict):
        store.read(replace(head, byte_length=head.byte_length + 1))


def test_record_mutation_and_reordering_fail_chain(tmp_path):
    store = journal(tmp_path)
    first = store.append(store.create(), b'{"n":1}')
    final = store.append(first, b'{"n":2}')
    before = store.path.read_bytes()
    store.path.write_bytes(before.replace(b'"n":1', b'"n":3'))
    with pytest.raises(JournalError):
        store.read(final)
    store.path.write_bytes(b"".join(reversed(before.splitlines(keepends=True))))
    with pytest.raises(JournalError):
        store.read(final)


def test_oversized_sparse_file_rejected_before_record_allocation(tmp_path):
    store = journal(tmp_path)
    head = store.create()
    with store.path.open("r+b") as handle:
        handle.seek(32 * (1 << 20))
        handle.write(b"x")
    with pytest.raises(JournalError, match="byte ceiling"):
        store.read(head)


def test_oversized_record_rejected(tmp_path):
    store = journal(tmp_path)
    head = store.create()
    store.path.write_bytes(b"x" * 16385 + b"\n")
    with pytest.raises(JournalError, match="framing"):
        store.read(head)


def test_append_count_limit_fails_without_write(tmp_path):
    store = journal(tmp_path)
    head = store.create()
    with pytest.raises(JournalError, match="append ceiling"):
        store.append(replace(head, count=65536), b"{}")
    assert store.path.read_bytes() == b""


def test_hardlink_alias_rejected(tmp_path):
    store = journal(tmp_path)
    head = store.create()
    alias = tmp_path / "alias.jsonl"
    os.link(store.path, alias)
    with pytest.raises(JournalError, match="single-link"):
        store.append(head, b"{}")
    assert alias.read_bytes() == b""


@pytest.mark.parametrize("root", [None, "A" * 64, "x" * 64, "a" * 63, True])
def test_invalid_identity_rejected(tmp_path, root):
    with pytest.raises(JournalError):
        AttemptJournal(tmp_path / "attempts.jsonl", root)


@pytest.mark.parametrize("name", ["nul", "a:b", "trailing.", "trailing "])
def test_unsafe_filename_rejected(tmp_path, name):
    with pytest.raises(JournalError):
        AttemptJournal(tmp_path / name, ROOT)


def test_relative_path_rejected():
    from pathlib import Path

    with pytest.raises(JournalError):
        AttemptJournal(Path("attempts.jsonl"), ROOT)


def test_thread_writers_compare_same_head(tmp_path):
    store = journal(tmp_path)
    head = store.create()

    def write(_index):
        try:
            store.append(head, b"{}")
            return "ack"
        except JournalConflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(write, range(8)))
    assert outcomes.count("ack") == 1
    assert outcomes.count("conflict") == 7


def test_acknowledgement_after_fsync_with_complete_record(tmp_path, monkeypatch):
    store = journal(tmp_path)
    head = store.create()
    original = os.fsync
    seen = []

    def verify_sync(fd):
        assert store.path.read_bytes().endswith(b"\n")
        seen.append(fd)
        original(fd)

    monkeypatch.setattr(os, "fsync", verify_sync)
    new = store.append(head, b'{"state":"INTENT"}')
    assert len(seen) == 1
    assert store.read(new).events == (b'{"state":"INTENT"}',)


def test_nonregular_directory_rejected_before_open(tmp_path):
    store = journal(tmp_path)
    head = store.create()
    store.path.unlink()
    store.path.mkdir()
    with pytest.raises(JournalError, match="regular"):
        store.read(head)


@pytest.mark.skipif(os.name != "posix", reason="native POSIX FIFO unavailable")
def test_posix_fifo_rejected_without_opening_other_end(tmp_path):
    store = journal(tmp_path)
    head = store.create()
    store.path.unlink()
    os.mkfifo(store.path)
    # No other end is opened. Correct pre-open check must reject immediately.
    with pytest.raises(JournalError, match="regular"):
        store.read(head)


@pytest.mark.parametrize("remove_lock", [False, True])
def test_controlled_interleaving_detects_lock_removal(
    tmp_path, monkeypatch, remove_lock
):
    import aluclu.alc_r0.attempt_journal as implementation

    store = journal(tmp_path)
    head = store.create()
    original_scan = AttemptJournal._scan
    first_scanned = threading.Event()
    second_scanned = threading.Event()
    release_first = threading.Event()
    outcomes = []

    def controlled_scan(self, handle):
        snapshot = original_scan(self, handle)
        if threading.current_thread().name == "journal-first":
            first_scanned.set()
            if not release_first.wait(10):
                raise AssertionError("controlled scan release missing")
        else:
            second_scanned.set()
        return snapshot

    @contextmanager
    def missing_lock(_path):
        yield

    def writer():
        try:
            store.append(head, b"{}")
            outcomes.append("ack")
        except JournalConflict:
            outcomes.append("conflict")
        except BaseException as exc:
            outcomes.append(exc)

    monkeypatch.setattr(AttemptJournal, "_scan", controlled_scan)
    if remove_lock:
        monkeypatch.setattr(implementation, "exclusive_file_lock", missing_lock)
    first = threading.Thread(target=writer, name="journal-first")
    second = threading.Thread(target=writer, name="journal-second")
    first.start()
    try:
        assert first_scanned.wait(10)
        second.start()
        if remove_lock:
            assert second_scanned.wait(10), (
                "no-lock mutant did not reach competing scan"
            )
            second.join(timeout=10)
            assert not second.is_alive()
        else:
            assert not second_scanned.wait(0.25), "competing scan escaped lock"
    finally:
        release_first.set()
        first.join(timeout=10)
        if second.ident is not None:
            second.join(timeout=10)
    assert not first.is_alive() and not second.is_alive()
    if remove_lock:
        assert outcomes == ["ack", "ack"]
        assert store.path.read_bytes().count(b"\n") == 2
        # Mutant acknowledged duplicate sequence1: the controlled fixture
        # demonstrates why serialization is a correctness requirement.
        with pytest.raises(JournalError, match="sequence"):
            store.read(head)
    else:
        assert sorted(outcomes) == ["ack", "conflict"]
        assert store.path.read_bytes().count(b"\n") == 1
