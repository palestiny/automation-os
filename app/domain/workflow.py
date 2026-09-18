from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID, uuid4


class WorkflowState(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


@dataclass(frozen=True)
class WorkflowStep:
    id: UUID
    name: str
    capability: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("WorkflowStep name cannot be empty")
        if not self.capability.strip():
            raise ValueError("WorkflowStep capability cannot be empty")

    @classmethod
    def create(cls, name: str, capability: str) -> "WorkflowStep":
        return cls(id=uuid4(), name=name, capability=capability)


@dataclass
class Workflow:
    id: UUID
    name: str
    _steps: list[WorkflowStep]
    state: WorkflowState

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Workflow name cannot be empty")
        if any(not isinstance(step, WorkflowStep) for step in self._steps):
            raise ValueError("Workflow steps must be WorkflowStep instances")

    @property
    def steps(self) -> tuple[WorkflowStep, ...]:
        return tuple(self._steps)

    @classmethod
    def create(
        cls, name: str, steps: list[WorkflowStep]
    ) -> "Workflow":
        return cls(
            id=uuid4(),
            name=name,
            _steps=list(steps),
            state=WorkflowState.DRAFT,
        )

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
