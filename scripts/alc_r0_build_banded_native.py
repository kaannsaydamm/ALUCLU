"""Explicit clean-source Windows fixture build; artifacts stay outside checkout."""

import argparse
import ctypes as ct
import hashlib
import json
import os
import subprocess
from pathlib import Path

COMPILER = Path(
    "C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/cl.exe"
)
SDK = Path("C:/Program Files (x86)/Windows Kits/10")
SDK_VERSION = "10.0.26100.0"
FLAGS = ["/nologo", "/O2", "/std:c++17", "/EHsc", "/MT", "/LD"]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_build_exit(path, exit_code):
    path.write_bytes(str(exit_code).encode("ascii") + b"\n")


def build_id_include(source_hash):
    return (
        "static const unsigned char ALC_R0_BUILD_ID[32] = {"
        + ",".join(str(b) for b in bytes.fromhex(source_hash))
        + "};\n"
    ).encode("ascii")


def compile_locked_snapshot(command, out, env, snapshot, include):
    """Hold source/include read handles denying writes/deletes while cl reads."""
    kernel = ct.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        ct.c_wchar_p,
        ct.c_uint32,
        ct.c_uint32,
        ct.c_void_p,
        ct.c_uint32,
        ct.c_uint32,
        ct.c_void_p,
    ]
    kernel.CreateFileW.restype = ct.c_void_p
    kernel.CloseHandle.argtypes = [ct.c_void_p]
    kernel.CloseHandle.restype = ct.c_int
    handles = []
    try:
        for path in (snapshot, include):
            handle = kernel.CreateFileW(str(path), 0x80000000, 1, None, 3, 0, None)
            if handle == ct.c_void_p(-1).value:
                raise OSError(ct.get_last_error(), "cannot lock build source")
            handles.append(handle)
        return subprocess.run(command, cwd=out, env=env, capture_output=True)
    finally:
        for handle in handles:
            kernel.CloseHandle(handle)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]

    def git(*parts):
        return subprocess.check_output(
            ["git", "-C", str(root), *parts], text=True
        ).strip()

    if git("status", "--porcelain", "--untracked-files=all"):
        raise RuntimeError("clean committed reviewed source required before build")
    commit, tree = git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}")
    out = args.output_dir.resolve()
    if out == root or root in out.parents:
        raise RuntimeError("build artifacts must be outside checkout")
    if out.exists() and any(out.iterdir()):
        raise RuntimeError("fresh output directory required")
    out.mkdir(parents=True, exist_ok=True)
    paths = [
        root / p
        for p in (
            "native/alc_r0/banded_edit_visibility.cpp",
            "src/aluclu/alc_r0/banded_edit_token_visibility_native.py",
            "src/aluclu/alc_r0/banded_edit_token_visibility_reference.py",
            "docs/superpowers/plans/2026-10-02-alc-r0-banded-native-fixture-design.md",
            "scripts/alc_r0_build_banded_native.py",
            "tests/test_alc_r0_banded_native.py",
        )
    ]
    source_hashes = {str(p): digest(p) for p in paths}
    native_hash = source_hashes[str(paths[0])]
    include = out / "alc_r0_build_id.h"
    include.write_bytes(build_id_include(native_hash))
    snapshot = out / "banded_edit_visibility.cpp"
    snapshot.write_bytes(paths[0].read_bytes())
    if digest(snapshot) != native_hash:
        raise RuntimeError("native snapshot source mismatch")
    vc = COMPILER.parents[3]
    linker = COMPILER.with_name("link.exe")
    tool_hashes = {str(tool): digest(tool) for tool in (COMPILER, linker)}
    version = subprocess.run([str(COMPILER)], capture_output=True)
    linker_version = subprocess.run([str(linker)], capture_output=True)
    env = os.environ.copy()
    env["INCLUDE"] = os.pathsep.join(
        str(p)
        for p in [
            vc / "include",
            *[SDK / "Include" / SDK_VERSION / p for p in ("ucrt", "shared", "um")],
        ]
    )
    env["LIB"] = os.pathsep.join(
        str(p)
        for p in [
            vc / "lib/x64",
            *[SDK / "Lib" / SDK_VERSION / p / "x64" for p in ("ucrt", "um")],
        ]
    )
    env["PATH"] = str(COMPILER.parent) + os.pathsep + env["PATH"]
    dll = out / "alc_r0_banded_fixture.dll"
    command = [
        str(COMPILER),
        *FLAGS,
        "/I" + str(out),
        str(snapshot),
        "/Fo" + str(out / "banded.obj"),
        "/Fe" + str(dll),
        "/link",
        "/IMPLIB:" + str(out / "banded.lib"),
    ]
    run = compile_locked_snapshot(command, out, env, snapshot, include)
    (out / "build.stdout.log").write_bytes(run.stdout)
    (out / "build.stderr.log").write_bytes(run.stderr)
    write_build_exit(out / "build.exit.log", run.returncode)
    if run.returncode:
        raise RuntimeError(f"compiler failed: {run.returncode}")
    deps = subprocess.run(
        [str(COMPILER.with_name("dumpbin.exe")), "/dependents", str(dll)],
        capture_output=True,
    )
    (out / "dependencies.log").write_bytes(deps.stdout + deps.stderr)
    if deps.returncode:
        raise RuntimeError("dependency inventory failed")
    version_after = subprocess.run([str(COMPILER)], capture_output=True)
    linker_version_after = subprocess.run([str(linker)], capture_output=True)
    if (
        git("status", "--porcelain", "--untracked-files=all")
        or git("rev-parse", "HEAD") != commit
        or git("rev-parse", "HEAD^{tree}") != tree
        or {str(p): digest(p) for p in paths} != source_hashes
        or digest(snapshot) != native_hash
        or digest(include) != hashlib.sha256(build_id_include(native_hash)).hexdigest()
        or {str(tool): digest(tool) for tool in (COMPILER, linker)} != tool_hashes
        or (version.stdout, version.stderr, version.returncode)
        != (version_after.stdout, version_after.stderr, version_after.returncode)
        or (linker_version.stdout, linker_version.stderr, linker_version.returncode)
        != (
            linker_version_after.stdout,
            linker_version_after.stderr,
            linker_version_after.returncode,
        )
    ):
        raise RuntimeError("source/commit changed during build; receipt refused")
    receipt = dict(
        abi=1,
        commit=commit,
        tree=tree,
        dirty_at_start=False,
        dirty_at_end=False,
        source_hashes=source_hashes,
        native_source_sha256=native_hash,
        generated_include_path=str(include),
        generated_include_sha256=digest(include),
        native_snapshot_path=str(snapshot),
        native_snapshot_sha256=digest(snapshot),
        compiler_path=str(COMPILER),
        compiler_sha256=tool_hashes[str(COMPILER)],
        compiler_version=(version.stdout + version.stderr).decode(errors="replace"),
        linker_path=str(linker),
        linker_sha256=tool_hashes[str(linker)],
        linker_version=(linker_version.stdout + linker_version.stderr).decode(
            errors="replace"
        ),
        sdk_version=SDK_VERSION,
        architecture="x64",
        command=command,
        compiler_environment={name: env[name] for name in ("INCLUDE", "LIB", "PATH")},
        dll_path=str(dll),
        dll_size=dll.stat().st_size,
        dll_sha256=digest(dll),
        build_exit=run.returncode,
        build_logs={
            str(out / name): digest(out / name)
            for name in ("build.stdout.log", "build.stderr.log", "build.exit.log")
        },
        dependency_command=[
            str(COMPILER.with_name("dumpbin.exe")),
            "/dependents",
            str(dll),
        ],
        dependency_exit=deps.returncode,
        dependencies_path=str(out / "dependencies.log"),
        dependencies_sha256=digest(out / "dependencies.log"),
        training_authority=False,
        held_out_data_present=False,
    )
    (out / "receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    print(out / "receipt.json")


if __name__ == "__main__":
    main()
