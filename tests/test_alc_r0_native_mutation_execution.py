"""Data-only execution gate tests; no native compilation/loading is exercised."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "native_mutation_execution", ROOT / "scripts/alc_r0_native_mutation_execution.py"
)
EXECUTION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXECUTION)


@pytest.mark.parametrize("text", ['{"schema":1,"schema":1}', '{"schema":NaN}', "{}"])
def test_strict_json_rejects_duplicate_nonfinite_or_missing_schema(text):
    with pytest.raises(ValueError):
        EXECUTION.decode_document(
            text, {"schema", "training_authority", "held_out_data_present"}
        )


def test_command_and_environment_are_closed():
    out = Path("C:/fixture-external/unit-control")
    command = EXECUTION.build_command(out)
    assert command[1:7] == ["/nologo", "/O2", "/std:c++17", "/EHsc", "/MT", "/LD"]
    env = EXECUTION.build_environment(
        {"CL": "/evil", "_CL_": "/evil", "PATH": "original"}
    )
    assert "CL" not in env and "_CL_" not in env
    assert env["PATH"].endswith("original")


@pytest.mark.parametrize("records", [{}, {"control": {}}, {"foreign": {}}])
def test_incomplete_or_foreign_aggregate_never_passes(records):
    with pytest.raises(ValueError):
        EXECUTION.aggregate_verified_records(records)


MANIFEST = Path(
    "C:/Users/kaann/Desktop/03_Projeler_Arge/ALUCLU/.research-evidence/alc_r0_banded_native_20261002/mutation-sources-5ed52f4-v1/manifest.json"
)


def test_actual_reviewed_manifest_raw_byte_binding():
    import hashlib

    raw = MANIFEST.read_bytes()
    binding = EXECUTION.capture_manifest_binding(MANIFEST)
    assert binding == hashlib.sha256(raw).hexdigest()
    EXECUTION.verify_manifest_unchanged(MANIFEST, binding)


def test_actual_reviewed_manifest_regeneration_positive():
    data, receipt, variants = EXECUTION.verify_manifest(MANIFEST)
    assert len(data["variants"]) == len(variants) == 10
    assert receipt["native_source_sha256"] == variants["control"]["source_sha256"]
    assert len(data["variants"][0]["cases"]) == 1473


@pytest.mark.parametrize(
    "field,value",
    [
        ("required_payload", 0),
        ("logical_capacity", 0),
        ("allocated_backing_bytes", 0),
        ("output_words", 63),
    ],
)
def test_allocation_proof_requires_exact_reference_layout(field, value):
    case = ((1,), (1,), 0)
    allocation = dict(
        required_payload=66,
        logical_capacity=66,
        allocated_backing_bytes=76,
        output_words=64,
    )
    EXECUTION.verify_allocation(allocation, case)
    allocation[field] = value
    with pytest.raises(ValueError):
        EXECUTION.verify_allocation(allocation, case)


def test_later_kill_cannot_promote_prior_guard_or_no_write_failure():
    clean = dict(
        status="invariant-detected",
        workspace_guards_intact=True,
        no_write_contract_intact=True,
    )
    killed = dict(
        status="semantic-killed",
        workspace_guards_intact=True,
        no_write_contract_intact=True,
    )
    assert EXECUTION.interpret_completed_prefix([clean, killed]) == "semantic-killed"
    for field in ("workspace_guards_intact", "no_write_contract_intact"):
        prior = dict(clean)
        prior[field] = False
        assert EXECUTION.interpret_completed_prefix([prior, killed]) == "canary-failed"


def _copy_manifest(tmp_path):
    import shutil

    copied = tmp_path / "generation"
    shutil.copytree(MANIFEST.parent, copied)
    path = copied / "manifest.json"
    EXECUTION.verify_manifest(path)
    return path


@pytest.mark.parametrize(
    "kind",
    [
        "foreign-id",
        "duplicate-id",
        "wrong-source-hash",
        "changed-witness",
        "wrong-probe-pin",
        "wrong-receipt-hash",
        "authority-true",
        "unknown-field",
        "schema-bool",
    ],
)
def test_regenerated_manifest_negative_from_real_positive(tmp_path, kind):
    import json

    path = _copy_manifest(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    original_sha = EXECUTION.sha(MANIFEST)
    if kind == "foreign-id":
        data["variants"][1]["variant_id"] = "foreign"
    elif kind == "duplicate-id":
        data["variants"][1]["variant_id"] = "control"
    elif kind == "wrong-source-hash":
        data["variants"][1]["source_sha256"] = "0" * 64
    elif kind == "changed-witness":
        data["variants"][1]["cases"][0][2] = 2
    elif kind == "wrong-probe-pin":
        data["provenance"]["verified_paths"][
            str(ROOT / "scripts/alc_r0_banded_edit_visibility_mutation_probe.py")
        ] = "0" * 64
    elif kind == "wrong-receipt-hash":
        data["provenance"]["baseline_receipt_sha256"] = "0" * 64
    elif kind == "authority-true":
        data["training_authority"] = True
    elif kind == "unknown-field":
        data["extra"] = 0
    else:
        data["schema"] = True
    EXECUTION.write_document(path, data)
    with pytest.raises(ValueError):
        EXECUTION.verify_manifest(path)
    assert EXECUTION.sha(MANIFEST) == original_sha


def test_changed_generated_bytes_rejected_without_changing_original(tmp_path):
    path = _copy_manifest(tmp_path)
    target = path.parent / "stale-column/banded_edit_visibility.cpp"
    original = EXECUTION.sha(
        MANIFEST.parent / "stale-column/banded_edit_visibility.cpp"
    )
    target.write_bytes(target.read_bytes() + b"\n")
    with pytest.raises(ValueError):
        EXECUTION.verify_manifest(path)
    assert (
        EXECUTION.sha(MANIFEST.parent / "stale-column/banded_edit_visibility.cpp")
        == original
    )


def test_closed_child_command_and_foreign_selection_rejected():
    root = Path("C:/fixture-external/build")
    command = EXECUTION.child_command(MANIFEST, root, "control")
    assert command[:4] == [str(EXECUTION.PYTHON), "-B", "-X", "faulthandler"]
    assert "--dll" not in command and command[-1] == "control"
    with pytest.raises(ValueError):
        EXECUTION.child_command(MANIFEST, root, "foreign.dll")


def test_new_records_use_explicit_utf8_lf(tmp_path):
    path = tmp_path / "record.json"
    EXECUTION.write_document(path, {"message": "fixture"})
    assert path.read_bytes() == b'{"message":"fixture"}\n'


@pytest.mark.parametrize("schema,authority", [(True, False), (1, 0), (1, True)])
def test_document_schema_and_authority_exact_types(schema, authority):
    import json

    with pytest.raises(ValueError):
        EXECUTION.decode_document(
            json.dumps(
                dict(
                    schema=schema,
                    training_authority=authority,
                    held_out_data_present=False,
                )
            ),
            {"schema", "training_authority", "held_out_data_present"},
        )


def _unit_rows(variant_id, status="survived", complete=True):
    """Synthetic structural UNIT input, never native execution evidence."""
    schedule = EXECUTION.generator().schedule(variant_id)
    cases = schedule if complete else schedule[:1]
    return [
        dict(
            observation=dict(variant_id=variant_id, case=case),
            status=status,
            workspace_guards_intact=True,
            no_write_contract_intact=True,
        )
        for case in cases
    ]


def test_unit_only_complete_control_and_nine_structure_admission():
    control = _unit_rows("control")
    assert EXECUTION.admit_completed_schedule("control", control) == "survived"
    for name in EXECUTION.IDS[1:]:
        rows = _unit_rows(name, "semantic-killed", False)
        assert EXECUTION.admit_completed_schedule(name, rows) == "semantic-killed"
    # Structural admission is not aggregate_verified_records and provides no
    # successful build, child exit, raw words, receipt or runtime provenance.


def test_unit_only_incomplete_or_reordered_control_schedule_rejected():
    rows = _unit_rows("control")
    with pytest.raises(ValueError):
        EXECUTION.admit_completed_schedule("control", rows[:-1])
    rows[0], rows[1] = rows[1], rows[0]
    with pytest.raises(ValueError):
        EXECUTION.admit_completed_schedule("control", rows)


def test_unit_only_later_kill_coverage_does_not_promote_corrupted_prefix():
    rows = _unit_rows("stale-column")[:2]
    rows[0]["status"] = "invariant-detected"
    rows[1]["status"] = "semantic-killed"
    assert EXECUTION.admit_completed_schedule("stale-column", rows) == "semantic-killed"
    rows[0]["no_write_contract_intact"] = False
    assert EXECUTION.admit_completed_schedule("stale-column", rows) == "canary-failed"


@pytest.mark.parametrize(
    "field", ["variant_id", "manifest_path", "manifest_sha256", "provenance"]
)
def test_unit_only_build_process_binding_mismatch(field):
    # This pure equality test does not replace verify_build/verify_provenance.
    build = dict(
        variant_id="control",
        manifest_path="unit",
        manifest_sha256="unit",
        provenance={"unit-only": True},
    )
    process = dict(build)
    EXECUTION.match_evidence_binding(process, build)
    process[field] = "changed"
    with pytest.raises(ValueError):
        EXECUTION.match_evidence_binding(process, build)
