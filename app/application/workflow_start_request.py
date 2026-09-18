from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class WorkflowStartRequest:
    """Application request produced by a trigger to start a Workflow."""

    workflow_id: UUID
