from __future__ import annotations

from uuid import UUID

from app.domain.execution import Execution
from app.domain.repositories import ExecutionRepository, WorkflowRepository
from app.domain.workflow import WorkflowState


class StartWorkflowExecution:
    """Application use case for starting a persisted published Workflow."""

    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        execution_repository: ExecutionRepository,
    ) -> None:
        self._workflow_repository = workflow_repository
        self._execution_repository = execution_repository

    def execute(self, workflow_id: UUID) -> Execution:
        workflow = self._workflow_repository.get(workflow_id)
        if workflow is None:
            raise ValueError(f"Workflow not found: {workflow_id}")

        if workflow.state != WorkflowState.PUBLISHED:
            raise ValueError("Only published workflows can be started")

        execution = Execution.create(workflow.id)
        self._execution_repository.save(execution)

        execution.start()
        self._execution_repository.save(execution)

        return execution
