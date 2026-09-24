from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.application.workflow_generation import WorkflowCandidate
from app.application.workflow_generator import WorkflowGenerator
from app.domain.intent import Intent
from app.infrastructure.ai.openai_workflow_generator import OpenAIWorkflowGenerator
from app.infrastructure.provider import ProviderConfiguration


@dataclass
class FakeParsedResponse:
    output_parsed: object


class FakeResponses:
    def __init__(self, payload: object) -> None:
        self.payload = payload
        self.calls: list[dict[str, object]] = []

    def parse(self, **kwargs: object) -> FakeParsedResponse:
        self.calls.append(kwargs)
        return FakeParsedResponse(self.payload)


class FakeClient:
    def __init__(self, payload: object) -> None:
        self.responses = FakeResponses(payload)


def configuration() -> ProviderConfiguration:
    return ProviderConfiguration(
        provider_id="openai",
        service_id="test-model",
        credentials_ref="test-key",
    )


def test_openai_workflow_generator_implements_provider_neutral_boundary():
    payload = {
        "name": "Create short video",
        "supported_goals": ["create_short_video"],
        "required_parameters": ["source_url"],
        "parameter_types": {"source_url": "string"},
        "steps": [
            {"name": "Acquire source", "capability": "content.acquire"},
        ],
        "triggers": ["manual"],
        "automation_domain": "content",
        "discovery_tags": ["video"],
    }
    generator: WorkflowGenerator = OpenAIWorkflowGenerator(
        FakeClient(payload),
        configuration(),
    )

    candidate = generator.generate(Intent.create("create_short_video"))

    assert isinstance(candidate, WorkflowCandidate)
    assert candidate.name == "Create short video"
    assert candidate.steps[0].capability == "content.acquire"


def test_openai_workflow_generator_sends_intent_to_provider():
    client = FakeClient(
        {
            "name": "Create short video",
            "supported_goals": ["create_short_video"],
            "required_parameters": [],
            "parameter_types": {},
            "steps": [{"name": "Acquire", "capability": "content.acquire"}],
            "triggers": ["manual"],
            "automation_domain": "content",
            "discovery_tags": [],
        }
    )
    generator = OpenAIWorkflowGenerator(client, configuration())

    generator.generate(Intent.create("create_short_video"))

    call = client.responses.calls[0]
    assert "create_short_video" in str(call["input"])


def test_openai_workflow_generator_rejects_missing_structured_response():
    client = FakeClient(None)
    generator = OpenAIWorkflowGenerator(client, configuration())

    with pytest.raises(ValueError, match="structured"):
        generator.generate(Intent.create("create_short_video"))
