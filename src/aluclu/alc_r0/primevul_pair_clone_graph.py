"""Small, non-authorizing pair-plus-near-clone dependency graph reference.

This is a correctness oracle for bounded synthetic/development fixtures. It
does not validate raw source bytes, access test data, or authorize training.
Full-corpus execution needs a separately validated resource-bounded backend.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from .devign_clone import _band_keys, _is_near_clone, minhash_signature
from .devign_preprocess import (
    code_five_shingles,
    normalize_devign_code,
    tokenize_devign_code,
)

_SOURCE_ID = re.compile(r"primevul:(?:0|[1-9][0-9]*)\Z")
_MAX_REFERENCE_ROWS = 4096
_SHINGLE = tuple[str, ...]


class PairCloneGraphError(ValueError):
    """The development reference graph has an invalid or unsafe input."""


@dataclass(frozen=True)
class PairCloneRecord:
    source_id: str
    function: str
    target: int


@dataclass(frozen=True)
class PairCloneReferenceResult:
    train: tuple[PairCloneRecord, ...]
    validation: tuple[PairCloneRecord, ...]
    root_by_id: dict[str, str]
    exact_joins: int
    lsh_candidate_pairs: int
    near_joins: int
    pair_joins: int
    train_components: int
    validation_components: int
    validation_removed_train_overlap: int
    validation_removed_roots: int
    training_authority: bool = False
    held_out_data_present: bool = False


def _normalized_and_shingles(
    record: PairCloneRecord,
) -> tuple[str, frozenset[_SHINGLE]]:
    normalized = normalize_devign_code(record.function.encode("utf-8", errors="strict"))
    return normalized, code_five_shingles(tokenize_devign_code(normalized))


def build_pair_clone_reference(
    *,
    train: tuple[PairCloneRecord, ...],
    validation: tuple[PairCloneRecord, ...],
    pair_edges: tuple[tuple[str, str], ...],
) -> PairCloneReferenceResult:
    """Group exact/near clones and explicit pairs; retain dependent labels."""

    if not isinstance(train, tuple) or not isinstance(validation, tuple):
        raise PairCloneGraphError("tuple development splits required")
    if not isinstance(pair_edges, tuple):
        raise PairCloneGraphError("tuple pair edges required")
    rows = train + validation
    if not rows or len(rows) > _MAX_REFERENCE_ROWS:
        raise PairCloneGraphError("reference row count is empty or over resource bound")
    ids: list[str] = []
    split_by_id: dict[str, str] = {}
    label_by_id: dict[str, int] = {}
    for split_name, split in (("train", train), ("validation", validation)):
        for row in split:
            if not isinstance(row, PairCloneRecord):
                raise PairCloneGraphError("PairCloneRecord required")
            if (
                not isinstance(row.source_id, str)
                or not _SOURCE_ID.fullmatch(row.source_id)
                or not isinstance(row.function, str)
                or not row.function.strip()
                or type(row.target) is not int
                or row.target not in (0, 1)
            ):
                raise PairCloneGraphError("invalid pair/clone source record")
            if row.source_id in split_by_id:
                raise PairCloneGraphError("source IDs must be unique across splits")
            ids.append(row.source_id)
            split_by_id[row.source_id] = split_name
            label_by_id[row.source_id] = row.target
    index_by_id = {source_id: index for index, source_id in enumerate(ids)}
    seen_edges: set[tuple[str, str]] = set()
    for edge in pair_edges:
        if not isinstance(edge, tuple) or len(edge) != 2:
            raise PairCloneGraphError("pair edge must have two source IDs")
        left, right = edge
        if left not in index_by_id or right not in index_by_id:
            raise PairCloneGraphError("unknown source ID in pair edge")
        if left == right or edge in seen_edges:
            raise PairCloneGraphError("duplicate or self pair edge")
        if split_by_id[left] != split_by_id[right]:
            raise PairCloneGraphError("pair edge crosses development splits")
        if label_by_id[left] != 1 or label_by_id[right] != 0:
            raise PairCloneGraphError("pair edge requires ordered opposite labels")
        seen_edges.add(edge)

    parent = list(range(len(rows)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> bool:
        a, b = find(left), find(right)
        if a == b:
            return False
        if ids[a] < ids[b]:
            parent[b] = a
        else:
            parent[a] = b
        return True

    exact_first: dict[str, int] = {}
    normalized_hashes: list[str] = []
    buckets: dict[tuple[int, bytes], list[int]] = {}
    exact_joins = 0
    candidate_pairs = 0
    near_joins = 0
    for index, row in enumerate(rows):
        normalized, shingles = _normalized_and_shingles(row)
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        normalized_hashes.append(digest)
        earlier_exact = exact_first.setdefault(digest, index)
        if earlier_exact != index:
            earlier_normalized, _ = _normalized_and_shingles(rows[earlier_exact])
            if earlier_normalized != normalized:
                raise PairCloneGraphError("normalized SHA-256 collision")
            if rows[earlier_exact].target != row.target:
                raise PairCloneGraphError("conflicting exact normalized-code labels")
            union(index, earlier_exact)
            exact_joins += 1
            continue
        if not shingles:
            continue
        keys = _band_keys(minhash_signature(shingles))
        candidates = {earlier for key in keys for earlier in buckets.get(key, ())}
        for earlier in sorted(candidates):
            if normalized_hashes[earlier] == digest:
                continue
            candidate_pairs += 1
            _, earlier_shingles = _normalized_and_shingles(rows[earlier])
            if _is_near_clone(shingles, earlier_shingles):
                union(index, earlier)
                near_joins += 1
        for key in keys:
            buckets.setdefault(key, []).append(index)

    pair_joins = 0
    for left, right in pair_edges:
        pair_joins += union(index_by_id[left], index_by_id[right])
    root_by_id = {source_id: ids[find(index)] for index, source_id in enumerate(ids)}

    def representatives(
        split: tuple[PairCloneRecord, ...],
    ) -> tuple[PairCloneRecord, ...]:
        retained: dict[tuple[str, str, int], PairCloneRecord] = {}
        for row in split:
            normalized, _ = _normalized_and_shingles(row)
            digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            key = (root_by_id[row.source_id], digest, row.target)
            prior = retained.get(key)
            if prior is None or row.source_id < prior.source_id:
                retained[key] = row
        return tuple(sorted(retained.values(), key=lambda item: item.source_id))

    kept_train = representatives(train)
    train_roots = {root_by_id[row.source_id] for row in train}
    overlap_roots = train_roots & {root_by_id[row.source_id] for row in validation}
    safe_validation = tuple(
        row for row in validation if root_by_id[row.source_id] not in overlap_roots
    )
    kept_validation = representatives(safe_validation)
    return PairCloneReferenceResult(
        train=kept_train,
        validation=kept_validation,
        root_by_id=root_by_id,
        exact_joins=exact_joins,
        lsh_candidate_pairs=candidate_pairs,
        near_joins=near_joins,
        pair_joins=pair_joins,
        train_components=len(train_roots),
        validation_components=len(
            {root_by_id[row.source_id] for row in kept_validation}
        ),
        validation_removed_train_overlap=len(validation) - len(safe_validation),
        validation_removed_roots=len(overlap_roots),
    )
