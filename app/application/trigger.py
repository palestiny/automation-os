from __future__ import annotations

from typing import Protocol

from app.application.workflow_start_request import WorkflowStartRequest


class Trigger(Protocol):
    """Boundary for mechanisms that request Workflow execution."""

    def create_start_request(self) -> WorkflowStartRequest:
        ...
