from __future__ import annotations

from uuid import UUID

from app.application.execution_context import ExecutionContext
from app.application.execute_workflow_step import ExecuteWorkflowStep
from app.application.resume_execution import ResumeExecution
from app.application.workflow_execution_orchestration import ExecuteWorkflow
from app.domain.execution import Execution


class ResumeAndExecuteExecution:
    """Resume a waiting Execution and continue it through workflow orchestration."""

    def __init__(
        self,
        resume_execution: ResumeExecution,
        execute_workflow: ExecuteWorkflow,
    ) -> None:
        if not isinstance(resume_execution, ResumeExecution):
            raise TypeError("resume_execution must be a ResumeExecution instance")
        if not isinstance(execute_workflow, ExecuteWorkflow):
            raise TypeError("execute_workflow must be an ExecuteWorkflow instance")
        self._resume_execution = resume_execution
        self._execute_workflow = execute_workflow

    def execute(self, execution_id: UUID) -> Execution:
        execution = self._resume_execution.execute(execution_id)
        return self._execute_workflow.execute(
            execution.id,
            ExecutionContext(),
        )
