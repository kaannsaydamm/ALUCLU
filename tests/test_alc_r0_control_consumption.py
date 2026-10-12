"""Real temporary persistence and harmless process crash, no scientific job."""
import importlib
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

import pytest
from aluclu.alc_r0.canonical import canonical_json_bytes,parse_canonical_json
from aluclu.alc_r0.fixed_d_wire import decode_d_request
from test_alc_r0_generation_binding import fixture
from test_alc_r0_fixed_d_wire import CONTROLS


def module():
    return importlib.import_module('aluclu.alc_r0.control_consumption')


def consume(directory,gen,req,**options):
    arguments=dict(installation_root='c'*64,deadline_ns=time.monotonic_ns()+10**9)
    arguments.update(options)
    return module().consume_control(directory,gen,req,**arguments)


@pytest.mark.parametrize('control',CONTROLS)
def test_first_publication_and_reopen(tmp_path,control):
    gen,req,_,_=fixture(control)
    receipt=consume(tmp_path,gen,req)
    reopened=module().read_consumption(tmp_path,control,deadline_ns=time.monotonic_ns()+10**9)
    assert reopened==receipt
    assert parse_canonical_json(reopened.data)['request_root']==req.root
    with pytest.raises(module().ControlConsumptionError): consume(tmp_path,gen,req)


def test_three_controls_are_independent(tmp_path):
    for control in CONTROLS:
        gen,req,_,_=fixture(control)
        consume(tmp_path,gen,req)
    assert len(list(tmp_path.iterdir()))==3


@pytest.mark.parametrize('kind',['empty','truncated','corrupt','directory'])
def test_existing_uncertain_claim_never_available(tmp_path,kind):
    gen,req,_,_=fixture()
    target=tmp_path/'d-cpu-fresh1.consumed.json'
    if kind=='directory': target.mkdir()
    else: target.write_bytes({'empty':b'','truncated':b'{','corrupt':b'wrong'}[kind])
    before=target.read_bytes() if target.is_file() else None
    with pytest.raises(module().ControlConsumptionError): consume(tmp_path,gen,req)
    assert target.exists()
    if before is not None: assert target.read_bytes()==before


@pytest.mark.parametrize('kind',['deadline','request_root','generation_root','installation'])
def test_invalid_before_mutation(tmp_path,kind):
    gen,req,_,_=fixture()
    options={}
    if kind=='deadline': options['deadline_ns']=1
    elif kind=='request_root': req=replace(req,root='f'*64)
    elif kind=='generation_root': gen=replace(gen,root='f'*64)
    else: options['installation_root']='f'*64
    with pytest.raises(module().ControlConsumptionError): consume(tmp_path,gen,req,**options)
    assert list(tmp_path.iterdir())==[]


def test_changed_generation_installation_cannot_reuse(tmp_path):
    gen,req,_,_=fixture()
    consume(tmp_path,gen,req)
    value=parse_canonical_json(req.data); value['reservation_id']='other'
    initial=decode_d_request(canonical_json_bytes(value))
    from aluclu.alc_r0.generation_binding import decode_generation,request_binding_root
    changed=parse_canonical_json(gen.data)
    changed.update(installation_root='f'*64,reservation_id='other',
                   request_binding_root=request_binding_root(initial))
    gen=decode_generation(canonical_json_bytes(changed))
    value['authority_generation_root']=gen.root
    req=decode_d_request(canonical_json_bytes(value))
    with pytest.raises(module().ControlConsumptionError):
        consume(tmp_path,gen,req,installation_root='f'*64)


def test_concurrent_writers_one_winner(tmp_path):
    gen,req,_,_=fixture()
    def attempt(_):
        try: consume(tmp_path,gen,req); return True
        except module().ControlConsumptionError: return False
    with ThreadPoolExecutor(max_workers=8) as executor:
        outcomes=list(executor.map(attempt,range(8)))
    assert outcomes.count(True)==1
    module().read_consumption(tmp_path,CONTROLS[0],deadline_ns=time.monotonic_ns()+10**9)


def test_abrupt_process_after_claim_stays_consumed(tmp_path):
    # Harmless child is covered by the outer owned pytest job; no model/workload.
    child=str(Path(__file__).with_name('alc_r0_control_claim_child.py'))
    command=(sys.executable,'-B',child,'crash',str(tmp_path))
    result=subprocess.run(command,capture_output=True,timeout=5,check=False)
    assert result.returncode==17 and result.stdout==b'' and result.stderr==b''
    assert (tmp_path/'d-cpu-fresh1.consumed.json').read_bytes()==b''
    fresh=subprocess.run((sys.executable,'-B',child,'consume',str(tmp_path)),
                         capture_output=True,timeout=5,check=False)
    assert fresh.returncode==18 and fresh.stdout==b'' and fresh.stderr==b''
    gen,req,_,_=fixture()
    with pytest.raises(module().ControlConsumptionError): consume(tmp_path,gen,req)


def test_cross_process_writers_one_winner(tmp_path):
    command=(sys.executable,'-B',str(Path(__file__).with_name('alc_r0_control_claim_child.py')),
             'consume',str(tmp_path))
    children=[]
    try:
        for _ in range(4): children.append(subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE))
        results=[]
        for child in children:
            out,err=child.communicate(timeout=5)
            assert out==b'' and err==b''
            results.append(child.returncode)
        assert results.count(0)==1 and results.count(18)==3
    finally:
        for child in children:
            if child.poll() is None: child.kill(); child.communicate(timeout=5)


def test_wrong_read_control_or_corrupt_record(tmp_path):
    gen,req,_,_=fixture()
    consume(tmp_path,gen,req)
    with pytest.raises(module().ControlConsumptionError):
        module().read_consumption(tmp_path,'other',deadline_ns=time.monotonic_ns()+10**9)
    path=tmp_path/'d-cpu-fresh1.consumed.json'
    # Controlled corruption is testing-only, never an automatic recovery API.
    path.write_bytes(b'{}')
    with pytest.raises(module().ControlConsumptionError):
        module().read_consumption(tmp_path,CONTROLS[0],deadline_ns=time.monotonic_ns()+10**9)
