import pytest

from aluclu.cognition import InputBoundaryError, validate_event_id


@pytest.mark.parametrize("value", ["", "has space", "é", "line\nbreak", "a" * 257])
def test_event_id_rejects_noncanonical_or_oversized_values(value: str) -> None:
    with pytest.raises(InputBoundaryError):
        validate_event_id(value)


@pytest.mark.parametrize("value", ["a", "evt_000001", "turn:1", "a.b-c_d"])
def test_event_id_accepts_canonical_ascii_values(value: str) -> None:
    assert validate_event_id(value) == value
