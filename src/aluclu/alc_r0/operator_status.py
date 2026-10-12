"""Bounded local status observation, not installation provenance or permission."""
from dataclasses import dataclass
import os

from .canonical import sha256_bytes
from .fixed_d_wire import _bounded_json, _string_end, _hash, _integer
from .fixed_d_request_file import _local_path, _ancestors, _check_deadline, _read_bytes
from .runtime_tree_inventory import _fingerprint, _kind, _same_open_identity

LIMIT = 4096


class OperatorStatusError(ValueError):
    """Invalid or unobserved status, never an accepting default."""


@dataclass(frozen=True, slots=True)
class OperatorStatus:
    data: bytes
    root: str
    installation_root: str
    generation_root: str
    sequence: int
    revoked: bool
    expires_utc_ns: int


def _bounds(data):
    if type(data) is not bytes or not 0 < len(data) <= LIMIT:
        raise OperatorStatusError('status bytes exceed bound')
    text = data.decode('utf-8', errors='strict')
    index, depth, tokens = 0, 0, 0
    while index < len(text):
        char = text[index]
        if char == '"':
            end = _string_end(text, index)
            if len(text[index+1:end-1].encode('utf-8')) > 256:
                raise OperatorStatusError('status string bound exceeded')
            index, tokens = end, tokens + 1
        elif char in '[{':
            depth, tokens, index = depth + 1, tokens + 1, index + 1
            if depth > 2: raise OperatorStatusError('status depth bound exceeded')
        elif char in ']}':
            depth, index = depth - 1, index + 1
            if depth < 0: raise OperatorStatusError('invalid status depth')
        elif char in ' ,:\t\r\n':
            index += 1
        else:
            tokens, index = tokens + 1, index + 1
            while index < len(text) and text[index] not in '\"[]{} ,:\t\r\n':
                index += 1
        if tokens > 64: raise OperatorStatusError('status token bound exceeded')
    if depth != 0: raise OperatorStatusError('unterminated status container')


def decode_operator_status(data: bytes) -> OperatorStatus:
    """Canonical typed observation; revoked/expiry are not authority decisions."""
    try:
        _bounds(data)
        value = _bounded_json(data, LIMIT)
        fields = {'schema','installation_root','generation_root','sequence','revoked','expires_utc_ns'}
        if type(value) is not dict or set(value) != fields:
            raise OperatorStatusError('exact status fields required')
        if value['schema'] != 'alc-r0-operator-status-v1' or type(value['revoked']) is not bool:
            raise OperatorStatusError('invalid status schema or revocation type')
        _hash(value['installation_root'])
        _hash(value['generation_root'])
        sequence = _integer(value['sequence'], 1)
        expiry = _integer(value['expires_utc_ns'], 1)
        return OperatorStatus(data,sha256_bytes(data),value['installation_root'],
                              value['generation_root'],sequence,value['revoked'],expiry)
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        if isinstance(exc, OperatorStatusError): raise
        raise OperatorStatusError('invalid canonical status') from exc


def _file(metadata):
    if _kind(metadata) != 'file' or metadata.st_nlink != 1 or not 1 <= metadata.st_size <= LIMIT:
        raise OperatorStatusError('bounded regular single-link status required')
    return _fingerprint(metadata)


def read_operator_status(path, *, deadline_ns: int) -> OperatorStatus:
    """One local read under caller-owned deadline; path does not prove origin."""
    if type(deadline_ns) is not int or not 1 <= deadline_ns <= 2**63-1:
        raise OperatorStatusError('invalid original status deadline')
    try:
        _check_deadline(deadline_ns)
        path = _local_path(path)
        ancestors = _ancestors(path, deadline_ns)
        if path.resolve(strict=True) != path:
            raise OperatorStatusError('unresolved status alias')
        _check_deadline(deadline_ns)
        original = _file(path.lstat())
        _check_deadline(deadline_ns)
        with path.open('rb',buffering=0) as stream:
            _check_deadline(deadline_ns)
            opened = _file(os.fstat(stream.fileno()))
            if not _same_open_identity(original,opened):
                raise OperatorStatusError('status open identity differs')
            data = _read_bytes(stream, original[3], deadline_ns)
            _check_deadline(deadline_ns)
            if _file(os.fstat(stream.fileno())) != opened:
                raise OperatorStatusError('open status changed')
        _check_deadline(deadline_ns)
        if _file(path.lstat()) != original or _ancestors(path,deadline_ns) != ancestors:
            raise OperatorStatusError('status path or ancestor changed')
        result = decode_operator_status(data)
        _check_deadline(deadline_ns)
        return result
    except (OSError,ValueError,TypeError,UnicodeError,RuntimeError) as exc:
        if isinstance(exc,OperatorStatusError): raise
        raise OperatorStatusError('status observation failed') from exc
