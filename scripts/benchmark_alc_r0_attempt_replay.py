"""Synthetic semantic replay timing, never a model/learning/resource gate."""

from __future__ import annotations

import hashlib
import json
import statistics
import sys
from pathlib import Path
from time import perf_counter_ns

import aluclu.alc_r0.attempt_state as attempt_state
from aluclu.alc_r0.attempt_state import AttemptReplay, RunSpec, replay_attempts
from aluclu.alc_r0.canonical import canonical_json_bytes

COUNTS = (8192, 16384, 33243)
SAMPLES = 3
RUN = "alc-r0-v1-dev-synthetic-replay-s20260916"
ROOT = "a" * 64


def fixture(count):
    specs = (RunSpec(RUN, False, tuple(f"w{i}" for i in range(count))),)

    def event(kind, **fields):
        return canonical_json_bytes(
            dict(run_id=RUN, attempt_id="a001", kind=kind, **fields)
        )

    history = (
        event(
            "intent",
            source_sha256=ROOT,
            invocation_sha256=ROOT,
            retry_kind="INITIAL",
            prior_source_sha256=None,
            prior_artifact_sha256=None,
            review_sha256=None,
        ),
        event("start", receipt_sha256=ROOT),
        *(event("work", work_id=w, evidence_sha256=ROOT) for w in specs[0].work_ids),
        event(
            "close",
            state="PREPARED",
            failure_class=None,
            evidence_sha256=ROOT,
            gpu_ns=0,
            wall_ns=0,
            storage_growth_bytes=0,
        ),
        event("result", state="PASS", evidence_sha256=ROOT),
    )
    return specs, history


def incremental(specs, history):
    replay = AttemptReplay(specs)
    for data in history:
        replay.append(data)
    return replay.snapshot()


def verified_source(checkout):
    expected = (checkout / "src/aluclu/alc_r0/attempt_state.py").resolve()
    imported = Path(attempt_state.__file__).resolve(strict=True)
    if imported != expected:
        raise RuntimeError("benchmark imported source does not match checkout")
    return imported


def main():
    checkout = Path(__file__).resolve().parents[1]
    imported = verified_source(checkout)
    results = []
    for count in COUNTS:
        specs, history = fixture(count)
        digest = hashlib.sha256()
        for data in history:
            digest.update(len(data).to_bytes(8, "big"))
            digest.update(data)
        times = {"reference_ns": [], "incremental_ns": []}
        expected = None
        for sample in range(SAMPLES):
            # Alternate ordering to reduce fixed first/second-path bias.
            names = ("reference_ns", "incremental_ns")
            if sample % 2:
                names = tuple(reversed(names))
            for name in names:
                started = perf_counter_ns()
                view = (replay_attempts if name == "reference_ns" else incremental)(
                    specs, history
                )
                times[name].append(perf_counter_ns() - started)
                if expected is None:
                    expected = view
                if view != expected:
                    raise RuntimeError("synthetic exact output parity failed")
            print(
                f"count={count} sample={sample + 1} parity=true",
                file=sys.stderr,
                flush=True,
            )
        results.append(
            dict(
                count=count,
                events=len(history),
                samples=SAMPLES,
                parity=True,
                input_length_framed_sha256=digest.hexdigest(),
                output_local_python_repr_sha256=hashlib.sha256(
                    repr(expected).encode()
                ).hexdigest(),
                **times,
                median_reference_over_incremental=(
                    statistics.median(times["reference_ns"])
                    / statistics.median(times["incremental_ns"])
                ),
            )
        )
    print(
        json.dumps(
            dict(
                schema="alc-r0-synthetic-attempt-replay-timing-v1",
                counts=list(COUNTS),
                samples=SAMPLES,
                python=sys.version,
                source_sha256=hashlib.sha256(imported.read_bytes()).hexdigest(),
                imported_source=str(imported),
                imported_source_matches_checkout=True,
                benchmark_sha256=hashlib.sha256(
                    Path(__file__).read_bytes()
                ).hexdigest(),
                results=results,
                claim="synthetic in-memory replay only; no latency threshold, storage/model/learning PASS",
            ),
            sort_keys=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
