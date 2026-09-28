from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.application.authorization import AuthorizationContext, TenantId
from app.application.review_workflow import (
    ApproveWorkflow,
    RejectWorkflow,
    StaleWorkflowReviewError,
)
from app.domain.workflow import Workflow, WorkflowStep


class InMemoryWorkflowRepository:
    def __init__(self, workflows=None):
        self._workflows = {workflow.id: workflow for workflow in (workflows or [])}

    def get(self, workflow_id):
        return self._workflows.get(workflow_id)

    def save(self, workflow):
        self._workflows[workflow.id] = workflow


class InMemoryReviewDecisionRepository:
    def __init__(self):
        self.decisions = []

    def save_idempotent(self, decision):
        for existing in self.decisions:
            if existing.idempotency_key == decision.idempotency_key:
                return existing, False
        self.decisions.append(decision)
        return decision, True


def draft_workflow(tenant_id):
    return Workflow.create(
        name="Generated draft",
        steps=[
            WorkflowStep.create(
                name="Create video",
                capability="video.create",
            )
        ],
        supported_goals=["create_short_video"],
        tenant_id=tenant_id,
    )


def tenant_context(tenant_id):
    return AuthorizationContext(
        principal_id="reviewer-1",
        tenant_id=TenantId(tenant_id),
    )


def test_approval_records_decision_without_publishing():
    tenant_id = uuid4()
    workflow = draft_workflow(tenant_id)
    workflows = InMemoryWorkflowRepository([workflow])
    decisions = InMemoryReviewDecisionRepository()

    result = ApproveWorkflow(workflows, decisions, clock=lambda: datetime.now(timezone.utc)).execute(
        workflow.id,
        tenant_context(tenant_id),
        idempotency_key="review-1",
        reason="Validated",
    )

    assert result.decision.value == "approved"
    assert result.workflow_id == workflow.id
    assert result.workflow_revision == workflow.review_revision
    assert workflow.state.value == "draft"
    assert len(decisions.decisions) == 1


def test_rejection_preserves_workflow_content():
    tenant_id = uuid4()
    workflow = draft_workflow(tenant_id)
    original_revision = workflow.review_revision
    workflows = InMemoryWorkflowRepository([workflow])
    decisions = InMemoryReviewDecisionRepository()

    result = RejectWorkflow(workflows, decisions, clock=lambda: datetime.now(timezone.utc)).execute(
        workflow.id,
        tenant_context(tenant_id),
        idempotency_key="review-1",
        reason="Missing validation",
    )

    assert result.decision.value == "rejected"
    assert workflow.state.value == "draft"
    assert workflow.review_revision == original_revision


def test_stale_review_target_cannot_be_approved():
    tenant_id = uuid4()
    workflow = draft_workflow(tenant_id)
    workflows = InMemoryWorkflowRepository([workflow])
    decisions = InMemoryReviewDecisionRepository()
    use_case = ApproveWorkflow(
        workflows,
        decisions,
        clock=lambda: datetime.now(timezone.utc),
    )

    expected_revision = workflow.review_revision
    workflow.add_step(
        WorkflowStep.create(
            name="Publish video",
            capability="video.publish",
        )
    )

    with pytest.raises(StaleWorkflowReviewError):
        use_case.execute(
            workflow.id,
            tenant_context(tenant_id),
            idempotency_key="review-1",
            expected_revision=expected_revision,
        )


def test_exact_replay_is_idempotent():
    tenant_id = uuid4()
    workflow = draft_workflow(tenant_id)
    workflows = InMemoryWorkflowRepository([workflow])
    decisions = InMemoryReviewDecisionRepository()
    use_case = ApproveWorkflow(
        workflows,
        decisions,
        clock=lambda: datetime.now(timezone.utc),
    )

    first = use_case.execute(
        workflow.id,
        tenant_context(tenant_id),
        idempotency_key="review-1",
    )
    second = use_case.execute(
        workflow.id,
        tenant_context(tenant_id),
        idempotency_key="review-1",
    )

    assert second is first
    assert len(decisions.decisions) == 1


def test_conflicting_replay_cannot_overwrite_original_decision():
    tenant_id = uuid4()
    workflow = draft_workflow(tenant_id)
    workflows = InMemoryWorkflowRepository([workflow])
    decisions = InMemoryReviewDecisionRepository()

    approve = ApproveWorkflow(
        workflows,
        decisions,
        clock=lambda: datetime.now(timezone.utc),
    )
    reject = RejectWorkflow(
        workflows,
        decisions,
        clock=lambda: datetime.now(timezone.utc),
    )

    approve.execute(
        workflow.id,
        tenant_context(tenant_id),
        idempotency_key="review-1",
    )

    with pytest.raises(ValueError, match="idempotency"):
        reject.execute(
            workflow.id,
            tenant_context(tenant_id),
            idempotency_key="review-1",
        )


def test_tenant_cannot_review_another_tenant_workflow():
    workflow = draft_workflow(uuid4())
    workflows = InMemoryWorkflowRepository([workflow])
    decisions = InMemoryReviewDecisionRepository()

    with pytest.raises(PermissionError):
        ApproveWorkflow(
            workflows,
            decisions,
            clock=lambda: datetime.now(timezone.utc),
        ).execute(
            workflow.id,
            tenant_context(uuid4()),
            idempotency_key="review-1",
        )


def test_approval_does_not_create_execution_or_publish():
    tenant_id = uuid4()
    workflow = draft_workflow(tenant_id)
    workflows = InMemoryWorkflowRepository([workflow])
    decisions = InMemoryReviewDecisionRepository()

    decision = ApproveWorkflow(
        workflows,
        decisions,
        clock=lambda: datetime.now(timezone.utc),
    ).execute(
        workflow.id,
        tenant_context(tenant_id),
        idempotency_key="review-1",
    )

    assert decision.workflow_id == workflow.id
    assert workflow.state.value == "draft"
