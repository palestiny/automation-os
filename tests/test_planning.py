from uuid import uuid4

import pytest

from app.application.planning import (
    DeterministicPlanner,
    PlanProposal,
    PlanValidationError,
    PlanningStatus,
    ValidatePlanProposal,
)
from app.domain.intent import Intent
from app.domain.workflow import Workflow, WorkflowParameter, WorkflowStep
from app.domain.workflow_version import WorkflowVersion


class FakeVersionRepository:
    def __init__(self, versions=()):
        self.versions = {version.id: version for version in versions}

    def get(self, version_id):
        return self.versions.get(version_id)

    def all(self):
        return tuple(self.versions.values())


def published_version(
    *,
    goal="create_video",
    parameters=None,
):
    workflow = Workflow.create(
        name="Video workflow",
        steps=[WorkflowStep.create("Render", "video.render")],
        supported_goals=[goal],
        required_parameters=list((parameters or {}).keys()),
        parameter_types=[
            WorkflowParameter.create(name, kind)
            for name, kind in (parameters or {}).items()
        ],
    )
    version = WorkflowVersion.create_from_workflow(workflow, 1)
    version.publish()
    return version


def test_planner_port_can_return_ready_structured_proposal():
    version = published_version(parameters={"source_url": "string"})
    planner = DeterministicPlanner(FakeVersionRepository([version]))

    proposal = planner.plan(
        Intent.create("create_video", {"source_url": "https://example.com/video"})
    )

    assert proposal.status is PlanningStatus.PLANNED
    assert proposal.workflow_version_id == version.id


def test_planner_requires_clarification_for_missing_parameters():
    version = published_version(parameters={"source_url": "string"})
    planner = DeterministicPlanner(FakeVersionRepository([version]))

    proposal = planner.plan(Intent.create("create_video"))

    assert proposal.status is PlanningStatus.CLARIFICATION_REQUIRED


def test_planner_returns_no_plan_when_no_published_version_matches():
    planner = DeterministicPlanner(FakeVersionRepository())

    proposal = planner.plan(Intent.create("unknown_goal"))

    assert proposal.status is PlanningStatus.NO_PLAN


def test_validator_rejects_unpublished_version():
    workflow = Workflow.create(
        "Draft workflow",
        [WorkflowStep.create("Render", "video.render")],
        supported_goals=["create_video"],
    )
    version = WorkflowVersion.create_from_workflow(workflow, 1)

    with pytest.raises(PlanValidationError, match="published"):
        ValidatePlanProposal(FakeVersionRepository([version])).execute(
            PlanProposal.planned(version.id)
        )


def test_validator_rejects_unknown_version():
    with pytest.raises(PlanValidationError, match="not found"):
        ValidatePlanProposal(FakeVersionRepository()).execute(
            PlanProposal.planned(uuid4())
        )


def test_validator_rejects_invalid_parameter_type():
    version = published_version(parameters={"count": "integer"})

    with pytest.raises(PlanValidationError, match="Invalid parameter type"):
        ValidatePlanProposal(FakeVersionRepository([version])).execute(
            PlanProposal.planned(version.id, {"count": "3"})
        )


def test_validator_accepts_only_exact_required_parameters():
    version = published_version(parameters={"source_url": "string"})

    validated = ValidatePlanProposal(
        FakeVersionRepository([version])
    ).execute(
        PlanProposal.planned(
            version.id,
            {"source_url": "https://example.com/video"},
        )
    )

    assert validated.workflow_version_id == version.id
    assert dict(validated.parameters)["source_url"].startswith("https://")


def test_clarification_is_not_execution():
    version = published_version(parameters={"source_url": "string"})
    proposal = DeterministicPlanner(FakeVersionRepository([version])).plan(
        Intent.create("create_video")
    )

    assert proposal.status is PlanningStatus.CLARIFICATION_REQUIRED
    assert proposal.workflow_version_id is None
