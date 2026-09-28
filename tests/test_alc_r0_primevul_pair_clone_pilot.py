from __future__ import annotations

from pathlib import Path

import pytest
from test_alc_r0_primevul_pairs_source import _paired_files
from test_alc_r0_primevul_source import _bytes, _files, _row

from aluclu.alc_r0.primevul_pair_clone_pilot import (
    PairClonePilotError,
    build_primevul_pair_clone_pilot,
)
from aluclu.alc_r0.primevul_pairs_source import PrimeVulPairExpectation
from aluclu.alc_r0.primevul_source import PrimeVulDevelopmentExpectation


def _fixture(
    tmp_path: Path,
) -> tuple[Path, Path, PrimeVulDevelopmentExpectation, PrimeVulPairExpectation]:
    full = tmp_path / "full"
    paired = tmp_path / "paired"
    full.mkdir()
    train = [
        _row(1, "red blue green yellow orange", 1),
        _row(2, "alpha beta gamma delta epsilon", 0),
        _row(3, "one two three four five", 1),
        _row(4, "six seven eight nine ten", 0),
    ]
    validation = [
        _row(5, "int valid_vulnerable;", 1),
        _row(6, "int valid_patched;", 0),
    ]
    source_expectation = _files(
        full, _bytes(train), _bytes(validation), train_positive=2, validation_positive=1
    )
    pair_expectation = _paired_files(paired, _bytes(train), _bytes(validation))
    return full, paired, source_expectation, pair_expectation


def test_first_n_pair_pilot_is_metadata_only_and_non_authorizing(
    tmp_path: Path,
) -> None:
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)

    receipt = build_primevul_pair_clone_pilot(
        full,
        paired,
        pair_count=2,
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
    )

    assert receipt["status"] == "development-reference-pilot-non-authorizing"
    assert receipt["input_pair_edges"] == 2
    assert receipt["input_unique_source_ids"] == 4
    assert receipt["retained_train_rows"] == 4
    assert receipt["full_corpus_graph_executed"] is False
    assert receipt["training_authority"] is False
    assert receipt["held_out_data_present"] is False
    assert len(receipt["selected_edge_ledger_sha256"]) == 64


@pytest.mark.parametrize("pair_count", [0, 3, 2049])
def test_pilot_count_bounds_fail_closed(tmp_path: Path, pair_count: int) -> None:
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)

    with pytest.raises(PairClonePilotError):
        build_primevul_pair_clone_pilot(
            full,
            paired,
            pair_count=pair_count,
            source_expectation=source_expectation,
            pair_expectation=pair_expectation,
        )
