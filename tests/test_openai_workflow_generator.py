from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.application.workflow_generation import WorkflowCandidate
from app.application.workflow_generator import WorkflowGenerator
from app.domain.intent import Intent
from app.infrastructure.ai.openai_workflow_generator import OpenAIWorkflowGenerator
from app.infrastructure.provider import ProviderConfiguration


class FakeResponses:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_parsed=self.payload)


class FakeClient:
    def __init__(self, payload):
        self.responses = FakeResponses(payload)


def make_configuration() -> ProviderConfiguration:
    return ProviderConfiguration(
        provider_id="openai",
        service_id="workflow-generation-test",
    )


def make_payload() -> SimpleNamespace:
    return SimpleNamespace(
        name="Generated short video workflow",
        supported_goals=["create_short_video"],
        required_parameters=["source_url"],
        parameter_types={"source_url": "string"},
        steps=[
            SimpleNamespace(name="Acquire source", capability="content.acquire"),
        ],
        triggers=["manual"],
        automation_domain="content",
        discovery_tags=["video", "shorts"],
    )


def test_openai_workflow_generator_implements_provider_neutral_boundary():
    generator = OpenAIWorkflowGenerator(
        client=FakeClient(make_payload()),
        configuration=make_configuration(),
    )

    assert isinstance(generator, WorkflowGenerator.__constraints__[0]) if hasattr(
        WorkflowGenerator, "__constraints__"
    ) else hasattr(generator, "generate")


def test_openai_workflow_generator_maps_structured_response_to_candidate():
    client = FakeClient(make_payload())
    generator = OpenAIWorkflowGenerator(client=client, configuration=make_configuration())

    candidate = generator.generate(Intent.create("create_short_video"))

    assert isinstance(candidate, WorkflowCandidate)
    assert candidate.name == "Generated short video workflow"
    assert candidate.supported_goals == ("create_short_video",)
    assert candidate.steps[0].capability == "content.acquire"
    assert candidate.parameter_types == (("source_url", "string"),)


def test_openai_workflow_generator_sends_intent_without_starting_execution():
    client = FakeClient(make_payload())
    generator = OpenAIWorkflowGenerator(client=client, configuration=make_configuration())

    generator.generate(Intent.create("create_short_video", {"source_url": "https://example.com"}))

    call = client.responses.calls[0]
    assert '"goal": "create_short_video"' in call["input"]
    assert '"source_url": "https://example.com"' in call["input"]
    assert "execution" in call["instructions"].lower()
    assert "do not start" in call["instructions"].lower()


def test_openai_workflow_generator_rejects_empty_provider_response():
    class EmptyResponses(FakeResponses):
        def parse(self, **kwargs):
            self.calls.append(kwargs)
            return SimpleNamespace(output_parsed=None)

    class EmptyClient:
        def __init__(self):
            self.responses = EmptyResponses(None)

    generator = OpenAIWorkflowGenerator(
        client=EmptyClient(),
        configuration=make_configuration(),
    )

    with pytest.raises(ValueError, match="structured workflow candidate"):
        generator.generate(Intent.create("create_short_video"))


def test_openai_workflow_generator_requires_openai_configuration():
    configuration = ProviderConfiguration(
        provider_id="anthropic",
        service_id="workflow-generation-test",
    )

    with pytest.raises(ValueError, match="openai"):
        OpenAIWorkflowGenerator(
            client=FakeClient(make_payload()),
            configuration=configuration,
        )
