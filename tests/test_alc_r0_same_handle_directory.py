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
from alc_r0_same_handle_directory import inspect_access
from alc_r0_same_handle_directory import decode_standard, inspect_standard
from alc_r0_same_handle_directory import initialized_sample, inspect_initialized


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


@pytest.mark.parametrize('access', [0x80, 0x81])
def test_native_open_closed_access_choices(tmp_path, access):
    api = fake_adapter()
    with api.open(tmp_path, access=access) as handle:
        assert handle == 19
    assert api.create.calls[0][1] == access
    assert api.create.calls[0][2:] == (7, None, 3, 0x02200000, None)
    assert api.close.calls == [(19,)]


@pytest.mark.parametrize('access', [0, 1, 0x82, -1, True, 128.0, '128', None])
def test_native_open_invalid_access_before_create(tmp_path, access):
    api = fake_adapter()
    with pytest.raises(ValueError, match='access'):
        with api.open(tmp_path, access=access):
            pass
    assert api.create.calls == []
    assert api.close.calls == []


class FakeAccess(FakeInspection):
    def __init__(self, fail_access=None):
        super().__init__()
        self.next_handle = 19
        self.fail_access = fail_access
        self.changed = False

    @contextmanager
    def open(self, path, access=0x80):
        handle = self.next_handle
        self.next_handle += 1
        self.events.append(('open', handle, access))
        if access == self.fail_access:
            raise OSError('injected access open')
        try:
            yield handle
        finally:
            self.events.append(('close', handle))

    def named(self, path):
        result = super().named(path)
        if self.changed:
            result['fields']['change_ticks'] = 999
        return result


def test_access_exact_intervention_sequence_and_no_early_enumeration(tmp_path):
    api = FakeAccess()
    def enumeration(path):
        api.events.append(('enumerate', path))
        api.changed = True
        return dict(count=0, name_bytes=0, names_sha256='a' * 64)
    result = inspect_access(tmp_path, api, enumeration)
    one = ['stat', 'identity', 'device', 'stat']
    assert [event[0] for event in api.events] == [
        'named', 'open', *one, 'named',
        'open', *one, *one, 'named', 'close', *one, 'named',
        'open', *one, *one, 'named', 'close', *one, 'named',
        'enumerate', *one, 'named', 'close', 'named']
    assert [event for event in api.events if event[0] == 'open'] == [
        ('open', 19, 0x80), ('open', 20, 0x80), ('open', 21, 0x81)]
    assert [stage['stage'] for stage in result['stages']] == [
        'baseline', 'attributes-open', 'attributes-closed',
        'list-access-open', 'list-access-closed', 'enumerated']
    assert [stage['second_handle'] is not None for stage in result['stages']] == [
        False, True, False, True, False, False]
    assert result['named_adjacent_differences'] == [[], [], [], [], [], ['change_ticks'], []]
    assert result['baseline_adjacent_differences'] == [[], [], [], [], ['size']]
    assert result['stages'][-1]['baseline']['fields']['size'] == 1
    assert result['stages'][-1]['named']['fields']['change_ticks'] == 999
    assert result['enumeration']['count'] == 0
    for stage in result['stages']:
        assert len(stage['baseline']['fields']) == 14
        assert stage['baseline']['raw']['stat']


def test_access_second_open_failure_closes_baseline(tmp_path):
    api = FakeAccess(fail_access=0x81)
    with pytest.raises(OSError, match='injected access open'):
        inspect_access(tmp_path, api)
    assert api.events[-1] == ('close', 19)
    assert not any(event[0] == 'enumerate' for event in api.events)


def test_access_enumeration_failure_closes_baseline(tmp_path):
    api = FakeAccess()
    def enumeration(path):
        raise ValueError('injected enumeration')
    with pytest.raises(ValueError, match='injected enumeration'):
        inspect_access(tmp_path, api, enumeration)
    assert [event for event in api.events if event[0] == 'close'] == [
        ('close', 20), ('close', 21), ('close', 19)]


def test_access_regular_file_denied_before_queries(tmp_path):
    path = tmp_path / 'file'
    path.write_bytes(b'x')
    api = FakeAccess()
    with pytest.raises(ValueError, match='directory'):
        inspect_access(path, api)
    assert api.events == []


def standard_record(allocation=8192, size=4096, links=1, pending=0, directory=1):
    return struct.pack('<qqIBB', allocation, size, links, pending, directory) + b'xy'


@pytest.mark.parametrize('sizes', [(8192, 4096), (0, 0)])
def test_standard_exact_native_boolean_layout_and_padding(sizes):
    raw = standard_record(allocation=sizes[0], size=sizes[1], links=0xffffffff)
    assert len(raw) == struct.calcsize('<qqIBB2x') == 24
    assert decode_standard(raw) == dict(fields=dict(allocation_size=sizes[0],
        size=sizes[1], link_count=0xffffffff, delete_pending=False, directory=True),
        raw_hex=raw.hex())


@pytest.mark.parametrize('raw', [b'x' * 23, b'x' * 25, bytearray(24),
    standard_record(allocation=-1), standard_record(size=-1), standard_record(links=0),
    standard_record(pending=1), standard_record(pending=2),
    standard_record(directory=0), standard_record(directory=2)])
def test_standard_malformed_directory_records_denied(raw):
    with pytest.raises(ValueError, match='standard'):
        decode_standard(raw)


def test_standard_nt_exact_class_and_length():
    query = FakeNt(length=24)
    result = nt_record(query, 19, 24, 5, lambda: None)
    assert query.calls == [(19, 24, 5)]
    assert result['record'] == b'z' * 24
    assert result['information'] == 24


@pytest.mark.parametrize('status,length', [(-1, 24), (0, 23), (0, 25)])
def test_standard_nt_failure_or_nonexact_length_denied(status, length):
    with pytest.raises(ValueError, match='completion'):
        nt_record(FakeNt(status=status, length=length), 19, 24, 5, lambda: None)


def test_standard_pending_routes_to_fatal_without_decode():
    def fatal():
        raise RuntimeError('injected pending fatal')
    with pytest.raises(RuntimeError, match='injected pending fatal'):
        nt_record(FakeNt(status=259, length=24), 19, 24, 5, fatal)


def test_standard_adapter_query_class_and_raw_retention():
    api = fake_adapter()
    raw = standard_record()
    query = FakeNt(length=24)
    def native(handle, iosb, buffer, size, info_class):
        result = query(handle, iosb, buffer, size, info_class)
        ctypes.memmove(buffer, raw, len(raw))
        return result
    api.query_stat = native
    result = api.standard(19)
    assert query.calls == [(19, 24, 5)]
    assert result['record'] == raw


class FakeStandard(FakeInspection):
    def standard(self, handle):
        self.events.append(('standard', handle))
        return dict(record=standard_record(allocation=1234), status=0,
            iosb_status=0, information=24)


def test_standard_sequence_preserves_query_disagreement(tmp_path):
    api = FakeStandard()
    def enumeration(path):
        api.events.append(('enumerate', path))
        return dict(count=0, name_bytes=0, names_sha256='a' * 64)
    result = inspect_standard(tmp_path, api, enumeration)
    one = ['stat', 'identity', 'device', 'stat']
    assert [event[0] for event in api.events] == [
        'named', 'open', *one, 'named', 'standard', *one, 'named',
        'enumerate', 'standard', *one, 'named', 'close', 'named']
    assert [stage['stage'] for stage in result['stages']] == [
        'baseline', 'after-standard', 'after-enumeration']
    assert result['standard_comparison_differences'] == [['allocation_size']] * 2
    assert result['standards'][0]['fields']['allocation_size'] == 1234
    assert result['stages'][1]['baseline']['fields']['allocation_size'] == 8192
    assert result['standards'][0]['raw_hex'] == standard_record(allocation=1234).hex()
    assert result['standards'][0]['nt_completion'] == dict(status=0, iosb_status=0, information=24)
    assert result['baseline_adjacent_differences'] == [[], []]
    assert result['named_adjacent_differences'] == [[], [], [], []]


def test_standard_decode_failure_closes_baseline_before_enumeration(tmp_path):
    class InvalidStandard(FakeStandard):
        def standard(self, handle):
            return dict(record=standard_record(directory=0), status=0,
                iosb_status=0, information=24)
    api = InvalidStandard()
    with pytest.raises(ValueError, match='standard'):
        inspect_standard(tmp_path, api)
    assert api.events[-1] == ('close', tmp_path)


def test_standard_regular_file_denied_before_native(tmp_path):
    path = tmp_path / 'file'
    path.write_bytes(b'x')
    api = FakeStandard()
    with pytest.raises(ValueError, match='directory'):
        inspect_standard(path, api)
    assert api.events == []


class FakeInitialized(FakeInspection):
    def standard_win32(self, handle):
        self.events.append(('standard-win32', handle))
        return dict(record=standard_record(), win32_succeeded=True,
            buffer_bytes=24, info_class=1)


def test_initialized_win32_exact_class_buffer_and_no_invented_count():
    api = fake_adapter()
    api.extended = FakeFunction(payload=standard_record())
    result = api.standard_win32(19)
    assert result == dict(record=standard_record(), win32_succeeded=True,
        buffer_bytes=24, info_class=1)
    call = api.extended.calls[0]
    assert (call[0], call[1], call[3]) == (19, 1, 24)
    assert 'information' not in result


def test_initialized_win32_failure_no_fallback():
    api = fake_adapter()
    api.extended = FakeFunction(result=0)
    with pytest.raises(OSError):
        api.standard_win32(19)
    assert len(api.extended.calls) == 1


def test_initialized_exact_sequence_and_raw_retention(tmp_path):
    api = FakeInitialized()
    def enumeration(path):
        api.events.append(('enumerate', path))
        return dict(count=0, name_bytes=0, names_sha256='a' * 64)
    result = inspect_initialized(tmp_path, api, enumeration)
    one = ['standard-win32', 'named', 'stat', 'identity', 'device', 'stat', 'named']
    assert [event[0] for event in api.events] == [
        'open', *one, 'enumerate', *one, *one, 'close', 'named']
    assert result['stable'] is True
    assert result['adjacent_differences'] == [[], [], []]
    assert result['enumeration']['names_sha256'] == 'a' * 64
    assert len(result['samples']) == 3
    for value in result['samples']:
        assert value['fields'] == decode(*records())['fields']
        assert len(value['fields']) == 14
        assert value['standard']['raw_hex'] == standard_record().hex()
        assert value['standard']['win32_completion'] == dict(
            win32_succeeded=True, buffer_bytes=24, info_class=1)
        assert value['handle']['raw']['stat'] == records()[0].hex()
        assert value['named_first']['native_record_hex'] == 'a' * 208
        assert value['named_last']['native_record_hex'] == 'a' * 208


@pytest.mark.parametrize('field', list(decode(*records())['fields']))
def test_initialized_rejects_each_of_14_named_bookend_changes(tmp_path, field):
    class Changed(FakeInitialized):
        def named(self, path):
            value = super().named(path)
            if sum(event[0] == 'named' for event in self.events) == 2:
                old = value['fields'][field]
                value['fields'][field] = 'f' * 32 if isinstance(old, str) else old + 1
            return value
    with pytest.raises(ValueError, match='named bookend'):
        initialized_sample(Changed(), tmp_path, 19)


@pytest.mark.parametrize('field', ['allocation_size', 'size', 'link_count'])
def test_initialized_rejects_standard_disagreement(tmp_path, field):
    class Changed(FakeInitialized):
        def standard_win32(self, handle):
            value = super().standard_win32(handle)
            kwargs = dict(allocation=8192, size=4096, links=1)
            kwargs[dict(allocation_size='allocation', size='size', link_count='links')[field]] += 1
            value['record'] = standard_record(**kwargs)
            return value
    with pytest.raises(ValueError, match='standard disagreement'):
        initialized_sample(Changed(), tmp_path, 19)


@pytest.mark.parametrize('field', [key for key in decode(*records())['fields']
    if key != 'device_characteristics'])
def test_initialized_rejects_each_cross_source_mismatch(tmp_path, field):
    class Changed(FakeInitialized):
        def named(self, path):
            value = super().named(path)
            old = value['fields'][field]
            value['fields'][field] = 'f' * 32 if isinstance(old, str) else old + 1
            return value
    with pytest.raises(ValueError, match='disagreement'):
        initialized_sample(Changed(), tmp_path, 19)


def test_initialized_device_sources_retained_not_substituted(tmp_path):
    class DeviceDifference(FakeInitialized):
        def named(self, path):
            value = super().named(path)
            value['fields']['device_characteristics'] = 256
            return value
    result = initialized_sample(DeviceDifference(), tmp_path, 19)
    assert result['cross_route_differences'] == ['device_characteristics']
    assert result['fields']['device_characteristics'] == 256
    assert result['handle']['fields']['device_characteristics'] == 32


def test_initialized_continuity_includes_device_field(tmp_path):
    class ContinuityChange(FakeInitialized):
        def stat(self, handle):
            self.events.append(('stat', handle))
            return dict(record=records()[0], status=0, iosb_status=0, information=72)

        def named(self, path):
            value = super().named(path)
            value['fields']['device_characteristics'] = 257 if self.changed else 256
            return value
    api = ContinuityChange()
    def enumeration(path):
        # Do not use inherited FakeSample.changed: that mutates stat as well.
        api.changed = True
        return dict(count=0)
    result = inspect_initialized(tmp_path, api, enumeration)
    assert result['stable'] is False
    assert result['adjacent_differences'] == [['device_characteristics'], [], []]


def test_initialized_failed_standard_closes_before_enumeration(tmp_path):
    class Failed(FakeInitialized):
        def standard_win32(self, handle):
            raise OSError('injected standard error')
    api = Failed()
    with pytest.raises(OSError, match='injected standard error'):
        inspect_initialized(tmp_path, api)
    assert api.events == [('open', tmp_path), ('close', tmp_path)]


def test_initialized_file_denied_before_queries(tmp_path):
    path = tmp_path / 'file'
    path.write_bytes(b'x')
    api = FakeInitialized()
    with pytest.raises(ValueError, match='directory'):
        inspect_initialized(path, api)
    assert api.events == []
