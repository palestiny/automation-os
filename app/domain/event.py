from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Event:
    """Normalized application event used for trigger matching and context propagation."""

    event_type: str
    source: str = "internal"
    external_event_id: str | None = None
    payload: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.event_type.strip():
            raise ValueError("Event event_type cannot be empty")
        if not self.source.strip():
            raise ValueError("Event source cannot be empty")
        if self.external_event_id is not None and not self.external_event_id.strip():
            raise ValueError("Event external_event_id cannot be empty")

    @classmethod
    def create(
        cls,
        event_type: str,
        *,
        source: str = "internal",
        external_event_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> "Event":
        return cls(
            event_type=event_type,
            source=source,
            external_event_id=external_event_id,
            payload=dict(payload) if payload is not None else None,
        )
