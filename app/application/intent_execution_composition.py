from __future__ import annotations

from app.application.intent_goal_catalog import IntentGoalCatalog
from app.application.intent_execution import ExecuteIntent
from app.application.start_workflow_execution import StartWorkflowExecution
from app.application.workflow_selection import SelectWorkflow
from app.domain.workflow import Workflow


class IntentExecutionComposition:
    """Composition root for intent execution dependencies."""

    def __init__(
        self,
        workflows: list[Workflow],
        start_workflow_execution: StartWorkflowExecution,
        goal_catalog: IntentGoalCatalog,
    ) -> None:
        if not isinstance(goal_catalog, IntentGoalCatalog):
            raise TypeError("goal_catalog must be an IntentGoalCatalog instance")

        self.execute_intent = ExecuteIntent(
            workflows=workflows,
            start_workflow_execution=start_workflow_execution,
            goal_catalog=goal_catalog,
        )
        self.selector = SelectWorkflow(workflows)
