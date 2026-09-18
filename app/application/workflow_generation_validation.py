from __future__ import annotations

from app.application.intent_goal_catalog import IntentGoalCatalog
from app.application.workflow_generation import WorkflowCandidate


class InvalidWorkflowCandidateError(ValueError):
    pass


class ValidateWorkflowCandidate:
    """Validate generated workflow candidates before review/publication."""

    def __init__(
        self,
        goal_catalog: IntentGoalCatalog,
        capability_ids: set[str],
    ) -> None:
        if not isinstance(goal_catalog, IntentGoalCatalog):
            raise TypeError("goal_catalog must be an IntentGoalCatalog instance")
        if any(not isinstance(value, str) or not value.strip() for value in capability_ids):
            raise ValueError("capability_ids must contain non-empty strings")

        self._goal_catalog = goal_catalog
        self._capability_ids = frozenset(capability_ids)

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

        unknown_capabilities = tuple(
            capability
            for capability in candidate.capabilities
            if capability not in self._capability_ids
        )
        if unknown_capabilities:
            raise InvalidWorkflowCandidateError(
                "Workflow candidate contains unsupported capability: "
                f"{unknown_capabilities[0]}"
            )

        return candidate
