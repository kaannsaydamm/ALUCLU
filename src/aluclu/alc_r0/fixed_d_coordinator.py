"""WIP fixed coordinator composition. Diagnostic evidence is NEVER science.

Default scientific installation is not established and remains denied. Closed
harmless roles share concrete ownership/verification mechanics; no caller can
select an executable, scientific verifier, runtime function or approving object.
This unfinished implementation is not qualification/learning readiness.
"""
from contextlib import ExitStack
from dataclasses import asdict,dataclass
import ctypes
import base64
import os
from pathlib import Path
import select
import socket
import sys
import tempfile
import threading
import time

from aluclu.cognition.persistence import atomic_write_bytes
from .canonical import canonical_json_bytes,parse_canonical_json,sha256_bytes
from .fixed_d_request_file import _local_path,_ancestors,_read_file,_check_deadline
from .fixed_d_wire import _bounded_json
from .deadline_file_lock import deadline_file_lock
from .reservation_store import ReservationStore
from .reservation_state import _DIAGNOSTIC_ID
from .runtime_tree_inventory import RuntimeTreeBounds,_walk,_hash_file,_fingerprint,_kind,_same_open_identity
from .reserved_owned_process import ReservedOwnedLease,OwnedStopSignal,_creation_time,_LeaseOutputPair
from .checkpoint_owned_process import _Job,_ProcessInformation,_create_suspended,_resume,OwnedProcessReceipt,_Accounting,_checked
from .bounded_process_output import BoundedOutputPair
from .operator_status import decode_operator_status
from .status_publication import StatusPublicationStore,prepare_status_intent,read_committed_operator_status
from .authority_watch_policy import WatchPolicy,OBSERVATION_NS
from .live_authority_watch import LiveAuthorityWatch
from .status_watch_consumer import StatusWatchConsumer

_DOMAIN='diagnostic-only'
_MODULE='aluclu.alc_r0.fixed_d_coordinator'
_NS=1_000_000_000
_SCENARIOS=('success','slow-parent','stale-before-create','stale-before-resume','blocked-observer',
    'bootstrap-conflict','bootstrap-wrong-role','busy-revocation','busy-tree-revocation','tree-validation-delay',
    'actuator-query-denied','actuator-terminate-denied','completion-conflict','output-capacity-lost')


class CoordinatorError(ValueError):
    """Unconfirmed composition. Never release an uncertain reservation."""


class _ReleasedCompletionUnconfirmed(CoordinatorError):
    """Execution settled with storage held; derivative report unconfirmed."""
    def __init__(self,owner_root):
        self.owner_root=owner_root
        super().__init__('execution settled; storage held; completion publication unconfirmed: '+owner_root)


class _ChannelClosed(CoordinatorError):
    """Explicit EOF only; malformed frames are not normal shutdown."""


class _ChannelCancelled(CoordinatorError):
    """Raised only by an explicit local cancellation check."""


class _ObserverStop:
    """Filesystem cancellation is confined to the owned observer process."""
    def __init__(self,root,deadline): self.path=root/'observer.stop.json'; self.deadline=deadline

    def is_set(self):
        if not self.path.exists(): return False
        _require(_read(self.path,self.deadline)==dict(domain=_DOMAIN),'observer shutdown marker differs')
        return True


def _require(condition,message):
    if not condition: raise CoordinatorError(message)


def _read(path,deadline):
    path=_local_path(path); before=_ancestors(path,deadline)
    data=_read_file(path,deadline)
    _require(_ancestors(path,deadline)==before,'namespace changed')
    return _bounded_json(data,16384)


def _fresh(path,value,deadline):
    _check_deadline(deadline)
    data=canonical_json_bytes(value)
    _require(len(data)<=16384,'bounded diagnostic record required')
    before=_ancestors(path,deadline)
    with path.open('xb') as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    _check_deadline(deadline)
    _require(_ancestors(path,deadline)==before,'publication namespace changed')
    _require(_read(path,deadline)==value,'publication readback differs')
    return sha256_bytes(data)


def _replace(path,value,deadline):
    _check_deadline(deadline)
    data=canonical_json_bytes(value)
    _require(len(data)<=16384,'bounded diagnostic message required')
    before=_ancestors(path,deadline)
    atomic_write_bytes(path,data)
    _check_deadline(deadline)
    _require(_ancestors(path,deadline)==before,'message namespace changed')


class _FileStandardInfo(ctypes.Structure):
    _fields_=[('allocation',ctypes.c_longlong),('eof',ctypes.c_longlong),
        ('links',ctypes.c_uint32),('delete_pending',ctypes.c_ubyte),('directory',ctypes.c_ubyte)]


class _FileAttributes(ctypes.Structure):
    _fields_=[('attributes',ctypes.c_uint32),('tag',ctypes.c_uint32)]


def _output_native(stream):
    import msvcrt
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    query=kernel.GetFileInformationByHandleEx
    query.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p,ctypes.c_uint32]
    query.restype=ctypes.c_int
    handle=msvcrt.get_osfhandle(stream.fileno())
    standard=_FileStandardInfo(); attributes=_FileAttributes()
    for kind,value in ((1,standard),(9,attributes)):
        if not query(handle,kind,ctypes.byref(value),ctypes.sizeof(value)):
            raise ctypes.WinError(ctypes.get_last_error())
    _require(not standard.directory and not standard.delete_pending and standard.links==1,
        'ordinary single-link live output required')
    _require(not attributes.attributes & (0x200|0x400|0x800),
        'sparse compressed or reparse output refused')
    return standard,attributes


def _observe_output(stream,path,limit,stage,deadline):
    _check_deadline(deadline)
    path=_local_path(path); ancestors=_ancestors(path,deadline)
    before=_fingerprint(path.lstat()); opened=_fingerprint(os.fstat(stream.fileno()))
    _require(_kind(path.lstat())=='file' and _same_open_identity(before,opened),
        'output path/open identity differs')
    native,attributes=_output_native(stream)
    _require(limit<=native.allocation<1<<63 and 0<=native.eof<=limit,
        'output allocation or EOF differs from bounded capacity')
    if stage in ('before-create','before-resume'):
        _require(native.eof==0,'suspended output EOF must be zero')
    _require(_fingerprint(path.lstat())==before and _fingerprint(os.fstat(stream.fileno()))==opened
        and _ancestors(path,deadline)==ancestors,'output identity changed during observation')
    _check_deadline(deadline)
    return dict(stream='stdout' if path.name.endswith('stdout') else 'stderr',path=path.name,
        limit_bytes=str(limit),allocation_bytes=str(native.allocation),eof_bytes=str(native.eof),
        links=str(native.links),device=str(opened[1]),inode=str(opened[2]),
        attributes=str(attributes.attributes),stage=stage,observed_monotonic_ns=str(time.monotonic_ns()))


def _allocate_output(stream,path,limit,deadline):
    _check_deadline(deadline)
    _require(limit==16384,'fixed diagnostic output capacity required')
    native,_=_output_native(stream)
    _require(native.eof==0,'fresh output required before allocation')
    _set_output_allocation(stream,limit)
    os.fsync(stream.fileno())
    return _observe_output(stream,path,limit,'before-create',deadline)


def _set_output_allocation(stream,amount):
    """Fixed native operation on an already owned diagnostic destination."""
    import msvcrt
    _require(type(amount) is int and amount in (0,16384),'closed allocation amount required')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    allocate=kernel.SetFileInformationByHandle
    allocate.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p,ctypes.c_uint32]
    allocate.restype=ctypes.c_int
    size=ctypes.c_longlong(amount)
    if not allocate(msvcrt.get_osfhandle(stream.fileno()),5,ctypes.byref(size),ctypes.sizeof(size)):
        raise ctypes.WinError(ctypes.get_last_error())


class _AllocatedOutputs:
    """Fixed same-destination capacity evidence; existing pump enforces writes."""
    def __init__(self,*arguments,**keywords):
        self._allocations={}; self._final_capacity=[]; self._capacity_lock=threading.Lock()
        self._capacity_secondary=None
        super().__init__(*arguments,**keywords)

    def _open_destination(self,path):
        path=_local_path(path)
        ancestors=_ancestors(path,self._deadline)  # Reject aliases BEFORE file creation/allocation.
        target=next(item for item in self._streams if item.path==path)
        stream=super()._open_destination(path)
        # Retain ownership BEFORE the native allocation can fail. Base partial
        # acquisition cleanup now owns this destination even on a raised call.
        target.destination=stream
        _require(_ancestors(path,self._deadline)==ancestors,'output ancestor changed during creation')
        row=self._allocate_destination(stream,path,target.limit)
        self._allocations[stream]=(path,target.limit,(row['device'],row['inode']))
        return stream

    def _allocate_destination(self,stream,path,limit):
        """Fixed private acquisition boundary; never a public selected backend."""
        return _allocate_output(stream,path,limit,self._deadline)

    def capacity_observations(self,stage,deadline):
        self._owner()
        _require(stage in ('before-create','before-resume'),'fixed output stage required')
        rows=[]
        for item in self._streams:
            path,limit,identity=self._allocations[item.destination]
            row=_observe_output(item.destination,path,limit,stage,min(deadline,self._deadline))
            _require((row['device'],row['inode'])==identity,'retained output identity differs')
            rows.append(row)
        return rows

    @property
    def final_capacity_observations(self):
        with self._capacity_lock: return tuple(dict(row) for row in self._final_capacity)

    def _close_resource(self,resource):
        if resource not in self._allocations or resource.closed:
            return super()._close_resource(resource)
        path,limit,identity=self._allocations[resource]; failure=None; row=None
        try:
            os.fsync(resource.fileno())
            candidate=_observe_output(resource,path,limit,'before-close',self._deadline)
            _require((candidate['device'],candidate['inode'])==identity,'final output identity differs')
            row=candidate  # Publish only after ALL observation checks succeed.
        except BaseException as error: failure=error
        try: super()._close_resource(resource)
        except BaseException as error:
            if failure is None: failure=error
            else:
                with self._capacity_lock:
                    if self._capacity_secondary is None: self._capacity_secondary=error
        if row is not None:
            with self._capacity_lock: self._final_capacity.append(row)
        if failure is not None: raise failure


class _AllocatedOutputPair(_AllocatedOutputs,BoundedOutputPair):
    """Fixed private observer/diagnostic sink, not a caller-selected backend."""


class _AllocatedLeaseOutput(_AllocatedOutputs,_LeaseOutputPair):
    """Preserves the existing lease-specific partial cleanup deadline."""


def _capacity_stage(spec,role,output,stage):
    rows=output.capacity_observations(stage,spec.useful)
    _fresh(spec.namespace/f'{role}.output.{stage}.json',dict(domain=_DOMAIN,
        request_root=spec.request_root,role=role,stage=stage,streams=rows),spec.useful)


def _action_observed(spec,role,action,information,started,finished):
    _fresh(spec.namespace/f'{role}.action.{action}.json',dict(domain=_DOMAIN,
        request_root=spec.request_root,role=role,action=action,
        pid=str(information.pid),creation_filetime_100ns=str(_creation_time(information.process)),
        started_monotonic_ns=str(started),finished_monotonic_ns=str(finished)),spec.useful)


def _caller_capacity(root,deadline):
    """Current caller capacity, never attributable job growth or a projection."""
    _check_deadline(deadline)
    _require(os.name=='nt','Windows capacity observation required')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    query=kernel.GetDiskFreeSpaceExW
    query.argtypes=[ctypes.c_wchar_p,*([ctypes.POINTER(ctypes.c_ulonglong)]*3)]
    query.restype=ctypes.c_int
    available=ctypes.c_ulonglong(); total=ctypes.c_ulonglong(); free=ctypes.c_ulonglong()
    if not query(str(root),ctypes.byref(available),ctypes.byref(total),ctypes.byref(free)):
        raise ctypes.WinError(ctypes.get_last_error())
    _check_deadline(deadline)
    return dict(kind='windows-caller-available-volume-observation',
        caller_available_bytes=str(available.value),caller_total_bytes=str(total.value),
        volume_free_bytes=str(free.value),observed_monotonic_ns=str(time.monotonic_ns()))


def _observe_growth(root,request_root,owner_root,pending_research,pending_physical,deadline):
    """Finite stable DEFAULT-STREAM prefix. Full reservations remain held.

    No physical-materialization claim, attribution by free-space delta or credit
    for future publications. Blocking calls still require outer native ownership.
    """
    root=_local_path(root); ancestors=_ancestors(root/'probe',deadline)
    _require(root.drive.casefold()=='c:','original C-volume capacity scope required')
    before_capacity=_caller_capacity(root,deadline)
    bounds=RuntimeTreeBounds(entry_count=128,path_bytes=8192,
        file_bytes=1<<20,total_file_bytes=1<<20)
    nodes,files,total=_walk(root,bounds,deadline)
    rows=[]
    for relative in sorted(path for path in nodes if path):
        _check_deadline(deadline)
        kind,fingerprint=nodes[relative]
        if kind=='file': _require(fingerprint[6]==1,'growth prefix hardlink refused')
        # Windows byte-range locks prohibit another handle reading their byte.
        # Do not unlock ownership for hashing or fabricate a content digest.
        held_lock=relative in ('operator/operator.lock','reservations/global.lock')
        rows.append(dict(path=relative,kind=kind,
            logical_bytes=str(fingerprint[3] if kind=='file' else 0),
            observation_kind='metadata-only-held-lock' if held_lock else 'hashed-default-stream',
            sha256=_hash_file(root/relative,fingerprint,deadline) if kind=='file' and not held_lock else None))
    _require(_walk(root,bounds,deadline)==(nodes,files,total),'growth prefix changed')
    _require(_ancestors(root/'probe',deadline)==ancestors,'growth namespace changed')
    after_capacity=_caller_capacity(root,deadline)
    for capacity in (before_capacity,after_capacity):
        _require(int(capacity['caller_available_bytes'])-pending_physical>=20*1024**3,
            'caller capacity minus retained storage below original floor')
    # Namespace-only diagnostic observation, NOT a global research-root audit.
    _require(total+pending_research<=25*1024**3,'diagnostic research bound exceeded')
    return dict(schema='alc-r0-diagnostic-growth-prefix-v1',domain=_DOMAIN,
        request_root=request_root,prefix_owner_root=owner_root,
        accounting_kind='full-declarations-held-no-materialization-credit',
        logical_kind='default-stream-prefix-only',physical_materialization_kind='unknown',
        prefix_inventory=rows,prefix_logical_bytes=str(total),
        pending_research_bytes=str(pending_research),pending_physical_bytes=str(pending_physical),
        capacity_before=before_capacity,capacity_after=after_capacity,
        unmeasured_publication_tail=['diagnostic.growth.json','reservations/**','diagnostic.result.json'],
        finished_monotonic_ns=str(time.monotonic_ns()))


def _channel_check(deadline,cancel):
    _check_deadline(deadline)
    if cancel is not None and cancel.is_set(): raise _ChannelCancelled('native channel cancelled')


def _channel_ready(channel,deadline,cancel,*,writing=False):
    _channel_check(deadline,cancel)
    wait=min(.02,max(0,(deadline-time.monotonic_ns())/1e9))
    readable,writable,errors=select.select([] if writing else [channel],
        [channel] if writing else [],[channel],wait)
    _channel_check(deadline,cancel)
    _require(not errors,'native channel exception')
    return bool(writable if writing else readable)


def _send_frame(channel,value,deadline,cancel=None):
    payload=canonical_json_bytes(value)
    _require(0<len(payload)<=8192,'native frame exceeds fixed cap')
    data=len(payload).to_bytes(4,'big')+payload; offset=0
    while offset<len(data):
        if not _channel_ready(channel,deadline,cancel,writing=True): continue
        try: count=channel.send(memoryview(data)[offset:])
        except BlockingIOError: continue
        _channel_check(deadline,cancel)
        _require(count>0,'native channel send closed')
        offset+=count


def _receive_frame(channel,deadline,cancel=None):
    def receive(size):
        data=bytearray()
        while len(data)<size:
            if not _channel_ready(channel,deadline,cancel): continue
            try: part=channel.recv(size-len(data))
            except BlockingIOError: continue
            _channel_check(deadline,cancel)
            if not part: raise _ChannelClosed('native channel EOF/truncation')
            data.extend(part)
        return bytes(data)
    size=int.from_bytes(receive(4),'big')
    _require(0<size<=8192,'native frame length exceeds fixed cap')
    value=_bounded_json(receive(size),8192)
    _channel_check(deadline,cancel)
    try: surplus=channel.recv(1,socket.MSG_PEEK)
    except BlockingIOError: surplus=None
    if surplus==b'': raise _ChannelClosed('native channel peer EOF')
    _require(surplus is None,'unexpected pipelined frame')
    return value


def _temporary_namespace(value,deadline,*,empty):
    path=_local_path(value)
    _ancestors(path/'probe',deadline)
    _require(path.is_dir() and path.resolve(strict=True)==path,'ordinary existing namespace required')
    temp=Path(tempfile.gettempdir()).resolve(strict=True)
    _require(path!=temp and path.is_relative_to(temp),'diagnostic namespace must be below system TEMP')
    if empty:
        with os.scandir(path) as entries:
            _require(next(entries,None) is None,'diagnostic namespace already consumed')
    return path


@dataclass(frozen=True,slots=True)
class _Execution:
    namespace: Path
    entry: int
    useful: int
    cleanup: int
    installation: str
    generation: str
    clock: str
    request: bytes
    request_root: str
    declaration: bytes


def _prepare(namespace,entry,scenario):
    _require(type(scenario) is str and scenario in _SCENARIOS,'closed diagnostic scenario required')
    useful=entry+15*_NS; cleanup=useful+10*_NS
    namespace=_temporary_namespace(namespace,useful,empty=True)
    descriptor=dict(schema='alc-r0-diagnostic-installation-v1',domain=_DOMAIN,scenario=scenario,
        namespace=str(namespace),entry_monotonic_ns=str(entry),
        useful_deadline_monotonic_ns=str(useful),cleanup_deadline_monotonic_ns=str(cleanup))
    installation=_fresh(namespace/'diagnostic.installation.json',descriptor,useful)
    generation=sha256_bytes(canonical_json_bytes(dict(domain=_DOMAIN,installation_root=installation)))
    clock=sha256_bytes(canonical_json_bytes(dict(domain=_DOMAIN,entry_monotonic_ns=str(entry))))
    request=canonical_json_bytes(dict(schema='alc-r0-diagnostic-request-v1',domain=_DOMAIN,
        installation_root=installation,generation_root=generation,clock_domain_root=clock,
        namespace=str(namespace),reservation_id='diagnostic-work',run_id=_DIAGNOSTIC_ID,
        entry_monotonic_ns=str(entry),useful_deadline_monotonic_ns=str(useful)))
    declaration=canonical_json_bytes(dict(experiment_id='alc-r0-smollm2-135m-v1',
        reservation_id='diagnostic-work',run_id=_DIAGNOSTIC_ID,attempt_id='a001',segment='initial',
        declaration_root=sha256_bytes(request),device='cpu',useful_wall_ceiling_ns=str(15*_NS),
        cleanup_ceiling_ns=str(10*_NS),charge_envelope_ns=str(25*_NS),gpu_reservation_ns='0',
        research_growth_bytes=str(1<<20),physical_growth_bytes=str(1<<20),
        stdout_limit_bytes='16384',stderr_limit_bytes='16384'))
    spec=_Execution(namespace,entry,useful,cleanup,installation,generation,clock,
                    request,sha256_bytes(request),declaration)
    _fresh(namespace/'diagnostic.request.json',parse_canonical_json(request),useful)
    _fresh(namespace/'declaration.json',parse_canonical_json(declaration),useful)
    operator=namespace/'operator'; operator.mkdir()
    status=decode_operator_status(canonical_json_bytes(dict(schema='alc-r0-operator-status-v1',
        installation_root=installation,generation_root=generation,sequence='1',revoked=False,
        expires_utc_ns=str(time.time_ns()+60*_NS))))
    StatusPublicationStore(operator,installation,generation).publish(
        prepare_status_intent(None,status),deadline_ns=useful)
    return spec


def _verify(spec,lease=None):
    _require(type(spec) is _Execution,'fixed internal execution required')
    root=_temporary_namespace(spec.namespace,spec.useful,empty=False)
    descriptor=_read(root/'diagnostic.installation.json',spec.useful)
    _require(descriptor['domain']==_DOMAIN and descriptor['namespace']==str(root)
        and sha256_bytes(canonical_json_bytes(descriptor))==spec.installation,'diagnostic origin differs')
    request=_read(root/'diagnostic.request.json',spec.useful)
    _require(canonical_json_bytes(request)==spec.request and request['domain']==_DOMAIN,'request differs')
    declaration=_read(root/'declaration.json',spec.useful)
    _require(canonical_json_bytes(declaration)==spec.declaration,'declaration differs')
    claim=_read(root/'diagnostic.consumed.json',spec.useful)
    expected=dict(domain=_DOMAIN,request_root=spec.request_root,**{key:declaration[key]
        for key in ('reservation_id','run_id','attempt_id','segment','declaration_root')})
    _require(claim==expected,'consumption differs')
    status=read_committed_operator_status(root/'operator',spec.installation,spec.generation,
                                          deadline_ns=spec.useful)
    _require(not status.revoked and status.expires_utc_ns>time.time_ns()+spec.cleanup-time.monotonic_ns(),
             'diagnostic status revoked/expired')
    if lease is not None:
        lease._check_stop(); lease._unexpired()
        if lease._state=='READY':
            binding=_read(root/'diagnostic.child.json',spec.useful)
            _require(binding['identity']==_identity(lease.identity)
                and binding['ready_owner_root']==lease._ready_root
                and binding['request_root']==spec.request_root,'held READY binding differs')
    _check_deadline(spec.useful)


def _identity(value):
    # FILETIME exceeds RFC8785 safe numeric integers: preserve exact decimal.
    return dict(pid=str(value.pid),creation_filetime_100ns=str(value.creation_filetime_100ns),
        owner_nonce=value.owner_nonce,receipt_root=value.receipt_root)


class _SharedTail:
    """One synchronized cleanup clock; neither owner may renew the tail."""
    def __init__(self,upper):
        self.upper=upper; self.deadline=None; self.lock=threading.Lock()

    def pin(self,limit=None):
        with self.lock:
            bound=min(self.upper,time.monotonic_ns()+10*_NS)
            if limit is not None: bound=min(bound,limit)
            self.deadline=bound if self.deadline is None else min(self.deadline,bound)
            return self.deadline

    def current(self):
        with self.lock: return self.upper if self.deadline is None else self.deadline


class _NativeActuator:
    """Private same-job action only. No filesystem, journal or lease mutation."""
    def __init__(self,lease):
        import _winapi
        self.signal=lease._stop_signal; self.tail=lease._shared_tail; self.useful=lease._deadline
        self.kernel=lease._job.kernel; self.finish=threading.Event(); self.error=None
        self.job=self.process=None; self.finished=None; self.terminated=False; self.drained=False
        self.closed=False; self.started=False; self.pid=lease._identity.pid; self.close_error=None
        self.thread=threading.Thread(target=self._run,name='alc-r0-native-stop',daemon=False)
        self._source_job=lease._job.handle; self._source_process=lease._information.process

    def _acquire(self):
        import _winapi
        current=_winapi.GetCurrentProcess()
        try:
            self.job=_winapi.DuplicateHandle(current,self._source_job,current,0,False,_winapi.DUPLICATE_SAME_ACCESS)
            self.process=_winapi.DuplicateHandle(current,self._source_process,current,0,False,_winapi.DUPLICATE_SAME_ACCESS)
        except BaseException as error:
            # The lease already retains this actuator, including partial handles.
            self.error=error
            raise
        finally: self._source_job=self._source_process=None

    def _counts(self):
        value=_Accounting()
        _checked(self.kernel.QueryInformationJobObject(self.job,1,ctypes.byref(value),ctypes.sizeof(value),None))
        return value

    def start(self):
        try:
            self._acquire(); self.started=True; self.thread.start()
        except BaseException as error:
            self.error=error; OwnedStopSignal.request_stop(self.signal)
            self.close(); raise

    def _run(self):
        import _winapi
        try:
            while not self.finish.is_set() and not OwnedStopSignal._requested(self.signal):
                if time.monotonic_ns()>=self.useful:
                    OwnedStopSignal.request_stop(self.signal); break
                self.finish.wait(.01)
            self.tail.pin()
            if self._counts().active_processes:
                _check_deadline(self.tail.current())
                _checked(self.kernel.TerminateJobObject(self.job,124)); self.terminated=True
            while self._counts().active_processes or _winapi.WaitForSingleObject(self.process,0)!=0:
                _check_deadline(self.tail.current()); time.sleep(.005)
            _check_deadline(self.tail.current()); self.drained=True
        except BaseException as error:
            self.error=error; OwnedStopSignal.request_stop(self.signal)
        finally: self.finished=time.monotonic_ns()

    def check(self):
        if self.error is not None: raise CoordinatorError('native actuator failed') from self.error
        _require(self.started and self.thread.is_alive(),'native actuator unexpectedly terminal')

    def close(self):
        # Failure reporting is absorbing, cleanup attempts are not disabled.
        # Reap any now-terminal thread/remaining handles under the SAME deadline.
        try: self._close_owned()
        except BaseException as error:
            if self.close_error is None: self.close_error=error
            OwnedStopSignal.request_stop(self.signal)
        if self.close_error is not None:
            OwnedStopSignal.request_stop(self.signal)
            raise CoordinatorError('native actuator cleanup previously failed') from self.close_error

    def _close_owned(self):
        import _winapi
        deadline=self.tail.pin(); self.finish.set()
        if self.thread.ident is not None: self.thread.join(max(0,deadline-time.monotonic_ns())/1e9)
        _require(not self.thread.is_alive(),'native actuator join unconfirmed')
        if not self.closed:
            try:
                if self.process is not None: _winapi.CloseHandle(self.process); self.process=None
            finally:
                if self.job is not None: _winapi.CloseHandle(self.job); self.job=None
            self.closed=True
        if self.error is not None: raise CoordinatorError('native actuator failed') from self.error
        _require(self.thread.ident is None or self.drained and self.finished<=deadline,
            'native actuator terminal observation unconfirmed')

    def report(self):
        return dict(domain=_DOMAIN,pid=str(self.pid),terminated=self.terminated,drained=self.drained,
            thread_alive=self.thread.is_alive(),duplicate_handles_closed=self.closed,
            finished_monotonic_ns=str(self.finished),cleanup_deadline_monotonic_ns=str(self.tail.current()))


def _cleanup_bound(spec,lease):
    if lease is None: return spec.cleanup
    bound=min(spec.cleanup,lease._shared_tail.current())
    return bound if lease._cleanup_deadline is None else min(bound,lease._cleanup_deadline)


def _in_job(process,job):
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.IsProcessInJob.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.POINTER(ctypes.c_int)]
    kernel.IsProcessInJob.restype=ctypes.c_int
    result=ctypes.c_int()
    _checked(kernel.IsProcessInJob(process,job,ctypes.byref(result)))
    return bool(result.value)


def _retain_diagnostic_descendant(spec,lease,owned):
    """Fixture corroboration only; never used to choose actuator targets."""
    import _winapi
    value=_read(spec.namespace/'descendant.started.json',spec.useful)
    _require(type(value) is dict and set(value)=={'domain','request_root','pid',
        'creation_filetime_100ns','parent_pid'} and all(type(item) is str for item in value.values()),
        'exact diagnostic descendant identity required')
    _require(value['domain']==_DOMAIN and value['request_root']==spec.request_root
        and value['parent_pid']==str(lease.identity.pid),'descendant origin differs')
    pid=int(value['pid'])
    _require(0<pid<2**32 and str(pid)==value['pid'],'canonical descendant PID required')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32]
    kernel.OpenProcess.restype=ctypes.c_void_p
    delayed=_read(spec.namespace/'diagnostic.installation.json',spec.useful)['scenario']=='tree-validation-delay'
    handle=_checked(kernel.OpenProcess(0x00100400,False,pid))  # query + synchronize, no terminate right
    owned.callback(_close_diagnostic_descendant,spec,lease,handle,value['pid'],delayed)
    _require(str(_creation_time(handle))==value['creation_filetime_100ns'],
        'descendant native creation identity differs')
    _require(_in_job(handle,lease._job.handle),'descendant not in actual worker job')
    _require(_winapi.WaitForSingleObject(handle,0)==258,'descendant not actually live')
    return handle,value


def _close_diagnostic_descendant(spec,lease,handle,pid,delayed=False):
    import _winapi
    failure=None
    try:
        if delayed:
            started=time.monotonic_ns()
        OwnedStopSignal.request_stop(lease._stop_signal)
        bound=lease._pin_cleanup_deadline()
        if delayed:
            before,root_before,descendant_before,before_sample=lease._diagnostic_cleanup_before
    except BaseException as error: failure=error
    finally:
        try: _winapi.CloseHandle(handle)
        except BaseException as error:
            if failure is None: failure=error
    if failure is not None: raise failure
    # Negative-diagnostic teardown only: cancellation/tail pin precede I/O.
    # A blocked receipt write must not postpone independent native actuation.
    if delayed:
        # Closed owner-unavailability fault BEFORE publication; not simulated
        # native API failure or a claim that filesystem I/O actually blocked.
        while time.monotonic_ns()<started+600_000_000:
            _check_deadline(bound)
            time.sleep(max(0,(started+600_000_000-time.monotonic_ns())/1e9))
        after=lease._job.accounting().active_processes
        root_after=_winapi.WaitForSingleObject(lease._information.process,0)
        sampled=time.monotonic_ns()
        _fresh(spec.namespace/'early.cleanup.observed.json',dict(domain=_DOMAIN,
            request_root=spec.request_root,validation_result=lease._diagnostic_validation_result,
            before_active=before,after_active=after,root_before_wait=root_before,
            root_after_wait=root_after,descendant_before_wait=descendant_before,
            stop_requested=OwnedStopSignal._requested(lease._stop_signal),
            started_monotonic_ns=str(started),sampled_monotonic_ns=str(sampled),
            before_sampled_monotonic_ns=str(before_sample),
            cleanup_deadline_monotonic_ns=str(bound)),bound)
    _fresh(spec.namespace/'descendant.handle.closed.json',dict(domain=_DOMAIN,
        request_root=spec.request_root,pid=pid,handle_closed=True,
        finished_monotonic_ns=str(time.monotonic_ns()),cleanup_deadline_monotonic_ns=str(bound)),bound)


class _FixedLease(ReservedOwnedLease):
    def __init__(self,spec,**arguments):
        _require(type(spec) is _Execution,'internal execution required')
        self._execution=spec; self._shared_tail=_SharedTail(spec.cleanup); self._actuator=None
        self._fixed_close_error=None
        super().__init__(**arguments)

    def _pin_cleanup_deadline(self):
        self._cleanup_deadline=self._shared_tail.pin(self._cleanup_deadline)
        if self._job is not None: self._job.cleanup_deadline_ns=self._cleanup_deadline
        return self._cleanup_deadline

    def start_actuator(self):
        _require(self._actuator is None,'native actuator single use')
        self._actuator=_NativeActuator(self)
        scenario=_read(self._execution.namespace/'diagnostic.installation.json',self._execution.useful)['scenario']
        if scenario in ('actuator-query-denied','actuator-terminate-denied'):
            # Closed diagnostic only: same owned Job, actual reduced access.
            import _winapi
            current=_winapi.GetCurrentProcess()
            access=0x0008 if scenario=='actuator-query-denied' else 0x0004
            restricted=_winapi.DuplicateHandle(current,self._job.handle,current,access,False,0)
            try:
                self._actuator._source_job=restricted
                self._actuator.start()
            finally: _winapi.CloseHandle(restricted)
        else: self._actuator.start()

    def _before_create(self):
        _verify(self._execution,self)
        _capacity_stage(self._execution,'work',self._output,'before-create')

    def _before_resume(self):
        _verify(self._execution,self)
        _require(self._actuator is not None,'native actuator required before resume')
        self._actuator.check()
        _capacity_stage(self._execution,'work',self._output,'before-resume')

    def _new_output(self,**arguments):
        return _AllocatedLeaseOutput(self,**arguments)

    def _create_owned_process(self,stdin):
        started=time.monotonic_ns()
        super()._create_owned_process(stdin)
        finished=time.monotonic_ns()
        _action_observed(self._execution,'work','create',self._information,started,finished)

    def _resume_owned_process(self):
        started=time.monotonic_ns()
        super()._resume_owned_process()
        finished=time.monotonic_ns()
        _action_observed(self._execution,'work','resume',self._information,started,finished)

    def _close(self):
        import _winapi
        if self._state=='CLOSED':
            # Base state closes admission, not necessarily actuator resources.
            # Retry only its separately owned resources; never republish receipts
            # or query original base handles which may already have been closed.
            try:
                if self._actuator is not None: self._actuator.close()
            except BaseException as error:
                if self._fixed_close_error is None: self._fixed_close_error=error
            if self._fixed_close_error is not None: raise self._fixed_close_error
            return
        receipt=None; forced=False; failure=None; resources_closed=False
        # Retain the first failure, but still attempt independent owner cleanup.
        # Physical cleanup evidence does NOT clear the failed execution.
        try:
            if self._actuator is not None: self._actuator.close()
        except BaseException as error: failure=error
        try:
            if self._job is not None and self._information.process:
                self._pin_cleanup_deadline()
                active=bool(self._job.accounting().active_processes)
                forced=active or self._actuator is not None and self._actuator.terminated
                if active: self._job.terminate_and_drain()
                _require(_winapi.WaitForSingleObject(self._information.process,self._job.remaining_cleanup_ms())==0,
                         'work cleanup root unobserved')
                counts=self._job.accounting()
                _require(counts.active_processes==0,'work cleanup tree unobserved')
                receipt=OwnedProcessReceipt(self._information.pid,_winapi.GetExitCodeProcess(self._information.process),
                    False,self._started,time.monotonic_ns(),counts.total_processes,counts.active_processes,
                    counts.user_time,counts.kernel_time)
        except BaseException as error:
            if failure is None: failure=error
        finally:
            try:
                super()._close(); resources_closed=True
            except BaseException as error:
                if failure is None: failure=error
        try:
            if receipt is not None and resources_closed:
                _fresh(self._execution.namespace/'work.cleanup.native.json',dict(domain=_DOMAIN,
                    forced=forced,receipt=asdict(receipt),cleanup_deadline_monotonic_ns=str(self._cleanup_deadline)),
                    self._cleanup_deadline)
            if self._actuator is not None and resources_closed:
                _fresh(self._execution.namespace/'actuator.native.json',self._actuator.report(),self._cleanup_deadline)
        except BaseException as error:
            if failure is None: failure=error
        self._fixed_close_error=failure
        if failure is not None: raise failure


def _command(role,spec):
    # Diagnostic only: direct installed base image avoids venv redirector PID.
    executable=Path(sys._base_executable).resolve(strict=True)
    _require(executable.is_file(),'actual diagnostic interpreter unavailable')
    return (str(executable),'-B','-m',_MODULE,role,str(spec.namespace),spec.installation)


def _environment():
    import rfc8785
    environment=os.environ.copy()
    source=Path(__file__).resolve().parents[2]
    package=Path(rfc8785.__file__).resolve().parents[1]
    environment.update(PYTHONPATH=os.pathsep.join((str(source),str(package))),
        PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='-1',
        HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1')
    environment.pop('PYTHONHOME',None)
    return environment


def _append(store,owner,kind,evidence,deadline,**fields):
    _check_deadline(deadline)
    prior=store.read(owner)
    event=canonical_json_bytes(dict(sequence=str(prior.snapshot.event_count+1),
        previous_root=prior.snapshot.root,reservation_id='diagnostic-work',kind=kind,
        evidence_root=evidence,**fields))
    result=store.commit(store.prepare(owner,event,evidence))
    _check_deadline(deadline)
    return result


class _Observer:
    """Actual owned observer process, same original envelope; no reader thread."""
    def __init__(self,spec):
        self.spec=spec; self.stack=ExitStack(); self.information=_ProcessInformation()
        self.job=None; self.output=None; self.started=None; self.closed=False; self.close_error=None
        self.closed_receipt=None
        self.channel=None; self.child_channel=None

    def start(self):
        import _winapi
        try:
            self.channel,self.child_channel=socket.socketpair()
            self.stack.callback(self.channel.close)
            self.stack.callback(self.child_channel.close)
            self.channel.setblocking(False)
            self.job=self.stack.enter_context(_Job()); self.job.cleanup_deadline_ns=self.spec.cleanup
            self.output=self.stack.enter_context(_AllocatedOutputPair(
                stdout_path=self.spec.namespace/'observer.stdout',stderr_path=self.spec.namespace/'observer.stderr',
                stdout_limit_bytes=16384,stderr_limit_bytes=16384,cleanup_deadline_ns=self.spec.cleanup))
            stdin=self.stack.enter_context(open(os.devnull,'rb'))
            self.started=time.monotonic_ns(); _verify(self.spec)
            _capacity_stage(self.spec,'observer',self.output,'before-create')
            try:
                action_started=time.monotonic_ns()
                _create_suspended(_command('observer',self.spec),self.spec.namespace,_environment(),stdin,
                    self.output.stdout,self.output.stderr,self.spec.useful,self.job,self.information)
                action_finished=time.monotonic_ns()
                _action_observed(self.spec,'observer','create',self.information,action_started,action_finished)
            finally: self.output.close_parent_writers()
            self.creation=_creation_time(self.information.process)
            bootstrap=dict(schema='diagnostic-socket-share-v1',
                domain=_DOMAIN,role='observer',request_root=self.spec.request_root,
                pid=str(self.information.pid),creation_filetime_100ns=str(self.creation),
                share=base64.b64encode(self.child_channel.share(self.information.pid)).decode('ascii'))
            scenario=_read(self.spec.namespace/'diagnostic.installation.json',self.spec.useful)['scenario']
            if scenario=='bootstrap-conflict':
                _fresh(self.spec.namespace/'observer.channel.json',dict(domain=_DOMAIN,
                    diagnostic_fault='exclusive-bootstrap-conflict'),self.spec.useful)
            elif scenario=='bootstrap-wrong-role': bootstrap['role']='worker'
            _fresh(self.spec.namespace/'observer.channel.json',bootstrap,self.spec.useful)
            _capacity_stage(self.spec,'observer',self.output,'before-resume')
            _check_deadline(self.spec.useful)
            action_started=time.monotonic_ns(); _resume(self.information.thread)
            action_finished=time.monotonic_ns()
            _action_observed(self.spec,'observer','resume',self.information,action_started,action_finished)
            until=min(self.spec.useful,time.monotonic_ns()+2*_NS)
            while not (self.spec.namespace/'observer.ready.json').exists():
                _require(_winapi.WaitForSingleObject(self.information.process,0)==258,
                    'observer exited before native channel readiness')
                _check_deadline(until); time.sleep(.005)
            ready=_read(self.spec.namespace/'observer.ready.json',until)
            _require(ready==dict(pid=str(self.information.pid),creation_filetime_100ns=str(self.creation),
                domain=_DOMAIN,request_root=self.spec.request_root),'observer actual identity differs')
            self.child_channel.close()
            return self
        except BaseException:
            self.close(); raise

    def finish(self,deadline):
        import _winapi
        self.job.cleanup_deadline_ns=min(self.spec.cleanup,deadline)
        if not (self.spec.namespace/'observer.stop.json').exists():
            _fresh(self.spec.namespace/'observer.stop.json',dict(domain=_DOMAIN),deadline)
        while self.job.accounting().active_processes:
            _check_deadline(deadline)
            _require(not self.output.violated,'observer output overflow')
            time.sleep(.005)
        _require(_winapi.WaitForSingleObject(self.information.process,0)==0,'observer root not terminal')
        counts=self.job.accounting()
        self.output.finish(deadline)
        result=OwnedProcessReceipt(self.information.pid,_winapi.GetExitCodeProcess(self.information.process),
            False,self.started,time.monotonic_ns(),counts.total_processes,counts.active_processes,
            counts.user_time,counts.kernel_time)
        self.close()
        return result

    def close(self):
        try: return self._close_owned()
        except BaseException as error:
            self.close_error=error; raise

    def _close_owned(self):
        import _winapi
        if self.closed:
            if self.close_error is not None: raise CoordinatorError('observer cleanup previously failed') from self.close_error
            return self.closed_receipt
        self.closed=True
        try:
            # Information is preallocated: retain handles even if CreateProcess
            # succeeded but its helper's return/cleanup raised. Drain FIRST.
            if self.job is not None:
                active=self.job.accounting().active_processes
                if active: self.job.terminate_and_drain()
                if self.information.process:
                    _require(_winapi.WaitForSingleObject(self.information.process,self.job.remaining_cleanup_ms())==0,
                             'observer cleanup root unobserved')
                    counts=self.job.accounting()
                    _require(counts.active_processes==0,'observer cleanup tree unobserved')
                    self.closed_receipt=OwnedProcessReceipt(self.information.pid,
                        _winapi.GetExitCodeProcess(self.information.process),False,self.started,
                        time.monotonic_ns(),counts.total_processes,counts.active_processes,
                        counts.user_time,counts.kernel_time)
        except BaseException as error:
            self.close_error=error; raise
        finally:
            try:
                try:
                    if self.information.thread:
                        _winapi.CloseHandle(self.information.thread); self.information.thread=None
                finally:
                    if self.information.process:
                        _winapi.CloseHandle(self.information.process); self.information.process=None
            finally:
                try: self.stack.close()
                except BaseException as error:
                    self.close_error=error; raise
        if self.closed_receipt is not None:
            _fresh(self.spec.namespace/'observer.cleanup.native.json',dict(domain=_DOMAIN,
                forced=bool(active),receipt=asdict(self.closed_receipt),
                parent_socket_closed=self.channel is None or self.channel.fileno()==-1,
                surplus_socket_closed=self.child_channel is None or self.child_channel.fileno()==-1,
                cleanup_deadline_monotonic_ns=str(self.job.cleanup_deadline_ns)),self.job.cleanup_deadline_ns)
        return self.closed_receipt


def _service(spec,watch,consumer,observer,cancel,observations):
    try:
        consumer._bind(watch)  # owner check precedes source-state mutation
        consumer._bind_source(spec.namespace/'operator','committed')
        return _service_owned(spec,watch,consumer,observer,cancel,observations)
    except BaseException:
        consumer._deny(); raise


def _observer_live(observer):
    import _winapi
    _require(type(observer) is _Observer and not observer.closed
        and _winapi.WaitForSingleObject(observer.information.process,0)==258
        and _creation_time(observer.information.process)==observer.creation,
        'owned observer identity/liveness differs')


def _service_owned(spec,watch,consumer,observer,cancel,observations):
    consumer._bind(watch)
    request=watch.wait_request(.02)
    if request is None:
        consumer._active(); return
    deadline=min(spec.useful,request.started_monotonic_ns+OBSERVATION_NS)
    _observer_live(observer)
    _require(1<=request.sequence<=64,'fixed runtime message count exceeded')
    _send_frame(observer.channel,dict(sequence=str(request.sequence),
        started_monotonic_ns=str(request.started_monotonic_ns),request_root=spec.request_root),deadline,cancel)
    response=_receive_frame(observer.channel,deadline,cancel)
    _require(type(response) is dict and set(response)=={'sequence','request_root',
        'request_started_monotonic_ns','observed_monotonic_ns','utc_upper_ns','status',
        'observer_pid','observer_creation_filetime_100ns'},'exact observer response fields required')
    _require(all(type(value) is str for value in response.values()),'exact observer response types required')
    _require(response['sequence']==str(request.sequence),'observer response sequence differs')
    for key in ('observed_monotonic_ns','utc_upper_ns'):
        value=response[key]
        _require(value.isascii() and value.isdecimal() and value==str(int(value))
            and 0<int(value)<2**63,'canonical positive signed64 observation required')
    _require(response['request_root']==spec.request_root,'observer response request differs')
    _require(response['request_started_monotonic_ns']==str(request.started_monotonic_ns)
        and response['observer_pid']==str(observer.information.pid)
        and response['observer_creation_filetime_100ns']==str(observer.creation),
        'observer native/request correspondence differs')
    captured=int(response['observed_monotonic_ns'])
    _require(request.started_monotonic_ns<=captured<=time.monotonic_ns()<deadline,
             'original observation window differs')
    status=decode_operator_status(response['status'].encode('utf-8'))
    observation=consumer.consume(status,observed_monotonic_ns=captured,utc_upper_ns=int(response['utc_upper_ns']))
    _check_deadline(deadline); _observer_live(observer)
    watch.submit(request,observation); _check_deadline(deadline); consumer._active()
    observations.append(dict(sequence=str(request.sequence),started_monotonic_ns=str(request.started_monotonic_ns),
        observed_monotonic_ns=str(captured),submitted_monotonic_ns=str(time.monotonic_ns())))


class _Bridge:
    """One consumer owner; no filesystem calls in this non-daemon thread."""
    def __init__(self,spec,watch,observer,signal):
        self.spec,self.watch,self.observer,self.signal=spec,watch,observer,signal
        self.cancel=threading.Event(); self.ready=threading.Event(); self.first=threading.Event()
        self.observations=[]; self.error=None; self.finished=None; self.close_deadline=None
        self.thread=threading.Thread(target=self._run,name='alc-r0-diagnostic-bridge',daemon=False)

    def _run(self):
        try:
            consumer=StatusWatchConsumer(self.spec.installation,self.spec.generation,self.spec.clock,self.signal)
            consumer._bind(self.watch)
            consumer._bind_source(self.spec.namespace/'operator','committed')
            self.ready.set()
            while not self.cancel.is_set():
                _service(self.spec,self.watch,consumer,self.observer,self.cancel,self.observations)
                if self.observations: self.first.set()
        except _ChannelCancelled as error:
            if not self.cancel.is_set():
                self.error=error; OwnedStopSignal.request_stop(self.signal)
        except BaseException as error:
            # A concurrent quiesce must not erase protocol/status/deadline errors.
            self.error=error; OwnedStopSignal.request_stop(self.signal)
        finally:
            self.finished=time.monotonic_ns(); self.ready.set(); self.first.set()

    def start(self):
        try:
            self.thread.start()
            bound=min(self.spec.useful,time.monotonic_ns()+OBSERVATION_NS)
            while not self.first.wait(.005): _check_deadline(bound)
            self.check()
            _require(bool(self.observations),'bridge initial observation missing')
            return self
        except BaseException:
            OwnedStopSignal.request_stop(self.signal); self.close(self.spec.cleanup); raise

    def check(self):
        if self.error is not None: raise CoordinatorError('observer bridge failed') from self.error
        _require(self.thread.is_alive() and not self.cancel.is_set(),'observer bridge unexpectedly terminal')

    def quiesce(self,deadline):
        self.close_deadline=deadline if self.close_deadline is None else min(deadline,self.close_deadline)
        self.cancel.set()
        if self.thread.ident is not None:
            self.thread.join(max(0,self.close_deadline-time.monotonic_ns())/1e9)
        _require(not self.thread.is_alive(),'native bridge join unconfirmed')
        _require(self.finished is None or self.finished<=self.close_deadline,'bridge closure exceeded original bound')
        if self.error is not None: raise CoordinatorError('observer bridge failed') from self.error

    def close(self,deadline):
        self.cancel.set()
        try: self.observer.channel.shutdown(socket.SHUT_RDWR)
        except OSError as error:
            if self.observer.channel.fileno()!=-1 and getattr(error,'winerror',None) not in (10038,10057):
                if self.error is None: self.error=error
        try: self.quiesce(deadline)
        finally:
            if not self.thread.is_alive(): self.observer.channel.close()


def _roles(role,namespace,installation):
    # Harmless process protocol only. These roles cannot import scientific worker.
    entry=time.monotonic_ns(); root=_temporary_namespace(namespace,entry+2*_NS,empty=False)
    descriptor=_read(root/'diagnostic.installation.json',entry+2*_NS)
    _require(sha256_bytes(canonical_json_bytes(descriptor))==installation
        and descriptor['domain']==_DOMAIN,'diagnostic role origin differs')
    deadline=int(descriptor['useful_deadline_monotonic_ns'])
    request=_read(root/'diagnostic.request.json',deadline); request_root=sha256_bytes(canonical_json_bytes(request))
    _require(request['domain']==_DOMAIN and request['installation_root']==installation,'role request differs')
    identity=dict(pid=str(os.getpid()),creation_filetime_100ns=str(_creation_time(ctypes.c_void_p(-1))))
    if role=='observer':
        bootstrap=_read(root/'observer.channel.json',deadline)
        _require(type(bootstrap) is dict and set(bootstrap)=={'schema','domain','role','request_root',
            'pid','creation_filetime_100ns','share'},'exact native bootstrap fields required')
        _require(bootstrap['schema']=='diagnostic-socket-share-v1' and bootstrap['domain']==_DOMAIN
            and bootstrap['role']=='observer' and bootstrap['request_root']==request_root
            and all(bootstrap[key]==value for key,value in identity.items()),'native bootstrap identity differs')
        _require(type(bootstrap['share']) is str and len(bootstrap['share'])<=4096,'bounded native share required')
        with socket.fromshare(base64.b64decode(bootstrap['share'],validate=True)) as channel:
            channel.setblocking(False)
            _fresh(root/'observer.ready.json',dict(**identity,domain=_DOMAIN,request_root=request_root),deadline)
            last=0; cancellation=_ObserverStop(root,deadline)
            while not cancellation.is_set():
                _check_deadline(deadline)
                if (descriptor['scenario'] in ('busy-revocation','busy-tree-revocation')
                        and (root/'revocation.arm.json').exists()
                        and not (root/'revocation.published.json').exists()):
                    arm=_read(root/'revocation.arm.json',deadline)
                    _require(arm['domain']==_DOMAIN and arm['request_root']==request_root,
                        'diagnostic revocation request differs')
                    previous=read_committed_operator_status(root/'operator',installation,
                        request['generation_root'],deadline_ns=deadline)
                    candidate=parse_canonical_json(previous.data)
                    candidate.update(sequence=str(previous.sequence+1),revoked=True)
                    revoked=decode_operator_status(canonical_json_bytes(candidate))
                    StatusPublicationStore(root/'operator',installation,request['generation_root']).publish(
                        prepare_status_intent(previous,revoked),deadline_ns=deadline)
                    _fresh(root/'revocation.published.json',dict(domain=_DOMAIN,request_root=request_root,
                        status_root=revoked.root,published_monotonic_ns=str(time.monotonic_ns())),deadline)
                if (root/'observer.block.json').exists():
                    # A real blocking wait lives only in the owned, killable process.
                    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
                    kernel.CreateEventW.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_wchar_p]
                    kernel.CreateEventW.restype=ctypes.c_void_p
                    kernel.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
                    kernel.WaitForSingleObject.restype=ctypes.c_uint32
                    kernel.CloseHandle.argtypes=[ctypes.c_void_p]
                    handle=kernel.CreateEventW(None,True,False,None)
                    _require(bool(handle),'diagnostic native wait acquisition failed')
                    try: kernel.WaitForSingleObject(handle,0xffffffff)
                    finally: kernel.CloseHandle(handle)
                try:
                    available=_channel_ready(channel,deadline,cancellation)
                except _ChannelCancelled: return 0
                if not available: continue
                _require(last<64,'fixed observer request count exceeded')
                try: message=_receive_frame(channel,min(deadline,time.monotonic_ns()+OBSERVATION_NS),cancellation)
                except _ChannelCancelled: return 0
                except (_ChannelClosed,ConnectionResetError):
                    if cancellation.is_set(): return 0
                    raise
                _require(type(message) is dict and set(message)=={'sequence','started_monotonic_ns','request_root'}
                    and all(type(value) is str for value in message.values()),'exact observer request required')
                _require(message['sequence']==str(last+1) and message['request_root']==request_root,
                    'observer request sequence/root differs')
                started=message['started_monotonic_ns']
                _require(started.isascii() and started.isdecimal() and started==str(int(started))
                    and 0<int(started)<=time.monotonic_ns(),'canonical request start required')
                bound=min(deadline,int(started)+OBSERVATION_NS)
                status=read_committed_operator_status(root/'operator',installation,request['generation_root'],deadline_ns=bound)
                captured=time.monotonic_ns()
                try:
                    _send_frame(channel,dict(sequence=str(last+1),request_root=request_root,
                        request_started_monotonic_ns=started,observer_pid=identity['pid'],
                        observer_creation_filetime_100ns=identity['creation_filetime_100ns'],
                        observed_monotonic_ns=str(captured),utc_upper_ns=str(time.time_ns()),status=status.data.decode()),bound,cancellation)
                except _ChannelCancelled: return 0
                except ConnectionResetError:
                    if cancellation.is_set(): return 0
                    raise
                last+=1
        return 0
    if role=='descendant':
        _require(descriptor['scenario'] in ('busy-tree-revocation','tree-validation-delay'),
            'closed descendant scenario required')
        binding=_read(root/'diagnostic.child.json',deadline)
        _require(str(os.getppid())==binding['identity']['pid'] and binding['request_root']==request_root,
            'diagnostic descendant parent differs')
        _fresh(root/'descendant.started.json',dict(domain=_DOMAIN,request_root=request_root,
            parent_pid=str(os.getppid()),**identity),deadline)
        while True:
            _check_deadline(deadline); time.sleep(.01)
    _require(role=='worker','closed harmless role required')
    while not (root/'worker.start.json').exists():
        _check_deadline(deadline); time.sleep(.005)
    start=_read(root/'worker.start.json',deadline)
    binding=_read(root/'diagnostic.child.json',deadline)
    _require(start['request_root']==request_root and binding['request_root']==request_root,'worker request mismatch')
    _require(binding['identity']['pid']==identity['pid']
        and binding['identity']['creation_filetime_100ns']==identity['creation_filetime_100ns'],
        'worker actual root PID/FILETIME differs')
    declaration=_read(root/'declaration.json',deadline)
    role_spec=_Execution(root,int(descriptor['entry_monotonic_ns']),deadline,
        int(descriptor['cleanup_deadline_monotonic_ns']),installation,request['generation_root'],
        request['clock_domain_root'],canonical_json_bytes(request),request_root,canonical_json_bytes(declaration))
    _verify(role_spec)
    store=ReservationStore(root/'reservations',(canonical_json_bytes(declaration),))
    view=store.read(start['running_owner_root']).snapshot.reservations[0]
    _require(view.state=='RUNNING' and view.identity_receipt_root==binding['identity']['receipt_root'],
             'worker owned RUNNING correspondence differs')
    _require(view.pid==int(identity['pid']) and view.creation_filetime_100ns==int(identity['creation_filetime_100ns'])
        and view.owner_nonce==binding['identity']['owner_nonce'] and start['ready_owner_root']==binding['ready_owner_root'],
        'worker complete identity/READY correspondence differs')
    if descriptor['scenario'] in ('busy-tree-revocation','tree-validation-delay'):
        import subprocess
        descendant=subprocess.Popen(_command('descendant',role_spec),cwd=root,
            env=_environment(),stdin=subprocess.DEVNULL,close_fds=True)
        while not (root/'descendant.started.json').exists():
            _check_deadline(deadline)
            _require(descendant.poll() is None,'diagnostic descendant exited before readiness')
            time.sleep(.005)
        child_identity=_read(root/'descendant.started.json',deadline)
        _require(child_identity['pid']==str(descendant.pid)
            and child_identity['creation_filetime_100ns']==str(_creation_time(descendant._handle)),
            'spawned descendant native identity differs')
    _fresh(root/'child.started.json',dict(domain=_DOMAIN,request_root=request_root,**identity),deadline)
    if descriptor['scenario'] in ('blocked-observer','busy-revocation','busy-tree-revocation','tree-validation-delay',
                                'actuator-query-denied','actuator-terminate-denied'):
        while True:
            _check_deadline(deadline); time.sleep(.01)
    if descriptor['scenario']=='completion-conflict':
        _fresh(root/'diagnostic.result.json',dict(domain=_DOMAIN,
            marker='diagnostic-completion-conflict'),deadline)
    _fresh(root/'child.result.json',dict(schema='alc-r0-harmless-child-v1',domain=_DOMAIN,
        request_root=request_root,identity_receipt_root=view.identity_receipt_root,**identity),deadline)
    return 0


def _coordinate(namespace,entry,scenario):
    spec=_prepare(namespace,entry,scenario); root=spec.namespace
    reservation=root/'reservations'; reservation.mkdir(); (reservation/'intents').mkdir()
    store=ReservationStore(reservation,(spec.declaration,)); signal=OwnedStopSignal()
    observer=None; watch=None; lease=None; bridge=None
    try:
        with ExitStack() as owned:
            with deadline_file_lock(root/'operator'/'operator.lock',spec.useful):
                with deadline_file_lock(reservation/'global.lock',spec.useful):
                    initial=store.initialize(store.initialization_intent())
                    reserved=_append(store,initial.sha256,'reserve',spec.request_root,spec.useful,
                        declaration_root=spec.request_root,entry_utc_ns=str(time.time_ns()),clock_domain_root=spec.clock,
                        entry_monotonic_ns=str(entry),useful_deadline_monotonic_ns=str(spec.useful))
                    declaration=parse_canonical_json(spec.declaration)
                    _fresh(root/'diagnostic.consumed.json',dict(domain=_DOMAIN,request_root=spec.request_root,
                        **{key:declaration[key] for key in ('reservation_id','run_id','attempt_id','segment','declaration_root')}),spec.useful)
                    if scenario=='stale-before-create':
                        changed=parse_canonical_json(spec.request); changed['domain']='changed'
                        _replace(root/'diagnostic.request.json',changed,spec.useful)
                    lease=owned.enter_context(_FixedLease(spec,store=store,expected_owner_root=reserved.sha256,
                        reservation_id='diagnostic-work',command=_command('worker',spec),cwd=root,
                        environment=_environment(),stdout_path=root/'work.stdout',stderr_path=root/'work.stderr',
                        deadline_ns=spec.useful,clock_domain_root=spec.clock,stop_signal=signal))
                    try:
                        ready=lease.publish_identity(spec.request_root,spec.request_root)
                        lease.start_actuator()
                        _fresh(root/'diagnostic.child.json',dict(domain=_DOMAIN,request_root=spec.request_root,
                            ready_owner_root=ready.sha256,identity=_identity(lease.identity)),spec.useful)
                        observer=_Observer(spec).start()
                        watch=LiveAuthorityWatch(WatchPolicy(spec.generation,spec.clock,spec.useful,spec.cleanup),signal)
                        watch.start()
                        bridge=_Bridge(spec,watch,observer,signal)
                        bridge.start()
                        if scenario=='stale-before-resume':
                            changed=_read(root/'diagnostic.child.json',spec.useful)
                            changed['request_root']='b'*64
                            _replace(root/'diagnostic.child.json',changed,spec.useful)
                        if scenario=='output-capacity-lost':
                            destination=lease._output._streams[0].destination
                            before,_=_output_native(destination)
                            _set_output_allocation(destination,0)  # Actual owned native loss, not forged evidence.
                            after,_=_output_native(destination)
                            _fresh(root/'work.output.capacity-lost.json',dict(domain=_DOMAIN,
                                request_root=spec.request_root,before_allocation_bytes=str(before.allocation),
                                after_allocation_bytes=str(after.allocation)),spec.useful)
                        running=lease.resume_verified(ready.sha256)
                    except BaseException:
                        lease._close_after_failure(); raise
            if scenario=='slow-parent':
                # Closed harmless composition fault: main unavailable for more
                # than the ORIGINAL observation window. Never extend that window.
                blocked_start=time.monotonic_ns()
                while time.monotonic_ns()<blocked_start+600_000_000:
                    time.sleep(max(0,(blocked_start+600_000_000-time.monotonic_ns())/1e9))
                blocked_end=time.monotonic_ns()
                _fresh(root/'parent.delay.json',dict(domain=_DOMAIN,
                    started_monotonic_ns=str(blocked_start),finished_monotonic_ns=str(blocked_end)),spec.useful)
            _fresh(root/'worker.start.json',dict(domain=_DOMAIN,request_root=spec.request_root,
                ready_owner_root=ready.sha256,running_owner_root=running.sha256),spec.useful)
            if scenario in ('actuator-query-denied','actuator-terminate-denied'):
                import _winapi
                while not (root/'child.started.json').exists():
                    bridge.check(); _check_deadline(spec.useful); time.sleep(.005)
                before=lease._job.accounting().active_processes
                root_before=_winapi.WaitForSingleObject(lease._information.process,0)
                _require(before>0 and root_before==258,'actual live work required before native denial')
                signal.request_stop(); bound=lease._pin_cleanup_deadline()
                actor=lease._actuator
                actor.thread.join(max(0,bound-time.monotonic_ns())/1e9)
                _require(not actor.thread.is_alive(),'diagnostic native actuator not terminal')
                _require(isinstance(actor.error,OSError) and actor.error.winerror==5,
                         'diagnostic actual native access denial required')
                active=lease._job.accounting().active_processes
                root_wait=_winapi.WaitForSingleObject(lease._information.process,0)
                sampled=time.monotonic_ns()
                _fresh(root/'actuator.failure.observed.json',dict(domain=_DOMAIN,
                    scenario=scenario,request_root=spec.request_root,pid=str(lease.identity.pid),
                    before_active=before,after_active=active,root_before_wait=root_before,
                    root_after_wait=root_wait,native_error_winerror=actor.error.winerror,
                    stop_requested=OwnedStopSignal._requested(signal),thread_alive=actor.thread.is_alive(),
                    terminated=actor.terminated,drained=actor.drained,sampled_monotonic_ns=str(sampled),
                    cleanup_deadline_monotonic_ns=str(bound)),bound)
                raise CoordinatorError('diagnostic native actuator access denied') from actor.error
            if scenario in ('busy-revocation','busy-tree-revocation','tree-validation-delay'):
                import _winapi
                while not (root/'child.started.json').exists():
                    bridge.check(); _check_deadline(spec.useful); time.sleep(.005)
                tree=None
                if scenario in ('busy-tree-revocation','tree-validation-delay'):
                    descendant_handle,descendant_identity=_retain_diagnostic_descendant(spec,lease,owned)
                    tree=dict(domain=_DOMAIN,request_root=spec.request_root,
                        descendant_pid=descendant_identity['pid'],
                        descendant_creation_filetime_100ns=descendant_identity['creation_filetime_100ns'],
                        descendant_in_work_job=_in_job(descendant_handle,lease._job.handle),
                        observer_pid=str(observer.information.pid),
                        observer_in_work_job=_in_job(observer.information.process,lease._job.handle),
                        observer_in_own_job=_in_job(observer.information.process,observer.job.handle),
                        descendant_before_wait=_winapi.WaitForSingleObject(descendant_handle,0),
                        observer_before_wait=_winapi.WaitForSingleObject(observer.information.process,0))
                    _require(not tree['observer_in_work_job'] and tree['observer_in_own_job']
                        and tree['observer_before_wait']==258,'separate-job live control required')
                    if scenario=='tree-validation-delay':
                        # Actual native wrong-job result, not patched verification.
                        lease._diagnostic_validation_result=_in_job(descendant_handle,observer.job.handle)
                        lease._diagnostic_cleanup_before=(lease._job.accounting().active_processes,
                            _winapi.WaitForSingleObject(lease._information.process,0),
                            _winapi.WaitForSingleObject(descendant_handle,0),time.monotonic_ns())
                        _require(lease._diagnostic_validation_result,'diagnostic wrong-job validation refused')
                before=lease._job.accounting().active_processes
                _require(before>0,'busy revocation requires actual live work')
                begin=time.monotonic_ns()
                _fresh(root/'revocation.arm.json',dict(domain=_DOMAIN,request_root=spec.request_root,
                    busy_started_monotonic_ns=str(begin)),spec.useful)
                # Deliberately NO lease/watch/bridge servicing during this interval.
                while time.monotonic_ns()<begin+600_000_000:
                    time.sleep(max(0,(begin+600_000_000-time.monotonic_ns())/1e9))
                active=lease._job.accounting().active_processes
                root_wait=_winapi.WaitForSingleObject(lease._information.process,0)
                if tree is not None:
                    tree.update(descendant_after_wait=_winapi.WaitForSingleObject(descendant_handle,0),
                        observer_after_wait=_winapi.WaitForSingleObject(observer.information.process,0))
                sampled=time.monotonic_ns()
                end=time.monotonic_ns()
                if tree is not None:
                    tree['sampled_monotonic_ns']=str(sampled)
                    _fresh(root/'tree.isolation.observed.json',tree,spec.useful)
                _fresh(root/'busy.revocation.observed.json',dict(domain=_DOMAIN,request_root=spec.request_root,
                    pid=str(lease.identity.pid),before_active=before,after_active=active,root_wait=root_wait,
                    stop_requested=OwnedStopSignal._requested(signal),busy_started_monotonic_ns=str(begin),
                    sampled_monotonic_ns=str(sampled),busy_finished_monotonic_ns=str(end)),spec.useful)
                bridge.check(); lease._check_stop()
                raise CoordinatorError('revoked diagnostic may never accept')
            if scenario=='blocked-observer':
                while not (root/'child.started.json').exists():
                    bridge.check(); _check_deadline(spec.useful); time.sleep(.005)
                _fresh(root/'observer.block.json',dict(domain=_DOMAIN),spec.useful)
            while lease._job.accounting().active_processes:
                bridge.check(); lease._check_stop(); lease._unexpired(); time.sleep(.005)
            terminal=lease.wait_terminal()
            _require(terminal.process.exit_code==0 and not terminal.process.timed_out,'work terminal failure')
            child=_read(root/'child.result.json',spec.useful)
            _require(child['request_root']==spec.request_root and child['identity_receipt_root']==lease.identity.receipt_root,
                     'child result correspondence failed')
            # Stop/join consumer first without closing its socket. Otherwise the
            # observer can see stop, exit, and race a still-live bridge's next read.
            bridge.quiesce(_cleanup_bound(spec,lease))
            _fresh(root/'observer.stop.json',dict(domain=_DOMAIN),_cleanup_bound(spec,lease))
            bridge.close(_cleanup_bound(spec,lease))
            watch.close(_cleanup_bound(spec,lease))
            observer_native=observer.finish(_cleanup_bound(spec,lease))
            _require(observer_native.exit_code==0,'observer terminal failure')
            work=dict(pid=str(lease.identity.pid),creation_filetime_100ns=str(lease.identity.creation_filetime_100ns),
                identity_receipt_root=lease.identity.receipt_root,exit_code=terminal.process.exit_code,
                active_processes=terminal.process.active_processes,outputs_closed=False)
            observer_report=dict(pid=str(observer_native.root_pid),creation_filetime_100ns=str(observer.creation),
                active_processes=observer_native.active_processes,terminal=True)
        finished=time.monotonic_ns()
        _fresh(root/'observer.bridge.json',dict(domain=_DOMAIN,closed=True,thread_alive=bridge.thread.is_alive(),
            socket_closed=observer.channel.fileno()==-1,
            finished_monotonic_ns=str(bridge.finished),observations=bridge.observations),spec.cleanup)
        work['outputs_closed']=all(item.resources_closed for item in lease._output.observations())
        _require(work['outputs_closed'],'work outputs still owned')
        _fresh(root/'work.native.json',asdict(terminal.process),spec.cleanup)
        _fresh(root/'observer.native.json',asdict(observer_native),spec.cleanup)
        _fresh(root/'outputs.capacity.final.json',dict(domain=_DOMAIN,request_root=spec.request_root,
            streams=[dict(row,role=role) for role,pair in (('work',lease._output),('observer',observer.output))
                for row in pair.final_capacity_observations]),spec.cleanup)
        charge=dict(domain=_DOMAIN,request_root=spec.request_root,reservation_id='diagnostic-work',
            clock_domain_root=spec.clock,entry_monotonic_ns=str(entry),owned_finished_monotonic_ns=str(finished),
            effective_wall_ns=str(finished-entry),effective_gpu_ns='0')
        charge_root=_fresh(root/'diagnostic.charge.json',charge,spec.cleanup)
        with deadline_file_lock(root/'operator'/'operator.lock',spec.cleanup):
            with deadline_file_lock(reservation/'global.lock',spec.cleanup):
                ended=_append(store,terminal.owner_root,'terminal',spec.request_root,spec.cleanup,
                    fact_kind='verified_owned_tree_terminal',identity_receipt_root=terminal.identity.receipt_root,
                    exit_code=str(terminal.process.exit_code),terminal_fact_root=sha256_bytes(canonical_json_bytes(asdict(terminal.process))))
                observation=_observe_growth(root,spec.request_root,ended.sha256,
                    ended.snapshot.pending_research_bytes,ended.snapshot.pending_physical_bytes,spec.cleanup)
                growth=_fresh(root/'diagnostic.growth.json',observation,spec.cleanup)
                # No guessed materialization or refunds: publication tail and all
                # unknown physical costs retain the original reservation charge.
                # Holding it is NOT proof of the prelaunch physical peak bound.
                released=_append(store,ended.sha256,'settle_storage_held',spec.request_root,spec.cleanup,
                    resource_charge_root=charge_root,wall_kind='observed',effective_wall_ns=str(finished-entry),
                    effective_gpu_ns='0',growth_observation_root=growth)
        report=dict(schema='alc-r0-coordinator-diagnostic-v1',domain=_DOMAIN,scenario=scenario,
            outcome='success',scientific_execution=False,entry_monotonic_ns=str(entry),
            useful_deadline_monotonic_ns=str(spec.useful),cleanup_deadline_monotonic_ns=str(spec.cleanup),
            finished_monotonic_ns=str(finished),request_root=spec.request_root,final_owner_root=released.sha256,
            work=work,observer=observer_report,storage_held=True,growth_observation_root=growth)
        try:
            _fresh(root/'diagnostic.result.json',report,spec.cleanup)
        except BaseException as error:
            raise _ReleasedCompletionUnconfirmed(released.sha256) from error
        return 0
    finally:
        # Cleanup may discover secondary failures; never mask the active denial.
        failure=sys.exc_info()[1]
        try:
            if bridge is not None: bridge.close(_cleanup_bound(spec,lease))
        except BaseException as error:
            if failure is None: failure=error
        try:
            if watch is not None: watch.close(_cleanup_bound(spec,lease))
        except BaseException as error:
            if failure is None: failure=error
        try:
            if observer is not None:
                if observer.job is not None: observer.job.cleanup_deadline_ns=_cleanup_bound(spec,lease)
                observer.close()
        except BaseException as error:
            if failure is None: failure=error
        try:
            if bridge is not None and not (root/'observer.bridge.json').exists():
                _fresh(root/'observer.bridge.json',dict(domain=_DOMAIN,closed=not bridge.thread.is_alive(),
                    thread_alive=bridge.thread.is_alive(),socket_closed=observer.channel.fileno()==-1,
                    finished_monotonic_ns=str(bridge.finished),observations=bridge.observations,
                    operational_error=None if bridge.error is None else type(bridge.error).__name__),
                    _cleanup_bound(spec,lease))
        except BaseException as error:
            if failure is None: failure=error
        if failure is not None: raise failure


def main():
    entry=time.monotonic_ns()
    arguments=sys.argv[1:]
    if not arguments:
        sys.stderr.write('alc-r0 scientific installation unavailable\n'); return 2
    try:
        if len(arguments)==3 and arguments[0]=='diagnostic' and arguments[1] in _SCENARIOS:
            return _coordinate(arguments[2],entry,arguments[1])
        if len(arguments)==3 and arguments[0] in ('worker','observer','descendant'):
            return _roles(*arguments)
        raise CoordinatorError('closed diagnostic invocation required')
    except _ReleasedCompletionUnconfirmed as error:
        sys.stderr.write('alc-r0 '+str(error)+'\n')
        return 3
    except (Exception,KeyboardInterrupt) as error:
        sys.stderr.write('alc-r0 coordinator denied: '+type(error).__name__+': '+str(error)[:512]+'\n')
        return 2


if __name__=='__main__': raise SystemExit(main())
