from __future__ import annotations

from app.application.planner import (
    PlanProposal,
    PlanningOutcome,
    PlanningRequest,
    ValidatedPlan,
)
from app.domain.workflow import WorkflowParameter
from app.domain.workflow_version import WorkflowVersion
from app.domain.repositories import WorkflowVersionRepository


class PlanValidationError(ValueError):
    pass


class PlanValidator:
    """Deterministically validates an untrusted planner proposal."""

    def __init__(self, workflow_versions: WorkflowVersionRepository) -> None:
        self._workflow_versions = workflow_versions

    def validate(
        self,
        request: PlanningRequest,
        proposal: PlanProposal,
    ) -> ValidatedPlan | PlanProposal:
        if not isinstance(request, PlanningRequest):
            raise TypeError("request must be a PlanningRequest")
        if not isinstance(proposal, PlanProposal):
            raise TypeError("proposal must be a PlanProposal")

        if proposal.outcome is not PlanningOutcome.PLANNED:
            return proposal

        if proposal.workflow_version_id is None:
            raise PlanValidationError(
                "Planned proposal must reference a workflow version"
            )

        version = self._workflow_versions.get(proposal.workflow_version_id)
        if version is None:
            raise PlanValidationError(
                f"Workflow version not found: {proposal.workflow_version_id}"
            )

        if version.state.value != "published":
            raise PlanValidationError(
                "Planner may only select a published workflow version"
            )

        supplied = dict(proposal.parameters)
        required = set(version.required_parameters)

        missing = required - supplied.keys()
        if missing:
            raise PlanValidationError(
                "Missing required workflow parameters: "
                + ", ".join(sorted(missing))
            )

        allowed_types = {item.name: item.type for item in version.parameter_types}
        for name, value in supplied.items():
            if name not in required:
                raise PlanValidationError(
                    f"Unknown workflow parameter: {name}"
                )
            parameter_type = allowed_types.get(name)
            if parameter_type is not None and not _matches_type(value, parameter_type):
                raise PlanValidationError(
                    f"Invalid value for workflow parameter: {name}"
                )

        return ValidatedPlan(
            workflow_version_id=version.id,
            parameters=tuple(sorted(supplied.items())),
        )


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
