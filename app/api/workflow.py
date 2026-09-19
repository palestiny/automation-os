from fastapi import APIRouter, Query

from app.application.list_workflows import ListWorkflows
from app.core.execution_dependencies import workflow_repository
from app.schemas.workflow.response import WorkflowParameterResponse, WorkflowResponse

router = APIRouter(prefix="/workflows", tags=["workflows"])

list_workflows = ListWorkflows(workflow_repository)


@router.get("", response_model=list[WorkflowResponse])
def get_workflows(goal: str | None = Query(default=None)):
    workflows = list_workflows.execute(goal=goal)
    return [
        WorkflowResponse(
            workflow_id=workflow.id,
            name=workflow.name,
            supported_goals=workflow.supported_goals,
            required_parameters=workflow.required_parameters,
            parameter_types=tuple(
                WorkflowParameterResponse(name=p.name, type=p.type)
                for p in workflow.parameter_types
            ),
        )
        for workflow in workflows
    ]
