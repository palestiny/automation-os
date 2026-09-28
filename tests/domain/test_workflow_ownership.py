from __future__ import annotations

from uuid import uuid4

import pytest

from app.domain.workflow import Workflow


def test_workflow_can_be_explicitly_owned_by_a_tenant() -> None:
    tenant_id = uuid4()

    workflow = Workflow.create(
        name="tenant workflow",
        steps=[],
        tenant_id=tenant_id,
    )

    assert workflow.tenant_id == tenant_id


def test_workflow_defaults_to_system_ownership_for_legacy_compatibility() -> None:
    workflow = Workflow.create(name="legacy workflow", steps=[])

    assert workflow.tenant_id is None


def test_workflow_rejects_invalid_tenant_identity() -> None:
    with pytest.raises(ValueError, match="tenant_id"):
        Workflow.create(
            name="invalid workflow",
            steps=[],
            tenant_id="tenant-not-a-uuid",
        )
