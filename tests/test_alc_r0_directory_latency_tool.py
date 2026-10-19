"""Closed filesystem observation is diagnostic, not scientific acceptance."""
import json
import os
from pathlib import Path
import sys
import time

import pytest

import alc_r0_fixed_d_coordinator_runner as runner
from aluclu.alc_r0.checkpoint_owned_process import run_owned_process


def test_directory_latency_command_is_closed():
    command=runner._directory_latency_command()
    assert command==(sys.executable,'-B','-c',runner._DIRECTORY_LATENCY_CODE)
    assert 'cProfile' not in command[3]


@pytest.mark.skipif(os.name!='nt',reason='Windows native owned process')
def test_actual_directory_latency_has_exact_finite_records(tmp_path):
    environment=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',
        PYTHONNOUSERSITE='1',CUDA_VISIBLE_DEVICES='-1')
    result=run_owned_process(runner._directory_latency_command(),cwd=tmp_path,
        environment=environment,stdout_path=tmp_path/'probe.stdout',
        stderr_path=tmp_path/'probe.stderr',deadline_ns=time.monotonic_ns()+60_000_000_000)
    assert result.exit_code==0 and not result.timed_out and result.active_processes==0
    with (tmp_path/'probe.stdout').open('rb') as stream: raw=stream.read(65537)
    assert len(raw)<=65536
    records=[json.loads(line) for line in raw.decode().splitlines()]
    assert len(records)==41
    assert records[0]['event']=='setup-begun'
    assert records[1]['event']=='setup-completed'
    namespace=Path(records[1]['namespace'])
    assert namespace.is_absolute() and namespace.is_dir()
    assert records[2]['event']=='metadata'
    pairs=records[3:-2]
    assert len(pairs)==36
    kinds=['fresh-mkdir']*6+['existing-mkdir']*6+['exclusive-write-flush-fsync']*6
    for index,kind in enumerate(kinds):
        begun,completed=pairs[index*2:index*2+2]
        assert begun['event']=='begun' and completed['event']=='completed'
        assert begun['operation']==completed['operation']==kind
        assert begun['index']==completed['index']==index%6
        assert completed['wall_ns']>=0 and completed['cpu_ns']>=0
    assert records[-2]['event']=='inventory'
    assert records[-2]['directories']==6 and records[-2]['files']==6
    assert records[-2]['payload_bytes']==6*512
    assert records[-1]['event']=='summary' and records[-1]['completed_operations']==18
    assert records[-1]['profile_overhead'] is False
    assert not (tmp_path/'probe.stderr').read_bytes()
