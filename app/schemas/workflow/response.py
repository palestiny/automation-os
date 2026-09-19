from uuid import UUID

from pydantic import BaseModel


class WorkflowParameterResponse(BaseModel):
    name: str
    type: str


class WorkflowResponse(BaseModel):
    workflow_id: UUID
    name: str
    supported_goals: tuple[str, ...]
    required_parameters: tuple[str, ...]
    parameter_types: tuple[WorkflowParameterResponse, ...]
    automation_domain: str | None
    discovery_tags: tuple[str, ...]
