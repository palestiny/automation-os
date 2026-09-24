from __future__ import annotations

import pytest

from app.application.workflow_generation import WorkflowCandidate, WorkflowCandidateStep
from app.application.workflow_candidate_materialization import MaterializeWorkflowCandidate
from app.domain.workflow import WorkflowState


def make_candidate() -> WorkflowCandidate:
    return WorkflowCandidate.create(
        name="Create short video",
        supported_goals=["create_short_video"],
        required_parameters=["source_url"],
        parameter_types={"source_url": "string"},
        steps=[
            WorkflowCandidateStep.create(
                name="Acquire source",
                capability="content.acquire",
            ),
        ],
        triggers=["manual"],
        automation_domain="content",
        discovery_tags=["video"],
    )


def test_materializer_converts_candidate_to_draft_workflow():
    materializer = MaterializeWorkflowCandidate()

    workflow = materializer.execute(make_candidate())

    assert workflow.state == WorkflowState.DRAFT
    assert workflow.name == "Create short video"
    assert len(workflow.steps) == 1
    assert workflow.steps[0].name == "Acquire source"
    assert workflow.steps[0].capability == "content.acquire"
    assert workflow.supported_goals == ("create_short_video",)
    assert workflow.required_parameters == ("source_url",)
    assert workflow.parameter_types[0].name == "source_url"
    assert workflow.parameter_types[0].type == "string"
    assert workflow.triggers[0].event_type == "manual"
    assert workflow.automation_domain == "content"
    assert workflow.discovery_tags == ("video",)


def test_materializer_rejects_non_candidate():
    materializer = MaterializeWorkflowCandidate()

    with pytest.raises(TypeError, match="WorkflowCandidate"):
        materializer.execute(object())
