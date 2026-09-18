import pytest

from app.application.capability_registry import (
    CapabilityNotFoundError,
    CapabilityRegistry,
    InvalidCapabilityError,
)
from app.application.capability_result import CapabilityResult


class FakeCapability:
    def execute(self, context):
        return CapabilityResult.success()


class InvalidCapability:
    pass


def test_registry_can_register_and_resolve_capability():
    registry = CapabilityRegistry()
    capability = FakeCapability()

    registry.register("video_download", capability)

    resolved = registry.resolve("video_download")

    assert resolved is capability


def test_registry_raises_when_capability_is_not_found():
    registry = CapabilityRegistry()

    with pytest.raises(CapabilityNotFoundError):
        registry.resolve("video_download")


def test_registry_rejects_invalid_capability():
    registry = CapabilityRegistry()

    with pytest.raises(InvalidCapabilityError):
        registry.register("video_download", InvalidCapability())


def test_registry_rejects_empty_capability_id():
    registry = CapabilityRegistry()

    with pytest.raises(ValueError, match="Capability id cannot be empty"):
        registry.register(" ", FakeCapability())
