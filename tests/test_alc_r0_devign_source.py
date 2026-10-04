from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

pa = pytest.importorskip("pyarrow")
pq = pytest.importorskip("pyarrow.parquet")

from aluclu.alc_r0.canonical import canonical_json_bytes  # noqa: E402
from aluclu.alc_r0.devign_source import (  # noqa: E402
    DevignDevelopmentExpectation,
    DevignSourceError,
    load_verified_devign_development,
)

_REPO = Path(__file__).resolve().parents[1]
_CANDIDATE = _REPO / "results" / "alc_r0_devign_development_candidate_20260925.json"


def _write_split(path: Path, ids: list[int], *, bad_schema: bool = False) -> None:
    schema = pa.schema(
        [
            pa.field("id", pa.int64() if bad_schema else pa.int32()),
            pa.field("func", pa.string()),
            pa.field("target", pa.bool_()),
            pa.field("project", pa.string()),
            pa.field("commit_id", pa.string()),
        ]
    )
    table = pa.Table.from_pylist(
        [
            {
                "id": source_id,
                "func": f"int function_{source_id}(void) {{ return {source_id}; }}",
                "target": bool(source_id % 2),
                "project": "qemu",
                "commit_id": "a" * 40,
            }
            for source_id in ids
        ],
        schema=schema,
    )
    pq.write_table(table, path)


def _source(tmp_path: Path, *, bad_schema: bool = False) -> Path:
    _write_split(
        tmp_path / "train-00000-of-00001.parquet", [2, 4], bad_schema=bad_schema
    )
    _write_split(tmp_path / "validation-00000-of-00001.parquet", [1])
    return tmp_path


def _expectation(root: Path) -> DevignDevelopmentExpectation:
    train = (root / "train-00000-of-00001.parquet").read_bytes()
    validation = (root / "validation-00000-of-00001.parquet").read_bytes()
    return DevignDevelopmentExpectation(
        revision="69bd48c03223c2104342acd9a807caf61ac3efb8",
        train_sha256=hashlib.sha256(train).hexdigest(),
        train_byte_length=len(train),
        train_rows=2,
        validation_sha256=hashlib.sha256(validation).hexdigest(),
        validation_byte_length=len(validation),
        validation_rows=1,
    )


def test_verified_source_emits_non_authorizing_receipt_without_code_text(
    tmp_path: Path,
) -> None:
    root = _source(tmp_path)

    result = load_verified_devign_development(root, expectation=_expectation(root))

    assert len(result.train) == 2
    assert len(result.validation) == 1
    assert result.train[0].source_id == "devign:00000002"
    assert result.receipt["training_authority"] is False
    assert result.receipt["held_out_data_present"] is False
    assert b"function_2" not in canonical_json_bytes(result.receipt)


def test_test_split_or_extra_file_fails_closed(tmp_path: Path) -> None:
    root = _source(tmp_path)
    expected = _expectation(root)
    (root / "test-00000-of-00001.parquet").write_bytes(b"sealed")

    with pytest.raises(DevignSourceError, match="exactly train and validation"):
        load_verified_devign_development(root, expectation=expected)


def test_changed_bytes_fail_before_parquet_parse(tmp_path: Path) -> None:
    root = _source(tmp_path)
    expected = _expectation(root)
    path = root / "train-00000-of-00001.parquet"
    path.write_bytes(path.read_bytes() + b"changed")

    with pytest.raises(DevignSourceError, match="byte length"):
        load_verified_devign_development(root, expectation=expected)


def test_same_length_byte_mutation_fails_sha256(tmp_path: Path) -> None:
    root = _source(tmp_path)
    expected = _expectation(root)
    path = root / "train-00000-of-00001.parquet"
    damaged = bytearray(path.read_bytes())
    damaged[8] ^= 1
    path.write_bytes(damaged)

    with pytest.raises(DevignSourceError, match="SHA-256"):
        load_verified_devign_development(root, expectation=expected)


def test_wrong_schema_fails_even_when_bytes_match(tmp_path: Path) -> None:
    root = _source(tmp_path, bad_schema=True)

    with pytest.raises(DevignSourceError, match="schema"):
        load_verified_devign_development(root, expectation=_expectation(root))


def test_cross_split_source_id_collision_fails(tmp_path: Path) -> None:
    root = _source(tmp_path)
    _write_split(root / "validation-00000-of-00001.parquet", [2])

    with pytest.raises(DevignSourceError, match="source ID"):
        load_verified_devign_development(root, expectation=_expectation(root))


def test_null_field_fails_even_when_parquet_bytes_are_expected(tmp_path: Path) -> None:
    root = _source(tmp_path)
    table = pq.read_table(root / "validation-00000-of-00001.parquet")
    nullable = table.set_column(2, "target", pa.array([None], type=pa.bool_()))
    pq.write_table(nullable, root / "validation-00000-of-00001.parquet")

    with pytest.raises(DevignSourceError, match="null"):
        load_verified_devign_development(root, expectation=_expectation(root))


def test_pinned_real_development_source_when_supplied() -> None:
    source_raw = os.environ.get("ALUCLU_R0_DEVIGN_DEVELOPMENT")
    if not source_raw:
        pytest.skip("pinned Devign development source path not supplied")

    result = load_verified_devign_development(Path(source_raw))

    assert len(result.train) == 21854
    assert len(result.validation) == 2732
    assert result.receipt["train_sha256"] == (
        "e319c83e2e816a10aeeebe78668aa95b757b04e555700bf5f826766b0e80bb06"
    )
    assert result.receipt["validation_sha256"] == (
        "a17a76ed040d7f8657d1ff741f967b44704c008101ac958e2990ad468203cfa4"
    )
    assert _CANDIDATE.read_bytes() == canonical_json_bytes(result.receipt) + b"\n"


def test_pinned_cli_matches_candidate_bytes_when_supplied() -> None:
    source_raw = os.environ.get("ALUCLU_R0_DEVIGN_DEVELOPMENT")
    if not source_raw:
        pytest.skip("pinned Devign development source path not supplied")

    result = subprocess.run(
        [sys.executable, "-m", "aluclu.alc_r0.devign_source", source_raw],
        cwd=_REPO,
        capture_output=True,
        check=True,
    )

    assert result.stdout == _CANDIDATE.read_bytes()
