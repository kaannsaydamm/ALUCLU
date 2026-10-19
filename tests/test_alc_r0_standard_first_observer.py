"""Injected library observer contracts, not installed-runtime acceptance."""
import struct
import ctypes
import time
from types import SimpleNamespace
from contextlib import contextmanager
from dataclasses import fields

import pytest

from test_alc_r0_windows_directory_metadata import api, record
from test_alc_r0_same_handle_directory import FakeFunction


def standard(allocation=4096, size=4096, links=1, pending=0, directory=1):
    return struct.pack('<qqIBB2x', allocation, size, links, pending, directory)


class FakeAPI:
    def __init__(self, *, changed_field=None, changed_at=2, failure=None):
        self.events = []
        self.changed_field, self.changed_at, self.failure = changed_field, changed_at, failure
        self.named_calls = 0

    @contextmanager
    def open(self, label):
        self.events.append('open')
        try:
            yield 19
        finally:
            self.events.append('close')

    def standard(self, handle):
        assert handle == 19
        self.events.append('standard')
        if self.failure == 'standard':
            raise ValueError('injected standard')
        return standard()

    def identity(self, handle):
        assert handle == 19
        self.events.append('identity')
        if self.failure == 'identity':
            raise ValueError('injected identity')
        return struct.pack('<Q16s', 2**64-2, bytes(range(1, 17)))

    def named(self, label):
        self.events.append('named')
        self.named_calls += 1
        if self.failure == 'named':
            raise ValueError('injected named')
        raw = record()
        if self.changed_field and self.named_calls == self.changed_at:
            if self.changed_field == 'FileId128':
                raw.FileId128[:] = b'f' * 16
            else:
                setattr(raw, self.changed_field, getattr(raw, self.changed_field) + 1)
        return bytes(raw)


def test_standard_library_exact_layout_and_valid_zero():
    assert api()._decode_standard(standard()) == (4096, 4096, 1)
    assert api()._decode_standard(standard(0, 0)) == (0, 0, 1)


@pytest.mark.parametrize('raw', [b'', bytes(23), bytes(25), bytearray(24),
    standard(-1), standard(size=-1), standard(links=0), standard(pending=1),
    standard(pending=2), standard(directory=0), standard(directory=2)])
def test_standard_library_invalid_records_deny(raw):
    with pytest.raises(ValueError, match='standard'):
        api()._decode_standard(raw)


def test_library_exact_sequence_full14_and_no_mutation():
    adapter = FakeAPI()
    result = api()._observe_composite(adapter, 'C:/fixed', time.monotonic_ns()+10**9)
    assert result == api()._decode(bytes(record()))
    assert len(fields(result)) == 14
    assert adapter.events == ['open', 'standard', 'named', 'identity', 'named', 'close', 'named']


@pytest.mark.parametrize('changed_at', [2, 3])
@pytest.mark.parametrize('field', ['FileId', 'CreationTime', 'LastWriteTime',
    'ChangeTime', 'AllocationSize', 'EndOfFile', 'FileAttributes', 'ReparseTag',
    'NumberOfLinks', 'DeviceType', 'DeviceCharacteristics', 'VolumeSerialNumber', 'FileId128'])
def test_library_named_fields_changed_deny_even_after_close(changed_at, field):
    # Mode is derived from FileAttributes; changing16->17 tests both attributes/mode.
    adapter = FakeAPI(changed_field=field, changed_at=changed_at)
    with pytest.raises(ValueError, match='directory'):
        api()._observe_composite(adapter, 'C:/fixed', time.monotonic_ns()+10**9)
    assert 'close' in adapter.events


@pytest.mark.parametrize('kind', ['volume', 'id', 'zero', 'short', 'long'])
def test_library_retained_handle_identity_mismatch_denied(kind):
    class BadIdentity(FakeAPI):
        def identity(self, handle):
            raw = super().identity(handle)
            return dict(volume=struct.pack('<Q16s', 1, bytes(range(1, 17))),
                id=struct.pack('<Q16s', 2**64-2, b'f'*16), zero=bytes(24),
                short=raw[:-1], long=raw+b'x')[kind]
    adapter = BadIdentity()
    with pytest.raises(ValueError, match='identity'):
        api()._observe_composite(adapter, 'C:/fixed', time.monotonic_ns()+10**9)
    assert adapter.events[-1] == 'close'


@pytest.mark.parametrize('field', ['allocation', 'size', 'links'])
def test_library_standard_disagreement_denied(field):
    class BadStandard(FakeAPI):
        def standard(self, handle):
            super().standard(handle)
            value = dict(allocation=4096, size=4096, links=1)
            value[field] += 1
            return standard(**value)
    adapter = BadStandard()
    with pytest.raises(ValueError, match='standard'):
        api()._observe_composite(adapter, 'C:/fixed', time.monotonic_ns()+10**9)
    assert adapter.events[-1] == 'close'


@pytest.mark.parametrize('failure', ['standard', 'identity', 'named'])
def test_library_acquisition_failure_closes_handle(failure):
    adapter = FakeAPI(failure=failure)
    with pytest.raises(ValueError, match='injected'):
        api()._observe_composite(adapter, 'C:/fixed', time.monotonic_ns()+10**9)
    assert adapter.events[-1] == 'close'


def test_library_expired_deadline_before_open():
    adapter = FakeAPI()
    with pytest.raises(ValueError, match='deadline expired'):
        api()._observe_composite(adapter, 'C:/fixed', 1)
    assert adapter.events == []


def test_library_expiry_during_acquisition_still_closes():
    class Expired(FakeAPI):
        def identity(self, handle):
            raise api().RuntimeInventoryError('original runtime inventory deadline expired')
    adapter = Expired()
    with pytest.raises(ValueError, match='deadline expired'):
        api()._observe_composite(adapter, 'C:/fixed', time.monotonic_ns()+10**9)
    assert adapter.events[-1] == 'close'


def libraries(fail_load=False):
    events = []
    kernel = SimpleNamespace(_handle=12, CreateFileW=FakeFunction(result=19),
        CloseHandle=FakeFunction(), GetFileInformationByHandleEx=FakeFunction(payload=standard()))
    named = SimpleNamespace(_handle=11, GetFileInformationByName=FakeFunction(payload=bytes(record())))
    def load(name, **kwargs):
        events.append(('load', name, kwargs))
        if name == 'kernel32.dll':
            if fail_load:
                raise OSError('injected load')
            return kernel
        assert name == 'api-ms-win-core-file-l2-1-4.dll'
        return named
    def release(handle):
        events.append(('release', handle))
    return events, load, release, kernel, named


def test_library_adapter_exact_abi_classes_flags_and_cleanup():
    events, loader, release, kernel, named = libraries()
    with api()._Win32DirectoryAPI(time.monotonic_ns()+10**9, loader, release) as adapter:
        assert kernel.CreateFileW.restype is ctypes.c_void_p
        assert kernel.GetFileInformationByHandleEx.restype is ctypes.c_int32
        assert kernel.GetFileInformationByHandleEx.argtypes == [
            ctypes.c_void_p, ctypes.c_int32, ctypes.c_void_p, ctypes.c_uint32]
        with adapter.open('C:/fixed') as handle:
            assert adapter.standard(handle) == standard()
            kernel.GetFileInformationByHandleEx.payload = struct.pack('<Q16s', 9, b'i'*16)
            assert adapter.identity(handle) == struct.pack('<Q16s', 9, b'i'*16)
            assert adapter.named('C:/fixed') == bytes(record())
    assert kernel.CreateFileW.calls == [('C:/fixed', 0x80, 7, None, 3, 0x02200000, None)]
    assert kernel.CloseHandle.calls == [(19,)]
    assert [(c[0], c[1], c[3]) for c in kernel.GetFileInformationByHandleEx.calls] == [
        (19, 1, 24), (19, 18, 24)]
    assert [(c[0], c[1], c[3]) for c in named.GetFileInformationByName.calls] == [('C:/fixed', 3, 104)]
    assert all(e[2] == dict(use_last_error=True, winmode=0x800) for e in events[:2])
    assert events[-2:] == [('release', 12), ('release', 11)]


@pytest.mark.parametrize('handle', [None, 0, ctypes.c_void_p(-1).value])
def test_library_adapter_invalid_handle_never_closed(handle):
    events, loader, release, kernel, _ = libraries()
    kernel.CreateFileW.result = handle
    with pytest.raises(ValueError, match='directory'):
        with api()._Win32DirectoryAPI(time.monotonic_ns()+10**9, loader, release) as adapter:
            with adapter.open('C:/fixed'):
                pytest.fail('invalid handle returned')
    assert kernel.CloseHandle.calls == []
    assert events[-2:] == [('release', 12), ('release', 11)]


@pytest.mark.parametrize('operation', ['standard', 'identity', 'named', 'close'])
def test_library_adapter_api_failure_closes_all_resources(operation):
    events, loader, release, kernel, named = libraries()
    if operation == 'close':
        kernel.CloseHandle.result = 0
    elif operation == 'named':
        named.GetFileInformationByName.result = 0
    else:
        kernel.GetFileInformationByHandleEx.result = 0
    with pytest.raises(ValueError, match='directory'):
        with api()._Win32DirectoryAPI(time.monotonic_ns()+10**9, loader, release) as adapter:
            with adapter.open('C:/fixed') as handle:
                if operation in ('standard', 'identity'):
                    getattr(adapter, operation)(handle)
                elif operation == 'named':
                    adapter.named('C:/fixed')
    assert kernel.CloseHandle.calls == [(19,)]
    assert events[-2:] == [('release', 12), ('release', 11)]


def test_library_adapter_partial_load_unwinds_first_library():
    events, loader, release, _, _ = libraries(fail_load=True)
    with pytest.raises(ValueError, match='directory API'):
        with api()._Win32DirectoryAPI(time.monotonic_ns()+10**9, loader, release):
            pytest.fail('failed load yielded')
    assert events[-1] == ('release', 11)


def test_library_adapter_deadline_expiry_in_body_does_not_skip_cleanup():
    events, loader, release, kernel, _ = libraries()
    with pytest.raises(ValueError, match='deadline expired'):
        with api()._Win32DirectoryAPI(time.monotonic_ns()+10**9, loader, release) as adapter:
            with adapter.open('C:/fixed'):
                adapter.deadline = 1
                adapter.standard(19)
    assert kernel.CloseHandle.calls == [(19,)]
    assert events[-2:] == [('release', 12), ('release', 11)]


@pytest.mark.parametrize('kind', ['raise', 'false'])
def test_library_adapter_release_failure_still_releases_remaining_library(kind):
    events, loader, release, _, _ = libraries()
    def failing_release(handle):
        release(handle)
        if handle == 12:
            if kind == 'raise':
                raise OSError('injected release error')
            return False
    with pytest.raises(ValueError, match='directory library release failed'):
        with api()._Win32DirectoryAPI(time.monotonic_ns()+10**9, loader, failing_release):
            pass
    assert events[-2:] == [('release', 12), ('release', 11)]


def test_library_adapter_expiry_after_create_closes_new_handle():
    events, loader, release, kernel, _ = libraries()
    with pytest.raises(ValueError, match='deadline expired'):
        with api()._Win32DirectoryAPI(time.monotonic_ns()+10**9, loader, release) as adapter:
            def create(*args):
                adapter.deadline = 1
                return 19
            kernel.CreateFileW = create
            adapter.create = create
            with adapter.open('C:/fixed'):
                pytest.fail('expired acquired handle yielded')
    assert kernel.CloseHandle.calls == [(19,)]
    assert events[-2:] == [('release', 12), ('release', 11)]
