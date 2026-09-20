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


from app.application.trigger_invocation import TriggerInvocation
from app.domain.execution import Execution


class ExternalEventIntake:
    """Application boundary for transport-neutral external event ingestion."""

    def __init__(self, trigger_invocation: TriggerInvocation) -> None:
        self._trigger_invocation = trigger_invocation

    def intake(self, external_event: ExternalEvent) -> tuple[Execution, ...]:
        event = external_event.normalized_event()
        dedupe_key = self._dedupe_key(external_event)

        return self._trigger_invocation.invoke(
            event,
            idempotency_key=dedupe_key,
        )

    @staticmethod
    def _dedupe_key(external_event: ExternalEvent) -> str | None:
        if external_event.external_event_id is not None:
            return (
                f"external-event:{external_event.source_id}:"
                f"{external_event.external_event_id}"
            )

        if external_event.idempotency_key is not None:
            return (
                f"external-request:{external_event.source_id}:"
                f"{external_event.idempotency_key}"
            )

        return None
