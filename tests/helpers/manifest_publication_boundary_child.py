"""Explicit process-local instrumentation; never a production writer."""

import hashlib
import inspect
import json
import os
import sys
from pathlib import Path

from aluclu.alc_r0.attempt_state import RunSpec
from aluclu.alc_r0.manifest_publication import ManifestOwner, PreparedPublication
from aluclu.cognition.persistence import atomic_write_bytes


def main():
    (
        owner_path,
        pages,
        run,
        old_hex,
        old_root,
        new_hex,
        new_root,
        stage,
        mode,
        checkout,
    ) = sys.argv[1:]
    source_path = Path(inspect.getfile(atomic_write_bytes)).resolve()
    expected_path = Path(checkout).resolve() / "src/aluclu/cognition/persistence.py"
    if source_path != expected_path:
        raise RuntimeError("wrong imported atomic writer origin")
    lines, start = inspect.getsourcelines(atomic_write_bytes)
    markers = {
        "temp_write": "handle.write(data)",
        "temp_fsync": "os.fsync(handle.fileno())",
        "pre_replace": "_windows_replace_write_through(temp, target)"
        if os.name == "nt"
        else "os.replace(temp, target)",
        "post_replace": "temp.unlink()",
    }
    if stage == "pre_receipt":
        stop_line = None
    else:
        matches = [
            start + i for i, line in enumerate(lines) if line.strip() == markers[stage]
        ]
        if len(matches) != 1:
            raise RuntimeError("ambiguous atomic boundary")
        stop_line = matches[0]
    owner = ManifestOwner(Path(owner_path), Path(pages), RunSpec(run, False, ("w1",)))
    prepared = PreparedPublication(
        bytes.fromhex(old_hex), old_root, bytes.fromhex(new_hex), new_root
    )
    reached = False

    def trace(frame, event, arg):
        nonlocal reached
        hit = frame.f_code is atomic_write_bytes.__code__ and (
            (stage == "pre_receipt" and event == "return")
            or (event == "line" and frame.f_lineno == stop_line)
        )
        if hit and not reached:
            reached = True
            if Path(frame.f_locals["target"]) != owner.path:
                raise RuntimeError("unexpected instrumented target")
            print(
                json.dumps(
                    dict(
                        stage=stage,
                        mode=mode,
                        pid=os.getpid(),
                        python_version=sys.version,
                        python_executable=sys.executable,
                        source=str(source_path),
                        source_sha256=hashlib.sha256(
                            source_path.read_bytes()
                        ).hexdigest(),
                        line=frame.f_lineno,
                        event=event,
                    )
                ),
                flush=True,
            )
            if mode == "fault":
                raise OSError("explicit isolated publication boundary fault")
            sys.stdin.buffer.read(1)  # Parent terminates exact paused child.
            raise RuntimeError("pause unexpectedly released")
        return trace

    sys.settrace(trace)  # Explicit child-local instrumentation, no module patch.
    try:
        owner.publish(prepared)
    except OSError:
        sys.settrace(None)
        if not reached:
            raise
        print("receipt=false", flush=True)
        return 74
    finally:
        sys.settrace(None)
    raise RuntimeError("boundary was not exercised")


if __name__ == "__main__":
    raise SystemExit(main())
