from __future__ import annotations

import pytest
from test_alc_r0_primevul_pair_clone_full import _fixture

from aluclu.alc_r0.primevul_pair_clone_full import run_primevul_full_graph
from aluclu.alc_r0.primevul_structural_audit_run import (
    PrimeVulStructuralAuditError,
    run_primevul_structural_audit,
)


class _ByteTokenizer:
    bos_token_id = None
    eos_token_id = None

    def encode(self, text: str, *, add_special_tokens: bool) -> list[int]:
        assert add_special_tokens is False
        return list(text.encode("utf-8"))


def test_full_fixture_receipt_is_bound_to_structural_audit(tmp_path) -> None:
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)
    receipt = run_primevul_full_graph(
        full,
        paired,
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
    )

    audit = run_primevul_structural_audit(
        full,
        paired,
        expected_receipt=receipt,
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
    )

    assert audit["status"] == "full-graph-structural-audit-clear-non-authorizing"
    assert audit["source_scope"] == "fixture"
    assert audit["input_rows"] == 4
    assert audit["retained_validation_rows"] == 2
    assert audit["training_authority"] is False
    assert audit["held_out_data_present"] is False


def test_full_fixture_can_redetect_near_edges_in_separate_pass(tmp_path) -> None:
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)
    receipt = run_primevul_full_graph(
        full,
        paired,
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
    )

    audit = run_primevul_structural_audit(
        full,
        paired,
        expected_receipt=receipt,
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
        include_near_edges=True,
    )

    assert (
        audit["status"]
        == "full-graph-structural-and-near-edge-audit-clear-non-authorizing"
    )
    assert (
        audit["near_edge_audit"]["lsh_candidate_pairs"]
        == receipt["lsh_candidate_pairs"]
    )
    assert audit["near_edge_audit"]["near_edges"] == receipt["near_joins"]
    assert audit["training_authority"] is False


def test_full_fixture_rejects_tampered_prior_receipt(tmp_path) -> None:
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)
    receipt = run_primevul_full_graph(
        full,
        paired,
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
    )
    receipt["component_root_ledger_sha256"] = "0" * 64

    with pytest.raises(PrimeVulStructuralAuditError, match="receipt mismatch"):
        run_primevul_structural_audit(
            full,
            paired,
            expected_receipt=receipt,
            source_expectation=source_expectation,
            pair_expectation=pair_expectation,
        )


def test_full_fixture_can_bind_retained_prompt_ids_without_raw_code(tmp_path) -> None:
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)
    receipt = run_primevul_full_graph(
        full,
        paired,
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
    )

    audit = run_primevul_structural_audit(
        full,
        paired,
        expected_receipt=receipt,
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
        prompt_tokenizer=_ByteTokenizer(),
        model_inventory_sha256="a" * 64,
    )

    prompt = audit["defect_prompt_audit"]
    assert prompt["train_rows"] == audit["retained_train_rows"]
    assert prompt["validation_rows"] == audit["retained_validation_rows"]
    assert prompt["training_authority"] is False
    assert prompt["model_inventory_sha256"] == "a" * 64
    assert "red blue" not in str(audit)


def test_prompt_options_must_be_supplied_as_one_bound_pair(tmp_path) -> None:
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)
    receipt = run_primevul_full_graph(
        full,
        paired,
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
    )

    with pytest.raises(PrimeVulStructuralAuditError, match="prompt"):
        run_primevul_structural_audit(
            full,
            paired,
            expected_receipt=receipt,
            source_expectation=source_expectation,
            pair_expectation=pair_expectation,
            prompt_tokenizer=_ByteTokenizer(),
        )
