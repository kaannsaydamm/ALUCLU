from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import torch

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the complete portable ALUCLU release gate."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/release_validation.json"),
    )
    return parser.parse_args()


def atomic_json_dump(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name,
        suffix=".tmp",
        dir=path.parent,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary_name, path)
    except BaseException:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
        raise


def source_digest() -> tuple[str, int]:
    extensions = {
        ".bib",
        ".cff",
        ".json",
        ".md",
        ".ps1",
        ".py",
        ".tex",
        ".toml",
    }
    named_files = {"LICENSE", "MANIFEST.in"}
    excluded_directories = {
        ".git",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "final_dist",
        "final_dist_ascii",
        "final_dist_i18n",
        "final_dist_i18n_mit",
        "results",
    }
    files = sorted(
        path
        for path in PROJECT_ROOT.rglob("*")
        if path.is_file()
        and (path.suffix in extensions or path.name in named_files)
        and not any(
            part in excluded_directories or part.endswith(".egg-info")
            for part in path.parts
        )
    )
    digest = hashlib.sha256()
    for path in files:
        relative = path.relative_to(PROJECT_ROOT).as_posix().encode()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest(), len(files)


def run_gate(name: str, arguments: list[str]) -> dict:
    started = time.perf_counter()
    completed = subprocess.run(
        [sys.executable, *arguments],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
        check=False,
        env=os.environ | {"PYTHONHASHSEED": "0"},
    )
    return {
        "name": name,
        "command": ["python", *arguments],
        "return_code": completed.returncode,
        "elapsed_seconds": time.perf_counter() - started,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main() -> None:
    args = parse_args()
    gates = [
        (
            "compileall",
            ["-m", "compileall", "-q", "src", "scripts", "tests"],
        ),
        ("pytest", ["-m", "pytest", "-q"]),
        (
            "diagnostic_mqar_smoke",
            [
                "scripts/train_mqar.py",
                "--steps",
                "2",
                "--batch-size",
                "2",
                "--n-pairs",
                "3",
                "--n-queries",
                "2",
                "--key-vocab-size",
                "16",
                "--value-vocab-size",
                "16",
                "--d-model",
                "8",
                "--n-layers",
                "1",
                "--eval-batches",
                "1",
                "--device",
                "cpu",
                "--output",
                "results/validation_diagnostic_mqar.json",
            ],
        ),
        (
            "zoology_mqar_smoke",
            [
                "scripts/train_zoology_mqar.py",
                "--input-seq-len",
                "16",
                "--num-kv-pairs",
                "3",
                "--vocab-size",
                "64",
                "--train-examples",
                "8",
                "--eval-examples",
                "4",
                "--batch-size",
                "4",
                "--epochs",
                "1",
                "--d-model",
                "8",
                "--n-layers",
                "1",
                "--device",
                "cpu",
                "--output",
                "results/validation_zoology_mqar.json",
            ],
        ),
        (
            "stream_performance_smoke",
            [
                "scripts/benchmark_stream.py",
                "--d-model",
                "8",
                "--n-layers",
                "1",
                "--vocab-size",
                "64",
                "--warmup-tokens",
                "16",
                "--measure-tokens",
                "8",
                "--prefill-tokens",
                "16",
                "--repeats",
                "2",
                "--torch-threads",
                "1",
                "--device",
                "cpu",
                "--output",
                "results/validation_performance.json",
            ],
        ),
    ]
    results = []
    for name, command in gates:
        print(f"[gate] {name}", flush=True)
        result = run_gate(name, command)
        results.append(result)
        if result["return_code"] != 0:
            break

    digest, file_count = source_digest()
    passed = len(results) == len(gates) and all(
        result["return_code"] == 0 for result in results
    )
    payload = {
        "protocol_id": "aluclu_portable_release_gate_v1",
        "passed": passed,
        "source": {
            "sha256": digest,
            "file_count": file_count,
        },
        "gates": results,
        "environment": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "platform": platform.platform(),
        },
    }
    output_path = (
        args.output if args.output.is_absolute() else PROJECT_ROOT / args.output
    )
    atomic_json_dump(output_path, payload)
    print(f"passed={passed} result={output_path}")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
