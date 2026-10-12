"""Closed harmless crash-after-claim diagnostic, never an experiment worker."""
import os
import sys
import time
from pathlib import Path
from aluclu.alc_r0.control_consumption import _claim,consume_control,ControlConsumptionError

if len(sys.argv)!=3 or sys.argv[1] not in ('crash','consume'):
    raise ValueError('closed diagnostic mode and temporary directory required')
directory=Path(sys.argv[2])
if not directory.is_absolute() or not directory.is_dir(): raise ValueError('temporary directory missing')
if sys.argv[1]=='crash':
    _claim(directory/'d-cpu-fresh1.consumed.json',time.monotonic_ns()+10**9)
    os._exit(17)
from test_alc_r0_generation_binding import fixture
generation,request,_,_=fixture()
try:
    consume_control(directory,generation,request,installation_root='c'*64,
                    deadline_ns=time.monotonic_ns()+2*10**9)
except ControlConsumptionError:
    sys.exit(18)
