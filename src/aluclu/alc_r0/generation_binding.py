"""Acyclic structural generation joins, never owned provenance or permission."""
from dataclasses import dataclass
import re

from .canonical import canonical_json_bytes, parse_canonical_json, sha256_bytes
from .fixed_d_wire import DRequest, _CONTROLS, _bounded_json, _hash, decode_d_request
from .operator_status import _bounds
from .reserved_owned_process import OwnedChildIdentity


class GenerationBindingError(ValueError):
    """Malformed or mismatched structural evidence; not an authority verdict."""


@dataclass(frozen=True, slots=True)
class GenerationRecord:
    data: bytes
    root: str


@dataclass(frozen=True, slots=True)
class ChildBinding:
    data: bytes
    root: str


def _require(condition):
    if not condition: raise GenerationBindingError('invalid generation binding')


def _record(data, fields, schema):
    try:
        _bounds(data)
        value=_bounded_json(data,4096)
        _require(type(value) is dict and set(value)==set(fields) and value['schema']==schema)
        return value
    except (ValueError,TypeError,UnicodeError,RecursionError) as exc:
        if isinstance(exc,GenerationBindingError): raise
        raise GenerationBindingError('invalid bounded generation record') from exc


def _root(value):
    try: _hash(value)
    except ValueError as exc: raise GenerationBindingError('invalid binding root') from exc


def _id(value):
    _require(type(value) is str and re.fullmatch('[A-Za-z0-9_-]{1,128}',value) is not None)


def _number(value, maximum):
    _require(type(value) is str and len(value)<=20 and re.fullmatch('[1-9][0-9]*',value) is not None)
    number=int(value)
    _require(number<=maximum)
    return number


def _request(request):
    _require(type(request) is DRequest)
    try: checked=decode_d_request(request.data)
    except ValueError as exc: raise GenerationBindingError('invalid request transport') from exc
    _require(type(request.root) is str and request.root==checked.root)
    return parse_canonical_json(checked.data)


def request_binding_root(request):
    value=_request(request)
    del value['authority_generation_root']
    return sha256_bytes(canonical_json_bytes(dict(
        schema='alc-r0-generation-request-binding-v1',request=value)))


def decode_generation(data):
    value=_record(data,('schema','installation_root','control_id','reservation_id',
        'attempt_id','segment','request_binding_root'),'alc-r0-operator-generation-v1')
    for field in ('installation_root','request_binding_root'): _root(value[field])
    _id(value['reservation_id'])
    _require(type(value['control_id']) is str and value['control_id'] in _CONTROLS
             and value['attempt_id']=='a001' and value['segment']=='initial')
    return GenerationRecord(data,sha256_bytes(data))


def validate_generation_binding(generation,request,installation_root):
    _require(type(generation) is GenerationRecord)
    checked=decode_generation(generation.data)
    _require(type(generation.root) is str and generation.root==checked.root)
    _root(installation_root)
    gen=parse_canonical_json(checked.data)
    req=_request(request)
    _require(gen['installation_root']==installation_root
        and gen['control_id']==req['control_id'] and gen['reservation_id']==req['reservation_id']
        and gen['request_binding_root']==request_binding_root(request)
        and req['authority_generation_root']==generation.root)
    return checked


def _identity_root(identity,reservation_id):
    _require(type(identity) is OwnedChildIdentity)
    _require(type(identity.pid) is int and 1<=identity.pid<=2**32-1
        and type(identity.creation_filetime_100ns) is int and 1<=identity.creation_filetime_100ns<=2**64-1
        and type(identity.owner_nonce) is str and re.fullmatch('[0-9a-f]{32}',identity.owner_nonce) is not None)
    _root(identity.receipt_root)
    root=sha256_bytes(canonical_json_bytes(dict(schema='alc-r0-owned-child-v1',
        reservation_id=reservation_id,pid=str(identity.pid),
        creation_filetime_100ns=str(identity.creation_filetime_100ns),owner_nonce=identity.owner_nonce)))
    _require(root==identity.receipt_root)
    return root


def validate_child_binding(data,generation,request,*,installation_root,identity,ready_owner_root):
    """Compare supplied evidence only; no store/handle/provenance is consulted."""
    validate_generation_binding(generation,request,installation_root)
    req=_request(request)
    _root(ready_owner_root)
    identity_root=_identity_root(identity,req['reservation_id'])
    value=_record(data,('schema','generation_root','request_root','ready_owner_root',
        'reservation_id','pid','creation_filetime_100ns','owner_nonce','identity_receipt_root'),
        'alc-r0-operator-child-binding-v1')
    for field in ('generation_root','request_root','ready_owner_root','identity_receipt_root'):
        _root(value[field])
    _id(value['reservation_id'])
    pid=_number(value['pid'],2**32-1)
    created=_number(value['creation_filetime_100ns'],2**64-1)
    _require(type(value['owner_nonce']) is str and re.fullmatch('[0-9a-f]{32}',value['owner_nonce']) is not None)
    _require((value['generation_root'],value['request_root'],value['ready_owner_root'],
        value['reservation_id'],pid,created,value['owner_nonce'],value['identity_receipt_root'])==
        (generation.root,request.root,ready_owner_root,req['reservation_id'],identity.pid,
         identity.creation_filetime_100ns,identity.owner_nonce,identity_root))
    return ChildBinding(data,sha256_bytes(data))
