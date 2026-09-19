from __future__ import annotations

from app.application.intent_analysis import IntentAnalyzer
from app.application.intent_execution import ExecuteIntent, IntentExecutionResult
from app.application.intent_validation import ValidateIntent


class ExecuteRequest:
    """Application entry point from a raw request to workflow execution."""

    def __init__(
        self,
        analyzer: IntentAnalyzer,
        execute_intent: ExecuteIntent,
        validate_intent: ValidateIntent | None = None,
    ) -> None:
        if analyzer is None:
            raise TypeError("analyzer is required")
        if not isinstance(execute_intent, ExecuteIntent):
            raise TypeError("execute_intent must be an ExecuteIntent instance")
        if validate_intent is not None and not isinstance(validate_intent, ValidateIntent):
            raise TypeError("validate_intent must be a ValidateIntent instance")

        self._analyzer = analyzer
        self._execute_intent = execute_intent
        self._validate_intent = validate_intent

    def execute(self, request: str) -> IntentExecutionResult:
        intent = self._analyzer.analyze(request)
        if self._validate_intent is not None:
            intent = self._validate_intent.execute(intent)
        return self._execute_intent.execute(intent)
