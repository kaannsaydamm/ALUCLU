"""Temporary single-generation transactions, not installed scientific authority."""
import importlib
import os
from pathlib import Path
import subprocess
import sys
import time
from dataclasses import replace

import pytest
from aluclu.alc_r0.canonical import canonical_json_bytes
from aluclu.alc_r0.operator_status import decode_operator_status,read_operator_status

ROOT='a'*64
MAX=2**63-1


def api(): return importlib.import_module('aluclu.alc_r0.status_publication')
def end(): return time.monotonic_ns()+5_000_000_000


def status(**changes):
    values=dict(schema='alc-r0-operator-status-v1',installation_root=ROOT,
        generation_root=ROOT,sequence='1',revoked=False,expires_utc_ns=str(MAX))
    values.update(changes)
    return decode_operator_status(canonical_json_bytes(values))


def store(path): return api().StatusPublicationStore(path,ROOT,ROOT)
def intent(previous,candidate): return api().prepare_status_intent(previous,candidate)


def test_initial_update_revoke_committed_read(tmp_path):
    owner=store(tmp_path); first=status()
    assert owner.publish(intent(None,first),deadline_ns=end())==first
    second=status(sequence='2',expires_utc_ns=str(MAX-1),revoked=True)
    assert owner.publish(intent(first,second),deadline_ns=end())==second
    assert owner.read(deadline_ns=end())==second
    assert api().read_committed_operator_status(tmp_path,ROOT,ROOT,deadline_ns=end())==second


@pytest.mark.parametrize('change',[dict(sequence='4'),dict(expires_utc_ns=str(MAX)),
    dict(revoked=False),dict(installation_root='b'*64),dict(generation_root='b'*64)])
def test_bad_transition_rejected(change):
    prior=status(sequence='2',expires_utc_ns=str(MAX-1),revoked=True)
    candidate=status(
        **(dict(sequence='3',expires_utc_ns=str(MAX-1),revoked=True)|change))
    with pytest.raises(ValueError): intent(prior,candidate)


@pytest.mark.parametrize('field,value',[('root','b'*64),('sequence',99),('revoked',True)])
def test_forged_status_reparsed(field,value):
    with pytest.raises(ValueError): intent(None,replace(status(),**{field:value}))


def test_forged_intent_no_mutation(tmp_path):
    item=intent(None,status())
    with pytest.raises(ValueError): store(tmp_path).publish(replace(item,root='b'*64),deadline_ns=end())
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('kind',['empty-intent','orphan-status','oversize-intent','hardlinked-intent'])
def test_uncertain_initialization_not_reset(tmp_path,kind):
    item=intent(None,status()); owner=store(tmp_path)
    path=tmp_path/'status.intent.json'
    if kind=='empty-intent': path.write_bytes(b'')
    elif kind=='orphan-status': (tmp_path/'status.json').write_bytes(status().data)
    elif kind=='oversize-intent': path.write_bytes(b'x'*16385)
    else:
        path.write_bytes(item.data); os.link(path,tmp_path/'alias.json')
    with pytest.raises((ValueError,OSError)): owner.publish(item,deadline_ns=end())
    if kind!='orphan-status': assert path.exists()


def test_stale_publication_and_third_state_recovery_refused(tmp_path):
    owner=store(tmp_path); first=status(); item=intent(None,first)
    owner.publish(item,deadline_ns=end())
    nextitem=intent(first,status(sequence='2',revoked=True))
    owner.publish(nextitem,deadline_ns=end())
    with pytest.raises(ValueError): owner.publish(nextitem,deadline_ns=end())
    (tmp_path/'status.json').write_bytes(status(sequence='3',revoked=True).data)
    with pytest.raises(ValueError): owner.recover(nextitem,deadline_ns=end())
    assert read_operator_status(tmp_path/'status.json',deadline_ns=end()).sequence==3


@pytest.mark.parametrize('kind',['initial','update'])
def test_real_crash_pending_read_denied_then_exact_forward_recovery(tmp_path,kind):
    from aluclu.alc_r0.checkpoint_owned_process import run_owned_process
    owner=store(tmp_path); first=status()
    if kind=='update': owner.publish(intent(None,first),deadline_ns=end())
    candidate=first if kind=='initial' else status(sequence='2',revoked=True)
    known=intent(None if kind=='initial' else first,candidate)
    helper=Path(__file__).with_name('alc_r0_status_publication_child.py')
    result=run_owned_process((sys.executable,'-B',str(helper),'crash-'+kind,str(tmp_path)),
        cwd=tmp_path,environment=dict(os.environ),stdout_path=tmp_path/'crash.stdout',
        stderr_path=tmp_path/'crash.stderr',deadline_ns=end())
    assert result.exit_code==17 and result.active_processes==0 and not result.timed_out
    with pytest.raises((ValueError,OSError)): owner.read(deadline_ns=end())
    fresh=run_owned_process((sys.executable,'-B',str(helper),'read',str(tmp_path)),
        cwd=tmp_path,environment=dict(os.environ),stdout_path=tmp_path/'read.stdout',
        stderr_path=tmp_path/'read.stderr',deadline_ns=end())
    assert fresh.exit_code==18 and fresh.active_processes==0 and not fresh.timed_out
    assert owner.recover(known,deadline_ns=end())==candidate
    assert owner.recover(known,deadline_ns=end())==candidate
    assert owner.read(deadline_ns=end())==candidate


def test_two_native_writers_same_predecessor_one_wins(tmp_path):
    owner=store(tmp_path); owner.publish(intent(None,status()),deadline_ns=end())
    helper=Path(__file__).with_name('alc_r0_status_publication_child.py')
    children=[subprocess.Popen((sys.executable,'-B',str(helper),mode,str(tmp_path)),
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL) for mode in ('revoke','tighten')]
    try:
        assert sorted(child.wait(timeout=5) for child in children)==[0,18]
    finally:
        for child in children:
            if child.poll() is None: child.terminate(); child.wait(timeout=2)
    assert owner.read(deadline_ns=end()).sequence==2


def test_original_expiry_before_mutation(tmp_path):
    with pytest.raises((ValueError,TimeoutError)):
        store(tmp_path).publish(intent(None,status()),deadline_ns=time.monotonic_ns()-1)
    assert not list(tmp_path.iterdir())


@pytest.mark.skipif(os.name!='nt',reason='Windows isolated unlock scheduling')
@pytest.mark.parametrize('mode',['late-unlock','late-recover'])
def test_late_unlock_never_returns_publication_success(tmp_path,mode):
    from aluclu.alc_r0.checkpoint_owned_process import run_owned_process
    helper=Path(__file__).with_name('alc_r0_status_publication_child.py')
    result=run_owned_process((sys.executable,'-B',str(helper),mode,str(tmp_path)),
        cwd=tmp_path,environment=dict(os.environ),stdout_path=tmp_path/'late.stdout',
        stderr_path=tmp_path/'late.stderr',deadline_ns=end())
    assert result.exit_code==0 and result.active_processes==0 and not result.timed_out
    assert (tmp_path/'late.stdout').read_text().strip()=='late-unlock-denied'
    assert (tmp_path/'late.stderr').read_bytes()==b''


def test_sequence_exhaustion_and_wrong_initializer():
    with pytest.raises(ValueError): intent(status(sequence=str(MAX)),status(sequence=str(MAX)))
    with pytest.raises(ValueError): intent(None,status(sequence='2'))


@pytest.mark.parametrize('data',[b'',b'{}',b'x'*16385,
    canonical_json_bytes(dict(schema='alc-r0-operator-status-intent-v1',previous_status=None,
                              candidate_status=None))])
def test_malformed_intent_decoder_is_bounded(data):
    with pytest.raises(ValueError): api().decode_status_intent(data)


@pytest.mark.parametrize('pin',['installation','generation'])
@pytest.mark.parametrize('operation',['read','publish','recover'])
def test_store_wrong_pins_deny_public_operations(tmp_path,pin,operation):
    owner=store(tmp_path); first=status(); initial=intent(None,first)
    owner.publish(initial,deadline_ns=end())
    wrong=api().StatusPublicationStore(tmp_path,'b'*64 if pin=='installation' else ROOT,
                                      'b'*64 if pin=='generation' else ROOT)
    before=(tmp_path/'status.json').read_bytes(),(tmp_path/'status.intent.json').read_bytes()
    with pytest.raises(ValueError):
        if operation=='read': wrong.read(deadline_ns=end())
        elif operation=='publish': wrong.publish(intent(first,status(sequence='2',revoked=True)),deadline_ns=end())
        else: wrong.recover(initial,deadline_ns=end())
    assert before==((tmp_path/'status.json').read_bytes(),(tmp_path/'status.intent.json').read_bytes())


@pytest.mark.parametrize('kind',['malformed','oversize','hardlink','empty'])
@pytest.mark.parametrize('operation',['read','recover'])
def test_public_intent_io_failures_never_normalize(tmp_path,kind,operation):
    owner=store(tmp_path); known=intent(None,status()); owner.publish(known,deadline_ns=end())
    path=tmp_path/'status.intent.json'
    if kind=='hardlink': os.link(path,tmp_path/'alias.json')
    else: path.write_bytes(b'{}' if kind=='malformed' else b'x'*16385 if kind=='oversize' else b'')
    before=path.read_bytes()
    with pytest.raises((ValueError,OSError)):
        if operation=='read': owner.read(deadline_ns=end())
        else: owner.recover(known,deadline_ns=end())
    assert path.read_bytes()==before


@pytest.mark.parametrize('kind',['changed-intent','missing-update-slot'])
def test_recovery_refuses_changed_intent_or_missing_update_slot(tmp_path,kind):
    owner=store(tmp_path); first=status(); owner.publish(intent(None,first),deadline_ns=end())
    known=intent(first,status(sequence='2',revoked=True)); owner.publish(known,deadline_ns=end())
    supplied=known
    if kind=='changed-intent': supplied=intent(first,status(sequence='2',expires_utc_ns=str(MAX-1)))
    else: (tmp_path/'status.json').unlink()
    with pytest.raises((ValueError,OSError)): owner.recover(supplied,deadline_ns=end())
    if kind=='missing-update-slot': assert not (tmp_path/'status.json').exists()
    else: assert owner.read(deadline_ns=end()).revoked


@pytest.mark.parametrize('kind',['missing','file','relative'])
def test_unsafe_public_store_namespace(tmp_path,kind):
    path=tmp_path/'missing' if kind=='missing' else tmp_path/'not-directory'
    if kind=='file': path.write_bytes(b'file')
    elif kind=='relative': path=Path('relative-status-namespace')
    with pytest.raises((ValueError,OSError)):
        store(path).read(deadline_ns=end())
    if kind=='missing': assert not path.exists()


@pytest.mark.skipif(os.name!='nt',reason='Windows actual junction')
def test_public_reader_rejects_junction_namespace(tmp_path):
    target=tmp_path/'target'; target.mkdir(); alias=tmp_path/'alias'
    store(target).publish(intent(None,status()),deadline_ns=end())
    assert target.resolve().is_relative_to(tmp_path.resolve())
    result=subprocess.run(('cmd.exe','/c','mklink','/J',str(alias),str(target)),
                          capture_output=True,timeout=3)
    assert result.returncode==0,result.stderr
    with pytest.raises(ValueError): store(alias).read(deadline_ns=end())


def test_actual_publication_between_intent_reads_denies_mixed_join(tmp_path):
    from aluclu.alc_r0.checkpoint_owned_process import run_owned_process
    helper=Path(__file__).with_name('alc_r0_status_publication_child.py')
    result=run_owned_process((sys.executable,'-B',str(helper),'mixed-read',str(tmp_path)),
        cwd=tmp_path,environment=dict(os.environ),stdout_path=tmp_path/'mixed.stdout',
        stderr_path=tmp_path/'mixed.stderr',deadline_ns=end())
    assert result.exit_code==0 and result.active_processes==0 and not result.timed_out
    assert (tmp_path/'mixed.stdout').read_text().strip()=='mixed-read-denied'
    assert (tmp_path/'mixed.stderr').read_bytes()==b''
