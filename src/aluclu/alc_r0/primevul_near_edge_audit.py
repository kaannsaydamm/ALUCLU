"""Independent LSH/near-edge discovery over a non-authorizing PrimeVul graph.

This implementation shares the frozen normalization/tokenization contract but
does not call the graph builder's MinHash, band, candidate, Jaccard, or union
functions. Passing it cannot establish source rights or training authority.
"""

from __future__ import annotations

import hashlib
import struct
from array import array
from collections import OrderedDict
from collections.abc import Callable
from typing import Any

import numpy as np

from .canonical import canonical_json_bytes
from .devign_preprocess import (
    code_five_shingles,
    normalize_devign_code,
    tokenize_devign_code,
)
from .primevul_pair_clone_graph import PairCloneRecord, PairCloneReferenceResult

_SEED = 20260916
_PERMUTATIONS = 256
_BANDS = 13
_ROWS_PER_BAND = 19
_MAX_ROWS = 250_000
_MAX_CANDIDATES = 10_000_000
_SHINGLE_CACHE_ROWS = 512
_MASK32 = np.uint64(0xFFFFFFFF)
_SHINGLE = tuple[str, ...]


class NearEdgeAuditError(ValueError):
    """The graph omitted a discoverable near edge or misstated its counts."""


def _affine_coefficients() -> tuple[np.ndarray, np.ndarray]:
    prefix = b"aluclu-devign-minhash-affine32-v1\0" + _SEED.to_bytes(8, "big")
    multipliers: list[int] = []
    offsets: list[int] = []
    for index in range(_PERMUTATIONS):
        digest = hashlib.sha256(prefix + index.to_bytes(4, "big")).digest()
        multipliers.append(int.from_bytes(digest[:4], "big") | 1)
        offsets.append(int.from_bytes(digest[4:8], "big"))
    return np.asarray(multipliers, dtype=np.uint64), np.asarray(
        offsets, dtype=np.uint64
    )


_MULTIPLIERS, _OFFSETS = _affine_coefficients()


def independent_minhash_signature(
    shingles: frozenset[_SHINGLE],
) -> tuple[int, ...]:
    """Recompute the frozen 256-permutation signature without graph helpers."""

    if not isinstance(shingles, frozenset) or any(
        not isinstance(shingle, tuple)
        or len(shingle) != 5
        or any(not isinstance(token, str) for token in shingle)
        for shingle in shingles
    ):
        raise NearEdgeAuditError("five-token shingle set required")
    if not shingles:
        return (0xFFFFFFFF,) * _PERMUTATIONS
    hashes = np.asarray(
        [
            int.from_bytes(
                hashlib.sha256(canonical_json_bytes(shingle)).digest()[:4], "big"
            )
            for shingle in shingles
        ],
        dtype=np.uint64,
    )
    minima = np.full(_PERMUTATIONS, 0xFFFFFFFF, dtype=np.uint64)
    for start in range(0, len(hashes), 256):
        batch = hashes[start : start + 256]
        transformed = (batch[:, None] * _MULTIPLIERS + _OFFSETS) & _MASK32
        minima = np.minimum(minima, np.min(transformed, axis=0))
    return tuple(int(value) for value in minima)


def _band_keys(signature: tuple[int, ...]) -> tuple[bytes, ...]:
    return tuple(
        struct.pack(
            "!B19I",
            band,
            *signature[band * _ROWS_PER_BAND : (band + 1) * _ROWS_PER_BAND],
        )
        for band in range(_BANDS)
    )


def audit_near_edges(
    *,
    train: tuple[PairCloneRecord, ...],
    validation: tuple[PairCloneRecord, ...],
    result: PairCloneReferenceResult,
    max_candidate_pairs: int = _MAX_CANDIDATES,
    progress: Callable[[int, int, int], None] | None = None,
) -> dict[str, Any]:
    """Rediscover every frozen-LSH candidate/near edge and check graph roots."""

    if (
        not isinstance(train, tuple)
        or not isinstance(validation, tuple)
        or not isinstance(result, PairCloneReferenceResult)
        or result.training_authority is not False
        or result.held_out_data_present is not False
        or type(max_candidate_pairs) is not int
        or not 0 <= max_candidate_pairs <= _MAX_CANDIDATES
        or (progress is not None and not callable(progress))
    ):
        raise NearEdgeAuditError("invalid non-authorizing audit input")
    rows = train + validation
    if not rows or len(rows) > _MAX_ROWS:
        raise NearEdgeAuditError("development row resource bound exceeded")
    ids = [row.source_id for row in rows]
    if len(set(ids)) != len(rows) or set(result.root_by_id) != set(ids):
        raise NearEdgeAuditError("root ledger does not cover unique source IDs")

    normalized_by_index: list[str] = []
    digests: list[bytes] = []
    exact_first: dict[bytes, int] = {}
    buckets: dict[bytes, array[int]] = {}
    shingle_cache: OrderedDict[int, frozenset[_SHINGLE]] = OrderedDict()

    def shingles_at(index: int) -> frozenset[_SHINGLE]:
        cached = shingle_cache.get(index)
        if cached is not None:
            shingle_cache.move_to_end(index)
            return cached
        shingles = code_five_shingles(tokenize_devign_code(normalized_by_index[index]))
        shingle_cache[index] = shingles
        if len(shingle_cache) > _SHINGLE_CACHE_ROWS:
            shingle_cache.popitem(last=False)
        return shingles

    candidates_checked = 0
    near_edges = 0
    exact_duplicates = 0
    near_ledger = hashlib.sha256(b"ALC-R0-NEAR-EDGE-AUDIT-v1\0")
    for index, row in enumerate(rows):
        normalized = normalize_devign_code(row.function.encode("utf-8", "strict"))
        digest = hashlib.sha256(normalized.encode("utf-8")).digest()
        normalized_by_index.append(normalized)
        digests.append(digest)
        first = exact_first.setdefault(digest, index)
        if first != index:
            if normalized_by_index[first] != normalized:
                raise NearEdgeAuditError("normalized-code SHA-256 collision")
            if rows[first].target != row.target:
                raise NearEdgeAuditError("conflicting exact normalized-code labels")
            if result.root_by_id[ids[first]] != result.root_by_id[row.source_id]:
                raise NearEdgeAuditError("exact duplicate crosses roots")
            exact_duplicates += 1
        else:
            shingles = shingles_at(index)
            if shingles:
                keys = _band_keys(independent_minhash_signature(shingles))
                candidates = sorted(
                    {earlier for key in keys for earlier in buckets.get(key, ())}
                )
                for earlier in candidates:
                    if digests[earlier] == digest:
                        continue
                    candidates_checked += 1
                    if candidates_checked > max_candidate_pairs:
                        raise NearEdgeAuditError("candidate resource bound exceeded")
                    other = shingles_at(earlier)
                    intersection = len(shingles & other)
                    union = len(shingles) + len(other) - intersection
                    if 10 * intersection >= 9 * union:
                        near_edges += 1
                        if (
                            result.root_by_id[ids[earlier]]
                            != result.root_by_id[row.source_id]
                        ):
                            raise NearEdgeAuditError("near edge crosses roots")
                        near_ledger.update(
                            canonical_json_bytes([ids[earlier], row.source_id]) + b"\n"
                        )
                for key in keys:
                    bucket = buckets.get(key)
                    if bucket is None:
                        buckets[key] = array("I", (index,))
                    else:
                        bucket.append(index)
        if progress is not None and (index % 1024 == 0 or index + 1 == len(rows)):
            progress(index + 1, len(rows), candidates_checked)

    if candidates_checked != result.lsh_candidate_pairs:
        raise NearEdgeAuditError("candidate count disagrees with graph")
    if near_edges != result.near_joins:
        raise NearEdgeAuditError("near-edge count disagrees with graph")
    return {
        "status": "near-edge-audit-clear-non-authorizing",
        "training_authority": False,
        "held_out_data_present": False,
        "input_rows": len(rows),
        "exact_duplicate_rows": exact_duplicates,
        "lsh_candidate_pairs": candidates_checked,
        "near_edges": near_edges,
        "near_edge_ledger_sha256": near_ledger.hexdigest(),
    }
