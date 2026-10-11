"""Finite scratch-only diagnosis, never runtime acceptance or model admission."""
import ctypes
import hashlib
import json
import os
import stat
import struct
import sys
import tempfile
import time
from dataclasses import asdict
from pathlib import Path
from contextlib import ExitStack

COUNTS = (0, 16, 48)
PAYLOAD = b'x' * 512


def create_case(root, count):
    if type(count) is not int or count not in COUNTS:
        raise ValueError('closed scratch file count required')
    if not isinstance(root, Path) or not root.is_absolute():
        raise ValueError('absolute scratch root required')
    metadata = root.lstat()
    if not stat.S_ISDIR(metadata.st_mode) or getattr(metadata, 'st_file_attributes', 0) & 0x400:
        raise ValueError('regular scratch root required')
    path = root / f'case-{count}'
    path.mkdir()
    for index in range(count):
        with (path / f'sample-{index:03d}.bin').open('xb') as output:
            output.write(PAYLOAD)
    return path


def inspect_case(path, count, api):
    if type(count) is not int or count not in COUNTS:
        raise ValueError('closed scratch file count required')
    if not isinstance(path, Path) or not path.is_absolute() or path.name != f'case-{count}':
        raise ValueError('closed absolute scratch case required')
    observations = {'first': api.named(path)}
    metadata = path.lstat()
    if not stat.S_ISDIR(metadata.st_mode) or getattr(metadata, 'st_file_attributes', 0) & 0x400:
        raise ValueError('regular scratch directory required')
    fingerprint = [metadata.st_mode, metadata.st_dev, metadata.st_ino, metadata.st_size,
        metadata.st_mtime_ns, metadata.st_ctime_ns, metadata.st_nlink,
        getattr(metadata, 'st_file_attributes', 0)]
    observations['after_lstat'] = api.named(path)
    standard = api.standard(path)
    observations['after_handle'] = api.named(path)
    names, name_bytes = [], 0
    with os.scandir(path) as entries:
        for entry in entries:
            name_bytes += len(entry.name.encode('utf-8'))
            if len(names) >= 48 or name_bytes > 4096:
                raise ValueError('scratch enumeration bound exceeded')
            names.append(entry.name)
    expected = [f'sample-{index:03d}.bin' for index in range(count)]
    if sorted(names) != expected:
        raise ValueError('scratch membership differs')
    observations['after_enumeration'] = api.named(path)
    payload_digest = hashlib.sha256()
    for name in expected:
        item = path / name
        file_metadata = item.lstat()
        if (not stat.S_ISREG(file_metadata.st_mode)
                or getattr(file_metadata, 'st_file_attributes', 0) & 0x400):
            raise ValueError('scratch regular payload required')
        with item.open('rb') as stream:
            payload = stream.read(513)
        if payload != PAYLOAD:
            raise ValueError('scratch payload differs')
        payload_digest.update(payload)
    observations['after_file_reads'] = api.named(path)
    encoded = json.dumps(expected, separators=(',', ':')).encode()
    return dict(path=str(path), count=count, observations=observations,
        lstat=fingerprint, standard=standard, read_bytes=count * 512,
        payload_sha256=payload_digest.hexdigest(),
        enumeration=dict(count=len(names), names_sha256=hashlib.sha256(encoded).hexdigest()))


class Basic(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int64) for name in
        ('FileId', 'CreationTime', 'LastAccessTime', 'LastWriteTime', 'ChangeTime',
         'AllocationSize', 'EndOfFile')] + [(name, ctypes.c_uint32) for name in
        ('FileAttributes', 'ReparseTag', 'NumberOfLinks', 'DeviceType',
         'DeviceCharacteristics', 'Reserved')] + [
        ('VolumeSerialNumber', ctypes.c_int64), ('FileId128', ctypes.c_ubyte * 16)]


class Standard(ctypes.Structure):
    _fields_ = [('allocation', ctypes.c_int64), ('size', ctypes.c_int64),
        ('links', ctypes.c_uint32), ('delete_pending', ctypes.c_ubyte),
        ('directory', ctypes.c_ubyte)]


class NativeAPI:
    def __enter__(self):
        if (os.name != 'nt' or struct.calcsize('P') != 8 or sys.byteorder != 'little'
                or ctypes.sizeof(Basic) != 104 or ctypes.sizeof(Standard) != 24):
            raise ValueError('Windows64 exact native ABI required')
        import _ctypes
        self.stack = ExitStack()
        try:
            named_library = ctypes.WinDLL('api-ms-win-core-file-l2-1-4.dll', use_last_error=True, winmode=0x800)
            self.stack.callback(_ctypes.FreeLibrary, named_library._handle)
            kernel = ctypes.WinDLL('kernel32.dll', use_last_error=True, winmode=0x800)
            self.stack.callback(_ctypes.FreeLibrary, kernel._handle)
            self.query = named_library.GetFileInformationByName
            self.query.argtypes = [ctypes.c_wchar_p, ctypes.c_int32, ctypes.c_void_p, ctypes.c_uint32]
            self.query.restype = ctypes.c_int32
            self.create = kernel.CreateFileW
            self.create.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
                ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
            self.create.restype = ctypes.c_void_p
            self.extended = kernel.GetFileInformationByHandleEx
            self.extended.argtypes = [ctypes.c_void_p, ctypes.c_int32, ctypes.c_void_p, ctypes.c_uint32]
            self.extended.restype = ctypes.c_int32
            self.close = kernel.CloseHandle
            self.close.argtypes = [ctypes.c_void_p]
            self.close.restype = ctypes.c_int32
            return self
        except BaseException:
            self.stack.close()
            raise

    def __exit__(self, *exception):
        self.stack.close()

    def named(self, path):
        value = Basic()
        if not self.query(str(path), 3, ctypes.byref(value), 104):
            raise ctypes.WinError(ctypes.get_last_error())
        if not value.FileAttributes & 16 or value.FileAttributes & 0x400 or value.ReparseTag:
            raise ValueError('native regular scratch directory required')
        return dict(size=value.EndOfFile, allocation_size=value.AllocationSize,
            file_id128=bytes(value.FileId128).hex(), volume_serial=value.VolumeSerialNumber & (2**64 - 1),
            write_ticks=value.LastWriteTime, creation_ticks=value.CreationTime,
            change_ticks=value.ChangeTime, link_count=value.NumberOfLinks,
            attributes=value.FileAttributes, reparse_tag=value.ReparseTag,
            legacy_file_id=value.FileId & (2**64 - 1), device_type=value.DeviceType,
            device_characteristics=value.DeviceCharacteristics,
            mode=stat.S_IFDIR | (0o555 if value.FileAttributes & 1 else 0o777),
            native_record_hex=bytes(value).hex())

    def standard(self, path):
        handle = self.create(str(path), 0x80, 7, None, 3, 0x02200000, None)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            value = Standard()
            if not self.extended(handle, 1, ctypes.byref(value), 24):
                raise ctypes.WinError(ctypes.get_last_error())
            if not value.directory:
                raise ValueError('native handle directory classification differs')
            return dict(size=value.size, allocation_size=value.allocation,
                links=value.links, delete_pending=bool(value.delete_pending), directory=bool(value.directory))
        finally:
            if not self.close(handle):
                raise ctypes.WinError(ctypes.get_last_error())


def owned_scratch():
    root = Path.cwd()
    with NativeAPI() as api:
        cases = [inspect_case(create_case(root, count), count, api) for count in COUNTS]
    print(json.dumps(dict(schema='alc-r0-scratch-directory-metadata-v1', python=sys.version,
        scratch_root=str(root), counts=COUNTS, payload_bytes=512, logical_written_bytes=32768,
        cases=cases), sort_keys=True, separators=(',', ':')))


def run_diagnostic(command, cwd, environment, paths, temporary):
    from aluclu.alc_r0.canonical import canonical_json_bytes
    from aluclu.alc_r0.reservation_store import ReservationStore
    from aluclu.alc_r0.reserved_owned_process import ReservedOwnedLease
    from test_alc_r0_owned_stop import RetainedHandles
    root = 'a' * 64
    namespace = temporary / 'reservations'
    namespace.mkdir()
    (namespace / 'intents').mkdir()
    declarations = (canonical_json_bytes(dict(
        experiment_id='alc-r0-smollm2-135m-v1', reservation_id='r1',
        run_id='alc-r0-v1-pilot-fixture-s20260916', attempt_id='a001', segment='initial',
        declaration_root=root, device='cpu', useful_wall_ceiling_ns='60000000000',
        cleanup_ceiling_ns='10000000000', charge_envelope_ns='70000000000',
        gpu_reservation_ns='0', research_growth_bytes='4194304', physical_growth_bytes='8388608',
        stdout_limit_bytes='65536', stderr_limit_bytes='4096')),)
    store = ReservationStore(namespace, declarations)
    initial = store.initialize(store.initialization_intent())
    entry = time.monotonic_ns()
    event = canonical_json_bytes(dict(sequence='1', previous_root=initial.snapshot.root,
        reservation_id='r1', kind='reserve', evidence_root=root, declaration_root=root,
        entry_utc_ns=str(time.time_ns()), clock_domain_root=root,
        entry_monotonic_ns=str(entry), useful_deadline_monotonic_ns=str(entry + 60_000_000_000)))
    reserved = store.commit(store.prepare(initial.sha256, event, root))
    with ReservedOwnedLease(store, reserved.sha256, 'r1', command, cwd=cwd,
        environment=environment, stdout_path=paths['.stdout.log'],
        stderr_path=paths['.stderr.log'], deadline_ns=entry + 60_000_000_000,
        clock_domain_root=root) as lease:
        handles = RetainedHandles(lease)
        try:
            ready = lease.publish_identity(root, root)
            running = lease.resume_verified(ready.sha256)
            terminal = lease.wait_terminal()
            handles.drained(exit_code=terminal.process.exit_code)
        finally:
            handles.close()
    return dict(process=asdict(terminal.process), output=asdict(terminal.output),
        synthetic_reservation_state=store.read(running.sha256).snapshot.reservations[0].state,
        scratch_root=str(temporary), scope='scratch-directory-diagnostic')


def main():
    mode = sys.argv[1:]
    if mode == ['--owned-scratch']:
        return owned_scratch()
    if mode not in (['--red'], ['--green'], ['--regression'], ['--scratch']):
        raise ValueError('closed diagnostic mode required')
    cwd = Path(__file__).resolve().parents[1]
    name = mode[0][2:]
    stem = cwd / f'results/alc_r0_directory_reproducer_{name}_20261011'
    paths = {suffix: Path(str(stem) + suffix) for suffix in
             ('.stdout.log', '.stderr.log', '.exit.json', '.xml')}
    if any(path.exists() for path in paths.values()):
        raise FileExistsError('retained evidence exists')
    tests = ['tests/test_alc_r0_directory_metadata_reproducer.py']
    if name == 'regression':
        tests += ['tests/test_alc_r0_windows_directory_metadata.py',
                  'tests/test_alc_r0_runtime_tree_inventory.py']
    environment = dict(os.environ, PYTHONPATH=str(cwd / 'src'),
        PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
        PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', CUDA_VISIBLE_DEVICES='-1',
        ALUCLU_TEST_ONLY_RUNTIME_SCAN='0', ALUCLU_TEST_ONLY_RUNTIME_CAUSE='0')
    temporary = Path(tempfile.mkdtemp(prefix='alc-r0-directory-reproducer-')).resolve(strict=True)
    command = (sys.executable, '-B', '-m', 'pytest', '-q', *tests, '--junitxml=' + str(paths['.xml']))
    if name == 'scratch':
        command = (sys.executable, '-I', '-B', str(Path(__file__).resolve()), '--owned-scratch')
        cwd = temporary
    receipt = run_diagnostic(command, cwd, environment, paths, temporary)
    data = json.dumps(receipt,
        sort_keys=True, separators=(',', ':')).encode()
    with paths['.exit.json'].open('xb') as output:
        output.write(data)
    print(data.decode())


if __name__ == '__main__':
    main()
