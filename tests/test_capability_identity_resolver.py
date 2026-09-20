import pytest

from app.application.capability_identity_resolver import (
    CapabilityIdentityResolver,
)


class FakeCapabilityIdentityResolver:
    def __init__(self, capability_ids: set[str]):
        self._capability_ids = frozenset(capability_ids)

    def contains(self, capability_id: str) -> bool:
        return capability_id in self._capability_ids


def test_capability_identity_resolver_exposes_read_only_identity_lookup():
    resolver: CapabilityIdentityResolver = FakeCapabilityIdentityResolver(
        {"content.acquire", "content.transcribe"}
    )

    assert resolver.contains("content.acquire")
    assert not resolver.contains("content.publish")


def test_capability_identity_resolver_does_not_require_provider_resolution():
    resolver: CapabilityIdentityResolver = FakeCapabilityIdentityResolver(
        {"content.acquire"}
    )

    assert resolver.contains("content.acquire")


def test_capability_identity_resolver_rejects_non_string_identity():
    resolver: CapabilityIdentityResolver = FakeCapabilityIdentityResolver(
        {"content.acquire"}
    )

    with pytest.raises(TypeError):
        resolver.contains(123)
