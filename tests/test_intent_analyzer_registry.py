from unittest.mock import Mock

import pytest

from app.application.intent_analyzer_registry import IntentAnalyzerRegistry
from app.application.intent_analysis import IntentAnalyzer


def test_registry_registers_and_resolves_analyzer():
    analyzer = Mock()
    registry = IntentAnalyzerRegistry()
    registry.register("openai", analyzer)
    assert registry.resolve("openai") is analyzer
    assert isinstance(registry.resolve("openai"), IntentAnalyzer)


def test_registry_rejects_duplicate_identifier():
    analyzer = Mock()
    registry = IntentAnalyzerRegistry()
    registry.register("openai", analyzer)
    with pytest.raises(ValueError, match="already registered"):
        registry.register("openai", analyzer)


def test_registry_rejects_unknown_identifier():
    registry = IntentAnalyzerRegistry()
    with pytest.raises(KeyError, match="Unknown"):
        registry.resolve("missing")


def test_registry_rejects_empty_identifier():
    registry = IntentAnalyzerRegistry()
    with pytest.raises(ValueError, match="non-empty"):
        registry.register("", Mock())
