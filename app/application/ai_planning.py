from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable
from uuid import UUID

from app.domain.intent import Intent
from app.domain.workflow import WorkflowParameter
from app.domain.workflow_version import WorkflowVersion


class PlanStatus(Enum):
    PLANNED = "planned"
    CLARIFICATION_REQUIRED = "clarification_required"
    NO_PLAN = "no_plan"
    PLANNER_FAILED = "planner_failed"


@dataclass(frozen=True)
class PlanProposal:
    workflow_id: UUID
    workflow_version_id: UUID
    parameters: dict[str, object]

    @classmethod
    def create(
        cls,
        workflow_id: UUID,
        workflow_version_id: UUID,
        parameters: dict[str, object] | None = None,
    ) -> "PlanProposal":
        return cls(
            workflow_id=workflow_id,
            workflow_version_id=workflow_version_id,
            parameters=dict(parameters or {}),
        )


@dataclass(frozen=True)
class PlanOutcome:
    status: PlanStatus
    workflow_id: UUID | None = None
    workflow_version_id: UUID | None = None
    parameters: dict[str, object] | None = None
    missing_parameters: tuple[str, ...] = ()
    message: str | None = None


@runtime_checkable
class PlannerPort(Protocol):
    def plan(self, intent: Intent) -> PlanProposal | None:
        ...


class AIPlanner:
    """Validate an AI proposal against deterministic published-version rules."""

    def __init__(self, fake_provider: PlannerPort):
        self._provider = fake_provider

    @staticmethod
    def _matches_type(value: object, parameter: WorkflowParameter) -> bool:
        if parameter.type == "string":
            return isinstance(value, str)
        if parameter.type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if parameter.type == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        if parameter.type == "boolean":
            return isinstance(value, bool)
        return False

    def plan(
        self,
        intent: Intent,
        published_versions: list[WorkflowVersion],
    ) -> PlanOutcome:
        try:
            proposal = self._provider.plan(intent)
        except Exception as exc:
            return PlanOutcome(
                status=PlanStatus.PLANNER_FAILED,
                message=str(exc),
            )

        if proposal is None:
            return PlanOutcome(status=PlanStatus.NO_PLAN)

        version = next(
            (
                candidate
                for candidate in published_versions
                if candidate.id == proposal.workflow_version_id
            ),
            None,
        )
        if version is None or version.state.value != "published":
            return PlanOutcome(status=PlanStatus.NO_PLAN)

        if version.workflow_id != proposal.workflow_id:
            return PlanOutcome(status=PlanStatus.NO_PLAN)

        missing = tuple(
            parameter
            for parameter in version.required_parameters
            if parameter not in proposal.parameters
        )
        if missing:
            return PlanOutcome(
                status=PlanStatus.CLARIFICATION_REQUIRED,
                workflow_id=version.workflow_id,
                workflow_version_id=version.id,
                missing_parameters=missing,
            )

        parameter_types = {parameter.name: parameter for parameter in version.parameter_types}
        if any(
            name in parameter_types
            and not self._matches_type(value, parameter_types[name])
            for name, value in proposal.parameters.items()
        ):
            return PlanOutcome(status=PlanStatus.NO_PLAN)

        return PlanOutcome(
            status=PlanStatus.PLANNED,
            workflow_id=version.workflow_id,
            workflow_version_id=version.id,
            parameters=dict(proposal.parameters),
        )
