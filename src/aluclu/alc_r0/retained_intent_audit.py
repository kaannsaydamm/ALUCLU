"""Closed published intent chain audit, not launch or global accounting authority.

Only cooperating writers in the existing trusted namespace are excluded by the
owner lock. The caller supplies a current independently authenticated owner root.
Rolling back both that authority and local storage is not detected. Off-ledger
attempts, review authorization, historical resources and fsync are not inferred.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .canonical import canonical_json_bytes, parse_canonical_json
from .manifest_publication import PublicationError, PublishedManifest, _sha
from .owned_append import AppendIntent, OwnedAppend


@dataclass(frozen=True, slots=True)
class RetainedIntentAudit:
    publication: PublishedManifest
    intent_count: int
    intent_bytes: int
    history_sha256: str


def audit_retained_intents(
    writer: OwnedAppend, expected_owner_sha256: str
) -> RetainedIntentAudit:
    """Verify every published intent and event, without repair or publication.

    The one-event-per-generation coordinator history must start at exact genesis.
    Pending/orphan inventory requires separate explicit recovery, never adoption
    here. Cost includes reading all pages and all retained bounded intent bytes;
    count ceilings are not a global storage/RSS reservation or performance claim.
    Existing read locks may create companion files. No partial receipt escapes.
    """
    if type(writer) is not OwnedAppend:
        raise PublicationError("exact coordinator required for retained audit")
    with writer.owner._lock():
        publication = writer.owner.read(expected_owner_sha256)
        current = parse_canonical_json(publication.data)
        generation = current["generation"]
        writer._intent_inventory(generation)
        events = tuple(
            event for attempt in publication.view.attempts for event in attempt.events
        )
        if generation != len(events):
            raise PublicationError("published generations differ from event count")
        previous = canonical_json_bytes(
            dict(
                version=1,
                generation=0,
                spec_sha256=current["spec_sha256"],
                previous=None,
                manifest=dict(version=1, spec_sha256=current["spec_sha256"], pages=[]),
                review=None,
            )
        )
        digest = hashlib.sha256(b"ALC-R0-RETAINED-INTENT-AUDIT-V1\0")
        digest.update(bytes.fromhex(current["spec_sha256"]))
        digest.update(bytes.fromhex(publication.sha256))
        retained_bytes = 0
        for index, event in enumerate(events, 1):
            path = writer.intents / f"intent-{index:06d}.json"
            data = writer._intent_read(path)
            built = writer._decode(AppendIntent(data, _sha(data)))
            prepared = built[1]
            if prepared.previous != previous:
                raise PublicationError("retained intent predecessor chain differs")
            item = parse_canonical_json(data)
            if canonical_json_bytes(item["event"]) != event:
                raise PublicationError("retained intent differs from published event")
            # Rebuilding each single-event transition from exact genesis proves
            # intermediate manifests/heads, not just neighbor-root equality.
            previous = prepared.candidate
            retained_bytes += len(data)
            digest.update(index.to_bytes(8, "big"))
            digest.update(len(data).to_bytes(8, "big"))
            digest.update(data)
        if previous != publication.data:
            raise PublicationError("retained intent chain does not reach pinned owner")
        writer._intent_inventory(generation)
        return RetainedIntentAudit(
            publication, generation, retained_bytes, digest.hexdigest()
        )
