from __future__ import annotations

import json
import os
import sys
import unicodedata
from dataclasses import replace

from aluclu.cognition.observation import (
    CanonicalJsonValue,
    EpisodeBoundaryDecisionV1,
    EpisodeBoundaryReason,
    ObservationRequestV1,
    ProvenanceV1,
    SensoriumCoreStateV1,
    SourceKind,
    build_canonical_observation,
    derive_boundary_signal_digests,
    derive_content_digest,
    derive_episode_id,
    derive_request_digest,
    derive_sensorium_core_state_digest,
    encode_observation_request,
    encode_sensorium_core_state,
)
from aluclu.cognition.recall_features import (
    active_feature_spec_id,
    active_normalizer_id,
    encode_retrieval_text,
    feature_vector_digest,
    search_view_utf8,
)

BOUNDARY_PROFILE_ID = "boundary-profile:" + ("1" * 64)
CONTENT_LABEL = "codepoint"
ZERO_HASH = "0" * 64


def _provenance() -> ProvenanceV1:
    return ProvenanceV1(
        source_kind=SourceKind.USER,
        source_instance_id="determinism-suite",
        origin_id="fixture:task2",
        observed_at_ns=1_725_000_000_000_000_000,
        parent_observation_ids=(),
        capture_method="subprocess",
        capture_version="1.0.0",
    )


def _request() -> ObservationRequestV1:
    return ObservationRequestV1(
        observation_id="obs:determinism-0001",
        session_id="session:task2-determinism",
        turn_id="turn:task2-determinism-0001",
        provenance=_provenance(),
        content=CanonicalJsonValue.from_value(
            {"label": CONTENT_LABEL, "text": "e\u0301"}
        ),
        retrieval_text="  e\u0301\r\nE\u0301\t",
        topic_key="topic:determinism",
        goal_ids=("goal:determinism",),
        participant_ids=("participant:assistant", "participant:user"),
        tool_invocation_id=None,
        tool_phase=None,
        force_boundary=True,
    )


def _initial_core() -> SensoriumCoreStateV1:
    return SensoriumCoreStateV1(
        boundary_profile_id=BOUNDARY_PROFILE_ID,
        session_signal_digest=None,
        current_episode_id=None,
        episode_observation_count=0,
        episode_canonical_request_bytes=0,
        goal_ids_signal_digest=None,
        participant_ids_signal_digest=None,
        tool_signal_digest=None,
        topic_signal_digest=None,
        last_observation_id=None,
        last_observation_sequence=0,
        last_observed_at_ns=None,
    )


def _post_core(request: ObservationRequestV1) -> SensoriumCoreStateV1:
    signals = derive_boundary_signal_digests(request)
    return SensoriumCoreStateV1(
        boundary_profile_id=BOUNDARY_PROFILE_ID,
        session_signal_digest=signals.session_signal_digest,
        current_episode_id=derive_episode_id(
            boundary_profile_id=BOUNDARY_PROFILE_ID,
            first_observation_id=request.observation_id,
            session_id=request.session_id,
        ),
        episode_observation_count=1,
        episode_canonical_request_bytes=len(encode_observation_request(request)),
        goal_ids_signal_digest=signals.goal_ids_signal_digest,
        participant_ids_signal_digest=signals.participant_ids_signal_digest,
        tool_signal_digest=signals.tool_signal_digest,
        topic_signal_digest=signals.topic_signal_digest,
        last_observation_id=request.observation_id,
        last_observation_sequence=1,
        last_observed_at_ns=request.provenance.observed_at_ns,
    )


def main() -> None:
    request = _request()
    initial_core = _initial_core()
    post_core = _post_core(request)
    episode_id = derive_episode_id(
        boundary_profile_id=BOUNDARY_PROFILE_ID,
        first_observation_id=request.observation_id,
        session_id=request.session_id,
    )
    observation = build_canonical_observation(
        request=request,
        boundary_decision=EpisodeBoundaryDecisionV1(
            episode_id=episode_id,
            reasons=(EpisodeBoundaryReason.FIRST_OBSERVATION,),
        ),
        pre_core_state_digest=derive_sensorium_core_state_digest(initial_core),
        post_core_state=post_core,
        pre_append_head_sequence=0,
        pre_append_head_hash=ZERO_HASH,
        boundary_profile_id=BOUNDARY_PROFILE_ID,
    )
    nfd_content = CanonicalJsonValue.from_value(
        {"label": CONTENT_LABEL, "text": "e\u0301"}
    )
    nfc_content = CanonicalJsonValue.from_value(
        {"label": CONTENT_LABEL, "text": "\u00e9"}
    )
    feature_vector = encode_retrieval_text(
        "e\u0301",
        feature_spec_id=active_feature_spec_id(),
    )

    payload = {
        "boundary_profile_id": BOUNDARY_PROFILE_ID,
        "content_digest_nfc": derive_content_digest(nfc_content),
        "content_digest_nfd": derive_content_digest(nfd_content),
        "episode_id": episode_id,
        "feature_spec_id": active_feature_spec_id(),
        "feature_vector_digest": feature_vector_digest(feature_vector),
        "normalizer_id": active_normalizer_id(),
        "post_core_bytes_len": len(encode_sensorium_core_state(post_core)),
        "post_core_state_digest": observation.post_core_state_digest,
        "pre_core_state_digest": observation.pre_core_state_digest,
        "python_hash_seed": os.environ.get("PYTHONHASHSEED"),
        "python_version": sys.version_info[:3],
        "request_bytes_len": len(encode_observation_request(request)),
        "request_digest": derive_request_digest(request),
        "search_hex_nfc": search_view_utf8(
            "\u00e9",
            normalizer_id=active_normalizer_id(),
        ).hex(),
        "search_hex_nfd": search_view_utf8(
            "e\u0301",
            normalizer_id=active_normalizer_id(),
        ).hex(),
        "timezone": os.environ.get("TZ"),
        "ucd_version": unicodedata.unidata_version,
    }
    round_tripped = replace(post_core)
    assert (
        derive_sensorium_core_state_digest(round_tripped)
        == (payload["post_core_state_digest"])
    )
    sys.stdout.write(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
