from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from aluclu.alc_r0.canonical import canonical_json_bytes
from aluclu.alc_r0.devign_clone import minhash_signature
from aluclu.alc_r0.devign_preprocess import code_five_shingles, tokenize_devign_code
from aluclu.alc_r0.primevul_near_edge_audit import (
    NearEdgeAuditError,
    audit_near_edges,
    independent_minhash_signature,
)
from aluclu.alc_r0.primevul_pair_clone_graph import PairCloneRecord
from aluclu.alc_r0.primevul_pair_clone_scalable import build_pair_clone_scalable


def _fixture():
    original = [f"token{index}" for index in range(200)]
    changed = original.copy()
    changed[100] = "replaced"
    train = (
        PairCloneRecord("primevul:1", " ".join(original), 1),
        PairCloneRecord("primevul:2", " ".join(changed), 0),
        PairCloneRecord("primevul:3", " ".join(original), 1),
    )
    validation = (PairCloneRecord("primevul:4", "other words with no overlap", 0),)
    result = build_pair_clone_scalable(
        train=train, validation=validation, pair_edges=()
    )
    return train, validation, result


def test_independent_minhash_matches_frozen_reference_vector() -> None:
    shingles = code_five_shingles(
        tokenize_devign_code(" ".join(f"token{index}" for index in range(200)))
    )

    assert independent_minhash_signature(shingles) == minhash_signature(shingles)


def test_independent_minhash_matches_scalar_single_shingle_arithmetic() -> None:
    shingle = ("a", "b", "c", "d", "e")
    signature = independent_minhash_signature(frozenset((shingle,)))
    shingle_hash = int.from_bytes(
        hashlib.sha256(canonical_json_bytes(shingle)).digest()[:4], "big"
    )
    prefix = b"aluclu-devign-minhash-affine32-v1\0" + (20260916).to_bytes(8, "big")
    for index in (0, 1, 127, 255):
        coefficient = hashlib.sha256(prefix + index.to_bytes(4, "big")).digest()
        multiplier = int.from_bytes(coefficient[:4], "big") | 1
        offset = int.from_bytes(coefficient[4:8], "big")
        assert signature[index] == (shingle_hash * multiplier + offset) & 0xFFFFFFFF


def test_near_edge_audit_rediscovers_edge_and_skips_exact_duplicate() -> None:
    train, validation, result = _fixture()

    audit = audit_near_edges(train=train, validation=validation, result=result)

    assert audit["status"] == "near-edge-audit-clear-non-authorizing"
    assert audit["input_rows"] == 4
    assert audit["exact_duplicate_rows"] == 1
    assert audit["lsh_candidate_pairs"] == result.lsh_candidate_pairs
    assert audit["near_edges"] == result.near_joins == 1
    assert len(audit["near_edge_ledger_sha256"]) == 64
    assert audit["training_authority"] is False
    assert audit["held_out_data_present"] is False


def test_near_edge_audit_rejects_missing_near_component_join() -> None:
    train, validation, result = _fixture()
    roots = dict(result.root_by_id)
    roots["primevul:2"] = "primevul:2"

    with pytest.raises(NearEdgeAuditError, match="near edge crosses roots"):
        audit_near_edges(
            train=train,
            validation=validation,
            result=replace(result, root_by_id=roots),
        )


def test_near_edge_audit_rejects_wrong_candidate_count() -> None:
    train, validation, result = _fixture()

    with pytest.raises(NearEdgeAuditError, match="candidate count"):
        audit_near_edges(
            train=train,
            validation=validation,
            result=replace(result, lsh_candidate_pairs=result.lsh_candidate_pairs + 1),
        )


def test_near_edge_audit_rejects_wrong_near_count() -> None:
    train, validation, result = _fixture()

    with pytest.raises(NearEdgeAuditError, match="near-edge count"):
        audit_near_edges(
            train=train,
            validation=validation,
            result=replace(result, near_joins=result.near_joins + 1),
        )


def test_near_edge_audit_fails_closed_on_candidate_resource_bound() -> None:
    train, validation, result = _fixture()

    with pytest.raises(NearEdgeAuditError, match="candidate resource bound"):
        audit_near_edges(
            train=train, validation=validation, result=result, max_candidate_pairs=0
        )
