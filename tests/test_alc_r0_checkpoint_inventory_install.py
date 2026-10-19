"""Atomic callback installation controls; no wrapper/host qualification."""

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from test_alc_r0_checkpoint_execution import Owner

from aluclu.alc_r0.checkpoint_execution import CheckpointExecutionError


def test_install_preserves_controller_and_does_not_execute_getter():
    owner = Owner()
    controller = owner.controller
    calls = []

    def getter():
        calls.append(1)
        return "a" * 64

    controller._install_state_fingerprint_getter(getter)
    assert owner.controller is controller
    assert controller.state_fingerprint_getter is getter
    assert not calls
    controller._install_state_fingerprint_getter(getter)
    assert not calls
    with controller.session():
        assert calls == [1]


@pytest.mark.parametrize("candidate", [None, 1, "constant"])
def test_invalid_install_leaves_default_unchanged(candidate):
    controller = Owner().controller
    with pytest.raises(CheckpointExecutionError):
        controller._install_state_fingerprint_getter(candidate)
    assert controller.state_fingerprint_getter is None


def test_replacement_denied_without_changing_installed_binding():
    controller = Owner().controller

    def getter():
        return "a" * 64

    controller._install_state_fingerprint_getter(getter)
    with pytest.raises(CheckpointExecutionError):
        controller._install_state_fingerprint_getter(lambda: "replacement")
    assert controller.state_fingerprint_getter is getter


@pytest.mark.parametrize("installed", [False, True])
def test_install_during_lease_denied_even_for_identical_binding(installed):
    controller = Owner().controller

    def getter():
        return "a" * 64

    if installed:
        controller._install_state_fingerprint_getter(getter)
    with controller.session():
        with pytest.raises(CheckpointExecutionError):
            controller._install_state_fingerprint_getter(getter)
        assert controller.state_fingerprint_getter is (getter if installed else None)
    assert controller._active is None


def test_install_serializes_with_capture_before_active_is_published():
    """Capture owns the lock even before _active becomes visible."""
    controller = Owner().controller
    capturing, release_capture, active, release_lease = (
        threading.Event() for _ in range(4)
    )

    def getter():
        capturing.set()
        assert release_capture.wait(5)
        return "a" * 64

    controller._install_state_fingerprint_getter(getter)

    def lease():
        with controller.session():
            active.set()
            assert release_lease.wait(5)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(lease)
        try:
            assert capturing.wait(5)
            second = pool.submit(controller._install_state_fingerprint_getter, getter)
            release_capture.set()
            assert active.wait(5)
            with pytest.raises(CheckpointExecutionError):
                second.result(timeout=5)
            assert controller.state_fingerprint_getter is getter
        finally:
            release_capture.set()
            release_lease.set()
        first.result(timeout=5)
    assert controller._active is None
