import os
from pathlib import Path

import pytest

from aluclu.cognition import PersistenceError, UnsafePathError
from aluclu.cognition.persistence import (
    atomic_write_bytes,
    exclusive_file_lock,
    resolve_ledger_path,
)


def test_resolved_relative_path_does_not_follow_later_chdir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    monkeypatch.chdir(first)

    resolved = resolve_ledger_path(Path("memory.sqlite3"))

    monkeypatch.chdir(second)
    assert resolved == (first / "memory.sqlite3").resolve()


def test_resolve_existing_directory_does_not_duplicate_its_name(tmp_path: Path) -> None:
    root = tmp_path / "record-keys"
    root.mkdir()

    assert resolve_ledger_path(root) == root.resolve()


@pytest.mark.skipif(os.name != "nt", reason="Win32 alias rule")
@pytest.mark.parametrize("name", ["memory.sqlite3.", "memory.sqlite3 "])
def test_windows_trailing_dot_or_space_path_fails_closed(
    tmp_path: Path,
    name: str,
) -> None:
    with pytest.raises(UnsafePathError):
        resolve_ledger_path(tmp_path / name)


def test_resolve_ledger_path_rejects_existing_symlink(tmp_path: Path) -> None:
    target = tmp_path / "target.sqlite3"
    link = tmp_path / "link.sqlite3"
    target.write_bytes(b"")
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are unavailable on this platform")

    with pytest.raises(UnsafePathError):
        resolve_ledger_path(link)


def test_resolve_ledger_path_rejects_symlink_parent(tmp_path: Path) -> None:
    target = tmp_path / "target"
    link = tmp_path / "link"
    target.mkdir()
    try:
        link.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlinks are unavailable on this platform")

    with pytest.raises(UnsafePathError):
        resolve_ledger_path(link / "memory.sqlite3")


def test_resolve_ledger_path_rejects_deep_path_below_symlink_parent(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target"
    nested = target / "nested"
    link = tmp_path / "link"
    nested.mkdir(parents=True)
    try:
        link.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlinks are unavailable on this platform")

    with pytest.raises(UnsafePathError):
        resolve_ledger_path(link / "nested" / "memory.sqlite3")


def test_atomic_write_bytes_rejects_symlink_target(tmp_path: Path) -> None:
    target = tmp_path / "target.bin"
    link = tmp_path / "link.bin"
    target.write_bytes(b"old")
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are unavailable on this platform")

    with pytest.raises(UnsafePathError):
        atomic_write_bytes(link, b"new")
    assert target.read_bytes() == b"old"


def test_atomic_write_bytes_replaces_bytes_durably(tmp_path: Path) -> None:
    path = tmp_path / "state.bin"

    atomic_write_bytes(path, b"one")
    atomic_write_bytes(path, b"two")

    assert path.read_bytes() == b"two"


def test_exclusive_file_lock_creates_lock_file(tmp_path: Path) -> None:
    path = tmp_path / "ledger.lock"

    with exclusive_file_lock(path):
        assert path.exists()
        assert path.stat().st_size >= 1


def test_exclusive_file_lock_is_reentrant_for_the_same_thread(tmp_path: Path) -> None:
    path = tmp_path / "ledger.lock"

    with exclusive_file_lock(path):
        with exclusive_file_lock(path):
            assert path.exists()


@pytest.mark.skipif(os.name != "nt", reason="Win32 lock error translation")
def test_exclusive_file_lock_translates_windows_acquisition_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import msvcrt

    def fail_lock(_fd: int, mode: int, _size: int) -> None:
        assert mode == msvcrt.LK_LOCK
        raise OSError(36, "simulated lock timeout")

    monkeypatch.setattr(msvcrt, "locking", fail_lock)

    with pytest.raises(PersistenceError, match="exclusive file lock is unavailable"):
        with exclusive_file_lock(tmp_path / "ledger.lock"):
            pytest.fail("the lock body must not run")
