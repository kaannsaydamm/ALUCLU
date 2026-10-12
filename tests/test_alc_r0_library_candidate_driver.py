"""Explicit candidate-driver contracts; no installed-runtime execution."""
import importlib
import time
from dataclasses import replace

import pytest
from aluclu.alc_r0.windows_directory_metadata import DirectoryObservation

def subject():
    return importlib.import_module('alc_r0_same_handle_directory').inspect_library

def observation():
    return DirectoryObservation(16895, 3, '01'*16, 4096, 2, 3, 1, 16, 4,
                                4096, 5, 7, 256, 0)

def test_candidate_sequence_full14_original_deadline(tmp_path):
    events = []
    deadline = time.monotonic_ns()+10**9
    def observe(path, *, deadline_ns):
        assert path == tmp_path
        assert deadline_ns == deadline
        events.append('observe')
        return observation()
    def enumerate_fn(path):
        assert path == tmp_path
        events.append('enumerate')
        return {'count': 16, 'name_bytes': 224, 'names_sha256': 'a'*64}
    result = subject()(tmp_path, observe, enumerate_fn, deadline_ns=deadline)
    assert events == ['observe', 'enumerate', 'observe', 'observe']
    assert len(result['observations']) == 3
    assert all(len(row) == 14 for row in result['observations'])
    assert result['stable'] is True
    assert result['observations'][0]['device_characteristics'] == 256
    assert result['enumeration']['count'] == 16

@pytest.mark.parametrize('at', [2, 3])
@pytest.mark.parametrize('field', tuple(DirectoryObservation.__dataclass_fields__))
def test_candidate_all14_changed_fail_no_retry(tmp_path, at, field):
    calls = []
    def observe(path, *, deadline_ns):
        calls.append(path)
        base = observation()
        value = getattr(base, field)
        changed = '02'*16 if isinstance(value, str) else value+1
        return replace(base, **{field: changed}) if len(calls) == at else base
    with pytest.raises(ValueError, match='changed'):
        subject()(tmp_path, observe, lambda p: {}, deadline_ns=time.monotonic_ns()+10**9)
    assert len(calls) == at

@pytest.mark.parametrize('stage', ['observe', 'enumerate'])
def test_candidate_acquisition_failure_is_not_retried(tmp_path, stage):
    calls = []
    def observe(path, *, deadline_ns):
        calls.append('observe')
        if stage == 'observe':
            raise OSError('injected')
        return observation()
    def enumerate_fn(path):
        calls.append('enumerate')
        raise OSError('injected')
    with pytest.raises(OSError, match='injected'):
        subject()(tmp_path, observe, enumerate_fn, deadline_ns=time.monotonic_ns()+10**9)
    assert calls == (['observe'] if stage == 'observe' else ['observe', 'enumerate'])

@pytest.mark.parametrize('expires_at', [0, 1, 2, 3, 4, 5, 6])
def test_candidate_original_expiry_stops_acquisition(tmp_path, expires_at):
    ticks = iter([0]*expires_at+[100]*10)
    events = []
    def observe(path, *, deadline_ns):
        events.append('observe')
        return observation()
    def enumerate_fn(path):
        events.append('enumerate')
        return {}
    with pytest.raises(ValueError, match='deadline'):
        subject()(tmp_path, observe, enumerate_fn, deadline_ns=50, clock=lambda: next(ticks))
    assert len(events) <= expires_at

@pytest.mark.parametrize('deadline', [True, 0, -1, '50', 2**63])
def test_candidate_invalid_deadline_denies_before_actions(tmp_path, deadline):
    def unexpected(*args, **kwargs):
        raise AssertionError('action before validation')
    with pytest.raises(ValueError, match='deadline'):
        subject()(tmp_path, unexpected, unexpected, deadline_ns=deadline)
