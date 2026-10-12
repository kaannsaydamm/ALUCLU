"""Single-open fixed-D transport integrity on a cooperating filesystem.

Not authenticated producer provenance, adversarial ABA protection or a permit.
Blocking OS calls require the outer owned job's original deadline boundary.
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path

from .canonical import normalize_evidence_path, sha256_bytes
from .fixed_d_wire import REQUEST_LIMIT, DRequest, decode_d_request
from .runtime_tree_inventory import _fingerprint, _kind, _same_open_identity


class DRequestFileError(ValueError):
    """Request transport cannot be read with bounded continuity evidence."""


def _check_deadline(deadline):
    if time.monotonic_ns() >= deadline:
        raise DRequestFileError('original request read deadline expired')


def _local_path(value):
    if type(value) not in (str, type(Path())):
        raise DRequestFileError('exact str or concrete Path required')
    raw = str(value)
    if not raw or len(raw) > 4096 or len(raw.encode('utf-8')) > 4096:
        raise DRequestFileError('request path exceeds bound')
    spelling = raw.replace('\\', '/') if os.name == 'nt' else raw
    if spelling.startswith('//') or raw.startswith(('\\\\', '\\?\\', '\\.\\')):
        raise DRequestFileError('local ordinary path required')
    path = Path(raw)
    if not path.is_absolute():
        raise DRequestFileError('absolute request path required')
    relative = spelling[len(path.anchor):]
    parts = relative.split('/')
    if len(parts) > 255:
        raise DRequestFileError('request path component bound exceeded')
    # Apply portable ordinary component rules on both platforms, before any I/O.
    normalize_evidence_path(relative)
    return path


def _ancestors(path, deadline):
    result = []
    for parent in reversed(path.parents):
        _check_deadline(deadline)
        metadata = parent.lstat()
        if _kind(metadata) != 'directory':
            raise DRequestFileError('request ancestor must be ordinary directory')
        fingerprint = _fingerprint(metadata)
        result.append((parent, (fingerprint[0:3], fingerprint[7])))
    _check_deadline(deadline)
    return result


def _file(metadata):
    if _kind(metadata) != 'file' or metadata.st_nlink != 1:
        raise DRequestFileError('request must be regular single-link file')
    if not 1 <= metadata.st_size <= REQUEST_LIMIT:
        raise DRequestFileError('request byte size exceeds bound')
    return _fingerprint(metadata)


def _read_bytes(stream, size, deadline):
    # At most announced size + one sentinel, and never over REQUEST_LIMIT + 1.
    data = bytearray()
    while len(data) <= size:
        _check_deadline(deadline)
        allowance = size + 1 - len(data)
        chunk = stream.read(allowance)
        _check_deadline(deadline)
        if type(chunk) is not bytes or len(chunk) > allowance:
            raise DRequestFileError('invalid request read result')
        if not chunk:
            if len(data) != size:
                raise DRequestFileError('request truncated while reading')
            return bytes(data)
        data.extend(chunk)
    raise DRequestFileError('request grew while reading')


def _read_file(path, deadline):
    """Private I/O operation; public entry accepts no backend substitution."""
    _check_deadline(deadline)
    original = _file(path.lstat())
    _check_deadline(deadline)
    with path.open('rb', buffering=0) as stream:
        _check_deadline(deadline)
        opened = _file(os.fstat(stream.fileno()))
        if not _same_open_identity(original, opened):
            raise DRequestFileError('request open identity differs')
        data = _read_bytes(stream, original[3], deadline)
        _check_deadline(deadline)
        if _file(os.fstat(stream.fileno())) != opened:
            raise DRequestFileError('open request changed while reading')
    _check_deadline(deadline)
    if _file(path.lstat()) != original:
        raise DRequestFileError('request path changed while reading')
    _check_deadline(deadline)
    return data


def read_d_request_file(path, *, expected_root: str, deadline_ns: int) -> DRequest:
    """Read once under the original deadline; supplied hash is not authority."""
    if type(expected_root) is not str or re.fullmatch('[0-9a-f]{64}', expected_root) is None:
        raise DRequestFileError('invalid expected request root')
    if type(deadline_ns) is not int or not 1 <= deadline_ns <= 2**63 - 1:
        raise DRequestFileError('invalid original request read deadline')
    _check_deadline(deadline_ns)
    try:
        path = _local_path(path)
        ancestors = _ancestors(path, deadline_ns)
        if path.resolve(strict=True) != path:
            raise DRequestFileError('request path is an unresolved alias')
        _check_deadline(deadline_ns)
        data = _read_file(path, deadline_ns)
        if _ancestors(path, deadline_ns) != ancestors:
            raise DRequestFileError('request ancestor identity changed')
        _check_deadline(deadline_ns)
        if sha256_bytes(data) != expected_root:
            raise DRequestFileError('request byte root differs')
        _check_deadline(deadline_ns)
        request = decode_d_request(data)
        _check_deadline(deadline_ns)
        return request
    except (OSError, ValueError, UnicodeError, RuntimeError) as exc:
        if isinstance(exc, DRequestFileError):
            raise
        raise DRequestFileError('request file validation failed') from exc
