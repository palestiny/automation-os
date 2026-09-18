from __future__ import annotations

from app.application.orchestrator import Orchestrator
from app.application.workflow_resolver import WorkflowResolver
from app.application.workflow_start_request import WorkflowStartRequest
from app.domain.execution import Execution


class WorkflowStartService:
    """Resolve a requested Workflow and delegate runtime startup to Orchestrator."""

    def __init__(
        self,
        workflow_resolver: WorkflowResolver,
        orchestrator: Orchestrator,
    ) -> None:
        self._workflow_resolver = workflow_resolver
        self._orchestrator = orchestrator

    def start(self, request: WorkflowStartRequest) -> Execution:
        workflow = self._workflow_resolver.get_by_id(request.workflow_id)
        if workflow is None:
            raise ValueError("Workflow was not found")

        return self._orchestrator.start(workflow)
