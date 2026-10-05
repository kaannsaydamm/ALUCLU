import hashlib
import os
from dataclasses import asdict

import pytest

from aluclu.alc_r0.attempt_journal import AttemptJournal, JournalConflict
from aluclu.alc_r0.attempt_state import AttemptStateError, RunSpec, replay_attempts
from aluclu.alc_r0.canonical import canonical_json_bytes
from aluclu.alc_r0.paged_history import (
    PagedHistoryError,
    declaration_root,
    page_identity,
    read_paged_history,
)

ROOT = "a" * 64
RUN = "alc-r0-v1-dev-paging-fixture-s20260916"
SPEC = RunSpec(RUN, False, ("w1", "w2"))


def history():
    def event(kind, **fields):
        return canonical_json_bytes(
            dict(run_id=RUN, attempt_id="a001", kind=kind, **fields)
        )

    return (
        event(
            "intent",
            source_sha256=ROOT,
            invocation_sha256=ROOT,
            retry_kind="INITIAL",
            prior_source_sha256=None,
            prior_artifact_sha256=None,
            review_sha256=None,
        ),
        event("start", receipt_sha256=ROOT),
        event("work", work_id="w1", evidence_sha256=ROOT),
        event("work", work_id="w2", evidence_sha256=ROOT),
        event(
            "close",
            state="PREPARED",
            failure_class=None,
            evidence_sha256=ROOT,
            gpu_ns=3,
            wall_ns=4,
            storage_growth_bytes=5,
        ),
        event("result", state="PASS", evidence_sha256=ROOT),
    )


def encode(heads):
    data = canonical_json_bytes(
        dict(
            version=1,
            spec_sha256=declaration_root(SPEC),
            pages=[asdict(head) for head in heads],
        )
    )
    return data, hashlib.sha256(data).hexdigest()


def write_pages(directory, groups):
    heads = []
    for index, events in enumerate(groups):
        previous = heads[-1] if heads else None
        journal = AttemptJournal(
            directory / f"page-{index:04d}.jsonl",
            page_identity(declaration_root(SPEC), index, previous),
        )
        head = journal.create()
        for event in events:
            head = journal.append(head, event)
        heads.append(head)
    return encode(heads), heads


def test_cross_page_restart_equals_complete_reference(tmp_path):
    events = history()
    (data, root), heads = write_pages(tmp_path, (events[:2], events[2:4], events[4:]))
    assert (
        read_paged_history(tmp_path, SPEC, data, root)
        == replay_attempts((SPEC,), events)[0]
    )
    assert heads[0].count == 2
    assert read_paged_history(tmp_path, SPEC, data, root).attempts[0].events == events


def test_empty_manifest_is_only_unstarted(tmp_path):
    data, root = encode(())
    assert read_paged_history(tmp_path, SPEC, data, root).state == "UNSTARTED"


def test_wrong_manifest_hash_rejected_before_path_access(tmp_path):
    data, root = encode(())
    with pytest.raises(PagedHistoryError, match="manifest root"):
        read_paged_history(tmp_path / "absent", SPEC, data, ROOT)
    assert not list(tmp_path.iterdir())


def test_changed_work_declaration_rejected(tmp_path):
    data, root = encode(())
    altered = RunSpec(RUN, False, ("w2", "w1"))
    with pytest.raises(PagedHistoryError, match="declaration"):
        read_paged_history(tmp_path, altered, data, root)


@pytest.mark.parametrize(
    "mutation", ["missing", "extra", "substitution", "directory", "truncate"]
)
def test_unsafe_or_incomplete_page_set_rejected(tmp_path, mutation):
    (data, root), _ = write_pages(tmp_path, (history()[:2], history()[2:]))
    page = tmp_path / "page-0001.jsonl"
    if mutation == "missing":
        page.unlink()
    elif mutation == "extra":
        (tmp_path / "page-0002.jsonl").write_bytes(b"")
    elif mutation == "substitution":
        page.write_bytes((tmp_path / "page-0000.jsonl").read_bytes())
    elif mutation == "directory":
        page.unlink()
        page.mkdir()
    else:
        page.write_bytes(page.read_bytes()[:-1])
    with pytest.raises((PagedHistoryError, RuntimeError)):
        read_paged_history(tmp_path, SPEC, data, root)


def test_reordered_manifest_heads_rejected(tmp_path):
    _, heads = write_pages(tmp_path, (history()[:2], history()[2:]))
    data, root = encode(tuple(reversed(heads)))
    with pytest.raises(RuntimeError):
        read_paged_history(tmp_path, SPEC, data, root)


def test_semantic_invalid_tail_returns_no_snapshot(tmp_path):
    (data, root), _ = write_pages(tmp_path, (history()[:2], (history()[3],)))
    with pytest.raises(AttemptStateError):
        read_paged_history(tmp_path, SPEC, data, root)


def test_old_manifest_cannot_adopt_new_page_head(tmp_path):
    (data, root), heads = write_pages(tmp_path, (history()[:2],))
    journal = AttemptJournal(
        tmp_path / "page-0000.jsonl", page_identity(declaration_root(SPEC), 0, None)
    )
    journal.append(heads[0], history()[2])
    with pytest.raises(JournalConflict):
        read_paged_history(tmp_path, SPEC, data, root)


@pytest.mark.parametrize(
    "pages",
    [
        None,
        {},
        [dict(count=True, byte_length=1, digest=ROOT)],
        [dict(count=0, byte_length=0, digest=ROOT)],
        [dict(count=65537, byte_length=1, digest=ROOT)],
        [dict(count=1, byte_length=32 * 2**20 + 1, digest=ROOT)],
        [dict(count=1, byte_length=1, digest=ROOT.upper())],
        [dict(count=1, byte_length=1, digest=ROOT, extra=1)],
        [dict(count=1, byte_length=1, digest=ROOT)] * 9,
        [dict(count=65536, byte_length=1, digest=ROOT)] * 5,
    ],
)
def test_malformed_manifest_bounds_fail_before_io(tmp_path, pages):
    data = canonical_json_bytes(
        dict(version=1, spec_sha256=declaration_root(SPEC), pages=pages)
    )
    with pytest.raises(PagedHistoryError):
        read_paged_history(
            tmp_path / "absent", SPEC, data, hashlib.sha256(data).hexdigest()
        )
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "data", [b"{}", b"[]", b"x" * 8193, b'{"version":1,"version":1}']
)
def test_bad_canonical_manifest_rejected(tmp_path, data):
    with pytest.raises(PagedHistoryError):
        read_paged_history(tmp_path, SPEC, data, hashlib.sha256(data).hexdigest())


def test_page_identity_binds_position_and_predecessor(tmp_path):
    _, heads = write_pages(tmp_path, (history()[:2],))
    root = declaration_root(SPEC)
    assert page_identity(root, 0, None) != page_identity(root, 1, heads[0])
    with pytest.raises(PagedHistoryError):
        page_identity(root, 1, None)
    with pytest.raises(PagedHistoryError):
        page_identity(root, 0, heads[0])


@pytest.mark.parametrize("index", [True, -1, 8, "1"])
def test_invalid_page_index_rejected(index):
    with pytest.raises(PagedHistoryError):
        page_identity(declaration_root(SPEC), index, None)


@pytest.mark.parametrize("change", [{"version": True}, {"version": 2}, {"extra": 1}])
def test_manifest_exact_version_and_fields(tmp_path, change):
    fields = dict(version=1, spec_sha256=declaration_root(SPEC), pages=[])
    fields.update(change)
    data = canonical_json_bytes(fields)
    with pytest.raises(PagedHistoryError):
        read_paged_history(tmp_path, SPEC, data, hashlib.sha256(data).hexdigest())


def test_relative_directory_rejected_before_storage_read():
    from pathlib import Path

    data, root = encode(())
    with pytest.raises(PagedHistoryError, match="absolute"):
        read_paged_history(Path("relative"), SPEC, data, root)


def test_hardlinked_page_rejected(tmp_path):
    directory = tmp_path / "pages"
    directory.mkdir()
    (data, root), _ = write_pages(directory, (history()[:2],))
    os.link(directory / "page-0000.jsonl", tmp_path / "alias.jsonl")
    with pytest.raises(PagedHistoryError, match="single-link"):
        read_paged_history(directory, SPEC, data, root)


def test_real_page_record_boundary_keeps_all_work_and_reference_rules(tmp_path):
    # Bulk synthetic storage fixture, NOT an implemented rotating writer. Each
    # record uses the existing journal format and is fully checked by the reader.
    from aluclu.alc_r0.attempt_journal import JournalHead
    from aluclu.alc_r0.canonical import parse_canonical_json

    spec = RunSpec(RUN, False, tuple(f"w{i}" for i in range(65536)))
    root = declaration_root(spec)
    events = (
        history()[:2]
        + tuple(
            canonical_json_bytes(
                dict(
                    run_id=RUN,
                    attempt_id="a001",
                    kind="work",
                    work_id=w,
                    evidence_sha256=ROOT,
                )
            )
            for w in spec.work_ids
        )
        + history()[4:]
    )
    heads = []
    for index, group in enumerate((events[:65536], events[65536:])):
        identity = page_identity(root, index, heads[-1] if heads else None)
        digest = hashlib.sha256(
            b"ALC-R0-JOURNAL-GENESIS-V1\0" + identity.encode()
        ).hexdigest()
        raw = bytearray()
        for sequence, event in enumerate(group, 1):
            line = (
                canonical_json_bytes(
                    dict(
                        version=1,
                        journal_id=identity,
                        sequence=sequence,
                        previous=digest,
                        event=parse_canonical_json(event),
                    )
                )
                + b"\n"
            )
            digest = hashlib.sha256(b"ALC-R0-JOURNAL-RECORD-V1\0" + line).hexdigest()
            raw.extend(line)
        assert len(raw) <= 32 * (1 << 20)
        (tmp_path / f"page-{index:04d}.jsonl").write_bytes(raw)
        heads.append(JournalHead(len(group), len(raw), digest))
    data = canonical_json_bytes(
        dict(version=1, spec_sha256=root, pages=[asdict(h) for h in heads])
    )
    result = read_paged_history(tmp_path, spec, data, hashlib.sha256(data).hexdigest())
    assert [h.count for h in heads] == [65536, 4]
    assert result.state == "PASS"
    assert result.attempts[0].events == events
    assert result.attempts[0].work == tuple((w, ROOT) for w in spec.work_ids)
    assert result.attempts[0].gpu_ns == 3
