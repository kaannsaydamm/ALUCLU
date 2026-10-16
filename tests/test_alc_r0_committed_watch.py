"""Committed-reader cancellation diagnostics, no installed scientific source."""
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import pytest
from aluclu.alc_r0.authority_watch_policy import WatchPolicy
from aluclu.alc_r0.live_authority_watch import LiveAuthorityWatch
from aluclu.alc_r0.reserved_owned_process import OwnedStopSignal,OwnedStopRequested,ReservedOwnedLease
from aluclu.alc_r0.status_watch_consumer import StatusWatchConsumer
from aluclu.alc_r0.status_publication import StatusPublicationStore,prepare_status_intent
from aluclu.alc_r0.operator_status import read_operator_status
from test_alc_r0_status_publication import ROOT,status


def context(tmp_path):
    owner=StatusPublicationStore(tmp_path,ROOT,ROOT)
    owner.publish(prepare_status_intent(None,status()),deadline_ns=time.monotonic_ns()+5_000_000_000)
    signal=OwnedStopSignal()
    deadline=time.monotonic_ns()+5_000_000_000
    watch=LiveAuthorityWatch(WatchPolicy(ROOT,ROOT,deadline,deadline+10_000_000_000),signal)
    consumer=StatusWatchConsumer(ROOT,ROOT,ROOT,signal)
    return owner,signal,watch,consumer,deadline


def serve(consumer,watch,path):
    return consumer.serve_committed_once(watch,path,time.time_ns(),
                                        utc_anchor_monotonic_ns=time.monotonic_ns())


def test_committed_service_queues_original_request(tmp_path):
    _,signal,watch,consumer,deadline=context(tmp_path)
    try:
        watch.start()
        assert serve(consumer,watch,tmp_path)
        assert not signal._event.is_set() and consumer._last==status()
    finally: watch.close(deadline+10_000_000_000)


def test_same_source_accepts_normally_committed_next_sequence(tmp_path):
    owner,signal,watch,consumer,deadline=context(tmp_path)
    try:
        watch.start(); assert serve(consumer,watch,tmp_path)
        original_policy=consumer._policy
        candidate=status(sequence='2',expires_utc_ns=str(2**63-2))
        assert owner.publish(prepare_status_intent(status(),candidate),deadline_ns=deadline)==candidate
        until=time.monotonic()+2
        while consumer._last!=candidate:
            assert time.monotonic()<until
            serve(consumer,watch,tmp_path)
        assert not signal._event.is_set()
        assert consumer._policy is original_policy and consumer._last.sequence==2
    finally: watch.close(deadline+10_000_000_000)


def test_repeated_same_source_cannot_extend_original_useful_deadline(tmp_path):
    owner,_,old_watch,_,old_deadline=context(tmp_path)
    old_watch.close(old_deadline+10_000_000_000)
    signal=OwnedStopSignal()
    deadline=time.monotonic_ns()+800_000_000
    policy=WatchPolicy(ROOT,ROOT,deadline,deadline+10_000_000_000)
    watch=LiveAuthorityWatch(policy,signal)
    consumer=StatusWatchConsumer(ROOT,ROOT,ROOT,signal)
    queued=0
    try:
        watch.start()
        while time.monotonic_ns()<deadline and not signal._event.is_set():
            try: queued+=int(serve(consumer,watch,tmp_path))
            except ValueError:
                assert time.monotonic_ns()>=deadline
        assert queued>=2
        # Same source after the original deadline cannot create a new window.
        while time.monotonic_ns()<deadline: time.sleep(.001)
        with pytest.raises(ValueError): serve(consumer,watch,tmp_path)
        assert signal._event.is_set() and consumer._policy is policy
        assert policy.useful_deadline_ns==deadline
    finally: watch.close(policy.envelope_deadline_ns)


@pytest.mark.parametrize('kind',['unknown','COMMITTED',None,1])
def test_private_unknown_route_kind_denies_before_request(tmp_path,kind):
    _,signal,watch,consumer,deadline=context(tmp_path)
    try:
        # Unstarted watch has no request. Closed-kind rejection still comes first.
        with pytest.raises(ValueError):
            consumer._serve_once(watch,tmp_path,time.time_ns(),time.monotonic_ns(),kind)
        assert signal._event.is_set() and consumer._source is None
    finally: watch.close(deadline+10_000_000_000)


@pytest.mark.parametrize('kind',['missing','empty','corrupt'])
def test_bad_intent_never_falls_back_to_valid_raw_slot(tmp_path,kind):
    _,signal,watch,consumer,deadline=context(tmp_path)
    path=tmp_path/'status.intent.json'
    if kind=='missing': path.unlink()
    else: path.write_bytes(b'' if kind=='empty' else b'{}')
    assert not read_operator_status(tmp_path/'status.json',deadline_ns=deadline).revoked
    try:
        watch.start()
        with pytest.raises((ValueError,OSError)): serve(consumer,watch,tmp_path)
        assert signal._event.is_set()
        with pytest.raises(ValueError):
            consumer.serve_once(watch,tmp_path/'status.json',time.time_ns(),
                                utc_anchor_monotonic_ns=time.monotonic_ns())
    finally: watch.close(deadline+10_000_000_000)


@pytest.mark.parametrize('change',['downgrade','upgrade','path'])
def test_source_kind_and_path_change_deny_before_next_read(tmp_path,change):
    _,signal,watch,consumer,deadline=context(tmp_path)
    try:
        watch.start()
        if change=='upgrade':
            assert consumer.serve_once(watch,tmp_path/'status.json',time.time_ns(),
                                      utc_anchor_monotonic_ns=time.monotonic_ns())
        else: assert serve(consumer,watch,tmp_path)
        with pytest.raises(ValueError):
            if change=='downgrade':
                consumer.serve_once(watch,tmp_path/'status.json',time.time_ns(),
                                    utc_anchor_monotonic_ns=time.monotonic_ns())
            else: serve(consumer,watch,tmp_path/'different' if change=='path' else tmp_path)
        assert signal._event.is_set()
    finally: watch.close(deadline+10_000_000_000)


def test_forward_repair_cannot_resurrect_denied_consumer(tmp_path):
    owner,signal,watch,consumer,deadline=context(tmp_path)
    class PublishedIntent(RuntimeError): pass
    class InterruptedPublisher(StatusPublicationStore):
        def _persist_intent(self,*args,**kwargs):
            super()._persist_intent(*args,**kwargs)
            raise PublishedIntent()
    candidate=status(sequence='2',expires_utc_ns=str(2**63-2))
    known=prepare_status_intent(status(),candidate)
    try:
        watch.start(); assert serve(consumer,watch,tmp_path)
        with pytest.raises(PublishedIntent):
            InterruptedPublisher(tmp_path,ROOT,ROOT).publish(known,deadline_ns=deadline)
        until=time.monotonic()+2; refused=False
        while not signal._event.is_set() and time.monotonic()<until:
            try: serve(consumer,watch,tmp_path)
            except (ValueError,OSError): refused=True
        assert refused and signal._event.is_set()
        assert owner.recover(known,deadline_ns=deadline)==candidate
        with pytest.raises(ValueError): serve(consumer,watch,tmp_path)
    finally: watch.close(deadline+10_000_000_000)


@pytest.mark.parametrize('value',[None,b'bytes',Path('relative'),object()])
def test_invalid_source_type_or_namespace_latches_stop(tmp_path,value):
    _,signal,watch,consumer,deadline=context(tmp_path)
    try:
        watch.start()
        with pytest.raises((ValueError,TypeError)): serve(consumer,watch,value)
        assert signal._event.is_set()
    finally: watch.close(deadline+10_000_000_000)


@pytest.mark.parametrize('pin',['installation','generation'])
def test_committed_reader_uses_consumers_original_roots(tmp_path,pin):
    _,signal,old_watch,_,deadline=context(tmp_path)
    old_watch.close(deadline+10_000_000_000)
    signal=OwnedStopSignal()
    generation='b'*64 if pin=='generation' else ROOT
    watch=LiveAuthorityWatch(WatchPolicy(generation,ROOT,deadline,deadline+10_000_000_000),signal)
    consumer=StatusWatchConsumer('b'*64 if pin=='installation' else ROOT,generation,ROOT,signal)
    try:
        watch.start()
        with pytest.raises(ValueError): serve(consumer,watch,tmp_path)
        assert signal._event.is_set()
    finally: watch.close(deadline+10_000_000_000)


@pytest.mark.skipif(os.name!='nt',reason='Windows normalized path spelling')
def test_case_spelling_change_does_not_silently_rebind(tmp_path):
    _,signal,watch,consumer,deadline=context(tmp_path)
    try:
        watch.start(); assert serve(consumer,watch,tmp_path)
        with pytest.raises(ValueError): serve(consumer,watch,str(tmp_path).swapcase())
        assert signal._event.is_set()
    finally: watch.close(deadline+10_000_000_000)


@pytest.mark.skipif(os.name!='nt',reason='Windows actual owned tree')
@pytest.mark.parametrize('kind',['held-publisher','crashed-publisher'])
def test_pending_publication_stops_actual_owned_tree_before_repair(tmp_path,kind):
    from test_alc_r0_reserved_owned_process import fixture as lease_fixture
    from test_alc_r0_owned_stop import RetainedHandles,closed,pending
    from aluclu.alc_r0.checkpoint_owned_process import run_owned_process
    directory=tmp_path/'operator'; directory.mkdir()
    owner=StatusPublicationStore(directory,ROOT,ROOT)
    owner.publish(prepare_status_intent(None,status()),deadline_ns=time.monotonic_ns()+5_000_000_000)
    source=("import subprocess,sys,time;"
        "subprocess.Popen([sys.executable,'-I','-c','import time;time.sleep(60)']);time.sleep(60)")
    arguments,reservations,_,_=lease_fixture(tmp_path,source=source)
    signal=OwnedStopSignal(); watch=retained=producer=publisher=None
    first=threading.Event(); persisted=threading.Event(); release=threading.Event()
    producer_errors=[]; publisher_errors=[]; published=[]
    unrelated=subprocess.Popen((sys.executable,'-I','-c','import time;time.sleep(60)'))
    try:
        with ReservedOwnedLease(**arguments,stop_signal=signal) as lease:
            retained=RetainedHandles(lease); ready=lease.publish_identity(ROOT,ROOT)
            deadline=arguments['deadline_ns']
            watch=LiveAuthorityWatch(WatchPolicy(ROOT,ROOT,deadline,deadline+10_000_000_000),signal)
            watch.start()
            def provide():
                consumer=StatusWatchConsumer(ROOT,ROOT,ROOT,signal)
                try:
                    while not signal._event.is_set():
                        if serve(consumer,watch,directory): first.set()
                except BaseException as error: producer_errors.append(error)
            producer=threading.Thread(target=provide); producer.start()
            assert first.wait(2)
            lease.resume_verified(ready.sha256)
            until=time.monotonic()+3
            while lease._job.accounting().active_processes<2:
                assert time.monotonic()<until; time.sleep(.01)
            candidate=status(sequence='2',expires_utc_ns=str(2**63-2))
            known=prepare_status_intent(status(),candidate)
            if kind=='held-publisher':
                class PausedPublisher(StatusPublicationStore):
                    def _persist_intent(self,*args,**kwargs):
                        super()._persist_intent(*args,**kwargs)
                        persisted.set()
                        if not release.wait(max(0,deadline-time.monotonic_ns())/1e9):
                            raise TimeoutError('original publisher gate expired')
                def publish():
                    try:
                        published.append(PausedPublisher(directory,ROOT,ROOT).publish(known,deadline_ns=deadline))
                    except BaseException as error: publisher_errors.append(error)
                publisher=threading.Thread(target=publish); publisher.start()
                assert persisted.wait(2) and publisher.is_alive() and not release.is_set()
            else:
                helper=Path(__file__).with_name('alc_r0_status_publication_child.py')
                result=run_owned_process((sys.executable,'-B',str(helper),'crash-update',str(directory)),
                    cwd=tmp_path,environment=dict(os.environ),stdout_path=tmp_path/'publisher.stdout',
                    stderr_path=tmp_path/'publisher.stderr',deadline_ns=deadline)
                assert result.exit_code==17 and result.active_processes==0 and not result.timed_out
            # Individual raw slot remains valid/nonrevoked: only committed join denies.
            assert read_operator_status(directory/'status.json',deadline_ns=deadline)==status()
            assert signal._event.wait(2)
            with pytest.raises(OwnedStopRequested): lease.wait_terminal()
            watch.close(lease._cleanup_deadline)
            producer.join(max(0,lease._cleanup_deadline-time.monotonic_ns())/1e9)
            assert not producer.is_alive() and len(producer_errors)==1
            assert isinstance(producer_errors[0],(ValueError,OSError))
            retained.drained(total=2); closed(lease)
            if publisher:
                assert publisher.is_alive() and not release.is_set() and not published
                release.set()
                publisher.join(max(0,lease._cleanup_deadline-time.monotonic_ns())/1e9)
                assert not publisher.is_alive() and not publisher_errors and published==[candidate]
            else:
                # Crash helper publishes revoked candidate; caller pins that exact intent.
                repaired=owner.recover(prepare_status_intent(status(),status(sequence='2',revoked=True)),
                                       deadline_ns=deadline)
                assert repaired.revoked
            with pytest.raises(OwnedStopRequested): lease._check_stop()
        pending(reservations,'RUNNING')
        assert unrelated.poll() is None
    finally:
        release.set()
        if watch: watch.close(lease._cleanup_deadline)
        for thread in (producer,publisher):
            if thread:
                thread.join(max(0,lease._cleanup_deadline-time.monotonic_ns())/1e9)
                assert not thread.is_alive()
        if retained: retained.close()
        unrelated.terminate(); unrelated.wait(timeout=10)
