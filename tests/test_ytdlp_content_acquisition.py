from app.application.content_acquisition import (
    ACQUIRED_CONTENT_ASSET_CONTEXT_KEY,
    CONTENT_SOURCE_CONTEXT_KEY,
)
from app.application.capability_result import CapabilityResult
from app.application.execution_context import ExecutionContext
from app.domain.content import ContentSource
from app.infrastructure.content_acquisition.ytdlp import (
    YtDlpContentAcquisitionCapability,
)


class FakeDownloader:
    def __init__(self, reference="storage/source.mp4", error=None):
        self.reference = reference
        self.error = error
        self.calls = []

    def download(self, source_reference: str) -> str:
        self.calls.append(source_reference)
        if self.error:
            raise self.error
        return self.reference


def context_with_source():
    context = ExecutionContext()
    context.set(
        CONTENT_SOURCE_CONTEXT_KEY,
        ContentSource.create("https://example.com/video", "video"),
    )
    return context


def test_ytdlp_acquisition_delegates_download_and_stores_asset():
    downloader = FakeDownloader()
    capability = YtDlpContentAcquisitionCapability(downloader)

    result = capability.execute(context_with_source())

    assert isinstance(result, CapabilityResult)
    assert result.succeeded is True
    assert downloader.calls == ["https://example.com/video"]


def test_ytdlp_acquisition_uses_downloaded_reference():
    downloader = FakeDownloader("storage/source.mp4")
    capability = YtDlpContentAcquisitionCapability(downloader)
    context = context_with_source()

    result = capability.execute(context)

    assert result.succeeded is True
    asset = context.get(ACQUIRED_CONTENT_ASSET_CONTEXT_KEY)
    assert asset.asset_type == "source_media"
    assert asset.reference == "storage/source.mp4"
    assert asset.source == context.get(CONTENT_SOURCE_CONTEXT_KEY)


def test_ytdlp_acquisition_translates_expected_provider_failure():
    downloader = FakeDownloader(error=RuntimeError("download failed"))
    capability = YtDlpContentAcquisitionCapability(downloader)

    result = capability.execute(context_with_source())

    assert result.succeeded is False
    assert "download failed" in str(result.error)
