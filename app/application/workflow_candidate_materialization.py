from __future__ import annotations

from app.application.workflow_generation import WorkflowCandidate
from app.domain.workflow import Trigger, Workflow, WorkflowParameter, WorkflowStep


class MaterializeWorkflowCandidate:
    """Deterministically materialize a validated candidate as a DRAFT workflow."""

    def execute(self, candidate: WorkflowCandidate) -> Workflow:
        if not isinstance(candidate, WorkflowCandidate):
            raise TypeError("candidate must be a WorkflowCandidate instance")

        steps = [
            WorkflowStep.create(
                name=step.name,
                capability=step.capability,
            )
            for step in candidate.steps
        ]
        triggers = [Trigger.create(trigger) for trigger in candidate.triggers]
        parameter_types = [
            WorkflowParameter.create(name=name, type=parameter_type)
            for name, parameter_type in candidate.parameter_types
        ]

        return Workflow.create(
            name=candidate.name,
            steps=steps,
            triggers=triggers,
            supported_goals=list(candidate.supported_goals),
            required_parameters=list(candidate.required_parameters),
            parameter_types=parameter_types,
            automation_domain=candidate.automation_domain,
            discovery_tags=list(candidate.discovery_tags),
        )
