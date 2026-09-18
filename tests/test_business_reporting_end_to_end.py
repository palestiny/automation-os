from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.capability_registry import CapabilityRegistry
from app.application.condition_evaluator import ConditionEvaluator
from app.application.execution_context import ExecutionContext
from app.application.execute_workflow_step import ExecuteWorkflowStep
from app.application.intent_execution import ExecuteIntent
from app.application.intent_analysis import IntentAnalyzer
from app.application.request_execution import ExecuteRequest
from app.application.start_workflow_execution import StartWorkflowExecution
from app.domain.business_reporting import BusinessData, ReportAsset, ReportSpecification
from app.domain.intent import Intent
from app.domain.workflow import Workflow, WorkflowStep
from app.infrastructure.capabilities.business_reporting import InMemoryBusinessReportCapability
from app.infrastructure.persistence.in_memory import InMemoryExecutionRepository, InMemoryWorkflowRepository


class FakeReportingAnalyzer:
    def analyze(self, request: str) -> Intent:
        assert request
        return Intent.create("generate_business_report")


def test_business_reporting_can_run_through_raw_request_path():
    workflow = Workflow.create(
        name="Business Report",
        steps=[WorkflowStep.create("Generate", "generate_business_report")],
        supported_goals=["generate_business_report"],
    )
    workflow.publish()

    workflow_repository = InMemoryWorkflowRepository()
    execution_repository = InMemoryExecutionRepository()
    workflow_repository.save(workflow)

    start = StartWorkflowExecution(workflow_repository, execution_repository)
    request_execution = ExecuteRequest(
        analyzer=FakeReportingAnalyzer(),
        execute_intent=ExecuteIntent(
            workflows=[workflow],
            start_workflow_execution=start,
        ),
    )

    result = request_execution.execute("Generate my report")

    assert result.execution is not None
    execution = result.execution

    context = ExecutionContext()
    context.set("business_data", BusinessData.create({"revenue": 100}))
    context.set(
        "report_specification",
        ReportSpecification.create("Sales", "json"),
    )

    registry = CapabilityRegistry()
    registry.register("generate_business_report", InMemoryBusinessReportCapability())

    ExecuteWorkflowStep(
        workflow_repository=workflow_repository,
        execution_repository=execution_repository,
        dispatcher=CapabilityDispatcher(registry),
        condition_evaluator=ConditionEvaluator(),
    ).execute(execution.id, context)

    persisted = execution_repository.get(execution.id)
    assert persisted is not None
    assert persisted.state.value == "completed"
    assert isinstance(context.get("report_asset"), ReportAsset)
