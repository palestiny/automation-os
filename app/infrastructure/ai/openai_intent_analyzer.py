from __future__ import annotations

from typing import Any

from app.domain.intent import Intent


class OpenAIIntentAnalyzer:
    """OpenAI adapter implementing the provider-neutral IntentAnalyzer boundary."""

    def __init__(self, client: Any, model: str) -> None:
        if client is None:
            raise TypeError("client is required")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model must be a non-empty string")

        self._client = client
        self._model = model.strip()

    def analyze(self, request: str) -> Intent:
        response = self._client.responses.parse(
            model=self._model,
            input=request,
            text_format=_IntentPayload,
        )
        payload = response.output_parsed

        if payload is None:
            raise ValueError("AI provider returned no structured intent")

        return Intent.create(payload.goal, payload.parameters)


class _IntentPayload:
    """Pydantic schema is attached lazily to keep the application boundary provider-neutral."""

    goal: str
    parameters: dict[str, object]

    def __init__(self, goal: str, parameters: dict[str, object]) -> None:
        self.goal = goal
        self.parameters = parameters
