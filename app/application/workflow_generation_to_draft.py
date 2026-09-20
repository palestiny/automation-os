from __future__ import annotations

from typing import Protocol

from app.application.workflow_generation import WorkflowCandidate
from app.domain.workflow import Trigger, Workflow, WorkflowParameter, WorkflowStep


class WorkflowRepository(Protocol):
    def save(self, workflow: Workflow) -> None: ...


class CreateDraftWorkflowFromCandidate:
    """Materialize a validated candidate as a new, unpublishable draft workflow."""

    def __init__(self, repository: WorkflowRepository) -> None:
        if not hasattr(repository, "save"):
            raise TypeError("repository must provide a save(workflow) method")
        self._repository = repository

    def execute(self, candidate: WorkflowCandidate) -> Workflow:
        if not isinstance(candidate, WorkflowCandidate):
            raise TypeError("candidate must be a WorkflowCandidate instance")
        if not candidate.steps:
            raise ValueError("Workflow candidate must contain at least one step")

        steps = [
            WorkflowStep.create(
                name=step.name,
                capability=step.capability,
            )
            for step in candidate.steps
        ]
        triggers = [Trigger.create(event_type) for event_type in candidate.triggers]
        parameter_types = [
            WorkflowParameter.create(name, parameter_type)
            for name, parameter_type in candidate.parameter_types
        ]

        workflow = Workflow.create(
            name=candidate.name,
            steps=steps,
            triggers=triggers,
            supported_goals=list(candidate.supported_goals),
            required_parameters=list(candidate.required_parameters),
            parameter_types=parameter_types,
            automation_domain=candidate.automation_domain,
            discovery_tags=list(candidate.discovery_tags),
        )
        self._repository.save(workflow)
        return workflow
