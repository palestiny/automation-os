from __future__ import annotations

from uuid import UUID

from app.domain.execution import Execution, ExecutionState
from app.domain.repositories import ExecutionRepository


class StartRetryingExecution:
    """Start a RETRYING Execution through the existing domain lifecycle."""

    def __init__(self, execution_repository: ExecutionRepository) -> None:
        self._execution_repository = execution_repository

    def execute(self, execution_id: UUID) -> Execution:
        execution = self._execution_repository.get(execution_id)
        if execution is None:
            raise ValueError(f"Execution not found: {execution_id}")

        if execution.state is not ExecutionState.RETRYING:
            raise ValueError("Execution can only be started from RETRYING state")

        execution.start()
        self._execution_repository.save(execution)
        return execution
