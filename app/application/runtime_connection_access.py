from __future__ import annotations

from uuid import UUID

from app.application.connection_runtime_resolution import ResolvedConnection
from app.application.execution_context import ExecutionContext
from app.application.runtime_connection_preparation import PreparedRuntimeConnections


RUNTIME_CONNECTIONS_KEY = "runtime.connections"


def get_prepared_connection(
    context: ExecutionContext,
    *,
    provider_id: str,
    reference: str,
) -> ResolvedConnection:
    prepared = context.get(RUNTIME_CONNECTIONS_KEY)
    if not isinstance(prepared, PreparedRuntimeConnections):
        raise RuntimeError("Runtime connections have not been prepared")

    for connection in prepared.connections:
        if connection.provider_id == provider_id and connection.reference == reference:
            return connection

    raise RuntimeError("Requested connection was not declared by the workflow version")
