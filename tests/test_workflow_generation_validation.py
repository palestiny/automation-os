from __future__ import annotations

import pytest

from app.application.intent_goal_catalog import IntentGoalCatalog
from app.application.workflow_generation_validation import (
    InvalidWorkflowCandidateError,
    ValidateWorkflowCandidate,
)
from app.application.workflow_generation import WorkflowCandidate


def make_candidate() -> WorkflowCandidate:
    return WorkflowCandidate.create(
        name="Short video pipeline",
        supported_goals=["create_short_video"],
        required_parameters=["source"],
        capabilities=["content.acquire", "content.transcribe"],
    )


def test_validator_accepts_supported_candidate():
    validator = ValidateWorkflowCandidate(
        goal_catalog=IntentGoalCatalog.create(["create_short_video"]),
        capability_ids={"content.acquire", "content.transcribe"},
    )

    assert validator.execute(make_candidate()) == make_candidate()


def test_validator_rejects_unknown_goal():
    validator = ValidateWorkflowCandidate(
        goal_catalog=IntentGoalCatalog.create(["publish_content"]),
        capability_ids={"content.acquire"},
    )

    with pytest.raises(InvalidWorkflowCandidateError, match="goal"):
        validator.execute(make_candidate())


def test_validator_rejects_unknown_capability():
    validator = ValidateWorkflowCandidate(
        goal_catalog=IntentGoalCatalog.create(["create_short_video"]),
        capability_ids={"content.acquire"},
    )

    with pytest.raises(InvalidWorkflowCandidateError, match="capability"):
        validator.execute(make_candidate())


def test_validator_rejects_non_candidate():
    validator = ValidateWorkflowCandidate(
        goal_catalog=IntentGoalCatalog.create(["create_short_video"]),
        capability_ids={"content.acquire"},
    )

    with pytest.raises(TypeError):
        validator.execute(object())
