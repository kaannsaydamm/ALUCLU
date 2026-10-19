"""Finite installed-file evidence inside an externally owned deadline boundary.

Not a native-module closure, authenticated provenance, immutable snapshot or
launch permit. Filesystem continuity assumes a cooperating host. Blocking OS
calls require the outer owned job's original deadline; Python checks alone do not
interrupt them. Existing regular hardlinks are allowed and counted logically.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import time
from dataclasses import asdict, dataclass
from itertools import chain
from pathlib import Path

from .canonical import CanonicalEvidenceError, canonical_json_bytes, normalize_evidence_path

_CHUNK = 65536
_MAX = (1 << 63) - 1


class RuntimeInventoryError(ValueError):
    """Installed component cannot support a complete bounded inventory."""


@dataclass(frozen=True, slots=True)
class RuntimeTreeBounds:
    entry_count: int
    path_bytes: int
    file_bytes: int
    total_file_bytes: int

    def __post_init__(self):
        for value, minimum, maximum in (
            (self.entry_count,1,65536), (self.path_bytes,1,4*1024**2),
            (self.file_bytes,0,4*1024**3), (self.total_file_bytes,0,16*1024**3),
        ):
            if type(value) is not int or not minimum <= value <= maximum:
                raise RuntimeInventoryError('invalid runtime inventory bound')


@dataclass(frozen=True, slots=True)
class RuntimeTreeEvidence:
    component: str
    absolute_root: str
    inventory_sha256: str
    entry_count: int
    file_count: int
    logical_file_bytes: int


def _deadline(deadline):
    if time.monotonic_ns() >= deadline:
        raise RuntimeInventoryError('original runtime inventory deadline expired')


def _fingerprint(metadata):
    return (metadata.st_mode,metadata.st_dev,metadata.st_ino,metadata.st_size,
            metadata.st_mtime_ns,metadata.st_ctime_ns,metadata.st_nlink,
            getattr(metadata,'st_file_attributes',0))


def _kind(metadata):
    if stat.S_ISLNK(metadata.st_mode) or getattr(metadata,'st_file_attributes',0) & 0x400:
        raise RuntimeInventoryError('symlink or reparse point in runtime tree')
    if stat.S_ISDIR(metadata.st_mode): return 'directory'
    if stat.S_ISREG(metadata.st_mode): return 'file'
    raise RuntimeInventoryError('nonregular runtime tree entry')


def _same_open_identity(path_fingerprint, opened_fingerprint):
    # On Windows Python 3.12, path stat's legacy ctime may be creation time,
    # while fstat reports change time. Keep each observation's full timestamp
    # for same-source continuity; compare all other fields across sources.
    if os.name != 'nt':
        return path_fingerprint == opened_fingerprint
    # CPython Windows path stat synthesizes all execute bits from extensions;
    # fstat has no pathname. Accept only that directed 0111 -> 0 difference.
    path_mode, opened_mode = path_fingerprint[0], opened_fingerprint[0]
    if path_mode != opened_mode and not (
            path_mode & 0o111 == 0o111 and opened_mode & 0o111 == 0
            and path_mode & ~0o111 == opened_mode):
        return False
    return (path_fingerprint[1:5] + path_fingerprint[6:] ==
            opened_fingerprint[1:5] + opened_fingerprint[6:])


def _directory_metadata(path, metadata, deadline):
    if os.name != 'nt':
        return _fingerprint(metadata)
    # Late import avoids initialization cycle with the observer's deadline/error helpers.
    from .windows_directory_metadata import observe_directory
    observed=observe_directory(path,deadline_ns=deadline)
    if not stat.S_ISDIR(observed.mode) or observed.attributes & 0x400:
        raise RuntimeInventoryError('native directory classification differs')
    return observed


def _walk(root, bounds, deadline):
    _deadline(deadline)
    root_stat = root.lstat()
    if _kind(root_stat) != 'directory':
        raise RuntimeInventoryError('runtime root must be a directory')
    nodes = {'': ('directory', _directory_metadata(root,root_stat,deadline))}
    pending, folded = [''], set()
    path_bytes = total = files = 0
    while pending:
        _deadline(deadline)
        relative = pending.pop()
        with os.scandir(root / relative) as iterator:
            for entry in iterator:
                _deadline(deadline)
                # Bound even empty directories before retaining or descending.
                if len(nodes) >= bounds.entry_count:
                    raise RuntimeInventoryError('runtime entry count exceeds bound')
                path = relative + '/' + entry.name if relative else entry.name
                try:
                    normalize_evidence_path(path)
                    length = len(path.encode('utf-8'))
                except (CanonicalEvidenceError,UnicodeError) as exc:
                    raise RuntimeInventoryError('unsafe runtime inventory path') from exc
                if path_bytes + length > bounds.path_bytes:
                    raise RuntimeInventoryError('runtime path bytes exceed bound')
                if path.casefold() in folded:
                    raise RuntimeInventoryError('duplicate runtime inventory path')
                # Windows DirEntry.stat omits identity fields; use full lstat.
                metadata = (root / path).lstat()
                kind = _kind(metadata)
                if kind == 'file':
                    if metadata.st_size < 0 or metadata.st_size > bounds.file_bytes:
                        raise RuntimeInventoryError('runtime file size exceeds bound')
                    if total + metadata.st_size > bounds.total_file_bytes:
                        raise RuntimeInventoryError('runtime logical bytes exceed bound')
                    total += metadata.st_size
                    files += 1
                else:
                    pending.append(path)
                retained=(_fingerprint(metadata) if kind=='file' else
                          _directory_metadata(root/path,metadata,deadline))
                nodes[path] = (kind,retained)
                folded.add(path.casefold())
                path_bytes += length
    _deadline(deadline)
    return nodes, files, total


def _hash_file(path, fingerprint, deadline):
    _deadline(deadline)
    if _fingerprint(path.lstat()) != fingerprint:
        raise RuntimeInventoryError('runtime file changed before opening')
    size, received, digest = fingerprint[3], 0, hashlib.sha256()
    with path.open('rb',buffering=0) as stream:
        opened = os.fstat(stream.fileno())
        opened_fingerprint = _fingerprint(opened)
        if _kind(opened) != 'file' or not _same_open_identity(fingerprint, opened_fingerprint):
            raise RuntimeInventoryError('runtime open-file identity differs')
        while True:
            _deadline(deadline)
            chunk = stream.read(min(_CHUNK,size-received+1))
            _deadline(deadline)
            if not chunk: break
            received += len(chunk)
            if received > size:
                raise RuntimeInventoryError('runtime file grew during inspection')
            digest.update(chunk)
        if received != size or _fingerprint(os.fstat(stream.fileno())) != opened_fingerprint:
            raise RuntimeInventoryError('runtime file changed while reading')
    if _fingerprint(path.lstat()) != fingerprint:
        raise RuntimeInventoryError('runtime file changed after reading')
    _deadline(deadline)
    return digest.hexdigest()


def _diagnostic_metadata(fingerprint):
    from .windows_directory_metadata import DirectoryObservation
    if type(fingerprint) is DirectoryObservation:
        return 'windows-directory-by-name-v1',asdict(fingerprint),asdict(fingerprint)
    if type(fingerprint) is tuple and len(fingerprint)==8:
        fields=('mode','device','inode','size','mtime_ns','ctime_ns','nlink','attributes')
        return 'python-stat-v1',dict(zip(fields,fingerprint)),fingerprint
    raise RuntimeInventoryError('unknown runtime metadata observation schema')


def _tree_change_message(component, before, after, deadline):
    """Bounded explanation from already bounded trees; never weaken refusal."""
    _deadline(deadline)
    first = None
    for path in chain(before,after):
        _deadline(deadline)
        if before.get(path) != after.get(path) and (first is None or path < first):
            first = path
    if first is None:
        return 'runtime tree changed during inspection'
    old, new = before.get(first), after.get(first)
    old_kind, old_fp = old if old is not None else (None,None)
    new_kind, new_fp = new if new is not None else (None,None)
    old_schema,old_fields,old_payload=(_diagnostic_metadata(old_fp) if old else (None,None,None))
    new_schema,new_fields,new_payload=(_diagnostic_metadata(new_fp) if new else (None,None,None))
    if old is None or new is None:
        differing = ['membership']
    else:
        differing = ['kind'] if old_kind != new_kind else []
        if old_schema!=new_schema:
            differing.append('observation_schema')
        else:
            differing += [name for name,value in old_fields.items() if value != new_fields[name]]
    encoded = first.encode('utf-8')
    detail = dict(component=component,path_prefix=first[:128],
        path_sha256=hashlib.sha256(encoded).hexdigest(),path_utf8_bytes=len(encoded),
        path_truncated=len(first)>128,before_kind=old_kind,after_kind=new_kind,
        differing_fields=differing,before=old_payload,after=new_payload)
    if 'windows-directory-by-name-v1' in (old_schema,new_schema):
        detail.update(before_schema=old_schema,after_schema=new_schema)
    message = 'runtime tree changed during inspection: ' + json.dumps(
        detail,ensure_ascii=True,separators=(',',':'))
    _deadline(deadline)
    return message


def inspect_runtime_tree(root: Path, *, component: str, deadline_ns: int,
                         bounds: RuntimeTreeBounds) -> RuntimeTreeEvidence:
    """Hash one explicitly selected component inside an owned deadline boundary.

    Root counts as one node but has no canonical relative-path row/path charge.
    Hardlink aliases count separately. The absolute root/component are bindings
    in the result, not a trusted choice of interpreter/import/DLL resolution.
    No installed environment, source authorization or training consent is inferred.
    """
    if type(bounds) is not RuntimeTreeBounds:
        raise RuntimeInventoryError('exact runtime tree bounds required')
    RuntimeTreeBounds.__post_init__(bounds)
    if type(component) is not str or component not in ('python-base','python-venv'):
        raise RuntimeInventoryError('unknown runtime component')
    if type(deadline_ns) is not int or not 0 < deadline_ns <= _MAX:
        raise RuntimeInventoryError('invalid original deadline')
    _deadline(deadline_ns)
    if not isinstance(root,Path) or not root.is_absolute():
        raise RuntimeInventoryError('absolute resolved runtime root required')
    try:
        if _kind(root.lstat()) != 'directory' or root.resolve(strict=True) != root:
            raise RuntimeInventoryError('absolute resolved directory root required')
        nodes, files, total = _walk(root,bounds,deadline_ns)
        if not files:
            raise RuntimeInventoryError('runtime component has no regular files')
        rows = []
        for relative in sorted((p for p in nodes if p),key=lambda p:p.encode('utf-8')):
            _deadline(deadline_ns)
            kind, fingerprint = nodes[relative]
            digest = _hash_file(root/relative,fingerprint,deadline_ns) if kind == 'file' else None
            rows.append(dict(path=relative,kind=kind,
                byte_length=fingerprint[3] if kind == 'file' else 0,sha256=digest))
        after, after_files, after_total = _walk(root,bounds,deadline_ns)
        if (after,after_files,after_total) != (nodes,files,total):
            raise RuntimeInventoryError(_tree_change_message(component,nodes,after,deadline_ns))
        _deadline(deadline_ns)
        digest = hashlib.sha256(canonical_json_bytes(rows)).hexdigest()
        _deadline(deadline_ns)
        return RuntimeTreeEvidence(component,root.as_posix(),digest,len(nodes),files,total)
    except OSError as exc:
        raise RuntimeInventoryError('runtime filesystem observation failed') from exc
