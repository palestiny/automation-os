from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.application.connection_runtime_resolution import ResolveRuntimeConnection, ResolvedConnection
from app.application.execution_context import ExecutionContext, _create_runtime_connection_writer
from app.domain.workflow_version import WorkflowVersion


class RuntimeConnectionPreparationError(RuntimeError):
    pass


@dataclass(frozen=True)
class PreparedRuntimeConnections:
    """Resolved runtime connections; secret material is intentionally excluded from repr."""

    connections: tuple[ResolvedConnection, ...]

    def __repr__(self) -> str:
        return f"PreparedRuntimeConnections(count={len(self.connections)})"


class PrepareWorkflowRuntimeConnections:
    """Resolve only the connections declared by the persisted executable version."""

    def __init__(
        self,
        resolver: ResolveRuntimeConnection,
    ):
        self._resolver = resolver

    def prepare(
        self,
        *,
        workflow_version: WorkflowVersion,
        tenant_id: UUID,
        context: ExecutionContext,
    ) -> PreparedRuntimeConnections:
        if workflow_version.tenant_id != tenant_id:
            raise PermissionError("Workflow version tenant does not match execution tenant")

        resolved = tuple(
            self._resolver.resolve(
                tenant_id=tenant_id,
                provider_id=requirement.provider_id,
                reference=requirement.reference,
            )
            for requirement in workflow_version.connection_requirements
        )

        prepared = PreparedRuntimeConnections(resolved)
        _create_runtime_connection_writer(context).set(prepared)
        return prepared
