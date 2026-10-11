from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import re
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypeAlias, cast

from .contracts import InputBoundaryError, JsonValue, StateIntegrityError

MAX_EVENT_ID_BYTES = 256
MAX_PAYLOAD_BYTES = 2_097_152
MAX_JSON_DEPTH = 32
MAX_JSON_NODES = 65_536
EVENT_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}\Z")
STATE_NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")

_JsonScalar: TypeAlias = None | bool | int | float | str


def validate_event_id(value: str) -> str:
    if type(value) is not str:
        raise InputBoundaryError("event_id must be a string")
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise InputBoundaryError("event_id must be ASCII") from exc
    if len(encoded) > MAX_EVENT_ID_BYTES or EVENT_ID_PATTERN.fullmatch(value) is None:
        raise InputBoundaryError("event_id is outside canonical boundary")
    return value


def canonical_json_bytes(value: JsonValue) -> bytes:
    _validate_json_tree(value)
    try:
        encoded = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, UnicodeEncodeError, ValueError) as exc:
        raise InputBoundaryError("value is not canonical JSON") from exc
    if len(encoded) > MAX_PAYLOAD_BYTES:
        raise InputBoundaryError("canonical payload exceeds 2097152 bytes")
    return encoded


def strict_json_loads(data: bytes) -> JsonValue:
    if type(data) is not bytes:
        raise InputBoundaryError("JSON input must be bytes")
    if len(data) > MAX_PAYLOAD_BYTES:
        raise InputBoundaryError("canonical payload exceeds 2097152 bytes")

    def reject_constant(value: str) -> None:
        raise InputBoundaryError(f"non-finite JSON constant is not allowed: {value}")

    def reject_duplicate_keys(pairs: list[tuple[str, JsonValue]]) -> dict[str, JsonValue]:
        seen: set[str] = set()
        result: dict[str, JsonValue] = {}
        for key, value in pairs:
            if key in seen:
                raise InputBoundaryError(f"duplicate JSON object key: {key}")
            seen.add(key)
            result[key] = value
        return result

    try:
        decoded = json.loads(
            data,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_constant,
        )
    except InputBoundaryError:
        raise
    except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputBoundaryError("invalid JSON bytes") from exc
    _validate_json_tree(decoded)
    return cast(JsonValue, decoded)


class SafeStateCodec:
    def __init__(self, root: str | Path, *, integrity_key: bytes) -> None:
        if type(integrity_key) is not bytes or len(integrity_key) != 32:
            raise InputBoundaryError("integrity_key must be exactly 32 bytes")
        self._root = Path(root)
        self._key = integrity_key

    def save(
        self,
        name: str,
        state: JsonValue,
        metadata: Mapping[str, JsonValue],
    ) -> int:
        safe_name = _validate_state_name(name)
        metadata_dict = _metadata_dict(metadata)
        self._root.mkdir(parents=True, exist_ok=True)
        generation = self._next_generation(safe_name)
        manifest_name = f"{safe_name}.{generation:020d}.manifest.json"
        manifest = {
            "generation": generation,
            "metadata": metadata_dict,
            "name": safe_name,
            "state": state,
            "version": 1,
        }
        manifest_bytes = canonical_json_bytes(cast(JsonValue, manifest))
        manifest_mac = self._mac_hex(b"manifest", manifest_bytes)
        manifest_envelope = {"mac": manifest_mac, "payload": manifest}
        _durable_replace(self._root / manifest_name, canonical_json_bytes(manifest_envelope))

        pointer = {
            "generation": generation,
            "manifest": manifest_name,
            "manifest_mac": manifest_mac,
            "name": safe_name,
            "version": 1,
        }
        pointer_bytes = canonical_json_bytes(cast(JsonValue, pointer))
        pointer_envelope = {
            "mac": self._mac_hex(b"pointer", pointer_bytes),
            "payload": pointer,
        }
        _durable_replace(self._pointer_path(safe_name), canonical_json_bytes(pointer_envelope))
        return generation

    def load(self, name: str) -> tuple[JsonValue, dict[str, JsonValue]]:
        safe_name = _validate_state_name(name)
        pointer = self._read_pointer(safe_name)
        manifest = self._read_manifest(safe_name, pointer)
        state = manifest.get("state")
        metadata = manifest.get("metadata")
        if type(metadata) is not dict:
            raise StateIntegrityError("state metadata is malformed")
        _validate_json_tree(state)
        _validate_json_tree(metadata)
        return cast(JsonValue, state), cast(dict[str, JsonValue], metadata)

    def _next_generation(self, safe_name: str) -> int:
        pointer_path = self._pointer_path(safe_name)
        if not pointer_path.exists():
            return 1
        pointer = self._read_pointer(safe_name)
        self._read_manifest(safe_name, pointer)
        generation = pointer.get("generation")
        return cast(int, generation) + 1

    def _pointer_path(self, safe_name: str) -> Path:
        return self._root / f"{safe_name}.json"

    def _mac_hex(self, domain: bytes, payload: bytes) -> str:
        return hmac.new(self._key, domain + b"\0" + payload, hashlib.sha256).hexdigest()

    def _read_pointer(self, safe_name: str) -> dict[str, JsonValue]:
        pointer = self._read_envelope(self._pointer_path(safe_name), b"pointer")
        if pointer.get("version") != 1 or pointer.get("name") != safe_name:
            raise StateIntegrityError("state pointer does not match requested name")
        manifest_name = pointer.get("manifest")
        generation = pointer.get("generation")
        manifest_mac = pointer.get("manifest_mac")
        if (
            type(manifest_name) is not str
            or type(generation) is not int
            or generation < 1
            or type(manifest_mac) is not str
            or Path(manifest_name).name != manifest_name
            or not manifest_name.startswith(f"{safe_name}.")
        ):
            raise StateIntegrityError("state pointer is malformed")
        return pointer

    def _read_manifest(
        self,
        safe_name: str,
        pointer: Mapping[str, JsonValue],
    ) -> dict[str, JsonValue]:
        manifest_name = cast(str, pointer["manifest"])
        generation = cast(int, pointer["generation"])
        manifest_mac = cast(str, pointer["manifest_mac"])
        manifest_path = self._root / manifest_name
        manifest = self._read_envelope(manifest_path, b"manifest", expected_mac=manifest_mac)
        if (
            manifest.get("version") != 1
            or manifest.get("name") != safe_name
            or manifest.get("generation") != generation
        ):
            raise StateIntegrityError("state manifest does not match pointer")
        return manifest

    def _read_envelope(
        self,
        path: Path,
        domain: bytes,
        *,
        expected_mac: str | None = None,
    ) -> dict[str, JsonValue]:
        try:
            envelope = strict_json_loads(path.read_bytes())
        except OSError as exc:
            raise StateIntegrityError(f"state file is unavailable: {path.name}") from exc
        if type(envelope) is not dict:
            raise StateIntegrityError("state envelope is malformed")
        payload = envelope.get("payload")
        mac = envelope.get("mac")
        if type(payload) is not dict or type(mac) is not str:
            raise StateIntegrityError("state envelope is malformed")
        payload_bytes = canonical_json_bytes(payload)
        actual_mac = self._mac_hex(domain, payload_bytes)
        if not hmac.compare_digest(mac, actual_mac):
            raise StateIntegrityError("state envelope MAC does not verify")
        if expected_mac is not None and not hmac.compare_digest(mac, expected_mac):
            raise StateIntegrityError("state manifest MAC does not match pointer")
        return payload

def _validate_state_name(name: str) -> str:
    if type(name) is not str or STATE_NAME_PATTERN.fullmatch(name) is None:
        raise InputBoundaryError("state name is outside canonical boundary")
    return name


def _metadata_dict(metadata: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    if type(metadata) is not dict:
        raise InputBoundaryError("metadata must be a JSON object")
    _validate_json_tree(metadata)
    return dict(metadata)


def _validate_json_tree(value: Any) -> None:
    stack: list[tuple[Any, int, bool]] = [(value, 1, False)]
    active_containers: set[int] = set()
    nodes = 0

    while stack:
        current, depth, leaving = stack.pop()
        if leaving:
            active_containers.remove(id(current))
            continue
        if depth > MAX_JSON_DEPTH:
            raise InputBoundaryError("JSON depth exceeds 32")
        nodes += 1
        if nodes > MAX_JSON_NODES:
            raise InputBoundaryError("JSON node count exceeds 65536")

        current_type = type(current)
        if current is None or current_type in (bool, int):
            continue
        if current_type is float:
            if not math.isfinite(current):
                raise InputBoundaryError("non-finite floats are not canonical JSON")
            continue
        if current_type is str:
            _validate_string(current)
            continue
        if current_type is list:
            container_id = id(current)
            if container_id in active_containers:
                raise InputBoundaryError("JSON cycles are not allowed")
            active_containers.add(container_id)
            stack.append((current, depth, True))
            for item in reversed(current):
                stack.append((item, depth + 1, False))
            continue
        if current_type is dict:
            container_id = id(current)
            if container_id in active_containers:
                raise InputBoundaryError("JSON cycles are not allowed")
            active_containers.add(container_id)
            stack.append((current, depth, True))
            for key, item in reversed(list(current.items())):
                if type(key) is not str:
                    raise InputBoundaryError("JSON object keys must be strings")
                nodes += 1
                if nodes > MAX_JSON_NODES:
                    raise InputBoundaryError("JSON node count exceeds 65536")
                _validate_string(key)
                stack.append((item, depth + 1, False))
            continue
        raise InputBoundaryError(f"unsupported JSON type: {current_type.__name__}")


def _validate_string(value: str) -> None:
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise InputBoundaryError("lone Unicode surrogates are not canonical JSON") from exc


def _durable_replace(path: Path, data: bytes) -> None:
    """Atomically replace a file after flushing bytes and the replace operation.

    Windows cannot fsync a directory handle through Python's portable APIs, so
    the replace step uses MoveFileExW with MOVEFILE_WRITE_THROUGH. POSIX uses
    os.replace followed by parent directory fsync.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        with temp_path.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if os.name == "nt":
            _windows_replace_write_through(temp_path, path)
        else:
            os.replace(temp_path, path)
            _fsync_directory(path.parent)
    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass


def _windows_replace_write_through(source: Path, target: Path) -> None:
    import ctypes

    movefile_replace_existing = 0x1
    movefile_write_through = 0x8
    flags = movefile_replace_existing | movefile_write_through
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    if not kernel32.MoveFileExW(str(source), str(target), flags):
        error = ctypes.get_last_error()
        raise OSError(error, "MoveFileExW failed", str(target))


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
