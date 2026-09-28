from __future__ import annotations

from uuid import UUID

from app.application.authorization import AuthorizationContext
from app.application.workflow_draft_review import _authorize_workflow
from app.domain.review_decision import ReviewDecision
from app.domain.workflow import Workflow


class ListWorkflowReviewDecisions:
    """Read immutable review-decision evidence for an authorized workflow."""

    def __init__(self, workflow_repository, review_decision_repository) -> None:
        if not hasattr(workflow_repository, "get"):
            raise TypeError("workflow_repository must provide get(workflow_id)")
        if not hasattr(review_decision_repository, "list_by_workflow_id"):
            raise TypeError(
                "review_decision_repository must provide list_by_workflow_id(workflow_id)"
            )
        self._workflow_repository = workflow_repository
        self._review_decision_repository = review_decision_repository

    def execute(
        self,
        workflow_id: UUID,
        context: AuthorizationContext,
    ) -> tuple[ReviewDecision, ...]:
        if not isinstance(workflow_id, UUID):
            raise TypeError("workflow_id must be a UUID")
        if not isinstance(context, AuthorizationContext):
            raise TypeError("context must be an AuthorizationContext")

        workflow = self._workflow_repository.get(workflow_id)
        if workflow is None:
            raise LookupError("Workflow not found")
        if not isinstance(workflow, Workflow):
            raise TypeError("workflow repository returned an invalid Workflow")

        _authorize_workflow(context, workflow)

        decisions = self._review_decision_repository.list_by_workflow_id(workflow.id)
        if any(not isinstance(item, ReviewDecision) for item in decisions):
            raise TypeError(
                "review decision repository returned an invalid ReviewDecision"
            )

        return tuple(sorted(decisions, key=lambda item: (item.created_at, item.id)))
