from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, TypeAlias

JsonValue: TypeAlias = (
    None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
)


class CognitionError(Exception):
    """Base class for cognition subsystem failures."""


class InputBoundaryError(CognitionError):
    """Raised when caller input cannot be represented canonically."""


class StateIntegrityError(CognitionError):
    """Raised when authenticated state sidecars do not verify."""


class PersistenceError(CognitionError):
    """Base class for persistence setup and capability failures."""


class UnsafePathError(PersistenceError):
    """Raised when a persistence path is unsafe for local storage."""


class KeyProviderUnavailable(PersistenceError):
    """Raised when a configured key provider cannot return its key."""


class LedgerCapabilityUnavailable(PersistenceError):
    """Raised when the platform cannot satisfy a ledger capability."""


class LedgerError(CognitionError):
    """Base class for encrypted ledger failures."""


class LedgerLifecycleError(LedgerError):
    """Raised when a ledger object is used in an invalid lifecycle state."""


class LedgerConflictError(LedgerError):
    """Raised when a requested ledger mutation conflicts with existing history."""


class LedgerMigrationRequired(LedgerError):
    """Raised when existing state is not supported by this schema."""


class LedgerIntegrityError(LedgerError):
    """Raised when authenticated ledger state fails verification."""


class LedgerKeyError(LedgerIntegrityError):
    """Raised when a record key is missing or invalid."""


class LedgerRollbackError(LedgerIntegrityError):
    """Raised when authenticated state appears rolled back."""


class LedgerSnapshotChanged(LedgerIntegrityError):
    """Raised when a cursor checkpoint no longer matches the ledger head."""


class LedgerSecurityScope(str, Enum):
    STATIC_TEST_KEY = "static_test_key"
    LOCAL_FILE_KEY = "local_file_key"
    OS_KEYRING = "os_keyring"


@dataclass(frozen=True, kw_only=True)
class LedgerRecord:
    sequence: int
    event_id: str
    payload: JsonValue
    record_hash: str
    created_ns: int


@dataclass(frozen=True, kw_only=True)
class AppendOutcome:
    record: LedgerRecord
    created: bool


@dataclass(frozen=True, kw_only=True)
class LedgerCursorCheckpoint:
    ledger_id: str
    snapshot_head_sequence: int
    snapshot_head_hash: str
    next_sequence: int


@dataclass(frozen=True, kw_only=True)
class LedgerVerificationStats:
    full_verifications: int
    delta_verifications: int


class KeyProvider(Protocol):
    @property
    def security_scope(self) -> LedgerSecurityScope: ...

    def get_key(self) -> bytes: ...
