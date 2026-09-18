from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.domain.intent import Intent


class _IntentPayload(BaseModel):
    goal: str
    parameters: dict[str, object]


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
        if not isinstance(request, str) or not request.strip():
            raise ValueError("request must be a non-empty string")

        response = self._client.responses.parse(
            model=self._model,
            input=request,
            text_format=_IntentPayload,
        )
        payload = response.output_parsed

        if payload is None:
            raise ValueError("AI provider returned no structured intent")

        return Intent.create(payload.goal, payload.parameters)
