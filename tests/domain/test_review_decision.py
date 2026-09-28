from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.domain.review_decision import ReviewDecision, ReviewDecisionType


def test_review_decision_is_immutable_evidence():
    tenant_id = uuid4()
    workflow_id = uuid4()
    decision_id = uuid4()
    created_at = datetime.now(timezone.utc)

    decision = ReviewDecision.create(
        decision_id=decision_id,
        workflow_id=workflow_id,
        workflow_revision="a" * 64,
        tenant_id=tenant_id,
        reviewer_principal_id="reviewer-1",
        decision=ReviewDecisionType.APPROVED,
        reason="Validated",
        idempotency_key="review-1",
        created_at=created_at,
    )

    assert decision.id == decision_id
    assert decision.workflow_id == workflow_id
    assert decision.workflow_revision == "a" * 64
    assert decision.tenant_id == tenant_id
    assert decision.reviewer_principal_id == "reviewer-1"
    assert decision.decision is ReviewDecisionType.APPROVED
    assert decision.reason == "Validated"
    assert decision.idempotency_key == "review-1"
    assert decision.created_at == created_at


@pytest.mark.parametrize(
    "kwargs",
    [
        {"workflow_revision": "short"},
        {"reviewer_principal_id": ""},
        {"idempotency_key": ""},
        {"decision": "approved"},
    ],
)
def test_review_decision_rejects_invalid_identity_or_decision(kwargs):
    values = {
        "workflow_id": uuid4(),
        "workflow_revision": "a" * 64,
        "tenant_id": uuid4(),
        "reviewer_principal_id": "reviewer-1",
        "decision": ReviewDecisionType.APPROVED,
        "reason": None,
        "idempotency_key": "review-1",
        "created_at": datetime.now(timezone.utc),
    }
    values.update(kwargs)

    with pytest.raises((TypeError, ValueError)):
        ReviewDecision.create(**values)


def test_review_revision_changes_when_reviewed_workflow_content_changes():
    from app.domain.workflow import Workflow, WorkflowStep

    workflow = Workflow.create(
        name="Generated draft",
        steps=[
            WorkflowStep.create(
                name="Create video",
                capability="video.create",
            )
        ],
        supported_goals=["create_short_video"],
        tenant_id=uuid4(),
    )

    first_revision = workflow.review_revision
    workflow.add_step(
        WorkflowStep.create(
            name="Publish video",
            capability="video.publish",
        )
    )

    assert workflow.review_revision != first_revision
    assert len(workflow.review_revision) == 64
