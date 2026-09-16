from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence
from uuid import UUID, uuid4


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
        if not name.strip():
            raise ValueError("WorkflowStep name cannot be blank")

        if not capability.strip():
            raise ValueError("WorkflowStep capability cannot be blank")

        return cls(
            id=uuid4(),
            name=name,
            capability=capability,
        )


@dataclass
class Workflow:
    id: UUID
    name: str
    _steps: list[WorkflowStep]
    state: WorkflowState

    @classmethod
    def create(cls, name: str, steps: Sequence[WorkflowStep]) -> "Workflow":
        if not name.strip():
            raise ValueError("Workflow name cannot be blank")

        return cls(
            id=uuid4(),
            name=name,
            _steps=list(steps),
            state=WorkflowState.DRAFT,
        )

    @property
    def steps(self) -> list[WorkflowStep]:
        return list(self._steps)

    def publish(self) -> None:
        if self.state != WorkflowState.DRAFT:
            raise ValueError(
                "Workflow can only be published from DRAFT state"
            )

        if not self._steps:
            raise ValueError(
                "Workflow must have at least one step before publishing"
            )

        self.state = WorkflowState.PUBLISHED

    def add_step(self, step: WorkflowStep) -> None:
        if self.state != WorkflowState.DRAFT:
            raise ValueError(
                "Steps can only be added to a Workflow in DRAFT state"
            )

        self._steps.append(step)
