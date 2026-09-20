import pytest

from app.application.capability_identity_resolver import CapabilityIdentityResolver


def test_capability_identity_resolver_exposes_read_only_identity_lookup():
    resolver = CapabilityIdentityResolver(
        {"content.acquire", "content.transcribe"}
    )

    assert resolver.contains("content.acquire")
    assert not resolver.contains("content.publish")


def test_capability_identity_resolver_does_not_require_provider_resolution():
    resolver = CapabilityIdentityResolver({"content.acquire"})

    assert resolver.contains("content.acquire")


def test_capability_identity_resolver_rejects_non_string_identity():
    resolver = CapabilityIdentityResolver({"content.acquire"})

    with pytest.raises(TypeError):
        resolver.contains(123)
