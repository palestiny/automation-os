from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Protocol, runtime_checkable
from uuid import UUID

from app.domain.intent import Intent
from app.domain.repositories import WorkflowRepository, WorkflowVersionRepository
from app.domain.workflow import WorkflowState
from app.domain.workflow_version import WorkflowVersion


class PlanningStatus(Enum):
    PLANNED = "planned"
    CLARIFICATION_REQUIRED = "clarification_required"
    NO_PLAN = "no_plan"
    PLANNER_FAILED = "planner_failed"


@dataclass(frozen=True)
class PlanningRequest:
    intent: Intent


@dataclass(frozen=True)
class PlanProposal:
    status: PlanningStatus
    workflow_version_id: UUID | None = None
    parameters: Mapping[str, object] = field(default_factory=dict)
    details: tuple[str, ...] = ()

    @classmethod
    def planned(
        cls,
        *,
        workflow_version_id: UUID,
        parameters: Mapping[str, object],
    ) -> "PlanProposal":
        return cls(
            status=PlanningStatus.PLANNED,
            workflow_version_id=workflow_version_id,
            parameters=dict(parameters),
        )

    @classmethod
    def clarification_required(
        cls,
        *,
        details: tuple[str, ...],
    ) -> "PlanProposal":
        return cls(
            status=PlanningStatus.CLARIFICATION_REQUIRED,
            details=details,
        )

    @classmethod
    def no_plan(cls, *, reason: str) -> "PlanProposal":
        return cls(
            status=PlanningStatus.NO_PLAN,
            details=(reason,),
        )


@runtime_checkable
class PlannerPort(Protocol):
    """Provider-neutral boundary for proposing an executable plan."""

    def plan(self, request: PlanningRequest) -> PlanProposal:
        ...


@dataclass(frozen=True)
class PlanningResult:
    status: PlanningStatus
    workflow_version_id: UUID | None = None
    parameters: Mapping[str, object] = ()
    details: tuple[str, ...] = ()


class CreatePlan:
    """Create a validated plan without starting workflow execution."""

    def __init__(
        self,
        *,
        workflow_repository: WorkflowRepository,
        workflow_version_repository: WorkflowVersionRepository,
        planner: PlannerPort,
    ) -> None:
        self._workflow_repository = workflow_repository
        self._workflow_version_repository = workflow_version_repository
        self._planner = planner

    def execute(self, intent: Intent) -> PlanningResult:
        try:
            proposal = self._planner.plan(PlanningRequest(intent=intent))
        except Exception as exc:
            return PlanningResult(
                status=PlanningStatus.PLANNER_FAILED,
                details=(str(exc) or exc.__class__.__name__,),
            )

        if proposal.status is not PlanningStatus.PLANNED:
            return PlanningResult(
                status=proposal.status,
                workflow_version_id=proposal.workflow_version_id,
                parameters=proposal.parameters,
                details=proposal.details,
            )

        if proposal.workflow_version_id is None:
            raise ValueError("Planned proposal requires a workflow version")

        version = self._workflow_version_repository.get(
            proposal.workflow_version_id
        )
        if version is None:
            raise ValueError("Workflow version not found")

        if version.state is not WorkflowState.PUBLISHED:
            raise ValueError("Only published workflow versions can be planned")

        if self._workflow_repository.get(version.workflow_id) is None:
            raise ValueError("Workflow version belongs to a missing workflow")

        if intent.goal not in version.supported_goals:
            raise ValueError("Workflow version does not support the requested goal")

        parameters = dict(proposal.parameters)
        self._validate_parameters(version, parameters)

        return PlanningResult(
            status=PlanningStatus.PLANNED,
            workflow_version_id=version.id,
            parameters=parameters,
        )

    @staticmethod
    def _matches_type(value: object, parameter_type: str) -> bool:
        if parameter_type == "string":
            return isinstance(value, str)
        if parameter_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if parameter_type == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        if parameter_type == "boolean":
            return isinstance(value, bool)
        return False

    @classmethod
    def _validate_parameters(
        cls,
        version: WorkflowVersion,
        parameters: Mapping[str, object],
    ) -> None:
        missing = tuple(
            name
            for name in version.required_parameters
            if name not in parameters
        )
        if missing:
            raise ValueError(
                "Missing required parameters: " + ", ".join(missing)
            )

        invalid = tuple(
            parameter.name
            for parameter in version.parameter_types
            if parameter.name in parameters
            and not cls._matches_type(
                parameters[parameter.name],
                parameter.type,
            )
        )
        if invalid:
            raise ValueError(
                "Invalid parameter types: " + ", ".join(invalid)
            )
