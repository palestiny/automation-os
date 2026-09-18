import pytest

from app.application.intent_execution_composition import IntentExecutionComposition
from app.application.intent_goal_catalog import IntentGoalCatalog
from app.application.start_workflow_execution import StartWorkflowExecution
from app.infrastructure.persistence.in_memory import (
    InMemoryExecutionRepository,
    InMemoryWorkflowRepository,
)
from app.domain.workflow import Workflow, WorkflowStep


def test_composition_wires_goal_catalog_into_intent_execution():
    workflow = Workflow.create(
        name="Content",
        steps=[WorkflowStep.create(name="Run", capability="content_run")],
        supported_goals=["create_short_video"],
    )
    workflow.publish()

    composition = IntentExecutionComposition(
        workflows=[workflow],
        start_workflow_execution=StartWorkflowExecution(
            InMemoryWorkflowRepository(),
            InMemoryExecutionRepository(),
        ),
        goal_catalog=IntentGoalCatalog.create(["create_short_video"]),
    )

    assert composition.execute_intent is not None
    assert composition.selector is not None


def test_composition_requires_goal_catalog():
    with pytest.raises(TypeError):
        IntentExecutionComposition(
            workflows=[],
            start_workflow_execution=None,
            goal_catalog=None,
        )
