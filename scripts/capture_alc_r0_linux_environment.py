from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import torch
from packaging.utils import canonicalize_name

from aluclu.alc_r0.canonical import canonical_json_bytes
from aluclu.alc_r0.linux_environment import (
    LINUX_LOCK_PATH,
    build_linux_evaluator_bootstrap_receipt,
)
from aluclu.alc_r0.schema_validation import validate_r0_document

_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_DISTRO_NAME = "ALUCLU-R0-EVAL"
_PYTHON_PREFIX = Path("/opt/aluclu-r0/linux-eval")


class CaptureError(RuntimeError):
    """Raised when a live Linux environment observation is incomplete."""


def _run(*arguments: str) -> str:
    completed = subprocess.run(
        arguments,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=120,
    )
    if completed.returncode != 0:
        raise CaptureError(
            f"command failed ({completed.returncode}): {arguments[0]}: "
            f"{completed.stderr.strip()}"
        )
    return completed.stdout.strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _os_release() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"')
    return values


def _meminfo() -> dict[str, int]:
    values: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text(encoding="ascii").splitlines():
        key, raw = line.split(":", 1)
        fields = raw.split()
        if not fields:
            continue
        amount = int(fields[0])
        if len(fields) > 1 and fields[1] == "kB":
            amount *= 1024
        values[key] = amount
    return values


def _cpu_model() -> str:
    for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
        if line.startswith("model name"):
            return line.split(":", 1)[1].strip()
    raise CaptureError("CPU model is unavailable")


def _python_inventory() -> tuple[list[dict[str, str]], bool]:
    prefix = _PYTHON_PREFIX.resolve(strict=True)
    records: dict[str, str] = {}
    origins_under_prefix = True
    for distribution in importlib.metadata.distributions():
        raw_name = distribution.metadata.get("Name")
        if raw_name is None:
            raise CaptureError("installed distribution lacks a Name field")
        name = canonicalize_name(raw_name)
        version = distribution.version
        if name in records:
            raise CaptureError(f"duplicate installed distribution: {name}")
        records[name] = version
        location = Path(str(distribution.locate_file(""))).resolve(strict=True)
        if not location.is_relative_to(prefix):
            origins_under_prefix = False
    items = [
        {"name": name, "version": records[name]}
        for name in sorted(records, key=lambda item: item.encode("utf-8"))
    ]
    return items, origins_under_prefix


def _distro_inventory() -> list[dict[str, str]]:
    output = _run("dpkg-query", "-W", "-f=${binary:Package}\\t${Version}\\n")
    records: dict[str, str] = {}
    for line in output.splitlines():
        name, separator, version = line.partition("\t")
        if not separator or not name or not version:
            raise CaptureError("malformed dpkg-query record")
        if name in records:
            raise CaptureError(f"duplicate distro package: {name}")
        records[name] = version
    return [
        {"name": name, "version": records[name]}
        for name in sorted(records, key=lambda item: item.encode("utf-8"))
    ]


def _system_site_packages_disabled() -> bool:
    configuration = (_PYTHON_PREFIX / "pyvenv.cfg").read_text(encoding="utf-8")
    values = {}
    for line in configuration.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip().casefold()] = value.strip().casefold()
    return values.get("include-system-site-packages") == "false"


def _gpu_observation() -> tuple[dict[str, Any], dict[str, Any]]:
    raw = _run(
        "nvidia-smi",
        "--query-gpu=name,driver_version,memory.total,compute_cap",
        "--format=csv,noheader,nounits",
    )
    rows = [row.strip() for row in raw.splitlines() if row.strip()]
    if len(rows) != 1:
        raise CaptureError("exactly one NVIDIA GPU row is required")
    fields = [field.strip() for field in rows[0].split(",")]
    if len(fields) != 4:
        raise CaptureError("unexpected nvidia-smi field count")
    compute_capability = [int(part) for part in fields[3].split(".")]

    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    if not torch.cuda.is_available():
        raise CaptureError("CUDA is unavailable")
    left = torch.tensor([[1.5, -2.0], [3.0, 4.0]], device="cuda", dtype=torch.bfloat16)
    right = torch.tensor([[2.0, 1.0], [-1.0, 3.0]], device="cuda", dtype=torch.bfloat16)
    product = torch.matmul(left, right)
    torch.cuda.synchronize()
    torch_version_module = importlib.import_module("torch.version")
    accelerator = {
        "bf16_supported": torch.cuda.is_bf16_supported(),
        "compute_capability": compute_capability,
        "cuda_available": torch.cuda.is_available(),
        "cuda_runtime": getattr(torch_version_module, "cuda", None),
        "cudnn_version": torch.backends.cudnn.version(),
        "device_count": torch.cuda.device_count(),
        "device_name": torch.cuda.get_device_name(0),
        "driver_version": fields[1],
        "memory_mib": int(fields[2]),
        "torch_version": torch.__version__,
    }
    probe = {
        "cudnn_benchmark": torch.backends.cudnn.benchmark,
        "cudnn_tf32": torch.backends.cudnn.allow_tf32,
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        "device": str(product.device),
        "dtype": str(product.dtype),
        "matmul_tf32": torch.backends.cuda.matmul.allow_tf32,
        "values_fp32": product.float().cpu().tolist(),
    }
    return accelerator, probe


def _verify_source_origins(repo_root: Path) -> None:
    root = repo_root.resolve(strict=True)
    for module_name in (
        "aluclu.alc_r0.canonical",
        "aluclu.alc_r0.linux_environment",
        "aluclu.alc_r0.schema_validation",
    ):
        module = sys.modules.get(module_name)
        if module is None or not isinstance(module.__file__, str):
            raise CaptureError(f"source module is unavailable: {module_name}")
        origin = Path(module.__file__).resolve(strict=True)
        if not origin.is_relative_to(root):
            raise CaptureError(f"source module escaped exported tree: {module_name}")


def _capture(args: argparse.Namespace) -> dict[str, object]:
    if _COMMIT.fullmatch(args.expected_source_commit) is None:
        raise CaptureError("expected source commit must be lowercase Git SHA-1")
    if platform.system() != "Linux":
        raise CaptureError("capture must run inside Linux")
    if os.environ.get("WSL_DISTRO_NAME") != _DISTRO_NAME:
        raise CaptureError("capture must run in ALUCLU-R0-EVAL")
    if Path(sys.prefix).resolve() != _PYTHON_PREFIX:
        raise CaptureError("capture must run from the frozen Linux evaluator venv")

    repo_root = args.repo_root.resolve(strict=True)
    _verify_source_origins(repo_root)
    lock_path = repo_root / Path(LINUX_LOCK_PATH)
    lock_manifest_path = repo_root / "locks/alc_r0/v1/lock-manifest.json"
    schema_root = (repo_root / "schemas/alc_r0/v1").resolve(strict=True)
    uv_path = args.uv.resolve(strict=True)
    uv_installer_path = args.uv_installer.resolve(strict=True)
    if _run(str(uv_path), "--version") != "uv 0.12.5 (x86_64-unknown-linux-gnu)":
        raise CaptureError("uv executable identity mismatch")

    dependency_output = _run(
        str(uv_path), "pip", "check", "--python", str(_PYTHON_PREFIX / "bin/python")
    )
    dependency_check = "All installed packages are compatible" in dependency_output
    python_packages, origins_under_prefix = _python_inventory()
    distro_packages = _distro_inventory()
    os_release = _os_release()
    memory = _meminfo()
    disk = shutil.disk_usage("/")
    accelerator, probe = _gpu_observation()
    filesystem_type = _run("findmnt", "-no", "FSTYPE", "/")

    receipt = build_linux_evaluator_bootstrap_receipt(
        source_commit=args.expected_source_commit,
        distro={
            "filesystem_type": filesystem_type,
            "kernel_release": platform.release(),
            "machine": platform.machine(),
            "name": os.environ["WSL_DISTRO_NAME"],
            "os_id": os_release.get("ID"),
            "pretty_name": os_release.get("PRETTY_NAME"),
            "version_id": os_release.get("VERSION_ID"),
            "wsl_version": 2,
        },
        resources={
            "cpu_model": _cpu_model(),
            "filesystem_free_bytes": disk.free,
            "filesystem_total_bytes": disk.total,
            "logical_cpu_count": os.cpu_count(),
            "ram_total_bytes": memory.get("MemTotal"),
            "swap_total_bytes": memory.get("SwapTotal"),
        },
        lock_relative_path=LINUX_LOCK_PATH,
        lock_bytes=lock_path.read_bytes(),
        lock_manifest_bytes=lock_manifest_path.read_bytes(),
        uv={
            "executable_sha256": _sha256(uv_path),
            "installer_sha256": _sha256(uv_installer_path),
            "version": "0.12.5",
        },
        python={
            "base_prefix": sys.base_prefix,
            "implementation": platform.python_implementation(),
            "prefix": sys.prefix,
            "system_site_packages": not _system_site_packages_disabled(),
            "version": platform.python_version(),
        },
        python_packages=python_packages,
        dependency_check=dependency_check,
        package_origins_under_prefix=origins_under_prefix,
        distro_packages=distro_packages,
        accelerator=accelerator,
        bf16_probe=probe,
    )
    encoded = canonical_json_bytes(receipt)
    validate_r0_document(
        encoded,
        schema_name="linux-evaluator-bootstrap-receipt",
        schema_root=schema_root,
    )
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Capture a non-authorizing ALC-R0 Linux evaluator bootstrap receipt."
    )
    parser.add_argument("--expected-source-commit", required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--uv", type=Path, required=True)
    parser.add_argument("--uv-installer", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.output.is_absolute():
        raise CaptureError("output path must be absolute")
    if args.output.exists() or args.output.is_symlink():
        raise CaptureError("output path must be new")
    if not args.output.parent.is_dir() or args.output.parent.is_symlink():
        raise CaptureError("output parent must be an existing real directory")

    receipt = _capture(args)
    encoded = canonical_json_bytes(receipt)
    with args.output.open("xb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    print(
        json.dumps(
            {
                "byte_length": len(encoded),
                "output": str(args.output),
                "sha256": hashlib.sha256(encoded).hexdigest(),
                "training_authority": False,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
