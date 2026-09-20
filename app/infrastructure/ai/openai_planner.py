from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from app.application.ai_planning import (
    PlanProposal,
    PlannerPort,
    PlanningRequest,
    PlanningStatus,
)
from app.infrastructure.provider import ProviderConfiguration


class _PlanPayload(BaseModel):
    status: PlanningStatus
    workflow_version_id: str | None = None
    parameters: dict[str, object] = {}
    details: list[str] = []


class OpenAIPlanner:
    """OpenAI adapter implementing the provider-neutral PlannerPort."""

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

    def plan(self, request: PlanningRequest) -> PlanProposal:
        candidates = [
            {
                "workflow_version_id": str(candidate.workflow_version_id),
                "name": candidate.name,
                "supported_goals": list(candidate.supported_goals),
                "required_parameters": list(candidate.required_parameters),
                "parameter_types": [
                    {"name": name, "type": parameter_type}
                    for name, parameter_type in candidate.parameter_types
                ],
            }
            for candidate in request.candidates
        ]

        instructions = (
            "Propose a plan using only one of the supplied published workflow "
            "version candidates. Never invent a workflow_version_id. "
            "If required information is missing, return clarification_required. "
            "If no candidate can satisfy the intent, return no_plan. "
            "Do not start execution. "
            f"Candidates: {json.dumps(candidates, sort_keys=True)}"
        )

        response = self._client.responses.parse(
            model=self._configuration.service,
            input=json.dumps(
                {
                    "goal": request.intent.goal,
                    "parameters": dict(request.intent.parameters),
                },
                sort_keys=True,
            ),
            instructions=instructions,
            text_format=_PlanPayload,
        )
        payload = response.output_parsed

        if payload is None:
            raise ValueError("AI provider returned no structured plan")

        if payload.status is PlanningStatus.PLANNED:
            if payload.workflow_version_id is None:
                raise ValueError(
                    "AI provider returned a planned result without a workflow version"
                )
            try:
                from uuid import UUID

                workflow_version_id = UUID(payload.workflow_version_id)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "AI provider returned an invalid workflow version id"
                ) from exc

            return PlanProposal.planned(
                workflow_version_id=workflow_version_id,
                parameters=payload.parameters,
            )

        if payload.status is PlanningStatus.CLARIFICATION_REQUIRED:
            return PlanProposal.clarification_required(
                details=tuple(payload.details)
            )

        if payload.status is PlanningStatus.NO_PLAN:
            return PlanProposal.no_plan(
                reason=payload.details[0]
                if payload.details
                else "No suitable published workflow",
            )

        raise ValueError(
            f"AI provider returned unsupported planning status: {payload.status.value}"
        )
