from __future__ import annotations

from uuid import UUID

from app.domain.execution import Execution
from app.domain.repositories import ExecutionRepository


class RetryExecution:
    """Move a persisted FAILED Execution to RETRYING through domain rules."""

    def __init__(self, execution_repository: ExecutionRepository) -> None:
        self._execution_repository = execution_repository

    def execute(self, execution_id: UUID) -> Execution:
        execution = self._execution_repository.get(execution_id)
        if execution is None:
            raise ValueError(f"Execution not found: {execution_id}")

        execution.retry()
        self._execution_repository.save(execution)

        return execution
