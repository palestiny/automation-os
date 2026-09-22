from __future__ import annotations

from uuid import UUID

from app.application.execution_context import ExecutionContext
from app.application.retry_execution import ManualRetryContext, RetryExecution
from app.application.start_retrying_execution import StartRetryingExecution
from app.application.workflow_execution_orchestration import ExecuteWorkflow
from app.domain.execution import Execution
from app.domain.repositories import ExecutionRepository


class RetryAndExecuteExecution:
    """Explicitly retry a failed Execution and run it through the workflow."""

    def __init__(
        self,
        retry_execution: RetryExecution,
        start_retrying_execution: StartRetryingExecution,
        execute_workflow: ExecuteWorkflow,
    ) -> None:
        self._retry_execution = retry_execution
        self._start_retrying_execution = start_retrying_execution
        self._execute_workflow = execute_workflow

    def execute(
        self,
        execution_id: UUID,
        *,
        manual_context: ManualRetryContext | None = None,
    ) -> Execution:
        execution = self._retry_execution.execute(
            execution_id,
            manual_context=manual_context,
        )
        execution = self._start_retrying_execution.execute(execution.id)
        return self._execute_workflow.execute(execution.id, ExecutionContext())
