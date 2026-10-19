"""Shared original-deadline exclusion, NOT operator provenance or admission.

Nonblocking lock probes cannot interrupt filesystem OS calls or the user body.
Cooperating namespace must remain present; no hostile replacement/ABA guarantee.
"""
from contextlib import contextmanager
import errno
import os
import threading
import time

from aluclu.cognition import persistence as _p
from .fixed_d_request_file import _local_path, _ancestors
from .runtime_tree_inventory import _fingerprint, _kind, _same_open_identity

_OWNED = threading.local()
_MAX = 2**63-1


class DeadlineLockError(ValueError):
    """Unsafe/unobserved lock identity; no successful exclusion result."""


def _deadline(end):
    if type(end) is not int or not 0 < end <= _MAX:
        raise DeadlineLockError('exact positive original deadline required')
    if time.monotonic_ns() >= end:
        raise TimeoutError('original lock deadline expired')


def _pause(end):
    _deadline(end)
    time.sleep(max(0,min(20_000_000,end-time.monotonic_ns()))/1e9)


@contextmanager
def _thread_lock(lock,end):
    acquired=False
    try:
        while not acquired:
            _deadline(end)
            acquired=lock.acquire(blocking=False)
            if not acquired: _pause(end)
        _deadline(end)
        yield
    finally:
        if acquired: lock.release()


def _registry(path,end):
    key=os.path.normcase(os.path.normpath(str(path)))
    with _thread_lock(_p._PROCESS_PATH_LOCKS_GUARD,end):
        entry=_p._PROCESS_PATH_LOCKS.get(key)
        if entry is None:
            entry=_p._ProcessPathLock()
            _p._PROCESS_PATH_LOCKS[key]=entry
        return key,entry  # strong reference held by waiting/owning caller


def _metadata(value,empty=False):
    if (_kind(value)!='file' or value.st_nlink!=1
            or value.st_size not in ((0,1) if empty else (1,))):
        raise DeadlineLockError('regular single-link one-byte lock required')
    return _fingerprint(value)


def _validate(path,stream,ancestors,end):
    _deadline(end)
    before=_metadata(path.lstat())
    opened=_metadata(os.fstat(stream.fileno()))
    if not _same_open_identity(before,opened):
        raise DeadlineLockError('lock path/open identity differs')
    _deadline(end)
    stream.seek(0)
    if stream.read(2)!=b'\0': raise DeadlineLockError('exact NUL lock byte required')
    _deadline(end)
    if (_metadata(os.fstat(stream.fileno()))!=opened
            or _metadata(path.lstat())!=before or _ancestors(path,end)!=ancestors):
        raise DeadlineLockError('lock namespace or open file changed')
    _deadline(end)


def _native(stream,unlock=False):
    if os.name=='nt':
        import msvcrt
        msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK if unlock else msvcrt.LK_NBLCK,1)
    else:
        import fcntl
        fcntl.flock(stream.fileno(),fcntl.LOCK_UN if unlock else fcntl.LOCK_EX|fcntl.LOCK_NB)


@contextmanager
def deadline_file_lock(path,deadline_ns):
    """Acquire shared exclusion before original deadline; never resets it.

    Legacy-only outer nesting rejects; validated bounded nesting reuses its
    retained handle. Bounded outer->legacy inner shares existing held marker.
    """
    _deadline(deadline_ns)
    path=_local_path(path)
    ancestors=_ancestors(path,deadline_ns)
    if path.resolve(strict=False)!=path: raise DeadlineLockError('lock alias rejected')
    key,entry=_registry(path,deadline_ns)
    with _thread_lock(entry.lock,deadline_ns):
        held=_p._held_process_paths()
        owned=getattr(_OWNED,'paths',None)
        if key in held:
            if owned is None or key not in owned:
                raise DeadlineLockError('legacy outer has no validated retained handle')
            stream,original_ancestors=owned[key]
            if ancestors!=original_ancestors: raise DeadlineLockError('nested namespace differs')
            _validate(path,stream,original_ancestors,deadline_ns)
            yield
            return
        original=None
        try: original=_metadata(path.lstat(),empty=True)
        except FileNotFoundError: pass
        _deadline(deadline_ns)
        with path.open('a+b',buffering=0) as stream:
            native=False
            try:
                _deadline(deadline_ns)
                opened=_metadata(os.fstat(stream.fileno()),empty=True)
                if original is not None and not _same_open_identity(original,opened):
                    raise DeadlineLockError('lock changed before open')
                while not native:
                    _deadline(deadline_ns)
                    stream.seek(0)  # seek errors are NOT native lock contention
                    try:
                        _native(stream)
                        native=True
                    except OSError as error:
                        if error.errno not in (errno.EACCES,errno.EAGAIN): raise
                        _pause(deadline_ns)
                _deadline(deadline_ns)
                if os.fstat(stream.fileno()).st_size==0:
                    if stream.write(b'\0')!=1: raise DeadlineLockError('lock initialization incomplete')
                    _deadline(deadline_ns)
                    stream.flush(); os.fsync(stream.fileno())
                    _deadline(deadline_ns)
                _validate(path,stream,ancestors,deadline_ns)
                if owned is None:
                    owned={}; _OWNED.paths=owned
                owned[key]=(stream,ancestors)
                held.add(key)
                _deadline(deadline_ns)
                yield
            finally:
                try:
                    if native:
                        stream.seek(0)
                        _native(stream,unlock=True)
                finally:
                    # Only this root path acquisition owns these marker entries.
                    if owned is not None: owned.pop(key,None)
                    held.discard(key)
                    if not held and hasattr(_p._HELD_PROCESS_PATHS,'paths'):
                        del _p._HELD_PROCESS_PATHS.paths
                    if owned is not None and not owned and hasattr(_OWNED,'paths'):
                        del _OWNED.paths
