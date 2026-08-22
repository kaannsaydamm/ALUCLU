import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from aluclu.cognition import (
    EncryptedLedger,
    FileRecordKeyStore,
    LedgerConflictError,
    LedgerIntegrityError,
    LedgerKeyError,
    LedgerLifecycleError,
    LedgerMigrationRequired,
    StaticKeyProvider,
)
from aluclu.cognition import ledger as ledger_module
from aluclu.cognition.codec import MAX_PAYLOAD_BYTES

MASTER_KEY = b"m" * 32


def test_construction_is_side_effect_free_and_lifecycle_is_typed(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    ledger = EncryptedLedger(path, StaticKeyProvider(MASTER_KEY))

    assert list(tmp_path.iterdir()) == []
    for operation in (
        ledger.event_count,
        lambda: ledger.read(""),
        lambda: ledger.append("", {"value": 1}),
        lambda: ledger.append_once("", {"value": 1}),
    ):
        with pytest.raises(LedgerLifecycleError):
            operation()

    ledger.unlock()
    ledger.unlock()
    ledger.close()
    ledger.close()
    for operation in (
        ledger.event_count,
        lambda: ledger.read(""),
        lambda: ledger.append("", {"value": 1}),
        lambda: ledger.append_once("", {"value": 1}),
    ):
        with pytest.raises(LedgerLifecycleError):
            operation()


def test_every_ledger_connection_enables_required_security_pragmas(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        connection = ledger._connection_required()
        assert connection.execute("PRAGMA trusted_schema").fetchone() == (0,)
        assert connection.execute("PRAGMA cell_size_check").fetchone() == (1,)

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        connection = ledger._connection_required()
        assert connection.execute("PRAGMA trusted_schema").fetchone() == (0,)
        assert connection.execute("PRAGMA cell_size_check").fetchone() == (1,)


def test_append_round_trip_is_encrypted_and_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    marker = "plain-marker-should-not-hit-sqlite"

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        first = ledger.append_once("evt_1", {"secret": marker})
        again = ledger.append_once("evt_1", {"secret": marker})

        assert first.created is True
        assert again.created is False
        assert again.record == first.record
        assert ledger.read("evt_1") == first.record
        assert ledger.event_count() == 1

    assert marker.encode() not in path.read_bytes()


def test_append_and_append_once_reject_conflicting_lineage(tmp_path: Path) -> None:
    with EncryptedLedger(tmp_path / "memory.sqlite3", StaticKeyProvider(MASTER_KEY)) as ledger:
        ledger.append("evt_1", {"value": 1})

        with pytest.raises(LedgerConflictError):
            ledger.append("evt_1", {"value": 1})
        with pytest.raises(LedgerConflictError):
            ledger.append_once("evt_1", {"value": 2})


def test_wrong_master_key_cannot_claim_existing_empty_ledger(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(b"a" * 32)):
        pass

    with pytest.raises(LedgerKeyError):
        EncryptedLedger(path, StaticKeyProvider(b"b" * 32)).unlock()


def test_existing_incomplete_database_is_never_initialized(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    connection = sqlite3.connect(path)
    try:
        connection.execute("CREATE TABLE legacy(value TEXT)")
        connection.execute("PRAGMA user_version = 1")
        connection.commit()
        assert connection.execute("PRAGMA journal_mode").fetchone() == ("delete",)
    finally:
        connection.close()

    with pytest.raises(LedgerMigrationRequired):
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)).unlock()

    connection = sqlite3.connect(path)
    try:
        assert connection.execute("PRAGMA user_version").fetchone() == (1,)
        assert connection.execute("PRAGMA journal_mode").fetchone() == ("delete",)
        assert {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        } == {"legacy"}
    finally:
        connection.close()


def test_schema_v2_and_exact_metadata_keys_are_created(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)):
        pass

    connection = sqlite3.connect(path)
    try:
        assert connection.execute("PRAGMA user_version").fetchone() == (2,)
        metadata = {row[0] for row in connection.execute("SELECT key FROM metadata")}
        assert metadata == {
            "schema_version",
            "ledger_id",
            "identity_root",
            "key_check",
            "head_sequence",
            "head_hash",
        }
    finally:
        connection.close()


def test_schema_column_drift_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)):
        pass
    connection = sqlite3.connect(path)
    try:
        connection.execute("ALTER TABLE history ADD COLUMN injected TEXT")
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(LedgerIntegrityError):
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)).unlock()


def test_new_ledger_accepts_explicit_matching_record_store(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    store = FileRecordKeyStore(
        tmp_path / "custom-keys.json",
        b"s" * 32,
        ledger_id="özel-ledger",
    )

    with EncryptedLedger(
        path,
        StaticKeyProvider(MASTER_KEY),
        record_key_store=store,
    ) as ledger:
        assert ledger.ledger_id == "özel-ledger"
        ledger.append("evt_1", {"value": 1})
        assert ledger.read("evt_1") is not None


def test_history_hash_matches_independent_literal_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "memory.sqlite3"
    random_values = iter([b"i" * 32, b"d" * 32, b"n" * 12])
    monkeypatch.setattr(ledger_module.secrets, "token_hex", lambda size: "11" * 16)
    monkeypatch.setattr(
        ledger_module.secrets,
        "token_bytes",
        lambda size: next(random_values),
    )
    monkeypatch.setattr(ledger_module.time, "time_ns", lambda: 123_456_789)

    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        outcome = ledger.append("evt_1", {"value": 1})

    connection = sqlite3.connect(path)
    try:
        ciphertext, record_hash = connection.execute(
            "SELECT ciphertext, record_hash FROM history WHERE sequence = 1"
        ).fetchone()
    finally:
        connection.close()

    assert ciphertext.hex() == "8fc5417fe8025043d55f040debbc155821c5e4df2e73f8c2cd71df"
    assert outcome.record.record_hash == (
        "3043a85acd76d0b475e7719b035e22ebd415840967246a8dfa611743f9d7bf18"
    )
    assert record_hash.hex() == outcome.record.record_hash


def test_ledger_accepts_exact_maximum_canonical_payload(tmp_path: Path) -> None:
    payload = "x" * (MAX_PAYLOAD_BYTES - 2)

    with EncryptedLedger(
        tmp_path / "memory.sqlite3",
        StaticKeyProvider(MASTER_KEY),
    ) as ledger:
        outcome = ledger.append("evt_max", payload)
        assert outcome.record.payload == payload
        assert ledger.read("evt_max") == outcome.record


@pytest.mark.parametrize(
    "mutation",
    [
        "UPDATE history SET ciphertext = X'00' WHERE sequence = 1",
        "DELETE FROM records WHERE event_id = 'evt_1'",
        "UPDATE metadata SET value = X'00' WHERE key = 'head_hash'",
    ],
)
def test_direct_sql_tamper_fails_full_verification(tmp_path: Path, mutation: str) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        ledger.append("evt_1", {"value": 1})

    connection = sqlite3.connect(path)
    try:
        connection.execute(mutation)
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(LedgerIntegrityError):
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)).unlock()


def test_forged_tombstone_projection_fails_full_verification(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)) as ledger:
        ledger.append("evt_1", {"value": 1})

    connection = sqlite3.connect(path)
    try:
        connection.execute("DELETE FROM records WHERE event_id = 'evt_1'")
        connection.execute(
            """
            INSERT INTO tombstones(event_id, history_sequence, record_hash)
            SELECT event_id, sequence, record_hash FROM history WHERE sequence = 1
            """
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(LedgerIntegrityError):
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)).unlock()


def test_missing_anchor_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    with EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)):
        pass
    anchor = path.with_suffix(path.suffix + ".anchor.json")
    anchor.unlink()

    with pytest.raises(LedgerIntegrityError):
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)).unlock()


def test_valid_lagging_anchor_advances_only_after_full_verification(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    anchor = path.with_suffix(path.suffix + ".anchor.json")
    ledger = EncryptedLedger(path, StaticKeyProvider(MASTER_KEY))
    ledger.unlock()
    old_anchor = anchor.read_bytes()
    try:
        ledger.append("evt_1", {"value": 1})
        current_anchor = anchor.read_bytes()
        anchor.write_bytes(old_anchor)

        ledger.verify_integrity()

        assert anchor.read_bytes() == current_anchor
    finally:
        ledger.close()


def test_open_ledger_detects_external_key_check_mutation(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    ledger = EncryptedLedger(path, StaticKeyProvider(MASTER_KEY))
    ledger.unlock()
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "UPDATE metadata SET value = zeroblob(32) WHERE key = 'key_check'"
        )
        connection.commit()
    finally:
        connection.close()

    try:
        with pytest.raises(LedgerKeyError):
            ledger.verify_integrity()
    finally:
        ledger.close()


def test_anchor_replaced_by_symlink_after_construction_fails_closed(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.sqlite3"
    ledger = EncryptedLedger(path, StaticKeyProvider(MASTER_KEY))
    ledger.unlock()
    anchor = path.with_suffix(path.suffix + ".anchor.json")
    target = tmp_path / "copied-anchor.json"
    target.write_bytes(anchor.read_bytes())
    anchor.unlink()
    try:
        anchor.symlink_to(target)
    except (OSError, NotImplementedError):
        ledger.close()
        pytest.skip("symlinks are unavailable on this platform")

    try:
        with pytest.raises(LedgerIntegrityError):
            ledger.verify_integrity()
    finally:
        ledger.close()


def test_two_ledger_objects_cannot_fork_history(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite3"
    ledgers = [
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)),
        EncryptedLedger(path, StaticKeyProvider(MASTER_KEY)),
    ]
    for ledger in ledgers:
        ledger.unlock()
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(
                pool.map(
                    lambda item: item[0].append(*item[1]),
                    zip(
                        ledgers,
                        [("evt_1", {"i": 1}), ("evt_2", {"i": 2})],
                        strict=True,
                    ),
                )
            )

        assert {outcome.record.sequence for outcome in outcomes} == {1, 2}
        ledgers[0].verify_integrity()
    finally:
        for ledger in ledgers:
            ledger.close()
