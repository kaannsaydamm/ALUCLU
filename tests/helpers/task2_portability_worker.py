from __future__ import annotations

import sys
from pathlib import Path
from typing import cast

from aluclu.cognition import (
    ApproximateCandidates,
    ConflictedRecollection,
    EncryptedLedger,
    EventIdRecallQuery,
    ExactRecollection,
    IncompleteRecollection,
    RecallExecutionPolicyV1,
    SensoriumReplayCompleteV1,
    SensoriumReplayIncompleteV1,
    SensoriumReplayPagePolicyV1,
    StaticKeyProvider,
    TextRecallQuery,
    active_feature_spec_id,
    active_normalizer_id,
    baseline_boundary_profile,
    canonical_json_bytes,
    encode_sensorium_state,
    recall,
    replay_sensorium_page,
)
from aluclu.cognition.contracts import JsonValue
from aluclu.cognition.ledger import VerifiedLedgerSession

MASTER_KEY = b"p" * 32


def _policy(page_size: int) -> RecallExecutionPolicyV1:
    return RecallExecutionPolicyV1(
        max_records=page_size,
        top_k=8,
        max_returned_payload_bytes=262_144,
        active_normalizer_id=active_normalizer_id(),
        active_feature_spec_id=active_feature_spec_id(),
        minimum_score_q32=0,
        minimum_margin_q32=0,
        allow_approximate=True,
        allow_incomplete=True,
    )


def _complete_recall(
    session: VerifiedLedgerSession, *, page_size: int
) -> ApproximateCandidates | ConflictedRecollection:
    query = TextRecallQuery(text="portable terminal sentinel 256")
    policy = _policy(page_size)
    current = recall(session, query, policy=policy)
    while type(current) is IncompleteRecollection:
        current = recall(session, query, policy=policy, continuation=current.continuation)
    if not isinstance(current, (ApproximateCandidates, ConflictedRecollection)):
        raise RuntimeError("portable text recall did not return candidates")
    return current


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("expected ledger path and final observation ID")
    path = Path(sys.argv[1])
    observation_id = sys.argv[2]
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        with ledger.verified_session() as session:
            event_count = session.event_count()
            if event_count != 256:
                raise RuntimeError("portable ledger has unexpected head")
            profile = baseline_boundary_profile()
            one_shot = replay_sensorium_page(
                session, SensoriumReplayPagePolicyV1(max_records=256), profile
            )
            if type(one_shot) is not SensoriumReplayCompleteV1:
                raise RuntimeError("one-shot portable replay did not complete")
            next_page = replay_sensorium_page(
                session, SensoriumReplayPagePolicyV1(max_records=37), profile
            )
            steps = 1
            while type(next_page) is SensoriumReplayIncompleteV1:
                if steps >= 8:
                    raise RuntimeError("portable replay exceeded page bound")
                next_page = replay_sensorium_page(
                    session,
                    SensoriumReplayPagePolicyV1(max_records=37),
                    next_page.continuation,
                )
                steps += 1
            if type(next_page) is not SensoriumReplayCompleteV1:
                raise RuntimeError("paged portable replay did not complete")
            exact = recall(
                session, EventIdRecallQuery(observation_id=observation_id)
            )
            if type(exact) is not ExactRecollection:
                raise RuntimeError("portable direct recall was not exact")
            text_one_shot = _complete_recall(session, page_size=256)
            text_paged = _complete_recall(session, page_size=37)
            payload = {
                "event_count": event_count,
                "one_shot_state_hex": encode_sensorium_state(one_shot.state).hex(),
                "paged_state_hex": encode_sensorium_state(next_page.state).hex(),
                "replay_records_examined": one_shot.page_work.records_examined,
                "replay_observations_applied": one_shot.page_work.observations_applied,
                "paged_replay_steps": steps,
                "exact_observation_id": exact.observation_id,
                "exact_content_hex": exact.content.canonical_bytes.hex(),
                "exact_record_hash": exact.record_hash,
                "content_is_observation": exact.content_is_observation,
                "content_is_verified_fact": exact.content_is_verified_fact,
                "one_shot_recall_ids": [
                    item.observation_id for item in text_one_shot.candidates
                ],
                "paged_recall_ids": [
                    item.observation_id for item in text_paged.candidates
                ],
                "recall_records_scanned": text_one_shot.work.records_scanned,
            }
            sys.stdout.buffer.write(
                canonical_json_bytes(cast(JsonValue, payload)) + b"\n"
            )


if __name__ == "__main__":
    main()
