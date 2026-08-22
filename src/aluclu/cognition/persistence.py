from __future__ import annotations

import os
import threading
import uuid
import weakref
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .contracts import PersistenceError, UnsafePathError

_WINDOWS_REPARSE_POINT = 0x400


class _ProcessPathLock:
    __slots__ = ("lock", "__weakref__")

    def __init__(self) -> None:
        self.lock = threading.RLock()


_PROCESS_PATH_LOCKS_GUARD = threading.Lock()
_PROCESS_PATH_LOCKS: weakref.WeakValueDictionary[str, _ProcessPathLock] = (
    weakref.WeakValueDictionary()
)
_HELD_PROCESS_PATHS = threading.local()


def resolve_ledger_path(path: str | Path) -> Path:
    candidate = Path(path)
    _reject_windows_aliases(candidate)
    resolved_parent = _safe_existing_parent(candidate)
    resolved = (resolved_parent / candidate.name).resolve(strict=False)
    if _is_link_or_reparse(candidate):
        raise UnsafePathError(f"unsafe link/reparse path: {candidate}")
    return resolved


def atomic_write_bytes(path: str | Path, data: bytes) -> None:
    if type(data) is not bytes:
        raise TypeError("data must be bytes")
    target = resolve_ledger_path(path)
    if _is_link_or_reparse(target):
        raise UnsafePathError(f"unsafe link/reparse path: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(f".{target.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        with temp.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if _is_link_or_reparse(target):
            raise UnsafePathError(f"unsafe link/reparse path: {target}")
        if os.name == "nt":
            _windows_replace_write_through(temp, target)
        else:
            os.replace(temp, target)
            _fsync_directory(target.parent)
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


@contextmanager
def exclusive_file_lock(path: str | Path) -> Iterator[None]:
    lock_path = resolve_ledger_path(path)
    if _is_link_or_reparse(lock_path):
        raise UnsafePathError(f"unsafe link/reparse path: {lock_path}")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_key, process_lock = _process_path_lock(lock_path)
    with process_lock.lock:
        held_paths = _held_process_paths()
        if lock_key in held_paths:
            yield
            return
        held_paths.add(lock_key)
        try:
            with lock_path.open("a+b", buffering=0) as handle:
                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    handle.write(b"\0")
                    handle.flush()
                    os.fsync(handle.fileno())
                handle.seek(0)
                try:
                    if os.name == "nt":
                        import msvcrt

                        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                    else:
                        import fcntl

                        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                except OSError as exc:
                    raise PersistenceError(
                        f"exclusive file lock is unavailable: {lock_path}"
                    ) from exc
                try:
                    yield
                finally:
                    handle.seek(0)
                    if os.name == "nt":
                        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            held_paths.remove(lock_key)
            if not held_paths:
                del _HELD_PROCESS_PATHS.paths


def _process_path_lock(path: Path) -> tuple[str, _ProcessPathLock]:
    key = os.path.normcase(os.path.normpath(str(path)))
    with _PROCESS_PATH_LOCKS_GUARD:
        process_lock = _PROCESS_PATH_LOCKS.get(key)
        if process_lock is None:
            process_lock = _ProcessPathLock()
            _PROCESS_PATH_LOCKS[key] = process_lock
    return key, process_lock


def _held_process_paths() -> set[str]:
    paths = getattr(_HELD_PROCESS_PATHS, "paths", None)
    if paths is None:
        paths = set()
        _HELD_PROCESS_PATHS.paths = paths
    return paths


def _safe_existing_parent(path: Path) -> Path:
    parent = path if path.exists() and path.is_dir() else path.parent
    probe = parent if parent != Path("") else Path.cwd()
    existing: list[Path] = []
    while not probe.exists():
        if probe == probe.parent:
            break
        probe = probe.parent
    for candidate in probe.resolve(strict=True).parents:
        existing.append(candidate)
    existing.append(probe)
    for candidate in existing:
        if _is_link_or_reparse(candidate):
            raise UnsafePathError(f"unsafe link/reparse parent: {candidate}")
    return parent.resolve(strict=False)


def _reject_windows_aliases(path: Path) -> None:
    if os.name != "nt":
        return
    for part in path.parts:
        if part.endswith(".") or part.endswith(" "):
            raise UnsafePathError("Windows trailing dot/space aliases are unsafe")


def _is_link_or_reparse(path: Path) -> bool:
    try:
        stat = path.lstat()
    except FileNotFoundError:
        return False
    if path.is_symlink():
        return True
    return bool(getattr(stat, "st_file_attributes", 0) & _WINDOWS_REPARSE_POINT)


def _windows_replace_write_through(source: Path, target: Path) -> None:
    import ctypes

    flags = 0x1 | 0x8
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    if not kernel32.MoveFileExW(str(source), str(target), flags):
        error = ctypes.get_last_error()
        raise OSError(error, "MoveFileExW failed", str(target))


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
