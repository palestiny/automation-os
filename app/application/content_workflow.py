from __future__ import annotations

from app.application.capability import Capability
from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.capability_registry import CapabilityRegistry
from app.application.condition_evaluator import ConditionEvaluator
from app.application.execution_context import ExecutionContext
from app.application.execute_workflow_step import ExecuteWorkflowStep
from app.application.start_workflow_execution import StartWorkflowExecution
from app.domain.repositories import ExecutionRepository, WorkflowRepository


CONTENT_ACQUIRE_CAPABILITY_ID = "content_source_acquire"
CONTENT_TRANSCRIBE_CAPABILITY_ID = "content_transcribe"
CONTENT_CLIP_EXTRACTION_CAPABILITY_ID = "content_extract_clip"
CONTENT_PUBLISH_CAPABILITY_ID = "content_publish"


class ContentWorkflowComposition:
    """Application composition for the first content source-to-clip slice."""

    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        execution_repository: ExecutionRepository,
        acquisition: Capability,
        transcription: Capability,
        clip_extraction: Capability,
        publishing: Capability,
    ) -> None:
        registry = CapabilityRegistry()
        registry.register(CONTENT_ACQUIRE_CAPABILITY_ID, acquisition)
        registry.register(CONTENT_TRANSCRIBE_CAPABILITY_ID, transcription)
        registry.register(CONTENT_CLIP_EXTRACTION_CAPABILITY_ID, clip_extraction)
        registry.register(CONTENT_PUBLISH_CAPABILITY_ID, publishing)

        dispatcher = CapabilityDispatcher(registry)
        self._start = StartWorkflowExecution(
            workflow_repository,
            execution_repository,
        )
        self._execute_step = ExecuteWorkflowStep(
            workflow_repository,
            execution_repository,
            dispatcher,
            ConditionEvaluator(),
        )

    def start(self, workflow_id):
        return self._start.execute(workflow_id)

    def execute_step(self, execution_id, context: ExecutionContext):
        return self._execute_step.execute(execution_id, context)
