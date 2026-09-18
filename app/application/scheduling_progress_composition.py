from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.application.execution_progress import ExecutionProgress, GetExecutionProgress
from app.application.scheduled_workflow_execution import StartDueWorkflowExecution
from app.application.scheduling import Clock, ScheduledExecutionRequest
from app.application.start_workflow_execution import StartWorkflowExecution
from app.domain.execution import Execution
from app.domain.repositories import ExecutionRepository, WorkflowRepository


class SchedulingProgressComposition:
    """Composes scheduling and progress over the existing execution runtime."""

    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        execution_repository: ExecutionRepository,
        clock: Clock,
    ) -> None:
        starter = StartWorkflowExecution(
            workflow_repository,
            execution_repository,
        )
        self._start_due = StartDueWorkflowExecution(starter, clock)
        self._get_progress = GetExecutionProgress(execution_repository)

    def schedule(
        self,
        workflow_id: UUID,
        scheduled_at: datetime,
    ) -> ScheduledExecutionRequest:
        return ScheduledExecutionRequest.create(workflow_id, scheduled_at)

    def start_if_due(
        self,
        request: ScheduledExecutionRequest,
    ) -> Execution | None:
        return self._start_due.execute(request)

    def get_progress(self, execution_id: UUID) -> ExecutionProgress:
        return self._get_progress.execute(execution_id)
