from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4
from enum import Enum

class WorkflowState(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"

@dataclass(frozen=True)
class WorkflowStep:
    id: UUID
    name: str
    capability: str

    @classmethod
    def create(cls, name: str, capability: str) -> "WorkflowStep":
        return cls(
            id=uuid4(),
            name=name,
            capability=capability,
        )

@dataclass
class Workflow:
    id: UUID
    name: str
    steps: list
    state: WorkflowState

    @classmethod
    def create(cls, name: str, steps: list) -> "Workflow":
        return cls(
            id=uuid4(),
            name=name,
            steps=steps,
            state=WorkflowState.DRAFT,
        )
    def publish(self) -> None:
        if self.state != WorkflowState.DRAFT:
            raise ValueError(
                "Workflow can only be published from DRAFT state"
            )

        if not self.steps:
            raise ValueError(
                "Workflow must have at least one step before publishing"
            )

        self.state = WorkflowState.PUBLISHED

    def add_step(self, step: WorkflowStep) -> None:
        if self.state != WorkflowState.DRAFT:
            raise ValueError(
                "Steps can only be added to a Workflow in DRAFT state"
            )

        self.steps.append(step)