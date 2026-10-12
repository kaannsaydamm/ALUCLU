"""Harmless transport fixtures; no model, tokenizer or execution authority."""
import hashlib
import importlib
import os
import time
from pathlib import Path

import pytest

from aluclu.alc_r0.canonical import canonical_json_bytes
from test_alc_r0_fixed_d_wire import request


def reader():
    return importlib.import_module('aluclu.alc_r0.fixed_d_request_file')


def fixture(tmp_path, data=None):
    data = canonical_json_bytes(request()) if data is None else data
    path = tmp_path / 'request.json'
    path.write_bytes(data)
    return path, data


def read(path, data, **kwargs):
    options = dict(expected_root=hashlib.sha256(data).hexdigest(),
                   deadline_ns=time.monotonic_ns() + 10_000_000_000)
    options.update(kwargs)
    return reader().read_d_request_file(path, **options)


@pytest.mark.parametrize('as_string', [False, True])
def test_valid_canonical_request(tmp_path, as_string):
    path, data = fixture(tmp_path)
    result = read(str(path) if as_string else path, data)
    assert result.data == data
    assert result.root == hashlib.sha256(data).hexdigest()


@pytest.mark.parametrize('root', ['b' * 64, 'A' * 64, '', 'a' * 63, None, 1])
def test_wrong_or_invalid_root(tmp_path, root):
    path, data = fixture(tmp_path)
    with pytest.raises(reader().DRequestFileError):
        read(path, data, expected_root=root)


@pytest.mark.parametrize('deadline', [None, True, 0, -1, 1, 2**63, '9'])
def test_invalid_or_expired_original_deadline(tmp_path, deadline):
    path, data = fixture(tmp_path)
    with pytest.raises(reader().DRequestFileError):
        read(path, data, deadline_ns=deadline)


@pytest.mark.parametrize('data', [b'', b'x' * 16385, b'{}', b'{', b'null'])
def test_size_and_codec_refusal(tmp_path, data):
    path, data = fixture(tmp_path, data)
    with pytest.raises(reader().DRequestFileError):
        read(path, data)


@pytest.mark.parametrize('path', ['relative.json', '../request.json',
                                '//server/share/request.json',
                                '\\\\?\\C:\\request.json',
                                '\\\\.\\C:\\request.json', None, 1, b'file'])
def test_invalid_paths(path):
    with pytest.raises(reader().DRequestFileError):
        read(path, b'{}')


def test_dot_components(tmp_path):
    path, data = fixture(tmp_path)
    raw = str(path.parent) + os.sep + '.' + os.sep + path.name
    with pytest.raises(reader().DRequestFileError):
        read(raw, data)


@pytest.mark.parametrize('kind', ['missing', 'directory', 'hardlink'])
def test_non_single_regular_file(tmp_path, kind):
    path, data = fixture(tmp_path)
    if kind == 'missing':
        path.unlink()
    elif kind == 'directory':
        path.unlink()
        path.mkdir()
    else:
        os.link(path, tmp_path / 'second.json')
    with pytest.raises(reader().DRequestFileError):
        read(path, data)


@pytest.mark.parametrize('ancestor', [False, True])
def test_links_refused(tmp_path, ancestor):
    path, data = fixture(tmp_path)
    alias = tmp_path / 'alias'
    try:
        alias.symlink_to(path.parent if ancestor else path, target_is_directory=ancestor)
    except OSError as exc:
        pytest.skip(f'host cannot create symlink: {exc.winerror}')
    with pytest.raises(reader().DRequestFileError):
        read(alias / path.name if ancestor else alias, data)


def test_path_bound():
    with pytest.raises(reader().DRequestFileError):
        read(os.path.abspath('x' * 4097), b'{}')


def test_worker_stays_denied():
    from aluclu.alc_r0.fixed_d_worker import WorkerHandoffUnavailable, _require_operator_handoff
    with pytest.raises(WorkerHandoffUnavailable):
        _require_operator_handoff()


@pytest.mark.parametrize('component', ['request:stream', 'NUL.json', 'CON',
                                     'COM1.txt', 'LPT¹', 'trailing.', 'trailing '])
def test_special_components_refused(tmp_path, component):
    with pytest.raises(reader().DRequestFileError):
        read(str(tmp_path / component), b'{}')


class ShortStream:
    def __init__(self, chunks):
        self.chunks = iter(chunks)
        self.allowances = []

    def read(self, allowance):
        self.allowances.append(allowance)
        return next(self.chunks)


def test_private_short_read_decreases_allowance():
    stream = ShortStream([b'a', b'b', b'c', b''])
    result = reader()._read_bytes(stream, 3, time.monotonic_ns() + 10**9)
    assert result == b'abc'
    assert stream.allowances == [4, 3, 2, 1]


@pytest.mark.parametrize('chunks', [[b'a', b''], [b'abcd'], [None], ['abc'],
                                  [bytearray(b'abc')], [b'abcde']])
def test_private_read_rejects_truncation_growth_or_invalid_return(chunks):
    stream = ShortStream(chunks)
    with pytest.raises(reader().DRequestFileError):
        reader()._read_bytes(stream, 3, time.monotonic_ns() + 10**9)


def test_private_expired_read_never_touches_stream():
    stream = ShortStream([])
    with pytest.raises(reader().DRequestFileError):
        reader()._read_bytes(stream, 3, 1)
    assert stream.allowances == []


class OwnedFilePath:
    """Explicit private-helper test double wrapping a real owned file handle."""
    def __init__(self, path, action):
        self.path, self.action = path, action
        self.stream = None
        self.opens = 0

    def lstat(self):
        return self.path.lstat()

    def open(self, *args, **kwargs):
        self.opens += 1
        self.stream = self.path.open(*args, **kwargs)
        if self.action == 'expire_after_open':
            # Private helper gets a deadline ~20ms away; cross it after acquire.
            time.sleep(0.04)
        return OwnedStream(self)


class OwnedStream:
    def __init__(self, owner):
        self.owner = owner
        self.acted = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.owner.stream.close()

    def fileno(self):
        return self.owner.stream.fileno()

    def read(self, count):
        result = self.owner.stream.read(count)
        if not self.acted and result:
            self.acted = True
            if self.owner.action == 'mutate':
                previous = self.owner.path.stat()
                os.utime(self.owner.path, ns=(previous.st_atime_ns,
                                             previous.st_mtime_ns + 2_000_000_000))
            elif self.owner.action == 'hardlink':
                os.link(self.owner.path, self.owner.path.parent / 'late-link')
        return result


@pytest.mark.parametrize('action', ['mutate', 'hardlink', 'expire_after_open'])
def test_owned_file_refusal_closes_real_handle(tmp_path, action):
    path, _ = fixture(tmp_path)
    owned = OwnedFilePath(path, action)
    duration = 20_000_000 if action == 'expire_after_open' else 10**9
    with pytest.raises(reader().DRequestFileError):
        reader()._read_file(owned, time.monotonic_ns() + duration)
    assert owned.opens == 1
    assert owned.stream is not None and owned.stream.closed


def test_owned_file_success_single_open_closes_real_handle(tmp_path):
    path, data = fixture(tmp_path)
    owned = OwnedFilePath(path, 'none')
    assert reader()._read_file(owned, time.monotonic_ns() + 10**9) == data
    assert owned.opens == 1 and owned.stream.closed
