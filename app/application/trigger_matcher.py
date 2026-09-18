from __future__ import annotations

from uuid import UUID

from app.domain.event import Event
from app.domain.workflow import Workflow


class TriggerMatcher:
    """Resolve a Workflow from a normalized Event without starting execution."""

    def match(self, event: Event, workflow: Workflow) -> UUID | None:
        for trigger in workflow.triggers:
            if trigger.event_type == event.event_type:
                return workflow.id

        return None
