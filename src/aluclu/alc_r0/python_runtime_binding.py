"""Owned factual current-process labels and on-disk Python component bytes.

Not mapped-image authentication, native/import closure, immutable snapshot,
trusted producer or launch permission. Blocking filesystem calls require the
external owned job's original deadline. No model or package runtime is imported.
"""
from __future__ import annotations

import hashlib
import os
import stat
import struct
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from .canonical import canonical_json_bytes
from .runtime_tree_inventory import (
    RuntimeInventoryError, RuntimeTreeBounds, _deadline, _fingerprint, _hash_file,
    _kind, inspect_runtime_tree,
)

_ENV = ('PYTHONPATH','PYTHONHOME','PYTHONNOUSERSITE','PYTHONDONTWRITEBYTECODE',
    'HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_DATASETS_OFFLINE',
    'CUDA_VISIBLE_DEVICES','CUBLAS_WORKSPACE_CONFIG')
_FLAGS = ('isolated','ignore_environment','no_user_site','safe_path',
          'dont_write_bytecode','optimize')


@dataclass(frozen=True, slots=True)
class PythonRuntimeBinding:
    data: bytes
    sha256: str


def _text_bytes(value):
    if type(value) is not str or len(value)>32768 or '\0' in value:
        raise RuntimeInventoryError('invalid bounded runtime observation text')
    try:
        size=len(value.encode('utf-8'))
    except UnicodeError as exc:
        raise RuntimeInventoryError('invalid runtime observation encoding') from exc
    if size>32768:
        raise RuntimeInventoryError('runtime observation text exceeds bound')
    return size


def _snapshot(deadline):
    _deadline(deadline)
    used = 0

    def text(value):
        nonlocal used
        size=_text_bytes(value)
        if used+size>4*1024**2:
            raise RuntimeInventoryError('runtime observation text exceeds bound')
        used+=size
        return value

    if os.name!='nt' or sys.platform!='win32' or sys.implementation.name!='cpython':
        raise RuntimeInventoryError('Windows CPython runtime required')
    if struct.calcsize('P')!=8 or sys.byteorder!='little':
        raise RuntimeInventoryError('Windows 64-bit little-endian runtime required')
    observed={name:text(getattr(sys,attribute)) for name,attribute in (
        ('executable','executable'),('base_executable','_base_executable'),
        ('prefix','prefix'),('exec_prefix','exec_prefix'),('base_prefix','base_prefix'),
        ('base_exec_prefix','base_exec_prefix'),('version','version'))}
    observed.update(implementation=text(sys.implementation.name),
        cache_tag=text(sys.implementation.cache_tag),platform=text(sys.platform),
        pointer_bits='64',byteorder=text(sys.byteorder))
    flags={}
    for name in _FLAGS:
        value=getattr(sys.flags,name)
        expected=bool if name=='safe_path' else int
        if type(value) is not expected or (expected is int and not 0<=value<=2):
            raise RuntimeInventoryError('invalid runtime flag observation')
        flags[name]=value
    observed['flags']=flags
    if type(sys.path) is not list or len(sys.path)>256:
        raise RuntimeInventoryError('invalid runtime import path observation')
    observed['path']=[text(value) for value in sys.path]
    environment={}
    for name in _ENV:
        value=os.environ.get(name)
        environment[name]=None if value is None else text(value)
    observed['environment']=environment
    _deadline(deadline)
    return observed


def _path(value,kind):
    path=Path(value)
    if (not path.is_absolute() or path.resolve(strict=True)!=path
            or _kind(path.lstat())!=kind):
        raise RuntimeInventoryError('resolved regular runtime path required')
    return path


def _base_root(value):
    raw=Path(value)
    if not raw.is_absolute():
        raise RuntimeInventoryError('absolute current base prefix required')
    metadata=raw.lstat()
    if not getattr(metadata,'st_file_attributes',0)&0x400:
        return _path(value,'directory'),None
    if (not stat.S_ISDIR(metadata.st_mode)
            or getattr(metadata,'st_reparse_tag',0)!=0xA0000003
            or raw.parent.resolve(strict=True)!=raw.parent):
        raise RuntimeInventoryError('single current-base directory junction required')
    immediate=os.readlink(raw)
    _text_bytes(immediate)
    normalized=immediate[4:] if immediate.startswith('\\\\?\\') else immediate
    target=Path(normalized)
    if len(target.drive)!=2 or target.drive[1]!=':' or not target.is_absolute():
        raise RuntimeInventoryError('absolute local immediate junction target required')
    physical=_path(normalized,'directory')
    _text_bytes(physical.as_posix())
    if raw.resolve(strict=True)!=physical:
        raise RuntimeInventoryError('junction target differs from physical base')
    return physical,(raw,_fingerprint(metadata),immediate,physical)


def _alias_payload(alias):
    if alias is None:
        return None
    raw,_,immediate,physical=alias
    for value in (raw.as_posix(),immediate,physical.as_posix()):
        _text_bytes(value)
    return dict(absolute_path=raw.as_posix(),immediate_target=immediate,
                resolved_root=physical.as_posix(),reparse_tag=str(0xA0000003))


def _retained_text_bound(observed,components,files,alias):
    groups=([value for value in observed.values() if type(value) is str],
            observed['path'],[v for v in observed['environment'].values() if v is not None])
    used=len('alc-r0-current-python-runtime-v1')
    for values in (*groups,*(row.values() for row in components),
                   *(row.values() for row in files),() if alias is None else alias.values()):
        for value in values:
            used+=_text_bytes(value)
            if used>4*1024**2:
                raise RuntimeInventoryError('retained runtime text exceeds aggregate bound')


def _layout(observed):
    if (observed['prefix']!=observed['exec_prefix']
            or observed['base_prefix']!=observed['base_exec_prefix']):
        raise RuntimeInventoryError('runtime prefix relationships differ')
    base,alias=_base_root(observed['base_prefix'])
    venv=_path(observed['prefix'],'directory')
    if base==venv:
        raise RuntimeInventoryError('distinct virtual environment required')
    special=[]
    for role,value,root,cap in (
        ('venv-executable',observed['executable'],venv,16*1024**2),
        ('base-executable',observed['base_executable'],base,16*1024**2),
        ('venv-config',str(venv/'pyvenv.cfg'),venv,64*1024),
    ):
        if role=='base-executable' and alias is not None:
            raw=Path(value)
            if (not raw.is_absolute() or not raw.is_relative_to(alias[0])
                    or _kind(raw.lstat())!='file'):
                raise RuntimeInventoryError('base executable raw label outside base alias')
            path=_path(str(raw.resolve(strict=True)),'file')
        else:
            path=_path(value,'file')
        if not path.is_relative_to(root):
            raise RuntimeInventoryError('runtime file outside corresponding component')
        fingerprint=_fingerprint(path.lstat())
        if not 0<=fingerprint[3]<=cap:
            raise RuntimeInventoryError('runtime special file exceeds bound')
        special.append((role,path,fingerprint))
    return base,venv,special,alias


def inspect_current_python_runtime(*, deadline_ns: int,
                                   bounds: RuntimeTreeBounds) -> PythonRuntimeBinding:
    """Compose factual labels/settings and current disk bytes, not a permit.

    Exact current roots derive from sys, never from a worker request. Observed
    import labels/environment are not certified safe. Serial scans and metadata
    continuity assume a cooperating host; mapped/native bytes remain unproven.
    """
    if type(deadline_ns) is not int or not 0<deadline_ns<(1<<63):
        raise RuntimeInventoryError('invalid original runtime deadline')
    if type(bounds) is not RuntimeTreeBounds:
        raise RuntimeInventoryError('exact component bounds required')
    RuntimeTreeBounds.__post_init__(bounds)
    _deadline(deadline_ns)
    try:
        before=_snapshot(deadline_ns)
        base,venv,special,alias=_layout(before)
        files=[]
        for role,path,fingerprint in special:
            digest=_hash_file(path,fingerprint,deadline_ns)
            files.append(dict(role=role,absolute_path=path.as_posix(),
                byte_length=str(fingerprint[3]),sha256=digest))
        components=[]
        for root,component in ((base,'python-base'),(venv,'python-venv')):
            evidence=asdict(inspect_runtime_tree(root,component=component,
                deadline_ns=deadline_ns,bounds=bounds))
            for name in ('entry_count','file_count','logical_file_bytes'):
                evidence[name]=str(evidence[name])
            components.append(evidence)
        for _,path,fingerprint in special:
            _deadline(deadline_ns)
            if _fingerprint(path.lstat())!=fingerprint:
                raise RuntimeInventoryError('runtime special file changed across scans')
        _deadline(deadline_ns)
        if _base_root(before['base_prefix'])!=(base,alias):
            raise RuntimeInventoryError('current base alias changed across scans')
        if _snapshot(deadline_ns)!=before:
            raise RuntimeInventoryError('current runtime observations changed')
        _deadline(deadline_ns)
        alias_payload=_alias_payload(alias)
        _retained_text_bound(before,components,files,alias_payload)
        data=canonical_json_bytes(dict(schema='alc-r0-current-python-runtime-v1',
            observed=before,base_prefix_alias=alias_payload,
            components=components,special_files=files))
        _deadline(deadline_ns)
        result=PythonRuntimeBinding(data,hashlib.sha256(data).hexdigest())
        _deadline(deadline_ns)
        return result
    except (OSError,AttributeError) as exc:
        raise RuntimeInventoryError('current runtime observation unavailable') from exc
