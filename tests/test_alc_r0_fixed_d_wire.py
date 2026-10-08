"""Synthetic fixed D transport only: no Torch, tokenizer, model or launch."""

import copy
import importlib
import subprocess
import sys
from dataclasses import FrozenInstanceError, asdict

import pytest

from aluclu.alc_r0.canonical import canonical_json_bytes, sha256_bytes
from aluclu.alc_r0.checkpoint_parity_inputs import parity_input


ROOT = "a" * 64
OTHER = "b" * 64
REVISION = "93efa2f097d58c2a74874c7e644dbc9b0cee75a2"
CONTROLS = (
    "alc-r0-qualification-v1-d-cpu-fresh1-s20260916",
    "alc-r0-qualification-v1-d-gpu-fresh1-s20260916",
    "alc-r0-qualification-v1-d-gpu-fresh2-s20260916",
)
ROOT_FIELDS = (
    "declaration_root", "source_export_root", "runtime_inventory_root",
    "snapshot_inventory_root", "fixture_source_root", "invocation_root",
    "authority_generation_root", "original_entry_root", "clock_domain_root",
)


def wire():
    return importlib.import_module("aluclu.alc_r0.fixed_d_wire")


def request(control=CONTROLS[0]):
    return dict(schema="alc-r0-fixed-d-request-v1", control_id=control,
                reservation_id="d-cpu-1", snapshot_path="C:/research/snapshot",
                useful_deadline_monotonic_ns="9223372036854775807",
                **dict.fromkeys(ROOT_FIELDS, ROOT))


def cells():
    return [dict(grid_id=f"{prefix}-r{rank}", ports=[str(p) for p in ports],
                 rank=str(rank), arm=arm)
            for prefix, ports in (("M", (14,)), ("L", (29,)), ("ML", (14, 29)))
            for rank in (4, 8, 16) for arm in ("capsule", "q_lora")]


def forward_cases():
    return [dict(batch="1", length=str(n), padding_side="none",
                 explicit_positions=explicit, cached=False)
            for n in (1, 8, 127, 512) for explicit in (False, True)] + [
                dict(batch="2", length=str(n), padding_side=side,
                     explicit_positions=explicit, cached=False)
                for n in (8, 127, 512) for side in ("left", "right")
                for explicit in (False, True)] + [
                dict(batch="1", length=str(n), padding_side="none",
                     explicit_positions=False, cached=True)
                for n in (1, 8, 127, 512)]


def token_fixtures():
    result = [asdict(parity_input(prefix_ids=(10, 11), suffix_ids=(12,),
                                 safe_ids=(13,), vulnerable_ids=(14, 15),
                                 eos_token_id=0, common_length=n,
                                 label=label, padded=padded))
              for n, padded in ((32, False), (64, False), (64, True))
              for label in ("safe", "vulnerable")]
    return [{key: list(value) if isinstance(value, tuple) else value
             for key, value in row.items()} for row in result]


def fixture_projection(numeric):
    digest = sha256_bytes(canonical_json_bytes(dict(fixtures=numeric,
                                                  revision=REVISION,
                                                  snapshot_inventory_sha256=ROOT)))
    projected = [{key: [str(x) for x in value] if isinstance(value, list)
                  else str(value) for key, value in row.items()} for row in numeric]
    return dict(snapshot_inventory_sha256=ROOT, model_revision=REVISION,
                tokenizer_class="transformers.example.TokenizerFast",
                fixture_sha256=digest, fixtures=projected)


def comparison(zero=False):
    return dict(reference_l2=0 if zero else 1, actual_l2=0 if zero else 1,
                difference_l2=0, relative_l2=None if zero else 0,
                cosine=None if zero else 1, exact_zero=zero)


def full_result(req):
    device, dtype = (("cpu", "torch.float32") if req["control_id"] == CONTROLS[0]
                     else ("cuda:0", "torch.bfloat16"))
    identity = dict(source_device=device, source_dtype=dtype, base_digest=ROOT)
    official_rows, witnesses, matrix_rows = [], [], []
    for cell in cells():
        for phase in ("unmounted", "zero", "detached"):
            for case in forward_cases():
                official_rows.append(dict(
                    key=dict(grid_id=cell["grid_id"], arm=cell["arm"], phase=phase),
                    case=case, official_sha256=ROOT, wrapper_sha256=ROOT,
                    incremental_official_sha256=ROOT if case["cached"] else None,
                    incremental_wrapper_sha256=ROOT if case["cached"] else None))
        witnesses.append(dict(grid_id=cell["grid_id"], arm=cell["arm"],
                              official_sha256=ROOT, mounted_sha256=OTHER))
        names = [f"factors.{p}.{role}" for p in cell["ports"] for role in ("A", "B")]
        rows = [dict(state=state, repeat=str(repeat), fixture_index=str(i),
                     losses=[1, 1], scores=[-1, -1], base_digest=ROOT, factor_digest=OTHER)
                for state, repeat in (("zero", 0), ("nonzero", 0), ("nonzero", 1))
                for i in range(6)]
        accum = dict(step="1", **{key: [[name, comparison()] for name in names]
                                  for key in ("factors", "exp_avg", "exp_avg_sq")})
        matrix_rows.append(dict(key=cell, result=dict(
            cases=rows, pending_losses=[1, 1], accumulation=accum,
            parameter_names=names,
            parameter_count=str(1152 * int(cell["rank"]) * len(cell["ports"])),
            base_digest=ROOT)))
    qualification = dict(**identity, fixtures=fixture_projection(token_fixtures()),
                         official=dict(**identity, cases=official_rows,
                                       nonzero_witnesses=witnesses),
                         matrix=dict(**identity, seed="20260916", cells=matrix_rows))
    return dict(schema="alc-r0-fixed-d-result-v1",
                request_root=sha256_bytes(canonical_json_bytes(req)),
                control_id=req["control_id"], reservation_id=req["reservation_id"],
                **{key: req[key] for key in ROOT_FIELDS},
                outcome="success", qualification=qualification, failure=None)


def decode_result(value, req=None):
    req = request() if req is None else req
    module = wire()
    view = module.decode_d_request(canonical_json_bytes(req))
    return module.decode_d_result(canonical_json_bytes(value), view)


@pytest.mark.parametrize("control", CONTROLS)
def test_complete_fixed_schedule_roundtrip(control):
    req = request(control)
    result = full_result(req)
    data = canonical_json_bytes(result)
    assert len(result["qualification"]["official"]["cases"]) == 1296
    assert len(data) < 4 * 1024 * 1024
    view = decode_result(result, req)
    assert view.data == data
    assert view.root == sha256_bytes(data)
    with pytest.raises(FrozenInstanceError):
        view.data = b"{}"


@pytest.mark.parametrize("key", tuple(request()))
def test_missing_request_field_denies(key):
    value = request()
    del value[key]
    with pytest.raises(wire().DWireError):
        wire().decode_d_request(canonical_json_bytes(value))


@pytest.mark.parametrize("key,value", [
    ("control_id", {}), ("control_id", CONTROLS[0] + "-retry"),
    ("reservation_id", "../d"), ("snapshot_path", "relative/a"),
    ("snapshot_path", "C:/a/../b"), ("snapshot_path", "C:/NUL/x"),
    ("snapshot_path", "C:/a. /x"), ("snapshot_path", "//host/a"),
    ("snapshot_path", "C:\\a\\b"), ("snapshot_path", "/a/"),
    ("useful_deadline_monotonic_ns", 1), ("useful_deadline_monotonic_ns", True),
    ("useful_deadline_monotonic_ns", "0"), ("useful_deadline_monotonic_ns", "01"),
    ("useful_deadline_monotonic_ns", "9223372036854775808"),
    ("declaration_root", ROOT.upper()), ("fixture_source_root", None),
])
def test_invalid_request_values_deny(key, value):
    req = request()
    req[key] = value
    with pytest.raises(wire().DWireError):
        wire().decode_d_request(canonical_json_bytes(req))


@pytest.mark.parametrize("path", ["/research/\u0085snapshot", "C:/research/\u009fsnapshot"])
def test_c1_controls_in_path_deny(path):
    req = request()
    req["snapshot_path"] = path
    with pytest.raises(wire().DWireError):
        wire().decode_d_request(canonical_json_bytes(req))


@pytest.mark.parametrize("outcome,category", [("error", "validation"),
                                              ("error", "runtime"), ("error", "oom"),
                                              ("interrupted", "interrupted")])
def test_closed_failure_receipt_is_transport_only(outcome, category):
    result = full_result(request())
    result.update(outcome=outcome, qualification=None,
                  failure=dict(stage="matrix", category=category,
                               completed_evidence_root=None))
    assert decode_result(result).outcome == outcome


MUTATIONS = [
    ("request_root", OTHER), ("declaration_root", OTHER), ("outcome", "PASS"),
    ("failure", {}), ("qualification.source_device", "cuda:0"),
    ("qualification.fixtures.fixture_sha256", OTHER),
    ("qualification.fixtures.model_revision", OTHER),
    ("qualification.fixtures.fixtures.0.labels.0", "100"),
    ("qualification.fixtures.fixtures.0.position_ids.0", "1"),
    ("qualification.fixtures.fixtures.0.input_ids.0", "49152"),
    ("qualification.fixtures.fixtures.0.attention_mask.0", True),
    ("qualification.official.cases.0.key.phase", "zero"),
    ("qualification.official.cases.0.case.explicit_positions", "false"),
    ("qualification.official.cases.0.wrapper_sha256", OTHER),
    ("qualification.official.cases.0.incremental_official_sha256", ROOT),
    ("qualification.official.cases.20.incremental_wrapper_sha256", None),
    ("qualification.official.nonzero_witnesses.0.mounted_sha256", ROOT),
    ("qualification.matrix.seed", "20260917"),
    ("qualification.matrix.cells.0.key.rank", "8"),
    ("qualification.matrix.cells.0.result.parameter_count", "1"),
    ("qualification.matrix.cells.0.result.parameter_names.0", "factors.29.A"),
    ("qualification.matrix.cells.0.result.cases.0.factor_digest", "bad"),
    ("qualification.matrix.cells.0.result.cases.0.losses.0", True),
    ("qualification.matrix.cells.0.result.cases.6.repeat", "1"),
    ("qualification.matrix.cells.0.result.accumulation.step", "2"),
    ("qualification.matrix.cells.0.result.accumulation.factors.0.0", "factors.29.A"),
]


def mutate(value, path, replacement):
    pieces = path.split(".")
    for piece in pieces[:-1]:
        value = value[int(piece)] if isinstance(value, list) else value[piece]
    last = int(pieces[-1]) if isinstance(value, list) else pieces[-1]
    value[last] = replacement


@pytest.mark.parametrize("path,replacement", MUTATIONS)
def test_field_mutations_fail_closed(path, replacement):
    result = full_result(request())
    mutate(result, path, replacement)
    with pytest.raises(wire().DWireError):
        decode_result(result)


@pytest.mark.parametrize("path", ["qualification", "qualification.fixtures",
                                  "qualification.official", "qualification.matrix",
                                  "qualification.matrix.cells.0.result"])
def test_extra_nested_field_denies(path):
    result = full_result(request())
    value = result
    for piece in path.split("."):
        value = value[int(piece)] if isinstance(value, list) else value[piece]
    value["extra"] = None
    with pytest.raises(wire().DWireError):
        decode_result(result)


@pytest.mark.parametrize("field,replacement", [
    ("exact_zero", 1), ("exact_zero", True), ("reference_l2", 0),
    ("actual_l2", -1), ("difference_l2", -1), ("relative_l2", None),
    ("relative_l2", 0.001), ("cosine", None), ("cosine", 0.99),
    ("cosine", 1.00001),
])
def test_tensor_comparison_mutations_deny(field, replacement):
    result = full_result(request())
    comp = result["qualification"]["matrix"]["cells"][0]["result"]["accumulation"]["factors"][0][1]
    comp[field] = replacement
    with pytest.raises(wire().DWireError):
        decode_result(result)


def test_null_zero_comparison_and_roundoff_cosine_are_preserved():
    result = full_result(request())
    comp = result["qualification"]["matrix"]["cells"][0]["result"]["accumulation"]["factors"]
    comp[0][1] = comparison(zero=True)
    comp[1][1]["cosine"] = 0.9999999999999999
    assert decode_result(result).outcome == "success"


def test_gpu_retained_tolerance_is_not_hash_equality():
    req = request(CONTROLS[1])
    result = full_result(req)
    result["qualification"]["official"]["cases"][0]["wrapper_sha256"] = OTHER
    comp = result["qualification"]["matrix"]["cells"][0]["result"]["accumulation"]["factors"][0][1]
    comp.update(difference_l2=1e-6, relative_l2=1e-6, cosine=0.9999995)
    assert decode_result(result, req).outcome == "success"


def test_full_schedule_large_finite_scalar_and_metadata_cap_projection():
    req = request(CONTROLS[2])
    req["snapshot_path"] = "/" + '"' * 4095
    result = full_result(req)
    result["qualification"]["fixtures"]["tokenizer_class"] = "a" * 254 + ".B"
    large_spelling = 1.2345678901234567e-300
    for row in result["qualification"]["matrix"]["cells"]:
        for case in row["result"]["cases"]:
            case["losses"] = [large_spelling, large_spelling]
            case["scores"] = [-large_spelling, -large_spelling]
        row["result"]["pending_losses"] = [large_spelling, large_spelling]
        for field in ("factors", "exp_avg", "exp_avg_sq"):
            for pair in row["result"]["accumulation"][field]:
                pair[1].update(reference_l2=large_spelling, actual_l2=large_spelling,
                               cosine=0.9999999999999999)
    data = canonical_json_bytes(result)
    assert len(data) < 4 * 1024 * 1024
    assert decode_result(result, req).data == data


@pytest.mark.parametrize("path", ["qualification.official.cases",
                                  "qualification.official.nonzero_witnesses",
                                  "qualification.matrix.cells",
                                  "qualification.matrix.cells.0.result.cases",
                                  "qualification.matrix.cells.0.result.accumulation.factors"])
def test_missing_scheduled_row_denies(path):
    result = full_result(request())
    value = result
    for piece in path.split("."):
        value = value[int(piece)] if isinstance(value, list) else value[piece]
    value.pop()
    with pytest.raises(wire().DWireError):
        decode_result(result)


@pytest.mark.parametrize("changes", [dict(stage="unknown"), dict(category="PASS"),
                                      dict(stage="bootstrap_binding", category="oom"),
                                      dict(category="interrupted"),
                                      dict(completed_evidence_root=False)])
def test_invalid_failure_record_denies(changes):
    result = full_result(request())
    failure = dict(stage="matrix", category="runtime", completed_evidence_root=None)
    failure.update(changes)
    result.update(outcome="error", qualification=None, failure=failure)
    with pytest.raises(wire().DWireError):
        decode_result(result)


def test_original_short_fixture_schedule_rejected_even_with_matching_hash():
    numeric = []
    for size, padded in ((32, False), (64, False), (64, True)):
        prompt = [10] * (size - 31)
        for candidate in ([13], [14] * 31):
            sequence = prompt + candidate
            padding = 7 if padded else 0
            numeric.append(dict(input_ids=sequence + [0] * padding,
                                labels=[-100] * len(prompt) + candidate + [-100] * padding,
                                attention_mask=[1] * len(sequence) + [0] * padding,
                                position_ids=list(range(len(sequence) + padding)),
                                prompt_length=len(prompt), candidate_ids=candidate))
    assert len(numeric[0]["input_ids"]) == 2
    result = full_result(request())
    result["qualification"]["fixtures"] = fixture_projection(numeric)
    with pytest.raises(wire().DWireError):
        decode_result(result)


@pytest.mark.parametrize("data", [b"", b"\xff", b"\xef\xbb\xbf{}", b'{"a":1,"a":2}',
                                  b'{"x":NaN}', b'{"x":1.0}', b'{}\n', b'{"x":"\\q"}',
                                  b'{"x":"\\ud800"}', b'{"x":"\\udc00"}',
                                  b"[" * 13 + b"0" + b"]" * 13])
def test_malformed_or_noncanonical_data_denies(data):
    with pytest.raises(wire().DWireError):
        wire().decode_d_request(data)


def test_preparse_caps_include_empty_containers_and_strings():
    module = wire()
    for data in (b"[" + b"[]," * 100000 + b"[]]",
                 b"[" + b"0," * 100000 + b"0]",
                 b'{"x":"' + b"a" * 4097 + b'"}'):
        with pytest.raises(module.DWireError, match="cap"):
            module._bounded_json(data, module.RESULT_LIMIT)
    assert module._bounded_json(b"[" + b"[]," * 99998 + b"[]]", module.RESULT_LIMIT)
    assert module._bounded_json(canonical_json_bytes({"x": "a" * 4096}), module.RESULT_LIMIT)
    assert module._bounded_json(canonical_json_bytes({"x": "😀" * 1024}), module.RESULT_LIMIT)
    with pytest.raises(module.DWireError, match="cap"):
        module._bounded_json(canonical_json_bytes({"x": "😀" * 1025}), module.RESULT_LIMIT)


def test_escaped_delimiters_and_surrogates_do_not_bypass_scan():
    module = wire()
    assert module._bounded_json(canonical_json_bytes({"x": '\\"[{}]'}), module.RESULT_LIMIT)
    with pytest.raises(module.DWireError):
        module._bounded_json(b'{"x":"\\ud83d\\ude00"}', module.RESULT_LIMIT)
    with pytest.raises(module.DWireError, match="cap"):
        module._bounded_json(b'{"x":"' + b"\\u0061" * 4097 + b'"}', module.RESULT_LIMIT)


def test_byte_type_and_limit_rejected_before_parse():
    module = wire()
    for value in (bytearray(b"{}"), "{}", b"x" * 16385):
        with pytest.raises(module.DWireError):
            module.decode_d_request(value)
    with pytest.raises(module.DWireError):
        module._bounded_json(b"x" * (module.RESULT_LIMIT + 1), module.RESULT_LIMIT)


def test_forged_request_view_does_not_supply_bindings():
    module = wire()
    req = module.decode_d_request(canonical_json_bytes(request()))
    fake = copy.copy(req)
    object.__setattr__(fake, "data", b"{}")
    with pytest.raises(module.DWireError):
        module.decode_d_result(canonical_json_bytes(full_result(request())), fake)


def test_import_has_no_heavy_runtime_dependency():
    code = ("import sys; import aluclu.alc_r0.fixed_d_wire; "
            "assert not any(n.split('.')[0] in {'torch','transformers','numpy'} for n in sys.modules)")
    completed = subprocess.run([sys.executable, "-c", code], capture_output=True,
                               text=True, timeout=10, check=False)
    assert completed.returncode == 0, completed.stderr
