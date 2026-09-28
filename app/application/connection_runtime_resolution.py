from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from app.application.connection_resolver import ConnectionResolver
from app.application.secret_provider import SecretProvider
from app.domain.connection import Connection


@dataclass(frozen=True)
class ResolvedConnection:
    """Runtime-only connection data after protected secret resolution.

    Secret material is deliberately excluded from the Connection domain entity
    and is retained only inside this execution-time result.
    """

    connection_id: UUID
    tenant_id: UUID
    provider_id: str
    reference: str
    authentication_type: str
    secret_material: object = field(repr=False)

    @classmethod
    def from_connection(
        cls,
        connection: Connection,
        secret_material: object,
    ) -> "ResolvedConnection":
        return cls(
            connection_id=connection.id,
            tenant_id=connection.tenant_id,
            provider_id=connection.provider_id,
            reference=connection.reference,
            authentication_type=connection.authentication_type,
            secret_material=secret_material,
        )


class ResolveRuntimeConnection:
    """Resolve a tenant-owned connection and its protected secret at runtime."""

    def __init__(
        self,
        connection_resolver: ConnectionResolver,
        secret_provider: SecretProvider,
    ) -> None:
        self._connection_resolver = connection_resolver
        self._secret_provider = secret_provider

    def resolve(
        self,
        *,
        tenant_id: UUID,
        provider_id: str,
        reference: str,
    ) -> ResolvedConnection:
        connection = self._connection_resolver.resolve(
            tenant_id=tenant_id,
            provider_id=provider_id,
            reference=reference,
        )
        try:
            secret_material = self._secret_provider.get_secret(
                connection.secret_reference
            )
        except Exception as exc:
            raise RuntimeError("Protected secret resolution failed") from exc

        return ResolvedConnection.from_connection(
            connection,
            secret_material,
        )
