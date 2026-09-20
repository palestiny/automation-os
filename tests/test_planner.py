from uuid import uuid4

import pytest

from app.application.plan_validator import PlanValidationError, PlanValidator
from app.application.planner import (
    PlanProposal,
    PlannerPort,
    PlanningOutcome,
    PlanningRequest,
    ValidatedPlan,
)
from app.domain.workflow import WorkflowParameter, WorkflowStep
from app.domain.workflow_version import WorkflowVersion


class FakeVersionRepository:
    def __init__(self, versions=()):
        self.versions = {version.id: version for version in versions}

    def get(self, version_id):
        return self.versions.get(version_id)


class FakePlanner:
    def __init__(self, proposal):
        self.proposal = proposal

    def plan(self, request):
        return self.proposal


def published_version(required=("name",), parameter_types=()):
    version = WorkflowVersion.create_from_workflow(
        __import__("app.domain.workflow", fromlist=["Workflow"]).Workflow.create(
            name="test workflow",
            steps=[WorkflowStep.create(name="step", capability="test.capability")],
            required_parameters=list(required),
            parameter_types=list(parameter_types),
        ),
        1,
    )
    version.publish()
    return version


def test_planner_port_is_provider_neutral():
    planner = FakePlanner(
        PlanProposal(outcome=PlanningOutcome.NO_PLAN, reason="no match")
    )

    assert isinstance(planner, PlannerPort)


def test_valid_proposal_becomes_validated_plan():
    version = published_version(
        parameter_types=[WorkflowParameter.create("name", "string")]
    )
    validator = PlanValidator(FakeVersionRepository([version]))
    proposal = PlanProposal(
        outcome=PlanningOutcome.PLANNED,
        workflow_version_id=version.id,
        parameters=(("name", "Khaled"),),
    )

    result = validator.validate(
        PlanningRequest(intent="automate greeting", context={}),
        proposal,
    )

    assert result == ValidatedPlan(
        workflow_version_id=version.id,
        parameters=(("name", "Khaled"),),
    )


def test_unknown_workflow_version_is_rejected():
    validator = PlanValidator(FakeVersionRepository())

    with pytest.raises(PlanValidationError, match="not found"):
        validator.validate(
            PlanningRequest(intent="do something", context={}),
            PlanProposal(
                outcome=PlanningOutcome.PLANNED,
                workflow_version_id=uuid4(),
            ),
        )


def test_unpublished_workflow_version_is_rejected():
    from app.domain.workflow import Workflow

    workflow = Workflow.create(
        name="draft",
        steps=[WorkflowStep.create(name="step", capability="test.capability")],
    )
    version = WorkflowVersion.create_from_workflow(workflow, 1)
    validator = PlanValidator(FakeVersionRepository([version]))

    with pytest.raises(PlanValidationError, match="published"):
        validator.validate(
            PlanningRequest(intent="do something", context={}),
            PlanProposal(
                outcome=PlanningOutcome.PLANNED,
                workflow_version_id=version.id,
            ),
        )


def test_missing_required_parameter_is_rejected():
    version = published_version(required=("name",))
    validator = PlanValidator(FakeVersionRepository([version]))

    with pytest.raises(PlanValidationError, match="Missing required"):
        validator.validate(
            PlanningRequest(intent="do something", context={}),
            PlanProposal(
                outcome=PlanningOutcome.PLANNED,
                workflow_version_id=version.id,
            ),
        )


def test_invalid_parameter_type_is_rejected():
    version = published_version(
        parameter_types=[WorkflowParameter.create("count", "integer")]
    )
    validator = PlanValidator(FakeVersionRepository([version]))

    with pytest.raises(PlanValidationError, match="Invalid value"):
        validator.validate(
            PlanningRequest(intent="count", context={}),
            PlanProposal(
                outcome=PlanningOutcome.PLANNED,
                workflow_version_id=version.id,
                parameters=(("count", "not-an-int"),),
            ),
        )


def test_clarification_is_explicit_and_does_not_require_execution():
    proposal = PlanProposal(
        outcome=PlanningOutcome.CLARIFICATION_REQUIRED,
        clarification_questions=("Which source should be used?",),
    )
    validator = PlanValidator(FakeVersionRepository())

    result = validator.validate(
        PlanningRequest(intent="download something", context={}),
        proposal,
    )

    assert result is proposal
    assert result.outcome is PlanningOutcome.CLARIFICATION_REQUIRED


def test_no_plan_is_explicit():
    proposal = PlanProposal(
        outcome=PlanningOutcome.NO_PLAN,
        reason="No published workflow matches",
    )
    result = PlanValidator(FakeVersionRepository()).validate(
        PlanningRequest(intent="unknown", context={}),
        proposal,
    )
    assert result.outcome is PlanningOutcome.NO_PLAN


def test_planning_contract_does_not_execute_workflow():
    proposal = PlanProposal(
        outcome=PlanningOutcome.PLANNED,
        workflow_version_id=uuid4(),
    )
    assert proposal.outcome is PlanningOutcome.PLANNED


def test_plan_workflow_stops_at_validated_plan():
    from app.application.plan_workflow import PlanWorkflow

    version = published_version(
        parameter_types=[WorkflowParameter.create("name", "string")]
    )
    planner = FakePlanner(
        PlanProposal(
            outcome=PlanningOutcome.PLANNED,
            workflow_version_id=version.id,
            parameters=(("name", "Khaled"),),
        )
    )

    result = PlanWorkflow(
        planner,
        PlanValidator(FakeVersionRepository([version])),
    ).execute(PlanningRequest(intent="greet", context={}))

    assert result.validated_plan is not None
    assert result.validated_plan.workflow_version_id == version.id


def test_plan_workflow_preserves_clarification_without_execution():
    from app.application.plan_workflow import PlanWorkflow

    proposal = PlanProposal(
        outcome=PlanningOutcome.CLARIFICATION_REQUIRED,
        clarification_questions=("Which source?",),
    )

    result = PlanWorkflow(
        FakePlanner(proposal),
        PlanValidator(FakeVersionRepository()),
    ).execute(PlanningRequest(intent="download", context={}))

    assert result.validated_plan is None
    assert result.proposal.outcome is PlanningOutcome.CLARIFICATION_REQUIRED


def test_plan_workflow_rejects_non_structured_planner_output():
    from app.application.plan_workflow import PlanWorkflow

    class BadPlanner:
        def plan(self, request):
            return "execute this"

    with pytest.raises(TypeError, match="PlanProposal"):
        PlanWorkflow(
            BadPlanner(),
            PlanValidator(FakeVersionRepository()),
        ).execute(PlanningRequest(intent="anything", context={}))
