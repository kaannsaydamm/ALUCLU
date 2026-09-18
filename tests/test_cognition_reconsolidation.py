from __future__ import annotations

import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from aluclu.cognition import (
    CanonicalJsonValue,
    EncryptedLedger,
    InputBoundaryError,
    LedgerLifecycleError,
    ObservationRequestV1,
    ProvenanceV1,
    SourceKind,
    StaticKeyProvider,
    VerifiedLedgerSession,
)
from aluclu.cognition.recollection import (
    CalibratedTextMatchEvidenceV1,
    EventIdRecallQuery,
    ExactRecollection,
    NoRecollection,
    RecallBasis,
    RecollectionWorkV1,
    recall,
)
from aluclu.cognition.reconsolidation import (
    ReconsolidationReason,
    commit_reconsolidation,
    propose_reconsolidation,
    reconsolidation_record_from_json_value,
    reconsolidation_record_to_json_value,
)
from aluclu.cognition.sensorium import (
    ObservationAcceptedV1,
    SensoriumStateV1,
    baseline_boundary_profile,
    ingest_observation,
    initialize_empty_sensorium_state,
)

MASTER_KEY = b"m" * 32


def _request(index: int, *, content: str) -> ObservationRequestV1:
    return ObservationRequestV1(
        observation_id=f"obs:recon-{index:04d}",
        session_id="session:recon",
        turn_id=f"turn:recon-{index:04d}",
        provenance=ProvenanceV1(
            source_kind=SourceKind.USER,
            source_instance_id="user:recon-fixture",
            origin_id="fixture:reconsolidation",
            observed_at_ns=1_725_000_000_000_000_000 + index,
            parent_observation_ids=(),
            capture_method="test",
            capture_version="1.0.0",
        ),
        content=CanonicalJsonValue.from_value({"private_memory": content}),
        retrieval_text=content,
        topic_key=None,
        goal_ids=(),
        participant_ids=("participant:user",),
        tool_invocation_id=None,
        tool_phase=None,
        force_boundary=False,
    )


def _ingest_pair(
    session: VerifiedLedgerSession,
) -> tuple[ExactRecollection, ExactRecollection]:
    profile = baseline_boundary_profile()
    state = initialize_empty_sensorium_state(session, profile)
    assert type(state) is SensoriumStateV1
    for request in (
        _request(1, content="parent secret must not enter lineage"),
        _request(2, content="trigger secret must not enter lineage"),
    ):
        accepted = ingest_observation(session, request, profile, state)
        assert type(accepted) is ObservationAcceptedV1
        state = accepted.next_state
    parent = recall(session, EventIdRecallQuery(observation_id="obs:recon-0001"))
    trigger = recall(session, EventIdRecallQuery(observation_id="obs:recon-0002"))
    assert type(parent) is ExactRecollection
    assert type(trigger) is ExactRecollection
    return parent, trigger


def _ingest_triple(
    session: VerifiedLedgerSession,
) -> tuple[ExactRecollection, ExactRecollection, ExactRecollection]:
    profile = baseline_boundary_profile()
    state = initialize_empty_sensorium_state(session, profile)
    assert type(state) is SensoriumStateV1
    for request in (
        _request(1, content="original claim"),
        _request(2, content="first correction"),
        _request(3, content="contradicting second correction"),
    ):
        accepted = ingest_observation(session, request, profile, state)
        assert type(accepted) is ObservationAcceptedV1
        state = accepted.next_state
    first = recall(session, EventIdRecallQuery(observation_id="obs:recon-0001"))
    second = recall(session, EventIdRecallQuery(observation_id="obs:recon-0002"))
    third = recall(session, EventIdRecallQuery(observation_id="obs:recon-0003"))
    assert type(first) is ExactRecollection
    assert type(second) is ExactRecollection
    assert type(third) is ExactRecollection
    return first, second, third


def test_reconsolidation_proposal_is_pure_and_repeatable(tmp_path: Path) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            parent, trigger = _ingest_pair(session)
            before = session.event_count()
            first = propose_reconsolidation(
                parent, trigger, reason=ReconsolidationReason.CORRECTION
            )
            second = propose_reconsolidation(
                parent, trigger, reason=ReconsolidationReason.CORRECTION
            )
            after = session.event_count()

    assert first == second
    assert first.reconsolidation_id.startswith("recon:")
    assert before == after == 2


def test_reconsolidation_commit_creates_content_free_child_without_parent_mutation(
    tmp_path: Path,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            parent, trigger = _ingest_pair(session)
            proposal = propose_reconsolidation(
                parent, trigger, reason=ReconsolidationReason.CORRECTION
            )
            created = commit_reconsolidation(session, proposal)
            child = session.read(proposal.reconsolidation_id)
            parent_after = recall(
                session, EventIdRecallQuery(observation_id=parent.observation_id)
            )
            trigger_after = recall(
                session, EventIdRecallQuery(observation_id=trigger.observation_id)
            )
            count = session.event_count()

    assert created.created is True
    assert count == 3
    assert child is not None
    assert type(child.payload) is dict
    assert child.payload["schema"] == "aluclu.reconsolidation.v1"
    assert child.payload["parent_observation_id"] == parent.observation_id
    assert child.payload["trigger_observation_id"] == trigger.observation_id
    wire = str(child.payload)
    for forbidden in (
        "parent secret must not enter lineage",
        "trigger secret must not enter lineage",
        "private_memory",
        "retrieval_text",
        "snippet",
        "summary",
        "feature_vector",
    ):
        assert forbidden not in wire
    assert type(parent_after) is ExactRecollection
    assert type(trigger_after) is ExactRecollection
    assert parent_after.record_hash == parent.record_hash
    assert trigger_after.record_hash == trigger.record_hash


def test_reconsolidation_retry_after_reopen_is_duplicate(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        with ledger.verified_session() as session:
            parent, trigger = _ingest_pair(session)
            proposal = propose_reconsolidation(
                parent, trigger, reason=ReconsolidationReason.CORRECTION
            )
            first = commit_reconsolidation(session, proposal)
            assert first.created is True

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as reopened:
        with reopened.verified_session() as session:
            retry = commit_reconsolidation(session, proposal)
            count = session.event_count()

    assert retry.created is False
    assert retry.record.record_hash == first.record.record_hash
    assert count == 3


def test_reconsolidation_rejects_nonexact_or_self_parent_input(
    tmp_path: Path,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            parent, trigger = _ingest_pair(session)
            missing = recall(
                session, EventIdRecallQuery(observation_id="obs:recon-missing")
            )
    assert type(missing) is NoRecollection
    with pytest.raises(InputBoundaryError):
        propose_reconsolidation(
            missing, trigger, reason=ReconsolidationReason.CORRECTION  # type: ignore[arg-type]
        )
    with pytest.raises(InputBoundaryError):
        propose_reconsolidation(
            parent, parent, reason=ReconsolidationReason.CORRECTION
        )


@pytest.mark.parametrize("endpoint", ["parent", "trigger"])
def test_shredded_endpoint_cannot_be_recreated_from_lineage(
    tmp_path: Path, endpoint: str
) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        with ledger.verified_session() as session:
            parent, trigger = _ingest_pair(session)
            proposal = propose_reconsolidation(
                parent, trigger, reason=ReconsolidationReason.CORRECTION
            )
            commit_reconsolidation(session, proposal)
            target = parent if endpoint == "parent" else trigger
            assert session.shred(target.observation_id)

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as reopened:
        with reopened.verified_session() as session:
            assert session.read(target.observation_id) is None
            child = session.read(proposal.reconsolidation_id)
            assert child is not None
            assert "parent secret must not enter lineage" not in str(child.payload)
            assert "trigger secret must not enter lineage" not in str(child.payload)
            assert session.is_tombstoned(target.observation_id)


def test_lineage_decoder_rejects_extra_content_and_broken_identity(
    tmp_path: Path,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            parent, trigger = _ingest_pair(session)
            proposal = propose_reconsolidation(
                parent, trigger, reason=ReconsolidationReason.CORRECTION
            )
    wire = reconsolidation_record_to_json_value(proposal.record)
    assert reconsolidation_record_from_json_value(wire) == proposal.record
    with pytest.raises(InputBoundaryError):
        reconsolidation_record_from_json_value(
            {**wire, "parent_content": "forbidden copy"}
        )
    with pytest.raises(InputBoundaryError):
        reconsolidation_record_from_json_value(
            {**wire, "parent_record_hash": "0" * 64}
        )


def test_stale_and_shredded_parent_reject_commit_before_append(
    tmp_path: Path,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            parent, trigger = _ingest_pair(session)
            stale_parent = replace(parent, record_hash="0" * 64)
            stale = propose_reconsolidation(
                stale_parent,
                trigger,
                reason=ReconsolidationReason.CORRECTION,
            )
            with pytest.raises(InputBoundaryError, match="endpoint changed"):
                commit_reconsolidation(session, stale)
            live = propose_reconsolidation(
                parent, trigger, reason=ReconsolidationReason.CORRECTION
            )
            assert session.shred(parent.observation_id)
            with pytest.raises(InputBoundaryError, match="no longer live"):
                commit_reconsolidation(session, live)
            assert session.event_count() == 3  # two appends plus one shred history
            assert session.read(live.reconsolidation_id) is None


def test_commit_rejects_active_cursor_without_read_or_append(
    tmp_path: Path,
) -> None:
    with EncryptedLedger(
        tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as ledger:
        with ledger.verified_session() as session:
            parent, trigger = _ingest_pair(session)
            proposal = propose_reconsolidation(
                parent, trigger, reason=ReconsolidationReason.CORRECTION
            )
            cursor = session.cursor(after_sequence=0, batch_size=1)
            try:
                with pytest.raises(LedgerLifecycleError):
                    commit_reconsolidation(session, proposal)
                assert session.read(proposal.reconsolidation_id) is None
            finally:
                cursor.close()
            assert session.event_count() == 2


def test_cross_ledger_recollection_cannot_be_committed_as_lineage(
    tmp_path: Path,
) -> None:
    with EncryptedLedger(
        tmp_path / "left.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as left:
        with left.verified_session() as left_session:
            parent, _ = _ingest_pair(left_session)
    with EncryptedLedger(
        tmp_path / "right.sqlite3", StaticKeyProvider(MASTER_KEY)
    ) as right:
        with right.verified_session() as right_session:
            _, foreign_trigger = _ingest_pair(right_session)
            proposal = propose_reconsolidation(
                parent,
                foreign_trigger,
                reason=ReconsolidationReason.CORRECTION,
            )
            with pytest.raises(InputBoundaryError, match="endpoint changed"):
                commit_reconsolidation(right_session, proposal)
            assert right_session.event_count() == 2


def test_real_process_death_after_lineage_append_retries_once(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        with ledger.verified_session() as session:
            parent, trigger = _ingest_pair(session)
            proposal = propose_reconsolidation(
                parent, trigger, reason=ReconsolidationReason.CORRECTION
            )

    worker = Path(__file__).parent / "helpers" / "task2_reconsolidation_crash_worker.py"
    completed = subprocess.run(
        [sys.executable, str(worker), str(path)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 93, completed.stderr

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as reopened:
        with reopened.verified_session() as session:
            duplicate = commit_reconsolidation(session, proposal)
            child = session.read(proposal.reconsolidation_id)
            assert duplicate.created is False
            assert child is not None
            assert duplicate.record.record_hash == child.record_hash
            assert session.event_count() == 3


def test_malformed_calibrated_evidence_cannot_enter_lineage(tmp_path: Path) -> None:
    with EncryptedLedger(path := tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)) as ledger:
        with ledger.verified_session() as session:
            parent, trigger = _ingest_pair(session)
            evidence = CalibratedTextMatchEvidenceV1(
                profile_digest="a" * 64,
                effective_policy_digest="b" * 64,
                score_q32=1,
                margin_q32=1,
            )
            calibrated = replace(
                parent,
                basis=RecallBasis.CALIBRATED_TEXT_MATCH,
                work=RecollectionWorkV1(
                    records_scanned=2,
                    canonical_payload_bytes_decoded=1,
                    candidates_scored=1,
                    candidates_returned=1,
                    output_bytes=1,
                    exhaustive=True,
                ),
                calibrated_evidence=evidence,
            )
            proposal = propose_reconsolidation(
                calibrated, trigger, reason=ReconsolidationReason.CORRECTION
            )
            assert proposal.record.calibration_profile_digest == "a" * 64
            object.__setattr__(evidence, "score_q32", -1)
            with pytest.raises(InputBoundaryError, match="proposal is invalid"):
                commit_reconsolidation(session, proposal)
            with pytest.raises(InputBoundaryError, match="recollection is malformed"):
                propose_reconsolidation(
                    calibrated, trigger, reason=ReconsolidationReason.CORRECTION
                )
            assert session.event_count() == 2
    assert path.exists()


def test_reverse_edge_and_extra_parent_field_fail_closed(tmp_path: Path) -> None:
    with EncryptedLedger(tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)) as ledger:
        with ledger.verified_session() as session:
            parent, trigger = _ingest_pair(session)
            with pytest.raises(InputBoundaryError, match="later observation"):
                propose_reconsolidation(
                    trigger, parent, reason=ReconsolidationReason.USER_LINK
                )
            proposal = propose_reconsolidation(
                parent, trigger, reason=ReconsolidationReason.CORRECTION
            )
            changed_reason = propose_reconsolidation(
                parent, trigger, reason=ReconsolidationReason.OUTCOME_LINK
            )
            assert changed_reason.reconsolidation_id != proposal.reconsolidation_id
            wire = reconsolidation_record_to_json_value(proposal.record)
            with pytest.raises(InputBoundaryError, match="wire shape"):
                reconsolidation_record_from_json_value(
                    {**wire, "additional_parent_observation_ids": ["obs:foreign"]}
                )
            with pytest.raises(InputBoundaryError):
                reconsolidation_record_from_json_value(
                    {**wire, "trigger_sequence": True}
                )


def test_conflicting_correction_observations_remain_distinct(tmp_path: Path) -> None:
    with EncryptedLedger(tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)) as ledger:
        with ledger.verified_session() as session:
            parent, first_trigger, second_trigger = _ingest_triple(session)
            assert first_trigger.content_digest != second_trigger.content_digest
            first = propose_reconsolidation(
                parent, first_trigger, reason=ReconsolidationReason.CORRECTION
            )
            second = propose_reconsolidation(
                parent, second_trigger, reason=ReconsolidationReason.CORRECTION
            )
            assert first.reconsolidation_id != second.reconsolidation_id
            assert commit_reconsolidation(session, first).created is True
            assert commit_reconsolidation(session, second).created is True
            assert session.event_count() == 5
            assert session.read(parent.observation_id) is not None
            assert session.read(first_trigger.observation_id) is not None
            assert session.read(second_trigger.observation_id) is not None
            assert session.read(first.reconsolidation_id) is not None
            assert session.read(second.reconsolidation_id) is not None


def test_commit_rejects_bare_ledger_and_closed_session(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        with ledger.verified_session() as session:
            parent, trigger = _ingest_pair(session)
            proposal = propose_reconsolidation(
                parent, trigger, reason=ReconsolidationReason.CONTEXT_ADDED
            )
            with pytest.raises(InputBoundaryError, match="VerifiedLedgerSession"):
                commit_reconsolidation(ledger, proposal)  # type: ignore[arg-type]
            assert session.event_count() == 2
        with pytest.raises(LedgerLifecycleError):
            commit_reconsolidation(session, proposal)
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as reopened:
        with reopened.verified_session() as session:
            assert session.event_count() == 2
            assert session.read(proposal.reconsolidation_id) is None
