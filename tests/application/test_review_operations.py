from __future__ import annotations

from uuid import uuid4

import pytest

from app.application.authorization import AuthorizationContext, AuthorizationDeniedError, TenantId
from app.application.review_queries import (
    ListReviewableDrafts,
    ListWorkflowReviewDecisions,
)
from app.domain.review_decision import ReviewDecision, ReviewDecisionType
from app.domain.workflow import Workflow, WorkflowStep


class WorkflowRepository:
    def __init__(self, workflows: list[Workflow]) -> None:
        self._items = {workflow.id: workflow for workflow in workflows}

    def all(self):
        return tuple(self._items.values())

    def get(self, workflow_id):
        return self._items.get(workflow_id)


class ReviewDecisionRepository:
    def __init__(self, decisions: list[ReviewDecision]) -> None:
        self._items = decisions

    def list_by_workflow_id(self, workflow_id):
        return tuple(
            decision
            for decision in self._items
            if decision.workflow_id == workflow_id
        )


def workflow(*, tenant_id=None, published=False) -> Workflow:
    item = Workflow.create(
        name="Reviewable workflow",
        steps=[WorkflowStep.create(name="Step", capability="test.capability")],
        tenant_id=tenant_id,
    )
    if published:
        item.publish()
    return item


def context(tenant_id) -> AuthorizationContext:
    return AuthorizationContext(
        principal_id="reviewer-1",
        tenant_id=TenantId(tenant_id),
    )


def test_lists_only_drafts_in_authorized_tenant():
    tenant_a = uuid4()
    tenant_b = uuid4()
    draft_a = workflow(tenant_id=tenant_a)
    draft_b = workflow(tenant_id=tenant_b)
    published_a = workflow(tenant_id=tenant_a, published=True)

    result = ListReviewableDrafts(
        WorkflowRepository([draft_a, draft_b, published_a])
    ).execute(context(tenant_a))

    assert result == (draft_a,)


def test_list_reviewable_drafts_rejects_wrong_tenant_context():
    tenant_a = uuid4()
    tenant_b = uuid4()
    draft = workflow(tenant_id=tenant_a)

    with pytest.raises(AuthorizationDeniedError):
        ListReviewableDrafts(WorkflowRepository([draft])).execute(
            context(tenant_b)
        )


def test_system_review_context_can_list_system_drafts_but_not_tenantless_by_inference():
    system_draft = workflow(tenant_id=None)
    tenant_draft = workflow(tenant_id=uuid4())

    result = ListReviewableDrafts(
        WorkflowRepository([system_draft, tenant_draft])
    ).execute(AuthorizationContext.system("system-reviewer"))

    assert result == (system_draft,)


def test_review_decisions_are_read_only_and_ordered():
    workflow_id = uuid4()
    first = ReviewDecision.create(
        workflow_id=workflow_id,
        workflow_revision="a" * 64,
        tenant_id=None,
        reviewer_principal_id="reviewer-1",
        decision=ReviewDecisionType.APPROVED,
        reason="Looks valid",
        idempotency_key="key-1",
    )
    second = ReviewDecision.create(
        workflow_id=workflow_id,
        workflow_revision="b" * 64,
        tenant_id=None,
        reviewer_principal_id="reviewer-2",
        decision=ReviewDecisionType.REJECTED,
        reason="Invalid output",
        idempotency_key="key-2",
    )

    result = ListWorkflowReviewDecisions(
        WorkflowRepository([workflow(tenant_id=None)]),
        ReviewDecisionRepository([second, first]),
    ).execute(
        workflow_id,
        AuthorizationContext.system("system-reviewer"),
    )

    assert result == (first, second)
