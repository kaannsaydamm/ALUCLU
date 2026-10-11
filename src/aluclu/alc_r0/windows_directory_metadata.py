"""Single-route Windows directory metadata for installed-tree continuity.

Integrated into Windows directory walks, not scientific execution. Resolved-path
validation and observation are non-atomic on a cooperating host. Native ticks
and identifiers are exact observations, not provenance or activation authority.
Blocking OS calls require the outer owned job's original deadline.
"""
from __future__ import annotations

import ctypes
import os
import stat
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

from .runtime_tree_inventory import RuntimeInventoryError, _deadline


class _NativeBasic(ctypes.Structure):
    # CPython3.12.13 FILE_STAT_BASIC_INFORMATION, fixed class3, Windows64.
    _fields_ = [(n,ctypes.c_int64) for n in (
        'FileId','CreationTime','LastAccessTime','LastWriteTime','ChangeTime',
        'AllocationSize','EndOfFile')] + [(n,ctypes.c_uint32) for n in (
        'FileAttributes','ReparseTag','NumberOfLinks','DeviceType',
        'DeviceCharacteristics','Reserved')] + [
        ('VolumeSerialNumber',ctypes.c_int64),('FileId128',ctypes.c_ubyte*16)]


@dataclass(frozen=True, slots=True)
class DirectoryObservation:
    mode: int
    volume_serial: int
    file_id128: str
    size: int
    write_ticks: int
    creation_ticks: int
    link_count: int
    attributes: int
    change_ticks: int
    allocation_size: int
    legacy_file_id: int
    device_type: int
    device_characteristics: int
    reparse_tag: int


def _decode(record):
    if type(record) is not bytes or len(record)!=104 or ctypes.sizeof(_NativeBasic)!=104:
        raise RuntimeInventoryError('exact native directory record required')
    raw=_NativeBasic.from_buffer_copy(record)
    identity=bytes(raw.FileId128)
    if (not raw.FileAttributes & 16 or raw.FileAttributes & 0x400 or raw.ReparseTag
            or raw.NumberOfLinks==0 or identity==bytes(16)
            or any(value<0 for value in (raw.EndOfFile,raw.AllocationSize,
                raw.CreationTime,raw.LastWriteTime,raw.ChangeTime))):
        raise RuntimeInventoryError('invalid native directory metadata')
    # All dirs synthesize execute bits, independent of pathname extensions.
    mode=stat.S_IFDIR | (0o555 if raw.FileAttributes & 1 else 0o777)
    return DirectoryObservation(mode,raw.VolumeSerialNumber & (2**64-1),
        identity.hex(),raw.EndOfFile,raw.LastWriteTime,raw.CreationTime,
        raw.NumberOfLinks,raw.FileAttributes,raw.ChangeTime,raw.AllocationSize,
        raw.FileId & (2**64-1),raw.DeviceType,raw.DeviceCharacteristics,raw.ReparseTag)


def _validated_path(path,deadline):
    _deadline(deadline)
    if not isinstance(path,Path):
        raise RuntimeInventoryError('exact absolute local directory path required')
    label=str(path)
    if (len(label)>32767 or '\0' in label or not path.is_absolute()
            or len(path.drive)!=2 or path.drive[1]!=':'):
        raise RuntimeInventoryError('bounded absolute local directory path required')
    try:
        if len(label.encode('utf-8'))>32768:
            raise RuntimeInventoryError('bounded absolute local directory path required')
        _deadline(deadline)
        resolved=path.resolve(strict=True)
        _deadline(deadline)
        if resolved!=path:
            raise RuntimeInventoryError('resolved non-alias directory path required')
        metadata=path.lstat()
        _deadline(deadline)
        if (not stat.S_ISDIR(metadata.st_mode)
                or getattr(metadata,'st_file_attributes',0)&0x400):
            raise RuntimeInventoryError('regular directory path required')
    except (OSError,UnicodeError) as exc:
        raise RuntimeInventoryError('directory path observation unavailable') from exc
    return label


def observe_directory(path: Path, *, deadline_ns: int) -> DirectoryObservation:
    """One system by-name query, exact raw metadata, no fallback or acceptance."""
    if type(deadline_ns) is not int or not 0<deadline_ns<(1<<63):
        raise RuntimeInventoryError('invalid original runtime deadline')
    _deadline(deadline_ns)
    if os.name!='nt' or struct.calcsize('P')!=8 or sys.byteorder!='little':
        raise RuntimeInventoryError('Windows64 little-endian native directory required')
    label=_validated_path(path,deadline_ns)
    _deadline(deadline_ns)
    import _ctypes
    try:
        library=ctypes.WinDLL('api-ms-win-core-file-l2-1-4.dll',
                             use_last_error=True,winmode=0x800)
    except OSError as exc:
        raise RuntimeInventoryError('native directory API unavailable') from exc
    try:
        _deadline(deadline_ns)
        query=library.GetFileInformationByName
        query.argtypes=[ctypes.c_wchar_p,ctypes.c_int32,ctypes.c_void_p,ctypes.c_uint32]
        query.restype=ctypes.c_int32
        raw=_NativeBasic()
        if ctypes.sizeof(raw)!=104:
            raise RuntimeInventoryError('native directory ABI unavailable')
        _deadline(deadline_ns)
        succeeded=query(label,3,ctypes.byref(raw),104)
        _deadline(deadline_ns)
        if not succeeded:
            raise RuntimeInventoryError('native directory query failed')
        record=bytes(raw)
    except AttributeError as exc:
        raise RuntimeInventoryError('native directory API unavailable') from exc
    finally:
        try:
            _ctypes.FreeLibrary(library._handle)
        except OSError as exc:
            raise RuntimeInventoryError('native directory library release failed') from exc
    _deadline(deadline_ns)
    result=_decode(record)
    _deadline(deadline_ns)
    return result
