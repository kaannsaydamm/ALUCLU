"""Closed crash/race diagnostics in temporary namespace, no scientific child."""
import os
from pathlib import Path
import sys
import time
from test_alc_r0_status_publication import ROOT,status
from aluclu.alc_r0.status_publication import StatusPublicationStore,prepare_status_intent


def main():
    if len(sys.argv)!=3 or sys.argv[1] not in ('crash-initial','crash-update','read','revoke','tighten','late-unlock','late-recover','mixed-read'):
        raise ValueError('closed temporary publication mode')
    mode=sys.argv[1]; directory=Path(sys.argv[2]); deadline=time.monotonic_ns()+5_000_000_000
    class CrashStore(StatusPublicationStore):
        def _persist_intent(self,*args,**kwargs):
            super()._persist_intent(*args,**kwargs)
            os._exit(17)
    owner=(CrashStore if mode.startswith('crash-') else StatusPublicationStore)(directory,ROOT,ROOT)
    if mode=='mixed-read':
        first=status(); owner.publish(prepare_status_intent(None,first),deadline_ns=deadline)
        update=prepare_status_intent(first,status(sequence='2',expires_utc_ns=str(2**63-2)))
        reads=0; armed=True
        def publish_between_reads(event,args):
            nonlocal reads,armed
            if armed and event=='open' and args[0]==str(directory/'status.intent.json'):
                reads+=1
                if reads==2:
                    armed=False  # isolate only the scheduled outer read, no recursion
                    owner.publish(update,deadline_ns=deadline)
        sys.addaudithook(publish_between_reads)
        try: owner.read(deadline_ns=deadline)
        except ValueError: pass
        else: raise AssertionError('mixed transaction accepted')
        assert reads==2 and not armed
        assert owner.read(deadline_ns=deadline).sequence==2
        print('mixed-read-denied')
        return
    if mode in ('late-unlock','late-recover'):
        known=prepare_status_intent(None,status())
        if mode=='late-recover': owner.publish(known,deadline_ns=deadline)
        deadline=time.monotonic_ns()+1_000_000_000
        observed=[]
        def delay_unlock(event,args):
            if event=='msvcrt.locking' and args[1]==0:
                observed.append(True)
                while time.monotonic_ns()<deadline: time.sleep(.002)
        sys.addaudithook(delay_unlock)  # isolated diagnostic, not parent mutation
        try:
            (owner.publish if mode=='late-unlock' else owner.recover)(known,deadline_ns=deadline)
        except TimeoutError: pass
        else: raise AssertionError('publication success returned after original deadline')
        assert observed==[True]
        assert owner.read(deadline_ns=time.monotonic_ns()+2_000_000_000)==status()
        print('late-unlock-denied')
        return
    try:
        if mode=='read': owner.read(deadline_ns=deadline); return
        first=status()
        candidate=first if mode=='crash-initial' else status(sequence='2',
            revoked=mode!='tighten',expires_utc_ns=str(2**63-2 if mode=='tighten' else 2**63-1))
        item=prepare_status_intent(None if mode=='crash-initial' else first,candidate)
        owner.publish(item,deadline_ns=deadline)
    except (ValueError,OSError,TimeoutError): raise SystemExit(18)


if __name__=='__main__': main()
