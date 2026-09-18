import pytest

from app.application.intent_analysis_result import (
    IntentAnalysisResult,
    IntentAnalysisStatus,
)
from app.domain.intent import Intent


def test_analyzed_result_contains_intent():
    intent = Intent.create("create_short_video", {"source": "video"})

    result = IntentAnalysisResult.analyzed(intent)

    assert result.status == IntentAnalysisStatus.ANALYZED
    assert result.intent == intent
    assert result.error is None


def test_failed_result_contains_error():
    result = IntentAnalysisResult.failed("provider unavailable")

    assert result.status == IntentAnalysisStatus.FAILED
    assert result.intent is None
    assert result.error == "provider unavailable"


def test_analyzed_requires_intent():
    with pytest.raises(TypeError):
        IntentAnalysisResult.analyzed(None)


def test_failed_requires_non_empty_error():
    with pytest.raises(ValueError):
        IntentAnalysisResult.failed("")


def test_result_is_immutable():
    result = IntentAnalysisResult.failed("error")

    with pytest.raises(AttributeError):
        result.status = IntentAnalysisStatus.ANALYZED
