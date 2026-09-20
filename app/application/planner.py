from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable
from uuid import UUID


class PlanningOutcome(Enum):
    PLANNED = "planned"
    CLARIFICATION_REQUIRED = "clarification_required"
    NO_PLAN = "no_plan"
    PLANNER_FAILED = "planner_failed"


@dataclass(frozen=True)
class PlanningRequest:
    intent: str
    context: dict[str, object]

    def __post_init__(self) -> None:
        if not self.intent.strip():
            raise ValueError("Planning intent cannot be empty")


@dataclass(frozen=True)
class PlanProposal:
    outcome: PlanningOutcome
    workflow_version_id: UUID | None = None
    parameters: tuple[tuple[str, object], ...] = ()
    clarification_questions: tuple[str, ...] = ()
    reason: str | None = None


@dataclass(frozen=True)
class ValidatedPlan:
    workflow_version_id: UUID
    parameters: tuple[tuple[str, object], ...]


@runtime_checkable
class PlannerPort(Protocol):
    def plan(self, request: PlanningRequest) -> PlanProposal:
        ...
