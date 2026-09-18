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
    derived_from: ContentAsset | None = None

    def __post_init__(self) -> None:
        if not self.asset_type.strip():
            raise ValueError("ContentAsset asset_type cannot be empty")
        if not self.reference.strip():
            raise ValueError("ContentAsset reference cannot be empty")
        if self.source is not None and not isinstance(self.source, ContentSource):
            raise ValueError("ContentAsset source must be a ContentSource instance")
        if self.derived_from is not None and not isinstance(self.derived_from, ContentAsset):
            raise ValueError("ContentAsset derived_from must be a ContentAsset instance")

    @classmethod
    def create(
        cls,
        asset_type: str,
        reference: str,
        source: ContentSource | None = None,
        derived_from: ContentAsset | None = None,
    ) -> "ContentAsset":
        return cls(
            id=uuid4(),
            asset_type=asset_type,
            reference=reference,
            source=source,
            derived_from=derived_from,
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


@dataclass(frozen=True)
class ClipSelection:
    """Provider-neutral explicit time range for a clip."""

    start_seconds: float
    end_seconds: float

    def __post_init__(self) -> None:
        if self.start_seconds < 0:
            raise ValueError("ClipSelection start_seconds cannot be negative")
        if self.end_seconds <= self.start_seconds:
            raise ValueError(
                "ClipSelection end_seconds must be greater than start_seconds"
            )

    @classmethod
    def create(cls, start_seconds: float, end_seconds: float) -> "ClipSelection":
        return cls(start_seconds=start_seconds, end_seconds=end_seconds)


@dataclass(frozen=True)
class PublicationRequest:
    """Provider-neutral intent to publish a content asset."""

    asset: ContentAsset
    destination: str

    def __post_init__(self) -> None:
        if not isinstance(self.asset, ContentAsset):
            raise ValueError(
                "PublicationRequest asset must be a ContentAsset instance"
            )
        if not self.destination.strip():
            raise ValueError("PublicationRequest destination cannot be empty")

    @classmethod
    def create(cls, asset: ContentAsset, destination: str) -> "PublicationRequest":
        return cls(asset=asset, destination=destination)


@dataclass(frozen=True)
class Publication:
    """Provider-neutral successful publication result."""

    id: UUID
    asset: ContentAsset
    destination: str
    external_reference: str

    def __post_init__(self) -> None:
        if not isinstance(self.asset, ContentAsset):
            raise ValueError("Publication asset must be a ContentAsset instance")
        if not self.destination.strip():
            raise ValueError("Publication destination cannot be empty")
        if not self.external_reference.strip():
            raise ValueError("Publication external_reference cannot be empty")

    @classmethod
    def create(
        cls,
        asset: ContentAsset,
        destination: str,
        external_reference: str,
    ) -> "Publication":
        return cls(
            id=uuid4(),
            asset=asset,
            destination=destination,
            external_reference=external_reference,
        )
