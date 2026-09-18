from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.execution import Execution, ExecutionState
from app.domain.repositories import ExecutionRepository


@dataclass(frozen=True)
class ExecutionProgress:
    execution_id: UUID
    workflow_id: UUID
    current_step: int
    state: ExecutionState
    attempt: int
    started_at: datetime | None
    finished_at: datetime | None


class ExecutionProgressNotFoundError(Exception):
    """Raised when progress is requested for an unknown execution."""


class GetExecutionProgress:
    """Projects persisted Execution state into a read-only progress model."""

    def __init__(self, execution_repository: ExecutionRepository) -> None:
        self._execution_repository = execution_repository

    def execute(self, execution_id: UUID) -> ExecutionProgress:
        execution = self._execution_repository.get(execution_id)
        if execution is None:
            raise ExecutionProgressNotFoundError(
                f"Execution not found: {execution_id}"
            )

        return ExecutionProgress(
            execution_id=execution.id,
            workflow_id=execution.workflow_id,
            current_step=execution.current_step,
            state=execution.state,
            attempt=execution.attempt,
            started_at=execution.started_at,
            finished_at=execution.finished_at,
        )
