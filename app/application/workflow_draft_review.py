from __future__ import annotations

from uuid import UUID

from app.application.authorization import (
    AuthorizationContext,
    AuthorizationPolicy,
    TenantId,
)
from app.domain.workflow import Workflow, WorkflowState


def _authorize_workflow(context: AuthorizationContext, workflow: Workflow) -> None:
    if workflow.tenant_id is None:
        AuthorizationPolicy.require_system(context)
        return
    AuthorizationPolicy.require_tenant(context, TenantId(workflow.tenant_id))


class GetDraftWorkflowForReview:
    """Retrieve one persisted DRAFT workflow inside the explicit authorization boundary."""

    def __init__(self, workflow_repository) -> None:
        if not hasattr(workflow_repository, "get"):
            raise TypeError("workflow_repository must provide a get(workflow_id) method")
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

        _authorize_workflow(context, workflow)
        return workflow


class ListReviewableDrafts:
    """List persisted DRAFT workflows visible to the explicit authorization context."""

    def __init__(self, workflow_repository) -> None:
        if not hasattr(workflow_repository, "all"):
            raise TypeError("workflow_repository must provide an all() method")
        self._workflow_repository = workflow_repository

    def execute(self, context: AuthorizationContext) -> tuple[Workflow, ...]:
        if not isinstance(context, AuthorizationContext):
            raise TypeError("context must be an AuthorizationContext")

        result: list[Workflow] = []
        for workflow in self._workflow_repository.all():
            if not isinstance(workflow, Workflow):
                raise TypeError("workflow repository returned an invalid Workflow")
            if workflow.state is not WorkflowState.DRAFT:
                continue
            _authorize_workflow(context, workflow)
            result.append(workflow)

        return tuple(sorted(result, key=lambda item: item.id))
