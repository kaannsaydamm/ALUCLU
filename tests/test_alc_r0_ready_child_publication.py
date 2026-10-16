"""Real owned suspended sentinel joins; fake operator roots are not authority."""
import importlib
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from aluclu.alc_r0.canonical import canonical_json_bytes,parse_canonical_json
from aluclu.alc_r0.fixed_d_wire import decode_d_request
from aluclu.alc_r0.generation_binding import decode_generation,request_binding_root
from aluclu.alc_r0.control_consumption import consume_control
from aluclu.alc_r0.reservation_store import ReservationStore
from aluclu.alc_r0.reserved_owned_process import ReservedOwnedLease,OwnedStopSignal
from test_alc_r0_fixed_d_wire import request,CONTROLS

pytestmark=pytest.mark.skipif(os.name!='nt',reason='actual Windows owned lease')
ROOT='a'*64


def module(): return importlib.import_module('aluclu.alc_r0.ready_child_publication')


def fixture(tmp_path,*,consume=True,request_declaration_root=ROOT,request_clock_root=ROOT):
    directory=tmp_path/'operator'; directory.mkdir()
    storepath=tmp_path/'reservations'; storepath.mkdir(); (storepath/'intents').mkdir()
    declaration=canonical_json_bytes(dict(experiment_id='alc-r0-smollm2-135m-v1',
        reservation_id='r1',run_id=CONTROLS[0],attempt_id='a001',segment='initial',
        declaration_root=ROOT,device='cpu',useful_wall_ceiling_ns='2700000000000',
        cleanup_ceiling_ns='10000000000',charge_envelope_ns='2710000000000',
        gpu_reservation_ns='0',research_growth_bytes='1024',physical_growth_bytes='4096',
        stdout_limit_bytes='1024',stderr_limit_bytes='1024'))
    store=ReservationStore(storepath,(declaration,)); initial=store.initialize(store.initialization_intent())
    origin=time.monotonic_ns(); deadline=origin+2700000000000
    value=request(); value.update(reservation_id='r1',useful_deadline_monotonic_ns=str(deadline),
        declaration_root=request_declaration_root,clock_domain_root=request_clock_root)
    pre=decode_d_request(canonical_json_bytes(value))
    generation=decode_generation(canonical_json_bytes(dict(schema='alc-r0-operator-generation-v1',
        installation_root='c'*64,control_id=CONTROLS[0],reservation_id='r1',attempt_id='a001',
        segment='initial',request_binding_root=request_binding_root(pre))))
    value['authority_generation_root']=generation.root
    req=decode_d_request(canonical_json_bytes(value))
    if consume: consume_control(directory,generation,req,installation_root='c'*64,deadline_ns=deadline)
    event=canonical_json_bytes(dict(sequence='1',previous_root=initial.snapshot.root,
        reservation_id='r1',kind='reserve',evidence_root=ROOT,declaration_root=ROOT,
        entry_utc_ns=str(time.time_ns()),clock_domain_root=ROOT,entry_monotonic_ns=str(origin),
        useful_deadline_monotonic_ns=str(deadline)))
    reserved=store.commit(store.prepare(initial.sha256,event,ROOT))
    sentinel=tmp_path/'sentinel'
    source=f"from pathlib import Path; Path({str(sentinel)!r}).write_text('executed')"
    arguments=dict(store=store,expected_owner_root=reserved.sha256,reservation_id='r1',
        command=(sys.executable,'-I','-c',source),cwd=tmp_path,environment=dict(os.environ),
        stdout_path=tmp_path/'stdout.log',stderr_path=tmp_path/'stderr.log',
        deadline_ns=deadline,clock_domain_root=ROOT)
    return directory,generation,req,arguments,sentinel


def publish(directory,generation,req,lease,ready,**overrides):
    arguments=dict(installation_root='c'*64,lease=lease,ready_owner_root=ready.sha256,
                   deadline_ns=lease._deadline)
    arguments.update(overrides)
    return module().publish_ready_child(directory,generation,req,**arguments)


def test_owned_ready_binding_before_explicit_resume(tmp_path):
    directory,gen,req,arguments,sentinel=fixture(tmp_path)
    with ReservedOwnedLease(**arguments) as lease:
        assert not sentinel.exists()
        ready=lease.publish_identity(ROOT,ROOT)
        binding=publish(directory,gen,req,lease,ready)
        assert not sentinel.exists()
        value=parse_canonical_json(binding.data)
        assert int(value['pid'])==lease.identity.pid
        assert int(value['creation_filetime_100ns'])==lease.identity.creation_filetime_100ns
        reopened=module().read_ready_child(directory,gen,req,installation_root='c'*64,
            identity=lease.identity,ready_owner_root=ready.sha256,deadline_ns=lease._deadline)
        assert reopened==binding
        lease.resume_verified(ready.sha256)
        terminal=lease.wait_terminal()
        assert terminal.process.exit_code==0 and terminal.process.active_processes==0
        assert terminal.output.valid
    assert sentinel.read_text()=='executed'


def test_close_after_publication_never_runs_or_releases(tmp_path):
    directory,gen,req,arguments,sentinel=fixture(tmp_path)
    with ReservedOwnedLease(**arguments) as lease:
        ready=lease.publish_identity(ROOT,ROOT)
        publish(directory,gen,req,lease,ready)
    assert not sentinel.exists()
    assert (directory/'d-cpu-fresh1.consumed.json').exists()
    assert (directory/'d-cpu-fresh1.child.json').exists()
    assert arguments['store'].read(ready.sha256).snapshot.reservations[0].state=='READY'


@pytest.mark.parametrize('kind',['missing','corrupt','mismatch'])
def test_consumption_bad_no_child_publication(tmp_path,kind):
    directory,gen,req,arguments,sentinel=fixture(tmp_path,consume=kind!='missing')
    if kind!='missing':
        path=directory/'d-cpu-fresh1.consumed.json'
        if kind=='corrupt': path.write_bytes(b'{}')
        else:
            value=parse_canonical_json(path.read_bytes()); value['generation_root']='f'*64
            path.write_bytes(canonical_json_bytes(value))
    with ReservedOwnedLease(**arguments) as lease:
        ready=lease.publish_identity(ROOT,ROOT)
        with pytest.raises(module().ReadyPublicationError): publish(directory,gen,req,lease,ready)
        assert not sentinel.exists() and not (directory/'d-cpu-fresh1.child.json').exists()


@pytest.mark.parametrize('kind',['root','deadline','request','generation'])
def test_wrong_pins_no_publication(tmp_path,kind):
    directory,gen,req,arguments,sentinel=fixture(tmp_path)
    with ReservedOwnedLease(**arguments) as lease:
        ready=lease.publish_identity(ROOT,ROOT); overrides={}
        if kind=='root': overrides['ready_owner_root']='f'*64
        elif kind=='deadline': overrides['deadline_ns']=lease._deadline-1
        elif kind=='request': req=replace(req,root='f'*64)
        else: gen=replace(gen,root='f'*64)
        with pytest.raises(module().ReadyPublicationError): publish(directory,gen,req,lease,ready,**overrides)
        assert not sentinel.exists() and not (directory/'d-cpu-fresh1.child.json').exists()


def test_nonready_and_duplicate_refused(tmp_path):
    directory,gen,req,arguments,sentinel=fixture(tmp_path)
    with ReservedOwnedLease(**arguments) as lease:
        with pytest.raises(module().ReadyPublicationError):
            module().publish_ready_child(directory,gen,req,installation_root='c'*64,lease=lease,
                ready_owner_root=ROOT,deadline_ns=lease._deadline)
        ready=lease.publish_identity(ROOT,ROOT)
        publish(directory,gen,req,lease,ready)
        with pytest.raises(module().ReadyPublicationError): publish(directory,gen,req,lease,ready)
        assert not sentinel.exists()


@pytest.mark.parametrize('field',['declaration','clock'])
def test_actual_reopened_declaration_or_clock_mismatch(tmp_path,field):
    options={'request_declaration_root':'f'*64} if field=='declaration' else {'request_clock_root':'f'*64}
    directory,gen,req,arguments,sentinel=fixture(tmp_path,**options)
    with ReservedOwnedLease(**arguments) as lease:
        ready=lease.publish_identity(ROOT,ROOT)
        with pytest.raises(module().ReadyPublicationError): publish(directory,gen,req,lease,ready)
        assert not sentinel.exists() and not (directory/'d-cpu-fresh1.child.json').exists()


def test_wrong_creating_thread_rejected(tmp_path):
    directory,gen,req,arguments,sentinel=fixture(tmp_path)
    with ReservedOwnedLease(**arguments) as lease:
        ready=lease.publish_identity(ROOT,ROOT)
        with ThreadPoolExecutor(max_workers=1) as executor:
            future=executor.submit(publish,directory,gen,req,lease,ready)
            with pytest.raises(module().ReadyPublicationError): future.result(timeout=2)
        assert not sentinel.exists() and not (directory/'d-cpu-fresh1.child.json').exists()


def test_owned_stop_latch_denies_publication(tmp_path):
    directory,gen,req,arguments,sentinel=fixture(tmp_path)
    signal=OwnedStopSignal(); arguments['stop_signal']=signal
    with ReservedOwnedLease(**arguments) as lease:
        ready=lease.publish_identity(ROOT,ROOT)
        signal.request_stop()
        with pytest.raises(module().ReadyPublicationError): publish(directory,gen,req,lease,ready)
        assert not sentinel.exists() and not (directory/'d-cpu-fresh1.child.json').exists()


def test_lease_lookalike_never_runs_hooks(tmp_path):
    directory,gen,req,arguments,_=fixture(tmp_path)
    class Trap:
        def __getattribute__(self,name): raise AssertionError('lease lookalike hook called')
    with pytest.raises(module().ReadyPublicationError):
        module().publish_ready_child(directory,gen,req,installation_root='c'*64,lease=Trap(),
            ready_owner_root=ROOT,deadline_ns=arguments['deadline_ns'])
    assert not (directory/'d-cpu-fresh1.child.json').exists()
