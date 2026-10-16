"""Harmless temp-storage subprocess fixture; never a training entrypoint."""

import os
import sys
from pathlib import Path

from aluclu.alc_r0.canonical import canonical_json_bytes, parse_canonical_json, sha256_bytes
from aluclu.alc_r0.reservation_store import PreparedReservationIntent, ReservationStore


class ExitAfterIntent(ReservationStore):
    def _persist(self, path, intent):
        super()._persist(path, intent)
        os._exit(73)


class ExitBeforeOwner(ReservationStore):
    def _publish(self, candidate):
        os._exit(73)


class ExitAfterOwner(ReservationStore):
    def _publish(self, candidate):
        super()._publish(candidate)
        os._exit(73)


def main():
    mode, root_arg, declaration_arg, intent_arg, output_arg = sys.argv[1:]
    root, declaration_path, intent_path, output_path = map(Path,
        (root_arg, declaration_arg, intent_arg, output_arg))
    if any(not path.is_absolute() for path in (root, declaration_path, intent_path, output_path)):
        raise ValueError("fixture requires exact absolute temporary paths")
    for path, limit in ((declaration_path, 16384), (intent_path, 16384)):
        if not 0 < path.stat().st_size <= limit:
            raise ValueError("fixture input byte cap")
    declarations = (declaration_path.read_bytes(),)
    data = intent_path.read_bytes()
    intent = PreparedReservationIntent(data, sha256_bytes(data))
    classes = {"intent": ExitAfterIntent, "journal": ExitBeforeOwner, "owner": ExitAfterOwner,
               "recover": ReservationStore, "compete": ReservationStore}
    store = classes[mode](root, declarations)
    if mode in ("intent", "journal", "owner"):
        store.commit(intent)
        raise AssertionError("crash fixture failed to terminate")
    if mode == "recover":
        receipt = store.resume(intent)
        verified = ReservationStore(root, declarations).read(receipt.sha256)
        assert verified == receipt
        output_path.write_bytes(canonical_json_bytes(dict(owner_root=receipt.sha256,
            events=receipt.snapshot.event_count, outstanding_gpu_ns=str(receipt.snapshot.outstanding_gpu_ns),
            state=receipt.snapshot.reservations[0].state)))
    else:
        try:
            receipt = store.commit(intent)
        except ValueError:
            sys.exit(74)
        output_path.write_bytes(canonical_json_bytes(dict(owner_root=receipt.sha256)))


if __name__ == "__main__":
    main()
