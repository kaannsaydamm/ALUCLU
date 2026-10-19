"""Exact synthetic scientific receipts, never a host/GPU/qualification run."""

import copy
import importlib
import subprocess
import sys
from dataclasses import replace

import pytest

from aluclu.alc_r0.canonical import canonical_json_bytes, parse_canonical_json
from aluclu.alc_r0.checkpoint_fidelity import TensorComparison
from aluclu.alc_r0.checkpoint_official_forward import (
    ForwardCase, OfficialKey, OfficialCase, NonzeroWitness, OfficialSuite,
)
from aluclu.alc_r0.checkpoint_optimizer import AdamWComparison
from aluclu.alc_r0.checkpoint_parity_cell import CaseComparison, ParityCell
from aluclu.alc_r0.checkpoint_parity_inputs import ParityInput
from aluclu.alc_r0.checkpoint_parity_matrix import CellKey, MatrixCell, ParityMatrix
from aluclu.alc_r0.checkpoint_parity_qualification import ParityQualification
from aluclu.alc_r0.checkpoint_parity_tokenizer import TokenizedParityFixtures
from aluclu.alc_r0.fixed_d_wire import DRequest, DWireError, decode_d_request
from test_alc_r0_fixed_d_wire import CONTROLS, ROOT, full_result, request, token_fixtures


def projection():
    return importlib.import_module("aluclu.alc_r0.fixed_d_projection")


def scientific(expected):
    """Independently reconstruct exact original receipt types from test schema."""
    q = expected["qualification"]
    f, o, m = q["fixtures"], q["official"], q["matrix"]
    fixtures = tuple(ParityInput(**{k: tuple(v) if type(v) is list else v
                                   for k, v in row.items()}) for row in token_fixtures())
    tokenized = TokenizedParityFixtures(f["snapshot_inventory_sha256"],
                                       f["model_revision"], f["tokenizer_class"],
                                       f["fixture_sha256"], fixtures)
    official = OfficialSuite(o["source_device"], o["source_dtype"], o["base_digest"], tuple(
        OfficialCase(OfficialKey(**row["key"]), ForwardCase(
            int(row["case"]["batch"]), int(row["case"]["length"]),
            row["case"]["padding_side"], row["case"]["explicit_positions"],
            row["case"]["cached"]), row["official_sha256"], row["wrapper_sha256"],
            row["incremental_official_sha256"], row["incremental_wrapper_sha256"])
        for row in o["cases"]), tuple(NonzeroWitness(**row) for row in o["nonzero_witnesses"]))
    cells = []
    for row in m["cells"]:
        k, r = row["key"], row["result"]
        key = CellKey(k["grid_id"], tuple(map(int, k["ports"])), int(k["rank"]), k["arm"])
        a = r["accumulation"]
        named = []
        for field in ("factors", "exp_avg", "exp_avg_sq"):
            named.append(tuple((name, TensorComparison(**{
                key: value if value is None or type(value) is bool else float(value)
                for key, value in c.items()})) for name, c in a[field]))
        accumulation = AdamWComparison(int(a["step"]), *named)
        cases = tuple(CaseComparison(c["state"], int(c["repeat"]), int(c["fixture_index"]),
                                     tuple(map(float, c["losses"])), tuple(map(float, c["scores"])),
                                     c["base_digest"], c["factor_digest"]) for c in r["cases"])
        result = ParityCell(cases, tuple(map(float, r["pending_losses"])), accumulation,
                            tuple(r["parameter_names"]), int(r["parameter_count"]), r["base_digest"])
        cells.append(MatrixCell(key, result))
    matrix = ParityMatrix(m["source_device"], m["source_dtype"], int(m["seed"]),
                          m["base_digest"], tuple(cells))
    return ParityQualification(q["source_device"], q["source_dtype"], q["base_digest"],
                               tokenized, official, matrix)


def fixture(control=CONTROLS[0]):
    req = request(control)
    expected = full_result(req)
    return decode_d_request(canonical_json_bytes(req)), expected, scientific(expected)


@pytest.mark.parametrize("control", CONTROLS)
def test_complete_scientific_roundtrip(control):
    req, expected, value = fixture(control)
    before = copy.deepcopy(value)
    result = projection().encode_d_success(value, req)
    assert result.data == canonical_json_bytes(expected)
    assert result.outcome == "success"
    assert len(result.data) < 4194304
    assert value == before


@pytest.mark.parametrize("field", ("factors", "exp_avg", "exp_avg_sq"))
def test_zero_and_gpu_nonzero_comparisons_preserved(field):
    req, expected, _ = fixture(CONTROLS[1])
    pairs = expected["qualification"]["matrix"]["cells"][0]["result"]["accumulation"][field]
    pairs[0][1].update(reference_l2=0, actual_l2=0, difference_l2=0,
                       relative_l2=None, cosine=None, exact_zero=True)
    pairs[1][1].update(reference_l2=2, actual_l2=2.000001, difference_l2=1e-6,
                       relative_l2=5e-7, cosine=0.9999999, exact_zero=False)
    result = projection().encode_d_success(scientific(expected), req)
    assert result.data == canonical_json_bytes(expected)


@pytest.mark.parametrize("category", ("validation", "runtime", "oom", "interrupted"))
def test_closed_failure(category):
    req, _, _ = fixture()
    result = projection().encode_d_failure(req, stage="host", category=category)
    value = parse_canonical_json(result.data)
    assert result.outcome == ("interrupted" if category == "interrupted" else "error")
    assert value["qualification"] is None
    assert value["failure"] == dict(stage="host", category=category, completed_evidence_root=None)


@pytest.mark.parametrize("stage,category", (("whatever", "runtime"), ("host", "whatever"),
                                          ("bootstrap_request", "oom"), (True, "runtime"),
                                          ("host", "x" * 10000)))
def test_invalid_failure_denies(stage, category):
    req, _, _ = fixture()
    with pytest.raises(DWireError):
        projection().encode_d_failure(req, stage=stage, category=category)


def mutate(value, route, replacement):
    if not route:
        return replacement
    key, *tail = route
    if type(key) is int:
        rows = list(value)
        rows[key] = mutate(rows[key], tail, replacement)
        return tuple(rows)
    return replace(value, **{key: mutate(getattr(value, key), tail, replacement)})


@pytest.mark.parametrize("route,replacement", [
    ((), {}), (("source_device",), "cuda:0"), (("base_digest",), "b" * 64),
    (("fixtures", "tokenizer_class"), "x" * 10000),
    (("fixtures", "tokenizer_class"), "a.\ud800"),
    (("fixtures", "fixtures"), ()), (("fixtures", "fixtures", 0, "input_ids"), (1,) * 10000),
    (("fixtures", "fixtures", 0, "prompt_length"), True),
    (("fixtures", "fixtures", 0, "labels", 0), -101),
    (("fixtures", "fixture_sha256"), "b" * 64),
    (("official", "cases"), ()), (("official", "nonzero_witnesses"), ()),
    (("official", "cases", 0, "key"), {}),
    (("official", "cases", 0, "case", "cached"), 0),
    (("official", "cases", 0, "case", "batch"), True),
    (("official", "cases", 0, "case", "length"), 1 << 10000),
    (("official", "cases", 0, "official_sha256"), "x" * 10000),
    (("official", "cases", 0, "incremental_official_sha256"), ROOT),
    (("matrix", "cells"), ()), (("matrix", "seed"), 20260917),
    (("matrix", "cells", 0, "key", "ports"), (14,) * 10000),
    (("matrix", "cells", 0, "result", "cases"), ()),
    (("matrix", "cells", 0, "result", "cases", 0, "losses"), (True, 1.0)),
    (("matrix", "cells", 0, "result", "cases", 0, "scores"), (1, 1.0)),
    (("matrix", "cells", 0, "result", "pending_losses"), (float("nan"), 1.0)),
    (("matrix", "cells", 0, "result", "parameter_names"), ("x" * 10000, "other")),
    (("matrix", "cells", 0, "result", "accumulation", "step"), "1"),
    (("matrix", "cells", 0, "result", "accumulation", "factors"), ()),
    (("matrix", "cells", 0, "result", "accumulation", "factors", 0, 1, "exact_zero"), 0),
    (("matrix", "cells", 0, "result", "accumulation", "factors", 0, 1, "relative_l2"), 1e-3),
    (("matrix", "cells", 0, "result", "accumulation", "factors", 0, 1, "cosine"), None),
])
def test_malformed_scientific_fields_deny(route, replacement):
    req, _, value = fixture()
    with pytest.raises(DWireError):
        projection().encode_d_success(mutate(value, route, replacement), req)


def test_lookalike_and_hook_types_never_converted():
    req, _, value = fixture()

    class Trap:
        def __str__(self):
            raise AssertionError("conversion hook invoked")
        def __iter__(self):
            raise AssertionError("iteration hook invoked")

    class Text(str):
        def __len__(self):
            raise AssertionError("string subclass hook invoked")

    for route, replacement in ((("base_digest",), Trap()),
                               (("fixtures", "tokenizer_class"), Text("a.b")),
                               (("official", "cases"), Trap())):
        with pytest.raises(DWireError):
            projection().encode_d_success(mutate(value, route, replacement), req)

    class Receipt(ParityQualification):
        pass

    subclass = Receipt(value.source_device, value.source_dtype, value.base_digest,
                       value.fixtures, value.official, value.matrix)
    with pytest.raises(DWireError):
        projection().encode_d_success(subclass, req)


def test_light_import_failure_and_forged_request_before_heavy_import():
    script = '''
import importlib.abc, sys
class Deny(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'torch', 'transformers', 'numpy'}:
            raise AssertionError('heavy import before denial')
sys.meta_path.insert(0, Deny())
from aluclu.alc_r0.fixed_d_projection import encode_d_success, encode_d_failure
from aluclu.alc_r0.fixed_d_wire import DRequest, DWireError, decode_d_request
from aluclu.alc_r0.canonical import canonical_json_bytes
req = decode_d_request(canonical_json_bytes(REQUEST))
assert encode_d_failure(req, stage='host', category='runtime').outcome == 'error'
for forged in (DRequest(req.data, 'b'*64), DRequest(b'{}', req.root), object()):
    try: encode_d_success(object(), forged)
    except DWireError: pass
    else: raise AssertionError('forged request accepted')
assert not {'torch','transformers','numpy'}.intersection(sys.modules)
print('light-projection-ok')
'''.replace("REQUEST", repr(request()))
    completed = subprocess.run((sys.executable, "-c", script), capture_output=True,
                               text=True, timeout=30, check=False)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert completed.stdout.strip() == "light-projection-ok"
    assert completed.stderr == ""


def test_receipt_construction_did_not_initialize_cuda():
    import torch
    assert not torch.cuda.is_initialized()
