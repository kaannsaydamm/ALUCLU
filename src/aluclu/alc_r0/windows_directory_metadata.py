"""Standard-first Windows directory metadata for installed-tree continuity.

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
from contextlib import ExitStack, contextmanager
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


def _decode_standard(record):
    if type(record) is not bytes or len(record) != 24:
        raise RuntimeInventoryError('exact standard directory record required')
    allocation, size, links, pending, directory = struct.unpack('<qqIBB2x', record)
    if allocation < 0 or size < 0 or not links or pending != 0 or directory != 1:
        raise RuntimeInventoryError('invalid standard directory metadata')
    return allocation, size, links


class _Win32DirectoryAPI:
    """Fixed synchronous Win32 contracts; outer owned job bounds blocking calls."""

    def __init__(self, deadline, loader=None, release=None):
        self.deadline, self.loader, self.release = deadline, loader, release

    def _release_library(self, handle):
        try:
            # _ctypes.FreeLibrary returns None on success and raises on failure;
            # an explicitly injected release may instead report False.
            if self.release(handle) is False:
                raise RuntimeInventoryError('native directory library release failed')
        except OSError as exc:
            raise RuntimeInventoryError('native directory library release failed') from exc

    def __enter__(self):
        if (self.loader is None) != (self.release is None):
            raise RuntimeInventoryError('paired directory loader/release required')
        _deadline(self.deadline)
        if self.loader is None:
            import _ctypes
            self.loader, self.release = ctypes.WinDLL, _ctypes.FreeLibrary
        self.stack = ExitStack()
        try:
            def load(name):
                _deadline(self.deadline)
                library = self.loader(name, use_last_error=True, winmode=0x800)
                self.stack.callback(self._release_library, library._handle)
                _deadline(self.deadline)
                return library
            named = load('api-ms-win-core-file-l2-1-4.dll')
            kernel = load('kernel32.dll')
            self.query_named = named.GetFileInformationByName
            self.query_named.argtypes = [ctypes.c_wchar_p, ctypes.c_int32,
                ctypes.c_void_p, ctypes.c_uint32]
            self.query_named.restype = ctypes.c_int32
            self.create = kernel.CreateFileW
            self.create.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
                ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
            self.create.restype = ctypes.c_void_p
            self.close = kernel.CloseHandle
            self.close.argtypes = [ctypes.c_void_p]
            self.close.restype = ctypes.c_int32
            self.extended = kernel.GetFileInformationByHandleEx
            self.extended.argtypes = [ctypes.c_void_p, ctypes.c_int32,
                ctypes.c_void_p, ctypes.c_uint32]
            self.extended.restype = ctypes.c_int32
            return self
        except (OSError, AttributeError) as exc:
            self.stack.close()
            raise RuntimeInventoryError('native directory API unavailable') from exc
        except BaseException:
            self.stack.close()
            raise

    def __exit__(self, *exception):
        # No deadline check may prevent releasing acquired libraries.
        self.stack.close()

    @contextmanager
    def open(self, label):
        _deadline(self.deadline)
        handle = self.create(label, 0x80, 7, None, 3, 0x02200000, None)
        if handle in (None, 0, ctypes.c_void_p(-1).value):
            raise RuntimeInventoryError('native directory open failed')
        try:
            _deadline(self.deadline)
            yield handle
        finally:
            if not self.close(handle):
                raise RuntimeInventoryError('native directory handle close failed')

    def _query_extended(self, handle, info_class):
        _deadline(self.deadline)
        value = ctypes.create_string_buffer(24)
        succeeded = self.extended(handle, info_class, ctypes.byref(value), 24)
        _deadline(self.deadline)
        if not succeeded:
            raise RuntimeInventoryError('native directory handle query failed')
        # BOOL success, not an exact returned-byte count.
        return bytes(value)

    def standard(self, handle):
        return self._query_extended(handle, 1)

    def identity(self, handle):
        return self._query_extended(handle, 18)

    def named(self, label):
        _deadline(self.deadline)
        raw = _NativeBasic()
        if ctypes.sizeof(raw) != 104:
            raise RuntimeInventoryError('native directory ABI unavailable')
        succeeded = self.query_named(label, 3, ctypes.byref(raw), 104)
        _deadline(self.deadline)
        if not succeeded:
            raise RuntimeInventoryError('native directory query failed')
        return bytes(raw)


def _observe_composite(api, label, deadline):
    _deadline(deadline)
    with api.open(label) as handle:
        standard = _decode_standard(api.standard(handle))
        _deadline(deadline)
        first = _decode(api.named(label))
        _deadline(deadline)
        if standard != (first.allocation_size, first.size, first.link_count):
            raise RuntimeInventoryError('standard directory disagreement')
        identity = api.identity(handle)
        _deadline(deadline)
        if type(identity) is not bytes or len(identity) != 24:
            raise RuntimeInventoryError('exact directory handle identity required')
        volume, identifier = struct.unpack('<Q16s', identity)
        if identifier == bytes(16) or (volume, identifier.hex()) != (
                first.volume_serial, first.file_id128):
            raise RuntimeInventoryError('directory handle identity disagreement')
        second = _decode(api.named(label))
        _deadline(deadline)
        if first != second:
            raise RuntimeInventoryError('directory named bookend changed')
    _deadline(deadline)
    final = _decode(api.named(label))
    _deadline(deadline)
    if first != final:
        raise RuntimeInventoryError('directory after-close bookend changed')
    return first


def observe_directory(path: Path, *, deadline_ns: int) -> DirectoryObservation:
    """Compound standard-first/full-named observations, not atomic path binding."""
    if type(deadline_ns) is not int or not 0 < deadline_ns < (1 << 63):
        raise RuntimeInventoryError('invalid original runtime deadline')
    _deadline(deadline_ns)
    if os.name != 'nt' or struct.calcsize('P') != 8 or sys.byteorder != 'little':
        raise RuntimeInventoryError('Windows64 little-endian native directory required')
    label = _validated_path(path, deadline_ns)
    with _Win32DirectoryAPI(deadline_ns) as api:
        result = _observe_composite(api, label, deadline_ns)
    _deadline(deadline_ns)
    return result
