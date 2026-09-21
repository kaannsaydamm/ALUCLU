from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from aluclu.alc_r0.canonical import canonical_json_bytes, parse_canonical_json
from aluclu.alc_r0.schema_validation import (
    R0SchemaValidationError,
    validate_r0_document,
)

SCHEMA_ROOT = Path(__file__).parents[1] / "schemas" / "alc_r0" / "v1"


def _acquisition_receipt() -> dict[str, object]:
    files = [
        {
            "byte_length": 1519,
            "path": ".gitattributes",
            "sha256": "11ad7efa24975ee4b0c3c3a38ed18737f0658a5f75a0a96787b576a78a023361",
        },
        {
            "byte_length": 6340,
            "path": "README.md",
            "sha256": "d1ba68cae64a89b6b434b11526e6e2271ee5ffd2c914ec35ed515f9d84c6085c",
        },
        {
            "byte_length": 704,
            "path": "config.json",
            "sha256": "1d556eab73b69c7f11f64c557a2f9c6f440bd4c6b89bb2584a6b498c92603843",
        },
        {
            "byte_length": 111,
            "path": "generation_config.json",
            "sha256": "2056c988e990b0d13670f63f2f3b87b3b6d07edaf7a3416998ba27dab2d8a059",
        },
        {
            "byte_length": 466391,
            "path": "merges.txt",
            "sha256": "0b54e8aa4e53d5383e2e4bc635a56b43f9647f7b13832d5d9ecd8f82dac4f510",
        },
        {
            "byte_length": 269060552,
            "path": "model.safetensors",
            "sha256": "80521b40281d6ce74e35c9282c22539e75aa0ac8578892b2a59955ef78d55da1",
        },
        {
            "byte_length": 831,
            "path": "special_tokens_map.json",
            "sha256": "e786b595b9a23148bf1630df78d9037a048ea671e48bfd3549a1e3c233742bb3",
        },
        {
            "byte_length": 2104556,
            "path": "tokenizer.json",
            "sha256": "9ca9acddb6525a194ec8ac7a87f24fbba7232a9a15ffa1af0c1224fcd888e47c",
        },
        {
            "byte_length": 3658,
            "path": "tokenizer_config.json",
            "sha256": "4bb9af56a342753d39374f4016a16574cab299fe088e896f425ce3c433f61424",
        },
        {
            "byte_length": 800662,
            "path": "vocab.json",
            "sha256": "82b84012e3add4d01d12ba14442026e49b8cbbaead1f79ecf3d919784f82dc79",
        },
    ]
    return {
        "experiment_id": "alc-r0-smollm2-135m-v1",
        "files": files,
        "inventory_sha256": hashlib.sha256(canonical_json_bytes(files)).hexdigest(),
        "repository": "HuggingFaceTB/SmolLM2-135M",
        "revision": "93efa2f097d58c2a74874c7e644dbc9b0cee75a2",
        "safetensors_only": True,
        "schema_id": (
            "https://aluclu.org/schemas/alc_r0/v1/acquisition-receipt.schema.json"
        ),
        "schema_version": 1,
        "trust_remote_code": False,
    }


def _lock_manifest() -> dict[str, object]:
    return {
        "creation_source_commit": "a" * 40,
        "experiment_id": "alc-r0-smollm2-135m-v1",
        "locks": [
            {
                "byte_length": 10,
                "input_sha256": "1" * 64,
                "platform": "x86_64-pc-windows-msvc",
                "python_implementation": "CPython",
                "python_version": "3.12.13",
                "relative_path": "locks/alc_r0/v1/windows-training.lock",
                "role": "windows-training",
                "sha256": "2" * 64,
                "status": "generated",
            },
            {
                "byte_length": 11,
                "input_sha256": "3" * 64,
                "platform": "x86_64-manylinux_2_28",
                "python_implementation": "CPython",
                "python_version": "3.12",
                "relative_path": "locks/alc_r0/v1/linux-eval.lock",
                "role": "linux-eval",
                "sha256": "4" * 64,
                "status": "provisional-until-rootfs-reproduced",
            },
        ],
        "resolver": {"name": "uv", "version": "0.12.5"},
        "schema_id": "https://aluclu.org/schemas/alc_r0/v1/lock-manifest.schema.json",
        "schema_version": 1,
    }


@pytest.mark.parametrize(
    "schema_name,payload",
    [
        ("acquisition-receipt", _acquisition_receipt()),
        ("lock-manifest", _lock_manifest()),
    ],
)
def test_r0_schema_accepts_exact_canonical_documents(
    schema_name: str,
    payload: dict[str, object],
) -> None:
    decoded = validate_r0_document(
        canonical_json_bytes(payload),
        schema_name=schema_name,
        schema_root=SCHEMA_ROOT,
    )

    assert decoded == payload


def test_schema_sources_are_themselves_canonical_and_closed() -> None:
    for path in sorted(SCHEMA_ROOT.glob("*.schema.json")):
        encoded = path.read_bytes()
        assert encoded == canonical_json_bytes(parse_canonical_json(encoded))


def test_tracked_lock_manifest_passes_the_frozen_schema() -> None:
    manifest_path = (
        Path(__file__).parents[1] / "locks" / "alc_r0" / "v1" / "lock-manifest.json"
    )

    decoded = validate_r0_document(
        manifest_path.read_bytes(),
        schema_name="lock-manifest",
        schema_root=SCHEMA_ROOT,
    )

    assert [record["role"] for record in decoded["locks"]] == [
        "windows-training",
        "linux-eval",
    ]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda receipt: receipt.update({"unexpected": True}),
        lambda receipt: receipt.update({"trust_remote_code": True}),
        lambda receipt: receipt.update({"revision": "main"}),
        lambda receipt: receipt["files"].append(  # type: ignore[union-attr]
            {"byte_length": 1, "path": "CONFIG.json", "sha256": "5" * 64}
        ),
        lambda receipt: receipt.update({"inventory_sha256": "0" * 64}),
    ],
)
def test_acquisition_receipt_rejects_schema_and_semantic_violations(mutation) -> None:
    receipt = _acquisition_receipt()
    mutation(receipt)

    with pytest.raises(R0SchemaValidationError):
        validate_r0_document(
            canonical_json_bytes(receipt),
            schema_name="acquisition-receipt",
            schema_root=SCHEMA_ROOT,
        )


def test_lock_manifest_rejects_reordered_roles_or_unknown_fields() -> None:
    manifest = _lock_manifest()
    manifest["locks"] = list(reversed(manifest["locks"]))  # type: ignore[arg-type]
    with pytest.raises(R0SchemaValidationError):
        validate_r0_document(
            canonical_json_bytes(manifest),
            schema_name="lock-manifest",
            schema_root=SCHEMA_ROOT,
        )

    manifest = _lock_manifest()
    manifest["resolver"]["unknown"] = True  # type: ignore[index]
    with pytest.raises(R0SchemaValidationError):
        validate_r0_document(
            canonical_json_bytes(manifest),
            schema_name="lock-manifest",
            schema_root=SCHEMA_ROOT,
        )


def test_schema_validation_rejects_noncanonical_bytes_and_unknown_schema() -> None:
    with pytest.raises(R0SchemaValidationError):
        validate_r0_document(
            b'{"schema_version": 1}',
            schema_name="lock-manifest",
            schema_root=SCHEMA_ROOT,
        )
    with pytest.raises(R0SchemaValidationError, match="unknown schema"):
        validate_r0_document(
            b"{}",
            schema_name="not-declared",
            schema_root=SCHEMA_ROOT,
        )


def test_schema_root_must_be_absolute_and_symlink_free(tmp_path: Path) -> None:
    with pytest.raises(R0SchemaValidationError, match="absolute"):
        validate_r0_document(
            canonical_json_bytes(_lock_manifest()),
            schema_name="lock-manifest",
            schema_root=Path("schemas/alc_r0/v1"),
        )

    link = tmp_path / "schemas-link"
    try:
        link.symlink_to(SCHEMA_ROOT, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlink creation is unavailable for this Windows token")
    with pytest.raises(R0SchemaValidationError, match="symlink"):
        validate_r0_document(
            canonical_json_bytes(_lock_manifest()),
            schema_name="lock-manifest",
            schema_root=link,
        )


def test_schema_loader_rejects_remote_references_before_resolution(
    tmp_path: Path,
) -> None:
    schema_root = tmp_path / "schemas"
    schema_root.mkdir()
    (schema_root / "lock-manifest.schema.json").write_bytes(
        canonical_json_bytes(
            {
                "$id": "https://aluclu.org/schemas/alc_r0/v1/lock-manifest.schema.json",
                "$ref": "https://attacker.invalid/schema.json",
                "$schema": "https://json-schema.org/draft/2020-12/schema",
            }
        )
    )

    with pytest.raises(R0SchemaValidationError, match="nonlocal"):
        validate_r0_document(
            canonical_json_bytes(_lock_manifest()),
            schema_name="lock-manifest",
            schema_root=schema_root.resolve(),
        )
