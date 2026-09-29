from __future__ import annotations

import os
from uuid import UUID

from app.application.connection_resolver import ConnectionResolver
from app.application.connection_runtime_resolution import ResolveRuntimeConnection
from app.application.runtime_connection_preparation import PrepareWorkflowRuntimeConnections
from app.application.secret_provider import SecretProvider
from app.infrastructure.persistence.in_memory import InMemoryConnectionRepository
from app.infrastructure.persistence.postgres import (
    PostgresConnectionRepository,
    PostgresSchema,
    postgres_connection_factory,
)


def build_runtime_connection_preparer(
    *,
    tenant_id: UUID,
    secret_provider: SecretProvider,
) -> PrepareWorkflowRuntimeConnections:
    """Build runtime connection resolution for one explicit tenant.

    Tenant identity is an input to composition, never inferred from a
    workflow or caller-provided connection reference.
    """
    if not isinstance(tenant_id, UUID):
        raise TypeError("tenant_id must be a UUID")

    database_url = os.environ.get("AUTOMATION_OS_DATABASE_URL")
    if database_url:
        connection_factory = postgres_connection_factory(database_url)
        with connection_factory() as connection:
            PostgresSchema.initialize(connection)
        repository = PostgresConnectionRepository(
            connection_factory,
            tenant_id=tenant_id,
        )
    else:
        repository = InMemoryConnectionRepository(tenant_id=tenant_id)

    return PrepareWorkflowRuntimeConnections(
        ResolveRuntimeConnection(
            ConnectionResolver(repository),
            secret_provider,
        )
    )
