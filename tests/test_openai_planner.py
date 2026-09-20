from __future__ import annotations

from uuid import uuid4

import pytest

from app.application.ai_planning import (
    PlanProposal,
    PlanningCandidate,
    PlanningRequest,
    PlanningStatus,
)
from app.domain.intent import Intent
from app.infrastructure.ai.openai_planner import OpenAIPlanner
from app.infrastructure.provider import ProviderConfiguration


class FakeParsed:
    def __init__(self, parsed):
        self.output_parsed = parsed


class FakeResponses:
    def __init__(self, parsed=None, error=None):
        self.parsed = parsed
        self.error = error
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return FakeParsed(self.parsed)


class FakeClient:
    def __init__(self, responses):
        self.responses = responses


class ParsedPlan:
    def __init__(
        self,
        status,
        workflow_version_id=None,
        parameters=None,
        details=None,
    ):
        self.status = status
        self.workflow_version_id = workflow_version_id
        self.parameters = parameters or {}
        self.details = details or []


def request():
    return PlanningRequest(
        intent=Intent.create(
            goal="create_content",
            parameters={"topic": "automation"},
        ),
        candidates=(
            PlanningCandidate(
                workflow_version_id=uuid4(),
                name="Create content",
                supported_goals=("create_content",),
                required_parameters=("topic",),
                parameter_types=(("topic", "string"),),
            ),
        ),
    )


def test_openai_planner_translates_structured_planned_response():
    version_id = request().candidates[0].workflow_version_id
    responses = FakeResponses(
        ParsedPlan(
            PlanningStatus.PLANNED,
            workflow_version_id=str(version_id),
            parameters={"topic": "automation"},
        )
    )
    planner = OpenAIPlanner(
        FakeClient(responses),
        ProviderConfiguration("openai", "test-model"),
    )

    result = planner.plan(request())

    assert result == PlanProposal.planned(
        workflow_version_id=version_id,
        parameters={"topic": "automation"},
    )
    assert responses.calls[0]["model"] == "test-model"
    assert "Candidates:" in responses.calls[0]["instructions"]


def test_openai_planner_preserves_clarification_outcome():
    responses = FakeResponses(
        ParsedPlan(
            PlanningStatus.CLARIFICATION_REQUIRED,
            details=["Missing target platform"],
        )
    )
    planner = OpenAIPlanner(
        FakeClient(responses),
        ProviderConfiguration("openai", "test-model"),
    )

    result = planner.plan(request())

    assert result.status is PlanningStatus.CLARIFICATION_REQUIRED
    assert result.details == ("Missing target platform",)


def test_openai_planner_preserves_no_plan_outcome():
    responses = FakeResponses(
        ParsedPlan(
            PlanningStatus.NO_PLAN,
            details=["No suitable workflow"],
        )
    )
    planner = OpenAIPlanner(
        FakeClient(responses),
        ProviderConfiguration("openai", "test-model"),
    )

    result = planner.plan(request())

    assert result.status is PlanningStatus.NO_PLAN
    assert result.details == ("No suitable workflow",)


def test_openai_planner_rejects_missing_structured_output():
    responses = FakeResponses(None)
    planner = OpenAIPlanner(
        FakeClient(responses),
        ProviderConfiguration("openai", "test-model"),
    )

    with pytest.raises(ValueError, match="structured plan"):
        planner.plan(request())


def test_openai_planner_rejects_invalid_workflow_version_id():
    responses = FakeResponses(
        ParsedPlan(
            PlanningStatus.PLANNED,
            workflow_version_id="not-a-uuid",
        )
    )
    planner = OpenAIPlanner(
        FakeClient(responses),
        ProviderConfiguration("openai", "test-model"),
    )

    with pytest.raises(ValueError, match="invalid workflow version id"):
        planner.plan(request())


def test_openai_planner_propagates_provider_failure():
    responses = FakeResponses(error=RuntimeError("provider unavailable"))
    planner = OpenAIPlanner(
        FakeClient(responses),
        ProviderConfiguration("openai", "test-model"),
    )

    with pytest.raises(RuntimeError, match="provider unavailable"):
        planner.plan(request())


def test_openai_planner_requires_openai_configuration_and_client():
    with pytest.raises(TypeError):
        OpenAIPlanner(None, ProviderConfiguration("openai", "test-model"))

    with pytest.raises(ValueError, match="openai"):
        OpenAIPlanner(
            FakeClient(FakeResponses()),
            ProviderConfiguration("other", "test-model"),
        )
