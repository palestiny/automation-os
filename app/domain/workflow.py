from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence
from uuid import UUID, uuid4

from app.domain.transition import Transition


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

        return cls(id=uuid4(), name=name, capability=capability)


@dataclass
class Workflow:
    _id: UUID
    _name: str
    _steps: list[WorkflowStep]
    _transitions: list[Transition]
    _state: WorkflowState

    @classmethod
    def create(cls, name: str, steps: Sequence[WorkflowStep]) -> "Workflow":
        if not name.strip():
            raise ValueError("Workflow name cannot be blank")
        return cls(_id=uuid4(), _name=name, _steps=list(steps), _transitions=[], _state=WorkflowState.DRAFT)

    @property
    def id(self) -> UUID: return self._id
    @property
    def name(self) -> str: return self._name
    @property
    def steps(self) -> list[WorkflowStep]: return list(self._steps)
    @property
    def transitions(self) -> list[Transition]: return list(self._transitions)
    @property
    def state(self) -> WorkflowState: return self._state

    def publish(self) -> None:
        if self._state != WorkflowState.DRAFT:
            raise ValueError("Workflow can only be published from DRAFT state")
        if not self._steps:
            raise ValueError("Workflow must have at least one step before publishing")
        self.validate_graph()
        self._state = WorkflowState.PUBLISHED

    def add_step(self, step: WorkflowStep) -> None:
        if self._state != WorkflowState.DRAFT:
            raise ValueError("Steps can only be added to a Workflow in DRAFT state")
        self._steps.append(step)

    def add_transition(self, transition: Transition) -> None:
        if self._state != WorkflowState.DRAFT:
            raise ValueError("Transitions can only be added to a Workflow in DRAFT state")
        step_ids = {step.id for step in self._steps}
        if transition.source_step_id not in step_ids or transition.target_step_id not in step_ids:
            raise ValueError("Transition must reference steps in the workflow")
        self._transitions.append(transition)

    def outgoing_transitions(self, step_id: UUID) -> list[Transition]:
        return [t for t in self._transitions if t.source_step_id == step_id]

    def validate_graph(self) -> None:
        if not self._steps:
            raise ValueError("Workflow must contain at least one step")
        step_ids = {step.id for step in self._steps}
        reachable = {self._steps[0].id}
        pending = [self._steps[0].id]
        transitions_by_source: dict[UUID, list[Transition]] = {step_id: [] for step_id in step_ids}
        for transition in self._transitions:
            transitions_by_source[transition.source_step_id].append(transition)
        while pending:
            current_step_id = pending.pop()
            for transition in transitions_by_source[current_step_id]:
                if transition.target_step_id not in reachable:
                    reachable.add(transition.target_step_id)
                    pending.append(transition.target_step_id)
        if step_ids - reachable:
            raise ValueError("Workflow contains unreachable steps")
