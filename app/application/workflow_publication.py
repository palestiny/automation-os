from __future__ import annotations

from app.domain.workflow import Workflow


class PublishWorkflow:
    """Explicit application boundary for publishing and persisting a DRAFT workflow."""

    def __init__(self, workflow_repository) -> None:
        if not hasattr(workflow_repository, "save"):
            raise TypeError("workflow_repository must provide a save(workflow) method")
        self._workflow_repository = workflow_repository

    def execute(self, workflow: Workflow) -> Workflow:
        if not isinstance(workflow, Workflow):
            raise TypeError("workflow must be a Workflow instance")

        workflow.publish()
        self._workflow_repository.save(workflow)
        return workflow
