"""Closed owned real sentinel publication tests, not an experiment launcher."""
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path
from aluclu.alc_r0.checkpoint_owned_process import run_owned_process


def main():
    entry=time.monotonic_ns()
    if len(sys.argv)!=2 or sys.argv[1] not in ('red','green','regression','green_v2','regression_v2'):
        raise ValueError('closed READY test mode required')
    mode=sys.argv[1]; bound=300 if mode in ('regression','regression_v2') else 120
    cwd=Path(__file__).resolve().parents[1]
    stem=cwd/'results'/f'alc_r0_ready_child_{mode}_20261013'
    paths={s:Path(str(stem)+s) for s in ('.stdout.log','.stderr.log','.xml','.exit.json')}
    if any(p.exists() for p in paths.values()): raise FileExistsError('evidence exists')
    arguments=['tests/test_alc_r0_ready_child_publication.py']
    if mode=='red': arguments+=['-k','owned_ready_binding']
    elif mode in ('regression','regression_v2'):
        arguments+=['tests/test_alc_r0_reserved_owned_process.py','tests/test_alc_r0_control_consumption.py',
                    'tests/test_alc_r0_generation_binding.py','tests/test_alc_r0_operator_status.py']
    environment=os.environ.copy()
    environment.update(PYTHONPATH=str(cwd/'src'),PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',
                       PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',CUDA_VISIBLE_DEVICES='-1')
    receipt=run_owned_process((sys.executable,'-m','pytest','-q',*arguments,
        '--junitxml='+str(paths['.xml'])),cwd=cwd,environment=environment,
        stdout_path=paths['.stdout.log'],stderr_path=paths['.stderr.log'],
        deadline_ns=entry+bound*10**9)
    data=json.dumps(dict(asdict(receipt),pytest_exit_code=receipt.exit_code,parent_bound_seconds=bound,
        scope='real-harmless-ready-publication'),sort_keys=True,separators=(',',':')).encode()
    with paths['.exit.json'].open('xb') as output: output.write(data)
    print(data.decode())


if __name__=='__main__': main()
