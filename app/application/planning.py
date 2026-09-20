from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol
from uuid import UUID

from app.domain.intent import Intent


class PlanningStatus(Enum):
    PLANNED = "planned"
    CLARIFICATION_REQUIRED = "clarification_required"
    NO_PLAN = "no_plan"
    PLANNER_FAILED = "planner_failed"


@dataclass(frozen=True)
class PlanProposal:
    status: PlanningStatus
    workflow_version_id: UUID | None = None
    parameters: tuple[tuple[str, object], ...] = ()
    clarification: str | None = None
    reason: str | None = None

    @classmethod
    def planned(
        cls,
        workflow_version_id: UUID,
        parameters: dict[str, object] | None = None,
    ) -> "PlanProposal":
        return cls(
            status=PlanningStatus.PLANNED,
            workflow_version_id=workflow_version_id,
            parameters=tuple((key, value) for key, value in (parameters or {}).items()),
        )

    @classmethod
    def clarification_required(cls, message: str) -> "PlanProposal":
        return cls(
            status=PlanningStatus.CLARIFICATION_REQUIRED,
            clarification=message,
        )

    @classmethod
    def no_plan(cls, reason: str) -> "PlanProposal":
        return cls(status=PlanningStatus.NO_PLAN, reason=reason)

    @classmethod
    def failed(cls, reason: str) -> "PlanProposal":
        return cls(status=PlanningStatus.PLANNER_FAILED, reason=reason)


class PlannerPort(Protocol):
    def plan(self, intent: Intent) -> PlanProposal:
        ...


@dataclass(frozen=True)
class ValidatedPlan:
    workflow_version_id: UUID
    parameters: tuple[tuple[str, object], ...]


class PlanValidationError(ValueError):
    pass


class ValidatePlanProposal:
    """Deterministically validates a planner proposal against a published version."""

    def __init__(self, workflow_versions) -> None:
        self._workflow_versions = workflow_versions

    def execute(self, proposal: PlanProposal) -> ValidatedPlan:
        if proposal.status is PlanningStatus.CLARIFICATION_REQUIRED:
            raise PlanValidationError("Planning requires clarification")
        if proposal.status is PlanningStatus.NO_PLAN:
            raise PlanValidationError("Planner produced no plan")
        if proposal.status is PlanningStatus.PLANNER_FAILED:
            raise PlanValidationError("Planner failed")
        if proposal.workflow_version_id is None:
            raise PlanValidationError("Planned result requires a workflow version")

        version = self._workflow_versions.get(proposal.workflow_version_id)
        if version is None:
            raise PlanValidationError("Workflow version not found")
        if version.state.value != "published":
            raise PlanValidationError("Only published workflow versions can be planned")

        parameters = dict(proposal.parameters)
        required = set(version.required_parameters)
        if set(parameters) != required:
            raise PlanValidationError("Plan parameters must exactly match required parameters")

        types = {parameter.name: parameter.type for parameter in version.parameter_types}
        for name, value in parameters.items():
            expected = types.get(name)
            if expected == "string" and not isinstance(value, str):
                raise PlanValidationError(f"Invalid parameter type: {name}")
            if expected == "integer" and (not isinstance(value, int) or isinstance(value, bool)):
                raise PlanValidationError(f"Invalid parameter type: {name}")
            if expected == "number" and (not isinstance(value, (int, float)) or isinstance(value, bool)):
                raise PlanValidationError(f"Invalid parameter type: {name}")
            if expected == "boolean" and not isinstance(value, bool):
                raise PlanValidationError(f"Invalid parameter type: {name}")

        return ValidatedPlan(
            workflow_version_id=proposal.workflow_version_id,
            parameters=proposal.parameters,
        )


class DeterministicPlanner:
    """Non-AI planner proving the provider-neutral planner contract."""

    def __init__(self, workflow_versions) -> None:
        self._workflow_versions = workflow_versions

    def plan(self, intent: Intent) -> PlanProposal:
        if not intent.goal.strip():
            return PlanProposal.clarification_required("A goal is required")

        candidates = [
            version
            for version in self._workflow_versions.all()
            if version.state.value == "published"
            and intent.goal in version.supported_goals
        ]
        if not candidates:
            return PlanProposal.no_plan("No published workflow version matches the intent")

        candidates.sort(key=lambda version: (version.workflow_id.hex, version.version_number))
        version = candidates[0]
        missing = [
            name for name in version.required_parameters
            if name not in intent.parameters
        ]
        if missing:
            return PlanProposal.clarification_required(
                f"Missing required parameters: {', '.join(missing)}"
            )
        return PlanProposal.planned(version.id, dict(intent.parameters))
