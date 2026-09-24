from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from app.application.workflow_generation import WorkflowCandidate, WorkflowCandidateStep
from app.application.workflow_generator import WorkflowGenerator
from app.domain.intent import Intent
from app.infrastructure.provider import ProviderConfiguration


class _WorkflowStepPayload(BaseModel):
    name: str
    capability: str


class _WorkflowPayload(BaseModel):
    name: str
    supported_goals: list[str]
    required_parameters: list[str] = Field(default_factory=list)
    parameter_types: dict[str, str] = Field(default_factory=dict)
    steps: list[_WorkflowStepPayload]
    triggers: list[str] = Field(default_factory=list)
    automation_domain: str | None = None
    discovery_tags: list[str] = Field(default_factory=list)


class OpenAIWorkflowGenerator:
    """OpenAI adapter implementing the provider-neutral WorkflowGenerator."""

    def __init__(
        self,
        client: Any,
        configuration: ProviderConfiguration,
    ) -> None:
        if client is None:
            raise TypeError("client is required")
        if not isinstance(configuration, ProviderConfiguration):
            raise TypeError("configuration must be a ProviderConfiguration instance")
        if configuration.provider != "openai":
            raise ValueError("configuration provider must be openai")

        self._client = client
        self._configuration = configuration

    def generate(self, intent: Intent) -> WorkflowCandidate:
        if not isinstance(intent, Intent):
            raise TypeError("intent must be an Intent instance")

        instructions = (
            "Generate one provider-neutral workflow candidate for the supplied intent. "
            "Return only the workflow structure. Do not publish, execute, or mutate "
            "existing workflows. Capabilities must be identities, not provider code. "
            f"Intent: {json.dumps({'goal': intent.goal, 'parameters': dict(intent.parameters)}, sort_keys=True)}"
        )

        response = self._client.responses.parse(
            model=self._configuration.service,
            input=json.dumps(
                {
                    "goal": intent.goal,
                    "parameters": dict(intent.parameters),
                },
                sort_keys=True,
            ),
            instructions=instructions,
            text_format=_WorkflowPayload,
        )
        raw_payload = response.output_parsed

        if raw_payload is None:
            raise ValueError("AI provider returned no structured workflow candidate")

        payload = _WorkflowPayload.model_validate(raw_payload)

        steps = [
            WorkflowCandidateStep.create(
                name=step.name,
                capability=step.capability,
            )
            for step in payload.steps
        ]

        return WorkflowCandidate.create(
            name=payload.name,
            supported_goals=payload.supported_goals,
            required_parameters=payload.required_parameters,
            parameter_types=payload.parameter_types,
            steps=steps,
            triggers=payload.triggers,
            automation_domain=payload.automation_domain,
            discovery_tags=payload.discovery_tags,
        )
