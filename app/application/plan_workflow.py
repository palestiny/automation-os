from __future__ import annotations

from dataclasses import dataclass

from app.application.plan_validator import PlanValidator
from app.application.planner import (
    PlanProposal,
    PlannerPort,
    PlanningRequest,
    PlanningOutcome,
    ValidatedPlan,
)


@dataclass(frozen=True)
class PlanningResult:
    proposal: PlanProposal
    validated_plan: ValidatedPlan | None = None


class PlanWorkflow:
    """Plan intent through a provider-neutral planner and deterministic validation."""

    def __init__(
        self,
        planner: PlannerPort,
        validator: PlanValidator,
    ) -> None:
        self._planner = planner
        self._validator = validator

    def execute(self, request: PlanningRequest) -> PlanningResult:
        if not isinstance(request, PlanningRequest):
            raise TypeError("request must be a PlanningRequest")

        proposal = self._planner.plan(request)
        if not isinstance(proposal, PlanProposal):
            raise TypeError("Planner must return a PlanProposal")

        if proposal.outcome is PlanningOutcome.PLANNER_FAILED:
            return PlanningResult(proposal=proposal)

        validated = self._validator.validate(request, proposal)

        if isinstance(validated, ValidatedPlan):
            return PlanningResult(
                proposal=proposal,
                validated_plan=validated,
            )

        return PlanningResult(proposal=validated)
