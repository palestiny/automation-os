from __future__ import annotations

from app.application.capability_identity_resolver import CapabilityIdentityResolver
from app.application.intent_goal_catalog import IntentGoalCatalog
from app.application.workflow_candidate_materialization import MaterializeWorkflowCandidate
from app.application.workflow_generation import WorkflowCandidate, WorkflowCandidateStep
from app.application.workflow_generation_on_no_match import (
    GenerateWorkflowOnNoMatch,
    WorkflowGenerationOnNoMatchStatus,
)
from app.application.workflow_generation_validation import ValidateWorkflowCandidate
from app.application.workflow_persistence import PersistWorkflow
from app.application.workflow_selection import SelectWorkflow
from app.domain.intent import Intent
from app.domain.workflow import Workflow, WorkflowState, WorkflowStep


class FakeGenerator:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, intent: Intent) -> WorkflowCandidate:
        self.calls += 1
        return WorkflowCandidate.create(
            name="Generated workflow",
            supported_goals=[intent.goal],
            capabilities=["content.acquire"],
            steps=[
                WorkflowCandidateStep.create(
                    "Acquire source",
                    "content.acquire",
                )
            ],
        )


def make_selection(workflows: list[Workflow]) -> SelectWorkflow:
    return SelectWorkflow(workflows)


class InMemoryWorkflowRepository:
    def __init__(self) -> None:
        self.saved = []

    def save(self, workflow: Workflow) -> None:
        self.saved.append(workflow)

    def get(self, workflow_id):
        return next((workflow for workflow in self.saved if workflow.id == workflow_id), None)

    def all(self):
        return tuple(self.saved)


def make_validator() -> ValidateWorkflowCandidate:
    return ValidateWorkflowCandidate(
        IntentGoalCatalog.create(["create_short_video"]),
        CapabilityIdentityResolver({"content.acquire"}),
    )


def test_no_match_generates_draft_workflow_without_publishing_or_executing():
    generator = FakeGenerator()
    use_case = GenerateWorkflowOnNoMatch(
        selector=make_selection([]),
        generator=generator,
        validator=make_validator(),
        materializer=MaterializeWorkflowCandidate(),
        persistence=PersistWorkflow(repository := InMemoryWorkflowRepository()),
    )

    result = use_case.execute(Intent.create("create_short_video"))

    assert result.status == WorkflowGenerationOnNoMatchStatus.GENERATED
    assert result.workflow is not None
    assert result.workflow.state is WorkflowState.DRAFT
    assert result.workflow.name == "Generated workflow"
    assert len(result.workflow.steps) == 1
    assert result.workflow.steps[0].capability == "content.acquire"
    assert result.candidate is None
    assert repository.saved == [result.workflow]
    assert generator.calls == 1


def test_selected_workflow_does_not_invoke_generator():
    workflow = Workflow.create(
        name="Existing workflow",
        steps=[WorkflowStep.create("Acquire source", "content.acquire")],
        supported_goals=["create_short_video"],
    )
    workflow.publish()

    generator = FakeGenerator()
    use_case = GenerateWorkflowOnNoMatch(
        selector=make_selection([workflow]),
        generator=generator,
        validator=make_validator(),
        materializer=MaterializeWorkflowCandidate(),
        persistence=PersistWorkflow(InMemoryWorkflowRepository()),
    )

    result = use_case.execute(Intent.create("create_short_video"))

    assert result.status == WorkflowGenerationOnNoMatchStatus.SELECTED
    assert result.workflow_id == workflow.id
    assert result.candidate is None
    assert generator.calls == 0


def test_clarification_required_does_not_invoke_generator():
    workflow = Workflow.create(
        name="Existing workflow",
        steps=[WorkflowStep.create("Acquire source", "content.acquire")],
        supported_goals=["create_short_video"],
        required_parameters=["source"],
    )
    workflow.publish()

    generator = FakeGenerator()
    use_case = GenerateWorkflowOnNoMatch(
        selector=make_selection([workflow]),
        generator=generator,
        validator=make_validator(),
        materializer=MaterializeWorkflowCandidate(),
        persistence=PersistWorkflow(InMemoryWorkflowRepository()),
    )

    result = use_case.execute(Intent.create("create_short_video"))

    assert result.status == WorkflowGenerationOnNoMatchStatus.CLARIFICATION_REQUIRED
    assert result.candidate is None
    assert generator.calls == 0
