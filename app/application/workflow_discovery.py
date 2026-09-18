from __future__ import annotations

from dataclasses import dataclass

from app.domain.workflow import Workflow, WorkflowState


@dataclass(frozen=True)
class WorkflowDiscoveryQuery:
    goal: str | None = None

    def __post_init__(self) -> None:
        if self.goal is not None and not isinstance(self.goal, str):
            raise ValueError("Workflow discovery goal must be a string or None")
        if self.goal is not None and not self.goal.strip():
            raise ValueError("Workflow discovery goal cannot be empty")


class DiscoverWorkflows:
    """Deterministically discovers published workflows without executing them."""

    def __init__(self, workflows: list[Workflow]) -> None:
        if any(not isinstance(workflow, Workflow) for workflow in workflows):
            raise ValueError("Workflow must be a Workflow instance")
        self._workflows = tuple(workflows)

    def execute(self, query: WorkflowDiscoveryQuery) -> tuple[Workflow, ...]:
        if not isinstance(query, WorkflowDiscoveryQuery):
            raise TypeError("query must be a WorkflowDiscoveryQuery instance")

        return tuple(
            workflow
            for workflow in self._workflows
            if workflow.state == WorkflowState.PUBLISHED
            and (
                query.goal is None
                or query.goal in workflow.supported_goals
            )
        )
