from __future__ import annotations

from app.application.scheduling import Clock, ScheduledExecutionRequest
from app.application.start_workflow_execution import StartWorkflowExecution
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
