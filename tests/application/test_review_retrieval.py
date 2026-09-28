from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.application.authorization import AuthorizationContext, TenantId
from app.application.review_retrieval import (
    GetReviewableDraft,
    GetWorkflowReviewDecisions,
    ListReviewableDrafts,
)
from app.domain.review_decision import ReviewDecision, ReviewDecisionType
from app.domain.workflow import Workflow, WorkflowState, WorkflowStep


class WorkflowRepo:
    def __init__(self, workflows):
        self.items = {workflow.id: workflow for workflow in workflows}

    def all(self):
        return tuple(self.items.values())

    def get(self, workflow_id):
        return self.items.get(workflow_id)


class DecisionRepo:
    def __init__(self, decisions=()):
        self.items = tuple(decisions)

    def list_by_workflow(self, workflow_id):
        return tuple(
            decision for decision in self.items if decision.workflow_id == workflow_id
        )


def workflow(tenant_id, state=WorkflowState.DRAFT):
    item = Workflow.create(
        name="Reviewable workflow",
        steps=[
            WorkflowStep.create(
                name="Create video",
                capability="video.create",
            )
        ],
        supported_goals=["create_short_video"],
        tenant_id=tenant_id,
    )
    if state is WorkflowState.PUBLISHED:
        item.publish()
    return item


def context(tenant_id):
    return AuthorizationContext(
        principal_id="reviewer-1",
        tenant_id=TenantId(tenant_id),
    )


def test_list_reviewable_drafts_returns_only_drafts_for_tenant():
    tenant_id = uuid4()
    visible = workflow(tenant_id)
    published = workflow(tenant_id, WorkflowState.PUBLISHED)
    other = workflow(uuid4())

    result = ListReviewableDrafts(
        WorkflowRepo([visible, published, other])
    ).execute(context(tenant_id))

    assert result == (visible,)


def test_list_reviewable_drafts_requires_explicit_system_context_for_system_workflows():
    system_workflow = workflow(None)

    result = ListReviewableDrafts(
        WorkflowRepo([system_workflow])
    ).execute(AuthorizationContext.system("system-reviewer"))

    assert result == (system_workflow,)


def test_tenant_context_cannot_list_system_workflow():
    system_workflow = workflow(None)

    with pytest.raises(PermissionError):
        ListReviewableDrafts(
            WorkflowRepo([system_workflow])
        ).execute(context(uuid4()))


def test_get_reviewable_draft_enforces_tenant_boundary():
    workflow_item = workflow(uuid4())

    with pytest.raises(PermissionError):
        GetReviewableDraft(
            WorkflowRepo([workflow_item])
        ).execute(workflow_item.id, context(uuid4()))


def test_get_reviewable_draft_rejects_published_workflow():
    tenant_id = uuid4()
    published = workflow(tenant_id, WorkflowState.PUBLISHED)

    with pytest.raises(ValueError, match="DRAFT"):
        GetReviewableDraft(
            WorkflowRepo([published])
        ).execute(published.id, context(tenant_id))


def test_get_workflow_review_decisions_returns_immutable_evidence():
    tenant_id = uuid4()
    workflow_item = workflow(tenant_id)
    first = ReviewDecision.create(
        workflow_id=workflow_item.id,
        workflow_revision=workflow_item.review_revision,
        tenant_id=tenant_id,
        reviewer_principal_id="reviewer-1",
        decision=ReviewDecisionType.REJECTED,
        reason="Needs validation",
        idempotency_key="review-1",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    second = ReviewDecision.create(
        workflow_id=workflow_item.id,
        workflow_revision=workflow_item.review_revision,
        tenant_id=tenant_id,
        reviewer_principal_id="reviewer-2",
        decision=ReviewDecisionType.APPROVED,
        reason="Validated",
        idempotency_key="review-2",
        created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    result = GetWorkflowReviewDecisions(
        WorkflowRepo([workflow_item]),
        DecisionRepo([second, first]),
    ).execute(workflow_item.id, context(tenant_id))

    assert result == (first, second)
    assert all(
        decision.workflow_revision == workflow_item.review_revision
        for decision in result
    )


def test_get_workflow_review_decisions_does_not_expose_another_tenant():
    workflow_item = workflow(uuid4())
    decision = ReviewDecision.create(
        workflow_id=workflow_item.id,
        workflow_revision=workflow_item.review_revision,
        tenant_id=workflow_item.tenant_id,
        reviewer_principal_id="reviewer-1",
        decision=ReviewDecisionType.APPROVED,
        reason=None,
        idempotency_key="review-1",
    )

    with pytest.raises(PermissionError):
        GetWorkflowReviewDecisions(
            WorkflowRepo([workflow_item]),
            DecisionRepo([decision]),
        ).execute(workflow_item.id, context(uuid4()))


def test_system_context_can_read_system_workflow_decisions():
    workflow_item = workflow(None)
    decision = ReviewDecision.create(
        workflow_id=workflow_item.id,
        workflow_revision=workflow_item.review_revision,
        tenant_id=None,
        reviewer_principal_id="system-reviewer",
        decision=ReviewDecisionType.APPROVED,
        reason=None,
        idempotency_key="review-1",
    )

    result = GetWorkflowReviewDecisions(
        WorkflowRepo([workflow_item]),
        DecisionRepo([decision]),
    ).execute(
        workflow_item.id,
        AuthorizationContext.system("system-reviewer"),
    )

    assert result == (decision,)
