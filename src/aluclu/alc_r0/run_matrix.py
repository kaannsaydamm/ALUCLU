"""Closed logical-run matrix frozen by the ALC-R0 preregistration."""

from __future__ import annotations

from dataclasses import dataclass

_FAMILIES = ("banking77", "devign")
_DEV_SEEDS = (20260917, 20260918)
_CONFIRM_SEEDS = (20260921, 20260922, 20260923, 20260924, 20260925)
_GRIDS = (
    "l-r4",
    "l-r8",
    "l-r16",
    "m-r4",
    "m-r8",
    "m-r16",
    "ml-r4",
    "ml-r8",
    "ml-r16",
)

_TRAIN_ARTIFACTS = tuple(
    sorted(
        (
            "base-digest.json",
            "checkpoint-inventory.json",
            "exit.json",
            "metrics.json",
            "resource-usage.json",
            "run-events.jsonl",
            "stderr.log",
            "stdout.log",
            "training-manifest.json",
        )
    )
)
_PILOT_ARTIFACTS = tuple(sorted((*_TRAIN_ARTIFACTS, "feasibility-projection.json")))
_TARGET_SCORE_ARTIFACTS = tuple(
    sorted(
        (
            "exit.json",
            "information-boundary-receipt.json",
            "metrics.json",
            "predictions.jsonl",
            "run-events.jsonl",
            "stderr.log",
            "stdout.log",
        )
    )
)
_RETENTION_SCORE_ARTIFACTS = tuple(
    sorted(
        (
            "exit.json",
            "likelihoods.jsonl",
            "metrics.json",
            "run-events.jsonl",
            "stderr.log",
            "stdout.log",
        )
    )
)
_ATTACH_ARTIFACTS = tuple(
    sorted(("attach-detach-receipt.json", "exit.json", "run-events.jsonl"))
)
_REMOUNT_ARTIFACTS = tuple(
    sorted(
        (
            "exit.json",
            "fresh-remount-receipt.json",
            "predictions.jsonl",
            "run-events.jsonl",
        )
    )
)
_BASE_DIGEST_ARTIFACTS = ("pre-post-base-digest.json",)
_CAPSULE_SIZE_ARTIFACTS = ("capsule-size-receipt.json",)
_RESOURCE_ARTIFACTS = ("resource-harness.json", "resource-samples.jsonl")


@dataclass(frozen=True, order=True)
class RunSpec:
    run_id: str
    phase: str
    kind: str
    family: str | None
    suite: str | None
    arm: str
    grid_id: str | None
    seed: int
    expected_artifacts: tuple[str, ...]

    def to_json(self) -> dict[str, object]:
        return {
            "arm": self.arm,
            "expected_artifacts": list(self.expected_artifacts),
            "family": self.family,
            "grid_id": self.grid_id,
            "kind": self.kind,
            "phase": self.phase,
            "run_id": self.run_id,
            "seed": self.seed,
            "suite": self.suite,
        }


def _run_id(phase: str, *parts: str, seed: int) -> str:
    return "-".join(("alc-r0-v1", phase, *parts, f"s{seed:08d}"))


def _row(
    phase: str,
    kind: str,
    *id_parts: str,
    family: str | None,
    suite: str | None,
    arm: str,
    grid_id: str | None,
    seed: int,
    expected_artifacts: tuple[str, ...],
) -> RunSpec:
    return RunSpec(
        run_id=_run_id(phase, *id_parts, seed=seed),
        phase=phase,
        kind=kind,
        family=family,
        suite=suite,
        arm=arm,
        grid_id=grid_id,
        seed=seed,
        expected_artifacts=expected_artifacts,
    )


def build_expected_run_matrix() -> tuple[RunSpec, ...]:
    """Return all 280 preregistered logical run rows in UTF-8 run-ID order."""

    rows: list[RunSpec] = []

    for family in _FAMILIES:
        for arm in ("capsule", "q-only-lora"):
            rows.append(
                _row(
                    "pilot",
                    "pilot-train",
                    "train",
                    family,
                    arm,
                    "m-r8",
                    family=family,
                    suite=None,
                    arm=arm,
                    grid_id="m-r8",
                    seed=20260916,
                    expected_artifacts=_PILOT_ARTIFACTS,
                )
            )

    for family in _FAMILIES:
        for arm in ("capsule", "q-only-lora"):
            for grid_id in _GRIDS:
                for seed in _DEV_SEEDS:
                    rows.append(
                        _row(
                            "dev",
                            "dev-train",
                            "train",
                            family,
                            arm,
                            grid_id,
                            family=family,
                            suite=None,
                            arm=arm,
                            grid_id=grid_id,
                            seed=seed,
                            expected_artifacts=_TRAIN_ARTIFACTS,
                        )
                    )
        for seed in _DEV_SEEDS:
            rows.append(
                _row(
                    "dev",
                    "dev-train",
                    "train",
                    family,
                    "q-v-lora",
                    "all-r8",
                    family=family,
                    suite=None,
                    arm="q-v-lora",
                    grid_id="all-r8",
                    seed=seed,
                    expected_artifacts=_TRAIN_ARTIFACTS,
                )
            )

    for family in _FAMILIES:
        for arm in ("capsule", "q-only-lora", "label-shuffled", "q-v-lora"):
            grid_id = "all-r8" if arm == "q-v-lora" else "selected"
            for seed in _CONFIRM_SEEDS:
                rows.append(
                    _row(
                        "confirm",
                        "confirm-train",
                        "train",
                        family,
                        arm,
                        family=family,
                        suite=None,
                        arm=arm,
                        grid_id=grid_id,
                        seed=seed,
                        expected_artifacts=_TRAIN_ARTIFACTS,
                    )
                )

    for family in _FAMILIES:
        for arm in ("base", "profile", "rag", "zero"):
            rows.append(
                _row(
                    "eval",
                    "target-score",
                    "target-score",
                    family,
                    arm,
                    family=family,
                    suite=None,
                    arm=arm,
                    grid_id="selected" if arm == "zero" else None,
                    seed=0,
                    expected_artifacts=_TARGET_SCORE_ARTIFACTS,
                )
            )
        for arm in (
            "capsule",
            "q-only-lora",
            "label-shuffled",
            "q-v-lora",
            "wrong-family",
        ):
            for seed in _CONFIRM_SEEDS:
                rows.append(
                    _row(
                        "eval",
                        "target-score",
                        "target-score",
                        family,
                        arm,
                        family=family,
                        suite=None,
                        arm=arm,
                        grid_id="all-r8" if arm == "q-v-lora" else "selected",
                        seed=seed,
                        expected_artifacts=_TARGET_SCORE_ARTIFACTS,
                    )
                )

    for suite in ("lambada", "wikitext2"):
        rows.append(
            _row(
                "eval",
                "retention-score",
                "retention-score",
                suite,
                "base",
                family=None,
                suite=suite,
                arm="base",
                grid_id=None,
                seed=0,
                expected_artifacts=_RETENTION_SCORE_ARTIFACTS,
            )
        )
        for family in _FAMILIES:
            for seed in _CONFIRM_SEEDS:
                rows.append(
                    _row(
                        "eval",
                        "retention-score",
                        "retention-score",
                        suite,
                        "capsule",
                        family,
                        family=family,
                        suite=suite,
                        arm="capsule",
                        grid_id="selected",
                        seed=seed,
                        expected_artifacts=_RETENTION_SCORE_ARTIFACTS,
                    )
                )

    for family in _FAMILIES:
        for seed in _CONFIRM_SEEDS:
            for kind, prefix, artifacts in (
                ("attach-detach", "attach-detach", _ATTACH_ARTIFACTS),
                ("fresh-remount", "fresh-remount", _REMOUNT_ARTIFACTS),
                ("capsule-size", "capsule-size", _CAPSULE_SIZE_ARTIFACTS),
                ("resource", "resource", _RESOURCE_ARTIFACTS),
            ):
                rows.append(
                    _row(
                        "eval",
                        kind,
                        prefix,
                        family,
                        family=family,
                        suite=None,
                        arm="capsule",
                        grid_id="selected",
                        seed=seed,
                        expected_artifacts=artifacts,
                    )
                )
            for arm in ("capsule", "q-only-lora", "label-shuffled", "q-v-lora"):
                rows.append(
                    _row(
                        "eval",
                        "base-digest",
                        "base-digest",
                        family,
                        arm,
                        family=family,
                        suite=None,
                        arm=arm,
                        grid_id="all-r8" if arm == "q-v-lora" else "selected",
                        seed=seed,
                        expected_artifacts=_BASE_DIGEST_ARTIFACTS,
                    )
                )

    ordered = tuple(sorted(rows, key=lambda row: row.run_id.encode("utf-8")))
    if len(ordered) != 280 or len({row.run_id for row in ordered}) != 280:
        raise RuntimeError("internal ALC-R0 run matrix cardinality violation")
    return ordered
