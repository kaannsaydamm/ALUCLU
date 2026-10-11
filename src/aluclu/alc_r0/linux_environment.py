"""Fail-closed evidence construction for the non-authorizing Linux bootstrap."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence
from typing import Any

from aluclu.alc_r0.canonical import canonical_json_bytes, normalize_evidence_path

EXPERIMENT_ID = "alc-r0-smollm2-135m-v1"
LINUX_LOCK_PATH = "locks/alc_r0/v1/linux-eval.lock"
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class LinuxEnvironmentEvidenceError(ValueError):
    """Raised when the Linux bootstrap observation cannot support its receipt."""


def _exact_mapping(
    value: Mapping[str, Any], *, keys: set[str], label: str
) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != keys:
        raise LinuxEnvironmentEvidenceError(f"{label} fields differ from contract")
    return dict(value)


def _require_sha256(value: object, *, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise LinuxEnvironmentEvidenceError(f"{label} must be lowercase SHA-256")
    return value


def _package_inventory(
    packages: Sequence[Mapping[str, str]], *, label: str
) -> dict[str, object]:
    if not packages:
        raise LinuxEnvironmentEvidenceError(f"{label} inventory must not be empty")
    copied: list[dict[str, str]] = []
    for package in packages:
        record = _exact_mapping(package, keys={"name", "version"}, label=label)
        name = record["name"]
        version = record["version"]
        if (
            not isinstance(name, str)
            or not name
            or not isinstance(version, str)
            or not version
        ):
            raise LinuxEnvironmentEvidenceError(
                f"{label} package name and version must be nonempty strings"
            )
        copied.append({"name": name, "version": version})
    names = [item["name"] for item in copied]
    if names != sorted(names, key=lambda item: item.encode("utf-8")):
        raise LinuxEnvironmentEvidenceError(f"{label} inventory is not UTF-8 sorted")
    if len(set(names)) != len(names):
        raise LinuxEnvironmentEvidenceError(f"{label} inventory contains duplicates")
    encoded = canonical_json_bytes(copied)
    return {
        "count": len(copied),
        "items": copied,
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def build_linux_evaluator_bootstrap_receipt(
    *,
    source_commit: str,
    distro: Mapping[str, Any],
    resources: Mapping[str, Any],
    lock_relative_path: str,
    lock_bytes: bytes,
    lock_manifest_bytes: bytes,
    uv: Mapping[str, Any],
    python: Mapping[str, Any],
    python_packages: Sequence[Mapping[str, str]],
    dependency_check: bool,
    package_origins_under_prefix: bool = True,
    distro_packages: Sequence[Mapping[str, str]],
    accelerator: Mapping[str, Any],
    bf16_probe: Mapping[str, Any],
) -> dict[str, object]:
    """Build a factual bootstrap receipt that cannot authorize scientific runs."""

    if _COMMIT.fullmatch(source_commit) is None:
        raise LinuxEnvironmentEvidenceError("source commit must be lowercase Git SHA-1")
    distro_record = _exact_mapping(
        distro,
        keys={
            "filesystem_type",
            "kernel_release",
            "machine",
            "name",
            "os_id",
            "pretty_name",
            "version_id",
            "wsl_version",
        },
        label="distro",
    )
    if distro_record["name"] != "ALUCLU-R0-EVAL":
        raise LinuxEnvironmentEvidenceError("distro name is not ALUCLU-R0-EVAL")
    if distro_record["os_id"] != "ubuntu" or distro_record["version_id"] != "24.04":
        raise LinuxEnvironmentEvidenceError("distro release is not frozen Ubuntu 24.04")
    if distro_record["wsl_version"] != 2:
        raise LinuxEnvironmentEvidenceError("evaluator must run under WSL2")
    if (
        distro_record["machine"] != "x86_64"
        or distro_record["filesystem_type"] != "ext4"
    ):
        raise LinuxEnvironmentEvidenceError("distro architecture/filesystem mismatch")
    if not str(distro_record["kernel_release"]).endswith("microsoft-standard-WSL2"):
        raise LinuxEnvironmentEvidenceError("kernel is not the expected WSL2 family")

    resource_record = _exact_mapping(
        resources,
        keys={
            "cpu_model",
            "filesystem_free_bytes",
            "filesystem_total_bytes",
            "logical_cpu_count",
            "ram_total_bytes",
            "swap_total_bytes",
        },
        label="resources",
    )
    integer_resources = {
        key: resource_record[key] for key in resource_record if key != "cpu_model"
    }
    if (
        not isinstance(resource_record["cpu_model"], str)
        or not resource_record["cpu_model"]
    ):
        raise LinuxEnvironmentEvidenceError("CPU model must be nonempty")
    if any(
        not isinstance(value, int) or value < 0 for value in integer_resources.values()
    ):
        raise LinuxEnvironmentEvidenceError(
            "resource counters must be nonnegative integers"
        )
    if (
        resource_record["logical_cpu_count"] < 1
        or resource_record["ram_total_bytes"] < 1
    ):
        raise LinuxEnvironmentEvidenceError(
            "CPU/RAM resource counters must be positive"
        )
    if resource_record["filesystem_total_bytes"] < 1 or (
        resource_record["filesystem_free_bytes"]
        > resource_record["filesystem_total_bytes"]
    ):
        raise LinuxEnvironmentEvidenceError(
            "filesystem resource counters are inconsistent"
        )

    if normalize_evidence_path(lock_relative_path) != LINUX_LOCK_PATH:
        raise LinuxEnvironmentEvidenceError("Linux lock path mismatch")
    if not isinstance(lock_bytes, bytes) or not lock_bytes:
        raise LinuxEnvironmentEvidenceError("Linux lock bytes must not be empty")
    if not isinstance(lock_manifest_bytes, bytes) or not lock_manifest_bytes:
        raise LinuxEnvironmentEvidenceError("lock manifest bytes must not be empty")

    uv_record = _exact_mapping(
        uv,
        keys={"executable_sha256", "installer_sha256", "version"},
        label="uv",
    )
    if uv_record["version"] != "0.12.5":
        raise LinuxEnvironmentEvidenceError("uv version differs from lock resolver")
    _require_sha256(uv_record["executable_sha256"], label="uv executable")
    _require_sha256(uv_record["installer_sha256"], label="uv installer")

    python_record = _exact_mapping(
        python,
        keys={
            "base_prefix",
            "implementation",
            "prefix",
            "system_site_packages",
            "version",
        },
        label="python",
    )
    if python_record != {
        "base_prefix": "/usr",
        "implementation": "CPython",
        "prefix": "/opt/aluclu-r0/linux-eval",
        "system_site_packages": False,
        "version": "3.12.3",
    }:
        raise LinuxEnvironmentEvidenceError("Python environment differs from contract")
    if dependency_check is not True:
        raise LinuxEnvironmentEvidenceError("dependency check must pass")
    if package_origins_under_prefix is not True:
        raise LinuxEnvironmentEvidenceError(
            "package origins must remain under venv prefix"
        )
    python_inventory = _package_inventory(python_packages, label="python package")
    versions = {item["name"]: item["version"] for item in python_inventory["items"]}  # type: ignore[index]
    required_versions = {
        "rfc8785": "0.1.4",
        "torch": "2.14.0+cu130",
        "transformers": "5.17.0",
    }
    if any(
        versions.get(name) != version for name, version in required_versions.items()
    ):
        raise LinuxEnvironmentEvidenceError("critical Python package version mismatch")

    accelerator_record = _exact_mapping(
        accelerator,
        keys={
            "bf16_supported",
            "compute_capability",
            "cuda_available",
            "cuda_runtime",
            "cudnn_version",
            "device_count",
            "device_name",
            "driver_version",
            "memory_mib",
            "torch_version",
        },
        label="accelerator",
    )
    if accelerator_record["cuda_available"] is not True:
        raise LinuxEnvironmentEvidenceError("CUDA must be available")
    if accelerator_record["bf16_supported"] is not True:
        raise LinuxEnvironmentEvidenceError("BF16 must be supported")
    if accelerator_record["device_count"] != 1:
        raise LinuxEnvironmentEvidenceError("exactly one evaluator GPU is required")
    if accelerator_record["compute_capability"] != [8, 9]:
        raise LinuxEnvironmentEvidenceError("GPU compute capability mismatch")
    if accelerator_record["torch_version"] != "2.14.0+cu130":
        raise LinuxEnvironmentEvidenceError("Torch version differs from lock")
    if accelerator_record["cuda_runtime"] != "13.0":
        raise LinuxEnvironmentEvidenceError("CUDA runtime differs from lock")
    for numeric in ("cudnn_version", "memory_mib"):
        if (
            not isinstance(accelerator_record[numeric], int)
            or accelerator_record[numeric] < 1
        ):
            raise LinuxEnvironmentEvidenceError(f"accelerator {numeric} is invalid")
    for text in ("device_name", "driver_version"):
        if (
            not isinstance(accelerator_record[text], str)
            or not accelerator_record[text]
        ):
            raise LinuxEnvironmentEvidenceError(f"accelerator {text} is invalid")

    probe_record = _exact_mapping(
        bf16_probe,
        keys={
            "cudnn_benchmark",
            "cudnn_tf32",
            "deterministic_algorithms",
            "device",
            "dtype",
            "matmul_tf32",
            "values_fp32",
        },
        label="BF16 probe",
    )
    if probe_record != {
        "cudnn_benchmark": False,
        "cudnn_tf32": False,
        "deterministic_algorithms": True,
        "device": "cuda:0",
        "dtype": "torch.bfloat16",
        "matmul_tf32": False,
        "values_fp32": [[5.0, -4.5], [2.0, 15.0]],
    }:
        raise LinuxEnvironmentEvidenceError("BF16 probe result differs from contract")

    return {
        "accelerator": accelerator_record,
        "bf16_probe": probe_record,
        "dedicated_windows_principal_present": False,
        "distro": distro_record,
        "distro_packages": _package_inventory(distro_packages, label="distro package"),
        "experiment_id": EXPERIMENT_ID,
        "held_out_data_present": False,
        "immutable_rootfs_present": False,
        "lock": {
            "byte_length": len(lock_bytes),
            "manifest_sha256": hashlib.sha256(lock_manifest_bytes).hexdigest(),
            "relative_path": lock_relative_path,
            "sha256": hashlib.sha256(lock_bytes).hexdigest(),
        },
        "python": {
            **python_record,
            "dependency_check": True,
            "package_origins_under_prefix": True,
            "packages": python_inventory,
        },
        "resources": resource_record,
        "rootfs_manifest_present": False,
        "schema_id": (
            "https://aluclu.org/schemas/alc_r0/v1/"
            "linux-evaluator-bootstrap-receipt.schema.json"
        ),
        "schema_version": 1,
        "sealer_authority": False,
        "source_commit": source_commit,
        "status": "bootstrap-verified-non-authorizing",
        "training_authority": False,
        "uv": uv_record,
    }
