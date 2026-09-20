from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol
from uuid import UUID

from app.domain.intent import Intent
from app.domain.workflow import WorkflowParameter, WorkflowState
from app.domain.workflow_version import WorkflowVersion


class PlanOutcome(Enum):
    PLANNED = "planned"
    CLARIFICATION_REQUIRED = "clarification_required"
    NO_PLAN = "no_plan"
    PLANNER_FAILED = "planner_failed"


@dataclass(frozen=True)
class PlannerInput:
    intent: Intent
    workflow_versions: tuple[WorkflowVersion, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.intent, Intent):
            raise TypeError("intent must be an Intent")
        if any(not isinstance(v, WorkflowVersion) for v in self.workflow_versions):
            raise TypeError("workflow_versions must contain WorkflowVersion instances")


@dataclass(frozen=True)
class PlanProposal:
    workflow_version_id: UUID
    parameters: dict[str, object]


@dataclass(frozen=True)
class PlanResult:
    outcome: PlanOutcome
    workflow_version_id: UUID | None = None
    parameters: dict[str, object] | None = None
    missing_parameters: tuple[str, ...] = ()
    reason: str | None = None


class PlannerPort(Protocol):
    def propose(self, planner_input: PlannerInput) -> PlanProposal | None:
        ...


class DeterministicPlanValidator:
    def validate(
        self,
        proposal: PlanProposal | None,
        planner_input: PlannerInput,
    ) -> PlanResult:
        if proposal is None:
            return PlanResult(PlanOutcome.NO_PLAN, reason="Planner returned no plan")

        version = next(
            (v for v in planner_input.workflow_versions if v.id == proposal.workflow_version_id),
            None,
        )
        if version is None:
            return PlanResult(PlanOutcome.NO_PLAN, reason="Workflow version was not found")

        if version.state is not WorkflowState.PUBLISHED:
            return PlanResult(
                PlanOutcome.NO_PLAN,
                reason="Only published workflow versions can be planned",
            )

        required = set(version.required_parameters)
        provided = set(proposal.parameters)
        missing = tuple(sorted(required - provided))
        if missing:
            return PlanResult(
                PlanOutcome.CLARIFICATION_REQUIRED,
                workflow_version_id=version.id,
                parameters=dict(proposal.parameters),
                missing_parameters=missing,
                reason="Required planning parameters are missing",
            )

        parameter_types = {p.name: p.type for p in version.parameter_types}
        for name, value in proposal.parameters.items():
            if name not in required:
                return PlanResult(
                    PlanOutcome.NO_PLAN,
                    reason=f"Unknown workflow parameter: {name}",
                )
            if not self._matches(parameter_types.get(name), value):
                return PlanResult(
                    PlanOutcome.NO_PLAN,
                    reason=f"Invalid parameter type for: {name}",
                )

        return PlanResult(
            PlanOutcome.PLANNED,
            workflow_version_id=version.id,
            parameters=dict(proposal.parameters),
        )

    @staticmethod
    def _matches(parameter_type: str | None, value: object) -> bool:
        if parameter_type is None:
            return True
        if parameter_type == "string":
            return isinstance(value, str)
        if parameter_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if parameter_type == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        if parameter_type == "boolean":
            return isinstance(value, bool)
        return False


class AIPlanner:
    """Plan with a replaceable provider, then enforce deterministic validation."""

    def __init__(self, planner_port: PlannerPort) -> None:
        self._planner_port = planner_port
        self._validator = DeterministicPlanValidator()

    def plan(self, planner_input: PlannerInput) -> PlanResult:
        try:
            proposal = self._planner_port.propose(planner_input)
        except Exception as exc:
            return PlanResult(
                PlanOutcome.PLANNER_FAILED,
                reason=str(exc),
            )
        return self._validator.validate(proposal, planner_input)
