from uuid import UUID

from app.application.trigger_invocation import TriggerInvocation
from app.domain.event import Event
from app.domain.workflow import Trigger, Workflow, WorkflowState, WorkflowStep


class FakeWorkflowRepository:
    def __init__(self, workflows: tuple[Workflow, ...]) -> None:
        self._workflows = workflows

    def all(self) -> tuple[Workflow, ...]:
        return self._workflows


class FakeStartWorkflowExecution:
    def __init__(self) -> None:
        self.workflow_ids: list[UUID] = []
        self.results: dict[UUID, object] = {}

    def execute(self, workflow_id: UUID) -> object:
        self.workflow_ids.append(workflow_id)
        result = object()
        self.results[workflow_id] = result
        return result


def workflow(
    workflow_id: str,
    *,
    published: bool,
    event_type: str = "video.uploaded",
) -> Workflow:
    return Workflow(
        id=UUID(workflow_id),
        name=f"Workflow {workflow_id}",
        _steps=[WorkflowStep.create("Process", "test")],
        state=WorkflowState.PUBLISHED if published else WorkflowState.DRAFT,
        _triggers=[Trigger.create(event_type)],
    )


def test_trigger_invocation_starts_only_matching_published_workflows():
    published = workflow(
        "00000000-0000-0000-0000-000000000002",
        published=True,
    )
    draft = workflow(
        "00000000-0000-0000-0000-000000000001",
        published=False,
    )
    non_matching = workflow(
        "00000000-0000-0000-0000-000000000003",
        published=True,
        event_type="video.deleted",
    )
    repository = FakeWorkflowRepository((draft, non_matching, published))
    starter = FakeStartWorkflowExecution()

    result = TriggerInvocation(repository, starter).invoke(
        Event.create("video.uploaded")
    )

    assert result == (starter.results[published.id],)
    assert starter.workflow_ids == [published.id]


def test_trigger_invocation_returns_no_match_without_starting_execution():
    repository = FakeWorkflowRepository(
        (
            workflow(
                "00000000-0000-0000-0000-000000000001",
                published=True,
                event_type="video.deleted",
            ),
        )
    )
    starter = FakeStartWorkflowExecution()

    result = TriggerInvocation(repository, starter).invoke(
        Event.create("video.uploaded")
    )

    assert result == ()
    assert starter.workflow_ids == []


def test_trigger_invocation_starts_multiple_matches_in_deterministic_workflow_id_order():
    first = workflow(
        "00000000-0000-0000-0000-000000000001",
        published=True,
    )
    second = workflow(
        "00000000-0000-0000-0000-000000000002",
        published=True,
    )
    repository = FakeWorkflowRepository((second, first))
    starter = FakeStartWorkflowExecution()

    result = TriggerInvocation(repository, starter).invoke(
        Event.create("video.uploaded")
    )

    assert starter.workflow_ids == [first.id, second.id]
    assert result == (
        starter.results[first.id],
        starter.results[second.id],
    )


def test_trigger_invocation_delegates_execution_start_to_start_workflow_execution():
    published = workflow(
        "00000000-0000-0000-0000-000000000001",
        published=True,
    )
    repository = FakeWorkflowRepository((published,))
    starter = FakeStartWorkflowExecution()

    TriggerInvocation(repository, starter).invoke(Event.create("video.uploaded"))

    assert starter.workflow_ids == [published.id]
