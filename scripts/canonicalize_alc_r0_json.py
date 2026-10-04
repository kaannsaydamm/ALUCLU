from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any, NoReturn

from aluclu.alc_r0.canonical import CanonicalEvidenceError, canonical_json_bytes


def _reject_constant(value: str) -> NoReturn:
    raise CanonicalEvidenceError(f"non-finite JSON number is forbidden: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CanonicalEvidenceError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _canonicalize(path: Path) -> None:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise CanonicalEvidenceError(f"UTF-8 BOM is forbidden: {path}")
    value = json.loads(
        raw.decode("utf-8", errors="strict"),
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
    )
    encoded = canonical_json_bytes(value)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name,
        suffix=".tmp",
        dir=path.parent,
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Canonicalize ALC-R0 JSON source files."
    )
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    for path in args.paths:
        _canonicalize(path)


if __name__ == "__main__":
    main()
