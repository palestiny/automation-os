from __future__ import annotations

from uuid import UUID

from app.application.execution_context import ExecutionContext
from app.application.runtime_connection_preparation import (
    PrepareWorkflowRuntimeConnections,
    PreparedRuntimeConnections,
)
from app.domain.workflow_version import WorkflowVersion


class ExecuteWorkflowRuntimePreparation:
    """Prepare immutable workflow-declared runtime dependencies before capability dispatch."""

    def __init__(self, connection_preparation: PrepareWorkflowRuntimeConnections):
        self._connection_preparation = connection_preparation

    def prepare(
        self,
        *,
        workflow_version: WorkflowVersion,
        tenant_id: UUID,
        context: ExecutionContext,
    ) -> PreparedRuntimeConnections:
        return self._connection_preparation.prepare(
            workflow_version=workflow_version,
            tenant_id=tenant_id,
            context=context,
        )
