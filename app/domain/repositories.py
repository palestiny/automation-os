from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from app.domain.execution import Execution
from app.domain.workflow import Workflow


@runtime_checkable
class WorkflowRepository(Protocol):
    """Persistence boundary for Workflow aggregates."""

    def save(self, workflow: Workflow) -> None:
        ...

    def get(self, workflow_id: UUID) -> Workflow | None:
        ...

    def all(self) -> tuple[Workflow, ...]:
        ...


@runtime_checkable
class ExecutionRepository(Protocol):
    """Persistence boundary for Execution aggregates."""

    def save(self, execution: Execution) -> None:
        ...

    def get(self, execution_id: UUID) -> Execution | None:
        ...

    def all(self) -> tuple[Execution, ...]:
        ...
