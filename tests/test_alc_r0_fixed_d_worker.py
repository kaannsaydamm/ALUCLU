"""Denied bootstrap and settings-only tests: no host/assets or real GPU."""

import importlib
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_alc_r0_fixed_d_wire import CONTROLS


def worker():
    return importlib.import_module("aluclu.alc_r0.fixed_d_worker")


DENIAL = "alc-r0 fixed D denied: reviewed operator handoff unavailable\n"


@pytest.mark.parametrize("control", CONTROLS)
def test_worker_bootstrap_denies(control, capsys):
    before = dict(os.environ)
    assert worker().main() == 2
    assert dict(os.environ) == before
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == DENIAL


def test_private_preparation_denies_before_request_hooks():
    class Trap:
        def __getattribute__(self, name):
            raise AssertionError("request accessed before handoff denial")

    module = worker()
    before = dict(os.environ)
    with pytest.raises(module.WorkerHandoffUnavailable):
        module._prepare_runtime(Trap())
    assert dict(os.environ) == before


def fresh(script, *, expected_exit=0, expected_out="settings-ok\n", expected_err=""):
    environment = os.environ.copy()
    environment.update(PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"),
                       PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1",
                       CUDA_VISIBLE_DEVICES="-1", ALUCLU_APPROVED="true",
                       ALUCLU_OPERATOR_HANDOFF="approved", ALUCLU_CONTROL=CONTROLS[1])
    completed = subprocess.run((sys.executable, "-c", script), env=environment,
                               capture_output=True, text=True, timeout=90, check=False)
    assert completed.returncode == expected_exit, completed.stdout + completed.stderr
    assert completed.stdout == expected_out
    assert completed.stderr == expected_err


DENY_IMPORTS = '''
import importlib.abc, sys
class Deny(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'torch', 'transformers', 'numpy'} or fullname.startswith(
            'aluclu.alc_r0.checkpoint_parity_qualification'):
            raise AssertionError('heavy/scientific import before denial')
sys.meta_path.insert(0, Deny())
'''


def test_light_import_and_private_preparation_no_environment_mutation():
    fresh(DENY_IMPORTS + '''
import os
from aluclu.alc_r0.fixed_d_worker import _prepare_runtime, WorkerHandoffUnavailable
before = dict(os.environ)
try: _prepare_runtime(object())
except WorkerHandoffUnavailable: pass
else: raise AssertionError('operator handoff invented')
assert dict(os.environ) == before
assert not {'torch', 'transformers', 'numpy'}.intersection(sys.modules)
print('settings-ok')
''')


def test_module_entry_denies_without_heavy_import():
    fresh(DENY_IMPORTS + '''
import runpy
runpy.run_module('aluclu.alc_r0.fixed_d_worker', run_name='__main__')
''', expected_exit=2, expected_out="", expected_err=DENIAL)


@pytest.mark.parametrize("arguments", ([], ["C:/does-not-exist/request.json"],
                                     ["--approved", "true", "--backend", "fake"]))
def test_direct_script_denies_all_approval_shaped_inputs(arguments):
    script_path = Path(__file__).resolve().parents[1] / "scripts/run_alc_r0_fixed_d_worker.py"
    fresh(DENY_IMPORTS + f'''
import runpy
sys.argv = {[str(script_path), *arguments]!r}
runpy.run_path({str(script_path)!r}, run_name='__main__')
''', expected_exit=2, expected_out="", expected_err=DENIAL)


class RecordingBackend:
    """Explicit settings helper fixture; never installed as a runtime module."""

    def __init__(self, *, inference=False, initialized=False, available=True, bf16=True,
                 fail_on=None):
        self.events = []
        self.inference = inference
        self.initialized = initialized
        self.available = available
        self.bf16 = bf16
        self.fail_on = fail_on
        self.cuda = SimpleNamespace(
            is_initialized=lambda: self.record("cuda.is_initialized", result=self.initialized),
            is_available=lambda: self.record("cuda.is_available", result=self.available),
            set_device=lambda value: self.record("cuda.set_device", value),
            is_bf16_supported=lambda: self.record("cuda.is_bf16_supported", result=self.bf16))
        self.backends = SimpleNamespace(
            cudnn=SimpleNamespace(allow_tf32=True, benchmark=True, deterministic=False),
            cuda=SimpleNamespace(matmul=SimpleNamespace(allow_tf32=True),
                                 enable_math_sdp=lambda v: self.record("math_sdp", v),
                                 enable_flash_sdp=lambda v: self.record("flash_sdp", v),
                                 enable_mem_efficient_sdp=lambda v: self.record("mem_sdp", v),
                                 enable_cudnn_sdp=lambda v: self.record("cudnn_sdp", v)))

    def record(self, name, *values, result=None):
        self.events.append((name, *values))
        if self.fail_on == name:
            raise RuntimeError("injected setting failure")
        return result

    def is_inference_mode_enabled(self):
        return self.record("inference", result=self.inference)

    def set_default_device(self, value):
        self.record("default_device", value)

    def set_grad_enabled(self, value):
        self.record("grad", value)

    def use_deterministic_algorithms(self, value, *, warn_only):
        self.record("deterministic", value, warn_only)


def test_cpu_settings_without_cuda_discovery():
    backend = RecordingBackend()
    worker()._apply_runtime_settings(backend, "cpu")
    assert backend.events == [("inference",), ("cuda.is_initialized",),
                              ("default_device", "cpu"), ("grad", True),
                              ("deterministic", True, False)]
    assert backend.backends.cudnn.allow_tf32  # CPU route does not touch GPU flags.


def test_gpu_fixed_reference_settings_order_and_values():
    backend = RecordingBackend()
    worker()._apply_runtime_settings(backend, "cuda:0")
    assert backend.events == [("inference",), ("cuda.is_available",),
                              ("cuda.set_device", 0), ("cuda.is_bf16_supported",),
                              ("default_device", "cpu"), ("grad", True),
                              ("deterministic", True, False), ("math_sdp", True),
                              ("flash_sdp", False), ("mem_sdp", False), ("cudnn_sdp", False)]
    assert backend.backends.cuda.matmul.allow_tf32 is False
    assert backend.backends.cudnn.allow_tf32 is False
    assert backend.backends.cudnn.benchmark is False
    assert backend.backends.cudnn.deterministic is True


@pytest.mark.parametrize("device", ("cuda", "cuda:1", "mps", True, None))
def test_unsupported_device_denies_before_backend_calls(device):
    backend = RecordingBackend()
    with pytest.raises(worker().WorkerSettingsError):
        worker()._apply_runtime_settings(backend, device)
    assert backend.events == []


@pytest.mark.parametrize("device,options,last", (
    ("cpu", dict(inference=True), "inference"),
    ("cuda:0", dict(inference=True), "inference"),
    ("cpu", dict(initialized=True), "cuda.is_initialized"),
    ("cuda:0", dict(available=False), "cuda.is_available"),
    ("cuda:0", dict(bf16=False), "cuda.is_bf16_supported"),
))
def test_invalid_runtime_terminal_without_settings_or_fallback(device, options, last):
    backend = RecordingBackend(**options)
    with pytest.raises(worker().WorkerSettingsError):
        worker()._apply_runtime_settings(backend, device)
    assert backend.events[-1] == (last,)
    assert not any(row[0] == "default_device" for row in backend.events)


@pytest.mark.parametrize("operation", ("cuda.set_device", "default_device", "grad",
                                      "deterministic", "math_sdp", "flash_sdp",
                                      "mem_sdp", "cudnn_sdp"))
def test_setting_failure_propagates_without_retry(operation):
    backend = RecordingBackend(fail_on=operation)
    with pytest.raises(RuntimeError, match="injected setting failure"):
        worker()._apply_runtime_settings(backend, "cuda:0")
    assert backend.events[-1][0] == operation
    assert sum(row[0] == operation for row in backend.events) == 1


def test_fresh_real_cpu_matches_original_context_without_host_or_cuda():
    fresh('''
import os, sys
os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_DATASETS_OFFLINE='1')
import torch
assert not torch.cuda.is_initialized()
from aluclu.alc_r0.fixed_d_worker import _apply_runtime_settings
_apply_runtime_settings(torch, 'cpu')
from aluclu.alc_r0.checkpoint_parity_qualification import _context
_context('cpu')
assert not torch.cuda.is_initialized()
assert torch.get_default_device() == torch.device('cpu')
assert torch.is_grad_enabled()
assert torch.are_deterministic_algorithms_enabled()
assert not torch.is_deterministic_algorithms_warn_only_enabled()
print('settings-ok')
''')
