"""Closed fixture-only native mutation source generator and pure classifier.

This stage never compiles or loads artifacts. A reviewed isolated build/loader
stage must consume the generated manifest before native mutation evidence exists.
"""

import argparse
import hashlib
import json
import re
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_SHA256 = "c577846b7f5de113230b89224d96a707eceecaf7659cad2b316d2138201f96ad"
REFERENCE_SHA256 = "dff2a30af16daa97dd0acd1ab39fe89403b35b6a4b181c95f7bf5db21f707f8d"
PLAN_SHA256 = "0cac0b1ac5f70bc7a3167a43d232672d90aed5eec168d0bd1fd150380fa3e3f3"
BASELINE_COMMIT = "d739a35dc7d184c77fec893a22c972fb5d40cf34"
PROBE_SHA256 = "e3c90674dcaa0927e661a2b240d1a9773a71d03e6999c3a48f2ca3f1b05365f1"
DETAIL_PLAN_SHA256 = "9d7e992ac31f03ca2953a82a9f250cb10c464b69e017516a93944e2a8024fb72"
MUTATION_IDS = (
    "drop-equal-indel-ties",
    "single-predecessor",
    "strip-equal-ends",
    "marginal-total",
    "marginal-joint",
    "inward-parity",
    "exclude-boundary",
    "stale-column",
    "accept-over-threshold",
)
_TIE = "const Candidate& pred=candidates[c]; if(pred.cost!=distance) continue;"
_PUBLISH = "        out[7]|=32;out[19]=distance;\n"
_STALE = "            if(i && prev_low<=j && j<=prev_high && previous[j-prev_low]<inf)\n                candidates[count++]={previous[j-prev_low]+1,previous,uint32_t(j-prev_low),2};"
_SUBSTITUTIONS = {
    "drop-equal-indel-ties": (
        _TIE,
        _TIE + " if(pred.operation && i && j && first[i-1]==second[j-1]) continue;",
    ),
    "single-predecessor": (
        "            current[col]=distance;\n",
        "            current[col]=distance;\n            for(uint32_t c=0;c<count;++c) if(candidates[c].cost==distance) { candidates[0]=candidates[c]; count=1; break; }\n",
    ),
    "strip-equal-ends": (
        "    uint32_t reason=0, width=0; uint64_t cells=0, payload=0, scratch=0;\n",
        "    while(n && m && first[0]==second[0]) { ++first; ++second; --n; --m; }\n    while(n && m && first[n-1]==second[m-1]) { --n; --m; }\n    uint32_t reason=0, width=0; uint64_t cells=0, payload=0, scratch=0;\n",
    ),
    "marginal-total": (
        _PUBLISH,
        _PUBLISH
        + "        for(uint32_t b=0;b<B;++b) { uint64_t s=uint64_t(1+7*b)*width; previous[s+4*width+terminal]=previous[s+terminal]+previous[s+2*width+terminal]; previous[s+5*width+terminal]=previous[s+width+terminal]+previous[s+3*width+terminal]; }\n",
    ),
    "marginal-joint": (
        _PUBLISH,
        _PUBLISH
        + "        for(uint32_t b=0;b<B;++b) { uint64_t s=uint64_t(1+7*b)*width; previous[s+6*width+terminal]=1u << ((previous[s+width+terminal]?2u:0u) | (previous[s+3*width+terminal]?1u:0u)); }\n",
    ),
    "inward-parity": (
        "        lower=-floor2(int(K)-delta); upper=floor2(delta+int(K));\n",
        "        lower=-floor2(int(K)-delta); upper=floor2(delta+int(K));\n        if((int(K)-delta)%2) { ++lower; --upper; }\n",
    ),
    "exclude-boundary": (
        "            Candidate candidates[3]; uint32_t count=0;\n",
        "            if(j==high) continue;\n            Candidate candidates[3]; uint32_t count=0;\n",
    ),
    "stale-column": (
        _STALE,
        "            if(i && prev_low<=j && j<=prev_high && j-low>=0 && uint32_t(j-low)<width && previous[j-low]<inf)\n                candidates[count++]={previous[j-low]+1,previous,uint32_t(j-low),2};",
    ),
    "accept-over-threshold": (
        "    if(distance>K) {out[1]=1;out[2]=2;}\n",
        "    if(false) {out[1]=1;out[2]=2;}\n",
    ),
}
_WITNESSES = {
    "drop-equal-indel-ties": ((7,), (7, 7), 1),
    "single-predecessor": ((1, 2), (2, 1), 2),
    "strip-equal-ends": ((7,), (7, 7), 1),
    "marginal-total": ((1, 2), (2, 1), 2),
    "marginal-joint": ((1, 2), (2, 1), 2),
    "inward-parity": ((1,), (1,), 1),
    "exclude-boundary": ((1,), (1,), 0),
    "accept-over-threshold": ((1,), (2,), 0),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _case(value):
    if type(value) not in (tuple, list) or len(value) != 3:
        raise ValueError("exact three-field fixture required")
    first, second, K = value
    if (
        any(
            type(endpoint) not in (tuple, list)
            or any(type(token) is not int or token < 0 for token in endpoint)
            for endpoint in (first, second)
        )
        or type(K) is not int
        or K < 0
    ):
        raise ValueError("exact nonnegative fixture integers required")
    return tuple(first), tuple(second), K


def fixed_grid():
    sequences = [s for n in range(4) for s in product((0, 1), repeat=n)]
    return tuple(
        (a, b, k)
        for a in sequences
        for b in sequences
        for k in range(len(a) + len(b) + 2)
    )


def schedule(variant_id):
    if type(variant_id) is not str or variant_id not in ("control", *MUTATION_IDS):
        raise ValueError("unknown closed variant")
    grid = fixed_grid()
    if variant_id == "control":
        witnesses = tuple(dict.fromkeys(_WITNESSES.values()))
        return witnesses + tuple(case for case in grid if case not in witnesses)
    if variant_id in ("inward-parity", "stale-column"):
        witness = _WITNESSES.get(variant_id)
        return ((witness,) if witness else ()) + tuple(
            case for case in grid if case != witness
        )
    return (_WITNESSES[variant_id],)


def generate_variants(baseline):
    if type(baseline) is not bytes or digest(baseline) != BASELINE_SHA256:
        raise ValueError("reviewed exact baseline bytes required")
    variants = {
        "control": dict(
            source_bytes=baseline,
            source_sha256=digest(baseline),
            old_bytes=b"",
            new_bytes=b"",
        )
    }
    for variant_id in MUTATION_IDS:
        old, new = (part.encode("ascii") for part in _SUBSTITUTIONS[variant_id])
        if baseline.count(old) != 1:
            raise ValueError("mutation anchor must occur exactly once: " + variant_id)
        changed = baseline.replace(old, new, 1)
        variants[variant_id] = dict(
            source_bytes=changed,
            source_sha256=digest(changed),
            old_bytes=old,
            new_bytes=new,
        )
    return variants


def _oracle(first, second):
    paths = []

    def visit(i, j, d, left, right):
        if i == len(first) and j == len(second):
            paths.append((d, left, right))
            return
        if i < len(first) and j < len(second) and first[i] == second[j]:
            visit(i + 1, j + 1, d, left, right)
        if i < len(first):
            visit(i + 1, j, d + 1, left + int(i == 0), right)
        if j < len(second):
            visit(i, j + 1, d + 1, left, right + int(j == 0))

    visit(0, 0, 0, 0, 0)
    distance = min(p[0] for p in paths)
    best = [p for p in paths if p[0] == distance]
    left, right, totals = (
        [p[1] for p in best],
        [p[2] for p in best],
        [p[1] + p[2] for p in best],
    )
    bits = sum(1 << s for s in {(2 if p[1] else 0) | (1 if p[2] else 0) for p in best})
    return distance, (
        min(left),
        max(left),
        min(right),
        max(right),
        min(totals),
        max(totals),
        bits,
    )


def expected_words(case):
    from aluclu.alc_r0.banded_edit_token_visibility_reference import (
        audit_banded_edit_token_visibility,
    )

    case = _case(case)
    first, second, K = case
    if case not in schedule("control"):
        raise ValueError("case outside frozen schedule")
    reference = ROOT / "src/aluclu/alc_r0/banded_edit_token_visibility_reference.py"
    if digest(reference.read_bytes()) != REFERENCE_SHA256:
        raise ValueError("reference identity changed")
    result = audit_banded_edit_token_visibility(
        first, second, code_budgets=(1,), distance_threshold=K
    )
    distance, states = _oracle(first, second)
    if distance <= K:
        if (
            result.edit_distance != distance
            or tuple(vars(result.budgets[0]).values())[1:] != states
        ):
            raise ValueError("reference/independent oracle disagreement")
    elif result.edit_distance is not None or result.budgets:
        raise ValueError("reference/independent threshold disagreement")
    cells = [
        (i, j)
        for i in range(len(first) + 1)
        for j in range(len(second) + 1)
        if abs(i - j) + abs(len(first) - len(second) - i + j) <= K
    ]
    if K < abs(len(first) - len(second)):
        if (
            result.band_lower_diagonal,
            result.band_upper_diagonal,
            result.scheduled_band_cells,
            result.max_row_width,
            result.estimated_scratch_bytes,
            result.visited_band_cells,
            result.allocated_packed_payload_bytes,
        ) != (None, None, 0, 0, None, 0, 0):
            raise ValueError("reference preflight presence disagreement")
    elif result.scheduled_band_cells != len(cells) or result.max_row_width != max(
        sum(i == row for i, j in cells) for row in range(len(first) + 1)
    ):
        raise ValueError("independent geometry disagreement")
    words = [0] * 64
    words[:7] = [
        1,
        int(result.reason is not None),
        0 if result.reason is None else 2,
        len(first),
        len(second),
        1,
        K,
    ]

    def wide(slot, value):
        words[slot], words[slot + 1] = value & 0xFFFFFFFF, value >> 32

    for bit, slot, value in (
        (1, 8, result.band_lower_diagonal),
        (2, 9, result.band_upper_diagonal),
        (4, 10, result.scheduled_band_cells),
        (8, 14, result.max_row_width),
        (16, 15, result.estimated_scratch_bytes),
        (32, 19, result.edit_distance),
    ):
        if value is not None:
            words[7] |= bit
            if slot in (10, 15):
                wide(slot, value)
            else:
                words[slot] = value & 0xFFFFFFFF
    wide(12, result.visited_band_cells)
    wide(17, result.allocated_packed_payload_bytes)
    if result.budgets:
        words[20:27] = states
    return words


def classify_observation(observation):
    required = {
        "variant_id",
        "compile_exit",
        "child_exit",
        "transport",
        "canaries_intact",
        "output_words",
        "case",
    }
    if type(observation) is not dict or set(observation) != required:
        raise ValueError("complete observation required")
    variant = observation["variant_id"]
    if type(variant) is not str or variant not in ("control", *MUTATION_IDS):
        raise ValueError("unknown variant")
    case = _case(observation["case"])
    if case not in schedule(variant):
        raise ValueError("case outside variant schedule")
    for key in ("compile_exit", "child_exit", "transport"):
        if type(observation[key]) is not int:
            raise ValueError("integer transport/exits required")
    if type(observation["canaries_intact"]) is not bool:
        raise ValueError("exact canary observation required")
    record = dict(
        variant_id=variant,
        case=case,
        status="survived",
        differences=[],
        training_authority=False,
        held_out_data_present=False,
        compile_exit=observation["compile_exit"],
        child_exit=observation["child_exit"],
        transport=observation["transport"],
        canaries_intact=observation["canaries_intact"],
        output_words=observation["output_words"],
    )
    if observation["compile_exit"]:
        record["status"] = "compile-failed"
    elif observation["child_exit"]:
        record["status"] = "child-crashed"
    elif observation["transport"] == 3:
        record["status"] = "invariant-detected"
    elif observation["transport"] in (1, 2):
        record["status"] = "transport-rejected"
    elif observation["transport"] != 0:
        raise ValueError("unknown native transport status")
    elif not observation["canaries_intact"]:
        record["status"] = "canary-failed"
    else:
        words = observation["output_words"]
        if (
            not isinstance(words, (list, tuple))
            or len(words) != 64
            or any(type(w) is not int or not 0 <= w <= 0xFFFFFFFF for w in words)
        ):
            raise ValueError("all64 exact uint32 raw output words required")
        expected = expected_words(case)
        if (
            words[0] != 1
            or words[1] not in (0, 1)
            or words[2] not in range(5)
            or any(words[55:])
        ):
            raise ValueError(
                "invalid ABI/authority/reserved raw output; no semantic kill"
            )
        if words[5] != 1 or words[7] & ~63 or any(words[27:55]):
            raise ValueError("invalid fixed budget/presence/unused exposure ABI")
        exact = words[1] == 0
        if exact != (words[2] == 0) or bool(words[7] & 32) != exact:
            raise ValueError("inconsistent method/reason/distance presence")
        if exact and words[7] != 63:
            raise ValueError("exact result requires complete geometry")
        if not exact and any(words[20:27]):
            raise ValueError("unresolved exposure is forbidden")
        for bit, slots in (
            (1, (8,)),
            (2, (9,)),
            (4, (10, 11)),
            (8, (14,)),
            (16, (15, 16)),
            (32, (19,)),
        ):
            if not words[7] & bit and any(words[s] for s in slots):
                raise ValueError("absent raw field nonzero")
        if (
            bool(words[7] & 1) != bool(words[7] & 2)
            or bool(words[7] & 4) != bool(words[7] & 8)
            or (words[7] & 16 and words[7] & 31 != 31)
        ):
            raise ValueError("inconsistent geometry presence")
        record["differences"] = [
            dict(slot=i, expected=e, actual=a)
            for i, (e, a) in enumerate(zip(expected, words))
            if e != a
        ]
        if record["differences"]:
            record["status"] = (
                "control-disagreed" if variant == "control" else "semantic-killed"
            )
    return record


def manifest(baseline, provenance):
    pins = {
        str(
            ROOT
            / "docs/superpowers/plans/2026-10-02-alc-r0-banded-native-fixture-design.md"
        ): PLAN_SHA256,
        str(
            ROOT / "src/aluclu/alc_r0/banded_edit_token_visibility_reference.py"
        ): REFERENCE_SHA256,
        str(
            ROOT / "scripts/alc_r0_banded_edit_visibility_mutation_probe.py"
        ): PROBE_SHA256,
        str(
            ROOT
            / "docs/superpowers/plans/2026-10-02-alc-r0-native-mutation-fixture-gate.md"
        ): DETAIL_PLAN_SHA256,
    }
    if (
        type(provenance) is not dict
        or set(provenance)
        != {
            "verified_paths",
            "baseline_receipt_path",
            "baseline_receipt_sha256",
            "generator_sha256",
        }
        or provenance["verified_paths"] != pins
    ):
        raise ValueError("closed pinned provenance required")
    receipt_path = Path(provenance["baseline_receipt_path"])
    if (
        not receipt_path.is_absolute()
        or receipt_path.resolve() != receipt_path
        or receipt_path.name != "receipt.json"
        or ROOT in receipt_path.parents
    ):
        raise ValueError("canonical external baseline receipt path required")
    if (
        type(provenance["baseline_receipt_sha256"]) is not str
        or not re.fullmatch("[0-9a-f]{64}", provenance["baseline_receipt_sha256"])
        or provenance["generator_sha256"] != digest(Path(__file__).read_bytes())
    ):
        raise ValueError("receipt/generator hash required")
    variants = generate_variants(baseline)
    return dict(
        schema=1,
        stage="generated-only-unbuilt",
        baseline_commit=BASELINE_COMMIT,
        baseline_sha256=BASELINE_SHA256,
        provenance=provenance,
        variants=[
            dict(
                variant_id=name,
                source_sha256=r["source_sha256"],
                old_hex=r["old_bytes"].hex(),
                new_hex=r["new_bytes"].hex(),
                cases=schedule(name),
            )
            for name, r in variants.items()
        ],
        training_authority=False,
        held_out_data_present=False,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--baseline-receipt", type=Path, required=True)
    args = parser.parse_args()
    from aluclu.alc_r0.banded_edit_token_visibility_native import read_build_receipt

    receipt = read_build_receipt(args.baseline_receipt)
    if (
        receipt["commit"] != BASELINE_COMMIT
        or receipt["native_source_sha256"] != BASELINE_SHA256
    ):
        raise ValueError("frozen baseline positive receipt required")
    baseline = (ROOT / "native/alc_r0/banded_edit_visibility.cpp").read_bytes()
    paths = [
        ROOT
        / "docs/superpowers/plans/2026-10-02-alc-r0-banded-native-fixture-design.md",
        ROOT / "src/aluclu/alc_r0/banded_edit_token_visibility_reference.py",
        ROOT / "scripts/alc_r0_banded_edit_visibility_mutation_probe.py",
        ROOT
        / "docs/superpowers/plans/2026-10-02-alc-r0-native-mutation-fixture-gate.md",
    ]
    hashes = {str(p): digest(p.read_bytes()) for p in paths}
    if tuple(hashes[str(p)] for p in paths) != (
        PLAN_SHA256,
        REFERENCE_SHA256,
        PROBE_SHA256,
        DETAIL_PLAN_SHA256,
    ):
        raise ValueError("frozen plan/reference mismatch")
    out = args.output_dir.resolve()
    if out == ROOT or ROOT in out.parents or out.exists():
        raise ValueError("fresh external directory required")
    variants = generate_variants(baseline)
    provenance = dict(
        verified_paths=hashes,
        baseline_receipt_path=str(args.baseline_receipt.resolve()),
        baseline_receipt_sha256=digest(args.baseline_receipt.read_bytes()),
        generator_sha256=digest(Path(__file__).read_bytes()),
    )
    data = manifest(baseline, provenance)
    out.mkdir(parents=True)
    for name, record in variants.items():
        directory = out / name
        directory.mkdir()
        (directory / "banded_edit_visibility.cpp").write_bytes(record["source_bytes"])
    (out / "manifest.json").write_text(
        json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    print(out / "manifest.json")


if __name__ == "__main__":
    main()
