from __future__ import annotations

from uuid import UUID

from app.application.execution_progress import ExecutionProgress, GetExecutionProgress
from app.domain.execution import ExecutionState
from app.domain.repositories import ExecutionRepository


class DiscoverExecutions:
    """Read-only collection projection over persisted executions."""

    def __init__(self, execution_repository: ExecutionRepository) -> None:
        self._repository = execution_repository
        self._progress = GetExecutionProgress(execution_repository)

    def execute(
        self,
        workflow_id: UUID | None = None,
        state: ExecutionState | None = None,
    ) -> tuple[ExecutionProgress, ...]:
        executions = self._repository.all()

        if workflow_id is not None:
            executions = tuple(
                execution for execution in executions
                if execution.workflow_id == workflow_id
            )

        if state is not None:
            executions = tuple(
                execution for execution in executions
                if execution.state == state
            )

        return tuple(
            self._progress.execute(execution.id)
            for execution in executions
        )
