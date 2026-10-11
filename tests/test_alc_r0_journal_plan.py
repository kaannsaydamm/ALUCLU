import hashlib

import pytest

from aluclu.alc_r0.attempt_journal import (
    AttemptJournal,
    JournalError,
    JournalHead,
    plan_journal_append,
)
from aluclu.alc_r0.canonical import canonical_json_bytes

IDENTITY = "a" * 64
EVENT = canonical_json_bytes(dict(kind="synthetic storage event"))


def genesis():
    return JournalHead(
        0,
        0,
        hashlib.sha256(b"ALC-R0-JOURNAL-GENESIS-V1\0" + IDENTITY.encode()).hexdigest(),
    )


def test_pure_plan_exact_bytes_match_actual_append(tmp_path):
    old = genesis()
    planned = plan_journal_append(IDENTITY, old, EVENT)
    assert not list(tmp_path.iterdir())
    expected = (
        canonical_json_bytes(
            dict(
                version=1,
                journal_id=IDENTITY,
                sequence=1,
                previous=old.digest,
                event=dict(kind="synthetic storage event"),
            )
        )
        + b"\n"
    )
    assert planned.line == expected
    assert planned.head == JournalHead(
        1,
        len(expected),
        hashlib.sha256(b"ALC-R0-JOURNAL-RECORD-V1\0" + expected).hexdigest(),
    )
    journal = AttemptJournal(tmp_path / "journal.jsonl", IDENTITY)
    assert journal.create() == old
    assert journal.append(old, EVENT) == planned.head
    assert journal.path.read_bytes() == planned.line
    assert journal.read(planned.head).events == (EVENT,)


def test_two_planned_records_preserve_exact_chain(tmp_path):
    first = plan_journal_append(IDENTITY, genesis(), EVENT)
    second = plan_journal_append(IDENTITY, first.head, EVENT)
    journal = AttemptJournal(tmp_path / "journal.jsonl", IDENTITY)
    old = journal.create()
    journal.append(old, EVENT)
    assert journal.append(first.head, EVENT) == second.head
    assert journal.path.read_bytes() == first.line + second.line
    assert second.head.byte_length == len(first.line + second.line)


@pytest.mark.parametrize(
    "change",
    [
        "identity",
        "head_type",
        "bool_count",
        "count_cap",
        "bytes_cap",
        "noncanonical",
        "not_object",
        "event_cap",
    ],
)
def test_invalid_plan_rejects_without_io(tmp_path, change):
    identity, head, event = IDENTITY, genesis(), EVENT
    if change == "identity":
        identity = "A" * 64
    elif change == "head_type":
        head = dict(count=0, byte_length=0, digest=head.digest)
    elif change == "bool_count":
        head = JournalHead(False, 0, head.digest)
    elif change == "count_cap":
        head = JournalHead(65536, 1, head.digest)
    elif change == "bytes_cap":
        head = JournalHead(1, 32 * (1 << 20), head.digest)
    elif change == "noncanonical":
        event = b'{ "x": 1 }'
    elif change == "not_object":
        event = b"[]"
    else:
        event = canonical_json_bytes(dict(payload="x" * 8192))
    with pytest.raises(JournalError):
        plan_journal_append(identity, head, event)
    assert not list(tmp_path.iterdir())
