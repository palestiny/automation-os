from dataclasses import dataclass
from uuid import uuid4

import pytest

from app.application.ai_planning import (
    PlanProposal,
    PlannerPort,
    PlanningRequest,
    PlanningStatus,
    CreatePlan,
)
from app.domain.intent import Intent
from app.domain.workflow import Workflow, WorkflowParameter, WorkflowStep, WorkflowState
from app.domain.workflow_version import WorkflowVersion
from app.infrastructure.persistence.in_memory import (
    InMemoryWorkflowRepository,
    InMemoryWorkflowVersionRepository,
)


@dataclass(frozen=True)
class FakePlanner:
    proposal: PlanProposal

    def plan(self, request: PlanningRequest) -> PlanProposal:
        return self.proposal


def published_workflow(
    *,
    required_parameters: list[str] | None = None,
) -> Workflow:
    workflow = Workflow.create(
        name="Create content",
        steps=[WorkflowStep.create(name="Create", capability="content.create")],
        supported_goals=["create_content"],
        required_parameters=required_parameters or [],
        parameter_types=[
            WorkflowParameter.create(name=name, type="string")
            for name in (required_parameters or [])
        ],
    )
    workflow.publish()
    return workflow


def published_version(workflow: Workflow) -> WorkflowVersion:
    version = WorkflowVersion.create_from_workflow(workflow, 1)
    version.publish()
    return version


def test_planner_port_is_provider_neutral():
    proposal = PlanProposal.planned(
        workflow_version_id=uuid4(),
        parameters={"topic": "automation"},
    )
    planner: PlannerPort = FakePlanner(proposal)

    result = planner.plan(
        PlanningRequest(
            intent=Intent.create(
                goal="create_content",
                parameters={"topic": "automation"},
            )
        )
    )

    assert result == proposal


def test_create_plan_accepts_valid_published_workflow_version():
    workflow = published_workflow(required_parameters=["topic"])
    version = published_version(workflow)

    workflows = InMemoryWorkflowRepository()
    versions = InMemoryWorkflowVersionRepository()
    workflows.save(workflow)
    versions.save(version)

    planner = FakePlanner(
        PlanProposal.planned(
            workflow_version_id=version.id,
            parameters={"topic": "automation"},
        )
    )

    result = CreatePlan(
        workflow_repository=workflows,
        workflow_version_repository=versions,
        planner=planner,
    ).execute(
        Intent.create(
            goal="create_content",
            parameters={"topic": "automation"},
        )
    )

    assert result.status is PlanningStatus.PLANNED
    assert result.workflow_version_id == version.id
    assert result.parameters == {"topic": "automation"}


def test_create_plan_rejects_unknown_workflow_version():
    workflows = InMemoryWorkflowRepository()
    versions = InMemoryWorkflowVersionRepository()

    planner = FakePlanner(
        PlanProposal.planned(
            workflow_version_id=uuid4(),
            parameters={},
        )
    )

    with pytest.raises(ValueError, match="Workflow version not found"):
        CreatePlan(
            workflow_repository=workflows,
            workflow_version_repository=versions,
            planner=planner,
        ).execute(Intent.create(goal="create_content"))


def test_create_plan_rejects_unpublished_workflow_version():
    workflow = published_workflow()
    version = WorkflowVersion.create_from_workflow(workflow, 1)

    workflows = InMemoryWorkflowRepository()
    versions = InMemoryWorkflowVersionRepository()
    workflows.save(workflow)
    versions.save(version)

    planner = FakePlanner(
        PlanProposal.planned(
            workflow_version_id=version.id,
            parameters={},
        )
    )

    with pytest.raises(ValueError, match="Only published workflow versions"):
        CreatePlan(
            workflow_repository=workflows,
            workflow_version_repository=versions,
            planner=planner,
        ).execute(Intent.create(goal="create_content"))


def test_create_plan_rejects_invalid_parameters():
    workflow = published_workflow(required_parameters=["topic"])
    version = published_version(workflow)

    workflows = InMemoryWorkflowRepository()
    versions = InMemoryWorkflowVersionRepository()
    workflows.save(workflow)
    versions.save(version)

    planner = FakePlanner(
        PlanProposal.planned(
            workflow_version_id=version.id,
            parameters={},
        )
    )

    with pytest.raises(ValueError, match="Missing required parameters"):
        CreatePlan(
            workflow_repository=workflows,
            workflow_version_repository=versions,
            planner=planner,
        ).execute(Intent.create(goal="create_content"))


def test_create_plan_preserves_clarification_required_outcome():
    proposal = PlanProposal.clarification_required(
        details=("Missing target platform",)
    )
    planner = FakePlanner(proposal)

    result = CreatePlan(
        workflow_repository=InMemoryWorkflowRepository(),
        workflow_version_repository=InMemoryWorkflowVersionRepository(),
        planner=planner,
    ).execute(Intent.create(goal="create_content"))

    assert result.status is PlanningStatus.CLARIFICATION_REQUIRED
    assert result.details == ("Missing target platform",)


def test_create_plan_preserves_no_plan_outcome():
    proposal = PlanProposal.no_plan(reason="No suitable published workflow")
    planner = FakePlanner(proposal)

    result = CreatePlan(
        workflow_repository=InMemoryWorkflowRepository(),
        workflow_version_repository=InMemoryWorkflowVersionRepository(),
        planner=planner,
    ).execute(Intent.create(goal="create_content"))

    assert result.status is PlanningStatus.NO_PLAN
    assert result.details == ("No suitable published workflow",)


def test_planner_failure_is_explicit():
    class FailingPlanner:
        def plan(self, request: PlanningRequest) -> PlanProposal:
            raise RuntimeError("provider unavailable")

    result = CreatePlan(
        workflow_repository=InMemoryWorkflowRepository(),
        workflow_version_repository=InMemoryWorkflowVersionRepository(),
        planner=FailingPlanner(),
    ).execute(Intent.create(goal="create_content"))

    assert result.status is PlanningStatus.PLANNER_FAILED
    assert result.details == ("provider unavailable",)


def test_create_plan_rejects_goal_not_supported_by_selected_version():
    workflow = published_workflow()
    version = published_version(workflow)

    workflows = InMemoryWorkflowRepository()
    versions = InMemoryWorkflowVersionRepository()
    workflows.save(workflow)
    versions.save(version)

    planner = FakePlanner(
        PlanProposal.planned(
            workflow_version_id=version.id,
            parameters={},
        )
    )

    with pytest.raises(ValueError, match="does not support the requested goal"):
        CreatePlan(
            workflow_repository=workflows,
            workflow_version_repository=versions,
            planner=planner,
        ).execute(Intent.create(goal="publish_video"))


def test_create_plan_rejects_invalid_parameter_types():
    workflow = published_workflow(required_parameters=["topic"])
    version = published_version(workflow)

    workflows = InMemoryWorkflowRepository()
    versions = InMemoryWorkflowVersionRepository()
    workflows.save(workflow)
    versions.save(version)

    planner = FakePlanner(
        PlanProposal.planned(
            workflow_version_id=version.id,
            parameters={"topic": 123},
        )
    )

    with pytest.raises(ValueError, match="Invalid parameter types"):
        CreatePlan(
            workflow_repository=workflows,
            workflow_version_repository=versions,
            planner=planner,
        ).execute(Intent.create(goal="create_content"))


def test_create_plan_rejects_unknown_capability():
    workflow = published_workflow()
    version = published_version(workflow)

    workflows = InMemoryWorkflowRepository()
    versions = InMemoryWorkflowVersionRepository()
    workflows.save(workflow)
    versions.save(version)

    class MissingCapabilityResolver:
        def resolve(self, capability_id):
            raise LookupError(capability_id)

    planner = FakePlanner(
        PlanProposal.planned(
            workflow_version_id=version.id,
            parameters={},
        )
    )

    with pytest.raises(ValueError, match="Unknown capability"):
        CreatePlan(
            workflow_repository=workflows,
            workflow_version_repository=versions,
            planner=planner,
            capability_resolver=MissingCapabilityResolver(),
        ).execute(Intent.create(goal="create_content"))
