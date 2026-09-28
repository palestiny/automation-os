from __future__ import annotations

from uuid import uuid4

import pytest

from app.application.authorization import AuthorizationContext, TenantId, AuthorizationDeniedError
from app.application.workflow_draft_review import GetDraftWorkflowForReview
from app.domain.workflow import Workflow, WorkflowState


class InMemoryWorkflowRepository:
    def __init__(self, workflows: list[Workflow] | None = None) -> None:
        self._workflows = {workflow.id: workflow for workflow in (workflows or [])}

    def get(self, workflow_id):
        return self._workflows.get(workflow_id)


def draft() -> Workflow:
    return Workflow.create(
        name="Generated draft",
        steps=[],
        supported_goals=["create_short_video"],
    )


def published() -> Workflow:
    workflow = Workflow.create(
        name="Published workflow",
        steps=[],
        supported_goals=["create_short_video"],
    )
    workflow.add_step(
        __import__("app.domain.workflow", fromlist=["WorkflowStep"]).WorkflowStep.create(
            name="Create video",
            capability="video.create",
        )
    )
    workflow.publish()
    return workflow


def test_returns_draft_for_explicit_review():
    tenant_id = uuid4()
    workflow = Workflow.create(name="Generated draft", steps=[], supported_goals=["create_short_video"], tenant_id=tenant_id)
    use_case = GetDraftWorkflowForReview(InMemoryWorkflowRepository([workflow]))

    result = use_case.execute(workflow.id, AuthorizationContext(principal_id="reviewer-1", tenant_id=TenantId(tenant_id)))

    assert result is workflow
    assert result.state is WorkflowState.DRAFT


def test_does_not_return_published_workflow_for_draft_review():
    workflow = published()
    use_case = GetDraftWorkflowForReview(InMemoryWorkflowRepository([workflow]))

    with pytest.raises(ValueError, match="DRAFT"):
        use_case.execute(workflow.id, AuthorizationContext.system("system-reviewer"))


def test_returns_not_found_when_workflow_does_not_exist():
    use_case = GetDraftWorkflowForReview(InMemoryWorkflowRepository())

    with pytest.raises(LookupError, match="not found"):
        use_case.execute(uuid4(), AuthorizationContext.system("system-reviewer"))


def test_rejects_invalid_workflow_id():
    use_case = GetDraftWorkflowForReview(InMemoryWorkflowRepository())

    with pytest.raises(TypeError, match="UUID"):
        use_case.execute("not-a-uuid", AuthorizationContext.system("system-reviewer"))


def test_rejects_draft_from_different_tenant():
    owner = uuid4()
    other_tenant = uuid4()
    workflow = Workflow.create(
        name="Tenant draft",
        steps=[],
        tenant_id=owner,
    )
    use_case = GetDraftWorkflowForReview(InMemoryWorkflowRepository([workflow]))

    with pytest.raises(AuthorizationDeniedError):
        use_case.execute(
            workflow.id,
            AuthorizationContext(
                principal_id="reviewer-2",
                tenant_id=TenantId(other_tenant),
            ),
        )
