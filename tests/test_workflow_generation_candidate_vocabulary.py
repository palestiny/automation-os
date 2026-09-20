from __future__ import annotations

import pytest

from app.application.workflow_generation import (
    WorkflowCandidate,
    WorkflowCandidateStep,
)


def test_candidate_vocabulary_can_represent_executable_workflow_shape_without_domain_ids():
    step = WorkflowCandidateStep.create(
        name="Acquire source",
        capability="content.acquire",
    )

    candidate = WorkflowCandidate.create(
        name="Create short video",
        supported_goals=["create_short_video"],
        required_parameters=["source_url"],
        parameter_types={"source_url": "string"},
        steps=[step],
        triggers=["manual"],
        automation_domain="content",
        discovery_tags=["video", "shorts"],
    )

    assert candidate.steps == (step,)
    assert candidate.triggers == ("manual",)
    assert candidate.parameter_types == (("source_url", "string"),)
    assert candidate.automation_domain == "content"
    assert candidate.discovery_tags == ("video", "shorts")


def test_candidate_step_does_not_require_runtime_workflow_step_identity():
    step = WorkflowCandidateStep.create(
        name="Acquire source",
        capability="content.acquire",
    )

    assert step.name == "Acquire source"
    assert step.capability == "content.acquire"


def test_candidate_parameter_types_must_reference_required_parameters():
    with pytest.raises(ValueError, match="required parameters"):
        WorkflowCandidate.create(
            name="Workflow",
            supported_goals=["create_short_video"],
            required_parameters=["source_url"],
            parameter_types={"unknown": "string"},
        )


def test_candidate_rejects_unsupported_parameter_type():
    with pytest.raises(ValueError, match="parameter type"):
        WorkflowCandidate.create(
            name="Workflow",
            supported_goals=["create_short_video"],
            required_parameters=["source_url"],
            parameter_types={"source_url": "object"},
        )


def test_candidate_requires_at_least_one_step_for_generation():
    with pytest.raises(ValueError, match="step"):
        WorkflowCandidate.create(
            name="Workflow",
            supported_goals=["create_short_video"],
            steps=[],
        )
