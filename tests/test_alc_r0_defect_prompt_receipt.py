from __future__ import annotations

import copy
from dataclasses import replace

import pytest

from aluclu.alc_r0.defect_prompt_receipt import (
    DefectPromptReceiptError,
    build_defect_prompt_candidate_receipt,
)
from aluclu.alc_r0.primevul_pair_clone_graph import (
    PairCloneRecord,
    PairCloneReferenceResult,
)


class _ByteTokenizer:
    bos_token_id = None
    eos_token_id = None

    def encode(self, text: str, *, add_special_tokens: bool) -> list[int]:
        assert add_special_tokens is False
        return list(text.encode("utf-8"))


def _graph() -> PairCloneReferenceResult:
    return PairCloneReferenceResult(
        train=(
            PairCloneRecord("primevul:1", "int a() { return 0; }", 0),
            PairCloneRecord("primevul:2", "int b() { return 1; }", 1),
        ),
        validation=(PairCloneRecord("primevul:3", "int c() { return 2; }", 0),),
        root_by_id={
            "primevul:1": "primevul:1",
            "primevul:2": "primevul:1",
            "primevul:3": "primevul:3",
        },
        exact_joins=0,
        lsh_candidate_pairs=0,
        near_joins=0,
        pair_joins=1,
        train_components=1,
        validation_components=1,
        validation_removed_train_overlap=0,
        validation_removed_roots=0,
    )


def test_candidate_receipt_binds_ordered_retained_rows_and_tokenizer() -> None:
    receipt = build_defect_prompt_candidate_receipt(
        _graph(), _ByteTokenizer(), model_inventory_sha256="a" * 64
    )

    assert receipt["status"] == "candidate-non-authorizing"
    assert receipt["training_authority"] is False
    assert receipt["held_out_data_present"] is False
    assert receipt["train_rows"] == 2
    assert receipt["validation_rows"] == 1
    assert receipt["train_labels"] == {"safe": 1, "vulnerable": 1}
    assert receipt["validation_labels"] == {"safe": 1, "vulnerable": 0}
    assert receipt["model_inventory_sha256"] == "a" * 64
    assert (
        receipt["ordered_train_prompt_ids_sha256"]
        != (receipt["ordered_validation_prompt_ids_sha256"])
    )
    assert len(receipt["candidate_token_map_sha256"]) == 64
    assert "int a" not in str(receipt)
    assert "primevul:1" not in str(receipt)


def test_receipt_changes_when_function_label_order_root_or_tokenizer_changes() -> None:
    graph = _graph()
    baseline = build_defect_prompt_candidate_receipt(
        graph, _ByteTokenizer(), model_inventory_sha256="a" * 64
    )

    class _ShiftedTokenizer(_ByteTokenizer):
        def encode(self, text: str, *, add_special_tokens: bool) -> list[int]:
            return [
                item + 1
                for item in super().encode(text, add_special_tokens=add_special_tokens)
            ]

    changed_tokenizer = build_defect_prompt_candidate_receipt(
        graph, _ShiftedTokenizer(), model_inventory_sha256="a" * 64
    )
    changed_function = replace(
        graph,
        train=(
            PairCloneRecord("primevul:1", "int a() { return 3; }", 0),
            graph.train[1],
        ),
    )
    changed_label = replace(
        graph,
        train=(
            PairCloneRecord("primevul:1", graph.train[0].function, 1),
            graph.train[1],
        ),
    )
    changed_root = copy.deepcopy(graph)
    changed_root.root_by_id["primevul:2"] = "primevul:2"

    for variant in (changed_function, changed_label, changed_root):
        receipt = build_defect_prompt_candidate_receipt(
            variant, _ByteTokenizer(), model_inventory_sha256="a" * 64
        )
        assert (
            receipt["ordered_train_prompt_ids_sha256"]
            != (baseline["ordered_train_prompt_ids_sha256"])
        )
    assert (
        changed_tokenizer["ordered_train_prompt_ids_sha256"]
        != (baseline["ordered_train_prompt_ids_sha256"])
    )


@pytest.mark.parametrize("bad_digest", ["0" * 63, "G" * 64, "a" * 65])
def test_bad_model_inventory_digest_is_rejected(bad_digest: str) -> None:
    with pytest.raises(DefectPromptReceiptError, match="inventory"):
        build_defect_prompt_candidate_receipt(
            _graph(), _ByteTokenizer(), model_inventory_sha256=bad_digest
        )


def test_invalid_graph_or_cross_split_root_is_rejected() -> None:
    graph = _graph()
    graph.root_by_id["primevul:3"] = "primevul:1"
    with pytest.raises(DefectPromptReceiptError, match="overlap"):
        build_defect_prompt_candidate_receipt(
            graph, _ByteTokenizer(), model_inventory_sha256="a" * 64
        )

    with pytest.raises(DefectPromptReceiptError, match="graph"):
        build_defect_prompt_candidate_receipt(
            object(), _ByteTokenizer(), model_inventory_sha256="a" * 64
        )
