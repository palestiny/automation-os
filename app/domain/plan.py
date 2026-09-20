from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID, uuid4


class PlanOutcome(Enum):
    PLANNED = "planned"
    NEEDS_CLARIFICATION = "needs_clarification"
    REJECTED = "rejected"


@dataclass(frozen=True)
class PlannedStep:
    name: str
    capability: str


@dataclass(frozen=True)
class PlanProposal:
    id: UUID
    goal: str
    steps: tuple[PlannedStep, ...]
    required_parameters: tuple[str, ...] = ()

    @classmethod
    def create(
        cls,
        goal: str,
        steps: tuple[PlannedStep, ...],
        required_parameters: tuple[str, ...] = (),
    ) -> "PlanProposal":
        return cls(
            id=uuid4(),
            goal=goal,
            steps=steps,
            required_parameters=required_parameters,
        )


@dataclass(frozen=True)
class PlanResult:
    outcome: PlanOutcome
    proposal: PlanProposal | None = None
    reason: str | None = None

    @classmethod
    def planned(cls, proposal: PlanProposal) -> "PlanResult":
        return cls(PlanOutcome.PLANNED, proposal)

    @classmethod
    def needs_clarification(cls, reason: str) -> "PlanResult":
        return cls(PlanOutcome.NEEDS_CLARIFICATION, reason=reason)

    @classmethod
    def rejected(cls, reason: str) -> "PlanResult":
        return cls(PlanOutcome.REJECTED, reason=reason)
