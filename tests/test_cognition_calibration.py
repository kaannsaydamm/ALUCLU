from __future__ import annotations

import hashlib
import struct
from collections.abc import Callable
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal, localcontext
from typing import Any, cast

import pytest

import aluclu.cognition as cognition_api
import aluclu.cognition.calibration as calibration_module
from aluclu.cognition import InputBoundaryError
from aluclu.cognition.calibration import (
    CalibrationArtifactV1,
    CalibrationDeploymentStatus,
    CalibrationDisabledReason,
    CalibrationPurpose,
    CalibrationSpecV1,
    CalibrationStatisticalStatus,
    LabeledRecallExampleV1,
    LabelIndependenceStatus,
    LabelProvenanceManifestV1,
    ThresholdSelectionRule,
    build_calibration_artifact,
    calibration_spec_from_json_value,
    calibration_spec_to_json_value,
    clopper_pearson_upper_bound,
    decode_calibration_artifact,
    decode_calibration_spec,
    decode_label_provenance_manifest,
    decode_labeled_recall_example,
    derive_calibration_artifact_digest,
    derive_calibration_spec_digest,
    derive_label_provenance_manifest_digest,
    derive_labeled_recall_example_digest,
    encode_calibration_artifact,
    encode_calibration_spec,
    encode_label_provenance_manifest,
    encode_labeled_recall_example,
    label_provenance_manifest_from_json_value,
    label_provenance_manifest_to_json_value,
    labeled_recall_example,
    labeled_recall_example_from_json_value,
    labeled_recall_example_to_json_value,
)
from aluclu.cognition.codec import canonical_json_bytes, strict_json_loads

# Independently generated at 160 decimal digits by regularized-beta inversion,
# then cross-checked with a separate arbitrary-precision binomial recurrence.
# Expected values are upper-rounded to the frozen 24-place output lattice.
_BOUND_FIXTURES = (
    (0, 0, "0.05", 10, "1"),
    (0, 1, "0.01", 1, "0.99"),
    (1, 1, "0.01", 1, "1"),
    (7, 7, "0.01", 8, "1"),
    (0, 100, "0.05", 10, "0.051604029624104003416529"),
    (3, 20, "0.05", 10, "0.449465406739485979638068"),
    (2, 100, "0.01", 20, "0.114628478227106434215945"),
    (0, 8_192, "0.01", 20, "0.000927414223873145725855"),
    (41, 8_192, "0.01", 20, "0.008122492527907508061789"),
    (8_191, 8_192, "0.01", 20, "0.999999938949581736343229"),
)

_REFERENCE_BRACKETS = (
    (
        0,
        100,
        "0.05",
        10,
        "0.051604029624104003416528549011825019770120768102135988378746",
        "0.051604029624104003416528549011825019770120768102135988378747",
    ),
    (
        3,
        20,
        "0.05",
        10,
        "0.449465406739485979638067610044323945311094092586512976964716",
        "0.449465406739485979638067610044323945311094092586512976964717",
    ),
    (
        2,
        100,
        "0.01",
        20,
        "0.114628478227106434215944787848433887325401418530863489815916",
        "0.114628478227106434215944787848433887325401418530863489815917",
    ),
    (
        0,
        8_192,
        "0.01",
        20,
        "0.000927414223873145725854448067561957565569046658234555190542",
        "0.000927414223873145725854448067561957565569046658234555190543",
    ),
    (
        41,
        8_192,
        "0.01",
        20,
        "0.008122492527907508061788090989821658758303277727626238650759",
        "0.008122492527907508061788090989821658758303277727626238650760",
    ),
    (
        8_191,
        8_192,
        "0.01",
        20,
        "0.999999938949581736343228208189735343252037573678027376928347",
        "0.999999938949581736343228208189735343252037573678027376928348",
    ),
)


@pytest.mark.parametrize(
    ("error_count", "selected_count", "delta_decimal", "family_size", "expected"),
    _BOUND_FIXTURES,
)
def test_clopper_pearson_upper_bound_matches_independent_fixtures(
    error_count: int,
    selected_count: int,
    delta_decimal: str,
    family_size: int,
    expected: str,
) -> None:
    assert (
        clopper_pearson_upper_bound(
            error_count=error_count,
            selected_count=selected_count,
            delta_decimal=delta_decimal,
            family_size=family_size,
        )
        == expected
    )


@pytest.mark.parametrize(
    (
        "error_count",
        "selected_count",
        "delta_decimal",
        "family_size",
        "reference_lower",
        "reference_upper",
    ),
    _REFERENCE_BRACKETS,
)
def test_clopper_pearson_result_is_conservatively_upper_rounded(
    error_count: int,
    selected_count: int,
    delta_decimal: str,
    family_size: int,
    reference_lower: str,
    reference_upper: str,
) -> None:
    actual = Decimal(
        clopper_pearson_upper_bound(
            error_count=error_count,
            selected_count=selected_count,
            delta_decimal=delta_decimal,
            family_size=family_size,
        )
    )

    assert actual >= Decimal(reference_upper)
    assert actual - Decimal(reference_lower) <= Decimal("1e-24")


def test_clopper_pearson_uses_bonferroni_tail_for_the_full_family() -> None:
    corrected = clopper_pearson_upper_bound(
        error_count=0,
        selected_count=100,
        delta_decimal="0.05",
        family_size=10,
    )
    uncorrected = clopper_pearson_upper_bound(
        error_count=0,
        selected_count=100,
        delta_decimal="0.05",
        family_size=1,
    )

    assert corrected == "0.051604029624104003416529"
    assert uncorrected == "0.029513049607039934500476"
    assert Decimal(corrected) > Decimal(uncorrected)


def test_clopper_pearson_ignores_the_ambient_decimal_context() -> None:
    baseline = clopper_pearson_upper_bound(
        error_count=0,
        selected_count=100,
        delta_decimal="0.05",
        family_size=1,
    )

    with localcontext() as hostile_context:
        hostile_context.prec = 6
        hostile_context.Emin = -9
        hostile_context.Emax = 9
        equivalent_tail = clopper_pearson_upper_bound(
            error_count=0,
            selected_count=100,
            delta_decimal="0.1",
            family_size=2,
        )

    assert baseline == "0.029513049607039934500476"
    assert equivalent_tail == baseline


def test_exact_fallback_reduces_the_probability_ratio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gcd_calls: list[tuple[int, int]] = []
    original_gcd = calibration_module.math.gcd

    def recording_gcd(left: int, right: int) -> int:
        gcd_calls.append((left, right))
        return original_gcd(left, right)

    monkeypatch.setattr(calibration_module.math, "gcd", recording_gcd)

    assert (
        clopper_pearson_upper_bound(
            error_count=250,
            selected_count=501,
            delta_decimal="0.5",
            family_size=1,
        )
        == "0.5"
    )
    assert (5 * 10**35, 10**36) in gcd_calls


def test_clopper_pearson_accepts_the_frozen_decimal_precision_boundary() -> None:
    assert (
        clopper_pearson_upper_bound(
            error_count=0,
            selected_count=0,
            delta_decimal=f"0.{'0' * 35}1",
            family_size=256,
        )
        == "1"
    )


@pytest.mark.parametrize(
    "overrides",
    (
        {"error_count": True},
        {"error_count": -1},
        {"error_count": 65_537},
        {"error_count": 2, "selected_count": 1},
        {"selected_count": True},
        {"selected_count": -1},
        {"selected_count": 65_537},
        {"family_size": True},
        {"family_size": 0},
        {"family_size": 257},
        {"delta_decimal": 0.05},
        {"delta_decimal": ""},
        {"delta_decimal": "0"},
        {"delta_decimal": "1"},
        {"delta_decimal": ".05"},
        {"delta_decimal": "0.050"},
        {"delta_decimal": "5e-2"},
        {"delta_decimal": "-0.05"},
        {"delta_decimal": "NaN"},
        {"delta_decimal": f"0.{'0' * 36}1"},
    ),
)
def test_clopper_pearson_rejects_noncanonical_or_invalid_inputs(
    overrides: dict[str, object],
) -> None:
    arguments: dict[str, object] = {
        "error_count": 0,
        "selected_count": 10,
        "delta_decimal": "0.05",
        "family_size": 4,
    }
    arguments.update(overrides)

    untyped_boundary_call = cast(Any, clopper_pearson_upper_bound)
    with pytest.raises(InputBoundaryError):
        untyped_boundary_call(**arguments)


_GOLD_SOURCE_DIGEST = "a" * 64
_DATASET_MANIFEST_DIGEST = "b" * 64
_SCORER_INPUT_MANIFEST_DIGEST = "c" * 64
_GOLD_LABEL_MANIFEST_DIGEST = "d" * 64


def _label_manifest(
    *,
    fit_example_ids: tuple[str, ...] = ("example:fit-1",),
    calibration_example_ids: tuple[str, ...] = (
        "example:calibration-1",
        "example:calibration-2",
    ),
) -> LabelProvenanceManifestV1:
    return LabelProvenanceManifestV1(
        issuer_id="issuer:research-team",
        adjudication_method_id="held-out-double-review.v1",
        gold_source_digest=_GOLD_SOURCE_DIGEST,
        dataset_manifest_digest=_DATASET_MANIFEST_DIGEST,
        scorer_input_manifest_digest=_SCORER_INPUT_MANIFEST_DIGEST,
        gold_label_manifest_digest=_GOLD_LABEL_MANIFEST_DIGEST,
        fit_example_ids=fit_example_ids,
        calibration_example_ids=calibration_example_ids,
        external_evidence_reference="audit:pending",
        external_signature_digest=None,
        independence_status=LabelIndependenceStatus.ASSERTED_NOT_PROVEN,
    )


def _calibration_spec(
    manifest: LabelProvenanceManifestV1 | None = None,
) -> CalibrationSpecV1:
    active_manifest = manifest or _label_manifest()
    return CalibrationSpecV1(
        purpose=CalibrationPurpose.PERSONAL_MEMORY_TEXT,
        query_stratum_id="personal-memory.en.v1",
        scorer_id="aluclu.similarity.cosine-q32.v1",
        normalizer_id="aluclu.search-view.nfc-ascii-ws.v1+ucd-15.0.0",
        feature_spec_id="aluclu.feature.signed-byte-ngram-1024-int16.v1+ucd-15.0.0",
        boundary_schema_id="aluclu.boundary-profile.v1",
        dataset_manifest_digest=_DATASET_MANIFEST_DIGEST,
        label_provenance_manifest_digest=(
            derive_label_provenance_manifest_digest(active_manifest)
        ),
        threshold_grid_q32=(0, 2**31, 2**32),
        minimum_margin_q32=2**24,
        alpha_decimal="0.1",
        delta_decimal="0.05",
        minimum_selected=2,
        minimum_coverage_decimal="0.25",
        selection_rule=ThresholdSelectionRule.MAX_COVERAGE_THEN_HIGHER_THRESHOLD,
    )


def _labeled_example(
    spec: CalibrationSpecV1 | None = None,
    manifest: LabelProvenanceManifestV1 | None = None,
) -> LabeledRecallExampleV1:
    active_manifest = manifest or _label_manifest()
    active_spec = spec or _calibration_spec(active_manifest)
    return labeled_recall_example(
        example_id="example:calibration-1",
        calibration_spec_digest=derive_calibration_spec_digest(active_spec),
        label_provenance_manifest_digest=(
            derive_label_provenance_manifest_digest(active_manifest)
        ),
        score_q32=2**31,
        eligible=True,
        target_observation_id="obs:gold-1",
        predicted_observation_id=None,
    )


def _example_for(
    *,
    example_id: str,
    score_q32: int,
    target_observation_id: str,
    predicted_observation_id: str | None,
    spec: CalibrationSpecV1,
    manifest: LabelProvenanceManifestV1,
    eligible: bool = True,
) -> LabeledRecallExampleV1:
    return labeled_recall_example(
        example_id=example_id,
        calibration_spec_digest=derive_calibration_spec_digest(spec),
        label_provenance_manifest_digest=(
            derive_label_provenance_manifest_digest(manifest)
        ),
        score_q32=score_q32,
        eligible=eligible,
        target_observation_id=target_observation_id,
        predicted_observation_id=predicted_observation_id,
    )


def _passing_artifact_inputs() -> tuple[
    CalibrationSpecV1,
    LabelProvenanceManifestV1,
    tuple[LabeledRecallExampleV1, ...],
]:
    manifest = _label_manifest()
    spec = replace(
        _calibration_spec(manifest),
        alpha_decimal="1",
        minimum_selected=1,
        minimum_coverage_decimal="0",
    )
    examples = (
        _example_for(
            example_id="example:calibration-1",
            score_q32=2**32,
            target_observation_id="obs:gold-1",
            predicted_observation_id="obs:gold-1",
            spec=spec,
            manifest=manifest,
        ),
        _example_for(
            example_id="example:calibration-2",
            score_q32=2**31,
            target_observation_id="obs:gold-2",
            predicted_observation_id="obs:gold-2",
            spec=spec,
            manifest=manifest,
        ),
    )
    return spec, manifest, examples


@pytest.mark.parametrize(
    ("instance", "field_names"),
    (
        (
            _label_manifest(),
            (
                "issuer_id",
                "adjudication_method_id",
                "gold_source_digest",
                "dataset_manifest_digest",
                "scorer_input_manifest_digest",
                "gold_label_manifest_digest",
                "fit_example_ids",
                "calibration_example_ids",
                "external_evidence_reference",
                "external_signature_digest",
                "independence_status",
            ),
        ),
        (
            _calibration_spec(),
            (
                "purpose",
                "query_stratum_id",
                "scorer_id",
                "normalizer_id",
                "feature_spec_id",
                "boundary_schema_id",
                "dataset_manifest_digest",
                "label_provenance_manifest_digest",
                "threshold_grid_q32",
                "minimum_margin_q32",
                "alpha_decimal",
                "delta_decimal",
                "minimum_selected",
                "minimum_coverage_decimal",
                "selection_rule",
            ),
        ),
        (
            _labeled_example(),
            (
                "example_id",
                "calibration_spec_digest",
                "label_provenance_manifest_digest",
                "score_q32",
                "eligible",
                "target_observation_id",
                "predicted_observation_id",
                "error",
            ),
        ),
    ),
)
def test_calibration_records_are_frozen_kw_only_and_slotted(
    instance: object,
    field_names: tuple[str, ...],
) -> None:
    assert is_dataclass(instance) and not isinstance(instance, type)
    assert tuple(field.name for field in fields(instance)) == field_names
    assert not hasattr(instance, "__dict__")
    first_field = field_names[0]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        setattr(instance, first_field, getattr(instance, first_field))
    with pytest.raises(TypeError):
        type(instance)(*[getattr(instance, name) for name in field_names])


def test_calibration_records_round_trip_canonically_with_stable_digests() -> None:
    manifest = _label_manifest()
    spec = _calibration_spec(manifest)
    example = _labeled_example(spec, manifest)

    for instance, encoder, decoder, to_value, from_value, digest in (
        (
            manifest,
            encode_label_provenance_manifest,
            decode_label_provenance_manifest,
            label_provenance_manifest_to_json_value,
            label_provenance_manifest_from_json_value,
            derive_label_provenance_manifest_digest,
        ),
        (
            spec,
            encode_calibration_spec,
            decode_calibration_spec,
            calibration_spec_to_json_value,
            calibration_spec_from_json_value,
            derive_calibration_spec_digest,
        ),
        (
            example,
            encode_labeled_recall_example,
            decode_labeled_recall_example,
            labeled_recall_example_to_json_value,
            labeled_recall_example_from_json_value,
            derive_labeled_recall_example_digest,
        ),
    ):
        encoded = cast(Callable[[Any], bytes], encoder)(instance)
        decoded = cast(Callable[[bytes], object], decoder)(encoded)
        json_value = cast(Callable[[Any], object], to_value)(instance)
        rebuilt = cast(Callable[[Any], object], from_value)(json_value)

        assert canonical_json_bytes(cast(Any, json_value)) == encoded
        assert decoded == instance
        assert rebuilt == instance
        assert cast(Callable[[Any], str], digest)(decoded) == cast(
            Callable[[Any], str], digest
        )(instance)


def test_calibration_schema_surface_is_exported_from_cognition_package() -> None:
    expected_names = (
        "CalibrationPurpose",
        "CalibrationSpecV1",
        "LabelIndependenceStatus",
        "LabeledRecallExampleV1",
        "LabelProvenanceManifestV1",
        "ThresholdSelectionRule",
        "calibration_spec_from_json_value",
        "calibration_spec_to_json_value",
        "clopper_pearson_upper_bound",
        "decode_calibration_spec",
        "decode_label_provenance_manifest",
        "decode_labeled_recall_example",
        "derive_calibration_spec_digest",
        "derive_label_provenance_manifest_digest",
        "derive_labeled_recall_example_digest",
        "encode_calibration_spec",
        "encode_label_provenance_manifest",
        "encode_labeled_recall_example",
        "label_provenance_manifest_from_json_value",
        "label_provenance_manifest_to_json_value",
        "labeled_recall_example",
        "labeled_recall_example_from_json_value",
        "labeled_recall_example_to_json_value",
    )

    for name in expected_names:
        assert hasattr(cognition_api, name)
        assert name in cognition_api.__all__


def test_threshold_grid_mutation_changes_the_spec_binding() -> None:
    manifest = _label_manifest()
    original = _calibration_spec(manifest)
    example = _labeled_example(original, manifest)
    mutated = replace(original, threshold_grid_q32=(0, 2**30, 2**32))

    assert derive_calibration_spec_digest(mutated) != (
        derive_calibration_spec_digest(original)
    )
    assert example.calibration_spec_digest == derive_calibration_spec_digest(original)
    assert example.calibration_spec_digest != derive_calibration_spec_digest(mutated)


@pytest.mark.parametrize(
    "threshold_grid_q32",
    (
        [],
        (),
        (2, 1),
        (1, 1),
        (True,),
        (-1,),
        (2**32 + 1,),
        tuple(range(257)),
    ),
)
def test_calibration_spec_rejects_invalid_threshold_grids(
    threshold_grid_q32: object,
) -> None:
    with pytest.raises(InputBoundaryError):
        replace(_calibration_spec(), threshold_grid_q32=threshold_grid_q32)


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("minimum_margin_q32", True),
        ("minimum_margin_q32", 2**32 + 1),
        ("purpose", "personal_memory_text"),
        ("selection_rule", "max_coverage_then_higher_threshold"),
        ("scorer_id", "scorer with spaces"),
        ("alpha_decimal", "0.10"),
        ("alpha_decimal", "1.0"),
        ("alpha_decimal", "2"),
        ("delta_decimal", "0"),
        ("minimum_selected", True),
        ("minimum_selected", 0),
        ("minimum_selected", 65_537),
        ("minimum_coverage_decimal", "0.250"),
        ("minimum_coverage_decimal", "-0.1"),
        ("dataset_manifest_digest", "A" * 64),
        ("label_provenance_manifest_digest", "not-a-digest"),
        ("query_stratum_id", "stratum with spaces"),
    ),
)
def test_calibration_spec_rejects_noncanonical_boundaries(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(InputBoundaryError):
        replace(_calibration_spec(), **{field_name: value})


def test_label_manifest_preserves_semantic_builder_failures() -> None:
    overlap = _label_manifest(
        fit_example_ids=("example:shared",),
        calibration_example_ids=("example:shared",),
    )
    empty = _label_manifest(calibration_example_ids=())

    assert overlap.fit_example_ids == overlap.calibration_example_ids
    assert empty.calibration_example_ids == ()


def test_label_manifest_is_bounded_to_a_round_trippable_id_set() -> None:
    fit_ids = tuple(f"example:fit-{index:04d}" for index in range(4_094))
    at_boundary = _label_manifest(fit_example_ids=fit_ids)

    assert len(at_boundary.fit_example_ids) + len(
        at_boundary.calibration_example_ids
    ) == 4_096
    assert decode_label_provenance_manifest(
        encode_label_provenance_manifest(at_boundary)
    ) == at_boundary

    with pytest.raises(InputBoundaryError):
        replace(
            at_boundary,
            fit_example_ids=fit_ids + ("example:fit-4094",),
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("fit_example_ids", ["example:fit-1"]),
        ("fit_example_ids", ("example:z", "example:a")),
        ("fit_example_ids", ("example:a", "example:a")),
        ("calibration_example_ids", ("bad id",)),
        ("issuer_id", "bad issuer"),
        ("gold_source_digest", "0" * 63),
        ("independence_status", "asserted_not_proven"),
        ("external_evidence_reference", ""),
        ("external_evidence_reference", "x" * 2_049),
        ("external_signature_digest", "A" * 64),
    ),
)
def test_label_manifest_rejects_structurally_invalid_fields(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(InputBoundaryError):
        replace(_label_manifest(), **{field_name: value})


def test_labeled_example_derives_error_and_blocks_direct_construction() -> None:
    manifest = _label_manifest()
    spec = _calibration_spec(manifest)
    incorrect = _labeled_example(spec, manifest)
    correct = labeled_recall_example(
        example_id="example:calibration-2",
        calibration_spec_digest=derive_calibration_spec_digest(spec),
        label_provenance_manifest_digest=(
            derive_label_provenance_manifest_digest(manifest)
        ),
        score_q32=2**32,
        eligible=False,
        target_observation_id="obs:gold-2",
        predicted_observation_id="obs:gold-2",
    )

    assert incorrect.error is True
    assert correct.error is False
    with pytest.raises(TypeError):
        LabeledRecallExampleV1()


def test_labeled_example_decoder_rejects_self_assigned_error() -> None:
    wire = strict_json_loads(encode_labeled_recall_example(_labeled_example()))
    assert type(wire) is dict
    wire["error"] = False

    with pytest.raises(InputBoundaryError):
        decode_labeled_recall_example(canonical_json_bytes(wire))


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("example_id", "bad id"),
        ("calibration_spec_digest", "A" * 64),
        ("label_provenance_manifest_digest", "0" * 63),
        ("score_q32", True),
        ("score_q32", 2**32 + 1),
        ("eligible", 1),
        ("target_observation_id", "event:not-an-observation"),
        ("predicted_observation_id", "obs:"),
    ),
)
def test_labeled_example_factory_rejects_invalid_boundaries(
    field_name: str,
    value: object,
) -> None:
    arguments: dict[str, object] = {
        "example_id": "example:calibration-1",
        "calibration_spec_digest": "a" * 64,
        "label_provenance_manifest_digest": "b" * 64,
        "score_q32": 2**31,
        "eligible": True,
        "target_observation_id": "obs:gold-1",
        "predicted_observation_id": None,
    }
    arguments[field_name] = value

    with pytest.raises(InputBoundaryError):
        cast(Any, labeled_recall_example)(**arguments)


@pytest.mark.parametrize(
    ("encoder", "decoder", "instance"),
    (
        (encode_calibration_spec, decode_calibration_spec, _calibration_spec()),
        (
            encode_label_provenance_manifest,
            decode_label_provenance_manifest,
            _label_manifest(),
        ),
        (
            encode_labeled_recall_example,
            decode_labeled_recall_example,
            _labeled_example(),
        ),
    ),
)
def test_calibration_decoders_require_exact_canonical_objects(
    encoder: Callable[[Any], bytes],
    decoder: Callable[[bytes], object],
    instance: object,
) -> None:
    encoded = encoder(instance)
    wire = strict_json_loads(encoded)
    assert type(wire) is dict

    missing = dict(wire)
    missing.pop(next(iter(missing)))
    with pytest.raises(InputBoundaryError):
        decoder(canonical_json_bytes(missing))

    unknown = dict(wire)
    unknown["unknown"] = None
    with pytest.raises(InputBoundaryError):
        decoder(canonical_json_bytes(unknown))

    wrong_schema = dict(wire)
    wrong_schema["schema"] = "aluclu.wrong.v1"
    with pytest.raises(InputBoundaryError):
        decoder(canonical_json_bytes(wrong_schema))

    with pytest.raises(InputBoundaryError):
        decoder(b" " + encoded)


def test_calibration_decoders_reject_bool_integer_fields() -> None:
    spec_wire = strict_json_loads(encode_calibration_spec(_calibration_spec()))
    assert type(spec_wire) is dict
    spec_wire["minimum_selected"] = True
    with pytest.raises(InputBoundaryError):
        decode_calibration_spec(canonical_json_bytes(spec_wire))

    example_wire = strict_json_loads(
        encode_labeled_recall_example(_labeled_example())
    )
    assert type(example_wire) is dict
    example_wire["score_q32"] = True
    with pytest.raises(InputBoundaryError):
        decode_labeled_recall_example(canonical_json_bytes(example_wire))


def test_calibration_builder_selects_maximum_coverage_then_higher_threshold() -> None:
    spec, manifest, examples = _passing_artifact_inputs()

    artifact = build_calibration_artifact(spec, manifest, examples)

    assert artifact.statistical_status is CalibrationStatisticalStatus.STATISTICAL_PASS
    assert artifact.deployment_status is CalibrationDeploymentStatus.TEST_ONLY
    assert artifact.independence_status is LabelIndependenceStatus.ASSERTED_NOT_PROVEN
    assert artifact.chosen_threshold_q32 == 2**31
    assert artifact.disabled_reasons == ()
    assert artifact.production_acceptance_digest is None
    assert tuple(result.threshold_q32 for result in artifact.threshold_results) == (
        0,
        2**31,
        2**32,
    )
    assert tuple(result.selected_count for result in artifact.threshold_results) == (
        2,
        2,
        1,
    )
    assert tuple(result.error_count for result in artifact.threshold_results) == (
        0,
        0,
        0,
    )
    assert tuple(result.coverage_decimal for result in artifact.threshold_results) == (
        "1",
        "1",
        "0.5",
    )
    assert all(result.passed for result in artifact.threshold_results)


def test_calibration_builder_is_deterministic_under_example_permutation() -> None:
    spec, manifest, examples = _passing_artifact_inputs()

    forward = build_calibration_artifact(spec, manifest, examples)
    reversed_artifact = build_calibration_artifact(
        spec,
        manifest,
        tuple(reversed(examples)),
    )

    assert reversed_artifact == forward
    assert reversed_artifact.artifact_digest == forward.artifact_digest
    assert reversed_artifact.example_set_digest == forward.example_set_digest


def test_calibration_artifact_round_trips_and_verifies_its_digest() -> None:
    spec, manifest, examples = _passing_artifact_inputs()
    artifact = build_calibration_artifact(spec, manifest, examples)

    encoded = encode_calibration_artifact(artifact)

    assert decode_calibration_artifact(encoded) == artifact
    assert derive_calibration_artifact_digest(artifact) == artifact.artifact_digest
    assert not hasattr(artifact, "__dict__")
    with pytest.raises(TypeError):
        CalibrationArtifactV1()

    wire = strict_json_loads(encoded)
    assert type(wire) is dict
    wire["chosen_threshold_q32"] = 0
    with pytest.raises(InputBoundaryError):
        decode_calibration_artifact(canonical_json_bytes(wire))


@pytest.mark.parametrize(
    "expected_reason",
    (
        CalibrationDisabledReason.ZERO_EXAMPLES,
        CalibrationDisabledReason.FIT_CALIBRATION_OVERLAP,
        CalibrationDisabledReason.LABEL_MANIFEST_LEAKAGE,
        CalibrationDisabledReason.DATASET_MANIFEST_MISMATCH,
        CalibrationDisabledReason.EXAMPLE_SET_MISMATCH,
        CalibrationDisabledReason.SPEC_DIGEST_MISMATCH,
        CalibrationDisabledReason.LABEL_MANIFEST_DIGEST_MISMATCH,
        CalibrationDisabledReason.INSUFFICIENT_SELECTED,
        CalibrationDisabledReason.NO_PASSING_THRESHOLD,
    ),
)
def test_calibration_builder_emits_explicit_disabled_reasons(
    expected_reason: CalibrationDisabledReason,
) -> None:
    spec, manifest, examples = _passing_artifact_inputs()

    if expected_reason is CalibrationDisabledReason.ZERO_EXAMPLES:
        manifest = _label_manifest(calibration_example_ids=())
        spec = _calibration_spec(manifest)
        examples = ()
    elif expected_reason is CalibrationDisabledReason.FIT_CALIBRATION_OVERLAP:
        manifest = _label_manifest(
            fit_example_ids=("example:calibration-1",),
        )
        spec = replace(
            _calibration_spec(manifest),
            alpha_decimal="1",
            minimum_selected=1,
            minimum_coverage_decimal="0",
        )
        examples = tuple(
            _example_for(
                example_id=example_id,
                score_q32=2**32,
                target_observation_id=f"obs:gold-{index}",
                predicted_observation_id=f"obs:gold-{index}",
                spec=spec,
                manifest=manifest,
            )
            for index, example_id in enumerate(
                manifest.calibration_example_ids,
                start=1,
            )
        )
    elif expected_reason is CalibrationDisabledReason.LABEL_MANIFEST_LEAKAGE:
        manifest = replace(
            manifest,
            scorer_input_manifest_digest=manifest.gold_label_manifest_digest,
        )
        spec = replace(
            spec,
            label_provenance_manifest_digest=(
                derive_label_provenance_manifest_digest(manifest)
            ),
        )
        examples = tuple(
            _example_for(
                example_id=example.example_id,
                score_q32=example.score_q32,
                target_observation_id=example.target_observation_id,
                predicted_observation_id=example.predicted_observation_id,
                spec=spec,
                manifest=manifest,
            )
            for example in examples
        )
    elif expected_reason is CalibrationDisabledReason.DATASET_MANIFEST_MISMATCH:
        spec = replace(spec, dataset_manifest_digest="e" * 64)
        examples = tuple(
            _example_for(
                example_id=example.example_id,
                score_q32=example.score_q32,
                target_observation_id=example.target_observation_id,
                predicted_observation_id=example.predicted_observation_id,
                spec=spec,
                manifest=manifest,
            )
            for example in examples
        )
    elif expected_reason is CalibrationDisabledReason.EXAMPLE_SET_MISMATCH:
        examples = examples[:1]
    elif expected_reason is CalibrationDisabledReason.SPEC_DIGEST_MISMATCH:
        spec = replace(spec, threshold_grid_q32=(0, 2**30, 2**32))
    elif expected_reason is CalibrationDisabledReason.LABEL_MANIFEST_DIGEST_MISMATCH:
        manifest = replace(manifest, issuer_id="issuer:changed")
    elif expected_reason is CalibrationDisabledReason.INSUFFICIENT_SELECTED:
        spec = replace(spec, minimum_selected=3)
        examples = tuple(
            _example_for(
                example_id=example.example_id,
                score_q32=example.score_q32,
                target_observation_id=example.target_observation_id,
                predicted_observation_id=example.predicted_observation_id,
                spec=spec,
                manifest=manifest,
            )
            for example in examples
        )
    elif expected_reason is CalibrationDisabledReason.NO_PASSING_THRESHOLD:
        spec = replace(spec, alpha_decimal="0")
        examples = tuple(
            _example_for(
                example_id=example.example_id,
                score_q32=example.score_q32,
                target_observation_id=example.target_observation_id,
                predicted_observation_id=example.predicted_observation_id,
                spec=spec,
                manifest=manifest,
            )
            for example in examples
        )

    artifact = build_calibration_artifact(spec, manifest, examples)

    assert artifact.statistical_status is CalibrationStatisticalStatus.DISABLED
    assert artifact.deployment_status is CalibrationDeploymentStatus.TEST_ONLY
    assert artifact.chosen_threshold_q32 is None
    assert expected_reason in artifact.disabled_reasons
    assert tuple(reason.value for reason in artifact.disabled_reasons) == tuple(
        sorted(reason.value for reason in artifact.disabled_reasons)
    )


def test_task2_builder_cannot_mint_production_acceptance() -> None:
    spec, manifest, examples = _passing_artifact_inputs()

    artifact = build_calibration_artifact(spec, manifest, examples)

    assert artifact.deployment_status is CalibrationDeploymentStatus.TEST_ONLY
    assert artifact.production_acceptance_digest is None
    assert not hasattr(calibration_module, "promote_calibration_artifact")


def test_artifact_surface_is_exported_from_cognition_package() -> None:
    expected_names = (
        "CalibrationArtifactV1",
        "CalibrationDeploymentStatus",
        "CalibrationDisabledReason",
        "CalibrationStatisticalStatus",
        "ThresholdCalibrationV1",
        "build_calibration_artifact",
        "calibration_artifact_from_json_value",
        "calibration_artifact_to_json_value",
        "decode_calibration_artifact",
        "derive_calibration_artifact_digest",
        "encode_calibration_artifact",
        "threshold_calibration_from_json_value",
        "threshold_calibration_to_json_value",
    )

    for name in expected_names:
        assert hasattr(cognition_api, name)
        assert name in cognition_api.__all__


def test_builder_binds_bonferroni_family_to_full_threshold_grid() -> None:
    manifest = _label_manifest()
    spec = replace(
        _calibration_spec(manifest),
        alpha_decimal="0.8",
        minimum_selected=2,
        minimum_coverage_decimal="0",
    )
    examples = tuple(
        _example_for(
            example_id=example_id,
            score_q32=2**32,
            target_observation_id=f"obs:gold-{index}",
            predicted_observation_id=f"obs:gold-{index}",
            spec=spec,
            manifest=manifest,
        )
        for index, example_id in enumerate(
            manifest.calibration_example_ids,
            start=1,
        )
    )

    artifact = build_calibration_artifact(spec, manifest, examples)

    assert artifact.statistical_status is CalibrationStatisticalStatus.DISABLED
    assert artifact.chosen_threshold_q32 is None
    assert tuple(
        result.risk_upper_bound_decimal for result in artifact.threshold_results
    ) == (
        "0.870900555126419437160692",
        "0.870900555126419437160692",
        "0.870900555126419437160692",
    )
    assert not any(result.passed for result in artifact.threshold_results)
    assert CalibrationDisabledReason.NO_PASSING_THRESHOLD in artifact.disabled_reasons


def test_builder_excludes_ineligible_examples_from_counts_and_errors() -> None:
    manifest = _label_manifest(
        calibration_example_ids=(
            "example:calibration-1",
            "example:calibration-2",
            "example:calibration-3",
        )
    )
    spec = replace(
        _calibration_spec(manifest),
        alpha_decimal="1",
        minimum_selected=1,
        minimum_coverage_decimal="0",
    )
    examples = (
        _example_for(
            example_id="example:calibration-1",
            score_q32=2**32,
            target_observation_id="obs:gold-1",
            predicted_observation_id="obs:gold-1",
            spec=spec,
            manifest=manifest,
        ),
        _example_for(
            example_id="example:calibration-2",
            score_q32=2**31,
            target_observation_id="obs:gold-2",
            predicted_observation_id="obs:gold-2",
            spec=spec,
            manifest=manifest,
        ),
        _example_for(
            example_id="example:calibration-3",
            score_q32=2**32,
            target_observation_id="obs:gold-3",
            predicted_observation_id="obs:wrong-3",
            spec=spec,
            manifest=manifest,
            eligible=False,
        ),
    )

    artifact = build_calibration_artifact(spec, manifest, examples)
    lowest_threshold = artifact.threshold_results[0]

    assert lowest_threshold.selected_count == 2
    assert lowest_threshold.error_count == 0
    assert lowest_threshold.coverage_decimal == "0.666666666666666666666666"


def test_builder_counts_selected_errors_and_binds_their_risk_bound() -> None:
    manifest = _label_manifest()
    spec = replace(
        _calibration_spec(manifest),
        alpha_decimal="0.99",
        minimum_selected=2,
        minimum_coverage_decimal="0",
    )
    examples = (
        _example_for(
            example_id="example:calibration-1",
            score_q32=2**32,
            target_observation_id="obs:gold-1",
            predicted_observation_id="obs:gold-1",
            spec=spec,
            manifest=manifest,
        ),
        _example_for(
            example_id="example:calibration-2",
            score_q32=2**32,
            target_observation_id="obs:gold-2",
            predicted_observation_id="obs:wrong-2",
            spec=spec,
            manifest=manifest,
        ),
    )

    artifact = build_calibration_artifact(spec, manifest, examples)

    assert tuple(
        (result.selected_count, result.error_count)
        for result in artifact.threshold_results
    ) == ((2, 1), (2, 1), (2, 1))
    assert tuple(
        result.risk_upper_bound_decimal for result in artifact.threshold_results
    ) == (
        "0.991631652042901126219544",
        "0.991631652042901126219544",
        "0.991631652042901126219544",
    )
    assert not any(result.passed for result in artifact.threshold_results)
    assert artifact.statistical_status is CalibrationStatisticalStatus.DISABLED


def test_builder_floors_nonterminating_coverage_before_the_gate() -> None:
    manifest = _label_manifest(
        calibration_example_ids=(
            "example:calibration-1",
            "example:calibration-2",
            "example:calibration-3",
        )
    )
    spec = replace(
        _calibration_spec(manifest),
        alpha_decimal="1",
        minimum_selected=1,
        minimum_coverage_decimal="0.333333333333333333333334",
    )
    examples = tuple(
        _example_for(
            example_id=example_id,
            score_q32=2**32 if index == 1 else 0,
            target_observation_id=f"obs:gold-{index}",
            predicted_observation_id=f"obs:gold-{index}",
            spec=spec,
            manifest=manifest,
        )
        for index, example_id in enumerate(
            manifest.calibration_example_ids,
            start=1,
        )
    )

    artifact = build_calibration_artifact(spec, manifest, examples)
    partial_results = artifact.threshold_results[1:]

    assert tuple(result.selected_count for result in partial_results) == (1, 1)
    assert tuple(result.coverage_decimal for result in partial_results) == (
        "0.333333333333333333333333",
        "0.333333333333333333333333",
    )
    assert not any(result.passed for result in partial_results)


def test_disabled_artifact_cannot_claim_production_acceptance() -> None:
    manifest = _label_manifest(calibration_example_ids=())
    spec = _calibration_spec(manifest)
    artifact = build_calibration_artifact(spec, manifest, ())
    wire = strict_json_loads(encode_calibration_artifact(artifact))
    assert type(wire) is dict
    wire["deployment_status"] = "production_accepted"
    wire["production_acceptance_digest"] = "f" * 64
    artifact_body = dict(wire)
    artifact_body.pop("artifact_digest")
    domain = b"aluclu.task2.calibration-artifact.v1"
    body_bytes = canonical_json_bytes(cast(Any, artifact_body))
    framed = (
        struct.pack(">Q", len(domain))
        + domain
        + struct.pack(">Q", len(body_bytes))
        + body_bytes
    )
    wire["artifact_digest"] = hashlib.sha256(framed).hexdigest()

    with pytest.raises(InputBoundaryError, match="statistical pass"):
        decode_calibration_artifact(canonical_json_bytes(wire))
