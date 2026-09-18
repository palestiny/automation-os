from __future__ import annotations

from typing import Protocol

from app.domain.content import ContentAsset


class MediaAssetNotFoundError(Exception):
    """Raised when the requested media artifact cannot be resolved."""


class MediaAssetReader(Protocol):
    """Provider-neutral read boundary for media artifacts."""

    def read(self, asset: ContentAsset) -> bytes:
        ...


class InMemoryMediaAssetReader:
    """Deterministic media reader for application tests."""

    def __init__(self, assets: dict[str, bytes]) -> None:
        self._assets = dict(assets)

    def read(self, asset: ContentAsset) -> bytes:
        try:
            return self._assets[asset.reference]
        except KeyError as exc:
            raise MediaAssetNotFoundError(
                f"Media asset was not found: {asset.reference}"
            ) from exc
