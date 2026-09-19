from __future__ import annotations

from app.application.scheduling import Clock, ScheduledExecutionRequest
from app.application.execution_context import ExecutionContext
from app.application.start_workflow_execution import StartWorkflowExecution
from app.application.workflow_execution_orchestration import ExecuteWorkflow
from app.domain.execution import Execution


class StartDueWorkflowExecution:
    """Starts a workflow only when its scheduled execution request is due."""

    def __init__(
        self,
        start_workflow_execution: StartWorkflowExecution,
        clock: Clock,
    ) -> None:
        self._start_workflow_execution = start_workflow_execution
        self._clock = clock

    def execute(
        self,
        request: ScheduledExecutionRequest,
    ) -> Execution | None:
        if self._clock.now() < request.scheduled_at:
            return None

        return self._start_workflow_execution.execute(request.workflow_id)


class ExecuteDueWorkflow:
    """Start and synchronously execute a workflow when its schedule is due."""

    def __init__(
        self,
        start_due_workflow_execution: StartDueWorkflowExecution,
        execute_workflow: ExecuteWorkflow,
    ) -> None:
        self._start_due = start_due_workflow_execution
        self._execute_workflow = execute_workflow

    def execute(
        self,
        request: ScheduledExecutionRequest,
    ) -> Execution | None:
        execution = self._start_due.execute(request)
        if execution is None:
            return None

        return self._execute_workflow.execute(
            execution.id,
            ExecutionContext(),
        )
