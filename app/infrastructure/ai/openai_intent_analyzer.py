from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.application.intent_goal_catalog import IntentGoalCatalog
from app.infrastructure.provider import ProviderConfiguration
from app.domain.intent import Intent


class _IntentPayload(BaseModel):
    goal: str
    parameters: dict[str, object]


class OpenAIIntentAnalyzer:
    """OpenAI adapter implementing the provider-neutral IntentAnalyzer boundary."""

    def __init__(
        self,
        client: Any,
        configuration: ProviderConfiguration,
        goal_catalog: IntentGoalCatalog | None = None,
    ) -> None:
        if client is None:
            raise TypeError("client is required")
        if not isinstance(configuration, ProviderConfiguration):
            raise TypeError("configuration must be a ProviderConfiguration instance")
        if configuration.provider != "openai":
            raise ValueError("configuration provider must be openai")
        if goal_catalog is not None and not isinstance(goal_catalog, IntentGoalCatalog):
            raise TypeError("goal_catalog must be an IntentGoalCatalog instance")

        self._client = client
        self._configuration = configuration
        self._goal_catalog = goal_catalog

    def analyze(self, request: str) -> Intent:
        if not isinstance(request, str) or not request.strip():
            raise ValueError("request must be a non-empty string")

        kwargs = {
            "model": self._configuration.service,
            "input": request,
            "text_format": _IntentPayload,
        }

        if self._goal_catalog is not None:
            kwargs["instructions"] = (
                "Classify the request using exactly one canonical goal from this "
                f"catalog: {', '.join(self._goal_catalog.goals)}. "
                "Never invent a new goal."
            )

        response = self._client.responses.parse(**kwargs)
        payload = response.output_parsed

        if payload is None:
            raise ValueError("AI provider returned no structured intent")

        if (
            self._goal_catalog is not None
            and not self._goal_catalog.contains(payload.goal)
        ):
            raise ValueError("AI provider returned an unknown intent goal")

        return Intent.create(payload.goal, payload.parameters)
