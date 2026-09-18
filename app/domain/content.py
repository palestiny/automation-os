from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ContentSource:
    """Provider-neutral reference to the origin of content."""

    reference: str
    source_type: str

    def __post_init__(self) -> None:
        if not self.reference.strip():
            raise ValueError("ContentSource reference cannot be empty")
        if not self.source_type.strip():
            raise ValueError("ContentSource source_type cannot be empty")

    @classmethod
    def create(cls, reference: str, source_type: str) -> "ContentSource":
        return cls(reference=reference, source_type=source_type)


@dataclass(frozen=True)
class ContentAsset:
    """Provider-neutral content artifact used by a content workflow."""

    id: UUID
    asset_type: str
    reference: str
    source: ContentSource | None = None

    def __post_init__(self) -> None:
        if not self.asset_type.strip():
            raise ValueError("ContentAsset asset_type cannot be empty")
        if not self.reference.strip():
            raise ValueError("ContentAsset reference cannot be empty")
        if self.source is not None and not isinstance(self.source, ContentSource):
            raise ValueError("ContentAsset source must be a ContentSource instance")

    @classmethod
    def create(
        cls,
        asset_type: str,
        reference: str,
        source: ContentSource | None = None,
    ) -> "ContentAsset":
        return cls(
            id=uuid4(),
            asset_type=asset_type,
            reference=reference,
            source=source,
        )


@dataclass(frozen=True)
class Transcript:
    """Provider-neutral textual representation derived from source media."""

    id: UUID
    text: str
    source_asset: ContentAsset

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("Transcript text cannot be empty")
        if not isinstance(self.source_asset, ContentAsset):
            raise ValueError(
                "Transcript source_asset must be a ContentAsset instance"
            )

    @classmethod
    def create(cls, text: str, source_asset: ContentAsset) -> "Transcript":
        return cls(
            id=uuid4(),
            text=text,
            source_asset=source_asset,
        )
