"""Closed native-directory candidate diagnostics; no actual runtime scan."""
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path
from aluclu.alc_r0.checkpoint_owned_process import run_owned_process


def main():
    entry=time.monotonic_ns()
    if sys.argv[1:] not in (['red'],['green'],['regression'],['red_integration'],['red_integration_v2'],['green_integration'],['regression_integration'],['cause_integration'],['green_integration_v2'],['regression_integration_v2'],['source_partition_v3'],['process_partition_v3']):
        raise ValueError('closed candidate diagnostic mode required')
    mode=sys.argv[1]; cwd=Path(__file__).resolve().parents[1]
    stem=cwd/'results'/f'alc_r0_windows_directory_{mode}_20261011'
    paths={s:Path(str(stem)+s) for s in ('.stdout.log','.stderr.log','.xml','.exit.json')}
    if any(p.exists() for p in paths.values()): raise FileExistsError('retained evidence exists')
    selection=['tests/test_alc_r0_windows_directory_metadata.py']
    if mode in ('red_integration','red_integration_v2'):
        selection=['tests/test_alc_r0_runtime_tree_inventory.py','-k','native_directory']
    elif mode in ('green_integration','green_integration_v2'):
        selection+=['tests/test_alc_r0_runtime_tree_inventory.py']
        if mode=='green_integration_v2':
            selection+=['tests/test_alc_r0_python_runtime_binding.py','-k','not actual_current_runtime']
    elif mode=='cause_integration':
        selection=['tests/test_alc_r0_python_runtime_binding.py','-k','exact_current_runtime_binding']
    elif mode=='source_partition_v3':
        selection=['tests/test_alc_r0_owned_source_inspection.py','tests/test_alc_r0_canonical.py']
    elif mode=='process_partition_v3':
        selection=['tests/test_alc_r0_reserved_owned_process.py',
            'tests/test_alc_r0_bounded_process_output.py','tests/test_alc_r0_owned_stop.py',
            'tests/test_alc_r0_live_authority_watch.py']
    if mode in ('regression','regression_integration','regression_integration_v2'):
        selection+=['tests/test_alc_r0_python_runtime_binding.py',
            'tests/test_alc_r0_runtime_tree_inventory.py',
            'tests/test_alc_r0_owned_source_inspection.py','tests/test_alc_r0_canonical.py',
            'tests/test_alc_r0_reserved_owned_process.py','tests/test_alc_r0_bounded_process_output.py',
            'tests/test_alc_r0_owned_stop.py','tests/test_alc_r0_live_authority_watch.py',
            '-k','not actual_current_runtime']
    environment=dict(os.environ,PYTHONPATH=str(cwd/'src'),PYTHONNOUSERSITE='1',
        PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',CUDA_VISIBLE_DEVICES='-1',
        ALUCLU_TEST_ONLY_RUNTIME_SCAN='0')
    environment['ALUCLU_TEST_ONLY_RUNTIME_CAUSE']='1' if mode=='cause_integration' else '0'
    verbosity='-vv' if mode in ('source_partition_v3','process_partition_v3') else '-q'
    receipt=run_owned_process((sys.executable,'-m','pytest',verbosity,*selection,
        '--junitxml='+str(paths['.xml'])),cwd=cwd,environment=environment,
        stdout_path=paths['.stdout.log'],stderr_path=paths['.stderr.log'],
        deadline_ns=entry+300_000_000_000)
    data=json.dumps(dict(asdict(receipt),pytest_exit_code=receipt.exit_code,
        scope='standalone-native-directory-candidate'),sort_keys=True,separators=(',',':')).encode()
    with paths['.exit.json'].open('xb') as out: out.write(data)
    print(data.decode())


if __name__=='__main__': main()
