from dataclasses import FrozenInstanceError

import pytest

from app.domain.intent import Intent


def test_intent_requires_non_empty_goal():
    with pytest.raises(ValueError, match="Intent goal cannot be empty"):
        Intent.create("   ")


def test_intent_stores_goal_and_parameters():
    intent = Intent.create(
        goal="create_short_video",
        parameters={"source_url": "https://example.com/video", "duration": 30},
    )

    assert intent.goal == "create_short_video"
    assert intent.parameters["source_url"] == "https://example.com/video"
    assert intent.parameters["duration"] == 30


def test_intent_parameters_are_immutable():
    intent = Intent.create(
        goal="create_short_video",
        parameters={"duration": 30},
    )

    with pytest.raises(TypeError):
        intent.parameters["duration"] = 60


def test_intent_is_immutable():
    intent = Intent.create(goal="create_short_video")

    with pytest.raises(FrozenInstanceError):
        intent.goal = "publish_content"


def test_intent_rejects_empty_parameter_names():
    with pytest.raises(ValueError, match="Intent parameter names cannot be empty"):
        Intent.create(
            goal="create_short_video",
            parameters={"   ": "value"},
        )


def test_intent_rejects_non_string_parameter_names():
    with pytest.raises(ValueError, match="Intent parameter names must be strings"):
        Intent.create(
            goal="create_short_video",
            parameters={1: "value"},
        )
