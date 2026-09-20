from __future__ import annotations

from uuid import UUID

from app.application.workflow_generation import WorkflowCandidate, WorkflowCandidateStep
from app.application.workflow_generation_to_draft import CreateDraftWorkflowFromCandidate
from app.domain.workflow import WorkflowState


class InMemoryWorkflowRepository:
    def __init__(self) -> None:
        self.saved = []

    def save(self, workflow) -> None:
        self.saved.append(workflow)


def make_candidate() -> WorkflowCandidate:
    return WorkflowCandidate.create(
        name="Generated short video workflow",
        supported_goals=["create_short_video"],
        required_parameters=["source_url"],
        parameter_types={"source_url": "string"},
        steps=[
            WorkflowCandidateStep.create("Acquire source", "content.acquire"),
            WorkflowCandidateStep.create("Transcribe source", "content.transcribe"),
        ],
        triggers=["manual"],
        automation_domain="content",
        discovery_tags=["video", "shorts"],
    )


def test_materializes_validated_candidate_as_new_draft_workflow():
    repository = InMemoryWorkflowRepository()
    use_case = CreateDraftWorkflowFromCandidate(repository)

    workflow = use_case.execute(make_candidate())

    assert workflow.state is WorkflowState.DRAFT
    assert workflow.name == "Generated short video workflow"
    assert workflow.supported_goals == ("create_short_video",)
    assert workflow.required_parameters == ("source_url",)
    assert workflow.parameter_types[0].name == "source_url"
    assert workflow.parameter_types[0].type == "string"
    assert workflow.triggers[0].event_type == "manual"
    assert workflow.automation_domain == "content"
    assert workflow.discovery_tags == ("video", "shorts")
    assert [step.name for step in workflow.steps] == [
        "Acquire source",
        "Transcribe source",
    ]
    assert [step.capability for step in workflow.steps] == [
        "content.acquire",
        "content.transcribe",
    ]
    assert all(isinstance(step.id, UUID) for step in workflow.steps)
    assert repository.saved == [workflow]


def test_materialization_never_publishes_or_executes_generated_workflow():
    repository = InMemoryWorkflowRepository()
    use_case = CreateDraftWorkflowFromCandidate(repository)

    workflow = use_case.execute(make_candidate())

    assert workflow.state is WorkflowState.DRAFT
