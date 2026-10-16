"""Closed owned synthetic repeat diagnostics, no model or GPU."""
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path
from aluclu.alc_r0.checkpoint_owned_process import run_owned_process


def main():
    entry = time.monotonic_ns()
    if len(sys.argv)!=2 or sys.argv[1] not in ('red','green','green_v2','regression'):
        raise ValueError('closed diagnostic mode required')
    mode = sys.argv[1]
    cwd = Path(__file__).resolve().parents[1]
    stem = cwd/'results'/f'alc_r0_official_repeat_{mode}_20261011'
    paths = {s:Path(str(stem)+s) for s in ('.stdout.log','.stderr.log','.xml','.exit.json')}
    if any(p.exists() for p in paths.values()):
        raise FileExistsError('retained evidence exists')
    selection = ['tests/test_alc_r0_official_repeat_assessment.py']
    if mode == 'red':
        selection += ['-k','equal_complete_official_digests']
    elif mode == 'regression':
        selection += ['tests/test_alc_r0_fixed_d_wire.py','tests/test_alc_r0_fixed_d_projection.py',
                      'tests/test_alc_r0_fixed_d_worker.py','tests/test_alc_r0_authority_watch_policy.py']
    environment = os.environ.copy()
    environment.update(PYTHONPATH=str(cwd/'src'),PYTHONNOUSERSITE='1',
                       PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
                       CUDA_VISIBLE_DEVICES='-1')
    receipt = run_owned_process((sys.executable,'-m','pytest','-q',*selection,
        '--junitxml='+str(paths['.xml'])),cwd=cwd,environment=environment,
        stdout_path=paths['.stdout.log'],stderr_path=paths['.stderr.log'],
        deadline_ns=entry+300_000_000_000)
    data = json.dumps(dict(asdict(receipt),pytest_exit_code=receipt.exit_code,
        scope='synthetic-official-repeat-assessment'),sort_keys=True,separators=(',',':')).encode()
    with paths['.exit.json'].open('xb') as out:
        out.write(data)
    print(data.decode())


if __name__ == '__main__':
    main()
