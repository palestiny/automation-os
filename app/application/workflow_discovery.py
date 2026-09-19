from __future__ import annotations

from dataclasses import dataclass

from app.domain.workflow import Workflow, WorkflowState


@dataclass(frozen=True)
class WorkflowDiscoveryQuery:
    goal: str | None = None
    automation_domain: str | None = None
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.goal is not None and not isinstance(self.goal, str):
            raise ValueError("Workflow discovery goal must be a string or None")
        if self.goal is not None and not self.goal.strip():
            raise ValueError("Workflow discovery goal cannot be empty")
        if self.automation_domain is not None and (not isinstance(self.automation_domain, str) or not self.automation_domain.strip()):
            raise ValueError("Workflow discovery domain cannot be empty")
        if any(not isinstance(tag, str) or not tag.strip() for tag in self.tags):
            raise ValueError("Workflow discovery tags must be non-empty strings")
        if len(set(self.tags)) != len(self.tags):
            raise ValueError("Workflow discovery tags must be unique")


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
            and (
                query.automation_domain is None
                or workflow.automation_domain == query.automation_domain
            )
            and all(tag in workflow.discovery_tags for tag in query.tags)
        )
