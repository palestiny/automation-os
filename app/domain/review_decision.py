from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class ReviewDecisionType(Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ReviewDecision:
    id: UUID
    workflow_id: UUID
    workflow_revision: str
    tenant_id: UUID | None
    reviewer_principal_id: str
    decision: ReviewDecisionType
    reason: str | None
    idempotency_key: str
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        workflow_id: UUID,
        workflow_revision: str,
        tenant_id: UUID | None,
        reviewer_principal_id: str,
        decision: ReviewDecisionType,
        reason: str | None,
        idempotency_key: str,
        created_at: datetime | None = None,
        decision_id: UUID | None = None,
    ) -> "ReviewDecision":
        return cls(
            id=decision_id or uuid4(),
            workflow_id=workflow_id,
            workflow_revision=workflow_revision,
            tenant_id=tenant_id,
            reviewer_principal_id=reviewer_principal_id,
            decision=decision,
            reason=reason.strip() if reason is not None else None,
            idempotency_key=idempotency_key.strip(),
            created_at=created_at or datetime.now(timezone.utc),
        )

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise TypeError("Review decision id must be a UUID")
        if not isinstance(self.workflow_id, UUID):
            raise TypeError("Review decision workflow_id must be a UUID")
        if self.tenant_id is not None and not isinstance(self.tenant_id, UUID):
            raise TypeError("Review decision tenant_id must be a UUID or None")
        if not isinstance(self.workflow_revision, str) or len(self.workflow_revision) != 64:
            raise ValueError("Review decision workflow_revision must be a SHA-256 hex digest")
        try:
            int(self.workflow_revision, 16)
        except ValueError as exc:
            raise ValueError("Review decision workflow_revision must be hexadecimal") from exc
        if not self.reviewer_principal_id.strip():
            raise ValueError("Reviewer principal id cannot be empty")
        if not isinstance(self.decision, ReviewDecisionType):
            raise TypeError("Review decision must be a ReviewDecisionType")
        if self.decision is ReviewDecisionType.REJECTED and not self.reason:
            raise ValueError("Rejected review decision requires a reason")
        if not self.idempotency_key.strip():
            raise ValueError("Review decision idempotency key cannot be empty")
        if self.created_at.tzinfo is None:
            raise ValueError("Review decision created_at must be timezone-aware")
