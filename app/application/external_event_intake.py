from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Any

from app.domain.event import Event


@dataclass(frozen=True)
class ExternalEvent:
    source_id: str
    event_type: str
    payload: Mapping[str, Any]
    external_event_id: str | None = None
    idempotency_key: str | None = None

    def normalized_event(self) -> Event:
        if not self.source_id.strip():
            raise ValueError("External event source_id cannot be empty")
        if not self.event_type.strip():
            raise ValueError("External event event_type cannot be empty")
        if self.external_event_id is not None and not self.external_event_id.strip():
            raise ValueError("External event external_event_id cannot be empty")
        if self.idempotency_key is not None and not self.idempotency_key.strip():
            raise ValueError("External event idempotency_key cannot be empty")
        return Event.create(self.event_type)
