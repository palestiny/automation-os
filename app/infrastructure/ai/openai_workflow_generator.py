from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

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
    required_parameters: list[str] = []
    parameter_types: dict[str, str] = {}
    steps: list[_WorkflowStepPayload]
    triggers: list[str] = []
    automation_domain: str | None = None
    discovery_tags: list[str] = []


class OpenAIWorkflowGenerator:
    """OpenAI adapter implementing the provider-neutral WorkflowGenerator boundary."""

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
            "Return only the workflow definition requested by the structured schema. "
            "Do not invent executable provider code or runtime workflow/step identities. "
            "Capabilities must be expressed only as capability identity strings. "
            "Do not publish, execute, or mutate an existing workflow. "
            "The candidate will be validated and reviewed before publication. "
            "The generated workflow must contain at least one step."
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
        payload = response.output_parsed

        if payload is None:
            raise ValueError("AI provider returned no structured workflow candidate")

        return WorkflowCandidate.create(
            name=payload.name,
            supported_goals=payload.supported_goals,
            required_parameters=payload.required_parameters,
            parameter_types=payload.parameter_types,
            steps=[
                WorkflowCandidateStep.create(
                    name=step.name,
                    capability=step.capability,
                )
                for step in payload.steps
            ],
            triggers=payload.triggers,
            automation_domain=payload.automation_domain,
            discovery_tags=payload.discovery_tags,
        )
