"""Trusted Windows execution primitive, NOT experiment admission or a sandbox.

The caller must authenticate source/runtime/assets, reconcile resource budgets,
and persist its attempt journal BEFORE invoking this primitive. Supply an absolute
monotonic deadline established before preflight; this function does not renew it.
Only newly created process handles and their private job are ever terminated.
Ordinary CreateProcess descendants are contained; hostile privileged/WMI escapes
are outside this boundary. Exit zero is not scientific acceptance.
"""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys
import time
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path

_KILL_ON_JOB_CLOSE = 0x2000
_CREATE_SUSPENDED = 0x4
_EXTENDED_STARTUPINFO_PRESENT = 0x80000
_CREATE_UNICODE_ENVIRONMENT = 0x400
_ATTRIBUTE_HANDLE_LIST = 0x20002
_ATTRIBUTE_JOB_LIST = 0x2000D
_CLEANUP_SECONDS = 10


@dataclass(frozen=True)
class OwnedProcessReceipt:
    """OS observations only; CPU times are not measured GPU consumption."""

    root_pid: int
    exit_code: int
    timed_out: bool
    started_ns: int
    finished_ns: int
    total_processes: int
    active_processes: int
    user_time_100ns: int
    kernel_time_100ns: int


class _BasicLimits(ctypes.Structure):
    _fields_ = [
        ("process_time", ctypes.c_int64),
        ("job_time", ctypes.c_int64),
        ("flags", ctypes.c_uint32),
        ("min_working_set", ctypes.c_size_t),
        ("max_working_set", ctypes.c_size_t),
        ("active_limit", ctypes.c_uint32),
        ("affinity", ctypes.c_size_t),
        ("priority", ctypes.c_uint32),
        ("scheduling", ctypes.c_uint32),
    ]


class _IoCounters(ctypes.Structure):
    _fields_ = [
        (name, ctypes.c_uint64)
        for name in (
            "read_operations",
            "write_operations",
            "other_operations",
            "read_bytes",
            "write_bytes",
            "other_bytes",
        )
    ]


class _ExtendedLimits(ctypes.Structure):
    _fields_ = [
        ("basic", _BasicLimits),
        ("io", _IoCounters),
        ("process_memory", ctypes.c_size_t),
        ("job_memory", ctypes.c_size_t),
        ("peak_process_memory", ctypes.c_size_t),
        ("peak_job_memory", ctypes.c_size_t),
    ]


class _Accounting(ctypes.Structure):
    _fields_ = [
        ("user_time", ctypes.c_int64),
        ("kernel_time", ctypes.c_int64),
        ("period_user_time", ctypes.c_int64),
        ("period_kernel_time", ctypes.c_int64),
        ("page_faults", ctypes.c_uint32),
        ("total_processes", ctypes.c_uint32),
        ("active_processes", ctypes.c_uint32),
        ("terminated_processes", ctypes.c_uint32),
    ]


class _StartupInfo(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_uint32),
        ("reserved", ctypes.c_wchar_p),
        ("desktop", ctypes.c_wchar_p),
        ("title", ctypes.c_wchar_p),
        *[
            (name, ctypes.c_uint32)
            for name in (
                "x",
                "y",
                "x_size",
                "y_size",
                "x_chars",
                "y_chars",
                "fill",
                "flags",
            )
        ],
        ("show", ctypes.c_uint16),
        ("reserved_size", ctypes.c_uint16),
        ("reserved_bytes", ctypes.c_void_p),
        ("stdin", ctypes.c_void_p),
        ("stdout", ctypes.c_void_p),
        ("stderr", ctypes.c_void_p),
    ]


class _StartupInfoEx(ctypes.Structure):
    _fields_ = [("basic", _StartupInfo), ("attributes", ctypes.c_void_p)]


class _ProcessInformation(ctypes.Structure):
    _fields_ = [
        ("process", ctypes.c_void_p),
        ("thread", ctypes.c_void_p),
        ("pid", ctypes.c_uint32),
        ("tid", ctypes.c_uint32),
    ]


def _kernel():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    signatures = {
        "CreateJobObjectW": ([ctypes.c_void_p, ctypes.c_wchar_p], ctypes.c_void_p),
        "SetInformationJobObject": (
            [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32],
            ctypes.c_int,
        ),
        "QueryInformationJobObject": (
            [
                ctypes.c_void_p,
                ctypes.c_int,
                ctypes.c_void_p,
                ctypes.c_uint32,
                ctypes.c_void_p,
            ],
            ctypes.c_int,
        ),
        "InitializeProcThreadAttributeList": (
            [
                ctypes.c_void_p,
                ctypes.c_uint32,
                ctypes.c_uint32,
                ctypes.POINTER(ctypes.c_size_t),
            ],
            ctypes.c_int,
        ),
        "UpdateProcThreadAttribute": (
            [
                ctypes.c_void_p,
                ctypes.c_uint32,
                ctypes.c_size_t,
                ctypes.c_void_p,
                ctypes.c_size_t,
                ctypes.c_void_p,
                ctypes.c_void_p,
            ],
            ctypes.c_int,
        ),
        "DeleteProcThreadAttributeList": ([ctypes.c_void_p], None),
        "CreateProcessW": (
            [
                ctypes.c_wchar_p,
                ctypes.c_wchar_p,
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_int,
                ctypes.c_uint32,
                ctypes.c_void_p,
                ctypes.c_wchar_p,
                ctypes.c_void_p,
                ctypes.POINTER(_ProcessInformation),
            ],
            ctypes.c_int,
        ),
        "TerminateJobObject": ([ctypes.c_void_p, ctypes.c_uint32], ctypes.c_int),
        "ResumeThread": ([ctypes.c_void_p], ctypes.c_uint32),
        "CloseHandle": ([ctypes.c_void_p], ctypes.c_int),
    }
    for name, (arguments, result) in signatures.items():
        function = getattr(kernel, name)
        function.argtypes = arguments
        function.restype = result
    return kernel


def _checked(result):
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())
    return result


class _Job:
    def __init__(self):
        self.kernel = _kernel()
        self.cleanup_deadline_ns = None
        self.handle = _checked(self.kernel.CreateJobObjectW(None, None))
        try:
            limits = _ExtendedLimits()
            limits.basic.flags = _KILL_ON_JOB_CLOSE
            _checked(
                self.kernel.SetInformationJobObject(
                    self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)
                )
            )
        except BaseException:
            _checked(self.kernel.CloseHandle(self.handle))
            raise

    def accounting(self):
        value = _Accounting()
        _checked(
            self.kernel.QueryInformationJobObject(
                self.handle, 1, ctypes.byref(value), ctypes.sizeof(value), None
            )
        )
        return value

    def terminate_and_drain(self):
        self.remaining_cleanup_ms()
        _checked(self.kernel.TerminateJobObject(self.handle, 124))
        while self.accounting().active_processes:
            if not self.remaining_cleanup_ms():
                raise TimeoutError("owned job did not drain within cleanup deadline")
            time.sleep(0.01)

    def remaining_cleanup_ms(self):
        if self.cleanup_deadline_ns is None:
            self.cleanup_deadline_ns = time.monotonic_ns() + int(_CLEANUP_SECONDS * 1e9)
        remaining = self.cleanup_deadline_ns - time.monotonic_ns()
        return max(0, remaining // 1_000_000)

    def __enter__(self):
        return self

    def __exit__(self, *exception):
        try:
            if self.accounting().active_processes:
                self.terminate_and_drain()
        finally:
            _checked(self.kernel.CloseHandle(self.handle))


def _resume(thread):
    previous = _kernel().ResumeThread(thread)
    if previous == 0xFFFFFFFF:
        raise ctypes.WinError(ctypes.get_last_error())
    if previous != 1:
        raise RuntimeError("owned primary thread has unexpected suspend count")


def _validate(command, cwd, environment, stdout_path, stderr_path, deadline_ns):
    if os.name != "nt" or ctypes.sizeof(ctypes.c_void_p) != 8:
        raise OSError("owned process reference implementation requires Windows x64")
    if sys.getwindowsversion().major < 10:
        raise OSError("creation-time job ownership requires Windows 10 or newer")
    if type(command) is not tuple or not command:
        raise TypeError("command must be a nonempty immutable tuple")
    if any(type(argument) is not str or "\x00" in argument for argument in command):
        raise ValueError("command arguments must be NUL-free strings")
    executable = Path(command[0])
    if not executable.is_absolute() or not executable.is_file():
        raise ValueError("explicit existing absolute executable required")
    if len(subprocess.list2cmdline(command)) >= 32767:
        raise ValueError("Windows command line limit exceeded")
    if not isinstance(cwd, Path) or not cwd.is_absolute() or not cwd.is_dir():
        raise ValueError("existing absolute working directory required")
    for target in (stdout_path, stderr_path):
        if not isinstance(target, Path) or not target.is_absolute():
            raise ValueError("absolute output paths required")
        if not target.parent.is_dir():
            raise ValueError("existing output parent required")
    if stdout_path.resolve() == stderr_path.resolve():
        raise ValueError("output paths must be distinct")
    if type(environment) is not dict or any(
        type(key) is not str
        or not key
        or "=" in key
        or "\x00" in key
        or type(value) is not str
        or "\x00" in value
        for key, value in environment.items()
    ):
        raise ValueError("explicit valid string environment required")
    if len({key.upper() for key in environment}) != len(environment):
        raise ValueError("case-insensitive environment keys must be unique")
    if type(deadline_ns) is not int or deadline_ns <= time.monotonic_ns():
        raise ValueError("unexpired absolute monotonic deadline required")


def _inherited_handle(stack, stream):
    import _winapi
    import msvcrt

    process = _winapi.GetCurrentProcess()
    handle = _winapi.DuplicateHandle(
        process,
        msvcrt.get_osfhandle(stream.fileno()),
        process,
        0,
        True,
        _winapi.DUPLICATE_SAME_ACCESS,
    )
    stack.callback(_winapi.CloseHandle, handle)
    return handle


def _update_attribute(kernel, attributes, key, value):
    _checked(
        kernel.UpdateProcThreadAttribute(
            attributes, 0, key, ctypes.byref(value), ctypes.sizeof(value), None, None
        )
    )


def _create_suspended(
    command, cwd, environment, stdin, stdout, stderr, deadline_ns, job, information
):
    import _winapi

    # Dedicated inheritable copies exist only during CreateProcess. Original
    # stream handles stay non-inheritable. HANDLE_LIST restricts this launch.
    with ExitStack() as stack:
        startup = _StartupInfoEx()
        startup.basic.cb = ctypes.sizeof(startup)
        startup.basic.flags = subprocess.STARTF_USESTDHANDLES
        startup.basic.stdin = _inherited_handle(stack, stdin)
        startup.basic.stdout = _inherited_handle(stack, stdout)
        startup.basic.stderr = _inherited_handle(stack, stderr)
        handles = (ctypes.c_void_p * 3)(
            startup.basic.stdin, startup.basic.stdout, startup.basic.stderr
        )
        jobs = (ctypes.c_void_p * 1)(job.handle)
        size = ctypes.c_size_t()
        result = job.kernel.InitializeProcThreadAttributeList(
            None, 2, 0, ctypes.byref(size)
        )
        if result or ctypes.get_last_error() != 122 or not size.value:
            raise OSError("unexpected attribute-list sizing result")
        attributes = ctypes.create_string_buffer(size.value)
        _checked(
            job.kernel.InitializeProcThreadAttributeList(
                attributes, 2, 0, ctypes.byref(size)
            )
        )
        stack.callback(job.kernel.DeleteProcThreadAttributeList, attributes)
        _update_attribute(job.kernel, attributes, _ATTRIBUTE_HANDLE_LIST, handles)
        _update_attribute(job.kernel, attributes, _ATTRIBUTE_JOB_LIST, jobs)
        startup.attributes = ctypes.addressof(attributes)
        command_line = ctypes.create_unicode_buffer(subprocess.list2cmdline(command))
        # Win32 Unicode environment blocks are case-insensitively ordered and
        # double-NUL terminated, including the empty explicit environment.
        entries = [
            f"{key}={environment[key]}" for key in sorted(environment, key=str.upper)
        ]
        environment_block = ctypes.create_unicode_buffer(
            "\x00".join(entries) + "\x00\x00"
        )
        if time.monotonic_ns() >= deadline_ns:
            raise TimeoutError("owned deadline expired before process creation")
        _checked(
            job.kernel.CreateProcessW(
                command[0],
                command_line,
                None,
                None,
                True,
                _CREATE_SUSPENDED
                | _EXTENDED_STARTUPINFO_PRESENT
                | _CREATE_UNICODE_ENVIRONMENT
                | _winapi.CREATE_NO_WINDOW,
                environment_block,
                str(cwd),
                ctypes.byref(startup),
                ctypes.byref(information),
            )
        )


def _execute(command, cwd, environment, stdin, stdout, stderr, deadline_ns):
    import _winapi

    # The output structure lives before acquisition and remains visible even if
    # CreateProcess succeeds but helper cleanup/return is interrupted. JOB_LIST
    # associates the process atomically, eliminating the unassigned-root interval.
    information = _ProcessInformation()
    with _Job() as job:
        started = time.monotonic_ns()
        try:
            _create_suspended(
                command,
                cwd,
                environment,
                stdin,
                stdout,
                stderr,
                deadline_ns,
                job,
                information,
            )
            if time.monotonic_ns() >= deadline_ns:
                raise TimeoutError("owned deadline expired before resume")
            _resume(information.thread)
            timed_out = False
            while True:
                if time.monotonic_ns() >= deadline_ns:
                    timed_out = True
                    job.terminate_and_drain()
                    break
                if not job.accounting().active_processes:
                    break
                remaining = (deadline_ns - time.monotonic_ns()) / 1e9
                time.sleep(max(0, min(0.02, remaining)))
            accounting = job.accounting()
            if (
                _winapi.WaitForSingleObject(
                    information.process, job.remaining_cleanup_ms()
                )
                != 0
            ):
                raise TimeoutError("owned root terminal state was not observable")
            return OwnedProcessReceipt(
                root_pid=information.pid,
                exit_code=_winapi.GetExitCodeProcess(information.process),
                timed_out=timed_out,
                started_ns=started,
                finished_ns=time.monotonic_ns(),
                total_processes=accounting.total_processes,
                active_processes=accounting.active_processes,
                user_time_100ns=accounting.user_time,
                kernel_time_100ns=accounting.kernel_time,
            )
        finally:
            try:
                if information.thread:
                    _winapi.CloseHandle(information.thread)
            finally:
                if information.process:
                    _winapi.CloseHandle(information.process)


def run_owned_process(
    command: tuple[str, ...],
    *,
    cwd: Path,
    environment: dict[str, str],
    stdout_path: Path,
    stderr_path: Path,
    deadline_ns: int,
) -> OwnedProcessReceipt:
    """Run a trusted command without a shell; drain its owned tree before return.

    Output files are exclusively created, never overwritten. Failed admission or
    creation may leave empty/partial files; their presence is never success. The
    absolute deadline includes caller preflight, not just this process's lifetime.
    Cleanup may take up to ten extra seconds and is not counted as useful work.
    """
    _validate(command, cwd, environment, stdout_path, stderr_path, deadline_ns)
    with ExitStack() as stack:
        stdout = stack.enter_context(stdout_path.open("xb"))
        stderr = stack.enter_context(stderr_path.open("xb"))
        stdin = stack.enter_context(open(os.devnull, "rb"))
        return _execute(
            command, cwd, dict(environment), stdin, stdout, stderr, deadline_ns
        )
