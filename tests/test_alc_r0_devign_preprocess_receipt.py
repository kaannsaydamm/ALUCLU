from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("pyarrow")

from aluclu.alc_r0.canonical import canonical_json_bytes  # noqa: E402
from aluclu.alc_r0.devign_preprocess_receipt import (  # noqa: E402
    DevignPreprocessReceiptError,
    build_devign_preprocess_candidate_receipt,
)
from aluclu.alc_r0.devign_source import (  # noqa: E402
    DevignSourceRecord,
    VerifiedDevignDevelopment,
    load_verified_devign_development,
)

_REPO = Path(__file__).resolve().parents[1]
_CANDIDATE = _REPO / "results" / "alc_r0_devign_preprocess_candidate_20260925.json"


def _record(source_id: str, function: str) -> DevignSourceRecord:
    return DevignSourceRecord(source_id, function, False, "qemu", "a" * 40)


def _development(
    train: tuple[DevignSourceRecord, ...],
    validation: tuple[DevignSourceRecord, ...],
) -> VerifiedDevignDevelopment:
    return VerifiedDevignDevelopment(
        train,
        validation,
        {"training_authority": False, "receipt_version": 1},
    )


def test_receipt_is_ordered_and_contains_no_function_text() -> None:
    source = _development(
        (
            _record("devign:00000001", "int a=1;"),
            _record("devign:00000002", "int b=2;"),
        ),
        (_record("devign:00000003", "int c=3;"),),
    )
    reversed_source = _development(source.train[::-1], source.validation)

    receipt = build_devign_preprocess_candidate_receipt(source)
    reordered = build_devign_preprocess_candidate_receipt(reversed_source)

    assert receipt["training_authority"] is False
    assert receipt["held_out_data_present"] is False
    assert receipt["train_rows"] == 2
    assert receipt["validation_rows"] == 1
    assert (
        receipt["ordered_train_normalized_sha256"]
        != reordered["ordered_train_normalized_sha256"]
    )
    assert b"int a=1" not in canonical_json_bytes(receipt)


def test_code_mutation_changes_root_without_changing_source_ids() -> None:
    original = _development(
        (_record("devign:00000001", "int a=1;"),),
        (_record("devign:00000002", "int b=2;"),),
    )
    changed = _development(
        (_record("devign:00000001", "int a=4;"),), original.validation
    )

    a = build_devign_preprocess_candidate_receipt(original)
    b = build_devign_preprocess_candidate_receipt(changed)

    assert a["ordered_train_normalized_sha256"] != b["ordered_train_normalized_sha256"]
    assert (
        a["ordered_validation_normalized_sha256"]
        == b["ordered_validation_normalized_sha256"]
    )


def test_empty_split_or_authorizing_source_rejected() -> None:
    with pytest.raises(DevignPreprocessReceiptError, match="nonempty"):
        build_devign_preprocess_candidate_receipt(
            _development((_record("devign:00000001", "int a=1;"),), ())
        )
    source = _development(
        (_record("devign:00000001", "int a=1;"),),
        (_record("devign:00000002", "int b=2;"),),
    )
    source.receipt["training_authority"] = True
    with pytest.raises(DevignPreprocessReceiptError, match="not authorize"):
        build_devign_preprocess_candidate_receipt(source)


def test_pinned_real_development_receipt_when_supplied() -> None:
    source_raw = os.environ.get("ALUCLU_R0_DEVIGN_DEVELOPMENT")
    if not source_raw:
        pytest.skip("pinned Devign development source path not supplied")

    source = load_verified_devign_development(Path(source_raw))
    receipt = build_devign_preprocess_candidate_receipt(source)

    assert receipt["train_rows"] == 21854
    assert receipt["validation_rows"] == 2732
    assert receipt["train_empty_shingle_rows"] == 0
    assert receipt["validation_empty_shingle_rows"] == 0
    assert receipt["train_normalization_changed_rows"] == 20442
    assert receipt["validation_normalization_changed_rows"] == 2566
    assert receipt["ordered_train_normalized_sha256"] == (
        "f72efab00d173c14de86d0bccefb06423a23281a4fc9daabab4c807048474a14"
    )
    assert receipt["ordered_validation_normalized_sha256"] == (
        "37687d42fffdbbd6e0a1c31a33818902267c29bf7b1bc99a89edcbeaeea80c4f"
    )
    assert _CANDIDATE.read_bytes() == canonical_json_bytes(receipt) + b"\n"


def test_pinned_cli_reproduces_candidate_bytes_when_supplied() -> None:
    source_raw = os.environ.get("ALUCLU_R0_DEVIGN_DEVELOPMENT")
    if not source_raw:
        pytest.skip("pinned Devign development source path not supplied")

    result = subprocess.run(
        [sys.executable, "-m", "aluclu.alc_r0.devign_preprocess_receipt", source_raw],
        cwd=_REPO,
        capture_output=True,
        check=True,
    )

    assert result.stdout == _CANDIDATE.read_bytes()
