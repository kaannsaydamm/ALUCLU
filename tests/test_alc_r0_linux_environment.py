from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, cast

import pytest

from aluclu.alc_r0.canonical import canonical_json_bytes
from aluclu.alc_r0.linux_environment import (
    LinuxEnvironmentEvidenceError,
    build_linux_evaluator_bootstrap_receipt,
)
from aluclu.alc_r0.schema_validation import (
    R0SchemaValidationError,
    validate_r0_document,
)
from scripts import capture_alc_r0_linux_environment

SCHEMA_ROOT = Path(__file__).parents[1] / "schemas" / "alc_r0" / "v1"
LOCK_PATH = "locks/alc_r0/v1/linux-eval.lock"


def _package_items() -> list[dict[str, str]]:
    return [
        {"name": "rfc8785", "version": "0.1.4"},
        {"name": "torch", "version": "2.14.0+cu130"},
        {"name": "transformers", "version": "5.17.0"},
    ]


def _distro_items() -> list[dict[str, str]]:
    return [
        {"name": "base-files", "version": "13ubuntu10.5"},
        {"name": "python3.12", "version": "3.12.3-1ubuntu0.16"},
    ]


def _build_receipt() -> dict[str, object]:
    lock_bytes = b"fully hashed linux lock\n"
    lock_manifest_bytes = canonical_json_bytes({"locks": ["linux-eval"]})
    python_packages = _package_items()
    distro_packages = _distro_items()
    return build_linux_evaluator_bootstrap_receipt(
        source_commit="a" * 40,
        distro={
            "filesystem_type": "ext4",
            "kernel_release": "6.18.33.2-microsoft-standard-WSL2",
            "machine": "x86_64",
            "name": "ALUCLU-R0-EVAL",
            "os_id": "ubuntu",
            "pretty_name": "Ubuntu 24.04.5 LTS",
            "version_id": "24.04",
            "wsl_version": 2,
        },
        resources={
            "cpu_model": "Example CPU",
            "filesystem_free_bytes": 30_000_000_000,
            "filesystem_total_bytes": 1_081_101_176_832,
            "logical_cpu_count": 16,
            "ram_total_bytes": 16_000_000_000,
            "swap_total_bytes": 4_000_000_000,
        },
        lock_relative_path=LOCK_PATH,
        lock_bytes=lock_bytes,
        lock_manifest_bytes=lock_manifest_bytes,
        uv={
            "executable_sha256": "1" * 64,
            "installer_sha256": "2" * 64,
            "version": "0.12.5",
        },
        python={
            "base_prefix": "/usr",
            "implementation": "CPython",
            "prefix": "/opt/aluclu-r0/linux-eval",
            "system_site_packages": False,
            "version": "3.12.3",
        },
        python_packages=python_packages,
        dependency_check=True,
        distro_packages=distro_packages,
        accelerator={
            "bf16_supported": True,
            "compute_capability": [8, 9],
            "cuda_available": True,
            "cuda_runtime": "13.0",
            "cudnn_version": 92400,
            "device_count": 1,
            "device_name": "NVIDIA GeForce RTX 4050 Laptop GPU",
            "driver_version": "610.78",
            "memory_mib": 6141,
            "torch_version": "2.14.0+cu130",
        },
        bf16_probe={
            "cudnn_benchmark": False,
            "cudnn_tf32": False,
            "deterministic_algorithms": True,
            "device": "cuda:0",
            "dtype": "torch.bfloat16",
            "matmul_tf32": False,
            "values_fp32": [[5.0, -4.5], [2.0, 15.0]],
        },
    )


def test_linux_bootstrap_receipt_is_closed_canonical_and_non_authorizing() -> None:
    receipt = _build_receipt()
    encoded = canonical_json_bytes(receipt)

    decoded = validate_r0_document(
        encoded,
        schema_name="linux-evaluator-bootstrap-receipt",
        schema_root=SCHEMA_ROOT,
    )

    assert decoded == receipt
    assert decoded["status"] == "bootstrap-verified-non-authorizing"
    assert decoded["training_authority"] is False
    assert decoded["sealer_authority"] is False
    assert decoded["held_out_data_present"] is False
    assert decoded["dedicated_windows_principal_present"] is False
    assert decoded["immutable_rootfs_present"] is False
    assert decoded["rootfs_manifest_present"] is False
    assert (
        decoded["lock"]["sha256"]
        == hashlib.sha256(  # type: ignore[index]
            b"fully hashed linux lock\n"
        ).hexdigest()
    )


def test_linux_bootstrap_receipt_binds_sorted_package_inventories() -> None:
    receipt = _build_receipt()

    python_record = cast(dict[str, Any], receipt["python"])
    python_inventory = cast(dict[str, Any], python_record["packages"])
    distro_inventory = cast(dict[str, Any], receipt["distro_packages"])
    assert python_inventory["count"] == 3
    assert distro_inventory["count"] == 2
    assert (
        python_inventory["sha256"]
        == hashlib.sha256(canonical_json_bytes(_package_items())).hexdigest()
    )
    assert (
        distro_inventory["sha256"]
        == hashlib.sha256(canonical_json_bytes(_distro_items())).hexdigest()
    )


@pytest.mark.parametrize(
    "field,value,match",
    [
        ("source_commit", "main", "source commit"),
        ("dependency_check", False, "dependency check"),
    ],
)
def test_linux_bootstrap_receipt_rejects_false_proof_inputs(
    field: str, value: object, match: str
) -> None:
    arguments = {
        "source_commit": "a" * 40,
        "distro": {
            "filesystem_type": "ext4",
            "kernel_release": "6.18.33.2-microsoft-standard-WSL2",
            "machine": "x86_64",
            "name": "ALUCLU-R0-EVAL",
            "os_id": "ubuntu",
            "pretty_name": "Ubuntu 24.04.5 LTS",
            "version_id": "24.04",
            "wsl_version": 2,
        },
        "resources": {
            "cpu_model": "Example CPU",
            "filesystem_free_bytes": 30_000_000_000,
            "filesystem_total_bytes": 1_081_101_176_832,
            "logical_cpu_count": 16,
            "ram_total_bytes": 16_000_000_000,
            "swap_total_bytes": 4_000_000_000,
        },
        "lock_relative_path": LOCK_PATH,
        "lock_bytes": b"lock",
        "lock_manifest_bytes": b"manifest",
        "uv": {
            "executable_sha256": "1" * 64,
            "installer_sha256": "2" * 64,
            "version": "0.12.5",
        },
        "python": {
            "base_prefix": "/usr",
            "implementation": "CPython",
            "prefix": "/opt/aluclu-r0/linux-eval",
            "system_site_packages": False,
            "version": "3.12.3",
        },
        "python_packages": _package_items(),
        "dependency_check": True,
        "distro_packages": _distro_items(),
        "accelerator": {
            "bf16_supported": True,
            "compute_capability": [8, 9],
            "cuda_available": True,
            "cuda_runtime": "13.0",
            "cudnn_version": 92400,
            "device_count": 1,
            "device_name": "NVIDIA GeForce RTX 4050 Laptop GPU",
            "driver_version": "610.78",
            "memory_mib": 6141,
            "torch_version": "2.14.0+cu130",
        },
        "bf16_probe": {
            "cudnn_benchmark": False,
            "cudnn_tf32": False,
            "deterministic_algorithms": True,
            "device": "cuda:0",
            "dtype": "torch.bfloat16",
            "matmul_tf32": False,
            "values_fp32": [[5.0, -4.5], [2.0, 15.0]],
        },
    }
    arguments[field] = value

    with pytest.raises(LinuxEnvironmentEvidenceError, match=match):
        build_linux_evaluator_bootstrap_receipt(**arguments)  # type: ignore[arg-type]


def test_linux_bootstrap_receipt_rejects_unsorted_or_duplicate_packages() -> None:
    arguments = _build_receipt()
    bad = list(reversed(_package_items()))

    with pytest.raises(LinuxEnvironmentEvidenceError, match="UTF-8 sorted"):
        build_linux_evaluator_bootstrap_receipt(
            source_commit=arguments["source_commit"],  # type: ignore[arg-type]
            distro=arguments["distro"],  # type: ignore[arg-type]
            resources=arguments["resources"],  # type: ignore[arg-type]
            lock_relative_path=LOCK_PATH,
            lock_bytes=b"lock",
            lock_manifest_bytes=b"manifest",
            uv=arguments["uv"],  # type: ignore[arg-type]
            python={
                key: value
                for key, value in arguments["python"].items()  # type: ignore[union-attr]
                if key
                not in {"dependency_check", "package_origins_under_prefix", "packages"}
            },
            python_packages=bad,
            dependency_check=True,
            distro_packages=_distro_items(),
            accelerator=arguments["accelerator"],  # type: ignore[arg-type]
            bf16_probe=arguments["bf16_probe"],  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda receipt: receipt.update({"training_authority": True}),
        lambda receipt: receipt.update({"sealer_authority": True}),
        lambda receipt: receipt.update({"immutable_rootfs_present": True}),
        lambda receipt: receipt["python"]["packages"].update(  # type: ignore[index]
            {"sha256": "0" * 64}
        ),
        lambda receipt: receipt["distro_packages"].update(  # type: ignore[union-attr]
            {"count": 999}
        ),
        lambda receipt: receipt.update({"unexpected": True}),
    ],
)
def test_linux_bootstrap_schema_rejects_authority_and_inventory_mutations(
    mutation,
) -> None:
    receipt = _build_receipt()
    mutation(receipt)

    with pytest.raises(R0SchemaValidationError):
        validate_r0_document(
            canonical_json_bytes(receipt),
            schema_name="linux-evaluator-bootstrap-receipt",
            schema_root=SCHEMA_ROOT,
        )


def test_dependency_check_uses_zero_exit_status_not_output_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, ...]] = []

    def successful_run(*arguments: str) -> str:
        calls.append(arguments)
        return ""

    monkeypatch.setattr(capture_alc_r0_linux_environment, "_run", successful_run)

    assert capture_alc_r0_linux_environment._dependency_check(Path("/opt/uv"))
    normalized_calls = [
        tuple(argument.replace("\\", "/") for argument in call) for call in calls
    ]
    assert normalized_calls == [
        (
            "/opt/uv",
            "pip",
            "check",
            "--python",
            "/opt/aluclu-r0/linux-eval/bin/python",
        )
    ]


def test_tracked_linux_bootstrap_receipt_is_exact_and_non_authorizing() -> None:
    receipt_path = (
        Path(__file__).parents[1]
        / "results"
        / "alc_r0"
        / "control"
        / "linux-evaluator-bootstrap-receipt.json"
    )
    encoded = receipt_path.read_bytes()
    decoded = validate_r0_document(
        encoded,
        schema_name="linux-evaluator-bootstrap-receipt",
        schema_root=SCHEMA_ROOT,
    )

    assert len(encoded) == 33_885
    assert hashlib.sha256(encoded).hexdigest() == (
        "f3eb83630369a7b71f08005ed69648eb0007143cbd911be45b5cb556cab1208a"
    )
    assert decoded["source_commit"] == ("ad5190d46889e2747698f3406073d0565208c286")
    assert decoded["python"]["packages"]["count"] == 68  # type: ignore[index]
    assert decoded["distro_packages"]["count"] == 523  # type: ignore[index]
    for authority_field in (
        "dedicated_windows_principal_present",
        "held_out_data_present",
        "immutable_rootfs_present",
        "rootfs_manifest_present",
        "sealer_authority",
        "training_authority",
    ):
        assert decoded[authority_field] is False
