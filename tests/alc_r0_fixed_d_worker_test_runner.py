"""Closed owned diagnostic worker/settings tests, no model or GPU launch."""

import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

from aluclu.alc_r0.checkpoint_owned_process import run_owned_process


def main():
    entry = time.monotonic_ns()
    if len(sys.argv) != 2 or sys.argv[1] not in ("red", "green", "regression"):
        raise ValueError("closed worker diagnostic mode required")
    mode = sys.argv[1]
    bound = 120 if mode == "red" else 300
    cwd = Path(__file__).resolve().parents[1]
    stem = cwd / "results" / f"alc_r0_fixed_d_worker_{mode}_20261008"
    paths = {suffix: Path(str(stem) + suffix)
             for suffix in (".stdout.log", ".stderr.log", ".xml", ".exit.json")}
    if any(path.exists() for path in paths.values()):
        raise FileExistsError("retained worker evidence exists")
    selection = ["tests/test_alc_r0_fixed_d_worker.py"]
    if mode == "red":
        selection += ["-k", "worker_bootstrap_denies"]
    elif mode == "regression":
        selection += ["tests/test_alc_r0_fixed_d_projection.py",
                      "tests/test_alc_r0_fixed_d_wire.py", "tests/test_alc_r0_canonical.py",
                      "tests/test_alc_r0_checkpoint_parity_inputs.py",
                      "tests/test_alc_r0_import_isolation.py"]
    environment = os.environ.copy()
    environment.update(PYTHONPATH=str(cwd / "src"), PYTHONNOUSERSITE="1",
                       PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
                       CUDA_VISIBLE_DEVICES="-1")
    command = (sys.executable, "-m", "pytest", "-q", *selection,
               "--junitxml=" + str(paths[".xml"]))
    receipt = run_owned_process(command, cwd=cwd, environment=environment,
                                stdout_path=paths[".stdout.log"],
                                stderr_path=paths[".stderr.log"],
                                deadline_ns=entry + bound * 1_000_000_000)
    record = dict(asdict(receipt), pytest_exit_code=receipt.exit_code,
                  parent_bound_seconds=bound, scope="denied-worker-settings-diagnostics")
    data = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    with paths[".exit.json"].open("xb") as output:
        output.write(data)
    print(data.decode("utf-8"))


if __name__ == "__main__":
    main()
