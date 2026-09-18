from app.application.content_acquisition import (
    ACQUIRED_CONTENT_ASSET_CONTEXT_KEY,
)
from app.application.content_clip_extraction import (
    CLIP_CONTEXT_KEY,
    InMemoryContentClipExtractionCapability,
)
from app.application.content_transcription import (
    CONTENT_TRANSCRIPT_CONTEXT_KEY,
    InMemoryContentTranscriptionCapability,
)
from app.application.content_publishing import (
    CONTENT_PUBLICATION_REQUEST_CONTEXT_KEY,
    PUBLICATION_CONTEXT_KEY,
    ContentPublishingCapability,
    PublicationProvider,
)
from app.application.content_workflow import (
    CONTENT_ACQUIRE_CAPABILITY_ID,
    CONTENT_CLIP_EXTRACTION_CAPABILITY_ID,
    CONTENT_PUBLISH_CAPABILITY_ID,
    CONTENT_TRANSCRIBE_CAPABILITY_ID,
    ContentWorkflowComposition,
)
from app.application.execution_context import ExecutionContext
from app.domain.execution import ExecutionState
from app.domain.content import ClipSelection, ContentSource, Publication, PublicationRequest
from app.domain.workflow import Workflow, WorkflowStep
from app.infrastructure.content_acquisition.ytdlp import (
    ContentDownloader,
    YtDlpContentAcquisitionCapability,
)
from app.infrastructure.persistence.in_memory import (
    InMemoryExecutionRepository,
    InMemoryWorkflowRepository,
)


class FakePublicationProvider(PublicationProvider):
    def __init__(self) -> None:
        self.received_request: PublicationRequest | None = None

    def publish(self, request: PublicationRequest) -> Publication:
        self.received_request = request
        return Publication.create(
            asset=request.asset,
            destination=request.destination,
            external_reference="provider-ref-123",
        )


class FakeContentDownloader(ContentDownloader):
    def __init__(self, downloaded_reference: str) -> None:
        self.downloaded_reference = downloaded_reference
        self.received_source_reference: str | None = None

    def download(self, source_reference: str) -> str:
        self.received_source_reference = source_reference
        return self.downloaded_reference


def test_content_workflow_composition_runs_source_to_clip_with_concrete_acquisition():
    source = ContentSource.create("source://123", "video")
    workflow = Workflow.create(
        "Content source to clip",
        [
            WorkflowStep.create("Acquire", CONTENT_ACQUIRE_CAPABILITY_ID),
            WorkflowStep.create("Transcribe", CONTENT_TRANSCRIBE_CAPABILITY_ID),
            WorkflowStep.create("Extract clip", CONTENT_CLIP_EXTRACTION_CAPABILITY_ID),
            WorkflowStep.create("Publish", CONTENT_PUBLISH_CAPABILITY_ID),
        ],
    )
    workflow.publish()

    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    workflows.save(workflow)

    downloader = FakeContentDownloader("asset://source/123")
    publication_provider = FakePublicationProvider()
    composition = ContentWorkflowComposition(
        workflows,
        executions,
        YtDlpContentAcquisitionCapability(downloader),
        InMemoryContentTranscriptionCapability("hello from transcript"),
        InMemoryContentClipExtractionCapability(
            "asset://clip/123",
            ClipSelection.create(10, 40),
        ),
        ContentPublishingCapability(publication_provider),
    )
    execution = composition.start(workflow.id)
    context = ExecutionContext()
    context.set("content.source", source)

    while execution.state is ExecutionState.RUNNING:
        composition.execute_step(execution.id, context)

    assert execution.state is ExecutionState.COMPLETED
    assert execution.current_step == 4
    assert downloader.received_source_reference == "source://123"
    assert context.get(ACQUIRED_CONTENT_ASSET_CONTEXT_KEY).reference == "asset://source/123"
    assert context.get(CONTENT_TRANSCRIPT_CONTEXT_KEY).text == "hello from transcript"
    assert context.get(CLIP_CONTEXT_KEY).reference == "asset://clip/123"
    publication_request = context.get(CONTENT_PUBLICATION_REQUEST_CONTEXT_KEY)
    assert publication_request.asset.reference == "asset://clip/123"
    assert publication_request.destination == "video_platform"
    context.set(CONTENT_PUBLICATION_REQUEST_CONTEXT_KEY, publication_request)
    publication = context.get(PUBLICATION_CONTEXT_KEY)
    assert publication.external_reference == "provider-ref-123"
    assert publication_provider.received_request == publication_request
