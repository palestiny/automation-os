from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.execution import ExecutionState


@dataclass(frozen=True)
class ExecutionEvent:
    """Immutable evidence of an execution lifecycle transition."""

    execution_id: UUID
    workflow_id: UUID
    sequence: int
    event_type: str
    state: ExecutionState
    attempt: int
    occurred_at: datetime

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise ValueError("Execution event sequence must be at least 1")
        if not self.event_type.strip():
            raise ValueError("Execution event type cannot be empty")
