"""Closed temporary persistence tests in owned job; never scientific authority."""
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path
from aluclu.alc_r0.checkpoint_owned_process import run_owned_process


def main():
    entry=time.monotonic_ns()
    if len(sys.argv)!=2 or sys.argv[1] not in ('red','green','regression'):
        raise ValueError('closed consumption mode required')
    mode=sys.argv[1]; cwd=Path(__file__).resolve().parents[1]
    stem=cwd/'results'/f'alc_r0_control_consumption_{mode}_20261013'
    paths={s:Path(str(stem)+s) for s in ('.stdout.log','.stderr.log','.xml','.exit.json')}
    if any(p.exists() for p in paths.values()): raise FileExistsError('evidence exists')
    arguments=['tests/test_alc_r0_control_consumption.py']
    if mode=='red': arguments+=['-k','first_publication']
    elif mode=='regression':
        arguments+=['tests/test_alc_r0_generation_binding.py','tests/test_alc_r0_operator_status.py',
                    'tests/test_alc_r0_fixed_d_request_file.py','tests/test_alc_r0_d_reservation_identity.py']
    environment=os.environ.copy()
    environment.update(PYTHONPATH=str(cwd/'src'),PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',
                       PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',CUDA_VISIBLE_DEVICES='-1')
    receipt=run_owned_process((sys.executable,'-m','pytest','-q',*arguments,
        '--junitxml='+str(paths['.xml'])),cwd=cwd,environment=environment,
        stdout_path=paths['.stdout.log'],stderr_path=paths['.stderr.log'],
        deadline_ns=entry+120_000_000_000)
    data=json.dumps(dict(asdict(receipt),pytest_exit_code=receipt.exit_code,
        parent_bound_seconds=120,scope='temporary-control-consumption'),sort_keys=True,separators=(',',':')).encode()
    with paths['.exit.json'].open('xb') as output: output.write(data)
    print(data.decode())


if __name__=='__main__': main()
