"""Synthetic structural joins, not authentic operator/OS identity or one-use."""
import importlib
from dataclasses import replace

import pytest
from aluclu.alc_r0.canonical import canonical_json_bytes, sha256_bytes
from aluclu.alc_r0.fixed_d_wire import decode_d_request
from aluclu.alc_r0.reserved_owned_process import OwnedChildIdentity
from test_alc_r0_fixed_d_wire import request, CONTROLS, ROOT_FIELDS


def module():
    return importlib.import_module('aluclu.alc_r0.generation_binding')


def fixture(control=CONTROLS[0]):
    req=request(control)
    initial=decode_d_request(canonical_json_bytes(req))
    gen_value=dict(schema='alc-r0-operator-generation-v1',installation_root='c'*64,
        control_id=control,reservation_id=req['reservation_id'],attempt_id='a001',
        segment='initial',request_binding_root=module().request_binding_root(initial))
    gen=module().decode_generation(canonical_json_bytes(gen_value))
    req['authority_generation_root']=gen.root
    final=decode_d_request(canonical_json_bytes(req))
    identity_value=dict(schema='alc-r0-owned-child-v1',reservation_id=req['reservation_id'],
        pid='123',creation_filetime_100ns='18446744073709551615',owner_nonce='d'*32)
    identity=OwnedChildIdentity(123,2**64-1,'d'*32,
                              sha256_bytes(canonical_json_bytes(identity_value)))
    binding=dict(schema='alc-r0-operator-child-binding-v1',generation_root=gen.root,
        request_root=final.root,ready_owner_root='e'*64,reservation_id=req['reservation_id'],
        pid='123',creation_filetime_100ns=str(2**64-1),owner_nonce='d'*32,
        identity_receipt_root=identity.receipt_root)
    return gen,final,identity,binding


def validate(gen,req,identity,binding,**overrides):
    options=dict(installation_root='c'*64,identity=identity,ready_owner_root='e'*64)
    options.update(overrides)
    return module().validate_child_binding(canonical_json_bytes(binding),gen,req,**options)


@pytest.mark.parametrize('control',CONTROLS)
def test_acyclic_full_structural_binding(control):
    gen,req,identity,binding=fixture(control)
    result=validate(gen,req,identity,binding)
    assert result.data==canonical_json_bytes(binding)
    assert result.root==sha256_bytes(result.data)
    assert module().request_binding_root(req)==module().request_binding_root(
        decode_d_request(canonical_json_bytes(request(control))))


@pytest.mark.parametrize('field',tuple(ROOT_FIELDS)+('reservation_id','snapshot_path',
                                                  'useful_deadline_monotonic_ns','control_id'))
def test_request_field_drift(field):
    gen,req,identity,binding=fixture()
    from aluclu.alc_r0.canonical import parse_canonical_json
    value=parse_canonical_json(req.data)
    if field.endswith('_root'): value[field]='f'*64
    elif field=='reservation_id': value[field]='other'
    elif field=='snapshot_path': value[field]='C:/other/snapshot'
    elif field=='control_id': value[field]=CONTROLS[1]
    else: value[field]='1'
    changed=decode_d_request(canonical_json_bytes(value))
    with pytest.raises(module().GenerationBindingError): validate(gen,changed,identity,binding)


@pytest.mark.parametrize('field',('generation_root','request_root','ready_owner_root',
    'reservation_id','pid','creation_filetime_100ns','owner_nonce','identity_receipt_root','schema'))
def test_child_field_drift(field):
    gen,req,identity,binding=fixture()
    replacement='f'*64 if field.endswith('_root') else 'f'*32 if field=='owner_nonce' else 'other'
    if field in ('pid','creation_filetime_100ns'): replacement='124'
    binding[field]=replacement
    with pytest.raises(module().GenerationBindingError): validate(gen,req,identity,binding)


@pytest.mark.parametrize('field,value',[('attempt_id','a002'),('segment','resume'),
    ('control_id','other'),('installation_root','A'*64),('extra',True)])
def test_generation_fields(field,value):
    gen,_,_,_=fixture()
    from aluclu.alc_r0.canonical import parse_canonical_json
    data=parse_canonical_json(gen.data); data[field]=value
    with pytest.raises(module().GenerationBindingError):
        module().decode_generation(canonical_json_bytes(data))


@pytest.mark.parametrize('field,value',[('pid',True),('pid',0),('pid',2**32),
    ('creation_filetime_100ns',0),('creation_filetime_100ns',2**64),
    ('owner_nonce','x'),('receipt_root','f'*64)])
def test_forged_identity(field,value):
    gen,req,identity,binding=fixture()
    with pytest.raises(module().GenerationBindingError):
        validate(gen,req,replace(identity,**{field:value}),binding)


@pytest.mark.parametrize('which',['generation','request','installation','ready'])
def test_forged_roots(which):
    gen,req,identity,binding=fixture()
    if which=='generation': gen=replace(gen,root='f'*64)
    if which=='request': req=replace(req,root='f'*64)
    options={}
    if which=='installation': options['installation_root']='f'*64
    if which=='ready': options['ready_owner_root']='f'*64
    with pytest.raises(module().GenerationBindingError): validate(gen,req,identity,binding,**options)


@pytest.mark.parametrize('data',[b'',b'{}',b'null',b' '*4097,b'['*3+b'0'+b']'*3])
def test_malformed_generation(data):
    with pytest.raises(module().GenerationBindingError): module().decode_generation(data)


def test_worker_denial_unchanged():
    from aluclu.alc_r0.fixed_d_worker import _require_operator_handoff,WorkerHandoffUnavailable
    with pytest.raises(WorkerHandoffUnavailable): _require_operator_handoff()
