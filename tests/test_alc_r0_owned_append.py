import hashlib

import pytest

from aluclu.alc_r0.attempt_state import RunSpec
from aluclu.alc_r0.canonical import canonical_json_bytes, parse_canonical_json
from aluclu.alc_r0.manifest_publication import ManifestOwner
from aluclu.alc_r0.owned_append import OwnedAppend

ROOT = "a" * 64
SPEC = RunSpec("alc-r0-v1-dev-owned-s20260916", False, ("w1",))


def event(kind="intent"):
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


def setup(tmp_path, cls=OwnedAppend):
    pages, intents = tmp_path / "pages", tmp_path / "intents"
    pages.mkdir()
    intents.mkdir()
    owner = ManifestOwner(tmp_path / "owner.json", pages, SPEC)
    return cls(owner, intents), owner.create()


def test_first_same_page_rotation_and_completed_restart(tmp_path):
    writer, old = setup(tmp_path)
    intent = writer.prepare(old.sha256, event(), ROOT)
    assert not list(writer.owner.pages.iterdir())
    assert not list(writer.intents.iterdir())
    assert hashlib.sha256(intent.data).hexdigest() == intent.sha256
    first = writer.commit(intent)
    assert parse_canonical_json(first.data)["generation"] == 1
    restarted = OwnedAppend(writer.owner, writer.intents)
    assert restarted.resume(intent) == first
    assert restarted.resume(intent) == first
    second_intent = restarted.prepare(first.sha256, event("start"), ROOT, rotate=True)
    second = restarted.commit(second_intent)
    assert len(parse_canonical_json(second.data)["manifest"]["pages"]) == 2
    assert sum(len(a.events) for a in second.view.attempts) == 2


def test_semantic_invalid_event_does_not_write(tmp_path):
    writer, old = setup(tmp_path)
    with pytest.raises(ValueError):
        writer.prepare(old.sha256, event("start"), ROOT)
    assert writer.owner.path.read_bytes() == old.data
    assert not list(writer.intents.iterdir())
    assert not list(writer.owner.pages.iterdir())


class InterruptedAppend(OwnedAppend):
    def _publish(self, prepared):
        raise OSError("owned fixture: page durable, publication not started")


def test_resume_exact_appended_page_never_duplicates(tmp_path):
    writer, old = setup(tmp_path, InterruptedAppend)
    intent = writer.prepare(old.sha256, event(), ROOT)
    with pytest.raises(OSError):
        writer.commit(intent)
    assert writer.owner.path.read_bytes() == old.data
    before = (writer.owner.pages / "page-0000.jsonl").read_bytes()
    receipt = OwnedAppend(writer.owner, writer.intents).resume(intent)
    assert (writer.owner.pages / "page-0000.jsonl").read_bytes() == before
    assert len(receipt.view.attempts[0].events) == 1


class InterruptedIntent(OwnedAppend):
    def _advance(self, intent, prepared, journal, prior, next_head, new_page):
        raise OSError("owned fixture: durable intent only")


def test_resume_durable_intent_before_page_creation(tmp_path):
    writer, old = setup(tmp_path, InterruptedIntent)
    intent = writer.prepare(old.sha256, event(), ROOT)
    with pytest.raises(OSError):
        writer.commit(intent)
    assert not list(writer.owner.pages.iterdir())
    assert len(list(writer.intents.iterdir())) == 1
    assert OwnedAppend(writer.owner, writer.intents).resume(intent).sha256 != old.sha256


def test_competing_intents_stale_predecessor_rejected(tmp_path):
    writer, old = setup(tmp_path)
    one = writer.prepare(old.sha256, event(), ROOT)
    two = writer.prepare(old.sha256, event(), "b" * 64)
    receipt = writer.commit(one)
    with pytest.raises(ValueError):
        writer.commit(two)
    assert writer.owner.read(receipt.sha256) == receipt


def test_partial_page_resume_rejects_without_repair(tmp_path):
    writer, old = setup(tmp_path, InterruptedAppend)
    intent = writer.prepare(old.sha256, event(), ROOT)
    with pytest.raises(OSError):
        writer.commit(intent)
    path = writer.owner.pages / "page-0000.jsonl"
    data = path.read_bytes()[:-1]
    path.write_bytes(data)  # Own malformed fixture, not application mutation.
    with pytest.raises((ValueError, RuntimeError)):
        OwnedAppend(writer.owner, writer.intents).resume(intent)
    assert path.read_bytes() == data
    assert writer.owner.path.read_bytes() == old.data


class InterruptedEmptyPage(OwnedAppend):
    def _advance(self, intent, prepared, journal, prior, next_head, new_page):
        journal.create()
        raise OSError("owned fixture: empty page created")


class InterruptedPublication(OwnedAppend):
    def _publish(self, prepared):
        self.owner.publish(prepared)
        raise OSError("owned fixture: published, no response")


@pytest.mark.parametrize("cls", [InterruptedEmptyPage, InterruptedPublication])
def test_explicit_restart_empty_page_or_published_without_response(tmp_path, cls):
    writer, old = setup(tmp_path, cls)
    intent = writer.prepare(old.sha256, event(), ROOT)
    with pytest.raises(OSError):
        writer.commit(intent)
    receipt = OwnedAppend(writer.owner, writer.intents).resume(intent)
    assert parse_canonical_json(receipt.data)["generation"] == 1
    assert len(receipt.view.attempts[0].events) == 1


@pytest.mark.parametrize("mutation", ["root", "candidate", "bool_target", "extra"])
def test_intent_exact_rebuild_rejects_before_mutation(tmp_path, mutation):
    from aluclu.alc_r0.owned_append import AppendIntent

    writer, old = setup(tmp_path)
    intent = writer.prepare(old.sha256, event(), ROOT)
    item = parse_canonical_json(intent.data)
    if mutation == "root":
        corrupt = AppendIntent(intent.data, "b" * 64)
    else:
        if mutation == "candidate":
            item["candidate"]["generation"] = 2
        elif mutation == "bool_target":
            item["target"] = False
        else:
            item["extra"] = 1
        data = canonical_json_bytes(item)
        corrupt = AppendIntent(data, hashlib.sha256(data).hexdigest())
    with pytest.raises(ValueError):
        writer.commit(corrupt)
    assert writer.owner.path.read_bytes() == old.data
    assert not list(writer.intents.iterdir())
    assert not list(writer.owner.pages.iterdir())


def test_same_page_and_concurrent_single_predecessor(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    writer, old = setup(tmp_path)
    intent = writer.prepare(old.sha256, event(), ROOT)

    def commit():
        try:
            return writer.commit(intent)
        except ValueError:
            return None

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(lambda _: commit(), range(2)))
    receipts = [r for r in results if r is not None]
    assert len(receipts) == 1
    next_intent = writer.prepare(receipts[0].sha256, event("start"), ROOT)
    receipt = writer.commit(next_intent)
    assert len(parse_canonical_json(receipt.data)["manifest"]["pages"]) == 1
    assert len(receipt.view.attempts[0].events) == 2


def test_unrecorded_page_cannot_be_adopted_by_commit(tmp_path):
    from aluclu.alc_r0.attempt_journal import AttemptJournal
    from aluclu.alc_r0.paged_history import declaration_root, page_identity

    writer, old = setup(tmp_path)
    intent = writer.prepare(old.sha256, event(), ROOT)
    journal = AttemptJournal(
        writer.owner.pages / "page-0000.jsonl",
        page_identity(declaration_root(SPEC), 0, None),
    )
    journal.append(journal.create(), event())
    before = journal.path.read_bytes()
    with pytest.raises(ValueError):
        writer.commit(intent)
    assert journal.path.read_bytes() == before
    assert not list(writer.intents.iterdir())


def test_reconcile_exact_page_rejects_wrong_head(tmp_path):
    from aluclu.alc_r0.attempt_journal import AttemptJournal, JournalConflict

    writer, old = setup(tmp_path, InterruptedAppend)
    intent = writer.prepare(old.sha256, event(), ROOT)
    with pytest.raises(OSError):
        writer.commit(intent)
    item = parse_canonical_json(intent.data)
    from aluclu.alc_r0.attempt_journal import JournalHead

    journal = AttemptJournal(writer.owner.pages / "page-0000.jsonl", item["journal_id"])
    head = JournalHead(**item["next"])
    assert journal.reconcile(head).head == head
    with pytest.raises(JournalConflict):
        journal.reconcile(JournalHead(**item["prior"]))


def test_actual_65536_record_rotation_preserves_entire_declared_work(tmp_path):
    from dataclasses import asdict

    from aluclu.alc_r0.attempt_journal import AttemptJournal, plan_journal_append
    from aluclu.alc_r0.manifest_publication import prepare_publication
    from aluclu.alc_r0.paged_history import declaration_root, page_identity

    spec = RunSpec(SPEC.run_id, False, tuple(f"w{i}" for i in range(65536)))
    pages, intents = tmp_path / "pages", tmp_path / "intents"
    pages.mkdir()
    intents.mkdir()
    owner = ManifestOwner(tmp_path / "owner.json", pages, spec)
    old = owner.create()
    journal = AttemptJournal(
        pages / "page-0000.jsonl", page_identity(declaration_root(spec), 0, None)
    )
    head = journal._genesis()
    raw = bytearray()
    events = [event(), event("start")]
    events.extend(
        canonical_json_bytes(
            dict(
                run_id=spec.run_id,
                attempt_id="a001",
                kind="work",
                work_id=w,
                evidence_sha256=ROOT,
            )
        )
        for w in spec.work_ids
    )
    # Bulk prior-state fixture; rotation and next two writes use ACTUAL coordinator.
    for data in events[:65536]:
        planned = plan_journal_append(journal.journal_id, head, data)
        raw.extend(planned.line)
        head = planned.head
    journal.path.write_bytes(raw)
    manifest = canonical_json_bytes(
        dict(version=1, spec_sha256=declaration_root(spec), pages=[asdict(head)])
    )
    initial = owner.publish(
        prepare_publication(
            spec,
            old.data,
            old.sha256,
            manifest,
            hashlib.sha256(manifest).hexdigest(),
            ROOT,
        )
    )
    writer = OwnedAppend(owner, intents)
    receipt = initial
    for data in events[65536:]:
        receipt = writer.commit(writer.prepare(receipt.sha256, data, ROOT))
    assert [
        h["count"] for h in parse_canonical_json(receipt.data)["manifest"]["pages"]
    ] == [65536, 2]
    assert receipt.view.attempts[0].events == tuple(events)
    assert receipt.view.attempts[0].work == tuple((w, ROOT) for w in spec.work_ids)
    assert journal.path.read_bytes() == raw


def test_owner_lock_blocks_competitor_inside_publication(tmp_path):
    from concurrent.futures import ThreadPoolExecutor, TimeoutError
    from threading import Event

    entered, release, second_started = Event(), Event(), Event()

    class PublicationBarrier(OwnedAppend):
        def _publish(self, prepared):
            entered.set()
            if not release.wait(10):
                raise TimeoutError("owned publication barrier timed out")
            return super()._publish(prepared)

    writer, old = setup(tmp_path, PublicationBarrier)
    intent = writer.prepare(old.sha256, event(), ROOT)
    other = OwnedAppend(writer.owner, writer.intents)

    def competing_commit():
        second_started.set()
        return other.commit(intent)

    with ThreadPoolExecutor(2) as pool:
        first = pool.submit(writer.commit, intent)
        try:
            assert entered.wait(10)
            target = writer.owner.pages / "page-0000.jsonl"
            before = target.read_bytes()
            second = pool.submit(competing_commit)
            assert second_started.wait(10)
            with pytest.raises(TimeoutError):
                second.result(timeout=0.25)
            assert writer.owner.path.read_bytes() == old.data
            assert target.read_bytes() == before
        finally:
            release.set()
        receipt = first.result(timeout=10)
        with pytest.raises(ValueError):
            second.result(timeout=10)
        assert writer.owner.read(receipt.sha256) == receipt
        assert target.read_bytes() == before


def test_resume_fsync_descriptor_failure_never_publishes(tmp_path):
    from aluclu.alc_r0.attempt_journal import AttemptJournal

    class ClosedAtFlush:
        """Owned fixture closes descriptor after scan, before REAL os.fsync."""

        def __init__(self, handle):
            self.handle = handle
            self.fd = handle.fileno()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.handle.close()

        def __getattr__(self, name):
            return getattr(self.handle, name)

        def fileno(self):
            return self.fd

        def flush(self):
            self.handle.flush()
            self.handle.close()

    class BadSyncJournal(AttemptJournal):
        def _open(self, mode):
            handle = super()._open(mode)
            return ClosedAtFlush(handle) if mode == "r+b" else handle

    class ReflushFailure(OwnedAppend):
        def _advance(self, intent, prepared, journal, prior, next_head, new_page):
            failing = BadSyncJournal(journal.path, journal.journal_id)
            return super()._advance(
                intent, prepared, failing, prior, next_head, new_page
            )

    writer, old = setup(tmp_path, InterruptedAppend)
    intent = writer.prepare(old.sha256, event(), ROOT)
    with pytest.raises(OSError):
        writer.commit(intent)
    target = writer.owner.pages / "page-0000.jsonl"
    before = target.read_bytes()
    with pytest.raises(OSError):
        ReflushFailure(writer.owner, writer.intents).resume(intent)
    assert writer.owner.path.read_bytes() == old.data
    assert target.read_bytes() == before
    receipt = OwnedAppend(writer.owner, writer.intents).resume(intent)
    assert len(receipt.view.attempts[0].events) == 1
