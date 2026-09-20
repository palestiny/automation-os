from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from app.application.workflow_builder import WorkflowBuilder
from app.domain.workflow import Trigger, Workflow, WorkflowParameter, WorkflowStep


class PlanningError(ValueError):
    """Raised when a planning request or planner output is invalid."""


@dataclass(frozen=True)
class PlanningRequest:
    goal: str
    context: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.goal, str) or not self.goal.strip():
            raise PlanningError("Planning request goal cannot be empty")


@dataclass(frozen=True)
class WorkflowPlanStep:
    name: str
    capability: str


@dataclass(frozen=True)
class WorkflowPlan:
    name: str
    steps: tuple[WorkflowPlanStep, ...]
    triggers: tuple[Trigger, ...] = ()
    supported_goals: tuple[str, ...] = ()
    required_parameters: tuple[str, ...] = ()
    parameter_types: tuple[WorkflowParameter, ...] = ()
    automation_domain: str | None = None
    discovery_tags: tuple[str, ...] = ()


class WorkflowPlanner(Protocol):
    def plan(self, request: PlanningRequest) -> WorkflowPlan:
        ...


class PlanWorkflow:
    """Turn a validated planner proposal into a draft Workflow only."""

    def __init__(
        self,
        planner: WorkflowPlanner,
        *,
        workflow_builder: WorkflowBuilder | None = None,
    ) -> None:
        self._planner = planner
        self._workflow_builder = workflow_builder or WorkflowBuilder()

    def execute(self, request: PlanningRequest) -> Workflow:
        plan = self._planner.plan(request)
        self._validate_plan(plan)

        steps = [
            WorkflowStep.create(
                name=step.name.strip(),
                capability=step.capability.strip(),
            )
            for step in plan.steps
        ]

        return self._workflow_builder.create(
            name=plan.name.strip(),
            steps=steps,
            triggers=list(plan.triggers),
            supported_goals=list(plan.supported_goals),
            required_parameters=list(plan.required_parameters),
            parameter_types=list(plan.parameter_types),
            automation_domain=plan.automation_domain,
            discovery_tags=list(plan.discovery_tags),
        )

    @staticmethod
    def _validate_plan(plan: WorkflowPlan) -> None:
        if not isinstance(plan, WorkflowPlan):
            raise PlanningError("Planner must return a WorkflowPlan")
        if not plan.name.strip():
            raise PlanningError("Workflow plan name cannot be empty")
        if not plan.steps:
            raise PlanningError("Workflow plan must contain at least one step")

        for step in plan.steps:
            if not isinstance(step, WorkflowPlanStep):
                raise PlanningError("Workflow plan steps must be WorkflowPlanStep instances")
            if not step.name.strip():
                raise PlanningError("Workflow plan step name cannot be empty")
            if not step.capability.strip():
                raise PlanningError("Workflow plan step capability cannot be empty")
