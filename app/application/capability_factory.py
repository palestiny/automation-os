from __future__ import annotations

from collections.abc import Callable

from app.application.capability import Capability


class CapabilityFactory:
    """Construct configured capability instances at application composition time."""

    def __init__(
        self,
        builders: dict[str, Callable[[], Capability]],
    ) -> None:
        self._builders = dict(builders)

    def create(self, capability_id: str) -> Capability:
        try:
            builder = self._builders[capability_id]
        except KeyError as exc:
            raise ValueError(
                f"Capability implementation not configured: {capability_id}"
            ) from exc

        capability = builder()

        if not isinstance(capability, Capability):
            raise TypeError(
                "Capability factory builder must return a Capability"
            )

        return capability
