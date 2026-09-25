from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from aluclu.alc_r0.canonical import canonical_json_bytes, parse_canonical_json
from aluclu.alc_r0.claim_ledger import (
    ClaimLedgerError,
    build_claim_ledger_candidate,
    build_claim_ledger_candidate_from_tree,
    verify_claim_ledger_candidate,
)
from aluclu.alc_r0.schema_validation import validate_r0_document

SCHEMA_ROOT = Path(__file__).parents[1] / "schemas" / "alc_r0" / "v1"

_FIRST = "results/alc_r0/control/model-acquisition-receipt.json"
_SECOND = "results/alc_r0/control/base-digest-receipt.json"
_MEDIA = {
    _FIRST: ("application/json", "acquisition-receipt"),
    _SECOND: ("application/json", "base-digest-receipt"),
}
_EVIDENCE = {_FIRST: b'{"a":1}', _SECOND: b'{"b":2}'}


def test_candidate_ledger_is_canonical_sorted_and_digest_bound() -> None:
    ledger_bytes = build_claim_ledger_candidate(_EVIDENCE, expected_media=_MEDIA)
    ledger = parse_canonical_json(ledger_bytes)
    assert isinstance(ledger, dict)
    unsigned = dict(ledger)
    root_digest = unsigned.pop("root_digest")

    assert [entry["path"] for entry in ledger["files"]] == [_SECOND, _FIRST]
    assert ledger["training_authority"] is False
    assert ledger["status"] == "candidate-non-authorizing"
    assert ledger["claim"] is None
    assert root_digest == hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest()
    assert (
        validate_r0_document(
            ledger_bytes,
            schema_name="claim-ledger-candidate",
            schema_root=SCHEMA_ROOT,
        )
        == ledger
    )
    assert (
        verify_claim_ledger_candidate(ledger_bytes, _EVIDENCE, expected_media=_MEDIA)
        == ledger
    )


def test_missing_extra_or_wrong_media_entries_fail_closed() -> None:
    with pytest.raises(ClaimLedgerError):
        build_claim_ledger_candidate({_FIRST: _EVIDENCE[_FIRST]}, expected_media=_MEDIA)
    with pytest.raises(ClaimLedgerError):
        build_claim_ledger_candidate(
            {**_EVIDENCE, "results/alc_r0/control/orphan.json": b"{}"},
            expected_media=_MEDIA,
        )
    with pytest.raises(ClaimLedgerError):
        build_claim_ledger_candidate(
            _EVIDENCE,
            expected_media={**_MEDIA, _FIRST: ("text/plain", None)},
        )


@pytest.mark.parametrize(
    "illegal_path",
    [
        "results/alc_r0/final/claim-ledger.json",
        "results/alc_r0/final/completion.json",
        "results/alc_r0/control/../control/a.json",
        "results/alc_r0/control/A\\B.json",
        "C:/results/alc_r0/control/a.json",
    ],
)
def test_self_reference_completion_and_unsafe_paths_are_rejected(
    illegal_path: str,
) -> None:
    with pytest.raises(ClaimLedgerError):
        build_claim_ledger_candidate(
            {illegal_path: b"{}"},
            expected_media={illegal_path: ("application/json", None)},
        )


def test_casefold_collision_is_rejected() -> None:
    upper = "results/alc_r0/control/A.json"
    lower = "results/alc_r0/control/a.json"
    with pytest.raises(ClaimLedgerError):
        build_claim_ledger_candidate(
            {upper: b"{}", lower: b"{}"},
            expected_media={
                upper: ("application/json", None),
                lower: ("application/json", None),
            },
        )


def test_tamper_root_digest_entry_order_and_byte_length_are_rejected() -> None:
    ledger_bytes = build_claim_ledger_candidate(_EVIDENCE, expected_media=_MEDIA)
    with pytest.raises(ClaimLedgerError):
        verify_claim_ledger_candidate(
            ledger_bytes, {**_EVIDENCE, _FIRST: b'{"a":9}'}, expected_media=_MEDIA
        )

    ledger = parse_canonical_json(ledger_bytes)
    assert isinstance(ledger, dict)
    for mutation in (
        {**ledger, "root_digest": "0" * 64},
        {**ledger, "files": list(reversed(ledger["files"]))},
        {
            **ledger,
            "files": [{**ledger["files"][0], "byte_length": 999}, ledger["files"][1]],
        },
        {**ledger, "claim": "ALC-0 same-base retrieval-off neural capability"},
    ):
        with pytest.raises(ClaimLedgerError):
            verify_claim_ledger_candidate(
                canonical_json_bytes(mutation), _EVIDENCE, expected_media=_MEDIA
            )


def test_noncanonical_ledger_and_duplicate_file_entry_are_rejected() -> None:
    ledger_bytes = build_claim_ledger_candidate(_EVIDENCE, expected_media=_MEDIA)
    with pytest.raises(ClaimLedgerError):
        verify_claim_ledger_candidate(
            b" " + ledger_bytes, _EVIDENCE, expected_media=_MEDIA
        )
    ledger = parse_canonical_json(ledger_bytes)
    assert isinstance(ledger, dict)
    ledger["files"].append(ledger["files"][0])
    with pytest.raises(ClaimLedgerError):
        verify_claim_ledger_candidate(
            canonical_json_bytes(ledger), _EVIDENCE, expected_media=_MEDIA
        )


def test_filesystem_candidate_scan_rejects_orphan_missing_and_symlink(
    tmp_path: Path,
) -> None:
    control = tmp_path / "results" / "alc_r0" / "control"
    control.mkdir(parents=True)
    for path, payload in _EVIDENCE.items():
        (tmp_path / path).write_bytes(payload)

    candidate = build_claim_ledger_candidate_from_tree(tmp_path, expected_media=_MEDIA)
    assert candidate == build_claim_ledger_candidate(_EVIDENCE, expected_media=_MEDIA)

    orphan = control / "orphan.json"
    orphan.write_bytes(b"{}")
    with pytest.raises(ClaimLedgerError):
        build_claim_ledger_candidate_from_tree(tmp_path, expected_media=_MEDIA)
    orphan.unlink()

    (tmp_path / _FIRST).unlink()
    with pytest.raises(ClaimLedgerError):
        build_claim_ledger_candidate_from_tree(tmp_path, expected_media=_MEDIA)

    try:
        (tmp_path / _FIRST).symlink_to(tmp_path / _SECOND)
    except OSError:
        pytest.skip("Windows user cannot create symlinks")
    with pytest.raises(ClaimLedgerError):
        build_claim_ledger_candidate_from_tree(tmp_path, expected_media=_MEDIA)


def test_tree_scanner_streams_jsonl_logs_and_binary_without_changing_digests(
    tmp_path: Path,
) -> None:
    run = tmp_path / "results" / "alc_r0" / "dev" / "sample"
    run.mkdir(parents=True)
    files = {
        "results/alc_r0/dev/sample/events.jsonl": b'{"n":1}\n{"n":2}\n',
        "results/alc_r0/dev/sample/stdout.log": "çoklu parça".encode(),
        "results/alc_r0/dev/sample/learned-artifact.safetensors": b"\x00\xff" * 128,
    }
    media = {
        "results/alc_r0/dev/sample/events.jsonl": (
            "application/x-ndjson",
            None,
        ),
        "results/alc_r0/dev/sample/stdout.log": ("text/plain;charset=utf-8", None),
        "results/alc_r0/dev/sample/learned-artifact.safetensors": (
            "application/vnd.safetensors",
            None,
        ),
    }
    for relative, payload in files.items():
        (tmp_path / relative).write_bytes(payload)
    assert build_claim_ledger_candidate_from_tree(
        tmp_path, expected_media=media
    ) == build_claim_ledger_candidate(files, expected_media=media)

    (tmp_path / "results/alc_r0/dev/sample/events.jsonl").write_bytes(b'{"n":1}\r\n')
    with pytest.raises(ClaimLedgerError):
        build_claim_ledger_candidate_from_tree(tmp_path, expected_media=media)
    (tmp_path / "results/alc_r0/dev/sample/events.jsonl").write_bytes(
        files["results/alc_r0/dev/sample/events.jsonl"]
    )
    (tmp_path / "results/alc_r0/dev/sample/stdout.log").write_bytes(b"\xff")
    with pytest.raises(ClaimLedgerError):
        build_claim_ledger_candidate_from_tree(tmp_path, expected_media=media)
