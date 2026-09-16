from __future__ import annotations

from app.domain.workflow import Workflow, WorkflowStep


class WorkflowBuilder:
    def __init__(self) -> None:
        self._name: str | None = None
        self._steps: list[WorkflowStep] = []

    def name(self, name: str) -> "WorkflowBuilder":
        self._name = name
        return self

    def add_step(self, name: str, capability: str) -> "WorkflowBuilder":
        self._steps.append(
            WorkflowStep.create(
                name=name,
                capability=capability,
            )
        )
        return self

    def build(self) -> Workflow:
        if self._name is None:
            raise ValueError("Workflow name must be provided before build")

        if not self._steps:
            raise ValueError("Workflow must contain at least one step")

        return Workflow.create(
            name=self._name,
            steps=self._steps,
        )
