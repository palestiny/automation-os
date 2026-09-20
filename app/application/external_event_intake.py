from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.application.trigger_invocation import TriggerInvocation
from app.domain.event import Event
from app.domain.execution import Execution


@dataclass(frozen=True)
class ExternalEvent:
    source: str
    event_type: str
    external_event_id: str | None = None
    payload: dict[str, Any] | None = None


@dataclass(frozen=True)
class ExternalEventIntakeResult:
    event: Event
    executions: tuple[Execution, ...]


class ExternalEventIntake:
    """Normalize validated external events and delegate them to trigger invocation."""

    def __init__(self, trigger_invocation: TriggerInvocation) -> None:
        self._trigger_invocation = trigger_invocation

    def receive(self, external_event: ExternalEvent) -> ExternalEventIntakeResult:
        if not external_event.source.strip():
            raise ValueError("External event source cannot be empty")
        if not external_event.event_type.strip():
            raise ValueError("External event event type cannot be empty")

        event = Event.create(
            external_event.event_type,
            source=external_event.source,
            external_event_id=external_event.external_event_id,
            payload=external_event.payload,
        )

        idempotency_key = None
        if event.external_event_id is not None:
            idempotency_key = (
                f"external-event:{event.source}:{event.external_event_id}"
            )

        executions = self._trigger_invocation.invoke(
            event,
            idempotency_key=idempotency_key,
        )
        return ExternalEventIntakeResult(event=event, executions=executions)
