from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from uuid import UUID


class ListingVisibility(Enum):
    PUBLIC = "public"
    HIDDEN = "hidden"


@dataclass(frozen=True)
class MarketplaceListing:
    """Discoverable metadata referencing an existing Workflow."""

    workflow_id: UUID
    title: str
    description: str
    domain: str
    supported_goals: tuple[str, ...]
    tags: tuple[str, ...]
    visibility: ListingVisibility = ListingVisibility.PUBLIC

    def __post_init__(self) -> None:
        if not isinstance(self.workflow_id, UUID):
            raise ValueError("Marketplace listing workflow_id must be a UUID")
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

    @classmethod
    def create(
        cls,
        workflow_id: UUID,
        title: str,
        description: str,
        domain: str,
        supported_goals: tuple[str, ...],
        tags: tuple[str, ...],
        visibility: ListingVisibility = ListingVisibility.PUBLIC,
    ) -> "MarketplaceListing":
        return cls(
            workflow_id=workflow_id,
            title=title.strip(),
            description=description.strip(),
            domain=domain.strip(),
            supported_goals=tuple(goal.strip() for goal in supported_goals),
            tags=tuple(tag.strip() for tag in tags),
            visibility=visibility,
        )
