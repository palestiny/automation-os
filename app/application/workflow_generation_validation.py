from __future__ import annotations

from app.application.capability_identity_resolver import CapabilityIdentityResolver
from app.application.intent_goal_catalog import IntentGoalCatalog
from app.application.workflow_generation import WorkflowCandidate


class InvalidWorkflowCandidateError(ValueError):
    pass


class ValidateWorkflowCandidate:
    """Validate generated workflow candidates before review/publication."""

    def __init__(
        self,
        goal_catalog: IntentGoalCatalog,
        capability_identity_resolver: CapabilityIdentityResolver,
    ) -> None:
        if not isinstance(goal_catalog, IntentGoalCatalog):
            raise TypeError("goal_catalog must be an IntentGoalCatalog instance")
        if not isinstance(capability_identity_resolver, CapabilityIdentityResolver):
            raise TypeError(
                "capability_identity_resolver must be a CapabilityIdentityResolver instance"
            )

        self._goal_catalog = goal_catalog
        self._capability_identity_resolver = capability_identity_resolver

    def execute(self, candidate: WorkflowCandidate) -> WorkflowCandidate:
        if not isinstance(candidate, WorkflowCandidate):
            raise TypeError("candidate must be a WorkflowCandidate instance")

        unknown_goals = tuple(
            goal for goal in candidate.supported_goals
            if not self._goal_catalog.contains(goal)
        )
        if unknown_goals:
            raise InvalidWorkflowCandidateError(
                f"Workflow candidate contains unsupported goal: {unknown_goals[0]}"
            )

        if not candidate.steps:
            raise InvalidWorkflowCandidateError(
                "Workflow candidate must contain at least one step"
            )

        step_capabilities = tuple(step.capability for step in candidate.steps)
        unknown_step_capabilities = tuple(
            capability
            for capability in step_capabilities
            if not self._capability_identity_resolver.contains(capability)
        )
        if unknown_step_capabilities:
            raise InvalidWorkflowCandidateError(
                "Workflow candidate contains unsupported capability: "
                f"{unknown_step_capabilities[0]}"
            )

        unknown_capabilities = tuple(
            capability
            for capability in candidate.capabilities
            if not self._capability_identity_resolver.contains(capability)
        )
        if unknown_capabilities:
            raise InvalidWorkflowCandidateError(
                "Workflow candidate contains unsupported capability: "
                f"{unknown_capabilities[0]}"
            )

        return candidate
