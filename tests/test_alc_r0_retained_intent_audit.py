"""Published local intent completeness, never global budget/launch authority."""

import hashlib
from dataclasses import FrozenInstanceError

import pytest

from aluclu.alc_r0.attempt_state import RunSpec
from aluclu.alc_r0.canonical import canonical_json_bytes, parse_canonical_json
from aluclu.alc_r0.manifest_publication import ManifestOwner, PublicationError
from aluclu.alc_r0.owned_append import OwnedAppend
from aluclu.alc_r0.retained_intent_audit import audit_retained_intents

ROOT = "a" * 64
SPEC = RunSpec("alc-r0-v1-dev-retained-audit-s20260916", False, ("w1",))


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


def fixture(tmp_path, count=2, rotate=False):
    pages, intents = tmp_path / "pages", tmp_path / "intents"
    pages.mkdir()
    intents.mkdir()
    owner = ManifestOwner(tmp_path / "owner.json", pages, SPEC)
    receipt = owner.create()
    writer = OwnedAppend(owner, intents)
    for kind in ("intent", "start")[:count]:
        receipt = writer.commit(
            writer.prepare(receipt.sha256, event(kind), ROOT, rotate=rotate)
        )
    return writer, receipt


def contents(writer):
    return {
        str(path): path.read_bytes()
        for path in (
            writer.owner.path,
            *writer.intents.glob("*"),
            *writer.owner.pages.glob("*.jsonl"),
        )
        if path.is_file()
    }


@pytest.mark.parametrize(
    "count,rotate", [(0, False), (1, False), (2, False), (2, True)]
)
def test_complete_published_history(tmp_path, count, rotate):
    writer, published = fixture(tmp_path, count, rotate)
    before = contents(writer)
    audit = audit_retained_intents(writer, published.sha256)
    assert audit.publication == published
    assert audit.intent_count == count
    assert audit.intent_bytes == sum(p.stat().st_size for p in writer.intents.glob("*"))
    assert len(audit.history_sha256) == 64
    assert audit_retained_intents(writer, published.sha256) == audit
    assert contents(writer) == before
    with pytest.raises(FrozenInstanceError):
        audit.intent_count = 100


@pytest.mark.parametrize("generation", [1, 2])
def test_missing_history_rejected_without_repair(tmp_path, generation):
    writer, published = fixture(tmp_path)
    (writer.intents / f"intent-{generation:06d}.json").unlink()
    before = contents(writer)
    with pytest.raises((PublicationError, FileNotFoundError)):
        audit_retained_intents(writer, published.sha256)
    assert contents(writer) == before


@pytest.mark.parametrize(
    "field", ["event", "review_sha256", "previous", "candidate", "target", "rotate"]
)
def test_plausible_historical_mutation_rejected(tmp_path, field):
    writer, published = fixture(tmp_path)
    path = writer.intents / "intent-000001.json"
    item = parse_canonical_json(path.read_bytes())
    if field == "event":
        item[field]["source_sha256"] = "b" * 64
    elif field == "review_sha256":
        item[field] = "b" * 64
    elif field in {"previous", "candidate"}:
        item[field]["generation"] = 1 if field == "previous" else 2
    elif field == "target":
        item[field] = 1
    else:
        item[field] = 1  # bool/int separation must survive canonical rebuilding.
    path.write_bytes(canonical_json_bytes(item))
    before = contents(writer)
    with pytest.raises(ValueError):
        audit_retained_intents(writer, published.sha256)
    assert contents(writer) == before


def test_individually_valid_forged_history_does_not_join_current_owner(tmp_path):
    writer, published = fixture(tmp_path)
    path = writer.intents / "intent-000001.json"
    old = parse_canonical_json(path.read_bytes())
    forged = writer._build(
        canonical_json_bytes(old["previous"]),
        old["previous_sha256"],
        event("intent"),
        "b" * 64,
        False,
    )[0]
    # Exact valid transition in isolation, but the next retained predecessor is
    # the original one. A file-local validity check must not bless the fork.
    path.write_bytes(forged.data)
    before = contents(writer)
    with pytest.raises(PublicationError):
        audit_retained_intents(writer, published.sha256)
    assert contents(writer) == before


@pytest.mark.parametrize(
    "payload", [b"", b"{", b"x" * 65537], ids=["empty", "malformed", "oversized"]
)
def test_malformed_bounded_intent_rejected(tmp_path, payload):
    writer, published = fixture(tmp_path)
    (writer.intents / "intent-000001.json").write_bytes(payload)
    before = contents(writer)
    with pytest.raises(ValueError):
        audit_retained_intents(writer, published.sha256)
    assert contents(writer) == before


@pytest.mark.parametrize(
    "name",
    ["intent-000003.json", "intent-000000.json", ".intent-000002.json.1.dead.tmp"],
)
def test_extra_pending_or_orphan_inventory_rejected(tmp_path, name):
    writer, published = fixture(tmp_path)
    (writer.intents / name).write_bytes(b"unacknowledged evidence")
    before = contents(writer)
    with pytest.raises(PublicationError):
        audit_retained_intents(writer, published.sha256)
    assert contents(writer) == before


def test_stale_owner_root_rejected(tmp_path):
    writer, published = fixture(tmp_path)
    before = contents(writer)
    with pytest.raises(PublicationError):
        audit_retained_intents(writer, "b" * 64)
    assert contents(writer) == before


def test_receipt_root_binds_all_intent_bytes(tmp_path):
    writer, published = fixture(tmp_path)
    audit = audit_retained_intents(writer, published.sha256)
    item = parse_canonical_json(published.data)
    digest = hashlib.sha256(b"ALC-R0-RETAINED-INTENT-AUDIT-V1\0")
    digest.update(bytes.fromhex(item["spec_sha256"]))
    digest.update(bytes.fromhex(published.sha256))
    for generation in range(1, 3):
        data = (writer.intents / f"intent-{generation:06d}.json").read_bytes()
        digest.update(generation.to_bytes(8, "big"))
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    assert audit.history_sha256 == digest.hexdigest()


def test_exact_coordinator_required(tmp_path):
    writer, published = fixture(tmp_path)

    class Subclass(OwnedAppend):
        pass

    with pytest.raises(PublicationError):
        audit_retained_intents(Subclass(writer.owner, writer.intents), published.sha256)


@pytest.mark.parametrize("unsafe", ["directory", "hardlink"])
def test_unsafe_retained_file_rejected(tmp_path, unsafe):
    writer, published = fixture(tmp_path)
    path = writer.intents / "intent-000001.json"
    if unsafe == "directory":
        path.unlink()
        path.mkdir()
    else:
        (tmp_path / "owned-extra-link").hardlink_to(path)
    before = contents(writer)
    with pytest.raises(PublicationError):
        audit_retained_intents(writer, published.sha256)
    assert contents(writer) == before


def test_actual_pending_intent_is_not_adopted_by_audit(tmp_path):
    writer, published = fixture(tmp_path, 1)

    class LostAdvance(OwnedAppend):
        def _advance(self, *args):
            raise OSError("owned fixture: durable pending intent, no page mutation")

    interrupted = LostAdvance(writer.owner, writer.intents)
    intent = interrupted.prepare(published.sha256, event("start"), ROOT)
    with pytest.raises(OSError):
        interrupted.commit(intent)
    before = contents(writer)
    with pytest.raises(PublicationError):
        audit_retained_intents(writer, published.sha256)
    assert contents(writer) == before
    # Only the existing explicitly supplied recovery path can publish it.
    resumed = writer.resume(intent)
    assert audit_retained_intents(writer, resumed.sha256).intent_count == 2
