from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.review_decision import ReviewDecisionType
from app.domain.workflow import WorkflowState


class WorkflowConditionResponse(BaseModel):
    left_operand: str
    operator: str
    right_operand: object


class WorkflowStepReviewResponse(BaseModel):
    id: UUID
    name: str
    capability: str
    condition: WorkflowConditionResponse | None


class WorkflowParameterReviewResponse(BaseModel):
    name: str
    type: str


class WorkflowReviewResponse(BaseModel):
    workflow_id: UUID
    name: str
    state: WorkflowState
    tenant_id: UUID | None
    review_revision: str
    steps: tuple[WorkflowStepReviewResponse, ...]
    triggers: tuple[str, ...]
    supported_goals: tuple[str, ...]
    required_parameters: tuple[str, ...]
    parameter_types: tuple[WorkflowParameterReviewResponse, ...]
    automation_domain: str | None
    discovery_tags: tuple[str, ...]


class ReviewDecisionRequest(BaseModel):
    expected_revision: str
    reason: str | None = None


class ReviewDecisionResponse(BaseModel):
    decision_id: UUID
    workflow_id: UUID
    workflow_revision: str
    tenant_id: UUID | None
    reviewer_principal_id: str
    decision: ReviewDecisionType
    reason: str | None
    idempotency_key: str
    created_at: datetime
