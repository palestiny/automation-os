from __future__ import annotations

from app.application.intent_analysis import IntentAnalyzer
from app.application.intent_validation import ValidateIntent
from app.application.intent_execution import ExecuteIntent, IntentExecutionResult


class ExecuteRequest:
    """Application entry point from a raw request to workflow execution."""

    def __init__(
        self,
        analyzer: IntentAnalyzer,
        execute_intent: ExecuteIntent,
    ) -> None:
        if analyzer is None:
            raise TypeError("analyzer is required")
        if not isinstance(execute_intent, ExecuteIntent):
            raise TypeError("execute_intent must be an ExecuteIntent instance")

        self._analyzer = analyzer
        self._execute_intent = execute_intent
        self._validate_intent = validate_intent

    def execute(self, request: str) -> IntentExecutionResult:
        intent = self._analyzer.analyze(request)
        if self._validate_intent is not None:
            intent = self._validate_intent.execute(intent)
        return self._execute_intent.execute(intent)
