import pytest

from app.application.workflow_generation import WorkflowCandidate, WorkflowCandidateStep


def candidate_step() -> WorkflowCandidateStep:
    return WorkflowCandidateStep.create("Acquire source", "content.acquire")


def test_candidate_contains_explicit_workflow_metadata():
    candidate = WorkflowCandidate.create(
        "Create short video",
        ["create_short_video"],
        ["source_url"],
        ["content.acquire", "content.transcribe"],
        steps=[candidate_step()],
    )
    assert candidate.name == "Create short video"
    assert candidate.supported_goals == ("create_short_video",)
    assert candidate.required_parameters == ("source_url",)
    assert candidate.capabilities == ("content.acquire", "content.transcribe")


def test_candidate_rejects_empty_name():
    with pytest.raises(ValueError, match="name"):
        WorkflowCandidate.create("", ["create_short_video"])


def test_candidate_rejects_empty_goal():
    with pytest.raises(ValueError, match="non-empty"):
        WorkflowCandidate.create("Workflow", [""])


def test_candidate_rejects_duplicate_goals():
    with pytest.raises(ValueError, match="unique"):
        WorkflowCandidate.create("Workflow", ["create_short_video", "create_short_video"])


def test_candidate_rejects_duplicate_parameters():
    with pytest.raises(ValueError, match="unique"):
        WorkflowCandidate.create("Workflow", ["create_short_video"], ["source_url", "source_url"])


def test_candidate_rejects_empty_capability():
    with pytest.raises(ValueError, match="non-empty"):
        WorkflowCandidate.create("Workflow", ["create_short_video"], capabilities=[""])


def test_candidate_is_immutable():
    candidate = WorkflowCandidate.create("Workflow", ["create_short_video"], steps=[candidate_step()])
    with pytest.raises(AttributeError):
        candidate.name = "Changed"
