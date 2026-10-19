"""Closed owned dormant-body tests, no scientific execution."""
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

from aluclu.alc_r0.checkpoint_owned_process import run_owned_process


def main():
    entry = time.monotonic_ns()
    if len(sys.argv) != 2 or sys.argv[1] not in (
            'red', 'red_v2', 'green', 'regression', 'repair_red', 'green_v2', 'regression_v2'):
        raise ValueError('closed dormant-body mode required')
    mode = sys.argv[1]
    cwd = Path(__file__).resolve().parents[1]
    stem = cwd / 'results' / f'alc_r0_fixed_d_body_{mode}_20261012'
    paths = {suffix: Path(str(stem) + suffix)
             for suffix in ('.stdout.log', '.stderr.log', '.xml', '.exit.json')}
    if any(path.exists() for path in paths.values()):
        raise FileExistsError('evidence already exists')
    arguments = ['tests/test_alc_r0_fixed_d_body.py']
    if mode == 'repair_red':
        arguments += ['-k', 'missing_typed or terminal_failure or static_fixed_call']
    elif mode in ('regression', 'regression_v2'):
        arguments += ['tests/test_alc_r0_fixed_d_worker.py',
                      'tests/test_alc_r0_fixed_d_request_file.py',
                      'tests/test_alc_r0_fixed_d_wire.py',
                      'tests/test_alc_r0_fixed_d_projection.py',
                      'tests/test_alc_r0_import_isolation.py']
    environment = os.environ.copy()
    environment.update(PYTHONPATH=str(cwd / 'src'), PYTHONNOUSERSITE='1',
                       PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
                       CUDA_VISIBLE_DEVICES='-1')
    receipt = run_owned_process(
        (sys.executable, '-m', 'pytest', '-q', *arguments,
         '--junitxml=' + str(paths['.xml'])), cwd=cwd, environment=environment,
        stdout_path=paths['.stdout.log'], stderr_path=paths['.stderr.log'],
        deadline_ns=entry + 120_000_000_000)
    record = dict(asdict(receipt), pytest_exit_code=receipt.exit_code,
                  parent_bound_seconds=120, scope='dormant-body-tests')
    data = json.dumps(record, sort_keys=True, separators=(',', ':')).encode()
    with paths['.exit.json'].open('xb') as output:
        output.write(data)
    print(data.decode())


if __name__ == '__main__':
    main()
