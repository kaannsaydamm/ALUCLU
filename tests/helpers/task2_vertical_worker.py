from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import cast

from test_cognition_task2_vertical import (
    MASTER_KEY,
    _active_profile,
    _policy,
)

from aluclu.cognition import (
    AbstainedRecollection,
    ConflictedRecollection,
    EncryptedLedger,
    EventIdRecallQuery,
    ExactRecollection,
    InputBoundaryError,
    NoRecollection,
    RecallBasis,
    ReconsolidationRecordV1,
    SensoriumReplayCompleteV1,
    SensoriumReplayIncompleteV1,
    SensoriumReplayPagePolicyV1,
    StaticKeyProvider,
    TextRecallQuery,
    baseline_boundary_profile,
    encode_sensorium_state,
    recall,
    reconsolidation_record_from_json_value,
    replay_continuation_from_json_value,
    replay_continuation_to_json_value,
    replay_sensorium_page,
    strict_json_loads,
    tighten_recall_policy,
)
from aluclu.cognition.contracts import JsonValue


def _lineage_snapshot(payload: JsonValue) -> tuple[ReconsolidationRecordV1, bool]:
    decoded = reconsolidation_record_from_json_value(payload)
    queryable = True
    try:
        EventIdRecallQuery(observation_id=decoded.reconsolidation_id)
    except InputBoundaryError:
        queryable = False
    return decoded, queryable


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit(
            "usage: task2_vertical_worker.py LEDGER PAGE_SIZE RECON_ID MODE"
        )
    ledger_path = Path(sys.argv[1])
    page_size = int(sys.argv[2])
    reconsolidation_id = sys.argv[3]
    mode = sys.argv[4]
    if mode not in {"live", "shredded"}:
        raise SystemExit("mode must be live or shredded")
    serialized_start = sys.stdin.buffer.read()
    start = (
        baseline_boundary_profile()
        if not serialized_start
        else replay_continuation_from_json_value(strict_json_loads(serialized_start))
    )

    with EncryptedLedger(ledger_path, StaticKeyProvider(MASTER_KEY)) as ledger:
        with ledger.verified_session() as session:
            replayed = replay_sensorium_page(
                session,
                SensoriumReplayPagePolicyV1(max_records=page_size),
                start,
            )
            if type(replayed) is SensoriumReplayIncompleteV1:
                output: dict[str, object] = {
                    "continuation": replay_continuation_to_json_value(
                        replayed.continuation
                    ),
                    "status": "incomplete",
                }
                sys.stdout.write(
                    json.dumps(
                        output,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                )
                sys.stdout.write("\n")
                return
            assert type(replayed) is SensoriumReplayCompleteV1

            child = session.read(reconsolidation_id)
            assert child is not None
            lineage, lineage_queryable = _lineage_snapshot(child.payload)
            assert type(child.payload) is dict
            lineage_payload = cast(dict[str, JsonValue], child.payload)

            if mode == "shredded":
                parent = recall(
                    session,
                    EventIdRecallQuery(observation_id="obs:vertical-0001"),
                )
                trigger = recall(
                    session,
                    EventIdRecallQuery(observation_id="obs:vertical-0005"),
                )
                assert type(parent) is NoRecollection
                assert type(trigger) is ExactRecollection
                snapshot = {
                    "lineage_basis": lineage.recall_basis.value,
                    "lineage_claims_verified_fact": (
                        "content_is_verified_fact" in lineage_payload
                    ),
                    "lineage_contains_content": "content" in lineage_payload,
                    "lineage_observation_queryable": lineage_queryable,
                    "parent_recollection": "none",
                    "parent_tombstoned": session.is_tombstoned(
                        "obs:vertical-0001"
                    ),
                    "sensorium_core_last_observation_id": (
                        replayed.state.core.last_observation_id
                    ),
                    "sensorium_core_last_observation_sequence": (
                        replayed.state.core.last_observation_sequence
                    ),
                    "sensorium_state_sha256": hashlib.sha256(
                        encode_sensorium_state(replayed.state)
                    ).hexdigest(),
                    "trigger_record_hash": trigger.record_hash,
                }
                output = {"snapshot": snapshot, "status": "complete"}
                sys.stdout.write(
                    json.dumps(
                        output,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                )
                sys.stdout.write("\n")
                return

            active = _active_profile()
            policy = _policy(active)
            tightening = tighten_recall_policy(policy, active)
            direct = tuple(
                recall(
                    session,
                    EventIdRecallQuery(observation_id=f"obs:vertical-{index:04d}"),
                )
                for index in range(1, 6)
            )
            assert all(type(item) is ExactRecollection for item in direct)
            exact = cast(tuple[ExactRecollection, ...], direct)

            selected = recall(
                session,
                TextRecallQuery(text="violet gasket checksum"),
                policy=policy,
                active_profile=active,
                policy_tightening=tightening,
            )
            assert type(selected) is ExactRecollection
            assert selected.basis is RecallBasis.CALIBRATED_TEXT_MATCH

            conflict = recall(
                session,
                TextRecallQuery(text="shared near tie signal"),
                policy=policy,
                active_profile=active,
                policy_tightening=tightening,
            )
            assert type(conflict) is ConflictedRecollection

            forced = recall(
                session,
                TextRecallQuery(text="violet gasket checksum"),
                policy=policy,
                active_profile=active,
                policy_tightening=tighten_recall_policy(
                    policy, active, force_abstain=True
                ),
            )
            assert type(forced) is AbstainedRecollection

            snapshot: dict[str, object] = {
                "conflict_candidates": [
                    candidate.observation_id for candidate in conflict.candidates
                ],
                "conflict_margin_q32": conflict.margin_q32,
                "episode_ids": [item.episode_id for item in exact],
                "forced_reason": forced.reason.value,
                "lineage_basis": lineage.recall_basis.value,
                "lineage_claims_verified_fact": (
                    "content_is_verified_fact" in lineage_payload
                ),
                "lineage_contains_content": "content" in lineage_payload,
                "lineage_effective_policy_digest": lineage.effective_policy_digest,
                "lineage_observation_queryable": lineage_queryable,
                "lineage_profile_digest": lineage.calibration_profile_digest,
                "parent_record_hash": exact[0].record_hash,
                "record_hashes": [item.record_hash for item in exact],
                "selected_basis": selected.basis.value,
                "selected_observation_id": selected.observation_id,
                "selected_record_hash": selected.record_hash,
                "sensorium_state_sha256": hashlib.sha256(
                    encode_sensorium_state(replayed.state)
                ).hexdigest(),
                "snapshot_head_sequence": (
                    replayed.state.task1_checkpoint.snapshot_head_sequence
                ),
                "trigger_record_hash": exact[4].record_hash,
            }

    output = {"snapshot": snapshot, "status": "complete"}
    sys.stdout.write(json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
