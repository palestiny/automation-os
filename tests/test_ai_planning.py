from __future__ import annotations

import pytest

from app.application.ai_planning import (
    PlanningError,
    PlanningRequest,
    WorkflowPlan,
    WorkflowPlanStep,
    WorkflowPlanner,
    PlanWorkflow,
)
from app.domain.workflow import WorkflowState


class FakePlanner(WorkflowPlanner):
    def __init__(self, plan=None, error=None):
        self.plan = plan
        self.error = error

    def plan(self, request):
        if self.error:
            raise self.error
        return self.plan


def valid_plan():
    return WorkflowPlan(
        name="Publish content",
        steps=(
            WorkflowPlanStep(name="prepare", capability="content.prepare"),
            WorkflowPlanStep(name="publish", capability="content.publish"),
        ),
        supported_goals=("publish_content",),
        automation_domain="content",
        discovery_tags=("content", "publishing"),
    )


def test_valid_plan_becomes_draft_workflow():
    workflow = PlanWorkflow(FakePlanner(valid_plan())).execute(
        PlanningRequest(goal="Publish content")
    )
    assert workflow.state is WorkflowState.DRAFT
    assert workflow.name == "Publish content"
    assert [step.capability for step in workflow.steps] == [
        "content.prepare",
        "content.publish",
    ]
    assert workflow.supported_goals == ("publish_content",)


def test_planning_has_no_execution_or_publish_side_effect():
    workflow = PlanWorkflow(FakePlanner(valid_plan())).execute(
        PlanningRequest(goal="Publish content")
    )
    assert workflow.state is WorkflowState.DRAFT


@pytest.mark.parametrize(
    "plan",
    [
        WorkflowPlan(name="", steps=()),
        WorkflowPlan(
            name="Invalid",
            steps=(WorkflowPlanStep(name="", capability="content.publish"),),
        ),
        WorkflowPlan(
            name="Invalid",
            steps=(WorkflowPlanStep(name="step", capability=""),),
        ),
    ],
)
def test_invalid_plan_is_rejected(plan):
    with pytest.raises(PlanningError):
        PlanWorkflow(FakePlanner(plan)).execute(PlanningRequest(goal="anything"))


def test_planner_exception_does_not_create_workflow():
    with pytest.raises(RuntimeError, match="model failed"):
        PlanWorkflow(FakePlanner(error=RuntimeError("model failed"))).execute(
            PlanningRequest(goal="Publish content")
        )


def test_empty_planning_request_is_rejected_before_planner_call():
    planner = FakePlanner(valid_plan())
    with pytest.raises(PlanningError, match="goal"):
        PlanWorkflow(planner).execute(PlanningRequest(goal=" "))


def test_planning_request_can_carry_context_without_model_types():
    request = PlanningRequest(
        goal="Publish content",
        context={"audience": "developers"},
    )
    assert request.goal == "Publish content"
    assert request.context["audience"] == "developers"
