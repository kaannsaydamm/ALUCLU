"""Bounded fixed-D transport, never model execution, provenance or authority.

Validate complete retained receipts, not absent tensor evidence. This module
imports no scientific runtime and opens no files or processes.
"""

import math
import re
import unicodedata
from dataclasses import dataclass

from .canonical import canonical_json_bytes, normalize_evidence_path, parse_canonical_json, sha256_bytes

REQUEST_LIMIT = 16384
RESULT_LIMIT = 4194304
_ROOT_FIELDS = (
    "declaration_root", "source_export_root", "runtime_inventory_root",
    "snapshot_inventory_root", "fixture_source_root", "invocation_root",
    "authority_generation_root", "original_entry_root", "clock_domain_root",
)
_CONTROLS = (
    "alc-r0-qualification-v1-d-cpu-fresh1-s20260916",
    "alc-r0-qualification-v1-d-gpu-fresh1-s20260916",
    "alc-r0-qualification-v1-d-gpu-fresh2-s20260916",
)
_REVISION = "93efa2f097d58c2a74874c7e644dbc9b0cee75a2"
_CELLS = tuple((f"{prefix}-r{rank}", ports, rank, arm)
               for prefix, ports in (("M", (14,)), ("L", (29,)), ("ML", (14, 29)))
               for rank in (4, 8, 16) for arm in ("capsule", "q_lora"))
_FORWARD = tuple((1, n, "none", explicit, False)
                 for n in (1, 8, 127, 512) for explicit in (False, True)) + tuple(
    (2, n, side, explicit, False) for n in (8, 127, 512)
    for side in ("left", "right") for explicit in (False, True)) + tuple(
    (1, n, "none", False, True) for n in (1, 8, 127, 512))
_STAGES = ("bootstrap_request", "bootstrap_binding", "bootstrap_inventory",
           "bootstrap_deadline", "worker_context", "tokenizer", "host",
           "official", "matrix", "terminal-assets", "worker_projection")


class DWireError(ValueError):
    """Invalid or oversized transport; no partial scientific acceptance."""


@dataclass(frozen=True)
class DRequest:
    data: bytes
    root: str


@dataclass(frozen=True)
class DResult:
    data: bytes
    root: str
    outcome: str


def _require(condition, message="invalid fixed D wire field"):
    if not condition:
        raise DWireError(message)


def _string_end(text, start):
    index, size = start + 1, 0
    while index < len(text):
        char = text[index]
        if char == '"':
            return index + 1
        _require(ord(char) >= 32, "invalid JSON string control")
        if char == "\\":
            index += 1
            _require(index < len(text), "unterminated JSON escape")
            char = text[index]
            if char == "u":
                digits = text[index + 1:index + 5]
                _require(re.fullmatch(r"[0-9A-Fa-f]{4}", digits) is not None,
                         "invalid Unicode escape")
                point = int(digits, 16)
                index += 4
                if 0xD800 <= point <= 0xDBFF:
                    _require(text[index + 1:index + 3] == "\\u", "unpaired surrogate")
                    low = text[index + 3:index + 7]
                    _require(re.fullmatch(r"[0-9A-Fa-f]{4}", low) is not None,
                             "invalid surrogate escape")
                    _require(0xDC00 <= int(low, 16) <= 0xDFFF, "unpaired surrogate")
                    index += 6
                    size += 4
                else:
                    _require(not 0xDC00 <= point <= 0xDFFF, "unpaired surrogate")
                    size += 1 if point < 128 else 2 if point < 2048 else 3
            else:
                _require(char in '\\"/bfnrt', "invalid JSON escape")
                size += 1
        else:
            point = ord(char)
            size += 1 if point < 128 else 2 if point < 2048 else 3 if point < 65536 else 4
        _require(size <= 4096, "string cap exceeded")
        index += 1
    raise DWireError("unterminated JSON string")


def _lexical_bounds(text):
    index, depth, tokens = 0, 0, 0
    while index < len(text):
        char = text[index]
        if char == '"':
            tokens += 1
            index = _string_end(text, index)
        elif char in "[{":
            tokens += 1
            depth += 1
            _require(depth <= 12, "depth cap exceeded")
            index += 1
        elif char in "]}":
            depth -= 1
            _require(depth >= 0, "unmatched JSON container")
            index += 1
        elif char in " ,:\t\r\n":
            index += 1
        else:
            tokens += 1
            index += 1
            while index < len(text) and text[index] not in '\"[]{} ,:\t\r\n':
                index += 1
        _require(tokens <= 100000, "token cap exceeded")
    _require(depth == 0, "unterminated JSON container")


def _bounded_json(data, limit):
    _require(type(data) is bytes and 0 < len(data) <= limit, "byte cap/type violation")
    try:
        _lexical_bounds(data.decode("utf-8", errors="strict"))
        return parse_canonical_json(data)
    except DWireError:
        raise
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError) as exc:
        raise DWireError("invalid canonical D transport") from exc


def _object(value, fields):
    _require(type(value) is dict and set(value) == set(fields), "exact object keys required")
    return value


def _array(value, size):
    _require(type(value) is list and len(value) == size, "fixed array size required")
    return value


def _integer(value, low=0, high=(1 << 63) - 1):
    _require(type(value) is str and len(value) <= 19 and
             re.fullmatch(r"0|[1-9][0-9]*", value) is not None, "decimal string required")
    number = int(value)
    _require(low <= number <= high, "integer range violation")
    return number


def _hash(value):
    _require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
             "canonical hash required")


def _measurement(value):
    _require(type(value) in (int, float), "finite measurement required")
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise DWireError("measurement overflow") from exc
    _require(math.isfinite(number), "finite measurement required")
    return number


def _path(value):
    _require(type(value) is str and value == unicodedata.normalize("NFC", value),
             "normalized absolute path required")
    _require(0 < len(value.encode("utf-8")) <= 4096 and "\\" not in value and
             not any(unicodedata.category(c) == "Cc" for c in value), "invalid path")
    windows = re.match(r"^[A-Za-z]:/", value) is not None
    _require(windows or (value.startswith("/") and not value.startswith("//")),
             "absolute local path required")
    parts = value[3 if windows else 1:].split("/")
    _require(all(part not in ("", ".", "..") for part in parts), "invalid path segments")
    if windows:
        try:
            normalize_evidence_path("/".join(parts))
        except ValueError as exc:
            raise DWireError("invalid Windows path") from exc


def _request(data):
    value = _object(_bounded_json(data, REQUEST_LIMIT), (
        "schema", "control_id", "reservation_id", *_ROOT_FIELDS,
        "useful_deadline_monotonic_ns", "snapshot_path"))
    _require(value["schema"] == "alc-r0-fixed-d-request-v1")
    _require(type(value["control_id"]) is str and value["control_id"] in _CONTROLS)
    _require(type(value["reservation_id"]) is str and
             re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value["reservation_id"]) is not None)
    for field in _ROOT_FIELDS:
        _hash(value[field])
    _integer(value["useful_deadline_monotonic_ns"], 1)
    _path(value["snapshot_path"])
    return value


def decode_d_request(data: bytes) -> DRequest:
    """Validate bounded transport syntax only; never construct a launch permit."""
    _request(data)
    return DRequest(data, sha256_bytes(data))


def _fixture(row, padded):
    _object(row, ("input_ids", "attention_mask", "labels", "position_ids",
                  "prompt_length", "candidate_ids"))
    _require(type(row["input_ids"]) is list and 3 <= len(row["input_ids"]) <= 71)
    size = len(row["input_ids"])
    numeric = {}
    for name, high in (("input_ids", 49151), ("attention_mask", 1), ("position_ids", 70)):
        numeric[name] = [_integer(x, 0, high) for x in _array(row[name], size)]
    numeric["labels"] = [-100 if x == "-100" else _integer(x, 0, 49151)
                         for x in _array(row["labels"], size)]
    candidate = row["candidate_ids"]
    _require(type(candidate) is list and 1 <= len(candidate) <= 64)
    numeric["candidate_ids"] = [_integer(x, 1, 49151) for x in candidate]
    prompt = numeric["prompt_length"] = _integer(row["prompt_length"], 1, 64)
    end = prompt + len(candidate)
    padding = 7 if padded else 0
    _require(size == end + padding and
             numeric["input_ids"][prompt:end] == numeric["candidate_ids"] and
             numeric["labels"] == [-100] * prompt + numeric["candidate_ids"] + [-100] * padding and
             numeric["attention_mask"] == [1] * end + [0] * padding and
             numeric["position_ids"] == list(range(size)))
    _require(not padding or numeric["input_ids"][-7:] == [0] * 7)
    return numeric


def _fixtures(value, req):
    _object(value, ("snapshot_inventory_sha256", "model_revision", "tokenizer_class",
                    "fixture_sha256", "fixtures"))
    _require(value["snapshot_inventory_sha256"] == req["snapshot_inventory_root"] and
             value["model_revision"] == _REVISION)
    name = value["tokenizer_class"]
    _require(type(name) is str and len(name) <= 256 and
             re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+", name) is not None)
    _hash(value["fixture_sha256"])
    rows = [_fixture(row, index >= 4)
            for index, row in enumerate(_array(value["fixtures"], 6))]
    candidates = [rows[0]["candidate_ids"], rows[1]["candidate_ids"]]
    _require(candidates[0] != candidates[1])
    for index, length in ((0, 32), (2, 64), (4, 71)):
        pair = rows[index:index + 2]
        prompt = pair[0]["prompt_length"]
        _require(max(len(row["input_ids"]) for row in pair) == length and
                 [row["candidate_ids"] for row in pair] == candidates and
                 pair[1]["prompt_length"] == prompt and
                 pair[0]["input_ids"][:prompt] == pair[1]["input_ids"][:prompt])
    for original, padded in zip(rows[2:4], rows[4:6], strict=True):
        _require(padded["input_ids"] == original["input_ids"] + [0] * 7)
    payload = dict(fixtures=rows, revision=_REVISION,
                   snapshot_inventory_sha256=value["snapshot_inventory_sha256"])
    _require(sha256_bytes(canonical_json_bytes(payload)) == value["fixture_sha256"],
             "original numeric fixture digest mismatch")


def _identity(value, identity):
    _require(all(value[field] == expected for field, expected in identity.items()),
             "qualification identity mismatch")


def _cell_key(value, cell):
    _object(value, ("grid_id", "ports", "rank", "arm"))
    grid, ports, rank, arm = cell
    _require(value["grid_id"] == grid and value["arm"] == arm and
             _integer(value["rank"]) == rank and
             tuple(_integer(x) for x in _array(value["ports"], len(ports))) == ports)


def _official(value, identity):
    _object(value, (*identity, "cases", "nonzero_witnesses"))
    _identity(value, identity)
    schedule = [(cell, phase, case) for cell in _CELLS
                for phase in ("unmounted", "zero", "detached") for case in _FORWARD]
    rows = _array(value["cases"], 1296)
    for row, (cell, phase, expected) in zip(rows, schedule, strict=True):
        _object(row, ("key", "case", "official_sha256", "wrapper_sha256",
                      "incremental_official_sha256", "incremental_wrapper_sha256"))
        _object(row["key"], ("grid_id", "arm", "phase"))
        _require(row["key"] == dict(grid_id=cell[0], arm=cell[3], phase=phase))
        case = _object(row["case"], ("batch", "length", "padding_side", "explicit_positions", "cached"))
        _require(type(case["explicit_positions"]) is bool and type(case["cached"]) is bool)
        actual = (_integer(case["batch"]), _integer(case["length"]), case["padding_side"],
                  case["explicit_positions"], case["cached"])
        _require(actual == expected)
        _hash(row["official_sha256"])
        _hash(row["wrapper_sha256"])
        if case["cached"]:
            _hash(row["incremental_official_sha256"])
            _hash(row["incremental_wrapper_sha256"])
        else:
            _require(row["incremental_official_sha256"] is None and
                     row["incremental_wrapper_sha256"] is None)
        if identity["source_device"] == "cpu":
            _require(row["official_sha256"] == row["wrapper_sha256"] and
                     row["incremental_official_sha256"] == row["incremental_wrapper_sha256"])
    for row, cell in zip(_array(value["nonzero_witnesses"], 18), _CELLS, strict=True):
        _object(row, ("grid_id", "arm", "official_sha256", "mounted_sha256"))
        _require(row["grid_id"] == cell[0] and row["arm"] == cell[3])
        _hash(row["official_sha256"])
        _hash(row["mounted_sha256"])
        _require(row["official_sha256"] != row["mounted_sha256"])


def _comparison(value, cpu):
    _object(value, ("reference_l2", "actual_l2", "difference_l2", "relative_l2", "cosine", "exact_zero"))
    ref, actual, diff = (_measurement(value[k]) for k in ("reference_l2", "actual_l2", "difference_l2"))
    _require(type(value["exact_zero"]) is bool and min(ref, actual, diff) >= 0)
    if value["exact_zero"]:
        _require(ref == actual == diff == 0 and value["relative_l2"] is None and value["cosine"] is None)
    else:
        relative, cosine = _measurement(value["relative_l2"]), _measurement(value["cosine"])
        _require(ref > 0 and actual > 0 and 0 <= relative <= 1e-5 and
                 1 - 1e-6 <= cosine <= 1 and (diff == 0) == (relative == 0))
        if cpu:
            _require(diff == relative == 0 and ref == actual)


def _pair(value):
    for number in _array(value, 2):
        _measurement(number)


def _matrix(value, identity):
    _object(value, (*identity, "seed", "cells"))
    _identity(value, identity)
    _require(_integer(value["seed"]) == 20260916)
    for row, cell in zip(_array(value["cells"], 18), _CELLS, strict=True):
        _object(row, ("key", "result"))
        _cell_key(row["key"], cell)
        result = _object(row["result"], ("cases", "pending_losses", "accumulation",
                                        "parameter_names", "parameter_count", "base_digest"))
        names = [f"factors.{port}.{role}" for port in cell[1] for role in ("A", "B")]
        _require(result["parameter_names"] == names and
                 _integer(result["parameter_count"]) == 1152 * cell[2] * len(cell[1]) and
                 result["base_digest"] == identity["base_digest"])
        for index, case in enumerate(_array(result["cases"], 18)):
            _object(case, ("state", "repeat", "fixture_index", "losses", "scores", "base_digest", "factor_digest"))
            state, repeat = (("zero", 0), ("nonzero", 0), ("nonzero", 1))[index // 6]
            _require(case["state"] == state and _integer(case["repeat"]) == repeat and
                     _integer(case["fixture_index"]) == index % 6 and case["base_digest"] == identity["base_digest"])
            _hash(case["factor_digest"])
            _pair(case["losses"])
            _pair(case["scores"])
        _pair(result["pending_losses"])
        accumulation = _object(result["accumulation"], ("step", "factors", "exp_avg", "exp_avg_sq"))
        _require(_integer(accumulation["step"]) == 1)
        for field in ("factors", "exp_avg", "exp_avg_sq"):
            for pair, name in zip(_array(accumulation[field], len(names)), names, strict=True):
                _array(pair, 2)
                _require(pair[0] == name)
                _comparison(pair[1], identity["source_device"] == "cpu")


def _qualification(value, req):
    _object(value, ("source_device", "source_dtype", "base_digest", "fixtures", "official", "matrix"))
    device, dtype = (("cpu", "torch.float32") if req["control_id"] == _CONTROLS[0]
                     else ("cuda:0", "torch.bfloat16"))
    _hash(value["base_digest"])
    identity = dict(source_device=device, source_dtype=dtype, base_digest=value["base_digest"])
    _identity(value, identity)
    _fixtures(value["fixtures"], req)
    _official(value["official"], identity)
    _matrix(value["matrix"], identity)


def decode_d_result(data: bytes, request: DRequest) -> DResult:
    """Validate complete retained evidence only; no OS or scientific acceptance."""
    _require(type(request) is DRequest, "DRequest transport required")
    req = _request(request.data)
    request_root = sha256_bytes(request.data)
    _require(request.root == request_root, "request byte root mismatch")
    value = _object(_bounded_json(data, RESULT_LIMIT), (
        "schema", "request_root", "control_id", "reservation_id", *_ROOT_FIELDS,
        "outcome", "qualification", "failure"))
    _require(value["schema"] == "alc-r0-fixed-d-result-v1" and value["request_root"] == request_root)
    _require(all(value[k] == req[k] for k in ("control_id", "reservation_id", *_ROOT_FIELDS)))
    outcome = value["outcome"]
    _require(type(outcome) is str and outcome in ("success", "error", "interrupted"))
    if outcome == "success":
        _require(value["failure"] is None)
        _qualification(value["qualification"], req)
    else:
        _require(value["qualification"] is None)
        failure = _object(value["failure"], ("stage", "category", "completed_evidence_root"))
        stage, category = failure["stage"], failure["category"]
        _require(type(stage) is str and stage in _STAGES and type(category) is str and
                 category in ("validation", "runtime", "oom", "interrupted"))
        _require((outcome == "interrupted") == (category == "interrupted") and
                 not (category == "oom" and stage.startswith("bootstrap_")))
        if failure["completed_evidence_root"] is not None:
            _hash(failure["completed_evidence_root"])
    return DResult(data, sha256_bytes(data), outcome)
