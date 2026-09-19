from __future__ import annotations

from uuid import UUID

from app.domain.workflow import Trigger, Workflow, WorkflowParameter, WorkflowStep


class WorkflowBuilder:
    """Application boundary for deterministic workflow composition."""

    def create(
        self,
        name: str,
        steps: list[WorkflowStep],
        *,
        triggers: list[Trigger] | None = None,
        supported_goals: list[str] | None = None,
        required_parameters: list[str] | None = None,
        parameter_types: list[WorkflowParameter] | None = None,
        automation_domain: str | None = None,
        discovery_tags: list[str] | None = None,
    ) -> Workflow:
        """Compose a draft Workflow without executing or persisting it."""
        self._validate_steps(steps)
        return Workflow.create(
            name=name,
            steps=steps,
            triggers=triggers,
            supported_goals=supported_goals,
            required_parameters=required_parameters,
            parameter_types=parameter_types,
            automation_domain=automation_domain,
            discovery_tags=discovery_tags,
        )

    @staticmethod
    def _validate_steps(steps: list[WorkflowStep]) -> None:
        if not steps:
            raise ValueError("Workflow must contain at least one step")

        if any(not isinstance(step, WorkflowStep) for step in steps):
            raise ValueError("Workflow steps must be WorkflowStep instances")

        ids = [step.id for step in steps]
        if len(set(ids)) != len(ids):
            raise ValueError("Workflow step identities must be unique")

        if any(not isinstance(step.id, UUID) for step in steps):
            raise ValueError("Workflow step identity must be a UUID")
