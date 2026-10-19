from __future__ import annotations

from pathlib import Path

import pytest
from test_alc_r0_primevul_pairs_source import _paired_files
from test_alc_r0_primevul_source import _bytes, _files, _row

from aluclu.alc_r0.primevul_pair_clone_full import run_primevul_full_graph
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
    ]
    validation = [
        _row(3, "one two three four five", 1),
        _row(4, "six seven eight nine ten", 0),
    ]
    source_expectation = _files(
        full, _bytes(train), _bytes(validation), train_positive=1, validation_positive=1
    )
    pair_expectation = _paired_files(paired, _bytes(train), _bytes(validation))
    return full, paired, source_expectation, pair_expectation


def test_full_runner_verifies_sources_and_emits_metadata_only_fixture_receipt(
    tmp_path: Path,
) -> None:
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)
    progress: list[tuple[int, int, int]] = []

    receipt = run_primevul_full_graph(
        full,
        paired,
        source_expectation=source_expectation,
        pair_expectation=pair_expectation,
        progress=lambda *values: progress.append(values),
    )

    assert receipt["status"] == "development-graph-non-authorizing"
    assert receipt["source_scope"] == "fixture"
    assert receipt["full_corpus_graph_executed"] is False
    assert receipt["input_train_rows"] == 2
    assert receipt["input_validation_rows"] == 2
    assert receipt["input_pair_edges"] == 2
    assert receipt["retained_train_rows"] == 2
    assert receipt["retained_validation_rows"] == 2
    assert receipt["validation_components"] == 1
    assert receipt["validation_components_positive"] == 1
    assert receipt["validation_components_negative"] == 1
    assert receipt["training_authority"] is False
    assert receipt["held_out_data_present"] is False
    assert progress[-1][:2] == (4, 4)
    assert "func" not in str(receipt)


def test_full_runner_rejects_mutated_paired_source(tmp_path: Path) -> None:
    full, paired, source_expectation, pair_expectation = _fixture(tmp_path)
    pair_path = paired / "primevul_train_paired.jsonl"
    data = pair_path.read_bytes()
    pair_path.write_bytes(data.replace(b"red", b"RED", 1))

    with pytest.raises(ValueError):
        run_primevul_full_graph(
            full,
            paired,
            source_expectation=source_expectation,
            pair_expectation=pair_expectation,
        )
