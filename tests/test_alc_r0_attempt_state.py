from dataclasses import FrozenInstanceError

import pytest

from aluclu.alc_r0.attempt_state import AttemptStateError, RunSpec, replay_attempts
from aluclu.alc_r0.canonical import canonical_json_bytes

RUN = "alc-r0-v1-dev-fixture-s20260916"
A, B, C = "a" * 64, "b" * 64, "c" * 64


def spec(resource=False):
    return (RunSpec(RUN, resource, ("w1", "w2")),)


def event(kind, attempt="a001", **fields):
    return canonical_json_bytes(
        dict(run_id=RUN, attempt_id=attempt, kind=kind, **fields)
    )


def intent(
    attempt="a001",
    source=A,
    retry="INITIAL",
    prior_source=None,
    prior_artifact=None,
    review=None,
):
    return event(
        "intent",
        attempt,
        source_sha256=source,
        invocation_sha256=B,
        retry_kind=retry,
        prior_source_sha256=prior_source,
        prior_artifact_sha256=prior_artifact,
        review_sha256=review,
    )


def start(attempt="a001"):
    return event("start", attempt, receipt_sha256=C)


def work(work_id, attempt="a001"):
    return event("work", attempt, work_id=work_id, evidence_sha256=C)


def close(state="INVALID", failure="IMPLEMENTATION", attempt="a001", gpu=5):
    return event(
        "close",
        attempt,
        state=state,
        failure_class=failure,
        evidence_sha256=C,
        gpu_ns=gpu,
        wall_ns=8,
        storage_growth_bytes=3,
    )


def test_prepared_then_result_and_immutable_history():
    rows = replay_attempts(
        spec(),
        (
            intent(),
            start(),
            work("w1"),
            work("w2"),
            close("PREPARED", None),
            event("result", state="PASS", evidence_sha256=C),
        ),
    )
    assert rows[0].state == "PASS"
    assert rows[0].attempts[0].gpu_ns == 5
    assert rows[0].attempts[0].work == (("w1", C), ("w2", C))
    with pytest.raises(FrozenInstanceError):
        rows[0].state = "FAIL"


def test_repair_retains_invalid_consumption():
    rows = replay_attempts(
        spec(),
        (
            intent(),
            start(),
            close(),
            intent(
                "a002",
                source=B,
                retry="REPAIR",
                prior_source=A,
                prior_artifact=C,
                review=C,
            ),
            start("a002"),
            close(attempt="a002", gpu=9),
        ),
    )
    assert [a.state for a in rows[0].attempts] == ["INVALID", "INVALID"]
    assert [a.gpu_ns for a in rows[0].attempts] == [5, 9]
    assert rows[0].repairs == 1


def test_resource_environment_third_attempt():
    events = [intent(), start(), close(failure="ENVIRONMENT")]
    for attempt in ("a002", "a003"):
        events += [
            intent(
                attempt, retry="ENVIRONMENT", prior_source=A, prior_artifact=C, review=C
            ),
            start(attempt),
            close(failure="ENVIRONMENT", attempt=attempt),
        ]
    assert len(replay_attempts(spec(True), tuple(events))[0].attempts) == 3
    with pytest.raises(AttemptStateError):
        replay_attempts(spec(False), tuple(events))


def test_resume_same_attempt_missing_work_and_segment_accounting():
    events = (
        intent(),
        start(),
        work("w1"),
        event(
            "interrupt",
            checkpoint_sha256=C,
            evidence_sha256=C,
            gpu_ns=7,
            wall_ns=9,
            storage_growth_bytes=2,
        ),
        event(
            "resume",
            checkpoint_sha256=C,
            source_sha256=A,
            invocation_sha256=B,
            review_sha256=C,
        ),
        work("w2"),
        close("PREPARED", None),
    )
    row = replay_attempts(spec(), events)[0]
    assert row.resumes == 1 and len(row.attempts) == 1
    assert (
        row.attempts[0].gpu_ns,
        row.attempts[0].wall_ns,
        row.attempts[0].storage_growth_bytes,
    ) == (12, 17, 5)


def test_unknown_and_unclosed_consumption_never_zero():
    assert replay_attempts(spec(), (intent(), start()))[0].attempts[0].gpu_ns is None
    assert (
        replay_attempts(spec(), (intent(), start(), close(gpu=None)))[0]
        .attempts[0]
        .gpu_ns
        is None
    )


@pytest.mark.parametrize(
    "tail",
    [
        event("result", state="PASS", evidence_sha256=C),
        close("PREPARED", None),
        work("w2"),
        work("foreign"),
        start(),
        intent(
            "a002", source=B, retry="REPAIR", prior_source=A, prior_artifact=C, review=C
        ),
        event(
            "resume",
            checkpoint_sha256=C,
            source_sha256=A,
            invocation_sha256=B,
            review_sha256=C,
        ),
    ],
)
def test_illegal_running_transitions(tail):
    with pytest.raises(AttemptStateError):
        replay_attempts(spec(), (intent(), start(), tail))


def test_resume_binding_and_once_limit():
    interrupted = event(
        "interrupt",
        checkpoint_sha256=C,
        evidence_sha256=C,
        gpu_ns=1,
        wall_ns=2,
        storage_growth_bytes=0,
    )
    prefix = (intent(), start(), interrupted)
    with pytest.raises(AttemptStateError):
        replay_attempts(
            spec(),
            prefix
            + (
                event(
                    "resume",
                    checkpoint_sha256=C,
                    source_sha256=B,
                    invocation_sha256=B,
                    review_sha256=C,
                ),
            ),
        )
    resume = event(
        "resume",
        checkpoint_sha256=C,
        source_sha256=A,
        invocation_sha256=B,
        review_sha256=C,
    )
    with pytest.raises(AttemptStateError):
        replay_attempts(spec(), prefix + (resume, interrupted, resume))


@pytest.mark.parametrize(
    "changes",
    [
        dict(prior_source=B),
        dict(prior_artifact=A),
        dict(review=None),
        dict(source=A),
        dict(retry="ENVIRONMENT"),
    ],
)
def test_invalid_repair_binding(changes):
    values = dict(
        attempt="a002",
        source=B,
        retry="REPAIR",
        prior_source=A,
        prior_artifact=C,
        review=C,
    )
    with pytest.raises(AttemptStateError):
        replay_attempts(
            spec(), (intent(), start(), close(), intent(**(values | changes)))
        )


def test_retry_after_prepared_or_terminal_forbidden():
    ready = (intent(), start(), work("w1"), work("w2"), close("PREPARED", None))
    with pytest.raises(AttemptStateError):
        replay_attempts(
            spec(),
            ready
            + (
                intent(
                    "a002",
                    source=B,
                    retry="REPAIR",
                    prior_source=A,
                    prior_artifact=C,
                    review=C,
                ),
            ),
        )
    with pytest.raises(AttemptStateError):
        replay_attempts(spec(), (intent(), close("BLOCKED", "OTHER"), start()))


def test_duplicate_work_extra_run_fields_noncanonical():
    bad = canonical_json_bytes(
        dict(run_id=RUN + "x", attempt_id="a001", kind="start", receipt_sha256=C)
    )
    for events in (
        (intent(), start(), work("w1"), work("w1")),
        (intent(), bad),
        (b'{ "x":1}',),
        (event("start", receipt_sha256=C, surprise=True),),
    ):
        with pytest.raises(AttemptStateError):
            replay_attempts(spec(), events)


def test_declarations_unique_strict_closed():
    for specs in (
        (RunSpec(RUN, True, ("w1", "w1")),),
        (spec()[0], spec()[0]),
        (RunSpec(RUN, 1, ("w1",)),),
    ):
        with pytest.raises(AttemptStateError):
            replay_attempts(specs, ())


@pytest.mark.parametrize("gpu", [True, -1, 1.5, 2**53])
def test_malformed_measurements(gpu):
    bad = (
        close().replace(b'"gpu_ns":5', b'"gpu_ns":9007199254740992')
        if gpu == 2**53
        else close(gpu=gpu)
    )
    with pytest.raises(AttemptStateError):
        replay_attempts(spec(), (intent(), start(), bad))


def test_second_repair_and_third_repair_forbidden():
    prefix = (
        intent(),
        start(),
        close(),
        intent(
            "a002", source=B, retry="REPAIR", prior_source=A, prior_artifact=C, review=C
        ),
        start("a002"),
        close(attempt="a002"),
    )
    with pytest.raises(AttemptStateError):
        replay_attempts(
            spec(True),
            prefix
            + (
                intent(
                    "a003",
                    source=C,
                    retry="REPAIR",
                    prior_source=B,
                    prior_artifact=C,
                    review=C,
                ),
            ),
        )


def test_fourth_environment_attempt_and_changed_source_forbidden():
    prefix = [intent(), start(), close(failure="ENVIRONMENT")]
    with pytest.raises(AttemptStateError):
        replay_attempts(
            spec(True),
            tuple(prefix)
            + (
                intent(
                    "a002",
                    source=B,
                    retry="ENVIRONMENT",
                    prior_source=A,
                    prior_artifact=C,
                    review=C,
                ),
            ),
        )
    for attempt in ("a002", "a003"):
        prefix += [
            intent(
                attempt, retry="ENVIRONMENT", prior_source=A, prior_artifact=C, review=C
            ),
            start(attempt),
            close(failure="ENVIRONMENT", attempt=attempt),
        ]
    with pytest.raises(AttemptStateError):
        replay_attempts(
            spec(True),
            tuple(prefix)
            + (
                intent(
                    "a004",
                    retry="ENVIRONMENT",
                    prior_source=A,
                    prior_artifact=C,
                    review=C,
                ),
            ),
        )


def test_resume_budget_shared_across_repaired_attempts():
    def interrupted(attempt):
        return event(
            "interrupt",
            attempt,
            checkpoint_sha256=C,
            evidence_sha256=C,
            gpu_ns=1,
            wall_ns=2,
            storage_growth_bytes=0,
        )

    def resumed(attempt, source):
        return event(
            "resume",
            attempt,
            checkpoint_sha256=C,
            source_sha256=source,
            invocation_sha256=B,
            review_sha256=C,
        )

    prefix = (
        intent(),
        start(),
        interrupted("a001"),
        resumed("a001", A),
        close(),
        intent(
            "a002", source=B, retry="REPAIR", prior_source=A, prior_artifact=C, review=C
        ),
        start("a002"),
        interrupted("a002"),
    )
    with pytest.raises(AttemptStateError):
        replay_attempts(spec(), prefix + (resumed("a002", B),))


@pytest.mark.parametrize(
    "changes",
    [dict(checkpoint_sha256=A), dict(invocation_sha256=A), dict(review_sha256=None)],
)
def test_wrong_resume_roots_rejected(changes):
    prefix = (
        intent(),
        start(),
        event(
            "interrupt",
            checkpoint_sha256=C,
            evidence_sha256=C,
            gpu_ns=1,
            wall_ns=2,
            storage_growth_bytes=0,
        ),
    )
    values = dict(
        checkpoint_sha256=C, source_sha256=A, invocation_sha256=B, review_sha256=C
    )
    with pytest.raises(AttemptStateError):
        replay_attempts(spec(), prefix + (event("resume", **(values | changes)),))


@pytest.mark.parametrize(
    "state,failure",
    [
        ("PASS", None),
        ("FAIL", "OTHER"),
        ("INVALID", None),
        ("BLOCKED", "ENVIRONMENT"),
        ("PREPARED", "OTHER"),
    ],
)
def test_invalid_close_classifications(state, failure):
    with pytest.raises(AttemptStateError):
        replay_attempts(
            spec(), (intent(), start(), work("w1"), work("w2"), close(state, failure))
        )


def test_fail_is_only_prepared_terminal_and_no_second_candidate():
    ready = (intent(), start(), work("w1"), work("w2"), close("PREPARED", None))
    terminal = ready + (event("result", state="FAIL", evidence_sha256=C),)
    assert replay_attempts(spec(), terminal)[0].state == "FAIL"
    with pytest.raises(AttemptStateError):
        replay_attempts(spec(), terminal + (close("PREPARED", None),))


def test_unknown_segment_sticky_after_resume():
    prefix = (
        intent(),
        start(),
        event(
            "interrupt",
            checkpoint_sha256=C,
            evidence_sha256=C,
            gpu_ns=None,
            wall_ns=2,
            storage_growth_bytes=0,
        ),
        event(
            "resume",
            checkpoint_sha256=C,
            source_sha256=A,
            invocation_sha256=B,
            review_sha256=C,
        ),
        close(),
    )
    assert replay_attempts(spec(), prefix)[0].attempts[0].gpu_ns is None


def test_segment_aggregate_overflow_rejected():
    prefix = (
        intent(),
        start(),
        event(
            "interrupt",
            checkpoint_sha256=C,
            evidence_sha256=C,
            gpu_ns=2**53 - 1,
            wall_ns=2,
            storage_growth_bytes=0,
        ),
        event(
            "resume",
            checkpoint_sha256=C,
            source_sha256=A,
            invocation_sha256=B,
            review_sha256=C,
        ),
    )
    with pytest.raises(AttemptStateError):
        replay_attempts(spec(), prefix + (close(gpu=1),))


@pytest.mark.parametrize(
    "events",
    [
        [],
        (b"{}",),
        (b"x" * 8193,),
        (b"[]",),
        (b'{"kind":true}',),
        (b'{"kind":"start","kind":"start"}',),
    ],
)
def test_malformed_history_and_event_shapes(events):
    with pytest.raises(AttemptStateError):
        replay_attempts(spec(), events)


def test_multiple_runs_isolated_and_declared_order_preserved():
    other = RUN.replace("fixture", "second")
    specs = (RunSpec(other, False, ("w1",)), spec()[0])
    rows = replay_attempts(specs, (intent(), start(), close()))
    assert [r.run_id for r in rows] == [other, RUN]
    assert rows[0].state == "UNSTARTED" and rows[0].attempts == ()
    assert rows[1].state == "INVALID"


def test_every_event_root_retained_in_immutable_attempt_view():
    interrupted = event(
        "interrupt",
        checkpoint_sha256=A,
        evidence_sha256=B,
        gpu_ns=1,
        wall_ns=2,
        storage_growth_bytes=0,
    )
    resumed = event(
        "resume",
        checkpoint_sha256=A,
        source_sha256=A,
        invocation_sha256=B,
        review_sha256=A,
    )
    events = (
        intent(),
        start(),
        interrupted,
        resumed,
        work("w1"),
        work("w2"),
        close("PREPARED", None),
        event("result", state="PASS", evidence_sha256=B),
    )
    attempt = replay_attempts(spec(), events)[0].attempts[0]
    assert attempt.events == events
    assert all(type(e) is bytes for e in attempt.events)
    with pytest.raises(FrozenInstanceError):
        attempt.events = ()


def test_large_work_declaration_does_not_shrink_epoch_schedule():
    # No real corpus/model: declaration larger than old4096 cap remains complete.
    declared = (RunSpec(RUN, False, tuple(f"w{i}" for i in range(33243))),)
    assert replay_attempts(declared, (intent(), start()))[0].state == "RUNNING"
    with pytest.raises(AttemptStateError):
        replay_attempts(declared, (intent(), start(), close("PREPARED", None)))


def test_per_run_and_total_work_caps_are_explicit_validation_errors():
    work_ids = tuple(f"w{i}" for i in range(65536))
    assert replay_attempts((RunSpec(RUN, False, work_ids),), ())[0].state == "UNSTARTED"
    with pytest.raises(AttemptStateError):
        replay_attempts((RunSpec(RUN, False, work_ids + ("extra",)),), ())
    declarations = tuple(
        RunSpec(RUN.replace("fixture", f"fixture-{i}"), False, work_ids)
        for i in range(5)
    )
    assert len(replay_attempts(declarations[:4], ())) == 4
    with pytest.raises(AttemptStateError, match="batch ceiling"):
        replay_attempts(declarations, ())


def test_event_count_cap_rejected_before_parsing_records():
    with pytest.raises(AttemptStateError, match="bounded immutable event history"):
        replay_attempts(spec(), (b"{}",) * 262145)


def test_storage_restart_replay(tmp_path):
    from aluclu.alc_r0.attempt_journal import AttemptJournal

    store = AttemptJournal(tmp_path / "attempts.jsonl", A)
    head = store.create()
    for item in (intent(), start(), close()):
        replay_attempts(spec(), store.read(head).events + (item,))
        head = store.append(head, item)
    assert (
        replay_attempts(spec(), AttemptJournal(store.path, A).read(head).events)[
            0
        ].state
        == "INVALID"
    )
