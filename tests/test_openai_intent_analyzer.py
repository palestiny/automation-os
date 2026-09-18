from __future__ import annotations

import pytest

from app.domain.intent import Intent
from app.infrastructure.ai.openai_intent_analyzer import OpenAIIntentAnalyzer


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


class ParsedIntent:
    def __init__(self, goal, parameters):
        self.goal = goal
        self.parameters = parameters


def test_openai_analyzer_translates_structured_response_to_intent():
    responses = FakeResponses(ParsedIntent("create_short_video", {"source": "youtube"}))
    analyzer = OpenAIIntentAnalyzer(FakeClient(responses), model="test-model")

    result = analyzer.analyze("Turn this YouTube video into a short")

    assert isinstance(result, Intent)
    assert result.goal == "create_short_video"
    assert dict(result.parameters) == {"source": "youtube"}
    assert responses.calls[0]["model"] == "test-model"
    assert responses.calls[0]["input"] == "Turn this YouTube video into a short"


def test_openai_analyzer_rejects_missing_structured_output():
    responses = FakeResponses(None)
    analyzer = OpenAIIntentAnalyzer(FakeClient(responses), model="test-model")

    with pytest.raises(ValueError, match="structured"):
        analyzer.analyze("Do something")


def test_openai_analyzer_propagates_provider_failure():
    error = RuntimeError("provider unavailable")
    responses = FakeResponses(error=error)
    analyzer = OpenAIIntentAnalyzer(FakeClient(responses), model="test-model")

    with pytest.raises(RuntimeError, match="provider unavailable"):
        analyzer.analyze("Do something")


def test_openai_analyzer_validates_provider_output_through_intent_boundary():
    responses = FakeResponses(ParsedIntent("", {}))
    analyzer = OpenAIIntentAnalyzer(FakeClient(responses), model="test-model")

    with pytest.raises(ValueError, match="goal"):
        analyzer.analyze("Do something")


def test_openai_analyzer_requires_client_and_model():
    with pytest.raises(TypeError):
        OpenAIIntentAnalyzer(None, model="test-model")

    responses = FakeResponses()
    with pytest.raises(ValueError, match="model"):
        OpenAIIntentAnalyzer(FakeClient(responses), model="  ")
