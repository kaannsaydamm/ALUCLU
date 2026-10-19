"""Temporary status observation, never an installed operator or permit."""
import importlib
import os
import time
from dataclasses import FrozenInstanceError

import pytest
from aluclu.alc_r0.canonical import canonical_json_bytes, sha256_bytes


def module():
    return importlib.import_module('aluclu.alc_r0.operator_status')


def record(**overrides):
    result = dict(schema='alc-r0-operator-status-v1', installation_root='a'*64,
                  generation_root='b'*64, sequence='1', revoked=False,
                  expires_utc_ns='9223372036854775807')
    result.update(overrides)
    return canonical_json_bytes(result)


def test_valid_status_is_frozen_observation():
    data = record()
    value = module().decode_operator_status(data)
    assert value.data == data and value.root == sha256_bytes(data)
    assert value.sequence == 1 and value.expires_utc_ns == 2**63-1
    assert value.revoked is False
    with pytest.raises(FrozenInstanceError):
        value.revoked = True


@pytest.mark.parametrize('field,value', [
    ('schema','other'), ('installation_root','A'*64), ('generation_root','x'),
    ('sequence',0), ('sequence','0'), ('sequence','01'), ('sequence',True),
    ('sequence',str(2**63)), ('expires_utc_ns','-1'), ('expires_utc_ns','1.0'),
    ('expires_utc_ns',None), ('revoked',1), ('revoked','false'), ('extra','x'),
])
def test_invalid_fields(field, value):
    with pytest.raises(module().OperatorStatusError):
        module().decode_operator_status(record(**{field:value}))


@pytest.mark.parametrize('data', [b'', b' '*4097, b'{}', b'null', b'{',
    b'{"schema":"x","schema":"x"}', b'['*3+b'0'+b']'*3,
    b'"'+b'x'*257+b'"', b'[0,'*32+b'0'+b']'*32,
    record()+b' ', record()+record(), bytearray(b'{}')])
def test_malformed_or_lexically_excessive(data):
    with pytest.raises(module().OperatorStatusError):
        module().decode_operator_status(data)


def test_revoked_or_old_expiry_are_observations_not_permissions():
    value = module().decode_operator_status(record(revoked=True, expires_utc_ns='1'))
    assert value.revoked is True and value.expires_utc_ns == 1


def test_real_single_read_and_next_status(tmp_path):
    path = tmp_path/'status.json'
    first = record()
    path.write_bytes(first)
    before = module().read_operator_status(path, deadline_ns=time.monotonic_ns()+10**9)
    next_path = tmp_path/'candidate.json'
    next_path.write_bytes(record(sequence='2', revoked=True))
    os.replace(next_path, path)
    after = module().read_operator_status(path, deadline_ns=time.monotonic_ns()+10**9)
    assert before.data == first and after.sequence == 2 and after.revoked
    assert before.root != after.root


@pytest.mark.parametrize('kind', ['oversize','empty','hardlink','directory','missing'])
def test_bad_files(tmp_path, kind):
    path = tmp_path/'status.json'
    path.write_bytes(record())
    if kind == 'oversize': path.write_bytes(b'x'*4097)
    elif kind == 'empty': path.write_bytes(b'')
    elif kind == 'hardlink': os.link(path,tmp_path/'alias')
    elif kind == 'directory': path.unlink(); path.mkdir()
    elif kind == 'missing': path.unlink()
    with pytest.raises(module().OperatorStatusError):
        module().read_operator_status(path,deadline_ns=time.monotonic_ns()+10**9)


@pytest.mark.parametrize('deadline',[1,0,None,True,2**63])
def test_bad_deadline(tmp_path,deadline):
    with pytest.raises(module().OperatorStatusError):
        module().read_operator_status(tmp_path/'missing',deadline_ns=deadline)


def test_worker_stays_denied():
    from aluclu.alc_r0.fixed_d_worker import _require_operator_handoff, WorkerHandoffUnavailable
    with pytest.raises(WorkerHandoffUnavailable): _require_operator_handoff()


def test_independent_lexical_token_boundary():
    # One container token plus63 scalar tokens, depth1: exactly64 allowed.
    module()._bounds(b'['+b','.join([b'0']*63)+b']')
    with pytest.raises(module().OperatorStatusError,match='token bound'):
        module()._bounds(b'['+b','.join([b'0']*64)+b']')


@pytest.mark.parametrize('path',['relative.json','//server/share/status.json',
                               'C:/ordinary/status:stream','C:/ordinary/NUL.json'])
def test_status_path_refusal(path):
    with pytest.raises(module().OperatorStatusError):
        module().read_operator_status(path,deadline_ns=time.monotonic_ns()+10**9)


@pytest.mark.parametrize('ancestor',[False,True])
def test_status_symlink_refusal(tmp_path,ancestor):
    path=tmp_path/'status.json'
    path.write_bytes(record())
    alias=tmp_path/'alias'
    try: alias.symlink_to(tmp_path if ancestor else path,target_is_directory=ancestor)
    except OSError as exc: pytest.skip(f'symlink unavailable: {exc}')
    with pytest.raises(module().OperatorStatusError):
        module().read_operator_status(alias/path.name if ancestor else alias,
                                     deadline_ns=time.monotonic_ns()+10**9)
