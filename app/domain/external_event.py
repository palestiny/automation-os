from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.domain.event import Event


@dataclass(frozen=True)
class ExternalEvent:
    """Normalized external event before trigger invocation."""

    source: str
    event_type: str
    payload: Mapping[str, object]
    event_id: str | None = None

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("External event source cannot be empty")
        if not self.event_type.strip():
            raise ValueError("External event event_type cannot be empty")
        if self.event_id is not None and not self.event_id.strip():
            raise ValueError("External event id cannot be empty")

    def to_event(self) -> Event:
        return Event.create(self.event_type)

    @property
    def deduplication_key(self) -> str | None:
        if self.event_id is None:
            return None
        return f"external:{self.source}:{self.event_id}"
