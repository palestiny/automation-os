from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    """Normalized application event used for trigger matching."""

    event_type: str

    def __post_init__(self) -> None:
        if not self.event_type.strip():
            raise ValueError("Event event_type cannot be empty")

    @classmethod
    def create(cls, event_type: str) -> "Event":
        return cls(event_type=event_type)
