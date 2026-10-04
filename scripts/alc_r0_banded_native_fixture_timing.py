"""Explicit fixed synthetic timing CLI; importing performs no timing or load.

Raw intervals include ctypes dispatch. Components are separate observations,
not an additive profile. Only full public audit median decides local benefit.
"""

import argparse
import ctypes as ct
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
from array import array
from functools import partial
from pathlib import Path
from sys import getsizeof
from time import perf_counter_ns

ROOT = Path(__file__).resolve().parents[1]
BUDGETS = (1, 2, 3, 4, 5)
METHODS = (
    "python_reference",
    "rank_mapping",
    "buffer_marshalling",
    "raw_native_ctypes",
    "public_native_end_to_end",
)
WARMUPS = 2
MEASURED = 5
RECEIPT = Path(
    "C:/Users/kaann/Desktop/03_Projeler_Arge/ALUCLU/.research-evidence/alc_r0_banded_native_20261002/build-d739a35-v1/receipt.json"
)
RECEIPT_SHA = "ec5463427664884af4c2315031733fe3eb9a496abc84322b5fefba46db4e8d61"
BASELINE_COMMIT = "d739a35dc7d184c77fec893a22c972fb5d40cf34"
PINS = {
    "docs/superpowers/plans/2026-10-02-alc-r0-native-fixture-timing-detail.md": "e21ee7e7caacfbd91a3caecfd3b11f924a34e6cafb28b90d5a8c198145d0820e",
    "docs/superpowers/plans/2026-10-02-alc-r0-banded-native-fixture-design.md": "0cac0b1ac5f70bc7a3167a43d232672d90aed5eec168d0bd1fd150380fa3e3f3",
    "src/aluclu/alc_r0/banded_edit_token_visibility_reference.py": "dff2a30af16daa97dd0acd1ab39fe89403b35b6a4b181c95f7bf5db21f707f8d",
    "src/aluclu/alc_r0/banded_edit_token_visibility_native.py": "a8dec598fb796b2703d8bfe01d7358e43edb90f9c85c4e58d2a276a9949452d2",
}
OWN_FILES = (
    "scripts/alc_r0_banded_native_fixture_timing.py",
    "tests/test_alc_r0_banded_native_fixture_timing.py",
)


def require(condition, message="invalid fixed fixture timing contract"):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fixed_cases():
    unique = tuple(range(10000))
    small = tuple(range(600))
    return (
        dict(name="unique-identity-10000-K0", first=unique, second=unique, K=0),
        dict(
            name="unique-insertion-10000-K1",
            first=unique,
            second=unique[:5000] + (10000,) + unique[5000:],
            K=1,
        ),
        dict(
            name="repeated-insertion-10000-K1",
            first=(7,) * 10000,
            second=(7,) * 10001,
            K=1,
        ),
        dict(name="unique-identity-600-K512", first=small, second=small, K=512),
    )


def measurement_schedule():
    return [
        (case, method, phase, index)
        for case in range(4)
        for method in METHODS
        for phase, count in (("warmup", WARMUPS), ("measured", MEASURED))
        for index in range(count)
    ]


def sample_statistics(samples):
    require(
        type(samples) in (list, tuple)
        and len(samples) == MEASURED
        and all(type(v) is int and v >= 0 for v in samples),
        "five exact nonnegative ns samples required",
    )
    return dict(
        samples_ns=list(samples),
        mean_ns=sum(samples) / MEASURED,
        median_ns=statistics.median(samples),
        min_ns=min(samples),
        max_ns=max(samples),
    )


def compare_medians(python_stats, native_stats):
    python = python_stats["median_ns"]
    native = native_stats["median_ns"]
    require(type(python) is int and python > 0 and type(native) is int and native >= 0)
    return dict(
        native_end_to_end_over_python_reference=native / python,
        native_end_to_end_faster=native < python,
    )


def encode_reference_words(result):
    """Independent complete B5 ABI encoder; no native decoder or DLL involved."""
    from aluclu.alc_r0.banded_edit_token_visibility_reference import (
        BandedEditVisibilityResult,
    )

    require(
        isinstance(result, BandedEditVisibilityResult)
        and result.requested_code_budgets == BUDGETS
    )
    require(
        result.training_authority is False and result.held_out_data_present is False
    )
    reasons = {
        None: 0,
        "endpoint-token-limit": 1,
        "distance-threshold-exceeded": 2,
        "band-cell-limit": 3,
        "scratch-byte-limit": 4,
    }
    require(result.reason in reasons)
    exact = result.status == "exact-non-authorizing"
    require(
        exact == (result.reason is None)
        and (exact or result.status == "resource-unresolved-non-authorizing")
    )
    words = [0] * 64
    words[:7] = [
        1,
        int(not exact),
        reasons[result.reason],
        result.first_tokens,
        result.second_tokens,
        5,
        result.distance_threshold,
    ]

    def wide(slot, value):
        require(type(value) is int and 0 <= value < 1 << 64)
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
            require(type(value) is int)
            words[7] |= bit
            if slot in (10, 15):
                wide(slot, value)
            else:
                words[slot] = value & 0xFFFFFFFF
    wide(12, result.visited_band_cells)
    wide(17, result.allocated_packed_payload_bytes)
    if exact:
        require(len(result.budgets) == 5 and result.edit_distance is not None)
        for index, row in enumerate(result.budgets):
            require(row.code_budget == BUDGETS[index])
            words[20 + 7 * index : 27 + 7 * index] = [
                row.first_min,
                row.first_max,
                row.second_min,
                row.second_max,
                row.total_min,
                row.total_max,
                row.joint_signature_bits,
            ]
    else:
        require(not result.budgets and result.edit_distance is None)
    require(
        len(words) == 64 and all(type(w) is int and 0 <= w <= 0xFFFFFFFF for w in words)
    )
    return words


def marshal_private(mapped, result):
    """Mapping excluded; geometry comes from admitted immutable reference."""
    from aluclu.alc_r0.banded_edit_token_visibility_reference import (
        BandedEditVisibilityLimits,
    )

    require(
        result.limits == BandedEditVisibilityLimits()
        and result.requested_code_budgets == BUDGETS
        and result.status == "exact-non-authorizing"
    )
    n, m = result.first_tokens, result.second_tokens
    require(
        0 <= n <= 32768 and 0 <= m <= 32768 and 0 <= result.distance_threshold <= 512
    )
    width = result.max_row_width
    cells = result.scheduled_band_cells
    scratch = result.estimated_scratch_bytes
    require(
        type(width) is int
        and 1 <= width <= 513
        and type(cells) is int
        and 0 < cells <= 4194304
        and type(scratch) is int
        and 0 < scratch <= 67108864
    )
    payload = 2 * (1 + 7 * 5) * 4 * width + 5 * (n + m)
    require(payload == result.allocated_packed_payload_bytes and payload <= 67108864)
    require(type(mapped) is tuple and len(mapped) == 3)
    left, right, ranks = mapped
    require(
        type(left) is tuple
        and type(right) is tuple
        and len(left) == n
        and len(right) == m
        and type(ranks) is int
        and 0 <= ranks <= 65536
        and (ranks > 0 or n == m == 0)
    )
    require(
        all(
            type(v) is int and 0 <= v < ranks
            for endpoint in (left, right)
            for v in endpoint
        )
    )
    require(array("I").itemsize == 4 and array("B").itemsize == 1)
    first = (ct.c_uint32 * n)(*left)
    second = (ct.c_uint32 * m)(*right)
    budgets = (ct.c_uint32 * 5)(*(min(b, max(n, m, 1)) for b in BUDGETS))
    policy = (ct.c_uint32 * 8)(
        32768,
        4194304,
        67108864,
        512,
        getsizeof(array("I")),
        getsizeof(array("B")),
        ranks,
        0,
    )
    workspace = (ct.c_uint32 * ((payload + 3) // 4 + 2))(
        *([0xA5A5A5A5] * ((payload + 3) // 4 + 2))
    )
    output = (ct.c_uint32 * 66)(*([0xDEADBEEF] * 66))
    wp = ct.cast(ct.byref(workspace, 4), ct.POINTER(ct.c_uint8))
    op = ct.cast(ct.byref(output, 4), ct.POINTER(ct.c_uint32))
    require(ct.addressof(workspace) + 4 & 3 == 0)
    # Every pointer's array owner stays in this private dictionary until checks.
    return dict(
        first=first,
        second=second,
        budgets=budgets,
        policy=policy,
        workspace=workspace,
        output=output,
        payload=payload,
        logical_capacity=payload,
        allocated_backing_bytes=ct.sizeof(workspace),
        args=(
            first,
            n,
            second,
            m,
            budgets,
            5,
            result.distance_threshold,
            policy,
            wp,
            payload,
            op,
            64,
        ),
    )


def validate_raw(buffers, transport, expected):
    require(type(transport) is int and transport == 0, "native transport failure")
    output = buffers["output"]
    raw = bytes(buffers["workspace"])
    payload = buffers["payload"]
    require(
        buffers["logical_capacity"] == payload
        and buffers["allocated_backing_bytes"] == 4 * ((payload + 3) // 4 + 2)
    )
    require(
        raw[:4] == b"\xa5" * 4
        and raw[4 + payload :] == b"\xa5" * (len(raw) - 4 - payload)
        and output[0] == output[-1] == 0xDEADBEEF,
        "guard failure",
    )
    require(list(output)[1:65] == expected, "full64 native/reference disagreement")


def verify_pins_and_receipt():
    from aluclu.alc_r0.banded_edit_token_visibility_native import read_build_receipt

    for relative, expected in PINS.items():
        require(sha(ROOT / relative) == expected, "timing source pin mismatch")
    require(sha(RECEIPT) == RECEIPT_SHA, "original positive receipt changed")
    receipt = read_build_receipt(RECEIPT)
    require(
        receipt["commit"] == BASELINE_COMMIT
        and receipt["native_source_sha256"]
        == "c577846b7f5de113230b89224d96a707eceecaf7659cad2b316d2138201f96ad"
    )
    return receipt


def git(*parts):
    return subprocess.check_output(["git", "-C", str(ROOT), *parts], text=True).strip()


def source_freeze():
    require(
        not git("status", "--porcelain", "--untracked-files=all"),
        "clean reviewed committed timing sources required",
    )
    commit, tree = git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}")
    hashes = {str(ROOT / relative): sha(ROOT / relative) for relative in OWN_FILES}
    for relative in OWN_FILES:
        committed = subprocess.check_output(
            ["git", "-C", str(ROOT), "show", commit + ":" + relative]
        )
        require(hashlib.sha256(committed).hexdigest() == hashes[str(ROOT / relative)])
    return dict(commit=commit, tree=tree, source_hashes=hashes, dirty=False)


def fresh_output(path):
    path = Path(path)
    require(
        path.is_absolute()
        and path.resolve() == path
        and path != ROOT
        and ROOT not in path.parents
        and not path.exists(),
        "fresh canonical external file required",
    )
    for component in (path.parent, *path.parent.parents):
        if component.exists():
            require(
                not getattr(component.stat(), "st_file_attributes", 0) & 0x400,
                "reparse output path forbidden",
            )
    return path


def _measured(operation):
    started = perf_counter_ns()
    value = operation()
    elapsed = perf_counter_ns() - started
    require(type(elapsed) is int and elapsed >= 0)
    return value, elapsed


def publish_completed_report(output, report, verify_artifact):
    """Verify and finish private bytes before an exclusive atomic publication."""
    verify_artifact()
    encoded = (json.dumps(report, sort_keys=True, allow_nan=False) + "\n").encode(
        "utf-8"
    )
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=output.parent, prefix=".alc-r0-timing-", suffix=".stage", delete=False
        ) as stream:
            stage = Path(stream.name)
            require(stream.write(encoded) == len(encoded), "incomplete staged report")
            stream.flush()
            os.fsync(stream.fileno())
        # A complete closed file becomes visible atomically. Unlike replace or
        # POSIX rename, hard-link creation never overwrites an existing target.
        os.link(stage, output)
    finally:
        if stage is not None:
            try:
                stage.unlink()
            except OSError:
                # Temporary-name cleanup is nonmandatory, not an acceptance
                # check capable of invalidating an already published report.
                pass
    return report


def execute(output):
    """Approved explicit CLI only. No runtime acceptance implied by unit tests."""
    from aluclu.alc_r0.banded_edit_token_visibility_native import (
        NativeBandedBackend,
        rank_tokens,
    )
    from aluclu.alc_r0.banded_edit_token_visibility_reference import (
        audit_banded_edit_token_visibility,
    )

    output = fresh_output(output)
    freeze = source_freeze()
    receipt = verify_pins_and_receipt()
    # Includes constructor provenance checks and load, not OS loader time alone.
    backend, load_ns = _measured(lambda: NativeBandedBackend(RECEIPT))
    order = []
    rows = []
    try:
        for case_index, case in enumerate(fixed_cases()):
            first, second, K = case["first"], case["second"], case["K"]
            args = dict(code_budgets=BUDGETS, distance_threshold=K)
            reference = audit_banded_edit_token_visibility(first, second, **args)
            expected = encode_reference_words(reference)
            require(reference.status == "exact-non-authorizing")
            mapped = rank_tokens(first, second)
            statistics_by_method = {}
            for method in METHODS:
                samples = []
                for phase, count in (("warmup", WARMUPS), ("measured", MEASURED)):
                    for repetition in range(count):
                        buffers = None
                        if method == "python_reference":
                            operation = partial(
                                audit_banded_edit_token_visibility,
                                first,
                                second,
                                **args,
                            )
                        elif method == "rank_mapping":
                            operation = partial(rank_tokens, first, second)
                        elif method == "buffer_marshalling":
                            operation = partial(marshal_private, mapped, reference)
                        elif method == "raw_native_ctypes":
                            buffers = marshal_private(mapped, reference)
                            backend._verify_artifact()
                            operation = partial(
                                backend.dll.aluclu_banded_audit_v1, *buffers["args"]
                            )
                        else:
                            operation = partial(backend.audit, first, second, **args)
                        if phase == "measured":
                            value, elapsed = _measured(operation)
                        else:
                            value = operation()
                            elapsed = None
                        # All checks outside the measured operation; failure aborts
                        # before any sample can support a speedup or success file.
                        if method in ("python_reference", "public_native_end_to_end"):
                            require(
                                value == reference,
                                "full public/reference parity failure",
                            )
                        elif method == "rank_mapping":
                            require(value == mapped, "mapping changed")
                        elif method == "buffer_marshalling":
                            require(
                                value["payload"]
                                == reference.allocated_packed_payload_bytes
                                and value["logical_capacity"] == value["payload"]
                            )
                        else:
                            validate_raw(buffers, value, expected)
                        order.append((case_index, method, phase, repetition))
                        if elapsed is not None:
                            samples.append(elapsed)
                        # Release private large arrays before the next sample.
                        value = None
                        buffers = None
                        operation = None
                statistics_by_method[method] = sample_statistics(samples)
            rows.append(
                dict(
                    name=case["name"],
                    first_tokens=len(first),
                    second_tokens=len(second),
                    distance_threshold=K,
                    code_budgets=BUDGETS,
                    expected_words=expected,
                    scheduled_band_cells=reference.scheduled_band_cells,
                    max_row_width=reference.max_row_width,
                    estimated_reference_scratch_bytes=reference.estimated_scratch_bytes,
                    packed_payload_bytes=reference.allocated_packed_payload_bytes,
                    methods=statistics_by_method,
                    comparison=compare_medians(
                        statistics_by_method["python_reference"],
                        statistics_by_method["public_native_end_to_end"],
                    ),
                )
            )
        backend._verify_artifact()
        require(verify_pins_and_receipt() == receipt and source_freeze() == freeze)
        require(order == measurement_schedule())
        report = dict(
            schema=1,
            status="fixed-synthetic-fixture-timing-non-authorizing",
            source_freeze=freeze,
            source_pins=PINS,
            baseline_receipt_path=str(RECEIPT),
            baseline_receipt_sha256=RECEIPT_SHA,
            original_build_commit=receipt["commit"],
            original_build_tree=receipt["tree"],
            original_source_hashes=receipt["source_hashes"],
            dll_sha256=receipt["dll_sha256"],
            dll_size=receipt["dll_size"],
            load_ns=load_ns,
            load_scope="public constructor validation plus load",
            clock="perf_counter_ns",
            methods_order=METHODS,
            warmups=WARMUPS,
            measured_repetitions=MEASURED,
            measurement_order=order,
            cases=rows,
            environment=dict(
                cpu=platform.processor()
                or os.environ.get("PROCESSOR_IDENTIFIER", "unavailable"),
                platform=platform.platform(),
                machine=platform.machine(),
                python=sys.version,
                python_executable=str(Path(sys.executable).resolve()),
                python_executable_sha256=sha(Path(sys.executable)),
                compiler_path=receipt["compiler_path"],
                compiler_sha256=receipt["compiler_sha256"],
                compiler_version=receipt["compiler_version"],
                compiler_flags=receipt["command"],
                architecture=receipt["architecture"],
                sdk_version=receipt["sdk_version"],
            ),
            interpretation=dict(
                raw_native_includes_ctypes_overhead=True,
                component_intervals_are_not_additive=True,
                end_to_end_includes_all_public_per_call_overhead=True,
                comparison="per-case median public native / median Python; no global ratio",
            ),
            training_authority=False,
            held_out_data_present=False,
        )
    finally:
        # Public owner remains retained through process exit; never unload it.
        backend._verify_artifact()
    # No fallible mandatory acceptance check may follow success publication.
    return publish_completed_report(output, report, backend._verify_artifact)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    execute(args.output)
    print(args.output)


if __name__ == "__main__":
    main()
