"""Real stdlib-only process fixtures; never load a model or authorize training."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from aluclu.alc_r0.checkpoint_owned_process import run_owned_process

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows Job Object evidence")


def run(tmp_path, source, *, seconds=10, **overrides):
    arguments = dict(
        command=(sys.executable, "-I", "-c", source),
        cwd=tmp_path,
        environment=dict(os.environ),
        stdout_path=tmp_path / "stdout.log",
        stderr_path=tmp_path / "stderr.log",
        deadline_ns=time.monotonic_ns() + int(seconds * 1e9),
    )
    arguments.update(overrides)
    return run_owned_process(**arguments)


def test_real_child_streams_arguments_and_explicit_environment(tmp_path):
    environment = dict(os.environ, ALC_OWNED_FIXTURE="exact value")
    receipt = run(
        tmp_path,
        "import os,sys; print(os.environ['ALC_OWNED_FIXTURE']); "
        "print(repr(sys.argv[1:])); print('error-stream', file=sys.stderr)",
        command=(
            sys.executable,
            "-I",
            "-c",
            "import os,sys; print(os.environ['ALC_OWNED_FIXTURE']); "
            "print(repr(sys.argv[1:])); print('error-stream', file=sys.stderr)",
            "a b",
            'quoted"value',
            "",
        ),
        environment=environment,
    )
    assert receipt.exit_code == 0 and not receipt.timed_out
    assert receipt.active_processes == 0
    assert receipt.total_processes >= 1
    assert receipt.finished_ns >= receipt.started_ns
    assert receipt.user_time_100ns >= 0 and receipt.kernel_time_100ns >= 0
    assert "exact value" in (tmp_path / "stdout.log").read_text()
    assert "['a b', 'quoted\"value', '']" in (tmp_path / "stdout.log").read_text()
    assert (tmp_path / "stderr.log").read_text().strip() == "error-stream"


def test_nonzero_exit_is_not_hidden(tmp_path):
    receipt = run(tmp_path, "raise SystemExit(7)")
    assert receipt.exit_code == 7 and not receipt.timed_out


def test_timeout_drains_owned_root_and_descendants(tmp_path):
    source = (
        "import subprocess,sys,time; "
        "subprocess.Popen([sys.executable,'-I','-c','import time; time.sleep(60)']); "
        "print('root-ready',flush=True); time.sleep(60)"
    )
    receipt = run(tmp_path, source, seconds=2)
    assert receipt.timed_out and receipt.exit_code == 124
    assert receipt.active_processes == 0 and receipt.total_processes >= 2
    assert "root-ready" in (tmp_path / "stdout.log").read_text()


def test_exited_root_does_not_hide_live_descendant(tmp_path):
    receipt = run(
        tmp_path,
        "import subprocess,sys; "
        "subprocess.Popen([sys.executable,'-I','-c','import time; time.sleep(60)'])",
        seconds=2,
    )
    assert receipt.timed_out and receipt.active_processes == 0
    assert receipt.exit_code == 0  # root completed; whole job exceeded its deadline
    assert receipt.total_processes >= 2


def test_unrelated_owned_test_process_survives_other_job_timeout(tmp_path):
    unrelated = subprocess.Popen(
        [sys.executable, "-I", "-c", "import time; time.sleep(5)"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        receipt = run(tmp_path, "import time; time.sleep(60)", seconds=1)
        assert receipt.timed_out and unrelated.poll() is None
        assert unrelated.wait(timeout=10) == 0
    finally:
        if unrelated.poll() is None:
            unrelated.terminate()  # exact handle owned by this fixture only
            unrelated.wait(timeout=10)


@pytest.mark.parametrize(
    "overrides",
    [
        {"command": ("python.exe", "-c", "pass")},
        {"command": (sys.executable, "a\x00b")},
        {"command": [sys.executable, "-c", "pass"]},
        {"cwd": Path("relative")},
        {"stdout_path": Path("relative.log")},
        {"deadline_ns": True},
        {"deadline_ns": 1},
        {"environment": {"BAD=KEY": "value"}},
        {"environment": {"GOOD": "bad\x00value"}},
    ],
)
def test_invalid_admission_creates_no_artifacts(tmp_path, overrides):
    with pytest.raises((ValueError, TypeError)):
        run(tmp_path, "pass", **overrides)
    assert list(tmp_path.iterdir()) == []


def test_existing_output_not_overwritten(tmp_path):
    target = tmp_path / "stdout.log"
    target.write_bytes(b"prior evidence")
    with pytest.raises(FileExistsError):
        run(tmp_path, "print('wrong')")
    assert target.read_bytes() == b"prior evidence"


def test_same_output_path_is_rejected_before_creation(tmp_path):
    with pytest.raises(ValueError):
        run(tmp_path, "pass", stderr_path=tmp_path / "stdout.log")
    assert list(tmp_path.iterdir()) == []


def test_job_attribute_failure_prevents_creation(tmp_path, monkeypatch):
    from aluclu.alc_r0 import checkpoint_owned_process as module

    def fail(*args):
        raise OSError("attribute fixture failure")

    monkeypatch.setattr(module, "_update_attribute", fail)
    with pytest.raises(OSError, match="attribute fixture failure"):
        run(tmp_path, "from pathlib import Path; Path('executed').write_text('bad')")
    assert not (tmp_path / "executed").exists()


def test_resume_failure_prevents_execution_and_drains_job(tmp_path, monkeypatch):
    from aluclu.alc_r0 import checkpoint_owned_process as module

    def fail(*args):
        raise OSError("resume fixture failure")

    monkeypatch.setattr(module, "_resume", fail)
    with pytest.raises(OSError, match="resume fixture failure"):
        run(tmp_path, "from pathlib import Path; Path('executed').write_text('bad')")
    assert not (tmp_path / "executed").exists()


def test_deadline_expiring_after_atomic_creation_never_resumes(tmp_path, monkeypatch):
    from aluclu.alc_r0 import checkpoint_owned_process as module

    create = module._create_suspended

    def slow_creation(*args):
        create(*args)
        time.sleep(0.3)

    monkeypatch.setattr(module, "_create_suspended", slow_creation)
    with pytest.raises(TimeoutError, match="before resume"):
        run(
            tmp_path,
            "from pathlib import Path; Path('executed').write_text('bad')",
            seconds=0.2,
        )
    assert not (tmp_path / "executed").exists()


def test_normal_descendant_completion_is_observed(tmp_path):
    receipt = run(
        tmp_path,
        "import subprocess,sys; subprocess.Popen([sys.executable,'-I','-c',"
        '"import time; from pathlib import Path; time.sleep(.3); '
        "Path('descendant-finished').write_text('done')\"])",
    )
    assert receipt.exit_code == 0 and not receipt.timed_out
    assert receipt.active_processes == 0 and receipt.total_processes >= 2
    assert (tmp_path / "descendant-finished").read_text() == "done"


def test_supervisor_abrupt_exit_closes_private_job_and_descendant(tmp_path):
    from aluclu.alc_r0 import checkpoint_owned_process as module

    # The outer job owns this entire fixture, including cleanup if the inner
    # supervisor's kill-on-close were broken. Loading the standalone file avoids
    # package/model-library imports in either child.
    source = (
        "import importlib.util,sys,os,time,threading; from pathlib import Path; "
        f"spec=importlib.util.spec_from_file_location('owned_fixture', {module.__file__!r}); "
        "m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; "
        "spec.loader.exec_module(m); "
        'exec("def exit_after_marker():\\n'
        " while not Path('inner-ready').exists(): time.sleep(.01)\\n"
        ' os._exit(0)\\n"); '
        "threading.Thread(target=exit_after_marker,daemon=True).start(); "
        "m.run_owned_process((sys.executable,'-I','-c',"
        '"from pathlib import Path; import time; '
        "Path('inner-ready').write_text('ready'); time.sleep(60)\"),"
        "cwd=Path.cwd(),environment=dict(os.environ),"
        "stdout_path=Path.cwd()/'inner-out.log',"
        "stderr_path=Path.cwd()/'inner-err.log',"
        "deadline_ns=time.monotonic_ns()+20_000_000_000)"
    )
    receipt = run(tmp_path, source, seconds=8)
    assert (tmp_path / "inner-ready").read_text() == "ready"
    assert receipt.exit_code == 0 and not receipt.timed_out
    assert receipt.active_processes == 0 and receipt.total_processes >= 3


@pytest.mark.parametrize("abrupt", [False, True])
def test_creation_return_interruption_cannot_orphan_suspended_root(tmp_path, abrupt):
    from aluclu.alc_r0 import checkpoint_owned_process as module

    # Outer job owns even an intentionally broken inner implementation. The
    # intercepted root is never resumed, so completion cannot be faked by a
    # fixture that merely exits quickly or fails to write an execution marker.
    source = (
        "import importlib.util,sys,os,time; from pathlib import Path; "
        f"spec=importlib.util.spec_from_file_location('owned_fixture',{module.__file__!r}); "
        "m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; "
        "spec.loader.exec_module(m); original=m._create_suspended; "
        'exec("def interrupt(*args):\\n'
        " original(*args)\\n"
        " Path('interruption-reached').write_text('yes')\\n"
        + (
            " os._exit(0)\\n"
            if abrupt
            else " raise RuntimeError('creation interruption')\\n"
        )
        + '"); m._create_suspended=interrupt; '
        'exec("try:\\n'
        " m.run_owned_process((sys.executable,'-I','-c','import time; time.sleep(60)'),"
        "cwd=Path.cwd(),environment=dict(os.environ),"
        "stdout_path=Path.cwd()/'inner-out.log',stderr_path=Path.cwd()/'inner-err.log',"
        "deadline_ns=time.monotonic_ns()+20_000_000_000)\\n"
        'except RuntimeError: pass\\n")'
    )
    receipt = run(tmp_path, source, seconds=3)
    assert (tmp_path / "interruption-reached").read_text() == "yes"
    assert receipt.exit_code == 0 and not receipt.timed_out
    assert receipt.active_processes == 0 and receipt.total_processes >= 3


@pytest.mark.parametrize("failure", [OSError, KeyboardInterrupt])
@pytest.mark.parametrize("point", ["resume", "creation"])
def test_failed_resume_observation_handle_proves_root_terminal(
    tmp_path, monkeypatch, failure, point
):
    import _winapi

    from aluclu.alc_r0 import checkpoint_owned_process as module

    captured = []
    create = module._create_suspended

    def observe(*args):
        create(*args)
        information = args[-1]
        current = _winapi.GetCurrentProcess()
        captured.append(
            _winapi.DuplicateHandle(
                current,
                information.process,
                current,
                0,
                False,
                _winapi.DUPLICATE_SAME_ACCESS,
            )
        )
        if point == "creation":
            raise failure("resume interruption")

    def fail(*args):
        raise failure("resume interruption")

    monkeypatch.setattr(module, "_create_suspended", observe)
    monkeypatch.setattr(module, "_resume", fail)
    try:
        with pytest.raises(failure, match="resume interruption"):
            run(tmp_path, "import time; time.sleep(60)")
        assert len(captured) == 1
        assert _winapi.WaitForSingleObject(captured[0], 5000) == 0
        assert _winapi.GetExitCodeProcess(captured[0]) == 124
    finally:
        for handle in captured:
            _winapi.CloseHandle(handle)


def test_cleanup_deadline_is_not_renewed_by_exit_retry(monkeypatch):
    from types import SimpleNamespace

    from aluclu.alc_r0 import checkpoint_owned_process as module

    closed = []
    job = object.__new__(module._Job)
    job.handle = 1  # fake kernel only; never passed to a real Win32 call
    job.kernel = SimpleNamespace(
        TerminateJobObject=lambda *args: True,
        CloseHandle=lambda *args: closed.append(True) or True,
    )
    job.cleanup_deadline_ns = None
    monkeypatch.setattr(job, "accounting", lambda: SimpleNamespace(active_processes=1))
    monkeypatch.setattr(module, "_CLEANUP_SECONDS", 0.02)
    with pytest.raises(TimeoutError):
        job.terminate_and_drain()
    deadline = job.cleanup_deadline_ns
    with pytest.raises(TimeoutError):
        job.__exit__(None, None, None)
    assert job.cleanup_deadline_ns == deadline and job.remaining_cleanup_ms() == 0
    assert closed == [True]


def test_native_x64_layouts_match_win32_contract():
    import ctypes

    from aluclu.alc_r0 import checkpoint_owned_process as module

    assert ctypes.sizeof(module._StartupInfo) == 104
    assert ctypes.sizeof(module._StartupInfoEx) == 112
    assert ctypes.sizeof(module._ProcessInformation) == 24
    assert ctypes.sizeof(module._BasicLimits) == 64
    assert ctypes.sizeof(module._ExtendedLimits) == 144
    assert ctypes.sizeof(module._Accounting) == 48


def test_case_duplicate_environment_is_rejected_before_launch(tmp_path):
    with pytest.raises(ValueError, match="case-insensitive"):
        run(tmp_path, "pass", environment={"PATH": "one", "Path": "two"})
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("operation", ["accounting", "terminate_and_drain"])
def test_cleanup_failure_closes_job_and_preserves_error(
    tmp_path, monkeypatch, operation
):
    import _winapi

    from aluclu.alc_r0 import checkpoint_owned_process as module

    captured = []
    create = module._create_suspended

    def fail(*args):
        raise OSError("injected cleanup failure")

    def observe(*args):
        create(*args)
        current = _winapi.GetCurrentProcess()
        captured.append(
            _winapi.DuplicateHandle(
                current,
                args[-1].process,
                current,
                0,
                False,
                _winapi.DUPLICATE_SAME_ACCESS,
            )
        )
        monkeypatch.setattr(module._Job, operation, fail)

    monkeypatch.setattr(module, "_create_suspended", observe)
    try:
        with pytest.raises(OSError, match="injected cleanup failure"):
            run(tmp_path, "import time; time.sleep(60)", seconds=0.5)
        assert len(captured) == 1
        assert _winapi.WaitForSingleObject(captured[0], 5000) == 0
        assert _winapi.GetExitCodeProcess(captured[0]) != 259
    finally:
        for handle in captured:
            _winapi.CloseHandle(handle)


def test_repeated_success_does_not_leak_parent_handles(tmp_path):
    import ctypes

    from aluclu.alc_r0 import checkpoint_owned_process as module

    kernel = module._kernel()
    kernel.GetCurrentProcess.argtypes = []
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    kernel.GetProcessHandleCount.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_uint32),
    ]
    kernel.GetProcessHandleCount.restype = ctypes.c_int

    def count():
        value = ctypes.c_uint32()
        assert kernel.GetProcessHandleCount(
            kernel.GetCurrentProcess(), ctypes.byref(value)
        )
        return value.value

    warmup = tmp_path / "warmup"
    warmup.mkdir()
    run(warmup, "pass")
    before = count()
    for index in range(6):
        directory = tmp_path / str(index)
        directory.mkdir()
        receipt = run(directory, "pass")
        assert receipt.exit_code == 0 and receipt.active_processes == 0
    assert count() <= before
