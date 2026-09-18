from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.capability_registry import CapabilityRegistry
from app.application.content_acquisition import (
    ACQUIRED_CONTENT_ASSET_CONTEXT_KEY,
    InMemoryContentAcquisitionCapability,
)
from app.application.content_clip_extraction import (
    CLIP_CONTEXT_KEY,
    InMemoryContentClipExtractionCapability,
)
from app.application.content_transcription import (
    CONTENT_TRANSCRIPT_CONTEXT_KEY,
    InMemoryContentTranscriptionCapability,
)
from app.application.content_workflow import (
    CONTENT_ACQUIRE_CAPABILITY_ID,
    CONTENT_CLIP_EXTRACTION_CAPABILITY_ID,
    CONTENT_TRANSCRIBE_CAPABILITY_ID,
    ContentWorkflowComposition,
)
from app.application.execution_context import ExecutionContext
from app.application.execute_workflow_step import ExecuteWorkflowStep
from app.application.condition_evaluator import ConditionEvaluator
from app.application.start_workflow_execution import StartWorkflowExecution
from app.domain.execution import ExecutionState
from app.domain.content import ClipSelection, ContentSource
from app.domain.workflow import Workflow, WorkflowStep
from app.infrastructure.persistence.in_memory import (
    InMemoryExecutionRepository,
    InMemoryWorkflowRepository,
)


def test_content_workflow_composition_runs_source_to_clip():
    source = ContentSource.create("source://123", "video")
    workflow = Workflow.create(
        "Content source to clip",
        [
            WorkflowStep.create("Acquire", CONTENT_ACQUIRE_CAPABILITY_ID),
            WorkflowStep.create("Transcribe", CONTENT_TRANSCRIBE_CAPABILITY_ID),
            WorkflowStep.create("Extract clip", CONTENT_CLIP_EXTRACTION_CAPABILITY_ID),
        ],
    )
    workflow.publish()

    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    workflows.save(workflow)

    registry = CapabilityRegistry()
    registry.register(
        CONTENT_ACQUIRE_CAPABILITY_ID,
        InMemoryContentAcquisitionCapability("asset://source/123"),
    )
    registry.register(
        CONTENT_TRANSCRIBE_CAPABILITY_ID,
        InMemoryContentTranscriptionCapability("hello from transcript"),
    )
    registry.register(
        CONTENT_CLIP_EXTRACTION_CAPABILITY_ID,
        InMemoryContentClipExtractionCapability(
            "asset://clip/123",
            ClipSelection.create(10, 40),
        ),
    )

    composition = ContentWorkflowComposition(
        workflows,
        executions,
        registry.resolve(CONTENT_ACQUIRE_CAPABILITY_ID),
        registry.resolve(CONTENT_TRANSCRIBE_CAPABILITY_ID),
        registry.resolve(CONTENT_CLIP_EXTRACTION_CAPABILITY_ID),
    )
    execution = composition.start(workflow.id)
    context = ExecutionContext()

    while execution.state is ExecutionState.RUNNING:
        composition.execute_step(execution.id, context)

    assert execution.state is ExecutionState.COMPLETED
    assert execution.current_step == 3
    assert context.get(ACQUIRED_CONTENT_ASSET_CONTEXT_KEY).reference == "asset://source/123"
    assert context.get(CONTENT_TRANSCRIPT_CONTEXT_KEY).text == "hello from transcript"
    assert context.get(CLIP_CONTEXT_KEY).reference == "asset://clip/123"
