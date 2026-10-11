"""Explicit fake-query contracts, not native feasibility or acceptance."""
import ctypes
import stat
import struct
import subprocess
import sys
from pathlib import Path

import pytest

from alc_r0_same_handle_directory import decode, nt_record, sample


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
