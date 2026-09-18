from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.capability_registry import CapabilityRegistry
from app.application.execution_context import ExecutionContext
from app.application.execute_workflow_step import ExecuteWorkflowStep
from app.application.start_workflow_execution import StartWorkflowExecution
from app.domain.business_reporting import BusinessData, ReportAsset, ReportSpecification
from app.domain.workflow import Workflow, WorkflowStep
from app.infrastructure.capabilities.business_reporting import InMemoryBusinessReportCapability
from app.infrastructure.persistence.in_memory import InMemoryExecutionRepository, InMemoryWorkflowRepository


def test_business_reporting_uses_shared_workflow_execution_pipeline():
    workflow = Workflow.create(
        name="Business Report",
        steps=[
            WorkflowStep.create(
                name="Generate report",
                capability="generate_business_report",
            )
        ],
        supported_goals=["generate_business_report"],
    )
    workflow.publish()

    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    workflows.save(workflow)

    registry = CapabilityRegistry()
    registry.register("generate_business_report", InMemoryBusinessReportCapability())

    execution = StartWorkflowExecution(workflows, executions).execute(workflow.id)
    context = execution.context
    context.set("business_data", BusinessData.create({"revenue": 100}))
    context.set(
        "report_specification",
        ReportSpecification.create("Sales", "json"),
    )

    result = ExecuteWorkflowStep(
        workflow_repository=workflows,
        execution_repository=executions,
        capability_dispatcher=CapabilityDispatcher(registry),
    ).execute(execution.id)

    assert result.execution.state.value == "completed"
    assert isinstance(context.get("report_asset"), ReportAsset)
