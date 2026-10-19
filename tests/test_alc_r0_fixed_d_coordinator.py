"""Integrated-entrypoint acceptance RED; not model or scientific evidence."""
import os
from pathlib import Path
import sys
import time

import pytest

from aluclu.alc_r0.canonical import canonical_json_bytes,parse_canonical_json
from aluclu.alc_r0.checkpoint_owned_process import run_owned_process
from aluclu.alc_r0.reservation_store import ReservationStore

pytestmark=pytest.mark.skipif(os.name!='nt',reason='actual Windows owned coordinator')
MODULE='aluclu.alc_r0.fixed_d_coordinator'


def invoke(tmp_path,arguments,*,runtime_baseline=False):
    environment=os.environ.copy()
    environment.update(PYTHONPATH=str(Path(__file__).resolve().parents[1]/'src'),
        PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='-1',
        HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1')
    command=((sys.executable,'-B','-c','pass') if runtime_baseline else
             (sys.executable,'-B','-m',MODULE,*arguments))
    return run_owned_process(command,
        cwd=tmp_path,environment=environment,stdout_path=tmp_path/'entry.stdout',
        stderr_path=tmp_path/'entry.stderr',deadline_ns=time.monotonic_ns()+30_000_000_000)


def bounded_json(path,limit=16384):
    with path.open('rb') as stream: data=stream.read(limit+1)
    assert 0<len(data)<=limit
    value=parse_canonical_json(data)
    assert canonical_json_bytes(value)==data
    return value


def test_actual_default_entrypoint_denies_missing_scientific_installation(tmp_path):
    baseline_path=tmp_path/'runtime-baseline'; baseline_path.mkdir()
    baseline=invoke(baseline_path,(),runtime_baseline=True)
    assert baseline.exit_code==0 and baseline.active_processes==0 and not baseline.timed_out
    receipt=invoke(tmp_path,())
    assert receipt.exit_code==2 and not receipt.timed_out
    # Windows venv launcher forwarding may create multiple runtime processes.
    # Require no additional members beyond the separately observed fixed runtime.
    assert receipt.active_processes==0 and receipt.total_processes==baseline.total_processes
    assert (tmp_path/'entry.stdout').read_bytes()==b''
    assert b'scientific installation unavailable' in (tmp_path/'entry.stderr').read_bytes()
    assert not (tmp_path/'reservations').exists()


@pytest.mark.parametrize('scenario',['success','slow-parent'])
def test_actual_diagnostic_entrypoint_completes_owned_and_reconciled_cycle(tmp_path,scenario):
    namespace=tmp_path/'diagnostic'; namespace.mkdir()
    receipt=invoke(tmp_path,('diagnostic',scenario,str(namespace)))
    assert receipt.exit_code==0 and not receipt.timed_out and receipt.active_processes==0
    report=bounded_json(namespace/'diagnostic.result.json')
    assert report['schema']=='alc-r0-coordinator-diagnostic-v1'
    assert report['domain']=='diagnostic-only' and report['scenario']==scenario
    assert report['outcome']=='success'
    assert report['scientific_execution'] is False
    origin=int(report['entry_monotonic_ns'])
    useful=int(report['useful_deadline_monotonic_ns'])
    cleanup=int(report['cleanup_deadline_monotonic_ns'])
    assert useful==origin+15_000_000_000 and cleanup==useful+10_000_000_000
    assert int(report['finished_monotonic_ns'])<=cleanup
    work=report['work']; observer=report['observer']
    assert work['exit_code']==0 and work['active_processes']==0 and work['outputs_closed'] is True
    assert observer['active_processes']==0 and observer['terminal'] is True
    worker_native=bounded_json(namespace/'work.native.json')
    observer_native=bounded_json(namespace/'observer.native.json')
    assert worker_native['root_pid']==int(work['pid'])>0
    assert observer_native['root_pid']==int(observer['pid'])>0
    assert observer_native['root_pid']!=worker_native['root_pid']
    assert int(observer['creation_filetime_100ns'])>0
    for native in (worker_native,observer_native):
        assert native['active_processes']==0 and native['timed_out'] is False
        assert origin<=native['started_ns']<native['finished_ns']<=int(report['finished_monotonic_ns'])
    child=bounded_json(namespace/'child.result.json')
    assert child['schema']=='alc-r0-harmless-child-v1'
    assert child['domain']=='diagnostic-only' and child['request_root']==report['request_root']
    assert child['identity_receipt_root']==work['identity_receipt_root']
    assert int(child['pid'])==int(work['pid'])>0
    assert int(child['creation_filetime_100ns'])==int(work['creation_filetime_100ns'])>0
    declaration=bounded_json(namespace/'declaration.json')
    assert declaration['run_id']=='alc-r0-diagnostic-coordinator-success'
    assert declaration['device']=='cpu' and declaration['gpu_reservation_ns']=='0'
    assert declaration['attempt_id']=='a001' and declaration['segment']=='initial'
    store=ReservationStore(namespace/'reservations',(canonical_json_bytes(declaration),))
    final=store.read(report['final_owner_root'])
    with store._lock():
        _,replay,_=store._read_locked(report['final_owner_root'])
    events=[parse_canonical_json(data) for data in replay._events]
    assert [event['kind'] for event in events]==[
        'reserve','child_created','identity_published','running','terminal','settle_storage_held']
    assert len(final.snapshot.reservations)==1
    view=final.snapshot.reservations[0]
    assert view.state=='EXECUTION_RELEASED_STORAGE_HELD' and view.effective_gpu_ns==0
    assert view.identity_receipt_root==work['identity_receipt_root']
    assert view.pid==int(child['pid'])
    assert final.snapshot.pending_physical_bytes==final.snapshot.pending_research_bytes==1<<20
    assert report['storage_held'] is True
    charge=bounded_json(namespace/'diagnostic.charge.json')
    assert charge['domain']=='diagnostic-only' and charge['effective_gpu_ns']=='0'
    assert charge['request_root']==report['request_root']
    assert charge['reservation_id']==declaration['reservation_id']
    assert charge['clock_domain_root']==events[0]['clock_domain_root']
    assert int(charge['entry_monotonic_ns'])==origin
    # Finish means owned work AND observer cleanup complete, before report encoding.
    assert charge['owned_finished_monotonic_ns']==report['finished_monotonic_ns']
    assert int(charge['effective_wall_ns'])>=int(report['finished_monotonic_ns'])-origin>0
    assert events[-1]['effective_wall_ns']==charge['effective_wall_ns']
    # Only the diagnostic one-use claim; no scientific D consumption filename.
    claim=bounded_json(namespace/'diagnostic.consumed.json')
    assert claim['domain']=='diagnostic-only' and claim['request_root']==report['request_root']
    assert claim['reservation_id']==declaration['reservation_id']
    for key in ('run_id','attempt_id','segment','declaration_root'):
        assert claim[key]==declaration[key]
    assert not list(namespace.glob('d-*.consumed.json'))
    if scenario=='slow-parent':
        delay=bounded_json(namespace/'parent.delay.json')
        begin=int(delay['started_monotonic_ns']); end=int(delay['finished_monotonic_ns'])
        assert end-begin>=600_000_000
        bridge=bounded_json(namespace/'observer.bridge.json')
        assert bridge['closed'] is True and bridge['thread_alive'] is False and bridge['socket_closed'] is True
        assert sum(begin<int(item['observed_monotonic_ns'])<end for item in bridge['observations'])>=2
        for item in bridge['observations']:
            assert 0<=int(item['submitted_monotonic_ns'])-int(item['started_monotonic_ns'])<250_000_000


@pytest.mark.parametrize('scenario,state',[
    ('stale-before-create','RESERVED'),('stale-before-resume','READY'),('blocked-observer','RUNNING'),
    ('bootstrap-conflict','READY'),('bootstrap-wrong-role','READY')])
def test_actual_entrypoint_retains_pending_on_stale_or_blocked_source(tmp_path,scenario,state):
    namespace=tmp_path/'diagnostic'; namespace.mkdir()
    receipt=invoke(tmp_path,('diagnostic',scenario,str(namespace)))
    assert receipt.exit_code==2 and receipt.active_processes==0 and not receipt.timed_out
    declaration=bounded_json(namespace/'declaration.json')
    owner=bounded_json(namespace/'reservations'/'owner.json')
    from aluclu.alc_r0.canonical import sha256_bytes
    store=ReservationStore(namespace/'reservations',(canonical_json_bytes(declaration),))
    view=store.read(sha256_bytes(canonical_json_bytes(owner))).snapshot
    assert view.reservations[0].state==state and view.pending_physical_bytes>0
    assert (namespace/'diagnostic.consumed.json').exists()
    assert not (namespace/'diagnostic.result.json').exists()
    assert not (namespace/'diagnostic.charge.json').exists()
    if state=='RESERVED':
        assert view.reservations[0].pid is None and not (namespace/'diagnostic.child.json').exists()
    else:
        work=bounded_json(namespace/'work.cleanup.native.json')
        observer=bounded_json(namespace/'observer.cleanup.native.json')
        assert work['forced'] is True
        assert work['receipt']['active_processes']==observer['receipt']['active_processes']==0
        assert work['receipt']['root_pid']!=observer['receipt']['root_pid']
        assert work['receipt']['finished_ns']<=int(work['cleanup_deadline_monotonic_ns'])
        assert observer['receipt']['finished_ns']<=int(observer['cleanup_deadline_monotonic_ns'])
        if state=='READY': assert not (namespace/'child.started.json').exists()
        else:
            assert (namespace/'child.started.json').exists() and observer['forced'] is True
            assert observer['receipt']['exit_code']==124
            bridge=bounded_json(namespace/'observer.bridge.json')
            assert bridge['closed'] is True and bridge['thread_alive'] is False and bridge['socket_closed'] is True
            assert bridge['operational_error'] is not None
    if scenario.startswith('bootstrap-'):
        assert observer['parent_socket_closed'] is True and observer['surplus_socket_closed'] is True
        assert not (namespace/'observer.ready.json').exists()
        assert not (namespace/'observer.bridge.json').exists()
        assert not (namespace/'worker.start.json').exists()
        if scenario=='bootstrap-conflict':
            assert observer['forced'] is True and observer['receipt']['exit_code']==124
            assert b'FileExistsError' in (tmp_path/'entry.stderr').read_bytes()
        else:
            assert observer['receipt']['exit_code']==2
            assert b'native bootstrap identity differs' in (namespace/'observer.stderr').read_bytes()


@pytest.mark.parametrize('scenario',['actuator-query-denied','actuator-terminate-denied'])
def test_actual_coordinator_native_denial_preserves_failure_and_reports_owner_cleanup(tmp_path,scenario):
    namespace=tmp_path/'diagnostic'; namespace.mkdir()
    receipt=invoke(tmp_path,('diagnostic',scenario,str(namespace)))
    assert receipt.exit_code==2 and not receipt.timed_out and receipt.active_processes==0
    observed=bounded_json(namespace/'actuator.failure.observed.json')
    assert observed['scenario']==scenario and observed['native_error_winerror']==5
    assert observed['before_active']>0 and observed['after_active']>0
    assert observed['root_before_wait']==observed['root_after_wait']==258
    assert observed['stop_requested'] is True and observed['thread_alive'] is False
    assert observed['terminated'] is False and observed['drained'] is False
    cleanup=bounded_json(namespace/'work.cleanup.native.json')
    assert cleanup['forced'] is True and cleanup['receipt']['active_processes']==0
    assert cleanup['receipt']['root_pid']==int(observed['pid'])
    assert cleanup['receipt']['exit_code']==124
    assert int(observed['sampled_monotonic_ns'])<=cleanup['receipt']['finished_ns']
    assert cleanup['receipt']['finished_ns']<=int(cleanup['cleanup_deadline_monotonic_ns'])
    actor=bounded_json(namespace/'actuator.native.json')
    assert actor['pid']==observed['pid'] and actor['thread_alive'] is False
    assert actor['duplicate_handles_closed'] is True
    assert actor['terminated'] is False and actor['drained'] is False
    assert actor['cleanup_deadline_monotonic_ns']==cleanup['cleanup_deadline_monotonic_ns']
    observer=bounded_json(namespace/'observer.cleanup.native.json')
    assert observer['receipt']['active_processes']==0
    assert b'native actuator' in (tmp_path/'entry.stderr').read_bytes()
    assert (namespace/'child.started.json').exists() and not (namespace/'child.result.json').exists()
    assert not (namespace/'diagnostic.result.json').exists() and not (namespace/'diagnostic.charge.json').exists()
    from aluclu.alc_r0.canonical import sha256_bytes
    declaration=bounded_json(namespace/'declaration.json'); owner=bounded_json(namespace/'reservations'/'owner.json')
    snapshot=ReservationStore(namespace/'reservations',(canonical_json_bytes(declaration),)).read(
        sha256_bytes(canonical_json_bytes(owner))).snapshot
    assert snapshot.reservations[0].state=='RUNNING'
    assert snapshot.pending_physical_bytes>0 and snapshot.pending_research_bytes>0
    assert (namespace/'diagnostic.consumed.json').exists()


def test_completion_conflict_after_release_reports_committed_state_not_pending(tmp_path):
    namespace=tmp_path/'diagnostic'; namespace.mkdir()
    receipt=invoke(tmp_path,('diagnostic','completion-conflict',str(namespace)))
    assert receipt.exit_code==3 and not receipt.timed_out and receipt.active_processes==0
    from aluclu.alc_r0.canonical import sha256_bytes
    declaration=bounded_json(namespace/'declaration.json'); owner=bounded_json(namespace/'reservations'/'owner.json')
    owner_root=sha256_bytes(canonical_json_bytes(owner))
    snapshot=ReservationStore(namespace/'reservations',(canonical_json_bytes(declaration),)).read(owner_root).snapshot
    # Execution settlement MUST NOT imply storage release or physical-growth proof.
    assert snapshot.reservations[0].state=='EXECUTION_RELEASED_STORAGE_HELD'
    assert snapshot.pending_physical_bytes==snapshot.pending_research_bytes==1<<20
    assert bounded_json(namespace/'diagnostic.result.json')==dict(
        domain='diagnostic-only',marker='diagnostic-completion-conflict')
    stderr=(tmp_path/'entry.stderr').read_bytes()
    assert b'execution settled; storage held; completion publication unconfirmed' in stderr
    assert owner_root.encode() in stderr and b'coordinator denied:' not in stderr
    assert bounded_json(namespace/'diagnostic.charge.json')['effective_gpu_ns']=='0'
    before=(namespace/'reservations'/'owner.json').read_bytes()
    claim=(namespace/'diagnostic.consumed.json').read_bytes()
    again=tmp_path/'again'; again.mkdir()
    refused=invoke(again,('diagnostic','completion-conflict',str(namespace)))
    assert refused.exit_code==2 and not refused.timed_out and refused.active_processes==0
    assert (namespace/'reservations'/'owner.json').read_bytes()==before
    assert (namespace/'diagnostic.consumed.json').read_bytes()==claim


def test_closed_diagnostic_declaration_is_cpu_only_fixed_envelope():
    from test_alc_r0_reservation_state import declaration
    from aluclu.alc_r0.reservation_state import ReservationReplay
    value=declaration(run_id='alc-r0-diagnostic-coordinator-success',device='cpu',
        useful_wall_ceiling_ns='15000000000',charge_envelope_ns='25000000000',gpu_reservation_ns='0')
    assert len(ReservationReplay((value,)).snapshot().reservations)==1


@pytest.mark.parametrize('scenario',['busy-revocation','busy-tree-revocation'])
def test_busy_revocation_terminates_actual_work_before_main_returns(tmp_path,scenario):
    namespace=tmp_path/'diagnostic'; namespace.mkdir()
    receipt=invoke(tmp_path,('diagnostic',scenario,str(namespace)))
    assert receipt.exit_code==2 and receipt.active_processes==0 and not receipt.timed_out
    observed=bounded_json(namespace/'busy.revocation.observed.json')
    published=bounded_json(namespace/'revocation.published.json')
    child=bounded_json(namespace/'child.started.json')
    assert observed['pid']==child['pid'] and observed['request_root']==published['request_root']
    begin=int(observed['busy_started_monotonic_ns']); end=int(observed['busy_finished_monotonic_ns'])
    sampled=int(observed['sampled_monotonic_ns'])
    assert end-begin>=600_000_000
    assert begin<=int(published['published_monotonic_ns'])<=sampled<=end
    assert observed['before_active']>0 and observed['stop_requested'] is True
    assert not (namespace/'diagnostic.result.json').exists() and not (namespace/'diagnostic.charge.json').exists()
    from aluclu.alc_r0.canonical import sha256_bytes
    declaration=bounded_json(namespace/'declaration.json')
    owner=bounded_json(namespace/'reservations'/'owner.json')
    store=ReservationStore(namespace/'reservations',(canonical_json_bytes(declaration),))
    snapshot=store.read(sha256_bytes(canonical_json_bytes(owner))).snapshot
    assert snapshot.reservations[0].state=='RUNNING'
    assert snapshot.pending_physical_bytes>0 and snapshot.pending_research_bytes>0
    assert (namespace/'diagnostic.consumed.json').exists()
    for filename in ('work.cleanup.native.json','observer.cleanup.native.json'):
        cleanup=bounded_json(namespace/filename)
        assert cleanup['receipt']['active_processes']==0
        assert cleanup['receipt']['finished_ns']<=int(cleanup['cleanup_deadline_monotonic_ns'])
    # An Event or later exception cleanup is not prompt native cancellation.
    assert observed['after_active']==0 and observed['root_wait']==0
    actuator=bounded_json(namespace/'actuator.native.json')
    assert actuator['pid']==child['pid'] and actuator['terminated'] is True and actuator['drained'] is True
    assert actuator['thread_alive'] is False and actuator['duplicate_handles_closed'] is True
    assert int(actuator['finished_monotonic_ns'])<=sampled
    assert int(actuator['cleanup_deadline_monotonic_ns'])==int(bounded_json(namespace/'work.cleanup.native.json')['cleanup_deadline_monotonic_ns'])
    if scenario=='busy-tree-revocation':
        tree=bounded_json(namespace/'tree.isolation.observed.json')
        descendant=bounded_json(namespace/'descendant.started.json')
        assert descendant['parent_pid']==child['pid']
        assert tree['descendant_pid']==descendant['pid'] and tree['descendant_pid']!=child['pid']
        assert tree['descendant_creation_filetime_100ns']==descendant['creation_filetime_100ns']
        assert tree['descendant_in_work_job'] is True
        assert tree['observer_in_work_job'] is False and tree['observer_in_own_job'] is True
        assert tree['descendant_before_wait']==tree['observer_before_wait']==258
        assert tree['descendant_after_wait']==0 and tree['observer_after_wait']==258
        assert tree['observer_pid']==bounded_json(namespace/'observer.ready.json')['pid']
        assert int(tree['sampled_monotonic_ns'])==sampled
        closure=bounded_json(namespace/'descendant.handle.closed.json')
        assert closure['pid']==descendant['pid'] and closure['handle_closed'] is True
        assert closure['request_root']==observed['request_root']
        assert sampled<=int(closure['finished_monotonic_ns'])<=int(closure['cleanup_deadline_monotonic_ns'])


def test_shared_cleanup_tail_never_renews_and_consumers_read_early_pin():
    from types import SimpleNamespace
    from aluclu.alc_r0.fixed_d_coordinator import _SharedTail,_cleanup_bound
    now=time.monotonic_ns(); tail=_SharedTail(now+20_000_000_000)
    first=tail.pin(now+1_000_000_000)
    assert tail.pin()==first and tail.pin(now+5_000_000_000)==first
    lease=SimpleNamespace(_shared_tail=tail,_cleanup_deadline=None)
    spec=SimpleNamespace(cleanup=now+20_000_000_000)
    assert _cleanup_bound(spec,lease)==first
    earlier=tail.pin(now+500_000_000)
    lease._cleanup_deadline=first
    assert _cleanup_bound(spec,lease)==earlier<first


def test_early_tree_validation_cancels_before_delayed_cleanup_publication(tmp_path):
    namespace=tmp_path/'diagnostic'; namespace.mkdir()
    receipt=invoke(tmp_path,('diagnostic','tree-validation-delay',str(namespace)))
    assert receipt.exit_code==2 and receipt.active_processes==0 and not receipt.timed_out
    observation=bounded_json(namespace/'early.cleanup.observed.json')
    assert observation['validation_result'] is False
    assert observation['before_active']>=2 and observation['root_before_wait']==258
    assert observation['descendant_before_wait']==258
    assert observation['after_active']==0 and observation['root_after_wait']==0
    assert observation['stop_requested'] is True
    begin=int(observation['started_monotonic_ns']); sample=int(observation['sampled_monotonic_ns'])
    assert int(observation['before_sampled_monotonic_ns'])<=begin
    assert sample-begin>=600_000_000
    actor=bounded_json(namespace/'actuator.native.json')
    assert begin<=int(actor['finished_monotonic_ns'])<=sample
    assert actor['terminated'] and actor['drained'] and actor['duplicate_handles_closed']
    assert actor['thread_alive'] is False
    closure=bounded_json(namespace/'descendant.handle.closed.json')
    assert closure['handle_closed'] is True and int(closure['finished_monotonic_ns'])>=sample
    assert observation['request_root']==closure['request_root']
    assert int(closure['cleanup_deadline_monotonic_ns'])==int(actor['cleanup_deadline_monotonic_ns'])
    assert not (namespace/'revocation.arm.json').exists()
    assert not (namespace/'revocation.published.json').exists()
    status=bounded_json(namespace/'operator'/'status.json')
    assert status['sequence']=='1' and status['revoked'] is False
    assert not (namespace/'diagnostic.result.json').exists() and not (namespace/'diagnostic.charge.json').exists()
    from aluclu.alc_r0.canonical import sha256_bytes
    declaration=bounded_json(namespace/'declaration.json'); owner=bounded_json(namespace/'reservations'/'owner.json')
    snapshot=ReservationStore(namespace/'reservations',(canonical_json_bytes(declaration),)).read(
        sha256_bytes(canonical_json_bytes(owner))).snapshot
    assert snapshot.reservations[0].state=='RUNNING' and snapshot.pending_physical_bytes>0
    assert snapshot.pending_research_bytes>0 and (namespace/'diagnostic.consumed.json').exists()


@pytest.mark.parametrize('entrypoint',['acquire','start'])
def test_actuator_real_partial_duplicate_failure_closes_owned_job_duplicate(entrypoint):
    # Real Windows DuplicateHandle failure after actual successful job duplication.
    # This is an isolated acquisition fault, not full coordinator/termination coverage.
    import _winapi
    from types import SimpleNamespace
    from aluclu.alc_r0.checkpoint_owned_process import _Job
    from aluclu.alc_r0.fixed_d_coordinator import _NativeActuator,_SharedTail,CoordinatorError
    from aluclu.alc_r0.reserved_owned_process import OwnedStopSignal
    deadline=time.monotonic_ns()+2_000_000_000
    with _Job() as job:
        signal=OwnedStopSignal(); tail=_SharedTail(deadline)
        lease=SimpleNamespace(_stop_signal=signal,_shared_tail=tail,_deadline=deadline,
            _job=job,_information=SimpleNamespace(process=0),_identity=SimpleNamespace(pid=0))
        actor=_NativeActuator(lease)
        try:
            if entrypoint=='acquire':
                with pytest.raises(OSError) as native: actor._acquire()
                assert native.value is actor.error and native.value.winerror==6
                # Observe the retained partial success BEFORE cleanup erases it.
                assert actor.job is not None and actor.process is None
                assert actor._counts().active_processes==0
                assert not OwnedStopSignal._requested(signal)
                with pytest.raises(CoordinatorError) as result: actor.close()
            else:
                with pytest.raises(CoordinatorError) as result: actor.start()
            # Cleanup must retain the real native acquisition error.
            assert isinstance(actor.error,OSError) and actor.error.winerror==6
            assert result.value.__cause__ is actor.close_error
            assert actor.close_error.__cause__ is actor.error
            assert OwnedStopSignal._requested(signal)
            assert actor._source_job is None and actor._source_process is None
            assert actor.job is None and actor.process is None and actor.closed
            assert not actor.started and actor.thread.ident is None and not actor.thread.is_alive()
            assert actor.finished is None and not actor.drained and not actor.terminated
            pinned=tail.current(); assert pinned<=deadline
            # Duplicate cleanup did not close the original owner handle.
            assert job.accounting().active_processes==0
            with pytest.raises(CoordinatorError) as repeated: actor.close()
            assert repeated.value.__cause__ is actor.close_error
            assert actor.job is None and actor.process is None and tail.current()<=pinned
        finally:
            # Test assertions must not leak a retained partial acquisition.
            try: actor.close()
            except CoordinatorError: pass  # sticky failure already asserted above
            assert not actor.thread.is_alive()
            for name in ('process','job'):
                handle=getattr(actor,name)
                if handle is not None:
                    _winapi.CloseHandle(handle); setattr(actor,name,None)


@pytest.mark.parametrize('access,fault',[(0x0008,'query'),(0x0004,'terminate')])
def test_actuator_real_access_denial_stays_failed_and_owner_drains_child(tmp_path,access,fault):
    # Actual restricted duplicates of the SAME privately owned job/root.
    # The harmless child stays suspended; no injected API or external target.
    import _winapi
    from types import SimpleNamespace
    from test_alc_r0_reserved_owned_process import fixture,ROOT
    from aluclu.alc_r0.reserved_owned_process import ReservedOwnedLease,OwnedStopSignal,OwnedStopRequested
    from aluclu.alc_r0.fixed_d_coordinator import _NativeActuator,_SharedTail,CoordinatorError,_in_job
    signal=OwnedStopSignal()
    arguments,store,_,sentinel=fixture(tmp_path,stop_signal=signal)
    current=_winapi.GetCurrentProcess(); retained=None
    try:
        with ReservedOwnedLease(**arguments) as lease:
            ready=lease.publish_identity(ROOT,ROOT)
            retained=_winapi.DuplicateHandle(current,lease._information.process,current,
                0x00100000,False,0)  # observation only: SYNCHRONIZE
            restricted=None; actor=None
            try:
                restricted=_winapi.DuplicateHandle(current,lease._job.handle,current,access,False,0)
                view=SimpleNamespace(_stop_signal=signal,
                    _shared_tail=_SharedTail(arguments['deadline_ns']+10_000_000_000),
                    _deadline=arguments['deadline_ns'],_information=lease._information,
                    _identity=lease.identity,
                    _job=SimpleNamespace(kernel=lease._job.kernel,handle=restricted))
                actor=_NativeActuator(view)
                assert _in_job(lease._information.process,lease._job.handle)
                assert lease._job.accounting().active_processes>=1
                assert _winapi.WaitForSingleObject(retained,0)==258 and not sentinel.exists()
                actor.start()
                assert actor.job is not None and actor.process is not None
                if fault=='query':
                    with pytest.raises(OSError) as denied: actor._counts()
                    assert denied.value.winerror==5
                else:
                    assert actor._counts().active_processes>=1
                signal.request_stop()
                actor.thread.join(max(0,arguments['deadline_ns']-time.monotonic_ns())/1e9)
                assert not actor.thread.is_alive() and actor.started
                assert isinstance(actor.error,OSError) and actor.error.winerror==5
                assert not actor.terminated and not actor.drained and actor.finished is not None
                # Failure is not a successful termination observation.
                assert lease._job.accounting().active_processes>=1
                assert _winapi.WaitForSingleObject(retained,0)==258
                with pytest.raises(CoordinatorError) as failed: actor.check()
                assert failed.value.__cause__ is actor.error
                with pytest.raises(CoordinatorError): actor.close()
                assert actor.closed and actor.job is None and actor.process is None
                with pytest.raises(OwnedStopRequested): lease.resume_verified(ready.sha256)
                assert not sentinel.exists()
            finally:
                try:
                    signal.request_stop()
                    if actor is not None:
                        try: actor.close()
                        except CoordinatorError: pass
                        assert not actor.thread.is_alive()
                        for name in ('process','job'):
                            handle=getattr(actor,name)
                            if handle is not None:
                                _winapi.CloseHandle(handle); setattr(actor,name,None)
                finally:
                    # Actor owns distinct duplicates, never this source handle.
                    if restricted is not None: _winapi.CloseHandle(restricted)
        # The independent primary owner, not the failed actuator, drains its job.
        assert _winapi.WaitForSingleObject(retained,0)==0 and not sentinel.exists()
        snapshot=store.read(ready.sha256).snapshot
        assert snapshot.reservations[0].state=='READY'
        assert snapshot.pending_physical_bytes>0 and snapshot.pending_research_bytes>0
    finally:
        if retained is not None: _winapi.CloseHandle(retained)


def test_closed_fixed_lease_retries_actor_cleanup_without_clearing_first_failure():
    # Retained-failure bookkeeping with actual private event handles.
    # NOT a claim that a native API/thread-start failure was injected.
    import _winapi
    import ctypes
    import threading
    from aluclu.alc_r0.fixed_d_coordinator import _FixedLease,_NativeActuator,_SharedTail
    from aluclu.alc_r0.reserved_owned_process import OwnedStopSignal
    actor=object.__new__(_NativeActuator)
    actor.process=actor.job=None
    actor.signal=OwnedStopSignal(); actor.tail=_SharedTail(time.monotonic_ns()+2_000_000_000)
    actor.finish=threading.Event(); actor.thread=threading.Thread(target=lambda: None)
    actor.closed=False; actor.error=None; actor.started=False; actor.drained=False
    original=RuntimeError('retained first fixed-lease cleanup failure'); actor.close_error=original
    lease=object.__new__(_FixedLease)
    lease._state='CLOSED'; lease._fixed_close_error=original; lease._actuator=actor
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateEventW.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_wchar_p]
    kernel.CreateEventW.restype=ctypes.c_void_p
    try:
        actor.process=kernel.CreateEventW(None,True,False,None)
        if not actor.process: raise ctypes.WinError(ctypes.get_last_error())
        actor.job=kernel.CreateEventW(None,True,False,None)
        if not actor.job: raise ctypes.WinError(ctypes.get_last_error())
        with pytest.raises(RuntimeError) as denied: lease._close()
        assert denied.value is original and lease._fixed_close_error is original
        assert actor.closed and actor.process is None and actor.job is None
        pinned=actor.tail.current()
        with pytest.raises(RuntimeError) as repeated: lease._close()
        assert repeated.value is original and actor.tail.current()<=pinned
        assert OwnedStopSignal._requested(actor.signal) and actor.thread.ident is None
    finally:
        if actor.process is not None: _winapi.CloseHandle(actor.process)
        if actor.job is not None: _winapi.CloseHandle(actor.job)


def test_actuator_retained_cleanup_error_does_not_skip_remaining_native_handles():
    # Local bookkeeping fixture, NOT a native termination/acquisition fault run.
    import _winapi
    import ctypes
    import threading
    from aluclu.alc_r0.fixed_d_coordinator import _NativeActuator,_SharedTail,CoordinatorError
    from aluclu.alc_r0.reserved_owned_process import OwnedStopSignal
    actor=object.__new__(_NativeActuator)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateEventW.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_wchar_p]
    kernel.CreateEventW.restype=ctypes.c_void_p
    actor.process=actor.job=None
    actor.signal=OwnedStopSignal(); actor.tail=_SharedTail(time.monotonic_ns()+1_000_000_000)
    actor.finish=threading.Event(); actor.thread=threading.Thread(target=lambda: None)
    actor.closed=False; actor.error=None; actor.started=False; actor.drained=False
    original=RuntimeError('retained prior cleanup failure'); actor.close_error=original
    try:
        actor.process=kernel.CreateEventW(None,True,False,None)
        if not actor.process: raise ctypes.WinError(ctypes.get_last_error())
        actor.job=kernel.CreateEventW(None,True,False,None)
        if not actor.job: raise ctypes.WinError(ctypes.get_last_error())
        with pytest.raises(CoordinatorError) as result: actor.close()
        assert result.value.__cause__ is original
        assert actor.closed and actor.process is None and actor.job is None
        with pytest.raises(CoordinatorError) as repeated: actor.close()
        assert repeated.value.__cause__ is original and actor.close_error is original
    finally:
        if actor.process is not None: _winapi.CloseHandle(actor.process)
        if actor.job is not None: _winapi.CloseHandle(actor.job)


@pytest.mark.parametrize('change',[
    dict(device='gpu',gpu_reservation_ns='25000000000'),dict(attempt_id='a002'),
    dict(segment='resume'),dict(useful_wall_ceiling_ns='15000000001',charge_envelope_ns='25000000001'),
    dict(charge_envelope_ns='25000000001'),dict(gpu_reservation_ns='1'),
    dict(run_id='alc-r0-diagnostic-coordinator-other')])
def test_closed_diagnostic_declaration_cannot_become_scientific(change):
    from test_alc_r0_reservation_state import declaration
    from aluclu.alc_r0.reservation_state import ReservationReplay
    values=dict(run_id='alc-r0-diagnostic-coordinator-success',device='cpu',
        useful_wall_ceiling_ns='15000000000',charge_envelope_ns='25000000000',gpu_reservation_ns='0')
    values.update(change)
    with pytest.raises(ValueError): ReservationReplay((declaration(**values),))


def test_actual_entrypoint_refuses_consumed_diagnostic_namespace(tmp_path):
    namespace=tmp_path/'diagnostic'; namespace.mkdir()
    first=invoke(tmp_path,('diagnostic','success',str(namespace)))
    assert first.exit_code==0 and first.active_processes==0
    original=(namespace/'reservations'/'owner.json').read_bytes()
    claim=(namespace/'diagnostic.consumed.json').read_bytes()
    second=tmp_path/'second'; second.mkdir()
    result=invoke(second,('diagnostic','success',str(namespace)))
    assert result.exit_code==2 and result.active_processes==0 and not result.timed_out
    assert (namespace/'reservations'/'owner.json').read_bytes()==original
    assert (namespace/'diagnostic.consumed.json').read_bytes()==claim


def test_actual_entrypoint_refuses_system_temp_root_without_writing(tmp_path):
    import tempfile
    result=invoke(tmp_path,('diagnostic','success',tempfile.gettempdir()))
    assert result.exit_code==2 and result.active_processes==0 and not result.timed_out
    assert b'below system TEMP' in (tmp_path/'entry.stderr').read_bytes()


@pytest.mark.parametrize('wire,eof,category',[
    (b'\x00\x00\x00\x00',False,'length exceeds'),
    (b'\x00\x00\x20\x01',False,'length exceeds'),
    (b'\x00\x00',True,'EOF/truncation'),
    (b'\x00\x00\x00\x04{}',True,'EOF/truncation'),
    (b'\x00\x00\x00\x02xx',False,'invalid canonical D transport'),
    (b'\x00\x00\x00\x02{}\x00',False,'unexpected pipelined frame'),
])
def test_native_frame_rejects_oversize_partial_malformed_and_pipeline(wire,eof,category):
    import socket
    from aluclu.alc_r0.fixed_d_coordinator import _receive_frame
    left,right=socket.socketpair()
    try:
        left.setblocking(False); right.sendall(wire)
        if eof: right.shutdown(socket.SHUT_WR)
        with pytest.raises(ValueError,match=category): _receive_frame(left,time.monotonic_ns()+250_000_000)
    finally: left.close(); right.close()


def test_native_frame_accepts_fragmented_header_and_payload_without_resetting_deadline():
    import socket
    import threading
    from aluclu.alc_r0.fixed_d_coordinator import _receive_frame
    left,right=socket.socketpair(); stop=threading.Event(); errors=[]
    payload=canonical_json_bytes(dict(sequence='1',request_root='a'*64))
    wire=len(payload).to_bytes(4,'big')+payload
    def sender():
        try:
            for offset in range(0,len(wire),3):
                right.sendall(wire[offset:offset+3]); time.sleep(.001)
            stop.wait(.5)
        except BaseException as error: errors.append(error)
    thread=threading.Thread(target=sender,daemon=False)
    try:
        left.setblocking(False); thread.start()
        assert _receive_frame(left,time.monotonic_ns()+250_000_000)==parse_canonical_json(payload)
    finally:
        stop.set(); thread.join(1); left.close(); right.close()
    assert not thread.is_alive() and not errors


@pytest.mark.parametrize('writing',[False,True])
def test_native_channel_cancellation_interrupts_receive_or_backpressured_send(writing):
    import socket
    import threading
    from aluclu.alc_r0.fixed_d_coordinator import _receive_frame,_send_frame,CoordinatorError
    left,right=socket.socketpair(); cancel=threading.Event()
    left.setblocking(False)
    if writing:
        left.setsockopt(socket.SOL_SOCKET,socket.SO_SNDBUF,4096)
        while True:
            try: left.send(b'x'*8192)
            except BlockingIOError: break
    thread=threading.Thread(target=lambda: (time.sleep(.03),cancel.set()),daemon=False)
    started=time.monotonic_ns()
    try:
        thread.start()
        with pytest.raises(CoordinatorError,match='cancelled'):
            if writing: _send_frame(left,dict(message='bounded'),started+250_000_000,cancel)
            else: _receive_frame(left,started+250_000_000,cancel)
    finally: thread.join(1); left.close(); right.close()
    assert cancel.is_set() and not thread.is_alive()
    assert time.monotonic_ns()-started<250_000_000


def test_observer_stop_cancels_a_partial_frame_without_closing_peer(tmp_path):
    import socket
    import threading
    from aluclu.alc_r0.fixed_d_coordinator import _ObserverStop,_ChannelCancelled,_receive_frame
    left,right=socket.socketpair(); errors=[]
    deadline=time.monotonic_ns()+250_000_000
    def publish_stop():
        try:
            time.sleep(.03)
            with (tmp_path/'observer.stop.json').open('xb') as stream:
                stream.write(canonical_json_bytes(dict(domain='diagnostic-only')))
        except BaseException as error: errors.append(error)
    thread=threading.Thread(target=publish_stop,daemon=False)
    try:
        left.setblocking(False); right.sendall(b'\x00\x00'); thread.start()
        with pytest.raises(_ChannelCancelled): _receive_frame(left,deadline,_ObserverStop(tmp_path,deadline))
    finally: thread.join(1); left.close(); right.close()
    assert not thread.is_alive() and not errors and time.monotonic_ns()<deadline
