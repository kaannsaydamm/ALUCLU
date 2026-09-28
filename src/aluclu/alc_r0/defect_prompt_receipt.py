"""Metadata-only candidate roots for retained family-B development prompts.

The caller must first verify source bytes and audit the pair/clone graph. This
helper binds that graph's retained rows to one tokenizer and prompt candidate;
it never reads held-out files, emits raw source, or grants training authority.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from typing import Any

from .banking_scoring import CandidateTokenizer, candidate_token_map_root
from .canonical import canonical_json_bytes, sha256_bytes
from .defect_prompt import (
    DEFECT_LABELS,
    DefectPromptError,
    DefectPromptTemplate,
    prepare_defect_prompt,
)
from .primevul_pair_clone_graph import PairCloneRecord, PairCloneReferenceResult

_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_MAX_ROWS = 250_000


class DefectPromptReceiptError(ValueError):
    """Retained development graph or prompt evidence is invalid."""


def _ordered_prompt_root(
    rows: Sequence[PairCloneRecord],
    *,
    root_by_id: dict[str, str],
    template: DefectPromptTemplate,
) -> tuple[str, int, dict[str, int], int]:
    digest = hashlib.sha256()
    truncated = 0
    label_counts = {label: 0 for label in DEFECT_LABELS}
    max_original_code_tokens = 0
    previous_id: str | None = None
    for row in rows:
        if (
            not isinstance(row, PairCloneRecord)
            or not isinstance(row.source_id, str)
            or not isinstance(row.function, str)
            or type(row.target) is not int
            or row.target not in (0, 1)
            or row.source_id not in root_by_id
            or not isinstance(root_by_id[row.source_id], str)
            or not root_by_id[row.source_id]
            or (previous_id is not None and row.source_id <= previous_id)
        ):
            raise DefectPromptReceiptError("invalid ordered retained graph row")
        previous_id = row.source_id
        try:
            prompt = template.build(row.function.encode("utf-8", errors="strict"))
        except (UnicodeEncodeError, DefectPromptError) as exc:
            raise DefectPromptReceiptError("invalid retained code prompt") from exc
        label = "vulnerable" if row.target == 1 else "safe"
        label_counts[label] += 1
        truncated += prompt.original_code_tokens > prompt.retained_code_tokens
        max_original_code_tokens = max(
            max_original_code_tokens, prompt.original_code_tokens
        )
        digest.update(
            canonical_json_bytes(
                {
                    "source_id": row.source_id,
                    "component_root": root_by_id[row.source_id],
                    "target": row.target,
                    "normalized_code_sha256": sha256_bytes(
                        prompt.normalized_code.encode("utf-8")
                    ),
                    "prompt_ids": list(prompt.token_ids),
                    "original_code_tokens": prompt.original_code_tokens,
                    "retained_code_tokens": prompt.retained_code_tokens,
                }
            )
            + b"\n"
        )
    return digest.hexdigest(), truncated, label_counts, max_original_code_tokens


def build_defect_prompt_candidate_receipt(
    graph: PairCloneReferenceResult,
    tokenizer: CandidateTokenizer,
    *,
    model_inventory_sha256: str,
    max_tokens: int = 512,
) -> dict[str, Any]:
    """Commit ordered retained prompt IDs without emitting development text.

    `model_inventory_sha256` must be recomputed from the independently pinned
    snapshot receipt by the caller. Its syntax alone is not provenance proof.
    """

    if not isinstance(model_inventory_sha256, str) or not _HEX64.fullmatch(
        model_inventory_sha256
    ):
        raise DefectPromptReceiptError("model inventory SHA-256 is invalid")
    if (
        not isinstance(graph, PairCloneReferenceResult)
        or graph.training_authority is not False
        or graph.held_out_data_present is not False
        or not graph.train
        or not graph.validation
        or len(graph.train) + len(graph.validation) > _MAX_ROWS
        or not isinstance(graph.root_by_id, dict)
    ):
        raise DefectPromptReceiptError("non-authorizing retained graph required")
    train_ids = {row.source_id for row in graph.train}
    validation_ids = {row.source_id for row in graph.validation}
    if train_ids & validation_ids:
        raise DefectPromptReceiptError("retained source IDs overlap")
    try:
        train_roots = {graph.root_by_id[source_id] for source_id in train_ids}
        validation_roots = {graph.root_by_id[source_id] for source_id in validation_ids}
    except KeyError as exc:
        raise DefectPromptReceiptError("retained graph root is missing") from exc
    if train_roots & validation_roots:
        raise DefectPromptReceiptError("train/validation component roots overlap")
    try:
        template = prepare_defect_prompt(tokenizer, max_tokens=max_tokens)
    except DefectPromptError as exc:
        raise DefectPromptReceiptError("defect prompt template is invalid") from exc
    train_root, train_truncated, train_labels, train_max = _ordered_prompt_root(
        graph.train, root_by_id=graph.root_by_id, template=template
    )
    validation_root, validation_truncated, validation_labels, validation_max = (
        _ordered_prompt_root(
            graph.validation, root_by_id=graph.root_by_id, template=template
        )
    )
    return {
        "receipt_version": 1,
        "status": "candidate-non-authorizing",
        "training_authority": False,
        "held_out_data_present": False,
        "model_inventory_sha256": model_inventory_sha256,
        "ordered_labels_sha256": sha256_bytes(canonical_json_bytes(DEFECT_LABELS)),
        "candidate_token_map_sha256": candidate_token_map_root(
            tokenizer, DEFECT_LABELS
        ),
        "prefix_token_ids_sha256": sha256_bytes(
            canonical_json_bytes(template.prefix_ids)
        ),
        "suffix_token_ids_sha256": sha256_bytes(
            canonical_json_bytes(template.suffix_ids)
        ),
        "prefix_tokens": len(template.prefix_ids),
        "suffix_tokens": len(template.suffix_ids),
        "max_candidate_tokens": template.max_candidate_tokens,
        "code_budget": template.code_budget,
        "max_common_tokens": template.max_tokens,
        "tokenization_policy": "separate-prefix-code-suffix-no-specials",
        "truncation_policy": "code-head-ceil-tail-floor-token-ids",
        "train_rows": len(graph.train),
        "validation_rows": len(graph.validation),
        "train_labels": train_labels,
        "validation_labels": validation_labels,
        "train_truncated_rows": train_truncated,
        "validation_truncated_rows": validation_truncated,
        "train_max_original_code_tokens": train_max,
        "validation_max_original_code_tokens": validation_max,
        "ordered_train_prompt_ids_sha256": train_root,
        "ordered_validation_prompt_ids_sha256": validation_root,
    }
