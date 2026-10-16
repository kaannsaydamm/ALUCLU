"""Open integrated accounting acceptance RED, not a standalone launch permit."""
import os
import time

import pytest

from aluclu.alc_r0.canonical import canonical_json_bytes,parse_canonical_json,sha256_bytes
from aluclu.alc_r0.reservation_store import ReservationStore
from test_alc_r0_fixed_d_coordinator import invoke,bounded_json

pytestmark=pytest.mark.skipif(os.name!='nt',reason='actual Windows diagnostic coordinator')


def test_request_only_growth_root_cannot_support_verified_materialization(tmp_path):
    namespace=tmp_path/'diagnostic'; namespace.mkdir()
    receipt=invoke(tmp_path,('diagnostic','success',str(namespace)))
    assert receipt.exit_code==0 and not receipt.timed_out and receipt.active_processes==0
    report=bounded_json(namespace/'diagnostic.result.json')
    declaration=bounded_json(namespace/'declaration.json')
    store=ReservationStore(namespace/'reservations',(canonical_json_bytes(declaration),))
    with store._lock():
        _,replay,_=store._read_locked(report['final_owner_root'])
    events=[parse_canonical_json(data) for data in replay.events]
    settlement=next(item for item in events if item['kind']=='settle_storage_held')
    request_only=sha256_bytes(canonical_json_bytes(dict(
        domain='diagnostic-only',request_root=report['request_root'])))
    assert settlement['growth_observation_root']!=request_only, (
        'request-only digest contains no inventory/capacity/tail facts; '
        'it cannot verify observed physical materialization')
    growth=bounded_json(namespace/'diagnostic.growth.json')
    assert sha256_bytes(canonical_json_bytes(growth))==settlement['growth_observation_root']
    assert report['growth_observation_root']==settlement['growth_observation_root']
    assert growth['request_root']==report['request_root']
    assert growth['prefix_owner_root']==bounded_json(namespace/'reservations'/'owner.json')['previous_owner_root']
    assert growth['accounting_kind']=='full-declarations-held-no-materialization-credit'
    assert growth['logical_kind']=='default-stream-prefix-only'
    assert growth['physical_materialization_kind']=='unknown'
    assert growth['unmeasured_publication_tail']==[
        'diagnostic.growth.json','reservations/**','diagnostic.result.json']
    assert report['storage_held'] is True
    snapshot=store.read(report['final_owner_root']).snapshot
    assert snapshot.reservations[0].state=='EXECUTION_RELEASED_STORAGE_HELD'
    assert snapshot.pending_physical_bytes==int(declaration['physical_growth_bytes'])==1<<20
    assert snapshot.pending_research_bytes==int(declaration['research_growth_bytes'])==1<<20
    assert not any(item['kind'] in ('release','reconcile') for item in events)
    rows=growth['prefix_inventory']
    assert 0<len(rows)<=128 and len({row['path'] for row in rows})==len(rows)
    assert sum(int(row['logical_bytes']) for row in rows)==int(growth['prefix_logical_bytes'])
    assert int(growth['prefix_logical_bytes'])<=1<<20
    for row in rows:
        assert row['kind'] in ('file','directory')
        if row['observation_kind']=='metadata-only-held-lock':
            assert row['path'] in ('operator/operator.lock','reservations/global.lock')
            assert row['sha256'] is None
        elif row['kind']=='file' and not row['path'].startswith('reservations/'):
            assert sha256_bytes((namespace/row['path']).read_bytes())==row['sha256']
        if row['kind']=='directory': assert row['sha256'] is None
    for capacity in (growth['capacity_before'],growth['capacity_after']):
        assert capacity['kind']=='windows-caller-available-volume-observation'
        assert int(capacity['caller_available_bytes'])-snapshot.pending_physical_bytes>=20*1024**3
        assert int(capacity['observed_monotonic_ns'])<=int(growth['finished_monotonic_ns'])


@pytest.mark.parametrize('cut',['entries','hardlink','bytes','deadline','capacity'])
def test_growth_inventory_rejects_unbounded_or_unsafe_prefix(tmp_path,cut):
    from aluclu.alc_r0.fixed_d_coordinator import _observe_growth
    from aluclu.alc_r0.runtime_tree_inventory import RuntimeInventoryError
    from aluclu.alc_r0.fixed_d_request_file import DRequestFileError
    root=tmp_path/'prefix'; root.mkdir()
    (root/'ordinary').write_bytes(b'content')
    if cut=='entries':
        for index in range(128): (root/f'node-{index}').mkdir()
    elif cut=='hardlink': os.link(root/'ordinary',root/'alias')
    elif cut=='bytes':
        with (root/'oversize').open('wb') as stream: stream.truncate((1<<20)+1)
    deadline=time.monotonic_ns()+5_000_000_000
    if cut=='deadline': deadline=time.monotonic_ns()-1
    with pytest.raises((RuntimeInventoryError,DRequestFileError,ValueError)):
        _observe_growth(root,'a'*64,'b'*64,1<<20,(1<<63)-1 if cut=='capacity' else 1<<20,deadline)
    assert not (root/'diagnostic.growth.json').exists()


def test_growth_observes_held_native_lock_without_unlock_or_false_hash(tmp_path):
    from aluclu.alc_r0.fixed_d_coordinator import _observe_growth
    from aluclu.alc_r0.deadline_file_lock import deadline_file_lock
    root=tmp_path/'prefix'; root.mkdir(); (root/'operator').mkdir()
    deadline=time.monotonic_ns()+5_000_000_000
    with deadline_file_lock(root/'operator'/'operator.lock',deadline):
        observation=_observe_growth(root,'a'*64,'b'*64,1<<20,1<<20,deadline)
    row=next(item for item in observation['prefix_inventory'] if item['path']=='operator/operator.lock')
    assert row['sha256'] is None and row['observation_kind']=='metadata-only-held-lock'
    assert row['logical_bytes']=='1'


def test_actual_output_capacity_precedes_owned_actions(tmp_path):
    namespace=tmp_path/'diagnostic'; namespace.mkdir()
    receipt=invoke(tmp_path,('diagnostic','success',str(namespace)))
    assert receipt.exit_code==0 and not receipt.timed_out and receipt.active_processes==0
    result=bounded_json(namespace/'diagnostic.result.json')
    identities={}
    for role in ('work','observer'):
        for stage in ('before-create','before-resume'):
            evidence=bounded_json(namespace/f'{role}.output.{stage}.json')
            assert evidence['domain']=='diagnostic-only' and evidence['request_root']==result['request_root']
            assert evidence['role']==role and evidence['stage']==stage
            assert {row['stream'] for row in evidence['streams']}=={'stdout','stderr'}
            action=bounded_json(namespace/f"{role}.action.{stage.removeprefix('before-')}.json")
            assert action['request_root']==result['request_root'] and action['role']==role
            assert action['action']==stage.removeprefix('before-')
            assert action['pid']==result[role]['pid']
            assert action['creation_filetime_100ns']==result[role]['creation_filetime_100ns']
            assert int(action['started_monotonic_ns'])<=int(action['finished_monotonic_ns'])<=int(result['finished_monotonic_ns'])
            for row in evidence['streams']:
                assert row['path']==f"{role}.{row['stream']}"
                assert row['limit_bytes']=='16384' and int(row['allocation_bytes'])>=16384
                assert row['eof_bytes']=='0' and row['links']=='1'
                assert int(row['inode'])>0 and int(row['device'])>=0
                assert int(result['entry_monotonic_ns'])<=int(row['observed_monotonic_ns'])<=int(result['finished_monotonic_ns'])
                assert int(row['observed_monotonic_ns'])<=int(action['started_monotonic_ns'])
                key=(role,row['stream']); identity=(row['device'],row['inode'])
                assert identities.setdefault(key,identity)==identity
    final=bounded_json(namespace/'outputs.capacity.final.json')
    assert final['request_root']==result['request_root']
    assert len(final['streams'])==4
    assert {(row['role'],row['stream']) for row in final['streams']}==set(identities)
    for row in final['streams']:
        assert row['stage']=='before-close' and int(row['allocation_bytes'])>=16384
        assert 0<=int(row['eof_bytes'])<=16384
        assert (row['device'],row['inode'])==identities[(row['role'],row['stream'])]
    declaration=bounded_json(namespace/'declaration.json')
    snapshot=ReservationStore(namespace/'reservations',(canonical_json_bytes(declaration),)).read(result['final_owner_root']).snapshot
    assert snapshot.pending_physical_bytes==snapshot.pending_research_bytes==1<<20
    assert result['scientific_execution'] is False


@pytest.mark.parametrize('excess',[False,True])
def test_preallocated_output_actual_pipe_exact_limit_and_overflow(tmp_path,excess):
    from aluclu.alc_r0.fixed_d_coordinator import _AllocatedOutputPair
    limit=16384; deadline=time.monotonic_ns()+5_000_000_000
    with _AllocatedOutputPair(stdout_path=tmp_path/'stdout',stderr_path=tmp_path/'stderr',
            stdout_limit_bytes=limit,stderr_limit_bytes=limit,cleanup_deadline_ns=deadline) as pair:
        first=pair.capacity_observations('before-create',deadline)
        assert len(first)==2 and all(int(row['allocation_bytes'])>=limit and row['eof_bytes']=='0' for row in first)
        pair.stdout.write(b'x'*limit+(b'!' if excess else b''))
        pair.close_parent_writers()
        finished=pair.finish(deadline)
    assert finished.valid is (not excess)
    assert finished.stdout.excess is excess and finished.stdout.persisted_bytes==limit
    assert finished.stdout.resources_closed and finished.stderr.resources_closed
    assert (tmp_path/'stdout').read_bytes()==b'x'*limit and (tmp_path/'stderr').read_bytes()==b''
    assert len(pair.final_capacity_observations)==2
    assert {(row['stream'],row['device'],row['inode']) for row in first}=={
        (row['stream'],row['device'],row['inode']) for row in pair.final_capacity_observations}
    assert all(int(row['allocation_bytes'])>=limit for row in pair.final_capacity_observations)
    assert sorted(int(row['eof_bytes']) for row in pair.final_capacity_observations)==[0,limit]
