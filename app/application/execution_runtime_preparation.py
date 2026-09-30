from __future__ import annotations

from uuid import UUID

from app.application.execution_context import ExecutionContext
from app.application.runtime_connection_preparation import PrepareWorkflowRuntimeConnections
from app.domain.workflow_version import WorkflowVersion


class PrepareExecutionRuntime:
    """Prepare immutable workflow-version runtime dependencies before capabilities run."""

    def __init__(self, connection_preparation: PrepareWorkflowRuntimeConnections):
        self._connection_preparation = connection_preparation

    def prepare(
        self,
        *,
        workflow_version: WorkflowVersion,
        tenant_id: UUID,
        context: ExecutionContext,
    ) -> None:
        self._connection_preparation.prepare(
            workflow_version=workflow_version,
            tenant_id=tenant_id,
            context=context,
        )
