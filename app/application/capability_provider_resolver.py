from __future__ import annotations

from app.application.capability import Capability
from app.application.capability_provider import CapabilityProvider
from app.application.capability_registry import (
    CapabilityNotFoundError,
    CapabilityRegistry,
)


class CapabilityProviderNotFoundError(Exception):
    pass


class _LegacyCapabilityProvider:
    """Compatibility adapter for capabilities registered before Phase 8.5."""

    def __init__(self, capability_id: str, capability: Capability) -> None:
        self.provider_id = "legacy-registry"
        self.capability_id = capability_id
        self._capability = capability

    def create(self) -> Capability:
        return self._capability


class CapabilityProviderResolver:
    """Resolve a configured provider for a stable capability identifier."""

    def __init__(
        self,
        *,
        legacy_registry: CapabilityRegistry | None = None,
    ) -> None:
        self._providers: dict[str, CapabilityProvider] = {}
        self._providers_by_capability: dict[str, set[str]] = {}
        self._defaults: dict[str, str] = {}
        self._legacy_registry = legacy_registry

    def register(
        self,
        provider: CapabilityProvider,
        *,
        as_default: bool = False,
    ) -> None:
        if not isinstance(provider, CapabilityProvider):
            raise TypeError(
                "Provider must implement the CapabilityProvider contract"
            )

        if not isinstance(provider.provider_id, str) or not provider.provider_id.strip():
            raise ValueError("Provider id cannot be empty")

        if not isinstance(provider.capability_id, str) or not provider.capability_id.strip():
            raise ValueError("Provider capability id cannot be empty")

        if provider.provider_id in self._providers:
            raise ValueError(
                f"Provider already registered: {provider.provider_id}"
            )

        self._providers[provider.provider_id] = provider
        self._providers_by_capability.setdefault(
            provider.capability_id,
            set(),
        ).add(provider.provider_id)

        if as_default:
            self.set_default(provider.capability_id, provider.provider_id)

    def set_default(self, capability_id: str, provider_id: str) -> None:
        if provider_id not in self._providers:
            raise CapabilityProviderNotFoundError(
                f"Provider not found: {provider_id}"
            )

        provider = self._providers[provider_id]
        if provider.capability_id != capability_id:
            raise ValueError(
                "Provider capability id does not match the requested capability id"
            )

        self._defaults[capability_id] = provider_id

    def resolve(self, capability_id: str) -> CapabilityProvider:
        provider_id = self._defaults.get(capability_id)

        if provider_id is not None:
            try:
                return self._providers[provider_id]
            except KeyError as exc:
                raise CapabilityProviderNotFoundError(
                    f"Default provider is unavailable: {provider_id}"
                ) from exc

        if capability_id in self._providers_by_capability:
            raise CapabilityProviderNotFoundError(
                f"No default provider configured for capability: {capability_id}"
            )

        if self._legacy_registry is not None:
            try:
                capability = self._legacy_registry.resolve(capability_id)
            except CapabilityNotFoundError:
                capability = None

            if capability is not None:
                return _LegacyCapabilityProvider(capability_id, capability)

        raise CapabilityProviderNotFoundError(
            f"No provider configured for capability: {capability_id}"
        )
