"""Commit lineage in a real process and die before caller-visible completion."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from aluclu.cognition import EncryptedLedger, StaticKeyProvider
from aluclu.cognition.recollection import EventIdRecallQuery, ExactRecollection, recall
from aluclu.cognition.reconsolidation import (
    ReconsolidationReason,
    commit_reconsolidation,
    propose_reconsolidation,
)


def main() -> None:
    ledger_path = Path(sys.argv[1])
    with EncryptedLedger(ledger_path, StaticKeyProvider(b"m" * 32)) as ledger:
        with ledger.verified_session() as session:
            parent = recall(session, EventIdRecallQuery(observation_id="obs:recon-0001"))
            trigger = recall(session, EventIdRecallQuery(observation_id="obs:recon-0002"))
            assert type(parent) is ExactRecollection
            assert type(trigger) is ExactRecollection
            proposal = propose_reconsolidation(
                parent, trigger, reason=ReconsolidationReason.CORRECTION
            )
            outcome = commit_reconsolidation(session, proposal)
            assert outcome.created is True
            os._exit(93)


if __name__ == "__main__":
    main()
