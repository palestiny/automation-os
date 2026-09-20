from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from app.application.trigger_invocation import TriggerInvocation
from app.domain.event import Event
from app.domain.execution import Execution


@dataclass(frozen=True)
class ExternalEvent:
    source_id: str
    event_type: str
    event_id: str | None = None
    payload: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("External event source_id cannot be empty")
        if not isinstance(self.event_type, str) or not self.event_type.strip():
            raise ValueError("External event event_type cannot be empty")
        if self.event_id is not None and (
            not isinstance(self.event_id, str) or not self.event_id.strip()
        ):
            raise ValueError("External event event_id cannot be empty when supplied")
        object.__setattr__(self, "payload", dict(self.payload))


@dataclass(frozen=True)
class ExternalEventResult:
    executions: tuple[Execution, ...]


class ExternalEventIntake:
    """Normalize trusted external events and delegate only to trigger invocation."""

    def __init__(self, trigger_invocation: TriggerInvocation) -> None:
        self._trigger_invocation = trigger_invocation

    def ingest(self, external_event: ExternalEvent) -> ExternalEventResult:
        event = Event.create(
            external_event.event_type,
            external_event.payload,
        )

        prefix = None
        if external_event.event_id is not None:
            prefix = (
                f"external:{external_event.source_id}:"
                f"{external_event.event_id}"
            )

        executions = self._trigger_invocation.invoke(
            event,
            idempotency_key_prefix=prefix,
        )
        return ExternalEventResult(executions=executions)
