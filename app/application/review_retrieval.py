from __future__ import annotations

from uuid import UUID

from app.application.authorization import (
    AuthorizationContext,
    AuthorizationPolicy,
    TenantId,
)
from app.domain.review_decision import ReviewDecision
from app.domain.workflow import Workflow, WorkflowState


class ListReviewableDrafts:
    """List persisted DRAFT workflows visible to the explicit authorization context."""

    def __init__(self, workflow_repository) -> None:
        if not hasattr(workflow_repository, "all"):
            raise TypeError("workflow_repository must provide all()")
        self._workflow_repository = workflow_repository

    def execute(self, context: AuthorizationContext) -> tuple[Workflow, ...]:
        self._validate_context(context)

        workflows = self._workflow_repository.all()
        if any(not isinstance(workflow, Workflow) for workflow in workflows):
            raise TypeError("workflow repository returned an invalid Workflow")

        result = []
        for workflow in workflows:
            if workflow.state is not WorkflowState.DRAFT:
                continue
            self._authorize(context, workflow)
            result.append(workflow)

        return tuple(sorted(result, key=lambda workflow: workflow.id))

    @staticmethod
    def _validate_context(context: AuthorizationContext) -> None:
        if not isinstance(context, AuthorizationContext):
            raise TypeError("context must be an AuthorizationContext")

    @staticmethod
    def _authorize(context: AuthorizationContext, workflow: Workflow) -> None:
        if workflow.tenant_id is None:
            if not context.is_system:
                raise PermissionError(
                    "System authorization is required for system workflow review"
                )
            AuthorizationPolicy.require_system(context)
            return

        AuthorizationPolicy.require_tenant(context, TenantId(workflow.tenant_id))


class GetReviewableDraft:
    """Retrieve one DRAFT workflow after explicit review authorization."""

    def __init__(self, workflow_repository) -> None:
        if not hasattr(workflow_repository, "get"):
            raise TypeError("workflow_repository must provide get(workflow_id)")
        self._workflow_repository = workflow_repository

    def execute(
        self,
        workflow_id: UUID,
        context: AuthorizationContext,
    ) -> Workflow:
        if not isinstance(workflow_id, UUID):
            raise TypeError("workflow_id must be a UUID")
        if not isinstance(context, AuthorizationContext):
            raise TypeError("context must be an AuthorizationContext")

        workflow = self._workflow_repository.get(workflow_id)
        if workflow is None:
            raise LookupError("Workflow not found")
        if not isinstance(workflow, Workflow):
            raise TypeError("workflow repository returned an invalid Workflow")
        if workflow.state is not WorkflowState.DRAFT:
            raise ValueError("Workflow is not in DRAFT state")

        ListReviewableDrafts._authorize(context, workflow)
        return workflow


class GetWorkflowReviewDecisions:
    """Read-only retrieval of immutable review decisions for one workflow."""

    def __init__(self, workflow_repository, review_decision_repository) -> None:
        if not hasattr(workflow_repository, "get"):
            raise TypeError("workflow_repository must provide get(workflow_id)")
        if not hasattr(review_decision_repository, "list_by_workflow"):
            raise TypeError(
                "review_decision_repository must provide list_by_workflow(workflow_id)"
            )
        self._workflow_repository = workflow_repository
        self._review_decision_repository = review_decision_repository

    def execute(
        self,
        workflow_id: UUID,
        context: AuthorizationContext,
    ) -> tuple[ReviewDecision, ...]:
        workflow = GetReviewableDraft(self._workflow_repository).execute(
            workflow_id,
            context,
        )

        decisions = self._review_decision_repository.list_by_workflow(workflow.id)
        if any(not isinstance(decision, ReviewDecision) for decision in decisions):
            raise TypeError(
                "review decision repository returned an invalid ReviewDecision"
            )

        return tuple(
            sorted(decisions, key=lambda decision: (decision.created_at, decision.id))
        )
