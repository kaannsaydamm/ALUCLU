from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

from aluclu.alc_r0.canonical import canonical_json_bytes
from aluclu.alc_r0.run_matrix import SOURCE_PLAN_PATH, build_logical_run_matrix_document

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the frozen canonical ALC-R0 logical-run matrix."
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    if not args.output.is_absolute():
        parser.error("--output must be absolute")
    if args.output.is_symlink():
        parser.error("--output must not be a symlink")
    if args.output.exists() and not args.replace:
        parser.error("--output must not already exist")
    output_parent = args.output.parent.resolve(strict=True)
    output = output_parent / args.output.name
    plan_bytes = (PROJECT_ROOT / SOURCE_PLAN_PATH).read_bytes()
    encoded = canonical_json_bytes(build_logical_run_matrix_document(plan_bytes))
    if args.replace:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=output.name,
            suffix=".tmp",
            dir=output_parent,
        )
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_name, output)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)
    else:
        descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())


if __name__ == "__main__":
    main()
