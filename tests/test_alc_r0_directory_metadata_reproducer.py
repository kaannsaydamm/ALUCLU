"""Scratch contract tests; explicit fake API is not native Windows evidence."""
import pytest

from alc_r0_directory_metadata_reproducer import COUNTS, PAYLOAD, create_case, inspect_case


class FakeAPI:
    def __init__(self):
        self.events = []

    def named(self, path):
        self.events.append(('named', path))
        return {'size': len(self.events), 'allocation': 8192}

    def standard(self, path):
        self.events.append(('standard', path))
        return {'size': 8192, 'allocation': 8192, 'directory': True}


@pytest.mark.parametrize('count', COUNTS)
def test_closed_creation_is_bounded_and_exclusive(tmp_path, count):
    path = create_case(tmp_path, count)
    assert path == tmp_path / f'case-{count}'
    assert sorted(p.name for p in path.iterdir()) == [f'sample-{n:03d}.bin' for n in range(count)]
    assert all(p.read_bytes() == PAYLOAD for p in path.iterdir())
    assert len(PAYLOAD) == 512
    with pytest.raises(FileExistsError):
        create_case(tmp_path, count)


@pytest.mark.parametrize('count', [-1, 1, 49, True, '16'])
def test_foreign_counts_denied_before_writes(tmp_path, count):
    with pytest.raises(ValueError):
        create_case(tmp_path, count)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('count', COUNTS)
def test_sequence_preserves_raw_queries_and_payload(tmp_path, count):
    path = create_case(tmp_path, count)
    api = FakeAPI()
    result = inspect_case(path, count, api)
    assert [event[0] for event in api.events] == ['named', 'named', 'standard', 'named', 'named', 'named']
    assert all(event[1] == path for event in api.events)
    assert list(result['observations']) == ['first', 'after_lstat', 'after_handle', 'after_enumeration', 'after_file_reads']
    assert [value['size'] for value in result['observations'].values()] == [1, 2, 4, 5, 6]
    assert result['enumeration']['count'] == count
    assert result['read_bytes'] == count * 512
    assert result['standard']['directory'] is True
    assert all(p.read_bytes() == PAYLOAD for p in path.iterdir())


def test_unexpected_membership_refused(tmp_path):
    path = create_case(tmp_path, 0)
    (path / 'foreign.bin').write_bytes(b'foreign')
    with pytest.raises(ValueError, match='membership'):
        inspect_case(path, 0, FakeAPI())


def test_corrupted_payload_refused(tmp_path):
    path = create_case(tmp_path, 16)
    (path / 'sample-000.bin').write_bytes(b'bad')
    with pytest.raises(ValueError, match='payload'):
        inspect_case(path, 16, FakeAPI())
