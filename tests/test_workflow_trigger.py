from dataclasses import FrozenInstanceError

import pytest

from app.application.trigger_matcher import TriggerMatcher
from app.domain.event import Event
from app.domain.workflow import Trigger, Workflow, WorkflowStep


def test_trigger_can_be_created():
    trigger = Trigger.create("video.uploaded")

    assert trigger.event_type == "video.uploaded"


def test_trigger_rejects_empty_event_type():
    with pytest.raises(ValueError):
        Trigger.create("")


def test_event_can_be_created():
    event = Event.create("video.uploaded")

    assert event.event_type == "video.uploaded"


def test_event_rejects_empty_event_type():
    with pytest.raises(ValueError):
        Event.create("")


def test_workflow_can_contain_triggers():
    trigger = Trigger.create("video.uploaded")
    workflow = Workflow.create(
        "Pipeline",
        [WorkflowStep.create("Process", "test")],
        triggers=[trigger],
    )

    assert workflow.triggers == (trigger,)


def test_trigger_is_immutable():
    trigger = Trigger.create("video.uploaded")

    with pytest.raises(FrozenInstanceError):
        trigger.event_type = "video.deleted"


def test_published_workflow_cannot_add_trigger():
    workflow = Workflow.create(
        "Pipeline",
        [WorkflowStep.create("Process", "test")],
    )
    workflow.publish()

    with pytest.raises(ValueError):
        workflow.add_trigger(Trigger.create("video.uploaded"))


def test_matching_event_resolves_workflow_id():
    trigger = Trigger.create("video.uploaded")
    workflow = Workflow.create(
        "Pipeline",
        [WorkflowStep.create("Process", "test")],
        triggers=[trigger],
    )
    event = Event.create("video.uploaded")

    matcher = TriggerMatcher()

    assert matcher.match(event, workflow) == workflow.id


def test_non_matching_event_returns_no_workflow():
    workflow = Workflow.create(
        "Pipeline",
        [WorkflowStep.create("Process", "test")],
        triggers=[Trigger.create("video.uploaded")],
    )
    event = Event.create("video.deleted")

    assert TriggerMatcher().match(event, workflow) is None
