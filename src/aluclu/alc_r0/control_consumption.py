"""Sticky fixed-control storage, not authenticated installation or admission.

Cooperating namespace must remain present and not be removed/replaced externally.
Errors never unlink a claim. Existing helper temp cleanup is not claim release.
"""
from dataclasses import dataclass
import os
from pathlib import Path

from aluclu.cognition.persistence import atomic_write_bytes
from .canonical import canonical_json_bytes,parse_canonical_json,sha256_bytes
from .fixed_d_wire import _CONTROLS
from .fixed_d_request_file import _local_path,_ancestors,_check_deadline,_read_bytes
from .generation_binding import validate_generation_binding,_record,_root,_id
from .operator_status import _file
from .runtime_tree_inventory import _fingerprint,_kind,_same_open_identity

_FILES=dict(zip(_CONTROLS,('d-cpu-fresh1.consumed.json','d-gpu-fresh1.consumed.json',
                         'd-gpu-fresh2.consumed.json'),strict=True))
_FIELDS=('schema','control_id','installation_root','generation_root','request_root','reservation_id')


class ControlConsumptionError(ValueError):
    """Consumption absent, conflicting or uncertain; never permission to retry."""


@dataclass(frozen=True,slots=True)
class ConsumptionRecord:
    data: bytes
    root: str


def _deadline(value):
    if type(value) is not int or not 1<=value<=2**63-1:
        raise ControlConsumptionError('invalid original consumption deadline')
    _check_deadline(value)


def _path(directory,control,deadline):
    _check_deadline(deadline)
    if type(control) is not str or control not in _FILES:
        raise ControlConsumptionError('closed control required')
    directory=_local_path(directory)
    if _kind(directory.lstat())!='directory' or directory.resolve(strict=True)!=directory:
        raise ControlConsumptionError('existing ordinary consumption namespace required')
    path=directory/_FILES[control]
    ancestors=_ancestors(path,deadline)
    _check_deadline(deadline)
    return path,ancestors


def _decode(data,control):
    value=_record(data,_FIELDS,'alc-r0-control-consumed-v1')
    if type(value['control_id']) is not str or value['control_id']!=control:
        raise ControlConsumptionError('consumption control differs')
    for field in ('installation_root','generation_root','request_root'): _root(value[field])
    _id(value['reservation_id'])
    return ConsumptionRecord(data,sha256_bytes(data))


def _claim(path,deadline):
    """Private exclusive-create step; no post-error deletion or retry."""
    _check_deadline(deadline)
    with path.open('xb') as stream:
        # Ownership is established by this open, not later existence checks.
        _check_deadline(deadline)
        opened=os.fstat(stream.fileno())
        if _kind(opened)!='file' or opened.st_nlink!=1 or opened.st_size!=0:
            raise ControlConsumptionError('unsafe exclusive claim')
        stream.flush()
        os.fsync(stream.fileno())
        _check_deadline(deadline)
        fingerprint=_fingerprint(os.fstat(stream.fileno()))
    _check_deadline(deadline)
    current=_fingerprint(path.lstat())
    if not _same_open_identity(current,fingerprint):
        raise ControlConsumptionError('claim identity changed')
    return current


def _read_record_path(path,ancestors,deadline_ns):
    """Private bounded bytes observation shared by the two fixed file domains."""
    _check_deadline(deadline_ns)
    original=_file(path.lstat())
    _check_deadline(deadline_ns)
    with path.open('rb',buffering=0) as stream:
        _check_deadline(deadline_ns)
        opened=_file(os.fstat(stream.fileno()))
        if not _same_open_identity(original,opened):
            raise ControlConsumptionError('record open identity differs')
        data=_read_bytes(stream,original[3],deadline_ns)
        if _file(os.fstat(stream.fileno()))!=opened:
            raise ControlConsumptionError('open record changed')
    _check_deadline(deadline_ns)
    if _file(path.lstat())!=original or _ancestors(path,deadline_ns)!=ancestors:
        raise ControlConsumptionError('record namespace changed')
    _check_deadline(deadline_ns)
    return data


def read_consumption(directory,control_id,*,deadline_ns):
    """Bounded stored observation, no availability/reset or provenance verdict."""
    try:
        _deadline(deadline_ns)
        path,ancestors=_path(directory,control_id,deadline_ns)
        data=_read_record_path(path,ancestors,deadline_ns)
        result=_decode(data,control_id)
        _check_deadline(deadline_ns)
        return result
    except (OSError,ValueError,TypeError,RuntimeError) as exc:
        if isinstance(exc,ControlConsumptionError): raise
        raise ControlConsumptionError('consumption observation failed') from exc


def consume_control(directory,generation,request,*,installation_root,deadline_ns):
    """Claim once before child creation; all failures keep the target unavailable."""
    try:
        _deadline(deadline_ns)
        checked=validate_generation_binding(generation,request,installation_root)
        gen=parse_canonical_json(checked.data)
        control=gen['control_id']
        data=canonical_json_bytes(dict(schema='alc-r0-control-consumed-v1',control_id=control,
            installation_root=installation_root,generation_root=checked.root,
            request_root=request.root,reservation_id=gen['reservation_id']))
        expected=_decode(data,control)
        path,ancestors=_path(directory,control,deadline_ns)
        claimed=_claim(path,deadline_ns)
        if _ancestors(path,deadline_ns)!=ancestors or _fingerprint(path.lstat())!=claimed:
            raise ControlConsumptionError('claim or namespace changed before publication')
        _check_deadline(deadline_ns)
        # Only the exclusive-create winner reaches replacement. Helper's own
        # temp cleanup never unlinks the fixed claim; namespace-loss is excluded.
        atomic_write_bytes(path,data)
        _check_deadline(deadline_ns)
        if _ancestors(path,deadline_ns)!=ancestors:
            raise ControlConsumptionError('namespace changed during publication')
        actual=read_consumption(directory,control,deadline_ns=deadline_ns)
        if actual!=expected: raise ControlConsumptionError('published consumption differs')
        _check_deadline(deadline_ns)
        return actual
    except (OSError,ValueError,TypeError,RuntimeError) as exc:
        if isinstance(exc,ControlConsumptionError): raise
        raise ControlConsumptionError('consumption failed; existing claim stays unavailable') from exc
