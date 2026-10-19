"""Development-only Devign near-clone grouping on verified train/validation.

The LSH is an approximate *candidate* generator. Every near-clone union is
confirmed with exact five-token-shingle Jaccard; no held-out test row is read.
"""

from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from fractions import Fraction

import numpy as np

from .canonical import canonical_json_bytes, sha256_bytes
from .devign_preprocess import (
    code_five_shingles,
    normalize_devign_code,
    tokenize_devign_code,
)
from .devign_source import DevignSourceRecord, VerifiedDevignDevelopment

MINHASH_SEED = 20260916
MINHASH_PERMUTATIONS = 256
LSH_CANDIDATE_THRESHOLD = 0.85
EXACT_JACCARD_THRESHOLD = 0.90
_JACCARD_FRACTION = Fraction(str(EXACT_JACCARD_THRESHOLD))
# Equal-weight false-positive/false-negative area minimization for 0.85 and
# 256 permutations yields 13 bands of 19 rows (247 values; 9 are unused).
LSH_BANDS = 13
LSH_ROWS = 19
_MASK32 = np.uint64(0xFFFFFFFF)
_SHINGLE = tuple[str, ...]


class DevignCloneGroupError(ValueError):
    """Development source or clone groups violate the frozen filter contract."""


@dataclass(frozen=True)
class DevignCloneResult:
    train: tuple[DevignSourceRecord, ...]
    validation: tuple[DevignSourceRecord, ...]
    root_by_id: dict[str, str]
    exact_joins: int
    lsh_candidate_pairs: int
    near_joins: int
    validation_removed_train_overlap: int


def _coefficients() -> tuple[np.ndarray, np.ndarray]:
    """Derive 256 odd affine multipliers and offsets from the fixed seed."""

    prefix = b"aluclu-devign-minhash-affine32-v1\0" + struct.pack("!Q", MINHASH_SEED)
    pairs = [
        hashlib.sha256(prefix + struct.pack("!I", index)).digest()
        for index in range(MINHASH_PERMUTATIONS)
    ]
    multipliers = np.fromiter(
        (int.from_bytes(pair[:4], "big") | 1 for pair in pairs),
        dtype=np.uint64,
        count=MINHASH_PERMUTATIONS,
    )
    offsets = np.fromiter(
        (int.from_bytes(pair[4:8], "big") for pair in pairs),
        dtype=np.uint64,
        count=MINHASH_PERMUTATIONS,
    )
    return multipliers, offsets


_MULTIPLIERS, _OFFSETS = _coefficients()


def minhash_signature(shingles: frozenset[_SHINGLE]) -> tuple[int, ...]:
    """Return 256 deterministic 32-bit minima for a five-token shingle set."""

    if not isinstance(shingles, frozenset) or any(
        not isinstance(shingle, tuple)
        or len(shingle) != 5
        or any(not isinstance(token, str) for token in shingle)
        for shingle in shingles
    ):
        raise DevignCloneGroupError("five-token shingle set required")
    if not shingles:
        return (0xFFFFFFFF,) * MINHASH_PERMUTATIONS
    # SHA-256 is the committed shingle hash; its first 32 big-endian bits feed
    # odd affine permutations modulo 2**32. Exact Jaccard never uses this hash.
    hashes = np.fromiter(
        (
            int.from_bytes(
                hashlib.sha256(canonical_json_bytes(shingle)).digest()[:4], "big"
            )
            for shingle in shingles
        ),
        dtype=np.uint64,
        count=len(shingles),
    )
    minima = np.full(MINHASH_PERMUTATIONS, 0xFFFFFFFF, dtype=np.uint64)
    for start in range(0, len(hashes), 256):
        chunk = hashes[start : start + 256]
        permuted = (chunk[:, None] * _MULTIPLIERS + _OFFSETS) & _MASK32
        minima = np.minimum(minima, permuted.min(axis=0))
    return tuple(int(value) for value in minima)


def _shingles(row: DevignSourceRecord) -> frozenset[_SHINGLE]:
    normalized = normalize_devign_code(row.function.encode("utf-8", errors="strict"))
    return code_five_shingles(tokenize_devign_code(normalized))


def _is_near_clone(left: frozenset[_SHINGLE], right: frozenset[_SHINGLE]) -> bool:
    if not left or not right:
        return False
    # Integer comparison avoids a platform-sensitive floating-point boundary.
    return _JACCARD_FRACTION.denominator * len(
        left & right
    ) >= _JACCARD_FRACTION.numerator * len(left | right)


def _band_keys(signature: tuple[int, ...]) -> tuple[tuple[int, bytes], ...]:
    return tuple(
        (
            band,
            struct.pack(
                f"!{LSH_ROWS}I",
                *signature[band * LSH_ROWS : (band + 1) * LSH_ROWS],
            ),
        )
        for band in range(LSH_BANDS)
    )


def audit_devign_exact_conflicts(
    source: VerifiedDevignDevelopment,
) -> dict[str, int | str | bool]:
    """Independent, exact normalized-code label audit before approximate LSH."""

    if (
        not isinstance(source, VerifiedDevignDevelopment)
        or source.receipt.get("training_authority") is not False
    ):
        raise DevignCloneGroupError(
            "non-authorizing verified development source required"
        )
    rows = source.train + source.validation
    ids = tuple(row.source_id for row in rows)
    if len(set(ids)) != len(ids):
        raise DevignCloneGroupError("source IDs must be unique across splits")
    groups: dict[str, list[int]] = {}
    for index, row in enumerate(rows):
        if type(row.target) is not bool:
            raise DevignCloneGroupError("source labels must be Boolean")
        normalized = normalize_devign_code(
            row.function.encode("utf-8", errors="strict")
        )
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        members = groups.setdefault(digest, [])
        if members and normalized != normalize_devign_code(
            rows[members[0]].function.encode("utf-8", errors="strict")
        ):
            raise DevignCloneGroupError("normalized SHA-256 collision")
        members.append(index)
    conflicts = [
        {
            "normalized_sha256": digest,
            "members": sorted((ids[index], rows[index].target) for index in members),
        }
        for digest, members in sorted(groups.items())
        if len({rows[index].target for index in members}) > 1
    ]
    return {
        "status": "failed-exact-label-conflicts"
        if conflicts
        else "exact-preflight-clear",
        "training_authority": False,
        "held_out_data_present": False,
        "source_receipt_sha256": sha256_bytes(canonical_json_bytes(source.receipt)),
        "source_rows": len(rows),
        "exact_normalized_groups": len(groups),
        "exact_duplicate_groups": sum(len(members) > 1 for members in groups.values()),
        "exact_conflict_groups": len(conflicts),
        "exact_conflict_members": sum(len(item["members"]) for item in conflicts),
        "conflict_ledger_sha256": sha256_bytes(canonical_json_bytes(conflicts)),
    }


def filter_devign_development(
    source: VerifiedDevignDevelopment,
) -> DevignCloneResult:
    """Group exact/near clones, then keep one root vote per development split."""

    if (
        not isinstance(source, VerifiedDevignDevelopment)
        or source.receipt.get("training_authority") is not False
    ):
        raise DevignCloneGroupError(
            "non-authorizing verified development source required"
        )
    preflight = audit_devign_exact_conflicts(source)
    if preflight["exact_conflict_groups"]:
        raise DevignCloneGroupError(
            f"conflicting labels in {preflight['exact_conflict_groups']} exact clone roots"
        )
    rows = source.train + source.validation
    ids = tuple(row.source_id for row in rows)
    if len(set(ids)) != len(ids):
        raise DevignCloneGroupError("source IDs must be unique across splits")
    if any(type(row.target) is not bool for row in rows):
        raise DevignCloneGroupError("source labels must be Boolean")

    parent = list(range(len(rows)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        a, b = find(left), find(right)
        if a != b:
            if ids[a] < ids[b]:
                parent[b] = a
            else:
                parent[a] = b

    exact_first: dict[str, int] = {}
    buckets: dict[tuple[int, bytes], list[int]] = {}
    candidate_pairs = 0
    exact_joins = 0
    near_joins = 0
    normalized_hashes: list[str] = []
    for index, row in enumerate(rows):
        normalized = normalize_devign_code(
            row.function.encode("utf-8", errors="strict")
        )
        normalized_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        normalized_hashes.append(normalized_hash)
        exact_match = exact_first.setdefault(normalized_hash, index)
        if exact_match != index:
            union(index, exact_match)
            exact_joins += 1

        shingles = code_five_shingles(tokenize_devign_code(normalized))
        if not shingles:
            continue
        keys = _band_keys(minhash_signature(shingles))
        candidates = {earlier for key in keys for earlier in buckets.get(key, ())}
        for earlier in sorted(candidates):
            if normalized_hashes[earlier] == normalized_hash:
                continue
            candidate_pairs += 1
            if _is_near_clone(shingles, _shingles(rows[earlier])):
                union(index, earlier)
                near_joins += 1
        for key in keys:
            buckets.setdefault(key, []).append(index)

    root_by_id = {source_id: ids[find(index)] for index, source_id in enumerate(ids)}
    labels: dict[str, bool] = {}
    for row in rows:
        root = root_by_id[row.source_id]
        previous = labels.setdefault(root, row.target)
        if previous != row.target:
            raise DevignCloneGroupError(f"conflicting labels in clone root {root}")

    def representatives(
        split: tuple[DevignSourceRecord, ...],
    ) -> dict[str, DevignSourceRecord]:
        result: dict[str, DevignSourceRecord] = {}
        for row in split:
            root = root_by_id[row.source_id]
            current = result.get(root)
            if current is None or row.source_id < current.source_id:
                result[root] = row
        return result

    train = representatives(source.train)
    validation = representatives(source.validation)
    overlapping = train.keys() & validation.keys()
    for root in overlapping:
        del validation[root]
    return DevignCloneResult(
        train=tuple(sorted(train.values(), key=lambda row: row.source_id)),
        validation=tuple(sorted(validation.values(), key=lambda row: row.source_id)),
        root_by_id=root_by_id,
        exact_joins=exact_joins,
        lsh_candidate_pairs=candidate_pairs,
        near_joins=near_joins,
        validation_removed_train_overlap=len(overlapping),
    )
