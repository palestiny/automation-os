from __future__ import annotations

import pytest

from app.application.capability_identity_resolver import CapabilityIdentityResolver
from app.application.intent_goal_catalog import IntentGoalCatalog
from app.application.workflow_generation import WorkflowCandidate, WorkflowCandidateStep
from app.application.workflow_generation_validation import (
    InvalidWorkflowCandidateError,
    ValidateWorkflowCandidate,
)


def make_step() -> WorkflowCandidateStep:
    return WorkflowCandidateStep.create("Acquire source", "content.acquire")


def make_candidate() -> WorkflowCandidate:
    return WorkflowCandidate.create(
        name="Short video pipeline",
        supported_goals=["create_short_video"],
        required_parameters=["source"],
        capabilities=["content.acquire", "content.transcribe"],
        steps=[make_step()],
    )


def make_validator(capability_ids: set[str]) -> ValidateWorkflowCandidate:
    return ValidateWorkflowCandidate(
        goal_catalog=IntentGoalCatalog.create(["create_short_video"]),
        capability_identity_resolver=CapabilityIdentityResolver(capability_ids),
    )


def test_validator_accepts_supported_candidate():
    validator = make_validator({"content.acquire", "content.transcribe"})

    assert validator.execute(make_candidate()) == make_candidate()


def test_validator_rejects_unknown_goal():
    validator = make_validator({"content.acquire"})

    candidate = WorkflowCandidate.create(
        name="Short video pipeline",
        supported_goals=["publish_content"],
        required_parameters=["source"],
        capabilities=["content.acquire"],
        steps=[make_step()],
    )

    with pytest.raises(InvalidWorkflowCandidateError, match="goal"):
        validator.execute(candidate)


def test_validator_rejects_unknown_capability():
    validator = make_validator({"content.acquire"})

    with pytest.raises(InvalidWorkflowCandidateError, match="capability"):
        validator.execute(make_candidate())


def test_validator_rejects_non_candidate():
    validator = make_validator({"content.acquire"})

    with pytest.raises(TypeError):
        validator.execute(object())
