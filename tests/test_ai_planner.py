from uuid import uuid4

import pytest

from app.application.ai_planner import (
    AIPlanner,
    PlanOutcome,
    PlanProposal,
    PlannerInput,
    PlannerPort,
)
from app.domain.intent import Intent
from app.domain.workflow import Workflow, WorkflowParameter, WorkflowStep, WorkflowState
from app.domain.workflow_version import WorkflowVersion


class FakePlanner(PlannerPort):
    def __init__(self, proposal=None, error=None):
        self.proposal = proposal
        self.error = error

    def propose(self, planner_input):
        if self.error:
            raise self.error
        return self.proposal


def published_version(workflow_id=None):
    workflow = Workflow.create(
        "publish",
        [WorkflowStep.create("step", "capability.test")],
        supported_goals=["publish"],
        required_parameters=["name"],
        parameter_types=[WorkflowParameter.create("name", "string")],
    )
    if workflow_id:
        workflow.id = workflow_id
    workflow.publish()
    version = WorkflowVersion.create_from_workflow(workflow, 1)
    version.publish()
    return version


def planner_input(version):
    return PlannerInput(
        intent=Intent.create("publish", {"name": "Khaled"}),
        workflow_versions=(version,),
    )


def test_valid_proposal_resolves_existing_published_version():
    version = published_version()
    proposal = PlanProposal(
        workflow_version_id=version.id,
        parameters={"name": "Khaled"},
    )
    result = AIPlanner(FakePlanner(proposal)).plan(planner_input(version))

    assert result.outcome is PlanOutcome.PLANNED
    assert result.workflow_version_id == version.id
    assert result.parameters == {"name": "Khaled"}


def test_unpublished_version_is_rejected():
    version = published_version()
    version.state = WorkflowState.DRAFT
    proposal = PlanProposal(version.id, {"name": "Khaled"})

    result = AIPlanner(FakePlanner(proposal)).plan(planner_input(version))

    assert result.outcome is PlanOutcome.NO_PLAN
    assert "published" in result.reason.lower()


def test_unknown_version_is_rejected():
    version = published_version()
    proposal = PlanProposal(uuid4(), {"name": "Khaled"})

    result = AIPlanner(FakePlanner(proposal)).plan(planner_input(version))

    assert result.outcome is PlanOutcome.NO_PLAN


def test_missing_required_parameter_requires_clarification():
    version = published_version()
    proposal = PlanProposal(version.id, {})

    result = AIPlanner(FakePlanner(proposal)).plan(planner_input(version))

    assert result.outcome is PlanOutcome.CLARIFICATION_REQUIRED
    assert "name" in result.missing_parameters


def test_invalid_parameter_type_is_rejected():
    version = published_version()
    proposal = PlanProposal(version.id, {"name": 42})

    result = AIPlanner(FakePlanner(proposal)).plan(planner_input(version))

    assert result.outcome is PlanOutcome.NO_PLAN
    assert "name" in result.reason


def test_provider_failure_maps_to_planner_failed():
    version = published_version()
    result = AIPlanner(FakePlanner(error=RuntimeError("provider down"))).plan(
        planner_input(version)
    )

    assert result.outcome is PlanOutcome.PLANNER_FAILED


def test_no_plan_is_explicit():
    version = published_version()
    result = AIPlanner(FakePlanner(None)).plan(planner_input(version))

    assert result.outcome is PlanOutcome.NO_PLAN


def test_planner_does_not_mutate_execution():
    version = published_version()
    proposal = PlanProposal(version.id, {"name": "Khaled"})
    result = AIPlanner(FakePlanner(proposal)).plan(planner_input(version))

    assert result.outcome is PlanOutcome.PLANNED
