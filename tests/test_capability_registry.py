from app.application.capability_registry import CapabilityRegistry
import pytest

from app.application.capability_registry import (
    CapabilityNotFoundError,
    CapabilityRegistry,
)

class FakeCapability:
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