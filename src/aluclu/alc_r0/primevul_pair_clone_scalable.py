"""Resource-bounded development graph, independently checked against the oracle.

This backend preserves the frozen clone rules while keeping only normalized
code, compact bucket indices, and a bounded shingle cache. It does not verify
source files, see held-out data, or authorize training on its own.
"""

from __future__ import annotations

import hashlib
import re
from array import array
from collections import OrderedDict
from collections.abc import Callable

from .devign_clone import _band_keys, _is_near_clone, minhash_signature
from .devign_preprocess import (
    code_five_shingles,
    normalize_devign_code,
    tokenize_devign_code,
)
from .primevul_pair_clone_graph import (
    PairCloneGraphError,
    PairCloneRecord,
    PairCloneReferenceResult,
)

_SOURCE_ID = re.compile(r"primevul:(?:0|[1-9][0-9]*)\Z")
_MAX_ROWS = 250_000
_MAX_CANDIDATE_PAIRS = 10_000_000
_SHINGLE_CACHE_ROWS = 512
_SHINGLE = tuple[str, ...]


def build_pair_clone_scalable(
    *,
    train: tuple[PairCloneRecord, ...],
    validation: tuple[PairCloneRecord, ...],
    pair_edges: tuple[tuple[str, str], ...],
    max_candidate_pairs: int = _MAX_CANDIDATE_PAIRS,
    progress: Callable[[int, int, int], None] | None = None,
) -> PairCloneReferenceResult:
    """Build the full-development dependency graph without retaining all shingles."""

    if not isinstance(train, tuple) or not isinstance(validation, tuple):
        raise PairCloneGraphError("tuple development splits required")
    if not isinstance(pair_edges, tuple):
        raise PairCloneGraphError("tuple pair edges required")
    if progress is not None and not callable(progress):
        raise PairCloneGraphError("progress callback must be callable")
    if (
        type(max_candidate_pairs) is not int
        or max_candidate_pairs < 0
        or max_candidate_pairs > _MAX_CANDIDATE_PAIRS
    ):
        raise PairCloneGraphError("invalid candidate resource bound")
    rows = train + validation
    if not rows or len(rows) > _MAX_ROWS:
        raise PairCloneGraphError(
            "development row count is empty or over resource bound"
        )
    ids: list[str] = []
    split_by_id: dict[str, str] = {}
    label_by_id: dict[str, int] = {}
    for split_name, split in (("train", train), ("validation", validation)):
        for row in split:
            if not isinstance(row, PairCloneRecord) or (
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

    parent = array("I", range(len(rows)))

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

    exact_first: dict[bytes, int] = {}
    normalized_by_index: list[str] = []
    hash_by_index: list[bytes] = []
    buckets: dict[bytes, array[int]] = {}
    shingle_cache: OrderedDict[int, frozenset[_SHINGLE]] = OrderedDict()

    def shingles_at(index: int) -> frozenset[_SHINGLE]:
        prior = shingle_cache.get(index)
        if prior is not None:
            shingle_cache.move_to_end(index)
            return prior
        result = code_five_shingles(tokenize_devign_code(normalized_by_index[index]))
        shingle_cache[index] = result
        if len(shingle_cache) > _SHINGLE_CACHE_ROWS:
            shingle_cache.popitem(last=False)
        return result

    exact_joins = 0
    candidate_pairs = 0
    near_joins = 0
    for index, row in enumerate(rows):
        normalized = normalize_devign_code(
            row.function.encode("utf-8", errors="strict")
        )
        digest = hashlib.sha256(normalized.encode("utf-8")).digest()
        normalized_by_index.append(normalized)
        hash_by_index.append(digest)
        earlier_exact = exact_first.setdefault(digest, index)
        if earlier_exact != index:
            if normalized_by_index[earlier_exact] != normalized:
                raise PairCloneGraphError("normalized SHA-256 collision")
            if rows[earlier_exact].target != row.target:
                raise PairCloneGraphError("conflicting exact normalized-code labels")
            union(index, earlier_exact)
            exact_joins += 1
            if progress is not None and (index % 1024 == 0 or index + 1 == len(rows)):
                progress(index + 1, len(rows), candidate_pairs)
            continue
        shingles = shingles_at(index)
        if not shingles:
            if progress is not None and (index % 1024 == 0 or index + 1 == len(rows)):
                progress(index + 1, len(rows), candidate_pairs)
            continue
        keys = tuple(
            bytes((band,)) + packed
            for band, packed in _band_keys(minhash_signature(shingles))
        )
        candidates = {earlier for key in keys for earlier in buckets.get(key, ())}
        for earlier in sorted(candidates):
            if hash_by_index[earlier] == digest:
                continue
            candidate_pairs += 1
            if candidate_pairs > max_candidate_pairs:
                raise PairCloneGraphError("candidate resource bound exceeded")
            if _is_near_clone(shingles, shingles_at(earlier)):
                union(index, earlier)
                near_joins += 1
        for key in keys:
            bucket = buckets.get(key)
            if bucket is None:
                buckets[key] = array("I", (index,))
            else:
                bucket.append(index)
        if progress is not None and (index % 1024 == 0 or index + 1 == len(rows)):
            progress(index + 1, len(rows), candidate_pairs)

    pair_joins = 0
    for left, right in pair_edges:
        pair_joins += union(index_by_id[left], index_by_id[right])
    root_by_id = {source_id: ids[find(index)] for index, source_id in enumerate(ids)}

    def representatives(indices: range | list[int]) -> tuple[PairCloneRecord, ...]:
        selected: dict[tuple[str, bytes, int], int] = {}
        for index in indices:
            key = (
                root_by_id[ids[index]],
                hash_by_index[index],
                rows[index].target,
            )
            previous = selected.get(key)
            if previous is None or ids[index] < ids[previous]:
                selected[key] = index
        return tuple(
            sorted(
                (rows[index] for index in selected.values()),
                key=lambda row: row.source_id,
            )
        )

    kept_train = representatives(range(len(train)))
    train_roots = {root_by_id[source_id] for source_id in ids[: len(train)]}
    overlap_roots = train_roots & {
        root_by_id[source_id] for source_id in ids[len(train) :]
    }
    safe_validation_indices = [
        index
        for index in range(len(train), len(rows))
        if root_by_id[ids[index]] not in overlap_roots
    ]
    kept_validation = representatives(safe_validation_indices)
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
        validation_removed_train_overlap=len(validation) - len(safe_validation_indices),
        validation_removed_roots=len(overlap_roots),
    )
