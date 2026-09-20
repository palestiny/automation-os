from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class Event:
    """Normalized application event used for trigger matching."""

    event_type: str
    payload: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.event_type, str) or not self.event_type.strip():
            raise ValueError("Event event_type cannot be empty")
        object.__setattr__(self, "payload", dict(self.payload))

    @classmethod
    def create(
        cls,
        event_type: str,
        payload: Mapping[str, object] | None = None,
    ) -> "Event":
        return cls(event_type=event_type, payload=payload or {})
