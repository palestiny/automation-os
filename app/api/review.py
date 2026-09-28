from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.application.authorization import AuthorizationContext
from app.application.review_retrieval import (
    GetReviewableDraft,
    GetWorkflowReviewDecisions,
    ListReviewableDrafts,
)
from app.application.review_workflow import ApproveWorkflow, RejectWorkflow
from app.core.execution_dependencies import build_review_repositories
from app.schemas.review.request import ReviewDecisionRequest
from app.schemas.review.response import (
    ReviewDecisionResponse,
    WorkflowConditionResponse,
    WorkflowParameterReviewResponse,
    WorkflowReviewResponse,
    WorkflowStepReviewResponse,
)

router = APIRouter(prefix="/review/workflows", tags=["workflow-review"])


def get_authorization_context() -> AuthorizationContext:
    """Trusted authentication adapter seam.

    The HTTP layer must receive identity from trusted authentication middleware.
    Client-controlled tenant/principal/system headers are intentionally unsupported.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Authorization context provider is not configured",
    )


def _workflow_response(workflow) -> WorkflowReviewResponse:
    return WorkflowReviewResponse(
        workflow_id=workflow.id,
        name=workflow.name,
        state=workflow.state,
        tenant_id=workflow.tenant_id,
        review_revision=workflow.review_revision,
        steps=tuple(
            WorkflowStepReviewResponse(
                id=step.id,
                name=step.name,
                capability=step.capability,
                condition=(
                    WorkflowConditionResponse(
                        left_operand=step.condition.left_operand,
                        operator=step.condition.operator,
                        right_operand=step.condition.right_operand,
                    )
                    if step.condition is not None
                    else None
                ),
            )
            for step in workflow.steps
        ),
        triggers=tuple(trigger.event_type for trigger in workflow.triggers),
        supported_goals=workflow.supported_goals,
        required_parameters=workflow.required_parameters,
        parameter_types=tuple(
            WorkflowParameterReviewResponse(
                name=parameter.name,
                type=parameter.type,
            )
            for parameter in workflow.parameter_types
        ),
        automation_domain=workflow.automation_domain,
        discovery_tags=workflow.discovery_tags,
    )


def _decision_response(decision) -> ReviewDecisionResponse:
    return ReviewDecisionResponse(
        decision_id=decision.id,
        workflow_id=decision.workflow_id,
        workflow_revision=decision.workflow_revision,
        tenant_id=decision.tenant_id,
        reviewer_principal_id=decision.reviewer_principal_id,
        decision=decision.decision,
        reason=decision.reason,
        idempotency_key=decision.idempotency_key,
        created_at=decision.created_at,
    )


def _map_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, LookupError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, RuntimeError):
        return HTTPException(status_code=503, detail=str(exc))
    raise TypeError("Unsupported review API exception mapping") from exc


@router.get("", response_model=list[WorkflowReviewResponse])
def list_reviewable_workflows(
    context: AuthorizationContext = Depends(get_authorization_context),
):
    try:
        workflow_repository, _ = build_review_repositories(context)
        workflows = ListReviewableDrafts(workflow_repository).execute(context)
        return [_workflow_response(workflow) for workflow in workflows]
    except (PermissionError, LookupError, ValueError, RuntimeError) as exc:
        raise _map_error(exc) from exc


@router.get("/{workflow_id}", response_model=WorkflowReviewResponse)
def get_reviewable_workflow(
    workflow_id: UUID,
    context: AuthorizationContext = Depends(get_authorization_context),
):
    try:
        workflow_repository, _ = build_review_repositories(context)
        workflow = GetReviewableDraft(workflow_repository).execute(
            workflow_id,
            context,
        )
        return _workflow_response(workflow)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.get(
    "/{workflow_id}/decisions",
    response_model=list[ReviewDecisionResponse],
)
def get_review_decisions(
    workflow_id: UUID,
    context: AuthorizationContext = Depends(get_authorization_context),
):
    try:
        workflow_repository, review_decision_repository = build_review_repositories(
            context
        )
        decisions = GetWorkflowReviewDecisions(
            workflow_repository,
            review_decision_repository,
        ).execute(workflow_id, context)
        return [_decision_response(decision) for decision in decisions]
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post(
    "/{workflow_id}/approve",
    response_model=ReviewDecisionResponse,
)
def approve_reviewable_workflow(
    workflow_id: UUID,
    request: ReviewDecisionRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    context: AuthorizationContext = Depends(get_authorization_context),
):
    try:
        workflow_repository, review_decision_repository = build_review_repositories(
            context
        )
        decision = ApproveWorkflow(
            workflow_repository,
            review_decision_repository,
        ).execute(
            workflow_id,
            context,
            idempotency_key=idempotency_key,
            expected_revision=request.expected_revision,
            reason=request.reason,
        )
        return _decision_response(decision)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post(
    "/{workflow_id}/reject",
    response_model=ReviewDecisionResponse,
)
def reject_reviewable_workflow(
    workflow_id: UUID,
    request: ReviewDecisionRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    context: AuthorizationContext = Depends(get_authorization_context),
):
    try:
        workflow_repository, review_decision_repository = build_review_repositories(
            context
        )
        decision = RejectWorkflow(
            workflow_repository,
            review_decision_repository,
        ).execute(
            workflow_id,
            context,
            idempotency_key=idempotency_key,
            expected_revision=request.expected_revision,
            reason=request.reason,
        )
        return _decision_response(decision)
    except Exception as exc:
        raise _map_error(exc) from exc
