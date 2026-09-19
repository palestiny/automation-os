from __future__ import annotations

from uuid import UUID

from app.application.execution_context import ExecutionContext
from app.application.resume_execution import ResumeExecution
from app.application.retry_execution import RetryExecution
from app.application.workflow_execution_orchestration import ExecuteWorkflow
from app.domain.execution import Execution
from app.domain.repositories import ExecutionRepository


class StartRetryingExecution:
    """Start a RETRYING Execution through the existing domain lifecycle."""

    def __init__(self, execution_repository: ExecutionRepository) -> None:
        self._execution_repository = execution_repository

    def execute(self, execution_id: UUID) -> Execution:
        execution = self._execution_repository.get(execution_id)
        if execution is None:
            raise ValueError(f"Execution not found: {execution_id}")

        execution.start()
        self._execution_repository.save(execution)
        return execution


class RetryAndExecuteExecution:
    """Explicitly retry a failed Execution and run it through the workflow."""

    def __init__(
        self,
        retry_execution: RetryExecution,
        execution_repository: ExecutionRepository,
        execute_workflow: ExecuteWorkflow,
    ) -> None:
        self._retry_execution = retry_execution
        self._execution_repository = execution_repository
        self._execute_workflow = execute_workflow

    def execute(self, execution_id: UUID) -> Execution:
        execution = self._retry_execution.execute(execution_id)
        execution = StartRetryingExecution(self._execution_repository).execute(execution.id)
        return self._execute_workflow.execute(execution.id, ExecutionContext())
