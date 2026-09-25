from __future__ import annotations

from app.domain.repositories import WorkflowRepository
from app.domain.workflow import Workflow


class PersistWorkflow:
    """Explicit application boundary for persisting a Workflow aggregate."""

    def __init__(self, workflow_repository: WorkflowRepository) -> None:
        if not hasattr(workflow_repository, "save"):
            raise TypeError("workflow_repository must provide a save(workflow) method")
        self._workflow_repository = workflow_repository

    def execute(self, workflow: Workflow) -> Workflow:
        if not isinstance(workflow, Workflow):
            raise TypeError("workflow must be a Workflow instance")

        self._workflow_repository.save(workflow)
        return workflow
