"""Diagnostic profiling boundaries; never scientific or admission evidence."""
import json
import os
from pathlib import Path
import sys
import time

import pytest

import alc_r0_fixed_d_coordinator_runner as runner
from aluclu.alc_r0.checkpoint_owned_process import run_owned_process


def test_latency_profile_command_is_fixed_cpu_diagnostic(tmp_path):
    command=runner._latency_profile_command(tmp_path)
    assert command==(sys.executable,'-B','-c',runner._LATENCY_PROFILE_CODE,
        'diagnostic','success',str(tmp_path))
    assert 'dump_stats' not in command[3] and 'pickle' not in command[3]
    assert 'print_stats(60)' in command[3]


@pytest.mark.parametrize('namespace',[Path('relative'),'not-a-path'])
def test_latency_profile_command_rejects_invalid_namespace(namespace):
    with pytest.raises(ValueError): runner._latency_profile_command(namespace)


@pytest.mark.skipif(os.name!='nt',reason='actual Windows native process ownership')
def test_latency_profile_actual_denial_preserves_nonzero_exit(tmp_path):
    missing=tmp_path/'missing'
    environment=os.environ.copy()
    environment.update(PYTHONPATH=str(Path(__file__).resolve().parents[1]/'src'),
        PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',CUDA_VISIBLE_DEVICES='-1',
        HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1')
    result=run_owned_process(runner._latency_profile_command(missing),cwd=tmp_path,
        environment=environment,stdout_path=tmp_path/'profile.stdout',
        stderr_path=tmp_path/'profile.stderr',deadline_ns=time.monotonic_ns()+30_000_000_000)
    assert result.exit_code==2 and result.active_processes==0 and not result.timed_out
    assert not missing.exists()
    with (tmp_path/'profile.stdout').open('rb') as stream: data=stream.read(65537)
    assert len(data)<=65536
    rows=[json.loads(row) for row in data.decode().splitlines() if row.startswith('{')]
    assert len(rows)==1
    report=rows[0]
    assert report['diagnostic_exit_code']==2 and report['profile_overhead'] is True
    assert report['scope']=='coordinator-main-thread-diagnostic-profile'
    assert report['scientific_modules_loaded_in_parent'] is False
    assert report['main_wall_ns']>=0 and report['pre_main_wall_ns']>=0
    assert report['profile_wall_ns']>=report['main_wall_ns']
    assert report['profile_cpu_ns']>=0
    assert b'coordinator denied' in (tmp_path/'profile.stderr').read_bytes()
