from __future__ import annotations

from app.domain.workflow import Workflow


class PublishWorkflow:
    """Explicit application boundary for publishing a DRAFT workflow."""

    def execute(self, workflow: Workflow) -> Workflow:
        if not isinstance(workflow, Workflow):
            raise TypeError("workflow must be a Workflow instance")

        workflow.publish()
        return workflow
