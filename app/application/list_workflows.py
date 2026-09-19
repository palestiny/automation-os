from __future__ import annotations

from app.application.workflow_discovery import DiscoverWorkflows, WorkflowDiscoveryQuery
from app.domain.repositories import WorkflowRepository
from app.domain.workflow import Workflow


class ListWorkflows:
    """Read-only application entry point for deterministic workflow discovery."""

    def __init__(self, workflow_repository: WorkflowRepository) -> None:
        if not isinstance(workflow_repository, WorkflowRepository):
            raise TypeError("workflow_repository must implement WorkflowRepository")
        self._workflow_repository = workflow_repository

    def execute(
        self,
        goal: str | None = None,
        automation_domain: str | None = None,
        tags: tuple[str, ...] = (),
    ) -> tuple[Workflow, ...]:
        discovery = DiscoverWorkflows(self._workflow_repository.all())
        return discovery.execute(
            WorkflowDiscoveryQuery(
                goal=goal,
                automation_domain=automation_domain,
                tags=tags,
            )
        )
