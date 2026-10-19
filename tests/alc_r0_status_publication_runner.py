"""Closed temporary transaction diagnostics under original owned job deadline."""
import json
import os
from pathlib import Path
import sys
import time
from dataclasses import asdict
from aluclu.alc_r0.checkpoint_owned_process import run_owned_process


def main():
    entry=time.monotonic_ns()
    if len(sys.argv)!=2 or sys.argv[1] not in ('red','green','regression','red_late','green_v2','regression_v2','green_v3','regression_v3'): raise ValueError('closed mode')
    mode=sys.argv[1]; cwd=Path(__file__).resolve().parents[1]
    stem=cwd/'results'/f'alc_r0_status_publication_{mode}_20261013'
    paths={s:Path(str(stem)+s) for s in ('.stdout.log','.stderr.log','.xml','.exit.json')}
    if any(p.exists() for p in paths.values()): raise FileExistsError('evidence exists')
    args=['tests/test_alc_r0_status_publication.py']
    if mode=='red': args+=['-k','initial_update_revoke']
    elif mode=='red_late': args+=['-k','late_unlock']
    elif mode in ('regression','regression_v2','regression_v3'): args+=['tests/test_alc_r0_operator_status.py',
        'tests/test_alc_r0_deadline_file_lock.py','tests/test_alc_r0_control_consumption.py']
    env=os.environ.copy(); env.update(PYTHONPATH=str(cwd/'src'),PYTHONNOUSERSITE='1',
        PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',CUDA_VISIBLE_DEVICES='-1')
    receipt=run_owned_process((sys.executable,'-m','pytest','-q',*args,'--junitxml='+str(paths['.xml'])),
        cwd=cwd,environment=env,stdout_path=paths['.stdout.log'],stderr_path=paths['.stderr.log'],
        deadline_ns=entry+120_000_000_000)
    data=json.dumps(dict(asdict(receipt),pytest_exit_code=receipt.exit_code,parent_bound_seconds=120,
        scope='temporary-status-publication'),sort_keys=True,separators=(',',':')).encode()
    with paths['.exit.json'].open('xb') as stream: stream.write(data)
    print(data.decode())


if __name__=='__main__': main()
