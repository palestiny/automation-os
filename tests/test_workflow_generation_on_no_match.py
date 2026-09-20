from __future__ import annotations

from uuid import uuid4

import pytest

from app.application.capability_identity_resolver import CapabilityIdentityResolver
from app.application.intent_goal_catalog import IntentGoalCatalog
from app.application.workflow_generation import WorkflowCandidate, WorkflowCandidateStep
from app.application.workflow_generation_validation import ValidateWorkflowCandidate
from app.application.workflow_generator import WorkflowGenerator
from app.application.workflow_selection import (
    SelectWorkflow,
    WorkflowSelectionStatus,
)
from app.application.workflow_generation_on_no_match import (
    GenerateWorkflowOnNoMatch,
    WorkflowGenerationOnNoMatchStatus,
)
from app.domain.intent import Intent
from app.domain.workflow import Workflow, WorkflowStep


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


def make_validator() -> ValidateWorkflowCandidate:
    return ValidateWorkflowCandidate(
        IntentGoalCatalog.create(["create_short_video"]),
        CapabilityIdentityResolver({"content.acquire"}),
    )


def test_no_match_generates_validated_candidate_without_publishing_or_executing():
    generator = FakeGenerator()
    use_case = GenerateWorkflowOnNoMatch(
        selector=make_selection([]),
        generator=generator,
        validator=make_validator(),
    )

    result = use_case.execute(Intent.create("create_short_video"))

    assert result.status == WorkflowGenerationOnNoMatchStatus.GENERATED
    assert result.candidate is not None
    assert result.candidate.name == "Generated workflow"
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
    )

    result = use_case.execute(Intent.create("create_short_video"))

    assert result.status == WorkflowGenerationOnNoMatchStatus.SELECTED
    assert result.candidate is None
    assert generator.calls == 0


def test_non_no_match_selection_status_does_not_invoke_generator():
    generator = FakeGenerator()
    use_case = GenerateWorkflowOnNoMatch(
        selector=make_selection([]),
        generator=generator,
        validator=make_validator(),
    )

    result = use_case.execute(
        Intent.create("create_short_video", parameters={"source": "https://example.com"})
    )

    assert result.status == WorkflowGenerationOnNoMatchStatus.GENERATED
    assert generator.calls == 1
