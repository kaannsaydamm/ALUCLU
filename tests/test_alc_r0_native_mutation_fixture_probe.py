"""Pure native mutation generation/classification; never builds or loads DLLs."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "native_mutation_fixture_probe",
    ROOT / "scripts/alc_r0_native_mutation_fixture_probe.py",
)
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


def test_closed_ten_variants_are_independent_and_deterministic():
    baseline = (ROOT / "native/alc_r0/banded_edit_visibility.cpp").read_bytes()
    first = PROBE.generate_variants(baseline)
    assert first == PROBE.generate_variants(baseline)
    assert tuple(first) == ("control", *PROBE.MUTATION_IDS)
    assert first["control"]["source_bytes"] == baseline
    assert len({record["source_sha256"] for record in first.values()}) == 10


def test_unknown_or_changed_baseline_fails_closed():
    with pytest.raises(ValueError):
        PROBE.generate_variants(b"not reviewed source")


def test_each_mutation_is_exact_single_baseline_anchor():
    baseline = (ROOT / "native/alc_r0/banded_edit_visibility.cpp").read_bytes()
    records = PROBE.generate_variants(baseline)
    for name in PROBE.MUTATION_IDS:
        record = records[name]
        assert baseline.count(record["old_bytes"]) == 1
        assert (
            baseline.replace(record["old_bytes"], record["new_bytes"], 1)
            == record["source_bytes"]
        )
    stale = records["stale-column"]["new_bytes"]
    assert b"uint32_t(j-low)<width" in stale
    assert b"prev_low<=j && j<=prev_high" in stale


def test_whole_control_schedule_reference_oracle_geometry_agree():
    cases = PROBE.schedule("control")
    assert len(PROBE.fixed_grid()) == 1470
    assert set(PROBE.fixed_grid()).issubset(cases)
    for case in cases:
        words = PROBE.expected_words(case)
        assert len(words) == 64 and words[55:] == [0] * 9
        assert words[3:7] == [len(case[0]), len(case[1]), 1, case[2]]


def test_closed_variant_schedule_rejects_unknown_ids_and_outside_cases():
    with pytest.raises(ValueError):
        PROBE.schedule("arbitrary-dll")
    with pytest.raises(ValueError):
        PROBE.expected_words(((99,), (), 512))


def test_manifest_stable_closed_identity_and_non_authority(tmp_path):
    baseline = (ROOT / "native/alc_r0/banded_edit_visibility.cpp").read_bytes()
    provenance = dict(
        verified_paths={
            str(
                ROOT
                / "docs/superpowers/plans/2026-10-02-alc-r0-banded-native-fixture-design.md"
            ): PROBE.PLAN_SHA256,
            str(
                ROOT / "src/aluclu/alc_r0/banded_edit_token_visibility_reference.py"
            ): PROBE.REFERENCE_SHA256,
            str(
                ROOT / "scripts/alc_r0_banded_edit_visibility_mutation_probe.py"
            ): PROBE.PROBE_SHA256,
            str(
                ROOT
                / "docs/superpowers/plans/2026-10-02-alc-r0-native-mutation-fixture-gate.md"
            ): PROBE.DETAIL_PLAN_SHA256,
        },
        baseline_receipt_path=str(tmp_path / "receipt.json"),
        baseline_receipt_sha256="0" * 64,
        generator_sha256=PROBE.digest(Path(SPEC.origin).read_bytes()),
    )
    first = PROBE.manifest(baseline, provenance)
    assert first == PROBE.manifest(baseline, provenance)
    assert [r["variant_id"] for r in first["variants"]] == [
        "control",
        *PROBE.MUTATION_IDS,
    ]
    assert first["stage"] == "generated-only-unbuilt"
    assert first["training_authority"] is first["held_out_data_present"] is False
    with pytest.raises(ValueError):
        PROBE.manifest(baseline, {"stage": "unit-only"})


@pytest.mark.parametrize(
    "case",
    [
        ((True,), (1,), 1),
        ((1,), (1,), True),
        ((1,), (1,), 1, 0),
        ((), (), -1),
        ((-1,), (), 1),
    ],
)
def test_exact_case_validation_excludes_bool_and_malformed(case):
    with pytest.raises(ValueError):
        PROBE.expected_words(case)


def test_control_disagreement_is_not_mutant_kill():
    case = ((1, 2), (2, 1), 2)
    words = PROBE.expected_words(case)
    words[24] = 0
    record = PROBE.classify_observation(
        dict(
            variant_id="control",
            compile_exit=0,
            child_exit=0,
            transport=0,
            canaries_intact=True,
            output_words=words,
            case=case,
        )
    )
    assert record["status"] == "control-disagreed"


@pytest.mark.parametrize("slot,value", [(7, 127), (27, 1), (54, 1), (2, 2), (7, 31)])
def test_structural_raw_abi_corruption_is_not_semantic_kill(slot, value):
    case = ((1, 2), (2, 1), 2)
    words = PROBE.expected_words(case)
    words[slot] = value
    with pytest.raises(ValueError):
        PROBE.classify_observation(
            dict(
                variant_id="marginal-total",
                compile_exit=0,
                child_exit=0,
                transport=0,
                canaries_intact=True,
                output_words=words,
                case=case,
            )
        )


@pytest.mark.parametrize("slot,value", [(19, 1), (7, 63), (20, 1), (2, 0)])
def test_unresolved_absent_distance_and_exposure_are_not_semantic_kills(slot, value):
    case = ((1,), (2,), 0)
    words = PROBE.expected_words(case)
    words[slot] = value
    with pytest.raises(ValueError):
        PROBE.classify_observation(
            dict(
                variant_id="accept-over-threshold",
                compile_exit=0,
                child_exit=0,
                transport=0,
                canaries_intact=True,
                output_words=words,
                case=case,
            )
        )


def test_accept_over_threshold_mathematics_remains_eligible():
    case = ((1,), (2,), 0)
    words = PROBE.expected_words(case)
    words[1], words[2], words[7], words[19], words[26] = 0, 0, 63, 3, 1
    record = PROBE.classify_observation(
        dict(
            variant_id="accept-over-threshold",
            compile_exit=0,
            child_exit=0,
            transport=0,
            canaries_intact=True,
            output_words=words,
            case=case,
        )
    )
    assert record["status"] == "semantic-killed"


@pytest.mark.parametrize(
    "field,value,status",
    [
        ("compile_exit", 1, "compile-failed"),
        ("child_exit", -1073741819, "child-crashed"),
        ("transport", 1, "transport-rejected"),
        ("transport", 3, "invariant-detected"),
        ("canaries_intact", False, "canary-failed"),
    ],
)
def test_failures_never_count_as_semantic_kills(field, value, status):
    case = ((1, 2), (2, 1), 2)
    observation = dict(
        variant_id="marginal-total",
        compile_exit=0,
        child_exit=0,
        transport=0,
        canaries_intact=True,
        output_words=PROBE.expected_words(case),
        case=case,
    )
    observation[field] = value
    assert PROBE.classify_observation(observation)["status"] == status


def test_only_completed_raw_disagreement_is_semantic_kill():
    case = ((1, 2), (2, 1), 2)
    words = PROBE.expected_words(case)
    observation = dict(
        variant_id="marginal-total",
        compile_exit=0,
        child_exit=0,
        transport=0,
        canaries_intact=True,
        output_words=words,
        case=case,
    )
    assert PROBE.classify_observation(observation)["status"] == "survived"
    observation["output_words"] = list(words)
    observation["output_words"][24] = 0
    record = PROBE.classify_observation(observation)
    assert (
        record["status"] == "semantic-killed" and record["differences"][0]["slot"] == 24
    )
