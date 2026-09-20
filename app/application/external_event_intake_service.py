from __future__ import annotations

from app.application.external_event_intake import ExternalEvent
from app.application.trigger_invocation import TriggerInvocation
from app.domain.execution import Execution


class ExternalEventIntake:
    """Normalize validated external events and delegate only through trigger invocation."""

    def __init__(self, trigger_invocation: TriggerInvocation) -> None:
        self._trigger_invocation = trigger_invocation

    def intake(self, external_event: ExternalEvent) -> tuple[Execution, ...]:
        event = external_event.normalized_event()
        idempotency_key = self._idempotency_key(external_event)

        return self._trigger_invocation.invoke(
            event,
            idempotency_key=idempotency_key,
        )

    @staticmethod
    def _idempotency_key(external_event: ExternalEvent) -> str | None:
        if external_event.external_event_id is not None:
            return f"external:{external_event.source_id}:{external_event.external_event_id}"
        if external_event.idempotency_key is not None:
            return f"external-key:{external_event.source_id}:{external_event.idempotency_key}"
        return None
