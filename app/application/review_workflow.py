from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.application.authorization import (
    AuthorizationContext,
    AuthorizationDeniedError,
    AuthorizationPolicy,
    TenantId,
)
from app.domain.review_decision import ReviewDecision, ReviewDecisionType
from app.domain.workflow import Workflow, WorkflowState


class StaleWorkflowReviewError(ValueError):
    """The workflow changed after the reviewer inspected it."""


class _ReviewWorkflow:
    decision_type: ReviewDecisionType

    def __init__(self, workflow_repository, review_decision_repository, *, clock=None) -> None:
        if not hasattr(workflow_repository, "get"):
            raise TypeError("workflow_repository must provide get(workflow_id)")
        if not hasattr(review_decision_repository, "save_idempotent"):
            raise TypeError(
                "review_decision_repository must provide save_idempotent(decision)"
            )
        self._workflow_repository = workflow_repository
        self._review_decision_repository = review_decision_repository
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def execute(
        self,
        workflow_id: UUID,
        context: AuthorizationContext,
        *,
        idempotency_key: str,
        expected_revision: str,
        reason: str | None = None,
    ) -> ReviewDecision:
        if not isinstance(workflow_id, UUID):
            raise TypeError("workflow_id must be a UUID")
        if not isinstance(context, AuthorizationContext):
            raise TypeError("context must be an AuthorizationContext")
        if not idempotency_key.strip():
            raise ValueError("idempotency_key cannot be empty")
        if not isinstance(expected_revision, str) or len(expected_revision) != 64:
            raise ValueError("expected_revision must be a SHA-256 hex digest")

        workflow = self._workflow_repository.get(workflow_id)
        if workflow is None:
            raise LookupError("Workflow not found")
        if not isinstance(workflow, Workflow):
            raise TypeError("workflow repository returned an invalid Workflow")
        if workflow.state is not WorkflowState.DRAFT:
            raise ValueError("Workflow is not in DRAFT state")

        self._authorize(context, workflow)

        existing = self._find_existing(idempotency_key)
        if existing is not None:
            if not self._same_request(existing, workflow, context, expected_revision, reason):
                raise ValueError(
                    "Review decision idempotency key conflicts with the original request"
                )
            return existing

        actual_revision = workflow.review_revision
        if expected_revision != actual_revision:
            raise StaleWorkflowReviewError(
                "Workflow changed after the review target was inspected"
            )

        decision = ReviewDecision.create(
            workflow_id=workflow.id,
            workflow_revision=actual_revision,
            tenant_id=workflow.tenant_id,
            reviewer_principal_id=context.principal_id,
            decision=self.decision_type,
            reason=reason,
            idempotency_key=idempotency_key,
            created_at=self._clock(),
        )

        persisted, created = self._review_decision_repository.save_idempotent(decision)
        if not isinstance(persisted, ReviewDecision):
            raise TypeError("review decision repository returned an invalid ReviewDecision")
        if created:
            return persisted

        if not self._same_request(persisted, workflow, context, expected_revision, reason):
            raise ValueError(
                "Review decision idempotency key conflicts with the original request"
            )
        return persisted

    @staticmethod
    def _authorize(context: AuthorizationContext, workflow: Workflow) -> None:
        if workflow.tenant_id is None:
            if not context.is_system:
                raise AuthorizationDeniedError(
                    "System authorization is required for legacy/system workflow review"
                )
            AuthorizationPolicy.require_system(context)
            return

        AuthorizationPolicy.require_tenant(
            context,
            TenantId(workflow.tenant_id),
        )

    def _same_request(
        self,
        existing: ReviewDecision,
        workflow: Workflow,
        context: AuthorizationContext,
        expected_revision: str,
        reason: str | None,
    ) -> bool:
        normalized_reason = reason.strip() if reason is not None else None
        return (
            existing.workflow_id == workflow.id
            and existing.workflow_revision == expected_revision
            and existing.tenant_id == workflow.tenant_id
            and existing.reviewer_principal_id == context.principal_id
            and existing.decision is self.decision_type
            and existing.reason == normalized_reason
        )

    def _find_existing(self, idempotency_key: str) -> ReviewDecision | None:
        repository = self._review_decision_repository
        getter = getattr(repository, "get_by_idempotency_key", None)
        if getter is None:
            return None
        result = getter(idempotency_key.strip())
        if result is not None and not isinstance(result, ReviewDecision):
            raise TypeError(
                "review decision repository returned an invalid ReviewDecision"
            )
        return result


class ApproveWorkflow(_ReviewWorkflow):
    decision_type = ReviewDecisionType.APPROVED


class RejectWorkflow(_ReviewWorkflow):
    decision_type = ReviewDecisionType.REJECTED
