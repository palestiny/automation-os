from fastapi import APIRouter, Depends, Query

from app.api.auth import get_authorization_context
from app.application.authorization import AuthorizationContext
from app.application.list_workflows import ListWorkflows
from app.core.execution_dependencies import build_tenant_persistence
from app.schemas.workflow.response import WorkflowParameterResponse, WorkflowResponse

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("", response_model=list[WorkflowResponse])
def get_workflows(
    goal: str | None = Query(default=None),
    automation_domain: str | None = Query(default=None),
    tag: list[str] | None = Query(default=None),
    context: AuthorizationContext = Depends(get_authorization_context),
):
    try:
        repositories = build_tenant_persistence(context)
        workflow_repository = repositories[0]
        workflows = ListWorkflows(workflow_repository).execute(
            goal=goal,
            automation_domain=automation_domain,
            tags=tuple(tag or ()),
        )
    except RuntimeError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail=str(exc)) from exc

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
            automation_domain=workflow.automation_domain,
            discovery_tags=workflow.discovery_tags,
        )
        for workflow in workflows
    ]
