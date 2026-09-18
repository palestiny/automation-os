from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domain.execution import Execution
from app.domain.workflow import Workflow


class WorkflowRepository(Protocol):
    """Persistence boundary for Workflow aggregates."""

    def save(self, workflow: Workflow) -> None:
        ...

    def get(self, workflow_id: UUID) -> Workflow | None:
        ...


class ExecutionRepository(Protocol):
    """Persistence boundary for Execution aggregates."""

    def save(self, execution: Execution) -> None:
        ...

    def get(self, execution_id: UUID) -> Execution | None:
        ...
