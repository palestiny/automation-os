from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.application.capability import Capability


@runtime_checkable
class CapabilityProvider(Protocol):
    """Application-level provider contract for a stable capability identity."""

    provider_id: str
    capability_id: str

    def create(self) -> Capability:
        ...
