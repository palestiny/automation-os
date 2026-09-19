from __future__ import annotations

from app.application.execution_context import ExecutionContext
from app.application.execute_workflow_step import ExecuteWorkflowStep
from app.domain.execution import Execution, ExecutionState
from app.domain.repositories import ExecutionRepository


class ExecuteWorkflow:
    """Drive a RUNNING Execution through its remaining workflow steps."""

    def __init__(
        self,
        execution_repository: ExecutionRepository,
        step_executor: ExecuteWorkflowStep,
    ) -> None:
        if not isinstance(step_executor, ExecuteWorkflowStep):
            raise TypeError("step_executor must be an ExecuteWorkflowStep instance")
        self._execution_repository = execution_repository
        self._step_executor = step_executor

    def execute(
        self,
        execution_id,
        context: ExecutionContext,
    ) -> Execution:
        execution = self._execution_repository.get(execution_id)
        if execution is None:
            raise ValueError(f"Execution not found: {execution_id}")

        if execution.state is not ExecutionState.RUNNING:
            raise ValueError("Execution must be RUNNING to execute workflow")

        if not isinstance(context, ExecutionContext):
            raise TypeError("context must be an ExecutionContext instance")

        while execution.state is ExecutionState.RUNNING:
            self._step_executor.execute(execution.id, context)

        return execution
