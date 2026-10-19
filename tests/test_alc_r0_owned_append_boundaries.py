"""Real owned children and Python call boundaries; NOT power-loss simulation."""

import hashlib
import json
import os
import subprocess
import sys
import sysconfig
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from aluclu.alc_r0.attempt_state import RunSpec
from aluclu.alc_r0.canonical import canonical_json_bytes, parse_canonical_json
from aluclu.alc_r0.manifest_publication import ManifestOwner
from aluclu.alc_r0.owned_append import OwnedAppend

ROOT = "a" * 64
SPEC = RunSpec("alc-r0-v1-dev-owned-boundary-s20260916", False, ("w1",))
STAGES = (
    "intent_prewrite",
    "intent_ack",
    "page_created",
    "append_prewrite",
    "append_presync",
    "append_ack",
    "owner_prereplace",
    "owner_postreplace",
    "owner_ack",
    "commit_receipt",
)
CASES = [
    (layout, stage)
    for layout in ("first", "same", "rotate")
    for stage in STAGES
    if not (layout == "same" and stage == "page_created")
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def event(kind):
    fields = dict(run_id=SPEC.run_id, attempt_id="a001", kind=kind)
    if kind == "intent":
        fields.update(
            source_sha256=ROOT,
            invocation_sha256=ROOT,
            retry_kind="INITIAL",
            prior_source_sha256=None,
            prior_artifact_sha256=None,
            review_sha256=None,
        )
    else:
        fields.update(receipt_sha256=ROOT)
    return canonical_json_bytes(fields)


@pytest.mark.parametrize("layout,stage", CASES)
@pytest.mark.parametrize("mode", ["fault", "kill"])
def test_actual_coordinator_child_boundary(tmp_path, layout, stage, mode):
    pages, intents = tmp_path / "pages", tmp_path / "intents"
    pages.mkdir()
    intents.mkdir()
    owner = ManifestOwner(tmp_path / "owner.json", pages, SPEC)
    old = owner.create()
    writer = OwnedAppend(owner, intents)
    if layout != "first":
        old = writer.commit(writer.prepare(old.sha256, event("intent"), ROOT))
    old_events = () if layout == "first" else (event("intent"),)
    proposed = event("intent" if layout == "first" else "start")
    intent = writer.prepare(old.sha256, proposed, ROOT, rotate=layout == "rotate")
    item = parse_canonical_json(intent.data)
    target = pages / f"page-{item['target']:04d}.jsonl"
    prior_page_bytes = {p.name: p.read_bytes() for p in pages.glob("*.jsonl")}
    candidate = canonical_json_bytes(item["candidate"])
    generation = item["candidate"]["generation"]
    intent_path = intents / f"intent-{generation:06d}.json"
    checkout = Path(__file__).resolve().parents[1]
    sources = {
        name: digest((checkout / name).read_bytes())
        for name in (
            "src/aluclu/alc_r0/owned_append.py",
            "src/aluclu/alc_r0/attempt_journal.py",
            "src/aluclu/alc_r0/manifest_publication.py",
            "src/aluclu/cognition/persistence.py",
        )
    }
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        dict.fromkeys(
            [
                str(checkout / "src"),
                sysconfig.get_paths()["purelib"],
                sysconfig.get_paths()["platlib"],
            ]
        )
    )
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment.pop("ALUCLU_R0_SNAPSHOT", None)
    args = [
        sys._base_executable,
        "-B",
        str(checkout / "tests/helpers/owned_append_boundary_child.py"),
        str(owner.path),
        str(pages),
        str(intents),
        SPEC.run_id,
        intent.data.hex(),
        intent.sha256,
        stage,
        mode,
        str(checkout),
        json.dumps(sources),
    ]
    child = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
    )
    with ThreadPoolExecutor(max_workers=1) as reader:
        try:
            line = reader.submit(child.stdout.readline).result(timeout=45)
            marker = json.loads(line)
            assert marker["stage"] == stage and marker["mode"] == mode
            assert marker["pid"] == child.pid
            assert marker["python_version"] == sys.version
            assert (
                Path(marker["python_executable"]).resolve()
                == Path(sys._base_executable).resolve()
            )
            assert marker["sources"] == sources
            assert Path(marker["checkout"]) == checkout
            assert marker["intent_sha256"] == intent.sha256
            if mode == "kill":
                assert child.poll() is None
                child.kill()  # Exact created Popen child; never a discovered PID.
            stdout, stderr = child.communicate(timeout=15)
            if mode == "fault":
                assert child.returncode == 74, stderr.decode(errors="replace")
                assert b"receipt=false" in stdout
            else:
                assert child.returncode != 0
                assert b"receipt=false" not in stdout
        finally:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=15)
    assert child.poll() is not None
    visible_candidate = stage in {"owner_postreplace", "owner_ack", "commit_receipt"}
    assert owner.path.read_bytes() == (candidate if visible_candidate else old.data)
    if stage == "intent_prewrite":
        assert not intent_path.exists()
        assert {
            p.name: p.read_bytes() for p in pages.glob("*.jsonl")
        } == prior_page_bytes
        with pytest.raises(FileNotFoundError):
            OwnedAppend(owner, intents).resume(intent)
        assert owner.path.read_bytes() == old.data
        return
    assert intent_path.read_bytes() == intent.data
    if stage == "intent_ack":
        assert {
            p.name: p.read_bytes() for p in pages.glob("*.jsonl")
        } == prior_page_bytes
    if stage == "page_created":
        assert target.read_bytes() == b""
    before_resume = target.read_bytes() if target.exists() else None
    resumed = OwnedAppend(owner, intents).resume(intent)
    assert resumed.data == candidate and resumed.sha256 == item["candidate_sha256"]
    assert parse_canonical_json(resumed.data)["generation"] == generation
    assert resumed.view.attempts[0].events == old_events + (proposed,)
    after_resume = target.read_bytes()
    if stage in {
        "append_presync",
        "append_ack",
        "owner_prereplace",
        "owner_postreplace",
        "owner_ack",
        "commit_receipt",
    }:
        assert (
            before_resume == after_resume
        )  # Never duplicate a visible intended event.
    assert OwnedAppend(owner, intents).resume(intent) == resumed
    assert target.read_bytes() == after_resume
    for name, data in prior_page_bytes.items():
        if name != target.name:
            assert (pages / name).read_bytes() == data


def test_owner_ack_never_marks_exceptional_atomic_return(tmp_path):
    pages, intents = tmp_path / "pages", tmp_path / "intents"
    pages.mkdir()
    intents.mkdir()
    owner = ManifestOwner(tmp_path / "owner.json", pages, SPEC)
    old = owner.create()
    writer = OwnedAppend(owner, intents)
    intent = writer.prepare(old.sha256, event("intent"), ROOT)
    checkout = Path(__file__).resolve().parents[1]
    sources = {
        name: digest((checkout / name).read_bytes())
        for name in (
            "src/aluclu/alc_r0/owned_append.py",
            "src/aluclu/alc_r0/attempt_journal.py",
            "src/aluclu/alc_r0/manifest_publication.py",
            "src/aluclu/cognition/persistence.py",
        )
    }
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        dict.fromkeys(
            [
                str(checkout / "src"),
                sysconfig.get_paths()["purelib"],
                sysconfig.get_paths()["platlib"],
            ]
        )
    )
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment.pop("ALUCLU_R0_SNAPSHOT", None)
    result = subprocess.run(
        [
            sys._base_executable,
            "-B",
            str(checkout / "tests/helpers/owned_append_boundary_child.py"),
            str(owner.path),
            str(pages),
            str(intents),
            SPEC.run_id,
            intent.data.hex(),
            intent.sha256,
            "owner_ack",
            "cleanup_error",
            str(checkout),
            json.dumps(sources),
        ],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=45,
        env=environment,
    )
    # Fixture creates a directory at the MOVED temporary path. Actual atomic
    # cleanup unlink then raises an OS error after replacement, not a trace throw.
    assert b"cleanup_error_injected=true" in result.stdout
    assert result.returncode == 1
    assert b'"stage"' not in result.stdout  # No false successful owner acknowledgement.
    item = parse_canonical_json(intent.data)
    assert owner.path.read_bytes() == canonical_json_bytes(item["candidate"])
    assert writer.resume(intent).view.attempts[0].events == (event("intent"),)
