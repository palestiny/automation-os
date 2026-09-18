import pytest

from app.application.capability import Capability
from app.application.capability_factory import CapabilityFactory
from app.application.capability_result import CapabilityResult


class ProviderCapability:
    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    def execute(self, context):
        return CapabilityResult.success()


class InvalidCapability:
    pass


def test_factory_constructs_configured_capability():
    factory = CapabilityFactory(
        {"video_download": lambda: ProviderCapability("provider-a")}
    )

    capability = factory.create("video_download")

    assert isinstance(capability, Capability)
    assert capability.provider_name == "provider-a"


def test_factory_creates_a_fresh_instance_for_each_request():
    factory = CapabilityFactory(
        {"video_download": lambda: ProviderCapability("provider-a")}
    )

    first = factory.create("video_download")
    second = factory.create("video_download")

    assert first is not second


def test_factory_rejects_unknown_capability_implementation():
    factory = CapabilityFactory({})

    with pytest.raises(
        ValueError,
        match="Capability implementation not configured",
    ):
        factory.create("video_download")


def test_factory_rejects_invalid_builder_result():
    factory = CapabilityFactory(
        {"video_download": lambda: InvalidCapability()}
    )

    with pytest.raises(TypeError, match="Capability"):
        factory.create("video_download")


def test_factory_does_not_expose_provider_selection_to_workflow_contract():
    factory = CapabilityFactory(
        {"video_download": lambda: ProviderCapability("provider-a")}
    )

    capability = factory.create("video_download")

    assert capability.provider_name == "provider-a"
