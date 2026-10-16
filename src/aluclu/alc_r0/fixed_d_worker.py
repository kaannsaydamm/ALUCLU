"""Fixed D denied bootstrap and private process-local reference settings.

NOT an accepting worker. Operator handoff/admission is not installed; no model,
tokenizer, qualification, provenance, resource or scientific claim is enabled.
The private settings seam is not an authorization API or host callback.
"""

import os
import sys
import time
import types
from pathlib import Path

from .canonical import parse_canonical_json
from .fixed_d_wire import DRequest, DWireError, decode_d_request


class WorkerHandoffUnavailable(RuntimeError):
    """The concrete reviewed operator handoff has not been installed."""


class WorkerSettingsError(ValueError):
    """Fixed process-local context cannot be established; no fallback."""


def _require_operator_handoff():
    # No self-asserted request, JSON, env flag or synthetic permit can open this.
    # Replacing this denial requires a concrete independently reviewed integration.
    raise WorkerHandoffUnavailable("reviewed operator handoff unavailable")


def _apply_runtime_settings(backend, device):
    """Private settings-only unit seam; production resolves fixed Torch internally.

    Does not load a host or grant execution. Caller must use an isolated process;
    changes are deliberate and terminal failure does not restore or retry them.
    Recording GPU backends in tests establish setter behavior, not CUDA fidelity.
    """
    if type(device) is not str or device not in ("cpu", "cuda:0"):
        raise WorkerSettingsError("closed CPU or CUDA0 device required")
    if backend.is_inference_mode_enabled():
        raise WorkerSettingsError("enclosing inference mode is not a grad context")
    if device == "cpu":
        if backend.cuda.is_initialized():
            raise WorkerSettingsError("CPU process must not have initialized CUDA")
    else:
        if not backend.cuda.is_available():
            raise WorkerSettingsError("CUDA0 required; no CPU fallback")
        backend.cuda.set_device(0)
        if not backend.cuda.is_bf16_supported():
            raise WorkerSettingsError("CUDA0 BF16 required; no dtype fallback")
    backend.set_default_device("cpu")
    backend.set_grad_enabled(True)
    backend.use_deterministic_algorithms(True, warn_only=False)
    if device == "cuda:0":
        backend.backends.cuda.matmul.allow_tf32 = False
        backend.backends.cudnn.allow_tf32 = False
        backend.backends.cudnn.benchmark = False
        backend.backends.cudnn.deterministic = True
        backend.backends.cuda.enable_math_sdp(True)
        backend.backends.cuda.enable_flash_sdp(False)
        backend.backends.cuda.enable_mem_efficient_sdp(False)
        backend.backends.cuda.enable_cudnn_sdp(False)


def _prepare_runtime(request):
    """Dormant fixed preparation, denied before request hooks/imports/mutation."""
    _require_operator_handoff()
    if type(request) is not DRequest:
        raise DWireError("DRequest transport required")
    checked = decode_d_request(request.data)
    if type(request.root) is not str or request.root != checked.root:
        raise DWireError("request byte root mismatch")
    if any(name in sys.modules for name in ("torch", "transformers")):
        raise WorkerSettingsError("fresh scientific runtime import required")
    req = parse_canonical_json(checked.data)
    device = "cpu" if req["control_id"] == "alc-r0-qualification-v1-d-cpu-fresh1-s20260916" else "cuda:0"
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      HF_DATASETS_OFFLINE="1", CUBLAS_WORKSPACE_CONFIG=":4096:8")
    if device == "cpu":
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    # GPU visibility is a future independently pinned coordinator duty. Never
    # choose/discover a physical GPU from the request or alter its mapping here.
    import torch

    _apply_runtime_settings(torch, device)
    from .checkpoint_parity_qualification import _context

    _context(device)
    return device


def _diagnostic(error, fallback_stage, diagnostic_types):
    """Private classification-only seam; never invokes a supplied callable."""
    qualification_error, qualification_interrupt, failure_type, oom_error = diagnostic_types
    stage = fallback_stage
    if type(error) in (qualification_error, qualification_interrupt):
        try:
            failure = object.__getattribute__(error, 'failure')
        except AttributeError:
            failure = None
        if type(failure) is failure_type:
            try:
                candidate = object.__getattribute__(failure, 'stage')
            except AttributeError:
                candidate = None
            if type(candidate) is str and candidate in (
                    'tokenizer', 'host', 'official', 'matrix', 'terminal-assets'):
                stage = candidate
    if issubclass(type(error), KeyboardInterrupt):
        return stage, 'interrupted'
    current, seen = error, set()
    for _ in range(8):
        if current is None or id(current) in seen:
            break
        seen.add(id(current))
        if issubclass(type(current), (MemoryError, oom_error)):
            return stage, 'oom'
        cause = BaseException.__cause__.__get__(current)
        current = cause if cause is not None else BaseException.__context__.__get__(current)
    return stage, 'validation' if issubclass(type(error), ValueError) else 'runtime'


def _runtime_oom_type():
    # Classification only; do not import a runtime after failed preparation.
    module = sys.modules.get('torch')
    candidate = vars(module).get('OutOfMemoryError') if type(module) is types.ModuleType else None
    return candidate if type(candidate) is type and issubclass(candidate, BaseException) else MemoryError


def _check_original_deadline(deadline):
    if time.monotonic_ns() >= deadline:
        raise WorkerSettingsError('original fixed D useful deadline expired')


def _terminal_failure(request, stage, category, deadline):
    """At most two bounded diagnostic encodes, never renewed scientific work."""
    from .fixed_d_projection import encode_d_failure

    if category != 'interrupted' and time.monotonic_ns() >= deadline:
        stage, category = 'bootstrap_deadline', 'validation'
    result = encode_d_failure(request, stage=stage, category=category)
    if category != 'interrupted' and stage != 'bootstrap_deadline' and time.monotonic_ns() >= deadline:
        result = encode_d_failure(request, stage='bootstrap_deadline', category='validation')
    return (130 if category == 'interrupted' else 2), result


def _execute_request(request):
    """Dormant fixed scientific composition; unconditional denial remains first.

    Denied/static tests are NOT dynamic execution proof. No output/CLI or producer
    integration, retry, scientific callback, or accepting permit is installed.
    """
    _require_operator_handoff()
    if type(request) is not DRequest:
        raise DWireError('DRequest transport required')
    checked = decode_d_request(request.data)
    if type(request.root) is not str or request.root != checked.root:
        raise DWireError('request byte root mismatch')
    req = parse_canonical_json(checked.data)
    deadline = int(req['useful_deadline_monotonic_ns'])
    from .fixed_d_projection import encode_d_success

    stage = 'worker_context'
    diagnostic_types = (None, None, None, MemoryError)
    try:
        _check_original_deadline(deadline)
        device = _prepare_runtime(checked)
        _check_original_deadline(deadline)
        from .checkpoint_parity_qualification import (
            ParityQualificationError, ParityQualificationInterrupted,
            QualificationFailure, run_parity_qualification,
        )
        diagnostic_types = (ParityQualificationError, ParityQualificationInterrupted,
                            QualificationFailure, _runtime_oom_type())
        stage = 'tokenizer'
        _check_original_deadline(deadline)
        qualification = run_parity_qualification(Path(req['snapshot_path']), device=device)
        _check_original_deadline(deadline)
        stage = 'worker_projection'
        result = encode_d_success(qualification, checked)
        _check_original_deadline(deadline)
        return 0, result
    except (Exception, KeyboardInterrupt) as error:
        diagnostic_types = (*diagnostic_types[:3], _runtime_oom_type())
        stage, category = _diagnostic(error, stage, diagnostic_types)
        return _terminal_failure(checked, stage, category, deadline)


def main():
    """Denied standalone bootstrap: no request file read or environment mutation."""
    try:
        _require_operator_handoff()
    except WorkerHandoffUnavailable:
        sys.stderr.write("alc-r0 fixed D denied: reviewed operator handoff unavailable\n")
        return 2
    # A future handoff implementation also needs the actual fixed worker body;
    # reaching here must not imply completion or accidentally return success.
    raise WorkerHandoffUnavailable("fixed scientific invocation is not installed")


if __name__ == "__main__":
    raise SystemExit(main())
