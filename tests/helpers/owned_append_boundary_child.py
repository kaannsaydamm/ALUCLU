"""Isolated Python boundary tracer. No production edits or global module patch."""

import hashlib
import inspect
import json
import os
import sys
from pathlib import Path

from aluclu.alc_r0.attempt_journal import AttemptJournal
from aluclu.alc_r0.attempt_state import RunSpec
from aluclu.alc_r0.canonical import parse_canonical_json
from aluclu.alc_r0.manifest_publication import ManifestOwner
from aluclu.alc_r0.owned_append import AppendIntent, OwnedAppend
from aluclu.cognition.persistence import atomic_write_bytes


def main():
    (
        owner_path,
        pages,
        intents,
        run,
        intent_hex,
        intent_root,
        stage,
        mode,
        checkout_text,
        expected_sources_text,
    ) = sys.argv[1:]
    checkout = Path(checkout_text).resolve()
    expected_sources = json.loads(expected_sources_text)
    funcs = {
        "src/aluclu/alc_r0/owned_append.py": OwnedAppend.commit,
        "src/aluclu/alc_r0/attempt_journal.py": AttemptJournal.append,
        "src/aluclu/alc_r0/manifest_publication.py": ManifestOwner._commit,
        "src/aluclu/cognition/persistence.py": atomic_write_bytes,
    }
    observed_sources = {}
    for name, func in funcs.items():
        source = Path(inspect.getfile(func)).resolve()
        if source != checkout / name:
            raise RuntimeError("wrong imported coordinator/writer origin")
        observed_sources[name] = hashlib.sha256(source.read_bytes()).hexdigest()
    if observed_sources != expected_sources:
        raise RuntimeError("source root mismatch")
    if mode not in {"fault", "kill", "cleanup_error"}:
        raise RuntimeError("unsupported owned fixture mode")
    if mode == "cleanup_error" and stage != "owner_ack":
        raise RuntimeError("cleanup error is only a negative acknowledgement control")
    owner = ManifestOwner(Path(owner_path), Path(pages), RunSpec(run, False, ("w1",)))
    writer = OwnedAppend(owner, Path(intents))
    intent = AppendIntent(bytes.fromhex(intent_hex), intent_root)
    item = parse_canonical_json(intent.data)
    target = owner.pages / f"page-{item['target']:04d}.jsonl"
    intent_path = writer.intents / f"intent-{item['candidate']['generation']:06d}.json"
    replace_line = (
        "_windows_replace_write_through(temp, target)"
        if os.name == "nt"
        else "os.replace(temp, target)"
    )
    boundaries = {
        "intent_prewrite": (
            OwnedAppend._persist,
            "atomic_write_bytes(path, intent.data)",
        ),
        "intent_ack": (OwnedAppend._persist, None),
        "page_created": (AttemptJournal.create, None),
        "append_prewrite": (
            AttemptJournal.append,
            "if handle.write(line) != len(line):",
        ),
        "append_presync": (AttemptJournal.append, "os.fsync(handle.fileno())"),
        "append_ack": (AttemptJournal.append, None),
        "owner_prereplace": (atomic_write_bytes, replace_line),
        "owner_postreplace": (atomic_write_bytes, "temp.unlink()"),
        # Reachable ONLY after atomic_write_bytes returned successfully. Atomic
        # trace 'return' can also mean exception unwinding, so never use it as ack.
        "owner_ack": (ManifestOwner._commit, "return PublishedManifest("),
        "commit_receipt": (OwnedAppend.commit, None),
    }
    func, needle = boundaries[stage]
    stop_line = None
    if needle is not None:
        lines, start = inspect.getsourcelines(func)
        matches = [start + i for i, line in enumerate(lines) if line.strip() == needle]
        if len(matches) != 1:
            raise RuntimeError("ambiguous coordinator boundary")
        stop_line = matches[0]
    reached = False
    exceptional_frames = set()
    cleanup_injected = False
    atomic_lines, atomic_start = inspect.getsourcelines(atomic_write_bytes)
    cleanup_matches = [
        atomic_start + i
        for i, line in enumerate(atomic_lines)
        if line.strip() == "temp.unlink()"
    ]
    if len(cleanup_matches) != 1:
        raise RuntimeError("ambiguous cleanup negative control")

    def trace(frame, event, arg):
        nonlocal reached, cleanup_injected
        if (
            mode == "cleanup_error"
            and not cleanup_injected
            and frame.f_code is atomic_write_bytes.__code__
            and event == "line"
            and frame.f_lineno == cleanup_matches[0]
            and Path(frame.f_locals["target"]) == owner.path
        ):
            temp = Path(frame.f_locals["temp"])
            if temp.parent != owner.path.parent or temp == owner.path or temp.exists():
                raise RuntimeError("unsafe owned temporary-path negative control")
            # Explicit fixture only: replacement MOVED this temporary file. The
            # actual cleanup's unlink(directory) raises; tracing remains enabled
            # and observes exceptional unwinding, so a false return marker fails.
            temp.mkdir()
            cleanup_injected = True
            print("cleanup_error_injected=true", flush=True)
        if frame.f_code is not func.__code__:
            return trace
        if event == "exception" and func is not atomic_write_bytes:
            exceptional_frames.add(id(frame))
        hit = (
            needle is None and event == "return" and id(frame) not in exceptional_frames
        ) or (needle is not None and event == "line" and frame.f_lineno == stop_line)
        if not hit or reached:
            return trace
        if func is atomic_write_bytes:
            if Path(frame.f_locals["target"]) != owner.path:
                return trace  # Ignore intent and page atomic writers.
        elif func is OwnedAppend._persist:
            if Path(frame.f_locals["path"]) != intent_path:
                raise RuntimeError("unexpected intent target")
        elif func in (AttemptJournal.create, AttemptJournal.append):
            if frame.f_locals["self"].path != target:
                raise RuntimeError("unexpected journal target")
        elif func is ManifestOwner._commit:
            if frame.f_locals["self"].path != owner.path:
                raise RuntimeError("unexpected publication owner")
        elif frame.f_locals["self"].owner.path != owner.path:
            raise RuntimeError("unexpected coordinator owner")
        reached = True
        print(
            json.dumps(
                dict(
                    stage=stage,
                    mode=mode,
                    pid=os.getpid(),
                    python_version=sys.version,
                    python_executable=sys.executable,
                    checkout=str(checkout),
                    sources=observed_sources,
                    intent_sha256=intent.sha256,
                    line=frame.f_lineno,
                    event=event,
                )
            ),
            flush=True,
        )
        if mode != "kill":
            raise OSError("explicit isolated coordinator boundary fault")
        sys.stdin.buffer.read(1)  # Parent kills exact created paused worker.
        raise RuntimeError("owned pause unexpectedly released")

    sys.settrace(trace)
    try:
        writer.commit(intent)
    except OSError:
        sys.settrace(None)
        if not reached:
            raise
        print("receipt=false", flush=True)
        return 74
    finally:
        sys.settrace(None)
    raise RuntimeError("requested coordinator boundary was not exercised")


if __name__ == "__main__":
    raise SystemExit(main())
