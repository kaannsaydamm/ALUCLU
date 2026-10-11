"""Explicit fake-query contracts, not native feasibility or acceptance."""
import ctypes
import stat
import struct
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from contextlib import contextmanager

import pytest

from alc_r0_same_handle_directory import decode, nt_record, sample
from alc_r0_same_handle_directory import NativeAPI, inspect, bounded_names


def records(**changes):
    fields = dict(legacy=-2, creation=1, access=2, write=3, change=4,
        allocation=8192, size=4096, attributes=16, reparse=0, links=1, effective=0)
    fields.update(changes)
    return (struct.pack('<7q4I', *fields.values()),
        struct.pack('<Q16s', 2**64-1, bytes(range(16))), struct.pack('<II', 7, 0x20))


def test_complete_exact_mapping_and_raw_retention():
    raw = records()
    result = decode(*raw)
    assert result['fields'] == dict(mode=stat.S_IFDIR | 0o777,
        volume_serial=2**64-1, file_id128=bytes(range(16)).hex(), size=4096,
        write_ticks=3, creation_ticks=1, link_count=1, attributes=16,
        change_ticks=4, allocation_size=8192, legacy_file_id=2**64-2,
        device_type=7, device_characteristics=0x20, reparse_tag=0)
    assert result['raw'] == dict(stat=raw[0].hex(), identity=raw[1].hex(), device=raw[2].hex())


def test_read_only_mode_and_valid_zero_sizes():
    result = decode(*records(attributes=17, allocation=0, size=0))
    assert result['fields']['mode'] == stat.S_IFDIR | 0o555
    assert result['fields']['size'] == result['fields']['allocation_size'] == 0


@pytest.mark.parametrize('index', range(3))
@pytest.mark.parametrize('kind', ['short', 'long', 'bytearray'])
def test_exact_raw_records_required(index, kind):
    raw = list(records())
    raw[index] = (raw[index][:-1] if kind == 'short' else
                  raw[index] + b'0' if kind == 'long' else bytearray(raw[index]))
    with pytest.raises(ValueError, match='record'):
        decode(*raw)


@pytest.mark.parametrize('changes', [dict(size=-1), dict(allocation=-1),
    dict(creation=-1), dict(write=-1), dict(change=-1), dict(links=0),
    dict(attributes=0), dict(attributes=0x410), dict(reparse=1)])
def test_malformed_directory_denied(changes):
    with pytest.raises(ValueError, match='metadata'):
        decode(*records(**changes))


def test_zero_128_identity_denied():
    values = list(records())
    values[1] = struct.pack('<Q16s', 1, bytes(16))
    with pytest.raises(ValueError, match='metadata'):
        decode(*values)


class FakeNt:
    def __init__(self, status=0, length=72, iosb_status=0x1234):
        self.status, self.length, self.iosb_status = status, length, iosb_status
        self.calls = []

    def __call__(self, handle, iosb_ptr, output, size, info_class):
        self.calls.append((handle, size, info_class))
        iosb_ptr._obj.status = self.iosb_status
        iosb_ptr._obj.information = self.length
        ctypes.memmove(output, b'z' * size, size)
        return self.status


def forbidden_fatal():
    raise AssertionError('unexpected fatal path')


def test_nt_return_success_authoritative_and_raw_status_retained():
    query = FakeNt()
    result = nt_record(query, 12, 72, 68, forbidden_fatal)
    assert query.calls == [(12, 72, 68)]
    assert result == dict(record=b'z' * 72, status=0, iosb_status=0x1234, information=72)


@pytest.mark.parametrize('status,length', [(0, 71), (0, 73), (-1073741822, 72), (1, 72)])
def test_nt_failed_or_nonexact_completion_denied(status, length):
    with pytest.raises(ValueError, match='query'):
        nt_record(FakeNt(status, length), 12, 72, 68, forbidden_fatal)


def test_pending_never_decodes_or_returns():
    class Fatal(BaseException):
        pass
    events = []
    def fatal():
        events.append('fatal')
        raise Fatal()
    with pytest.raises(Fatal):
        nt_record(FakeNt(259), 12, 72, 68, fatal)
    assert events == ['fatal']


def test_real_pending_fatal_isolated_child_exit():
    script = Path(__file__).with_name('alc_r0_same_handle_directory.py')
    command = ('import runpy; m=runpy.run_path(' + repr(str(script)) +
        '); m["pending_exit"](); raise RuntimeError("returned")')
    result = subprocess.run([sys.executable, '-I', '-B', '-c', command],
        capture_output=True, timeout=10)
    assert result.returncode == 71
    assert result.stdout == b''
    assert result.stderr == b'alc-r0 native query pending; isolated exit71\n'


def test_pending_fatal_with_closed_stderr_does_not_unwind_buffers():
    script = Path(__file__).with_name('alc_r0_same_handle_directory.py')
    command = ('import os, runpy\nm=runpy.run_path(' + repr(str(script)) + ')\n'
        'os.close(2)\ntry:\n'
        ' m["nt_record"](lambda *args:259,12,72,68,m["pending_exit"])\n'
        'finally:\n os.write(1,b"UNWOUND")\n')
    result = subprocess.run([sys.executable, '-I', '-B', '-c', command],
        capture_output=True, timeout=10)
    assert result.returncode == 71
    assert result.stdout == result.stderr == b''


class FakeSample:
    def __init__(self, changed=False):
        self.events, self.changed = [], changed

    def stat(self, handle):
        self.events.append(('stat', handle))
        raw = records(size=1 if self.changed and len(self.events) > 1 else 4096)[0]
        return dict(record=raw, status=0, iosb_status=0, information=72)

    def identity(self, handle):
        self.events.append(('identity', handle))
        return records()[1]

    def device(self, handle):
        self.events.append(('device', handle))
        return dict(record=records()[2], status=0, iosb_status=0, information=8)


def test_sample_query_order_and_retention():
    api = FakeSample()
    result = sample(api, 19)
    assert api.events == [('stat', 19), ('identity', 19), ('device', 19), ('stat', 19)]
    assert result['fields'] == decode(*records())['fields']
    assert result['stat_bookend']['record_hex'] == records()[0].hex()
    assert result['nt_stat']['status'] == result['nt_device']['status'] == 0


def test_sample_mutation_denied_without_normalization():
    with pytest.raises(ValueError, match='bookend'):
        sample(FakeSample(changed=True), 19)


class FakeFunction:
    def __init__(self, result=1, payload=None):
        self.result, self.payload, self.calls = result, payload, []

    def __call__(self, *args):
        self.calls.append(args)
        if self.payload is not None:
            ctypes.memmove(args[2], self.payload, len(self.payload))
        return self.result


def fake_adapter(handle=19, close=1):
    api = NativeAPI()
    api.create, api.close = FakeFunction(handle), FakeFunction(close)
    api.extended = FakeFunction(payload=records()[1])
    return api


def test_handle_exact_flags_and_close_even_on_failure(tmp_path):
    api = fake_adapter()
    with pytest.raises(RuntimeError, match='body failure'):
        with api.open(tmp_path) as handle:
            assert handle == 19
            raise RuntimeError('body failure')
    assert api.create.calls == [(str(tmp_path), 0x80, 7, None, 3, 0x02200000, None)]
    assert api.close.calls == [(19,)]


@pytest.mark.parametrize('handle', [None, 0, ctypes.c_void_p(-1).value])
def test_invalid_handle_never_used_or_closed(tmp_path, handle):
    api = fake_adapter(handle=handle)
    with pytest.raises(OSError):
        with api.open(tmp_path):
            pytest.fail('invalid handle yielded')
    assert api.close.calls == []


def test_close_failure_not_hidden(tmp_path):
    api = fake_adapter(close=0)
    with pytest.raises(OSError):
        with api.open(tmp_path):
            pass
    assert api.close.calls == [(19,)]


def test_native_methods_fixed_query_classes_and_fatal_binding():
    api = fake_adapter()
    api.query_stat = FakeNt()
    api.query_device = FakeNt(length=8)
    assert api.stat(19)['record'] == b'z' * 72
    assert api.device(19)['record'] == b'z' * 8
    assert api.query_stat.calls == [(19, 72, 68)]
    assert api.query_device.calls == [(19, 8, 4)]
    assert api.identity(19) == records()[1]
    call = api.extended.calls[0]
    assert (call[0], call[1], call[3]) == (19, 18, 24)


def test_identity_win32_failure_denied():
    api = fake_adapter()
    api.extended.result = 0
    with pytest.raises(OSError):
        api.identity(19)


def test_named_full_mapping_retains_original104_bytes(tmp_path):
    api = fake_adapter()
    base, identity, device = records()
    raw = base[:68] + device + bytes(4) + identity
    assert len(raw) == 104
    api.query_named = FakeFunction(payload=raw)
    result = api.named(tmp_path)
    assert result['fields'] == decode(*records())['fields']
    assert result['native_record_hex'] == raw.hex()
    call = api.query_named.calls[0]
    assert (call[0], call[1], call[3]) == (str(tmp_path), 3, 104)


def test_named_failure_denied(tmp_path):
    api = fake_adapter()
    api.query_named = FakeFunction(result=0)
    with pytest.raises(OSError):
        api.named(tmp_path)


def fake_libraries(fail=None):
    events = []
    libraries = {
        'api-ms-win-core-file-l2-1-4.dll': SimpleNamespace(_handle=11, GetFileInformationByName=FakeFunction()),
        'kernel32.dll': SimpleNamespace(_handle=12, CreateFileW=FakeFunction(),
            CloseHandle=FakeFunction(), GetFileInformationByHandleEx=FakeFunction()),
        'ntdll.dll': SimpleNamespace(_handle=13, NtQueryInformationFile=FakeFunction(),
            NtQueryVolumeInformationFile=FakeFunction())}
    def loader(name, **kwargs):
        events.append(('load', name, kwargs))
        if name == fail:
            raise OSError('injected load failure')
        return libraries[name]
    def release(handle):
        events.append(('release', handle))
    return events, loader, release


def test_loader_system32_prototypes_and_reverse_cleanup():
    events, loader, release = fake_libraries()
    with NativeAPI(loader, release) as api:
        assert api.query_stat.restype is ctypes.c_int32
        assert api.query_device.restype is ctypes.c_int32
        assert len(api.query_stat.argtypes) == len(api.query_device.argtypes) == 5
        assert api.create.restype is ctypes.c_void_p
        assert api.extended.argtypes[-1] is ctypes.c_uint32
    assert [event[1] for event in events[:3]] == [
        'api-ms-win-core-file-l2-1-4.dll', 'kernel32.dll', 'ntdll.dll']
    assert all(event[2] == dict(use_last_error=True, winmode=0x800) for event in events[:3])
    assert events[3:] == [('release', 13), ('release', 12), ('release', 11)]


def test_partial_library_load_unwinds():
    events, loader, release = fake_libraries(fail='ntdll.dll')
    with pytest.raises(OSError, match='injected'):
        with NativeAPI(loader, release):
            pass
    assert events[-2:] == [('release', 12), ('release', 11)]


class FakeInspection(FakeSample):
    def __init__(self, different=False):
        super().__init__()
        self.different = different

    def named(self, path):
        self.events.append(('named', path))
        fields = decode(*records(size=0 if self.different else 4096))['fields']
        return dict(fields=fields, native_record_hex='a' * 208)

    @contextmanager
    def open(self, path):
        self.events.append(('open', path))
        try:
            yield 19
        finally:
            self.events.append(('close', path))


def test_inspection_exact_sequence_and_cross_route_differences(tmp_path):
    api = FakeInspection(different=True)
    def enumeration(path):
        api.events.append(('enumerate', path))
        return dict(count=0, names_sha256='a' * 64)
    result = inspect(tmp_path, api, enumeration)
    one = ['stat', 'identity', 'device', 'stat']
    assert [event[0] for event in api.events] == [
        'named', 'open', *one, 'named', 'enumerate', *one, 'named', *one, 'close', 'named']
    assert len(result['handle_samples']) == 3
    assert len(result['named_samples']) == 4
    assert result['handle_stable'] and result['named_stable']
    assert result['cross_route_differences'] == [['size']] * 4
    assert result['handle_samples'][0]['fields']['size'] == 4096
    assert result['named_samples'][0]['fields']['size'] == 0


def test_inspection_enumeration_failure_closes_handle(tmp_path):
    api = FakeInspection()
    def enumeration(path):
        raise ValueError('enumeration failed')
    with pytest.raises(ValueError, match='enumeration failed'):
        inspect(tmp_path, api, enumeration)
    assert api.events[-1] == ('close', tmp_path)


def test_inspection_regular_file_refused_before_native(tmp_path):
    path = tmp_path / 'not-directory'
    path.write_bytes(b'not-dir')
    api = FakeInspection()
    with pytest.raises(ValueError, match='directory'):
        inspect(path, api)
    assert api.events == []


def test_enumeration_exact_count_and_bound(tmp_path):
    for index in range(256):
        (tmp_path / str(index)).touch()
    result = bounded_names(tmp_path)
    assert result['count'] == 256
    assert len(result['names_sha256']) == 64
    (tmp_path / 'overflow').touch()
    with pytest.raises(ValueError, match='bound'):
        bounded_names(tmp_path)
