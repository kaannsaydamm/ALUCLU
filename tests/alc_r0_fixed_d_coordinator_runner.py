"""Preserve integrated entrypoint RED under native process ownership."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import sys
import time

from aluclu.alc_r0.checkpoint_owned_process import run_owned_process


def main():
    entry=time.monotonic_ns()
    if len(sys.argv)!=2 or sys.argv[1] not in ('red','red_v2','red_v3','green','green_v2','green_v3','green_v4','green_v5','green_v6','regression','native_red','native_green','native_green_v2','native_green_v3','native_green_v4','native_green_v5','regression_v2','bootstrap_red','bootstrap_green','regression_v3','busy_red','regression_busy_red','actuator_green','actuator_green_v2','actuator_green_v3','actuator_green_v4','regression_actuator','tree_red','tree_green','tree_green_v2','tree_green_v3','tree_green_v4','regression_tree','early_red','early_green','early_green_v2','regression_early','partial_acquire','partial_acquire_v2','abrupt_diagnose','regression_partial_acquire','regression_partial_diagnose','query_fault','regression_query_fault','query_fault_v2','regression_query_fault_v2','integrated_denial_red','integrated_denial_native_red','integrated_denial_green','integrated_denial_green_v2','integrated_retry_red','integrated_denial_green_v3','integrated_denial_green_v4','regression_integrated_denial','regression_integrated_denial_v2','primary_red','primary_green','regression_primary','primary_green_v2','regression_primary_v2','primary_dependents','growth_acceptance_red','growth_acceptance_red_v2','completion_red','completion_green','regression_completion','storage_hold_red','storage_hold_green','storage_growth_green','storage_growth_regression','storage_growth_red','storage_growth_green_v2','storage_growth_regression_a','storage_growth_regression_b','output_capacity_red','output_capacity_red_v2','output_capacity_green','output_capacity_negative_red','output_capacity_negative_green','output_capacity_negative_green_v2','output_capacity_reparse_red','output_capacity_final_focus','output_capacity_regression_a','output_capacity_regression_b','output_capacity_regression_c','running_output_red','running_output_green','running_output_regression_a','running_output_regression_b','running_output_regression_c'): raise ValueError('closed checkpoint only')
    cwd=Path(__file__).resolve().parents[1]
    stamp='20261015' if sys.argv[1] in ('busy_red','regression_busy_red','actuator_green','actuator_green_v2','actuator_green_v3','actuator_green_v4','regression_actuator','tree_red','tree_green','tree_green_v2','tree_green_v3','tree_green_v4','regression_tree','early_red','early_green','early_green_v2','regression_early','partial_acquire','partial_acquire_v2','abrupt_diagnose','regression_partial_acquire','regression_partial_diagnose') else '20261013'
    if sys.argv[1] in ('query_fault','regression_query_fault','query_fault_v2','regression_query_fault_v2','integrated_denial_red','integrated_denial_native_red','integrated_denial_green','integrated_denial_green_v2','integrated_retry_red','integrated_denial_green_v3','integrated_denial_green_v4','regression_integrated_denial','regression_integrated_denial_v2','primary_red','primary_green','regression_primary','primary_green_v2','regression_primary_v2','primary_dependents','growth_acceptance_red','growth_acceptance_red_v2','completion_red','completion_green','regression_completion'): stamp='20261016'
    if sys.argv[1].startswith('storage_'): stamp='20261016'
    if sys.argv[1].startswith('output_capacity_'): stamp='20261016'
    stem=cwd/'results'/f'alc_r0_fixed_d_coordinator_{sys.argv[1]}_{stamp}'
    if sys.argv[1].startswith('running_output_'):
        stem=cwd/'results'/f'alc_r0_fixed_d_coordinator_{sys.argv[1]}_20261016'
    paths={suffix:Path(str(stem)+suffix) for suffix in ('.stdout.log','.stderr.log','.xml','.exit.json')}
    if any(path.exists() for path in paths.values()): raise FileExistsError('immutable evidence exists')
    environment=os.environ.copy()
    environment.update(PYTHONPATH=str(cwd/'src'),PYTHONDONTWRITEBYTECODE='1',
        PYTHONNOUSERSITE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',CUDA_VISIBLE_DEVICES='-1')
    cases=['tests/test_alc_r0_fixed_d_coordinator.py']
    if sys.argv[1] in ('query_fault','query_fault_v2'): cases+=['-k','real_access_denial']
    if sys.argv[1] in ('integrated_denial_red','integrated_denial_native_red','integrated_denial_green','integrated_denial_green_v2','integrated_retry_red','integrated_denial_green_v3','integrated_denial_green_v4'):
        cases+=['-k','actual_coordinator_native_denial']
    if sys.argv[1]=='integrated_retry_red': cases=['tests/test_alc_r0_fixed_d_coordinator.py','-k','closed_fixed_lease']
    if sys.argv[1] in ('integrated_denial_green_v3','integrated_denial_green_v4'): cases=['tests/test_alc_r0_fixed_d_coordinator.py','-k','actual_coordinator_native_denial or closed_fixed_lease']
    if sys.argv[1] in ('primary_red','primary_green','primary_green_v2'):
        cases=['tests/test_alc_r0_reserved_owned_process.py','-k','primary_failure_survives']
    if sys.argv[1]=='primary_dependents':
        cases=['tests/test_alc_r0_owned_stop.py','tests/test_alc_r0_ready_child_publication.py',
            'tests/test_alc_r0_committed_watch.py']
    if sys.argv[1] in ('growth_acceptance_red','growth_acceptance_red_v2'): cases=['tests/test_alc_r0_coordinator_growth_acceptance.py']
    if sys.argv[1] in ('completion_red','completion_green'):
        cases=['tests/test_alc_r0_fixed_d_coordinator.py','-k','completion_conflict_after_release']
    if sys.argv[1]=='native_red': cases+=['-k','slow-parent']
    if sys.argv[1]=='bootstrap_red': cases+=['-k','bootstrap']
    if sys.argv[1]=='busy_red': cases+=['-k','busy_revocation']
    if sys.argv[1]=='tree_red': cases+=['-k','busy-tree-revocation']
    if sys.argv[1]=='early_red': cases+=['-k','early_tree_validation']
    if sys.argv[1] in ('partial_acquire','partial_acquire_v2'): cases+=['-k','real_partial_duplicate_failure']
    if sys.argv[1]=='abrupt_diagnose':
        cases=['tests/test_alc_r0_reserved_owned_process.py::test_abrupt_lease_parent_exit_leaves_no_owned_orphan[running]',
            '-vv','--tb=short','-x','-p','no:cacheprovider']
    if sys.argv[1] in ('regression','regression_v2','regression_v3','regression_busy_red','regression_actuator','regression_tree','regression_early','partial_acquire','regression_partial_acquire','regression_partial_diagnose','query_fault','regression_query_fault','regression_query_fault_v2','regression_integrated_denial','regression_integrated_denial_v2','regression_primary','regression_primary_v2','regression_completion'):
        cases+=['tests/test_alc_r0_reservation_state.py','tests/test_alc_r0_reservation_store.py',
            'tests/test_alc_r0_reserved_owned_process.py','tests/test_alc_r0_live_authority_watch.py',
            'tests/test_alc_r0_status_watch_consumer.py']
    if sys.argv[1] in ('query_fault','regression_query_fault','query_fault_v2','regression_query_fault_v2','integrated_denial_red','integrated_denial_native_red','integrated_denial_green','integrated_denial_green_v2','integrated_retry_red','integrated_denial_green_v3','integrated_denial_green_v4','regression_integrated_denial','regression_integrated_denial_v2','primary_red','primary_green','regression_primary','primary_green_v2','regression_primary_v2','primary_dependents','growth_acceptance_red','growth_acceptance_red_v2','completion_red','completion_green','regression_completion'):
        cases+=['-o','addopts=','-vv','--tb=short','-x','-p','no:cacheprovider']
    if sys.argv[1]=='regression_partial_diagnose':
        cases+=['-vv','--tb=short','-x','-p','no:cacheprovider']
    if sys.argv[1] in ('storage_hold_red','storage_hold_green'):
        cases=['tests/test_alc_r0_reservation_state.py','-k','storage_held']
    if sys.argv[1] in ('storage_growth_red','storage_growth_green','storage_growth_green_v2'):
        cases=['tests/test_alc_r0_coordinator_growth_acceptance.py',
            'tests/test_alc_r0_fixed_d_coordinator.py','-k','growth or completes_owned or completion_conflict']
    if sys.argv[1]=='storage_growth_regression':
        cases=['tests/test_alc_r0_coordinator_growth_acceptance.py','tests/test_alc_r0_fixed_d_coordinator.py',
            'tests/test_alc_r0_reservation_state.py','tests/test_alc_r0_reservation_store.py',
            'tests/test_alc_r0_reserved_owned_process.py','tests/test_alc_r0_live_authority_watch.py',
            'tests/test_alc_r0_status_watch_consumer.py']
    if sys.argv[1].startswith('storage_'):
        if sys.argv[1]=='storage_growth_regression_a':
            cases=['tests/test_alc_r0_coordinator_growth_acceptance.py','tests/test_alc_r0_fixed_d_coordinator.py',
                'tests/test_alc_r0_reservation_state.py','tests/test_alc_r0_reservation_store.py']
        if sys.argv[1]=='storage_growth_regression_b':
            cases=['tests/test_alc_r0_reserved_owned_process.py','tests/test_alc_r0_live_authority_watch.py',
                'tests/test_alc_r0_status_watch_consumer.py']
        cases+=['-o','addopts=','-vv','--tb=short','-p','no:cacheprovider']
    if sys.argv[1].startswith('output_capacity_'):
        cases=['tests/test_alc_r0_coordinator_growth_acceptance.py','-k',
            'output_capacity or preallocated_output','-o','addopts=','-vv','--tb=short','-p','no:cacheprovider']
        if sys.argv[1]=='output_capacity_reparse_red':
            cases=['tests/test_alc_r0_coordinator_growth_acceptance.py','-k','reparse_ancestor',
                '-o','addopts=','-vv','--tb=short','-p','no:cacheprovider']
        if sys.argv[1]=='output_capacity_regression_a':
            cases=['tests/test_alc_r0_coordinator_growth_acceptance.py','tests/test_alc_r0_fixed_d_coordinator.py',
                'tests/test_alc_r0_reservation_state.py','tests/test_alc_r0_reservation_store.py']
        if sys.argv[1]=='output_capacity_regression_b':
            cases=['tests/test_alc_r0_reserved_owned_process.py','tests/test_alc_r0_live_authority_watch.py',
                'tests/test_alc_r0_status_watch_consumer.py']
        if sys.argv[1]=='output_capacity_regression_c':
            cases=['tests/test_alc_r0_bounded_process_output.py']
        if sys.argv[1] in ('output_capacity_regression_a','output_capacity_regression_b','output_capacity_regression_c'):
            cases+=['-o','addopts=','-vv','--tb=short','-p','no:cacheprovider']
    if sys.argv[1].startswith('running_output_'):
        cases=['tests/test_alc_r0_coordinator_growth_acceptance.py','-k','actual_running_output_overflow',
            '-o','addopts=','-vv','--tb=short','-p','no:cacheprovider']
        if sys.argv[1]=='running_output_regression_a':
            cases=['tests/test_alc_r0_coordinator_growth_acceptance.py','tests/test_alc_r0_fixed_d_coordinator.py',
                'tests/test_alc_r0_reservation_state.py','tests/test_alc_r0_reservation_store.py']
        if sys.argv[1]=='running_output_regression_b':
            cases=['tests/test_alc_r0_reserved_owned_process.py','tests/test_alc_r0_live_authority_watch.py',
                'tests/test_alc_r0_status_watch_consumer.py']
        if sys.argv[1]=='running_output_regression_c':
            cases=['tests/test_alc_r0_bounded_process_output.py']
        if sys.argv[1].startswith('running_output_regression_'):
            cases+=['-o','addopts=','-vv','--tb=short','-p','no:cacheprovider']
    result=run_owned_process((sys.executable,'-B','-m','pytest','-q',*cases,'--junitxml='+str(paths['.xml'])),
        cwd=cwd,environment=environment,stdout_path=paths['.stdout.log'],
        stderr_path=paths['.stderr.log'],deadline_ns=entry+120_000_000_000)
    data=json.dumps(dict(asdict(result),pytest_exit_code=result.exit_code,
        parent_bound_seconds=120,scope='integrated-coordinator-acceptance-work-in-progress'),
        sort_keys=True,separators=(',',':')).encode()
    with paths['.exit.json'].open('xb') as stream: stream.write(data)
    print(data.decode())


if __name__=='__main__': main()
