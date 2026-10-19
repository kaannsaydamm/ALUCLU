"""Isolated diagnostic only; never installed binding or training admission."""
import json
import os
import ctypes
import stat
import struct
import sys
import tempfile
import hashlib
import time
from dataclasses import asdict
from contextlib import ExitStack, contextmanager
from pathlib import Path


def decode(stat_record, identity_record, device_record):
    for record, length in zip((stat_record, identity_record, device_record), (72, 24, 8)):
        if type(record) is not bytes or len(record) != length:
            raise ValueError('exact same-handle record required')
    (legacy, creation, access, write, change, allocation, size,
        attributes, reparse, links, effective) = struct.unpack('<7q4I', stat_record)
    volume, identity = struct.unpack('<Q16s', identity_record)
    device, characteristics = struct.unpack('<II', device_record)
    if (not attributes & 16 or attributes & 0x400 or reparse or not links
            or identity == bytes(16)
            or any(value < 0 for value in (creation, write, change, allocation, size))):
        raise ValueError('invalid same-handle directory metadata')
    return dict(fields=dict(mode=stat.S_IFDIR | (0o555 if attributes & 1 else 0o777),
        volume_serial=volume, file_id128=identity.hex(), size=size,
        write_ticks=write, creation_ticks=creation, link_count=links,
        attributes=attributes, change_ticks=change, allocation_size=allocation,
        legacy_file_id=legacy & (2**64-1), device_type=device,
        device_characteristics=characteristics, reparse_tag=reparse),
        raw=dict(stat=stat_record.hex(), identity=identity_record.hex(), device=device_record.hex()))


class StatusUnion(ctypes.Union):
    _fields_ = [('status', ctypes.c_int32), ('pointer', ctypes.c_void_p)]


class IOStatus(ctypes.Structure):
    _anonymous_ = ('completion',)
    _fields_ = [('completion', StatusUnion), ('information', ctypes.c_size_t)]


def nt_record(query, handle, size, info_class, fatal):
    if (struct.calcsize('P') != 8 or ctypes.sizeof(IOStatus) != 16
            or IOStatus.information.offset != 8
            or (size, info_class) not in ((72, 68), (8, 4), (24, 5))):
        raise ValueError('exact same-handle query ABI required')
    value = ctypes.create_string_buffer(size)
    iosb = IOStatus()
    status = query(handle, ctypes.byref(iosb), ctypes.byref(value), size, info_class)
    if status & 0xffffffff == 259:
        # Actual caller's fatal exits this isolated process before locals unwind.
        fatal()
        raise RuntimeError('non-returning pending fatal returned')
    if status != 0 or iosb.information != size:
        raise ValueError(f'nonexact native query completion: status={status & 0xffffffff:08x}, bytes={iosb.information}')
    return dict(record=bytes(value), status=status,
        iosb_status=iosb.status & 0xffffffff, information=iosb.information)


def sample(api, handle):
    first = api.stat(handle)
    identity = api.identity(handle)
    device = api.device(handle)
    last = api.stat(handle)
    result = decode(first['record'], identity, device['record'])
    final = decode(last['record'], identity, device['record'])
    if result['fields'] != final['fields']:
        raise ValueError('same-handle stat bookend changed')
    def receipt(value):
        return dict(status=value['status'], iosb_status=value['iosb_status'],
            information=value['information'])
    result.update(nt_stat=receipt(first), nt_device=receipt(device),
        stat_bookend=dict(record_hex=last['record'].hex(), **receipt(last)))
    return result


def pending_exit():
    try:
        os.write(2, b'alc-r0 native query pending; isolated exit71\n')
    finally:
        os._exit(71)


class NativeAPI:
    def __init__(self, loader=None, release=None):
        self.loader, self.release = loader, release

    def __enter__(self):
        if os.name != 'nt' or struct.calcsize('P') != 8 or sys.byteorder != 'little':
            raise ValueError('Windows64 little-endian diagnostic required')
        if (self.loader is None) != (self.release is None):
            raise ValueError('paired loader/release required')
        if self.loader is None:
            import _ctypes
            self.loader, self.release = ctypes.WinDLL, _ctypes.FreeLibrary
        self.stack = ExitStack()
        try:
            def load(name):
                library = self.loader(name, use_last_error=True, winmode=0x800)
                self.stack.callback(self.release, library._handle)
                return library
            named = load('api-ms-win-core-file-l2-1-4.dll')
            kernel = load('kernel32.dll')
            native = load('ntdll.dll')
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
            self.query_stat = native.NtQueryInformationFile
            self.query_device = native.NtQueryVolumeInformationFile
            for query in (self.query_stat, self.query_device):
                query.argtypes = [ctypes.c_void_p, ctypes.POINTER(IOStatus),
                    ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int32]
                query.restype = ctypes.c_int32
            return self
        except BaseException:
            self.stack.close()
            raise

    def __exit__(self, *exception):
        self.stack.close()

    @contextmanager
    def open(self, path, access=0x80):
        if type(access) is not int or access not in (0x80, 0x81):
            raise ValueError('closed diagnostic access required')
        handle = self.create(str(path), access, 7, None, 3, 0x02200000, None)
        if handle in (None, 0, ctypes.c_void_p(-1).value):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            yield handle
        finally:
            if not self.close(handle):
                raise ctypes.WinError(ctypes.get_last_error())

    def stat(self, handle):
        return nt_record(self.query_stat, handle, 72, 68, pending_exit)

    def standard(self, handle):
        return nt_record(self.query_stat, handle, 24, 5, pending_exit)

    def standard_win32(self, handle):
        value = ctypes.create_string_buffer(24)
        if not self.extended(handle, 1, ctypes.byref(value), 24):
            raise ctypes.WinError(ctypes.get_last_error())
        # This API reports BOOL success, not a returned byte count.
        return dict(record=bytes(value), win32_succeeded=True,
            buffer_bytes=24, info_class=1)

    def device(self, handle):
        return nt_record(self.query_device, handle, 8, 4, pending_exit)

    def identity(self, handle):
        value = ctypes.create_string_buffer(24)
        if not self.extended(handle, 18, ctypes.byref(value), 24):
            raise ctypes.WinError(ctypes.get_last_error())
        return bytes(value)

    def named(self, path):
        value = ctypes.create_string_buffer(104)
        if not self.query_named(str(path), 3, ctypes.byref(value), 104):
            raise ctypes.WinError(ctypes.get_last_error())
        raw = bytes(value)
        fields = decode(raw[:68] + bytes(4), raw[80:104], raw[68:76])['fields']
        return dict(fields=fields, native_record_hex=raw.hex())


def bounded_names(path):
    names, length = [], 0
    with os.scandir(path) as entries:
        for entry in entries:
            length += len(entry.name.encode('utf-8'))
            if len(names) >= 256 or length > 32768:
                raise ValueError('directory enumeration bound exceeded')
            names.append(entry.name)
    encoded = json.dumps(sorted(names), ensure_ascii=True, separators=(',', ':')).encode()
    return dict(count=len(names), name_bytes=length, names_sha256=hashlib.sha256(encoded).hexdigest())


def inspect(path, api, enumerate_fn=bounded_names):
    if (not isinstance(path, Path) or not path.is_absolute() or '\0' in str(path)
            or len(str(path).encode('utf-8')) > 32768
            or path.resolve(strict=True) != path):
        raise ValueError('resolved bounded absolute directory required')
    metadata = path.lstat()
    if (not stat.S_ISDIR(metadata.st_mode)
            or getattr(metadata, 'st_file_attributes', 0) & 0x400
            or (os.name == 'nt' and (len(path.drive) != 2 or path.drive[1] != ':'))):
        raise ValueError('regular local directory required')
    named = [api.named(path)]
    handles = []
    with api.open(path) as handle:
        handles.append(sample(api, handle))
        named.append(api.named(path))
        enumeration = enumerate_fn(path)
        handles.append(sample(api, handle))
        named.append(api.named(path))
        handles.append(sample(api, handle))
    named.append(api.named(path))
    differences = []
    for named_index, handle_index in ((0, 0), (1, 0), (2, 1), (3, 2)):
        left, right = named[named_index]['fields'], handles[handle_index]['fields']
        differences.append(sorted(key for key in left if left[key] != right[key]))
    return dict(path=str(path), named_samples=named, handle_samples=handles,
        enumeration=enumeration, cross_route_differences=differences,
        named_stable=all(item['fields'] == named[0]['fields'] for item in named),
        handle_stable=all(item['fields'] == handles[0]['fields'] for item in handles))


def inspect_library(path, observe, enumerate_fn=bounded_names, *, deadline_ns,
                    clock=time.monotonic_ns):
    """Finite public-observer continuity, not full-runtime acceptance."""
    from aluclu.alc_r0.windows_directory_metadata import DirectoryObservation
    if type(deadline_ns) is not int or not 0 < deadline_ns < 2**63:
        raise ValueError('invalid original candidate deadline')

    def check():
        if clock() >= deadline_ns:
            raise ValueError('original candidate deadline expired')

    def observation():
        check()
        result = observe(path, deadline_ns=deadline_ns)
        check()
        if type(result) is not DirectoryObservation:
            raise ValueError('exact public directory observation required')
        return asdict(result)

    first = observation()
    check()
    enumeration = enumerate_fn(path)
    check()
    observations = [first]
    for _ in range(2):
        current = observation()
        if current != first:
            raise ValueError('public directory observation changed')
        observations.append(current)
    return dict(path=str(path), observations=observations,
                enumeration=enumeration, stable=True)


def owned_native_library():
    # -I ignores PYTHONPATH/script-directory imports. Only this reviewed checkout
    # is inserted explicitly; no caller-supplied source or discovery fallback.
    source_root = Path(__file__).resolve().parents[1] / 'src'
    sys.path.insert(0, str(source_root))
    from aluclu.alc_r0.windows_directory_metadata import observe_directory
    deadline = time.monotonic_ns() + 45_000_000_000
    root = Path.cwd().resolve(strict=True)
    scratch = root / 'control-16'
    scratch.mkdir()
    for index in range(16):
        with (scratch / f'sample-{index:03d}.bin').open('xb') as output:
            output.write(b'x' * 512)
    installed = (Path(sys.base_prefix) / 'Lib' / 'asyncio').resolve(strict=True)
    cases = [inspect_library(path, observe_directory, deadline_ns=deadline)
             for path in (installed, scratch)]
    if cases[1]['enumeration']['count'] != 16:
        raise ValueError('owned control membership differs')
    print(json.dumps(dict(schema='alc-r0-public-directory-candidate-v1',
        python=sys.version, executable=sys.executable, base_prefix=sys.base_prefix,
        scope='finite-readonly-installed-and-owned-scratch', scratch_root=str(root),
        logical_written_bytes=8192, cases=cases), sort_keys=True, separators=(',', ':')))


def owned_native():
    root = Path.cwd()
    scratch = root / 'control-16'
    scratch.mkdir()
    for index in range(16):
        with (scratch / f'sample-{index:03d}.bin').open('xb') as output:
            output.write(b'x' * 512)
    installed = Path(sys.base_prefix).resolve(strict=True) / 'Lib' / 'asyncio'
    with NativeAPI() as api:
        cases = [inspect(installed, api), inspect(scratch, api)]
    print(json.dumps(dict(schema='alc-r0-same-handle-directory-v1', python=sys.version,
        scope='finite-readonly-installed-and-owned-scratch', scratch_root=str(root),
        logical_written_bytes=8192, cases=cases), sort_keys=True, separators=(',', ':')))


def inspect_access(path, api, enumerate_fn=bounded_names):
    if (not isinstance(path, Path) or not path.is_absolute() or '\0' in str(path)
            or len(str(path).encode('utf-8')) > 32768
            or path.resolve(strict=True) != path):
        raise ValueError('resolved bounded absolute directory required')
    metadata = path.lstat()
    if (not stat.S_ISDIR(metadata.st_mode)
            or getattr(metadata, 'st_file_attributes', 0) & 0x400
            or (os.name == 'nt' and (len(path.drive) != 2 or path.drive[1] != ':'))):
        raise ValueError('regular local directory required')
    before = api.named(path)
    stages = []
    with api.open(path, access=0x80) as baseline:
        def mark(stage, second=None):
            stages.append(dict(stage=stage, baseline=sample(api, baseline),
                second_handle=None if second is None else sample(api, second),
                named=api.named(path)))
        mark('baseline')
        with api.open(path, access=0x80) as second:
            mark('attributes-open', second)
        mark('attributes-closed')
        with api.open(path, access=0x81) as second:
            mark('list-access-open', second)
        mark('list-access-closed')
        enumeration = enumerate_fn(path)
        mark('enumerated')
    after = api.named(path)
    def adjacent(observations):
        return [sorted(key for key in left['fields']
            if left['fields'][key] != right['fields'][key])
            for left, right in zip(observations, observations[1:])]
    return dict(path=str(path), before=before, stages=stages, after=after,
        enumeration=enumeration,
        named_adjacent_differences=adjacent([before, *[s['named'] for s in stages], after]),
        baseline_adjacent_differences=adjacent([s['baseline'] for s in stages]))


def decode_standard(record):
    if type(record) is not bytes or len(record) != 24:
        raise ValueError('exact standard directory record required')
    allocation, size, links, pending, directory = struct.unpack('<qqIBB2x', record)
    if allocation < 0 or size < 0 or not links or pending != 0 or directory != 1:
        raise ValueError('invalid standard directory metadata')
    return dict(fields=dict(allocation_size=allocation, size=size,
        link_count=links, delete_pending=False, directory=True), raw_hex=record.hex())


def inspect_standard(path, api, enumerate_fn=bounded_names):
    if (not isinstance(path, Path) or not path.is_absolute() or '\0' in str(path)
            or len(str(path).encode('utf-8')) > 32768
            or path.resolve(strict=True) != path):
        raise ValueError('resolved bounded absolute directory required')
    metadata = path.lstat()
    if (not stat.S_ISDIR(metadata.st_mode)
            or getattr(metadata, 'st_file_attributes', 0) & 0x400
            or (os.name == 'nt' and (len(path.drive) != 2 or path.drive[1] != ':'))):
        raise ValueError('regular local directory required')
    before, stages, standards = api.named(path), [], []
    with api.open(path) as baseline:
        def mark(stage):
            stages.append(dict(stage=stage, baseline=sample(api, baseline), named=api.named(path)))
        def standard():
            value = api.standard(baseline)
            decoded = decode_standard(value['record'])
            decoded['nt_completion'] = {key: value[key] for key in ('status', 'iosb_status', 'information')}
            standards.append(decoded)
        mark('baseline')
        standard()
        mark('after-standard')
        enumeration = enumerate_fn(path)
        standard()
        mark('after-enumeration')
    after = api.named(path)
    def adjacent(observations):
        return [sorted(key for key in left['fields']
            if left['fields'][key] != right['fields'][key])
            for left, right in zip(observations, observations[1:])]
    return dict(path=str(path), before=before, stages=stages, after=after,
        standards=standards, enumeration=enumeration,
        named_adjacent_differences=adjacent([before, *[s['named'] for s in stages], after]),
        baseline_adjacent_differences=adjacent([s['baseline'] for s in stages]),
        standard_comparison_differences=[sorted(key for key in ('allocation_size', 'size', 'link_count')
            if std['fields'][key] != stage['baseline']['fields'][key])
            for std, stage in zip(standards, stages[1:])])


def owned_native_standard():
    root = Path.cwd()
    scratch = root / 'control-16'
    scratch.mkdir()
    for index in range(16):
        with (scratch / f'sample-{index:03d}.bin').open('xb') as output:
            output.write(b'x' * 512)
    installed = Path(sys.base_prefix).resolve(strict=True) / 'Lib' / 'asyncio'
    with NativeAPI() as api:
        cases = [inspect_standard(installed, api), inspect_standard(scratch, api)]
    print(json.dumps(dict(schema='alc-r0-directory-standard-v1', python=sys.version,
        scope='finite-readonly-installed-and-owned-scratch', scratch_root=str(root),
        logical_written_bytes=8192, cases=cases), sort_keys=True, separators=(',', ':')))


def initialized_sample(api, path, handle):
    value = api.standard_win32(handle)
    standard = decode_standard(value['record'])
    standard['win32_completion'] = {key: value[key] for key in
        ('win32_succeeded', 'buffer_bytes', 'info_class')}
    first = api.named(path)
    retained = sample(api, handle)
    last = api.named(path)
    if first['fields'] != last['fields']:
        raise ValueError('initialized named bookend changed')
    if any(standard['fields'][key] != first['fields'][key]
            for key in ('allocation_size', 'size', 'link_count')):
        raise ValueError('initialized standard disagreement')
    differences = sorted(key for key in first['fields']
        if first['fields'][key] != retained['fields'][key])
    if any(key != 'device_characteristics' for key in differences):
        raise ValueError('initialized cross-source disagreement')
    return dict(fields=dict(first['fields']), named_first=first, named_last=last,
        standard=standard, handle=retained, cross_route_differences=differences)


def inspect_initialized(path, api, enumerate_fn=bounded_names):
    if (not isinstance(path, Path) or not path.is_absolute() or '\0' in str(path)
            or len(str(path).encode('utf-8')) > 32768
            or path.resolve(strict=True) != path):
        raise ValueError('resolved bounded absolute directory required')
    metadata = path.lstat()
    if (not stat.S_ISDIR(metadata.st_mode)
            or getattr(metadata, 'st_file_attributes', 0) & 0x400
            or (os.name == 'nt' and (len(path.drive) != 2 or path.drive[1] != ':'))):
        raise ValueError('regular local directory required')
    with api.open(path) as handle:
        first = initialized_sample(api, path, handle)
        enumeration = enumerate_fn(path)
        second = initialized_sample(api, path, handle)
        third = initialized_sample(api, path, handle)
    final = api.named(path)
    observations = [first, second, third, final]
    differences = [sorted(key for key in left['fields']
        if left['fields'][key] != right['fields'][key])
        for left, right in zip(observations, observations[1:])]
    return dict(path=str(path), samples=[first, second, third], final_named=final,
        enumeration=enumeration, adjacent_differences=differences,
        stable=not any(differences))


def owned_native_initialized():
    root = Path.cwd()
    scratch = root / 'control-16'
    scratch.mkdir()
    for index in range(16):
        with (scratch / f'sample-{index:03d}.bin').open('xb') as output:
            output.write(b'x' * 512)
    installed = Path(sys.base_prefix).resolve(strict=True) / 'Lib' / 'asyncio'
    with NativeAPI() as api:
        cases = [inspect_initialized(installed, api), inspect_initialized(scratch, api)]
    print(json.dumps(dict(schema='alc-r0-directory-initialized-v1', python=sys.version,
        scope='finite-readonly-installed-and-owned-scratch', scratch_root=str(root),
        logical_written_bytes=8192, cases=cases), sort_keys=True, separators=(',', ':')))


def owned_native_access():
    root = Path.cwd()
    scratch = root / 'control-16'
    scratch.mkdir()
    for index in range(16):
        with (scratch / f'sample-{index:03d}.bin').open('xb') as output:
            output.write(b'x' * 512)
    installed = Path(sys.base_prefix).resolve(strict=True) / 'Lib' / 'asyncio'
    with NativeAPI() as api:
        cases = [inspect_access(installed, api), inspect_access(scratch, api)]
    print(json.dumps(dict(schema='alc-r0-directory-access-v1', python=sys.version,
        scope='finite-readonly-installed-and-owned-scratch', scratch_root=str(root),
        logical_written_bytes=8192, cases=cases), sort_keys=True, separators=(',', ':')))


_INVENTORY_NODES = (
    "tests/test_alc_r0_runtime_tree_inventory.py::test_exact_canonical_runtime_inventory",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_enumerated_identity_matches_path_and_open_file",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_change_diagnostic_identifies_exact_field[0-mode]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_change_diagnostic_identifies_exact_field[1-device]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_change_diagnostic_identifies_exact_field[2-inode]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_change_diagnostic_identifies_exact_field[3-size]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_change_diagnostic_identifies_exact_field[4-mtime_ns]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_change_diagnostic_identifies_exact_field[5-ctime_ns]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_change_diagnostic_identifies_exact_field[6-nlink]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_change_diagnostic_identifies_exact_field[7-attributes]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_change_diagnostic_membership_and_kind[added]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_change_diagnostic_membership_and_kind[removed]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_change_diagnostic_membership_and_kind[kind]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_change_diagnostic_bounded_path_and_deterministic_first",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_change_diagnostic_original_deadline",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_native_directory_walk_root_and_nested",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_native_directory_diagnostic_schema_change",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_native_directory_diagnostic_each_field[mode]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_native_directory_diagnostic_each_field[volume_serial]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_native_directory_diagnostic_each_field[file_id128]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_native_directory_diagnostic_each_field[size]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_native_directory_diagnostic_each_field[write_ticks]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_native_directory_diagnostic_each_field[creation_ticks]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_native_directory_diagnostic_each_field[link_count]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_native_directory_diagnostic_each_field[attributes]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_native_directory_diagnostic_each_field[change_ticks]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_native_directory_diagnostic_each_field[allocation_size]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_native_directory_diagnostic_each_field[legacy_file_id]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_native_directory_diagnostic_each_field[device_type]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_native_directory_diagnostic_each_field[device_characteristics]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_native_directory_diagnostic_each_field[reparse_tag]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_exact_finite_bounds[entry_count-0]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_exact_finite_bounds[entry_count-True]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_exact_finite_bounds[entry_count-65537]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_exact_finite_bounds[path_bytes-0]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_exact_finite_bounds[path_bytes-4194305]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_exact_finite_bounds[file_bytes--1]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_exact_finite_bounds[file_bytes-4294967297]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_exact_finite_bounds[total_file_bytes-17179869185]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_exact_finite_bounds[total_file_bytes-1.0]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_exact_all_bounds",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_one_byte_or_node_over_bound_denies[entry_count-1]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_one_byte_or_node_over_bound_denies[path_bytes-9]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_one_byte_or_node_over_bound_denies[file_bytes-6]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_one_byte_or_node_over_bound_denies[total_file_bytes-6]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_empty_directories_are_counted_and_hashed",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_empty_directory_cannot_bypass_node_bound",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_zero_length_file_and_zero_byte_allowances",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_multiple_chunks_and_binary_unicode_path",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_hardlinks_charge_each_logical_path",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_junction_denies_without_following_target",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_invalid_inputs_deny[expired]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_invalid_inputs_deny[component]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_invalid_inputs_deny[relative]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_invalid_inputs_deny[missing]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_invalid_inputs_deny[file]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_invalid_inputs_deny[empty]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_cross_source_identity_exception_is_only_windows_ctime[0]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_cross_source_identity_exception_is_only_windows_ctime[1]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_cross_source_identity_exception_is_only_windows_ctime[2]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_cross_source_identity_exception_is_only_windows_ctime[3]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_cross_source_identity_exception_is_only_windows_ctime[4]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_cross_source_identity_exception_is_only_windows_ctime[5]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_cross_source_identity_exception_is_only_windows_ctime[6]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_cross_source_identity_exception_is_only_windows_ctime[7]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_non_windows_requires_full_timestamp_identity",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_windows_executable_mode_exception_is_directed[33279-33206-True]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_windows_executable_mode_exception_is_directed[33270-33206-False]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_windows_executable_mode_exception_is_directed[33279-33207-False]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_windows_executable_mode_exception_is_directed[33279-33060-False]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_windows_executable_mode_exception_is_directed[33206-33279-False]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_windows_executable_mode_exception_is_directed[16895-33206-False]",
    "tests/test_alc_r0_runtime_tree_inventory.py::test_changed_path_and_bytes_change_inventory",
)


def main():
    mode = sys.argv[1:]
    if mode == ['--owned-native-library']:
        return owned_native_library()
    if mode == ['--owned-native']:
        return owned_native()
    if mode == ['--owned-native-access']:
        return owned_native_access()
    if mode == ['--owned-native-standard']:
        return owned_native_standard()
    if mode == ['--owned-native-initialized']:
        return owned_native_initialized()
    if mode not in (['--red'], ['--green'], ['--regression'],
                    ['--red-v2'], ['--green-v2'], ['--regression-v2'],
                    ['--red-adapter'], ['--green-adapter'], ['--regression-adapter'], ['--native'],
                    ['--red-access'], ['--green-access'], ['--regression-access'], ['--native-access'],
                    ['--green-access-v2'], ['--regression-access-v2'],
                    ['--red-standard'], ['--green-standard'], ['--regression-standard'], ['--native-standard'],
                    ['--red-initialized'], ['--green-initialized'], ['--regression-initialized'],
                    ['--regression-initialized-a'], ['--regression-initialized-b'],
                    ['--red-library'], ['--green-library'],
                    ['--red-library-v2'], ['--green-library-v2'],
                    ['--red-library-v3'], ['--green-library-v3'],
                    ['--regression-library-a'], ['--regression-library-b'],
                    ['--regression-library-b1'], ['--regression-library-b2'],
                    ['--regression-library-b21'], ['--regression-library-b22'], ['--regression-library-b23'],
                    ['--red-library-driver'], ['--green-library-driver'], ['--regression-library-driver'],
                    ['--native-library'],
                    ['--native-initialized']):
        raise ValueError('closed test-only mode required')
    from alc_r0_directory_metadata_reproducer import run_diagnostic
    cwd = Path(__file__).resolve().parents[1]
    name = mode[0][2:]
    stem = cwd / f'results/alc_r0_same_handle_{name}_20261011'
    paths = {suffix: Path(str(stem) + suffix) for suffix in
             ('.stdout.log', '.stderr.log', '.exit.json', '.xml')}
    if any(path.exists() for path in paths.values()):
        raise FileExistsError('retained evidence exists')
    tests = ['tests/test_alc_r0_same_handle_directory.py']
    if name in ('red-library-driver', 'green-library-driver', 'regression-library-driver'):
        tests = ['tests/test_alc_r0_library_candidate_driver.py']
    if name == 'regression-library-driver':
        tests += ['tests/test_alc_r0_standard_first_observer.py',
                  'tests/test_alc_r0_same_handle_directory.py']
    if name in ('red-library', 'green-library', 'red-library-v2', 'green-library-v2',
                'red-library-v3', 'green-library-v3', 'regression-library-a'):
        tests = ['tests/test_alc_r0_standard_first_observer.py']
    if name == 'regression-library-a':
        tests += ['tests/test_alc_r0_windows_directory_metadata.py']
    if name == 'regression-library-b':
        tests = ['tests/test_alc_r0_runtime_tree_inventory.py']
    if name in ('regression-library-b1', 'regression-library-b2'):
        tests = list(_INVENTORY_NODES[:36] if name.endswith('b1') else _INVENTORY_NODES[36:])
    partitions = {'regression-library-b21': (36, 46),
        'regression-library-b22': (46, 57), 'regression-library-b23': (57, 73)}
    if name in partitions:
        start, end = partitions[name]
        tests = list(_INVENTORY_NODES[start:end])
    if name in ('regression', 'regression-v2', 'regression-adapter', 'regression-access', 'regression-access-v2', 'regression-standard', 'regression-initialized'):
        tests += ['tests/test_alc_r0_directory_metadata_reproducer.py',
            'tests/test_alc_r0_windows_directory_metadata.py',
            'tests/test_alc_r0_runtime_tree_inventory.py']
    if name == 'regression-initialized-a':
        tests += ['tests/test_alc_r0_directory_metadata_reproducer.py']
    if name == 'regression-initialized-b':
        tests = ['tests/test_alc_r0_windows_directory_metadata.py',
            'tests/test_alc_r0_runtime_tree_inventory.py']
    environment = dict(os.environ, PYTHONPATH=str(cwd / 'src'),
        PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
        PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', CUDA_VISIBLE_DEVICES='-1',
        ALUCLU_TEST_ONLY_RUNTIME_SCAN='0', ALUCLU_TEST_ONLY_RUNTIME_CAUSE='0')
    temporary = Path(tempfile.mkdtemp(prefix='alc-r0-same-handle-')).resolve(strict=True)
    command = (sys.executable, '-B', '-m', 'pytest', '-q', *tests, '--junitxml=' + str(paths['.xml']))
    if name in partitions:
        command += ('--durations=10', '--tb=short')
    if name in ('red-library', 'green-library', 'red-library-v2', 'green-library-v2',
                'red-library-v3', 'green-library-v3', 'regression-library-a', 'regression-library-b'):
        command += ('--tb=short',)
    if name in ('red-library-driver', 'green-library-driver', 'regression-library-driver'):
        command += ('--tb=short',)
    if name in ('native', 'native-access', 'native-standard', 'native-initialized', 'native-library'):
        command = (sys.executable, '-I', '-B', str(Path(__file__).resolve()), '--owned-' + name)
        cwd = temporary
    receipt = run_diagnostic(command, cwd, environment, paths, temporary)
    receipt['scope'] = 'same-handle-directory-diagnostic'
    data = json.dumps(receipt, sort_keys=True, separators=(',', ':')).encode()
    with paths['.exit.json'].open('xb') as output:
        output.write(data)
    print(data.decode())


if __name__ == '__main__':
    main()
