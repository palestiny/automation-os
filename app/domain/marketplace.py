from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from uuid import UUID, uuid4


class ListingVisibility(Enum):
    PUBLIC = "public"
    HIDDEN = "hidden"


class ListingStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    WITHDRAWN = "withdrawn"


@dataclass(frozen=True)
class MarketplaceListing:
    """Discoverable metadata pinned to an immutable WorkflowVersion when available."""

    workflow_id: UUID | None
    title: str
    description: str
    domain: str
    supported_goals: tuple[str, ...]
    tags: tuple[str, ...]
    visibility: ListingVisibility = ListingVisibility.PUBLIC
    status: ListingStatus = ListingStatus.DRAFT
    id: UUID | None = None
    workflow_version_id: UUID | None = None

    def __post_init__(self) -> None:
        if self.id is None:
            object.__setattr__(self, "id", uuid4())
        if not isinstance(self.id, UUID):
            raise ValueError("Marketplace listing id must be a UUID")
        if self.workflow_id is not None and not isinstance(self.workflow_id, UUID):
            raise ValueError("Marketplace listing workflow_id must be a UUID")
        if self.workflow_version_id is not None and not isinstance(self.workflow_version_id, UUID):
            raise ValueError("Marketplace listing workflow_version_id must be a UUID")
        if self.workflow_id is None and self.workflow_version_id is None:
            raise ValueError("Marketplace listing requires a workflow or workflow version identity")
        if not self.title.strip():
            raise ValueError("Marketplace listing title cannot be empty")
        if not self.description.strip():
            raise ValueError("Marketplace listing description cannot be empty")
        if not self.domain.strip():
            raise ValueError("Marketplace listing domain cannot be empty")
        if not self.supported_goals:
            raise ValueError("Marketplace listing requires at least one goal")
        if any(not isinstance(goal, str) or not goal.strip() for goal in self.supported_goals):
            raise ValueError("Marketplace listing goals must be non-empty strings")
        if len(set(self.supported_goals)) != len(self.supported_goals):
            raise ValueError("Marketplace listing goals must be unique")
        if any(not isinstance(tag, str) or not tag.strip() for tag in self.tags):
            raise ValueError("Marketplace listing tags must be non-empty strings")
        if len(set(self.tags)) != len(self.tags):
            raise ValueError("Marketplace listing tags must be unique")
        if not isinstance(self.visibility, ListingVisibility):
            raise ValueError("Marketplace listing visibility is invalid")
        if not isinstance(self.status, ListingStatus):
            raise ValueError("Marketplace listing status is invalid")

    @classmethod
    def create(
        cls,
        workflow_id: UUID | None = None,
        title: str = "",
        description: str = "",
        domain: str = "",
        supported_goals: tuple[str, ...] = (),
        tags: tuple[str, ...] = (),
        visibility: ListingVisibility = ListingVisibility.PUBLIC,
        status: ListingStatus = ListingStatus.DRAFT,
        *,
        workflow_version_id: UUID | None = None,
        listing_id: UUID | None = None,
    ) -> "MarketplaceListing":
        return cls(
            id=listing_id or uuid4(),
            workflow_id=workflow_id,
            workflow_version_id=workflow_version_id,
            title=title.strip(),
            description=description.strip(),
            domain=domain.strip(),
            supported_goals=tuple(goal.strip() for goal in supported_goals),
            tags=tuple(tag.strip() for tag in tags),
            visibility=visibility,
            status=status,
        )

    def publish(self) -> "MarketplaceListing":
        if self.status == ListingStatus.WITHDRAWN:
            raise ValueError("withdrawn listing cannot be published")
        if self.status == ListingStatus.PUBLISHED:
            return self
        return replace(self, status=ListingStatus.PUBLISHED)

    def withdraw(self) -> "MarketplaceListing":
        if self.status != ListingStatus.PUBLISHED:
            raise ValueError("Only published listing can be withdrawn")
        return replace(self, status=ListingStatus.WITHDRAWN)
