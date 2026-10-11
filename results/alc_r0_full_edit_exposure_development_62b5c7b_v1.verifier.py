"""Root data-only terminal checks declared before the development DP result.

This is receipt/accounting validation, not prompt or neural acceptance.
Never launches DP, loads a DLL, reads held-out data, or changes a threshold.
"""

import hashlib
import json
import math
import re
import sys
from dataclasses import asdict
from pathlib import Path

from aluclu.alc_r0.acquisition import verify_model_snapshot
from aluclu.alc_r0.canonical import canonical_json_bytes
from aluclu.alc_r0.full_development_banded_edit_exposure import (
    GEOMETRY_RECEIPT_SHA256,
    NATIVE_DLL_SHA256,
    NATIVE_RECEIPT_SHA256,
    load_pinned_geometry_receipt,
    verify_pinned_native_build,
)
from aluclu.alc_r0.source_checkout import inspect_clean_source_checkout

ROOT = Path(
    r"C:\Users\kaann\Desktop\03_Projeler_Arge\ALUCLU\.worktrees\unified-lifelong-cognition-local"
)
STEM = Path(__file__).parent / "full-edit-exposure-development-62b5c7b-v1"
COMMIT = "62b5c7b6577078db5aa79fd2822a9b2381286597"
SUMMARY_KEYS = (
    "pairs",
    "known_geometry_pairs",
    "unknown_geometry_pairs",
    "known_band_cells_sum",
)
TERMINAL = (
    "exact_zero_distance",
    "exact_positive_distance",
    "preflight_unresolved",
    "global_cap_unresolved",
    "terminal_threshold_unresolved",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonnegative_integer(value):
    return type(value) is int and value >= 0


def digest(value):
    return hashlib.sha256(value).hexdigest()


def unique(items):
    result = {}
    for key, value in items:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def parse(raw):
    return json.loads(
        raw,
        object_pairs_hook=unique,
        parse_constant=lambda v: require(False, "nonfinite JSON"),
    )


def main():
    exit_path = Path(str(STEM) + ".exit.log")
    require(
        exit_path.is_file(), "actual terminal exit receipt missing; still incomplete"
    )
    terminal = parse(exit_path.read_bytes())
    require(
        type(terminal["actual_exposure_exit_code"]) is int
        and terminal["actual_exposure_exit_code"] == 0,
        "actual child failed",
    )
    require(terminal["source_commit"] == COMMIT, "wrong terminal source freeze")
    raw = Path(str(STEM) + ".stdout.log").read_bytes()
    stderr = Path(str(STEM) + ".stderr.log").read_bytes()
    require(
        digest(raw) == terminal["stdout_sha256"]
        and digest(stderr) == terminal["stderr_sha256"],
        "raw log commitment mismatch",
    )
    result = parse(raw)
    require(
        canonical_json_bytes(result) + b"\n" == raw,
        "stdout is not one complete canonical JSON plus LF",
    )
    require(
        result["status"] == "retained-development-banded-edit-exposure-non-authorizing",
        "wrong diagnostic status",
    )
    for receipt in (result, terminal):
        require(
            receipt["training_authority"] is False
            and receipt["held_out_data_present"] is False,
            "authority flag mismatch",
        )
    checkout = inspect_clean_source_checkout(ROOT)
    require(
        checkout.source_commit == COMMIT
        and result["source_checkout"] == asdict(checkout),
        "current clean source freeze mismatch",
    )
    geometry = load_pinned_geometry_receipt(
        ROOT
        / "results/alc_r0_banded_pair_resource_census_full_f7af513_20261003.stdout.log"
    )
    core_keys = (
        "receipt_version",
        "status",
        "training_authority",
        "held_out_data_present",
        "policy",
        "policy_sha256",
        "train",
        "validation",
        "ordered_internal_records_sha256",
        "admission",
    )
    require(
        canonical_json_bytes(result["geometry_prepass"])
        == canonical_json_bytes({k: geometry[k] for k in core_keys}),
        "complete unchanged geometry prepass mismatch",
    )
    for key in (
        "source_scope",
        "source_expectation",
        "pair_expectation",
        "pair_source_receipt_sha256",
        "model_inventory_sha256",
        "graph_ledgers",
        "retained_train_rows",
        "retained_validation_rows",
        "model_repository",
        "model_revision",
        "model_snapshot_receipt_sha256",
    ):
        require(
            canonical_json_bytes(result[key]) == canonical_json_bytes(geometry[key]),
            "prior provenance mismatch: " + key,
        )
    require(
        result["geometry_receipt_sha256"] == GEOMETRY_RECEIPT_SHA256
        and result["geometry_source_checkout"] == geometry["source_checkout"],
        "geometry receipt identity mismatch",
    )
    expected_policy = dict(
        operation="bounded-band-edit-exposure-development-only",
        version=1,
        geometry_policy_sha256=geometry["policy_sha256"],
        geometry_prepass_records_sha256=geometry["ordered_internal_records_sha256"],
        total_cell_cap=3_000_000_000,
        limits=geometry["policy"]["limits"],
        distance_threshold=512,
        code_budgets=[499, 1011, 2035, 4083, 8179],
        order="train-then-validation-author-file-order",
        exhaustion="permanent-at-first-locally-eligible-nonfitting-pair",
    )
    require(
        canonical_json_bytes(result["policy"]) == canonical_json_bytes(expected_policy),
        "new policy changed",
    )
    require(
        result["policy_sha256"] == digest(canonical_json_bytes(expected_policy)),
        "policy digest mismatch",
    )
    launch = parse(Path(str(STEM) + ".launch.json").read_bytes())
    require(
        launch["source_commit"] == COMMIT
        and launch["launcher_sha256"]
        == "255d73c3bc5da7a5cf165d935938b6a4fd62bd26fff90caa218b1d68603dd9ad",
        "launch identity mismatch",
    )
    expected_args = launch["arguments"]
    expected_invocation = dict(
        zip(
            (
                "development_data_dir",
                "paired_development_data_dir",
                "tokenizer_snapshot",
                "native_build_receipt",
                "geometry_receipt",
            ),
            expected_args[3:],
            strict=True,
        )
    )
    require(
        result["invocation"]["module"] == expected_args[2], "module invocation mismatch"
    )
    for key, value in expected_invocation.items():
        require(
            result["invocation"][key] == str(Path(value).resolve(strict=True)),
            "invocation path mismatch: " + key,
        )
    require(
        result["invocation"]["python_executable"] == launch["python"],
        "Python invocation mismatch",
    )
    snapshot = verify_model_snapshot(Path(expected_invocation["tokenizer_snapshot"]))
    require(
        snapshot["inventory_sha256"] == result["model_inventory_sha256"]
        and digest(canonical_json_bytes(snapshot))
        == result["model_snapshot_receipt_sha256"],
        "current model snapshot mismatch",
    )
    native = verify_pinned_native_build(expected_invocation["native_build_receipt"])
    require(
        result["native_build_receipt_sha256"] == NATIVE_RECEIPT_SHA256
        and result["native_dll_sha256"] == NATIVE_DLL_SHA256,
        "native receipt/artifact mismatch",
    )
    require(
        result["native_build_identifier"] == native["native_source_sha256"]
        and result["native_source_hashes"] == native["source_hashes"],
        "native source identity mismatch",
    )
    scheduled = visited = 0
    report = {}
    for split, universe, eligible, expected_cells in (
        ("train", 4344, 4160, 2494753540),
        ("validation", 482, 469, 210458744),
    ):
        s = result[split]
        strata = s["strata"]
        require(s["survival"] == geometry[split]["survival"], "survival mismatch")
        require(
            strata["universe"]["pairs"] == universe
            and strata["locally_eligible"]["pairs"] == eligible,
            "cohort mismatch",
        )
        require(
            strata["dp_attempted"] == strata["locally_eligible"]
            and strata["global_cap_unresolved"]["pairs"] == 0,
            "unexpected global admission",
        )
        require(
            strata["dp_attempted"]["known_band_cells_sum"] == expected_cells
            and s["visited_band_cells"] == expected_cells,
            "scheduled/visited mismatch",
        )
        for name, summary in strata.items():
            require(
                all(nonnegative_integer(v) for v in summary.values()),
                "invalid summary integer",
            )
            require(
                summary["pairs"]
                == summary["known_geometry_pairs"] + summary["unknown_geometry_pairs"],
                "known/unknown count mismatch",
            )
            require(
                nonnegative_integer(s["components"][name])
                and s["components"][name] <= summary["pairs"],
                "root-union count bound",
            )
        for key in SUMMARY_KEYS:
            require(
                sum(strata[name][key] for name in TERMINAL) == strata["universe"][key],
                "terminal partition mismatch: " + key,
            )
            require(
                sum(
                    strata[name][key]
                    for name in TERMINAL
                    if name.startswith("exact_")
                    or name == "terminal_threshold_unresolved"
                )
                == strata["dp_attempted"][key],
                "DP partition mismatch: " + key,
            )
        require(
            all(
                nonnegative_integer(v)
                for v in s["preflight_unresolved_reasons"].values()
            )
            and sum(s["preflight_unresolved_reasons"].values())
            == strata["preflight_unresolved"]["pairs"],
            "local reason count mismatch",
        )
        require(
            s["second_pass_geometry_records_sha256"]
            == geometry[split]["ordered_internal_records_sha256"],
            "second-pass token/geometry mismatch",
        )
        require(
            re.fullmatch("[a-f0-9]{64}", s["ordered_internal_records_sha256"])
            is not None,
            "missing exposure split digest",
        )
        n = strata["exact_positive_distance"]["pairs"]
        require(
            [b["code_budget"] for b in s["budget_exposure"]]
            == expected_policy["code_budgets"],
            "budget grid mismatch",
        )
        for b in s["budget_exposure"]:
            require(
                nonnegative_integer(b["pairs"]) and b["pairs"] == n,
                "conditional denominator mismatch",
            )
            h = b["joint_signature_histogram"]
            require(
                set(h) == {str(i) for i in range(1, 16)}
                and all(nonnegative_integer(v) for v in h.values())
                and sum(h.values()) == n,
                "signature histogram mismatch",
            )
            require(
                all(nonnegative_integer(v) for v in b["sums"].values()),
                "invalid exposure count",
            )
            require(
                b["sums"]["first_min"] <= b["sums"]["first_max"]
                and b["sums"]["second_min"] <= b["sums"]["second_max"]
                and b["sums"]["total_min"] <= b["sums"]["total_max"],
                "aggregate bound inversion",
            )
            a, bmax, c, e, t, u = (
                b["sums"][k]
                for k in (
                    "first_min",
                    "first_max",
                    "second_min",
                    "second_max",
                    "total_min",
                    "total_max",
                )
            )
            require(
                a + c <= t <= min(a + e, bmax + c)
                and max(a + e, bmax + c) <= u <= bmax + e,
                "aggregate direct-total inconsistency",
            )
            for key in (
                "some_optimum_hides_all",
                "all_optima_hide_all",
                "every_optimum_exposes",
                "some_optimum_exposes",
                "every_optimum_exposes_all",
                "some_optimum_exposes_all",
            ):
                require(
                    nonnegative_integer(b[key]) and b[key] <= n,
                    "predicate count outside denominator",
                )
            require(
                b["some_optimum_hides_all"] + b["every_optimum_exposes"] == n
                and b["all_optima_hide_all"] + b["some_optimum_exposes"] == n,
                "predicate partition mismatch",
            )
            require(
                b["all_optima_hide_all"] == h["1"]
                and b["every_optimum_exposes_all"] <= b["some_optimum_exposes_all"],
                "signature/predicate mismatch",
            )
            for suffix in ("min", "max"):
                total = b["pair_total_" + suffix + "_fraction_sum"]
                mean = b["mean_pair_total_" + suffix + "_fraction"]
                require(
                    type(total) in (int, float)
                    and math.isfinite(total)
                    and 0 <= total <= n,
                    "invalid ratio sum",
                )
                require(
                    mean is None
                    if n == 0
                    else type(mean) in (int, float)
                    and math.isclose(mean, total / n, rel_tol=1e-12),
                    "conditional mean mismatch",
                )
            require(
                b["pair_total_min_fraction_sum"] <= b["pair_total_max_fraction_sum"],
                "ratio bound inversion",
            )
        scheduled += expected_cells
        visited += s["visited_band_cells"]
        report[split] = {
            key: strata[key]["pairs"] for key in ("universe", "dp_attempted", *TERMINAL)
        }
    require(
        result["admission"]
        == dict(
            scheduled_band_cells=scheduled,
            remaining_band_cells=3_000_000_000 - scheduled,
            exhausted=False,
        ),
        "final new admission mismatch",
    )
    require(visited == scheduled == 2705212284, "global cell accounting mismatch")
    require(
        re.fullmatch("[a-f0-9]{64}", result["ordered_internal_records_sha256"])
        is not None,
        "missing global exposure digest",
    )
    require(
        b"primevul:" not in raw
        and b'"component_root"' not in raw
        and b'"first_token_ids_sha256"' not in raw,
        "per-pair material leaked",
    )
    print(
        json.dumps(
            dict(
                status="root-terminal-accounting-verified-non-authorizing",
                stdout_sha256=digest(raw),
                stderr_sha256=digest(stderr),
                source_commit=COMMIT,
                splits=report,
                scheduled_band_cells=scheduled,
                visited_band_cells=visited,
                training_authority=False,
                held_out_data_present=False,
            ),
            sort_keys=True,
        )
    )


def parser_self_test():
    require(
        nonnegative_integer(0) and not nonnegative_integer(False),
        "boolean accepted as integer",
    )
    require(parse(b'{"x":1}') == {"x": 1}, "valid JSON rejected")
    for raw in (b'{"x":1,"x":2}', b'{"x":NaN}'):
        try:
            parse(raw)
        except ValueError:
            continue
        raise ValueError("malformed JSON accepted")
    print("parser controls passed; not terminal development acceptance")


if __name__ == "__main__":
    if sys.argv[1:] == ["--parser-self-test"]:
        parser_self_test()
    else:
        require(not sys.argv[1:], "verification has no source/policy overrides")
        main()
