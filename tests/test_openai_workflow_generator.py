from types import SimpleNamespace

import pytest

from app.domain.intent import Intent
from app.infrastructure.ai.openai_workflow_generator import OpenAIWorkflowGenerator
from app.infrastructure.provider import ProviderConfiguration


class FakeResponses:
    def __init__(self, parsed):
        self.parsed = parsed
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_parsed=self.parsed)


class FakeClient:
    def __init__(self, parsed):
        self.responses = FakeResponses(parsed)


def configuration() -> ProviderConfiguration:
    return ProviderConfiguration.create(
        provider="openai",
        service="gpt-test",
        api_key="test-key",
    )


def test_openai_workflow_generator_returns_provider_neutral_candidate():
    client = FakeClient(
        SimpleNamespace(
            name="Create short video",
            supported_goals=["create_short_video"],
            required_parameters=["source_url"],
            parameter_types={"source_url": "string"},
            steps=[
                {"name": "Acquire source", "capability": "content.acquire"},
            ],
            triggers=["manual"],
            automation_domain="content",
            discovery_tags=["video"],
        )
    )

    generator = OpenAIWorkflowGenerator(client, configuration())

    candidate = generator.generate(
        Intent.create("create_short_video", {"source_url": "https://example.com/video"})
    )

    assert candidate.name == "Create short video"
    assert candidate.supported_goals == ("create_short_video",)
    assert candidate.required_parameters == ("source_url",)
    assert candidate.parameter_types == (("source_url", "string"),)
    assert candidate.steps[0].capability == "content.acquire"
    assert candidate.triggers == ("manual",)
    assert candidate.automation_domain == "content"
    assert candidate.discovery_tags == ("video",)
    assert client.responses.calls


def test_openai_workflow_generator_rejects_missing_structured_response():
    client = FakeClient(None)
    generator = OpenAIWorkflowGenerator(client, configuration())

    with pytest.raises(ValueError, match="structured"):
        generator.generate(Intent.create("create_short_video"))
