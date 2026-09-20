from __future__ import annotations


class CapabilityIdentityResolver:
    """Read-only application boundary for known capability identities."""

    def __init__(self, capability_ids: set[str] | frozenset[str]) -> None:
        if any(not isinstance(value, str) or not value.strip() for value in capability_ids):
            raise ValueError("capability_ids must contain non-empty strings")

        self._capability_ids = frozenset(capability_ids)

    def contains(self, capability_id: str) -> bool:
        if not isinstance(capability_id, str):
            raise TypeError("capability_id must be a string")

        return capability_id in self._capability_ids
