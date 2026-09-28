from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class ConnectionStatus(Enum):
    ACTIVE = "active"
    REVOKED = "revoked"


@dataclass
class Connection:
    """Tenant-owned provider configuration without embedded secret material."""

    id: UUID
    tenant_id: UUID
    provider_id: str
    reference: str
    authentication_type: str
    secret_reference: str
    status: ConnectionStatus
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise ValueError("Connection id must be a UUID")
        if not isinstance(self.tenant_id, UUID):
            raise ValueError("Connection tenant_id must be a UUID")
        if not isinstance(self.provider_id, str) or not self.provider_id.strip():
            raise ValueError("Connection provider_id cannot be empty")
        if not isinstance(self.reference, str) or not self.reference.strip():
            raise ValueError("Connection reference cannot be empty")
        if not isinstance(self.authentication_type, str) or not self.authentication_type.strip():
            raise ValueError("Connection authentication_type cannot be empty")
        if not isinstance(self.secret_reference, str) or not self.secret_reference.strip():
            raise ValueError("Connection secret_reference cannot be empty")
        if not isinstance(self.status, ConnectionStatus):
            raise ValueError("Connection status must be a ConnectionStatus")
        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise ValueError("Connection timestamps must be timezone-aware")

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        provider_id: str,
        reference: str,
        authentication_type: str,
        secret_reference: str,
        connection_id: UUID | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> "Connection":
        now = (clock or (lambda: datetime.now(timezone.utc)))()
        return cls(
            id=connection_id or uuid4(),
            tenant_id=tenant_id,
            provider_id=provider_id.strip(),
            reference=reference.strip(),
            authentication_type=authentication_type.strip(),
            secret_reference=secret_reference.strip(),
            status=ConnectionStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

    def revoke(self, *, clock: Callable[[], datetime] | None = None) -> None:
        if self.status is ConnectionStatus.REVOKED:
            raise ValueError("Connection is already revoked")
        self.status = ConnectionStatus.REVOKED
        self.updated_at = (clock or (lambda: datetime.now(timezone.utc)))()
