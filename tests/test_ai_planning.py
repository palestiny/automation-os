from uuid import uuid4

from app.application.ai_planning import (
    AIPlanner,
    PlanProposal,
    PlanStatus,
    PlannerPort,
)
from app.domain.intent import Intent
from app.domain.workflow import Workflow, WorkflowParameter, WorkflowStep
from app.domain.workflow_version import WorkflowVersion


class FakePlannerProvider:
    def __init__(self, proposal=None, error=None):
        self.proposal = proposal
        self.error = error

    def plan(self, intent):
        if self.error:
            raise self.error
        return self.proposal


def make_version(published=True):
    workflow = Workflow.create(
        name="video workflow",
        steps=[WorkflowStep.create(name="download", capability="video.download")],
        supported_goals=["download video"],
        required_parameters=["url"],
        parameter_types=[WorkflowParameter(name="url", type="string")],
    )
    version = WorkflowVersion.create_from_workflow(workflow, 1)
    if published:
        version.publish()
    return workflow, version


def test_planner_provider_is_provider_neutral():
    assert isinstance(FakePlannerProvider(), PlannerPort)


def test_valid_proposal_becomes_planned():
    workflow, version = make_version()
    proposal = PlanProposal.create(
        workflow_id=workflow.id,
        workflow_version_id=version.id,
        parameters={"url": "https://example.com"},
    )

    result = AIPlanner(FakePlannerProvider(proposal)).plan(
        Intent.create("download video", {"url": "https://example.com"}),
        [version],
    )

    assert result.status is PlanStatus.PLANNED
    assert result.workflow_id == workflow.id
    assert result.workflow_version_id == version.id


def test_unpublished_version_is_rejected():
    workflow, version = make_version(False)
    proposal = PlanProposal.create(
        workflow_id=workflow.id,
        workflow_version_id=version.id,
        parameters={"url": "https://example.com"},
    )

    result = AIPlanner(FakePlannerProvider(proposal)).plan(
        Intent.create("download video", {"url": "https://example.com"}),
        [version],
    )

    assert result.status is PlanStatus.NO_PLAN


def test_version_ownership_mismatch_is_rejected():
    _, version = make_version()
    proposal = PlanProposal.create(
        workflow_id=uuid4(),
        workflow_version_id=version.id,
        parameters={"url": "https://example.com"},
    )

    result = AIPlanner(FakePlannerProvider(proposal)).plan(
        Intent.create("download video", {"url": "https://example.com"}),
        [version],
    )

    assert result.status is PlanStatus.NO_PLAN


def test_invalid_parameter_type_is_rejected():
    workflow, version = make_version()
    proposal = PlanProposal.create(
        workflow_id=workflow.id,
        workflow_version_id=version.id,
        parameters={"url": 123},
    )

    result = AIPlanner(FakePlannerProvider(proposal)).plan(
        Intent.create("download video", {"url": "https://example.com"}),
        [version],
    )

    assert result.status is PlanStatus.NO_PLAN


def test_missing_required_parameter_requires_clarification():
    workflow, version = make_version()
    proposal = PlanProposal.create(
        workflow_id=workflow.id,
        workflow_version_id=version.id,
        parameters={},
    )

    result = AIPlanner(FakePlannerProvider(proposal)).plan(
        Intent.create("download video", {}),
        [version],
    )

    assert result.status is PlanStatus.CLARIFICATION_REQUIRED
    assert result.missing_parameters == ("url",)


def test_provider_failure_is_explicit():
    result = AIPlanner(
        FakePlannerProvider(error=RuntimeError("model down"))
    ).plan(Intent.create("download video", {}), [])

    assert result.status is PlanStatus.PLANNER_FAILED


def test_none_proposal_is_no_plan():
    result = AIPlanner(FakePlannerProvider()).plan(
        Intent.create("download video", {}), []
    )

    assert result.status is PlanStatus.NO_PLAN


def test_planner_has_no_execution_dependency():
    assert not hasattr(AIPlanner, "start_execution")
    assert not hasattr(AIPlanner, "execute_capability")
