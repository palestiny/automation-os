from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domain.workflow import Workflow


class WorkflowResolver(Protocol):
    """Application port for resolving a Workflow by identity."""

    def get_by_id(self, workflow_id: UUID) -> Workflow | None:
        ...
