from __future__ import annotations

from app.application.intent_analysis import IntentAnalyzer


class IntentAnalyzerRegistry:
    """Deterministic registry for configured IntentAnalyzer implementations."""

    def __init__(self) -> None:
        self._analyzers: dict[str, IntentAnalyzer] = {}

    def register(self, identifier: str, analyzer: IntentAnalyzer) -> None:
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError("Intent analyzer identifier must be a non-empty string")
        if identifier in self._analyzers:
            raise ValueError(f"Intent analyzer already registered: {identifier}")
        if not isinstance(analyzer, IntentAnalyzer):
            raise TypeError("analyzer must implement IntentAnalyzer")
        self._analyzers[identifier] = analyzer

    def resolve(self, identifier: str) -> IntentAnalyzer:
        if identifier not in self._analyzers:
            raise KeyError(f"Unknown intent analyzer: {identifier}")
        return self._analyzers[identifier]
