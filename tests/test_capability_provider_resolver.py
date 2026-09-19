import pytest

from app.application.capability_provider import CapabilityProvider
from app.application.capability_provider_resolver import (
    CapabilityProviderNotFoundError,
    CapabilityProviderResolver,
)
from app.application.capability_result import CapabilityResult


class FakeCapability:
    def execute(self, context):
        return CapabilityResult.success()


class FakeProvider:
    def __init__(self, provider_id: str, capability_id: str):
        self.provider_id = provider_id
        self.capability_id = capability_id

    def create(self):
        return FakeCapability()


class InvalidProvider:
    provider_id = "invalid"
    capability_id = "video_download"


def test_provider_contract_exposes_stable_identity():
    provider = FakeProvider("provider-a", "video_download")

    assert isinstance(provider, CapabilityProvider)
    assert provider.provider_id == "provider-a"
    assert provider.capability_id == "video_download"


def test_resolver_supports_multiple_providers_for_one_capability():
    resolver = CapabilityProviderResolver()
    provider_a = FakeProvider("provider-a", "video_download")
    provider_b = FakeProvider("provider-b", "video_download")

    resolver.register(provider_a)
    resolver.register(provider_b)
    resolver.set_default("video_download", "provider-b")

    assert resolver.resolve("video_download") is provider_b


def test_resolver_requires_explicit_default_when_multiple_providers_exist():
    resolver = CapabilityProviderResolver()
    resolver.register(FakeProvider("provider-a", "video_download"))
    resolver.register(FakeProvider("provider-b", "video_download"))

    with pytest.raises(
        CapabilityProviderNotFoundError,
        match="No default provider configured",
    ):
        resolver.resolve("video_download")


def test_resolver_fails_when_capability_has_no_provider():
    resolver = CapabilityProviderResolver()

    with pytest.raises(
        CapabilityProviderNotFoundError,
        match="No provider configured",
    ):
        resolver.resolve("video_download")


def test_resolver_rejects_empty_provider_identity():
    resolver = CapabilityProviderResolver()

    with pytest.raises(ValueError, match="provider id"):
        resolver.register(FakeProvider(" ", "video_download"))


def test_resolver_rejects_duplicate_provider_identity():
    resolver = CapabilityProviderResolver()
    provider = FakeProvider("provider-a", "video_download")

    resolver.register(provider)

    with pytest.raises(ValueError, match="already registered"):
        resolver.register(provider)


def test_resolver_rejects_invalid_provider():
    resolver = CapabilityProviderResolver()

    with pytest.raises(TypeError, match="CapabilityProvider"):
        resolver.register(InvalidProvider())
