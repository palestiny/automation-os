from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TenantId(str):
    SYSTEM_VALUE = "system"

    @classmethod
    def create(cls, value: str) -> "TenantId":
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Tenant id cannot be empty")
        value = value.strip()
        return cls(value)

    @classmethod
    def system(cls) -> "TenantId":
        return cls(cls.SYSTEM_VALUE)


class Role(Enum):
    OWNER = "owner"
    MEMBER = "member"


@dataclass(frozen=True)
class Principal:
    subject: str
    roles: frozenset[Role]

    @classmethod
    def create(cls, subject: str, roles: set[Role] | frozenset[Role]) -> "Principal":
        if not isinstance(subject, str) or not subject.strip():
            raise ValueError("Principal subject cannot be empty")
        normalized = frozenset(roles)
        if not normalized:
            raise ValueError("Principal must have at least one role")
        if not all(isinstance(role, Role) for role in normalized):
            raise ValueError("Principal roles must be Role values")
        return cls(subject=subject.strip(), roles=normalized)


@dataclass(frozen=True)
class TenantContext:
    tenant_id: TenantId
    principal: Principal

    def __post_init__(self) -> None:
        if not isinstance(self.tenant_id, TenantId):
            raise TypeError("Tenant context requires a TenantId")
        if not isinstance(self.principal, Principal):
            raise TypeError("Tenant context requires a Principal")

    @property
    def is_system(self) -> bool:
        return self.tenant_id == TenantId.system()

    @classmethod
    def system(cls) -> "TenantContext":
        return cls(
            tenant_id=TenantId.system(),
            principal=Principal.create("system", {Role.OWNER}),
        )
