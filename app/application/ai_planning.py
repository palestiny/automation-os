from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable
from uuid import UUID

from app.domain.intent import Intent
from app.domain.workflow import WorkflowParameter, WorkflowState
from app.domain.workflow_version import WorkflowVersion


class PlanningStatus(Enum):
    PLANNED = "planned"
    CLARIFICATION_REQUIRED = "clarification_required"
    NO_PLAN = "no_plan"
    PLANNER_FAILED = "planner_failed"


@dataclass(frozen=True)
class PlanningCandidate:
    workflow_version_id: UUID
    name: str
    supported_goals: tuple[str, ...]
    required_parameters: tuple[str, ...]
    parameter_types: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class PlanningRequest:
    intent: Intent
    candidates: tuple[PlanningCandidate, ...] = ()


@dataclass(frozen=True)
class PlanProposal:
    status: PlanningStatus
    workflow_version_id: UUID | None = None
    parameters: dict[str, object] | None = None
    details: tuple[str, ...] = ()

    @classmethod
    def planned(cls, workflow_version_id: UUID, parameters: dict[str, object]) -> "PlanProposal":
        return cls(PlanningStatus.PLANNED, workflow_version_id, dict(parameters))

    @classmethod
    def clarification_required(cls, details: tuple[str, ...]) -> "PlanProposal":
        return cls(PlanningStatus.CLARIFICATION_REQUIRED, details=tuple(details))

    @classmethod
    def no_plan(cls, reason: str) -> "PlanProposal":
        return cls(PlanningStatus.NO_PLAN, details=(reason,))


@dataclass(frozen=True)
class PlanOutcome:
    status: PlanningStatus
    workflow_id: UUID | None = None
    workflow_version_id: UUID | None = None
    parameters: dict[str, object] | None = None
    missing_parameters: tuple[str, ...] = ()
    details: tuple[str, ...] = ()


@runtime_checkable
class PlannerPort(Protocol):
    def plan(self, request: PlanningRequest) -> PlanProposal:
        ...


class DeterministicPlanValidator:
    """Validate provider output against existing published WorkflowVersion artifacts."""

    def validate(
        self,
        proposal: PlanProposal,
        request: PlanningRequest,
        versions: tuple[WorkflowVersion, ...],
    ) -> PlanOutcome:
        if proposal.status is not PlanningStatus.PLANNED:
            return PlanOutcome(
                status=proposal.status,
                details=proposal.details,
            )

        if proposal.workflow_version_id is None:
            return PlanOutcome(
                PlanningStatus.NO_PLAN,
                details=("Planned result has no workflow version",),
            )

        version = next(
            (candidate for candidate in versions if candidate.id == proposal.workflow_version_id),
            None,
        )
        if version is None:
            raise ValueError("Workflow version not found")

        if version.state is not WorkflowState.PUBLISHED:
            raise ValueError("Only published workflow versions can be planned")

        if request.intent.goal not in version.supported_goals:
            raise ValueError("Selected workflow version does not support the requested goal")

        parameters = dict(proposal.parameters or {})
        missing = tuple(
            name for name in version.required_parameters if name not in parameters
        )
        if missing:
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")

        parameter_types = {p.name: p for p in version.parameter_types}
        invalid = tuple(
            name
            for name, value in parameters.items()
            if name not in {p.name for p in version.parameter_types}
            and name not in version.required_parameters
            or name in parameter_types
            and not self._matches_type(value, parameter_types[name])
        )
        if invalid:
            raise ValueError(f"Invalid parameter types: {', '.join(invalid)}")

        return PlanOutcome(
            status=PlanningStatus.PLANNED,
            workflow_id=version.workflow_id,
            workflow_version_id=version.id,
            parameters=parameters,
        )

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


class CreatePlan:
    """Application boundary: plan and validate, but never start execution."""

    def __init__(
        self,
        workflow_repository,
        workflow_version_repository,
        planner: PlannerPort,
        capability_resolver=None,
    ):
        self._workflow_repository = workflow_repository
        self._workflow_version_repository = workflow_version_repository
        self._planner = planner
        self._capability_resolver = capability_resolver
        self._validator = DeterministicPlanValidator()

    def execute(self, intent: Intent) -> PlanOutcome:
        all_versions = tuple(self._workflow_version_repository.all())
        published_versions = tuple(
            version
            for version in all_versions
            if version.state is WorkflowState.PUBLISHED
        )
        request = PlanningRequest(
            intent=intent,
            candidates=tuple(
                PlanningCandidate(
                    workflow_version_id=version.id,
                    name=version.name,
                    supported_goals=version.supported_goals,
                    required_parameters=version.required_parameters,
                    parameter_types=tuple(
                        (parameter.name, parameter.type)
                        for parameter in version.parameter_types
                    ),
                )
                for version in published_versions
            ),
        )
        try:
            proposal = self._planner.plan(request)
            if not isinstance(proposal, PlanProposal):
                raise ValueError("Planner returned invalid proposal")
            result = self._validator.validate(proposal, request, all_versions)
            if result.status is PlanningStatus.PLANNED and self._capability_resolver is not None:
                version = next(v for v in all_versions if v.id == result.workflow_version_id)
                for step in version.steps:
                    try:
                        self._capability_resolver.resolve(step.capability)
                    except Exception as exc:
                        raise ValueError(f"Unknown capability: {step.capability}") from exc
            return result
        except ValueError:
            raise
        except Exception as exc:
            return PlanOutcome(
                PlanningStatus.PLANNER_FAILED,
                details=(str(exc),),
            )
