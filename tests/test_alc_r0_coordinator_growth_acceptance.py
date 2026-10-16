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
