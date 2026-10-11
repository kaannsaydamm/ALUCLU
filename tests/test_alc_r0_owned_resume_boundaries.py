"""Interrupted recovery of pinned storage intent, never an experiment retry."""

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
from aluclu.alc_r0.manifest_publication import ManifestOwner, PublicationError
from aluclu.alc_r0.owned_append import OwnedAppend

ROOT = "a" * 64
SPEC = RunSpec("alc-r0-v1-dev-owned-resume-s20260916", False, ("w1",))
STATES = {
    "absent": (
        "intent_prewrite",
        "intent_ack",
        "page_created",
        "append_prewrite",
        "append_presync",
        "append_ack",
        "owner_prereplace",
        "owner_postreplace",
        "owner_ack",
        "resume_receipt",
    ),
    "empty": (
        "intent_ack",
        "reconcile_presync",
        "reconcile_ack",
        "append_ack",
        "resume_receipt",
    ),
    "prior": ("reconcile_presync", "reconcile_ack", "append_presync", "resume_receipt"),
    "next": (
        "intent_prewrite",
        "intent_atomic_prereplace",
        "intent_atomic_postreplace",
        "intent_ack",
        "reconcile_presync",
        "reconcile_ack",
        "owner_prereplace",
        "owner_postreplace",
        "owner_ack",
        "resume_receipt",
    ),
    "candidate": (
        "intent_prewrite",
        "intent_atomic_prereplace",
        "intent_atomic_postreplace",
        "intent_ack",
        "reconcile_presync",
        "reconcile_ack",
        "owner_prereplace",
        "owner_postreplace",
        "owner_ack",
        "resume_receipt",
    ),
    "rotate_next": ("reconcile_presync", "owner_postreplace", "resume_receipt"),
    "rotate_candidate": ("reconcile_presync", "owner_postreplace", "resume_receipt"),
}
CASES = [(state, stage) for state, stages in STATES.items() for stage in stages]


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


class LostAdvance(OwnedAppend):
    def _advance(self, intent, prepared, journal, prior, next_head, new_page):
        raise OSError("owned fixture: retained intent, prior page state")


class LostEmpty(OwnedAppend):
    def _advance(self, intent, prepared, journal, prior, next_head, new_page):
        journal.create()
        raise OSError("owned fixture: retained intent and empty created page")


class LostPublish(OwnedAppend):
    def _publish(self, prepared):
        raise OSError("owned fixture: retained intent and exact next page")


class LostResponse(OwnedAppend):
    def _publish(self, prepared):
        self.owner.publish(prepared)
        raise OSError("owned fixture: exact candidate owner, response lost")


def pending(tmp_path, state):
    pages, intents = tmp_path / "pages", tmp_path / "intents"
    pages.mkdir()
    intents.mkdir()
    owner = ManifestOwner(tmp_path / "owner.json", pages, SPEC)
    old = owner.create()
    writer = OwnedAppend(owner, intents)
    earlier = ()
    if state == "prior" or state.startswith("rotate_"):
        earlier = (event("intent"),)
        old = writer.commit(writer.prepare(old.sha256, earlier[0], ROOT))
    new_event = event("start" if earlier else "intent")
    cls = {
        "absent": LostAdvance,
        "empty": LostEmpty,
        "prior": LostAdvance,
        "next": LostPublish,
        "candidate": LostResponse,
        "rotate_next": LostPublish,
        "rotate_candidate": LostResponse,
    }[state]
    interrupted = cls(owner, intents)
    intent = interrupted.prepare(
        old.sha256, new_event, ROOT, rotate=state.startswith("rotate_")
    )
    with pytest.raises(OSError):
        interrupted.commit(intent)
    return owner, intents, old, intent, earlier + (new_event,)


def interrupt_resume(owner, intents, intent, stage, mode):
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
        str(owner.pages),
        str(intents),
        SPEC.run_id,
        intent.data.hex(),
        intent.sha256,
        stage,
        mode,
        str(checkout),
        json.dumps(sources),
        "resume",
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
            marker = json.loads(reader.submit(child.stdout.readline).result(timeout=45))
            assert marker["stage"] == stage and marker["mode"] == mode
            assert marker["operation"] == "resume"
            assert marker["pid"] == child.pid
            assert marker["python_version"] == sys.version
            assert (
                Path(marker["python_executable"]).resolve()
                == Path(sys._base_executable).resolve()
            )
            assert Path(marker["checkout"]) == checkout and marker["sources"] == sources
            assert marker["intent_sha256"] == intent.sha256
            if mode == "kill":
                assert child.poll() is None
                child.kill()  # Exact created child only, never a discovered PID.
            stdout, stderr = child.communicate(timeout=15)
            if mode == "fault":
                assert child.returncode == 74, stderr.decode(errors="replace")
                assert b"receipt=false" in stdout
            else:
                assert child.returncode != 0 and b"receipt=false" not in stdout
        finally:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=15)
    assert child.poll() is not None


@pytest.mark.parametrize("state,stage", CASES)
@pytest.mark.parametrize("mode", ["fault", "kill"])
def test_actual_resume_child_boundary(tmp_path, state, stage, mode):
    owner, intents, old, intent, expected_events = pending(tmp_path, state)
    item = parse_canonical_json(intent.data)
    candidate = canonical_json_bytes(item["candidate"])
    target = owner.pages / f"page-{item['target']:04d}.jsonl"
    initial_pages = {p.name: p.read_bytes() for p in owner.pages.glob("*.jsonl")}
    initial_owner = owner.path.read_bytes()
    interrupt_resume(owner, intents, intent, stage, mode)
    published = "candidate" in state or stage in {
        "owner_postreplace",
        "owner_ack",
        "resume_receipt",
    }
    assert owner.path.read_bytes() == (candidate if published else initial_owner)
    intent_path = intents / f"intent-{item['candidate']['generation']:06d}.json"
    assert intent_path.read_bytes() == intent.data
    if stage == "intent_atomic_prereplace" and mode == "kill":
        # Atomic rewrite left an unacknowledged temporary file. Closed inventory
        # rejects the extra entry: no automatic deletion, adoption or retry.
        inventory = {p.name: p.read_bytes() for p in intents.iterdir()}
        assert any(name.endswith(".tmp") for name in inventory)
        with pytest.raises(PublicationError, match="inventory"):
            OwnedAppend(owner, intents).resume(intent)
        assert {p.name: p.read_bytes() for p in intents.iterdir()} == inventory
        assert {
            p.name: p.read_bytes() for p in owner.pages.glob("*.jsonl")
        } == initial_pages
        assert owner.path.read_bytes() == initial_owner
        return
    before = target.read_bytes() if target.exists() else None
    receipt = OwnedAppend(owner, intents).resume(intent)
    assert receipt.data == candidate and receipt.sha256 == item["candidate_sha256"]
    assert (
        parse_canonical_json(receipt.data)["generation"]
        == item["candidate"]["generation"]
    )
    assert receipt.view.attempts[0].events == expected_events
    if state in {"next", "candidate", "rotate_next", "rotate_candidate"}:
        assert target.read_bytes() == initial_pages[target.name]
    if stage in {
        "append_presync",
        "append_ack",
        "owner_prereplace",
        "owner_postreplace",
        "owner_ack",
        "resume_receipt",
    }:
        assert target.read_bytes() == before
    for name, data in initial_pages.items():
        if name != target.name:
            assert (owner.pages / name).read_bytes() == data
    if state in {"next", "candidate"} and stage == "resume_receipt":
        interrupt_resume(
            owner, intents, intent, stage, mode
        )  # Cut recovery a SECOND time.
        assert OwnedAppend(owner, intents).resume(intent) == receipt
    assert OwnedAppend(owner, intents).resume(intent) == receipt
    assert len(receipt.view.attempts[0].events) == len(expected_events)
