from dataclasses import dataclass

import pytest

from app.application.intent_analysis import IntentAnalyzer
from app.domain.intent import Intent


@dataclass(frozen=True)
class FakeIntentAnalyzer:
    intent: Intent

    def analyze(self, request: str) -> Intent:
        if not request.strip():
            raise ValueError("Intent analysis request cannot be empty")
        return self.intent


def test_intent_analyzer_boundary_returns_structured_intent():
    expected = Intent.create(
        goal="create_short_video",
        parameters={"duration": 30},
    )
    analyzer: IntentAnalyzer = FakeIntentAnalyzer(expected)

    result = analyzer.analyze("Create a 30 second video")

    assert result == expected


def test_intent_analyzer_boundary_rejects_empty_request():
    analyzer: IntentAnalyzer = FakeIntentAnalyzer(
        Intent.create(goal="create_short_video")
    )

    with pytest.raises(ValueError, match="Intent analysis request cannot be empty"):
        analyzer.analyze("   ")


def test_intent_analyzer_is_provider_neutral():
    expected = Intent.create(goal="publish_content")
    analyzer: IntentAnalyzer = FakeIntentAnalyzer(expected)

    assert analyzer.analyze("Publish this content") == expected
