"""Isolated diagnostic only; never installed binding or training admission."""
import json
import os
import ctypes
import stat
import struct
import sys
import tempfile
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
            or (size, info_class) not in ((72, 68), (8, 4))):
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


def main():
    mode = sys.argv[1:]
    if mode not in (['--red'], ['--green'], ['--regression'],
                    ['--red-v2'], ['--green-v2'], ['--regression-v2']):
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
    if name in ('regression', 'regression-v2'):
        tests += ['tests/test_alc_r0_directory_metadata_reproducer.py',
            'tests/test_alc_r0_windows_directory_metadata.py',
            'tests/test_alc_r0_runtime_tree_inventory.py']
    environment = dict(os.environ, PYTHONPATH=str(cwd / 'src'),
        PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
        PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', CUDA_VISIBLE_DEVICES='-1',
        ALUCLU_TEST_ONLY_RUNTIME_SCAN='0', ALUCLU_TEST_ONLY_RUNTIME_CAUSE='0')
    temporary = Path(tempfile.mkdtemp(prefix='alc-r0-same-handle-')).resolve(strict=True)
    command = (sys.executable, '-B', '-m', 'pytest', '-q', *tests, '--junitxml=' + str(paths['.xml']))
    receipt = run_diagnostic(command, cwd, environment, paths, temporary)
    data = json.dumps(receipt, sort_keys=True, separators=(',', ':')).encode()
    with paths['.exit.json'].open('xb') as output:
        output.write(data)
    print(data.decode())


if __name__ == '__main__':
    main()
