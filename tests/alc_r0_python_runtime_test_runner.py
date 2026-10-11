"""Closed owned Python runtime-binding diagnostics; no scientific execution."""
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path
from aluclu.alc_r0.checkpoint_owned_process import run_owned_process


def main():
    entry=time.monotonic_ns()
    if len(sys.argv)!=2 or sys.argv[1] not in ('red','green','regression','actual','red_v2','green_v2','regression_v2','green_v3','regression_v3','red_v3','green_v4','regression_v4','actual_v2','green_v5','regression_v5','red_diff','green_diff','regression_diff','actual_v3','green_diff_v2','regression_diff_v2','actual_v4'):
        raise ValueError('closed diagnostic mode required')
    mode=sys.argv[1]; cwd=Path(__file__).resolve().parents[1]
    stem=cwd/'results'/f'alc_r0_python_runtime_{mode}_20261011'
    paths={s:Path(str(stem)+s) for s in ('.stdout.log','.stderr.log','.xml','.exit.json')}
    if any(p.exists() for p in paths.values()): raise FileExistsError('retained evidence exists')
    if mode in ('actual','actual_v2','actual_v3','actual_v4') and (cwd/'results'/f'alc_r0_python_runtime_{mode}_20261011.binding.json').exists():
        raise FileExistsError('retained actual binding exists')
    selection=['tests/test_alc_r0_python_runtime_binding.py']
    if mode=='red': selection+=['-k','exact_current_runtime']
    elif mode=='red_v2': selection+=['-k','executable_metadata_sources']
    elif mode=='red_v3': selection+=['-k','current_base_single_junction']
    elif mode=='red_diff': selection=['tests/test_alc_r0_runtime_tree_inventory.py','-k','change_diagnostic']
    elif mode in ('actual','actual_v2','actual_v3','actual_v4'): selection+=['-k','actual_current_runtime']
    else: selection+=['-k','not actual_current_runtime']
    if mode in ('green_diff','green_diff_v2'): selection+=['tests/test_alc_r0_runtime_tree_inventory.py']
    if mode in ('regression','regression_v2','regression_v3','regression_v4','regression_v5','regression_diff','regression_diff_v2'):
        selection+=['tests/test_alc_r0_runtime_tree_inventory.py',
            'tests/test_alc_r0_owned_source_inspection.py','tests/test_alc_r0_canonical.py',
            'tests/test_alc_r0_reserved_owned_process.py','tests/test_alc_r0_bounded_process_output.py',
            'tests/test_alc_r0_owned_stop.py','tests/test_alc_r0_live_authority_watch.py']
    environment=dict(os.environ,PYTHONPATH=str(cwd/'src'),PYTHONNOUSERSITE='1',
        PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',CUDA_VISIBLE_DEVICES='-1')
    environment['ALUCLU_TEST_ONLY_RUNTIME_SCAN']='1' if mode in ('actual','actual_v2','actual_v3','actual_v4') else '0'
    environment['ALUCLU_TEST_ONLY_RUNTIME_SCAN_MODE']=mode
    receipt=run_owned_process((sys.executable,'-m','pytest','-q',*selection,
        '--junitxml='+str(paths['.xml'])),cwd=cwd,environment=environment,
        stdout_path=paths['.stdout.log'],stderr_path=paths['.stderr.log'],
        deadline_ns=entry+(960_000_000_000 if mode=='actual_v4' else 300_000_000_000))
    data=json.dumps(dict(asdict(receipt),pytest_exit_code=receipt.exit_code,
        scope='owned-current-python-runtime-diagnostic'),sort_keys=True,separators=(',',':')).encode()
    with paths['.exit.json'].open('xb') as out: out.write(data)
    print(data.decode())


if __name__=='__main__': main()
