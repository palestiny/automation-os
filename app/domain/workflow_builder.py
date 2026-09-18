from __future__ import annotations

from app.domain.workflow import Workflow, WorkflowStep


class WorkflowBuilder:
    """Authoring convenience for constructing draft Workflow definitions."""

    def __init__(self, name: str) -> None:
        self._workflow = Workflow.create(name=name, steps=[])

    def add_step(self, name: str, capability: str) -> "WorkflowBuilder":
        self._workflow.add_step(
            WorkflowStep.create(name=name, capability=capability)
        )
        return self

    def build(self) -> Workflow:
        return self._workflow
