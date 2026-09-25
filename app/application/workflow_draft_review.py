from __future__ import annotations

from uuid import UUID

from app.domain.workflow import Workflow, WorkflowState


class GetDraftWorkflowForReview:
    """Retrieve one persisted DRAFT workflow for explicit review."""

    def __init__(self, workflow_repository) -> None:
        if not hasattr(workflow_repository, "get"):
            raise TypeError("workflow_repository must provide a get(workflow_id) method")
        self._workflow_repository = workflow_repository

    def execute(self, workflow_id: UUID) -> Workflow:
        if not isinstance(workflow_id, UUID):
            raise TypeError("workflow_id must be a UUID")

        workflow = self._workflow_repository.get(workflow_id)

        if workflow is None:
            raise LookupError("Workflow not found")

        if not isinstance(workflow, Workflow):
            raise TypeError("workflow repository returned an invalid Workflow")

        if workflow.state is not WorkflowState.DRAFT:
            raise ValueError("Workflow is not in DRAFT state")

        return workflow
