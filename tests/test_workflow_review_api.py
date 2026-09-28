from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.application.authorization import AuthorizationContext, TenantId
from app.domain.workflow import Workflow, WorkflowStep
from app.infrastructure.persistence.in_memory import InMemoryReviewDecisionRepository
from app.main import app
import app.api.review as review_api


class WorkflowRepository:
    def __init__(self, workflows=()):
        self.items = {workflow.id: workflow for workflow in workflows}

    def all(self):
        return tuple(self.items.values())

    def get(self, workflow_id):
        return self.items.get(workflow_id)


def make_workflow(tenant_id):
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


def make_context(tenant_id):
    return AuthorizationContext(
        principal_id="reviewer-1",
        tenant_id=TenantId(tenant_id),
    )


def configure_review(workflows):
    workflow_repository = WorkflowRepository(workflows)
    decision_repository = InMemoryReviewDecisionRepository()

    def repositories(_context):
        return workflow_repository, decision_repository

    original = review_api.build_review_repositories
    review_api.build_review_repositories = repositories
    return workflow_repository, decision_repository, original


def test_review_api_lists_only_visible_drafts_and_exposes_revision():
    tenant_id = uuid4()
    visible = make_workflow(tenant_id)
    other = make_workflow(uuid4())
    published = make_workflow(tenant_id)
    published.publish()

    _, _, original = configure_review([visible, other, published])
    context = make_context(tenant_id)
    app.dependency_overrides[review_api.get_authorization_context] = lambda: context

    try:
        response = TestClient(app).get("/review/workflows")
    finally:
        app.dependency_overrides = {}
        review_api.build_review_repositories = original

    assert response.status_code == 200
    assert [item["workflow_id"] for item in response.json()] == [str(visible.id)]
    assert response.json()[0]["review_revision"] == visible.review_revision


def test_review_api_denies_cross_tenant_single_workflow_access():
    tenant_id = uuid4()
    workflow = make_workflow(uuid4())

    _, _, original = configure_review([workflow])
    app.dependency_overrides[review_api.get_authorization_context] = (
        lambda: make_context(tenant_id)
    )

    try:
        response = TestClient(app).get(f"/review/workflows/{workflow.id}")
    finally:
        app.dependency_overrides = {}
        review_api.build_review_repositories = original

    assert response.status_code == 403


def test_approve_api_records_evidence_without_publishing():
    tenant_id = uuid4()
    workflow = make_workflow(tenant_id)

    _, decisions, original = configure_review([workflow])
    app.dependency_overrides[review_api.get_authorization_context] = (
        lambda: make_context(tenant_id)
    )

    try:
        response = TestClient(app).post(
            f"/review/workflows/{workflow.id}/approve",
            headers={"Idempotency-Key": "review-1"},
            json={"expected_revision": workflow.review_revision},
        )
    finally:
        app.dependency_overrides = {}
        review_api.build_review_repositories = original

    assert response.status_code == 200
    assert response.json()["decision"] == "approved"
    assert response.json()["workflow_revision"] == workflow.review_revision
    assert workflow.state.value == "draft"
    assert len(decisions.list_by_workflow(workflow.id)) == 1


def test_reject_api_requires_reason_and_preserves_workflow():
    tenant_id = uuid4()
    workflow = make_workflow(tenant_id)

    _, _, original = configure_review([workflow])
    app.dependency_overrides[review_api.get_authorization_context] = (
        lambda: make_context(tenant_id)
    )

    try:
        response = TestClient(app).post(
            f"/review/workflows/{workflow.id}/reject",
            headers={"Idempotency-Key": "review-1"},
            json={
                "expected_revision": workflow.review_revision,
                "reason": "Needs validation",
            },
        )
    finally:
        app.dependency_overrides = {}
        review_api.build_review_repositories = original

    assert response.status_code == 200
    assert response.json()["decision"] == "rejected"
    assert response.json()["reason"] == "Needs validation"
    assert workflow.state.value == "draft"


def test_approve_api_rejects_stale_revision():
    tenant_id = uuid4()
    workflow = make_workflow(tenant_id)
    stale_revision = workflow.review_revision
    workflow.add_step(
        WorkflowStep.create(
            name="Publish video",
            capability="video.publish",
        )
    )

    _, _, original = configure_review([workflow])
    app.dependency_overrides[review_api.get_authorization_context] = (
        lambda: make_context(tenant_id)
    )

    try:
        response = TestClient(app).post(
            f"/review/workflows/{workflow.id}/approve",
            headers={"Idempotency-Key": "review-1"},
            json={"expected_revision": stale_revision},
        )
    finally:
        app.dependency_overrides = {}
        review_api.build_review_repositories = original

    assert response.status_code == 409
    assert "changed" in response.json()["detail"]


def test_approve_api_exact_replay_is_idempotent_and_conflict_is_rejected():
    tenant_id = uuid4()
    workflow = make_workflow(tenant_id)

    _, decisions, original = configure_review([workflow])
    app.dependency_overrides[review_api.get_authorization_context] = (
        lambda: make_context(tenant_id)
    )

    try:
        first = TestClient(app).post(
            f"/review/workflows/{workflow.id}/approve",
            headers={"Idempotency-Key": "review-1"},
            json={"expected_revision": workflow.review_revision},
        )
        replay = TestClient(app).post(
            f"/review/workflows/{workflow.id}/approve",
            headers={"Idempotency-Key": "review-1"},
            json={"expected_revision": workflow.review_revision},
        )
        conflict = TestClient(app).post(
            f"/review/workflows/{workflow.id}/reject",
            headers={"Idempotency-Key": "review-1"},
            json={
                "expected_revision": workflow.review_revision,
                "reason": "Invalid output",
            },
        )
    finally:
        app.dependency_overrides = {}
        review_api.build_review_repositories = original

    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json()["decision_id"] == first.json()["decision_id"]
    assert conflict.status_code == 409
    assert len(decisions.list_by_workflow(workflow.id)) == 1


def test_review_api_returns_decision_history_in_deterministic_order():
    tenant_id = uuid4()
    workflow = make_workflow(tenant_id)

    _, _, original = configure_review([workflow])
    app.dependency_overrides[review_api.get_authorization_context] = (
        lambda: make_context(tenant_id)
    )

    try:
        client = TestClient(app)
        first = client.post(
            f"/review/workflows/{workflow.id}/approve",
            headers={"Idempotency-Key": "review-1"},
            json={"expected_revision": workflow.review_revision},
        )
        second = client.get(f"/review/workflows/{workflow.id}/decisions")
    finally:
        app.dependency_overrides = {}
        review_api.build_review_repositories = original

    assert first.status_code == 200
    assert second.status_code == 200
    assert len(second.json()) == 1
    assert second.json()[0]["decision_id"] == first.json()["decision_id"]


def test_review_api_fails_closed_without_authorization_context():
    response = TestClient(app).get("/review/workflows")
    assert response.status_code == 503
