from __future__ import annotations

from uuid import UUID

from app.domain.execution import Execution
from app.domain.repositories import ExecutionRepository, WorkflowRepository
from app.domain.workflow import Workflow


class InMemoryWorkflowRepository(WorkflowRepository):
    """In-memory adapter for Workflow persistence."""

    def __init__(self) -> None:
        self._items: dict[UUID, Workflow] = {}

    def save(self, workflow: Workflow) -> None:
        self._items[workflow.id] = workflow

    def get(self, workflow_id: UUID) -> Workflow | None:
        return self._items.get(workflow_id)


class InMemoryExecutionRepository(ExecutionRepository):
    """In-memory adapter for Execution persistence."""

    def __init__(self) -> None:
        self._items: dict[UUID, Execution] = {}

    def save(self, execution: Execution) -> None:
        self._items[execution.id] = execution

    def get(self, execution_id: UUID) -> Execution | None:
        return self._items.get(execution_id)
