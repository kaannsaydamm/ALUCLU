"""Actual owned READY correspondence, not installation provenance or admission.

Caller owns outer operator-before-reservation ordering and scientific validation.
No resume/release is performed. Low-level lease API still usable independently.
"""
from aluclu.cognition.persistence import atomic_write_bytes
from .canonical import canonical_json_bytes,parse_canonical_json
from .control_consumption import _path,_deadline,_claim,_read_record_path,read_consumption
from .fixed_d_request_file import _ancestors,_check_deadline
from .generation_binding import _request,_root,validate_generation_binding,validate_child_binding
from .reserved_owned_process import ReservedOwnedLease
from .runtime_tree_inventory import _fingerprint


class ReadyPublicationError(ValueError):
    """READY publication unconfirmed; caller must not infer resume permission."""


def _context(lease,request,ready_owner_root,deadline):
    if type(lease) is not ReservedOwnedLease:
        raise ReadyPublicationError('exact owned lease required')
    lease._require('READY')
    _deadline(deadline)
    _root(ready_owner_root)
    if (lease._lock is None or ready_owner_root!=lease._ready_root
            or deadline!=lease._deadline or deadline!=int(request['useful_deadline_monotonic_ns'])
            or request['reservation_id']!=lease._id or request['clock_domain_root']!=lease._clock):
        raise ReadyPublicationError('held READY/deadline/domain binding differs')
    lease._check_stop()
    lease._check_output()
    lease._live_identity()
    view=lease._view(lease._store.read(ready_owner_root),'READY')
    declaration=parse_canonical_json(view.declaration)
    expected_device='cpu' if request['control_id'].endswith('-cpu-fresh1-s20260916') else 'gpu'
    if (declaration['run_id']!=request['control_id'] or declaration['attempt_id']!='a001'
            or declaration['segment']!='initial' or declaration['device']!=expected_device
            or declaration['declaration_root']!=request['declaration_root']):
        raise ReadyPublicationError('reopened declaration differs')
    identity=lease.identity
    if identity.pid!=lease._information.pid:
        raise ReadyPublicationError('owned PID differs')
    lease._check_stop()
    lease._check_output()
    lease._live_identity()
    _check_deadline(deadline)
    return identity


def _consumption(directory,generation,request,installation_root,req,deadline):
    record=read_consumption(directory,req['control_id'],deadline_ns=deadline)
    expected=canonical_json_bytes(dict(schema='alc-r0-control-consumed-v1',
        control_id=req['control_id'],installation_root=installation_root,
        generation_root=generation.root,request_root=request.root,
        reservation_id=req['reservation_id']))
    if record.data!=expected:
        raise ReadyPublicationError('stored consumption differs')


def _child_path(directory,control,deadline):
    path,ancestors=_path(directory,control,deadline)
    return path.with_name(path.name.replace('.consumed.json','.child.json')),ancestors


def read_ready_child(directory,generation,request,*,installation_root,identity,
                     ready_owner_root,deadline_ns):
    """Bounded structural read; supplied identity does not prove owned origin."""
    try:
        _deadline(deadline_ns)
        validate_generation_binding(generation,request,installation_root)
        req=_request(request)
        path,ancestors=_child_path(directory,req['control_id'],deadline_ns)
        data=_read_record_path(path,ancestors,deadline_ns)
        result=validate_child_binding(data,generation,request,installation_root=installation_root,
            identity=identity,ready_owner_root=ready_owner_root)
        _check_deadline(deadline_ns)
        return result
    except (OSError,ValueError,TypeError,RuntimeError) as exc:
        if isinstance(exc,ReadyPublicationError): raise
        raise ReadyPublicationError('READY binding observation failed') from exc


def publish_ready_child(directory,generation,request,*,installation_root,lease,
                        ready_owner_root,deadline_ns):
    """Publish only from actual held READY state; never resume or free a claim."""
    try:
        if type(lease) is not ReservedOwnedLease:
            raise ReadyPublicationError('exact owned lease required')
        lease._require('READY')
        validate_generation_binding(generation,request,installation_root)
        req=_request(request)
        identity=_context(lease,req,ready_owner_root,deadline_ns)
        _consumption(directory,generation,request,installation_root,req,deadline_ns)
        data=canonical_json_bytes(dict(schema='alc-r0-operator-child-binding-v1',
            generation_root=generation.root,request_root=request.root,
            ready_owner_root=ready_owner_root,reservation_id=req['reservation_id'],
            pid=str(identity.pid),creation_filetime_100ns=str(identity.creation_filetime_100ns),
            owner_nonce=identity.owner_nonce,identity_receipt_root=identity.receipt_root))
        expected=validate_child_binding(data,generation,request,installation_root=installation_root,
            identity=identity,ready_owner_root=ready_owner_root)
        path,ancestors=_child_path(directory,req['control_id'],deadline_ns)
        _context(lease,req,ready_owner_root,deadline_ns)
        claimed=_claim(path,deadline_ns)
        if _ancestors(path,deadline_ns)!=ancestors or _fingerprint(path.lstat())!=claimed:
            raise ReadyPublicationError('child claim or namespace changed')
        _context(lease,req,ready_owner_root,deadline_ns)
        atomic_write_bytes(path,data)
        _check_deadline(deadline_ns)
        if _ancestors(path,deadline_ns)!=ancestors:
            raise ReadyPublicationError('child namespace changed during publication')
        actual=read_ready_child(directory,generation,request,installation_root=installation_root,
            identity=identity,ready_owner_root=ready_owner_root,deadline_ns=deadline_ns)
        if actual!=expected: raise ReadyPublicationError('published child binding differs')
        _consumption(directory,generation,request,installation_root,req,deadline_ns)
        if _context(lease,req,ready_owner_root,deadline_ns)!=identity:
            raise ReadyPublicationError('owned identity changed after publication')
        return actual
    except (OSError,ValueError,TypeError,RuntimeError) as exc:
        if isinstance(exc,ReadyPublicationError): raise
        raise ReadyPublicationError('READY publication failed; claims remain unavailable') from exc
