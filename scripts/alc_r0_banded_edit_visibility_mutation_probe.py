"""Isolated synthetic mutation evidence; never alters production source files."""

import hashlib
import json
import sys
from itertools import product
from pathlib import Path
from types import ModuleType

if sys.flags.optimize:
    raise RuntimeError("Assertions must be enabled")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
SOURCE = ROOT / "src/aluclu/alc_r0/banded_edit_token_visibility_reference.py"
TEXT = SOURCE.read_text(encoding="utf-8")


def load(text, name):
    module = ModuleType(name)
    module.__package__ = "aluclu.alc_r0"
    sys.modules[name] = module
    try:
        exec(compile(text, str(SOURCE), "exec"), module.__dict__)
        return module
    except BaseException:
        del sys.modules[name]
        raise


def oracle(first, second, budget):
    paths = []

    def retained(n, pos):
        return int(n <= budget or pos < (budget + 1) // 2 or pos >= n - budget // 2)

    def visit(i, j, distance, left, right):
        if i == len(first) and j == len(second):
            paths.append((distance, left, right))
            return
        if i < len(first) and j < len(second) and first[i] == second[j]:
            visit(i + 1, j + 1, distance, left, right)
        if i < len(first):
            visit(i + 1, j, distance + 1, left + retained(len(first), i), right)
        if j < len(second):
            visit(i, j + 1, distance + 1, left, right + retained(len(second), j))

    visit(0, 0, 0, 0, 0)
    distance = min(p[0] for p in paths)
    chosen = [p for p in paths if p[0] == distance]
    left, right = [p[1] for p in chosen], [p[2] for p in chosen]
    totals = [p[1] + p[2] for p in chosen]
    bits = sum(
        1 << s for s in {(2 if p[1] else 0) | (1 if p[2] else 0) for p in chosen}
    )
    return distance, (
        min(left),
        max(left),
        min(right),
        max(right),
        min(totals),
        max(totals),
        bits,
    )


def check(module, case):
    first, second, threshold = case
    expected_distance, expected = oracle(first, second, 1)
    actual = module.audit_banded_edit_token_visibility(
        first, second, code_budgets=(1,), distance_threshold=threshold
    )
    assert (actual.first_tokens, actual.second_tokens) == (len(first), len(second))
    if expected_distance > threshold:
        assert actual.edit_distance is None and actual.budgets == ()
        assert actual.reason == "distance-threshold-exceeded"
    else:
        assert actual.edit_distance == expected_distance
        row = actual.budgets[0]
        assert (
            row.first_min,
            row.first_max,
            row.second_min,
            row.second_max,
            row.total_min,
            row.total_max,
            row.joint_signature_bits,
        ) == expected
        cells = sum(
            abs(i - j) + abs(len(first) - len(second) - i + j) <= threshold
            for i in range(len(first) + 1)
            for j in range(len(second) + 1)
        )
        assert actual.visited_band_cells == actual.scheduled_band_cells == cells


def main():
    tie = "                    if cost != distance:\n                        continue\n"
    before_exposure = "    exposures = tuple(\n"
    mutations = [
        (
            "drop-equal-indel-ties",
            tie,
            tie
            + "                    if operation and i and j and first[i - 1] == second[j - 1]:\n                        continue\n",
            [((7,), (7, 7), 1)],
        ),
        (
            "single-predecessor",
            "            current[0][column] = distance\n",
            "            current[0][column] = distance\n            candidates = [next(item for item in candidates if item[0] == distance)] if candidates else []\n",
            [((1, 2), (2, 1), 2)],
        ),
        (
            "strip-equal-ends",
            "    n, m, threshold = len(first), len(second), distance_threshold\n",
            "    while first and second and first[0] == second[0]:\n        first, second = first[1:], second[1:]\n    while first and second and first[-1] == second[-1]:\n        first, second = first[:-1], second[:-1]\n    n, m, threshold = len(first), len(second), distance_threshold\n",
            [((7,), (7, 7), 1)],
        ),
        (
            "marginal-total",
            before_exposure,
            "    for index in range(count):\n        offset = 1 + 7 * index\n        previous[offset + 4][terminal] = previous[offset][terminal] + previous[offset + 2][terminal]\n        previous[offset + 5][terminal] = previous[offset + 1][terminal] + previous[offset + 3][terminal]\n"
            + before_exposure,
            [((1, 2), (2, 1), 2)],
        ),
        (
            "marginal-joint",
            before_exposure,
            "    for index in range(count):\n        offset = 1 + 7 * index\n        previous[offset + 6][terminal] = 1 << ((2 if previous[offset + 1][terminal] else 0) | (1 if previous[offset + 3][terminal] else 0))\n"
            + before_exposure,
            [((1, 2), (2, 1), 2)],
        ),
        (
            "inward-parity",
            "    cells = width = 0\n    for i in range(n + 1):\n",
            "    if (threshold - delta) % 2:\n        lower += 1\n        upper -= 1\n    cells = width = 0\n    for i in range(n + 1):\n",
            [((1,), (1,), 1)],
        ),
        (
            "exclude-boundary",
            "        for j in range(low, high + 1):\n",
            "        for j in range(low, high):\n",
            [((1,), (1,), 0)],
        ),
        (
            "stale-column",
            "                index = j - prev_low\n",
            "                index = j - low\n",
            None,
        ),
        (
            "accept-over-threshold",
            "    if distance > threshold:\n",
            "    if False:\n",
            [((1,), (2,), 0)],
        ),
    ]
    tiny = [s for n in range(4) for s in product((0, 1), repeat=n)]
    grid = [(a, b, k) for a in tiny for b in tiny for k in range(len(a) + len(b) + 2)]
    control = load(TEXT, "alc_banded_control")
    for case in grid:
        check(control, case)
    del sys.modules[control.__name__]
    records = []
    for name, old, new, cases in mutations:
        if TEXT.count(old) != 1:
            raise RuntimeError(f"Invalid mutation anchor: {name}")
        changed = TEXT.replace(old, new)
        module = load(changed, "alc_banded_mutant_" + name.replace("-", "_"))
        killed = None
        try:
            for case in cases if cases is not None else grid:
                try:
                    check(module, case)
                except (AssertionError, IndexError, StopIteration) as error:
                    killed = {"case": case, "observed": type(error).__name__}
                    break
        finally:
            del sys.modules[module.__name__]
        if killed is None:
            raise AssertionError(f"Mutant survived: {name}")
        records.append(
            {
                "mutation": name,
                "source_sha256": hashlib.sha256(changed.encode()).hexdigest(),
                "killed": killed,
            }
        )
    print(
        json.dumps(
            {
                "status": "fixture-mutations-killed",
                "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                "control_cases": len(grid),
                "mutations": records,
                "training_authority": False,
                "held_out_data_present": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
