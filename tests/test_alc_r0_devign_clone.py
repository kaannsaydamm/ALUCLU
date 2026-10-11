from __future__ import annotations

import hashlib
import struct

import pytest

from aluclu.alc_r0.devign_clone import (
    DevignCloneGroupError,
    _is_near_clone,
    audit_devign_exact_conflicts,
    filter_devign_development,
    minhash_signature,
)
from aluclu.alc_r0.devign_clone_receipt import build_devign_exact_conflict_receipt
from aluclu.alc_r0.devign_preprocess import code_five_shingles, tokenize_devign_code
from aluclu.alc_r0.devign_source import DevignSourceRecord, VerifiedDevignDevelopment


def _row(number: int, code: str, target: bool = False) -> DevignSourceRecord:
    return DevignSourceRecord(
        source_id=f"devign:{number:08d}",
        function=code,
        target=target,
        project="qemu",
        commit_id="0" * 40,
    )


def _source(
    train: tuple[DevignSourceRecord, ...],
    validation: tuple[DevignSourceRecord, ...],
) -> VerifiedDevignDevelopment:
    return VerifiedDevignDevelopment(
        train=train,
        validation=validation,
        receipt={"training_authority": False},
    )


def test_minhash_is_order_independent_and_has_256_values() -> None:
    shingles = code_five_shingles(tokenize_devign_code("int x = 1 ; return x ;"))

    signature = minhash_signature(shingles)

    assert len(signature) == 256
    assert signature == minhash_signature(frozenset(reversed(sorted(shingles))))
    assert signature != minhash_signature(
        code_five_shingles(tokenize_devign_code("int y = 2 ; return y ;"))
    )
    assert hashlib.sha256(struct.pack("!256I", *signature)).hexdigest() == (
        "fd37c3754762ed510e99dfa76672eca59306956a138234bc0f1f7fccb57ce1b1"
    )


def test_exact_and_token_whitespace_clones_collapse_and_train_excludes_validation() -> (
    None
):
    source = _source(
        (
            _row(2, "int x = 1; return x;"),
            _row(1, "int x = 1; return x;"),
            _row(3, "int   x=1;\nreturn x;"),
            _row(4, "int z = 4; return z;"),
        ),
        (
            _row(5, "int x=1; return x;"),
            _row(6, "int y = 2; return y;"),
            _row(7, "int y=2; return y;"),
        ),
    )

    result = filter_devign_development(source)

    assert tuple(row.source_id for row in result.train) == (
        "devign:00000001",
        "devign:00000004",
    )
    assert tuple(row.source_id for row in result.validation) == ("devign:00000006",)
    assert result.root_by_id["devign:00000005"] == "devign:00000001"
    assert result.validation_removed_train_overlap == 1


def test_conflicting_labels_in_exact_group_fail_closed() -> None:
    source = _source(
        (_row(1, "int x = 1;", False),),
        (_row(2, "int x = 1;", True),),
    )

    with pytest.raises(DevignCloneGroupError, match="conflicting labels"):
        filter_devign_development(source)
    audit = audit_devign_exact_conflicts(source)
    assert audit["exact_conflict_groups"] == 1
    assert audit["exact_conflict_members"] == 2
    assert audit["training_authority"] is False


def test_transitive_near_clone_group_uses_exact_jaccard_after_lsh() -> None:
    base = [f"v{index:03d}" for index in range(100)]
    middle = base.copy()
    middle[20] = "changed"
    last = middle.copy()
    last[70] = "changed_two"
    source = _source(
        (_row(3, " ".join(last)), _row(1, " ".join(base))),
        (_row(2, " ".join(middle)),),
    )

    result = filter_devign_development(source)

    assert result.root_by_id == {
        "devign:00000001": "devign:00000001",
        "devign:00000002": "devign:00000001",
        "devign:00000003": "devign:00000001",
    }
    assert tuple(row.source_id for row in result.train) == ("devign:00000001",)
    assert result.validation == ()
    assert result.near_joins >= 2


def test_exact_jaccard_accepts_the_boundary_and_rejects_below_it() -> None:
    shingles = frozenset((f"token{index}", "a", "b", "c", "d") for index in range(10))
    ordered = sorted(shingles)

    assert _is_near_clone(frozenset(ordered[:9]), shingles)
    assert not _is_near_clone(frozenset(ordered[:8]), shingles)


def test_authorizing_source_and_duplicate_ids_fail_closed() -> None:
    row = _row(1, "int x = 1;")
    with pytest.raises(DevignCloneGroupError, match="non-authorizing"):
        filter_devign_development(
            VerifiedDevignDevelopment((row,), (), {"training_authority": True})
        )
    with pytest.raises(DevignCloneGroupError, match="source IDs"):
        filter_devign_development(_source((row, row), ()))


def test_conflict_receipt_keeps_near_clone_and_test_access_unexecuted() -> None:
    source = _source(
        (_row(1, "int x = 1;", False),),
        (_row(2, "int x = 1;", True),),
    )

    receipt = build_devign_exact_conflict_receipt(source)

    assert receipt["audit"]["status"] == "failed-exact-label-conflicts"
    assert receipt["minhash_coefficient_sha256"] == (
        "08ed1ca23b267dc9f06267b318f2e95990c72c0f2b06480647afcd79aeaf9e42"
    )
    assert receipt["lsh_executed"] is False
    assert receipt["held_out_data_present"] is False
    assert receipt["training_authority"] is False
