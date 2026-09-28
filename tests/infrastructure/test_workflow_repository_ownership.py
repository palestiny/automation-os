from __future__ import annotations

from uuid import uuid4

import pytest

from app.domain.workflow import Workflow
from app.infrastructure.persistence.in_memory import InMemoryWorkflowRepository


def _workflow(tenant_id):
    return Workflow.create(
        name="review draft",
        steps=[],
        tenant_id=tenant_id,
    )


def test_tenant_scoped_workflow_repository_returns_only_owned_workflows() -> None:
    tenant_a = uuid4()
    tenant_b = uuid4()
    repository = InMemoryWorkflowRepository(tenant_id=tenant_a)

    owned = _workflow(tenant_a)
    foreign = _workflow(tenant_b)

    repository.save(owned)

    with pytest.raises(ValueError, match="different tenant"):
        repository.save(foreign)

    assert repository.get(owned.id) is owned
    assert repository.get(foreign.id) is None
    assert repository.all() == (owned,)


def test_system_scoped_workflow_repository_keeps_system_ownership() -> None:
    repository = InMemoryWorkflowRepository(tenant_id=None)
    workflow = _workflow(None)

    repository.save(workflow)

    assert repository.get(workflow.id) is workflow
    assert repository.all() == (workflow,)
