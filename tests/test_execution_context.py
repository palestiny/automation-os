import pytest

from app.application.execution_context import ExecutionContext


def test_execution_context_can_store_and_get_value():
    context = ExecutionContext()

    context.set("video_url", "https://example.com/video")

    assert context.get("video_url") == "https://example.com/video"


def test_execution_context_raises_key_error_for_missing_value():
    context = ExecutionContext()

    with pytest.raises(KeyError):
        context.get("missing")


def test_execution_context_replaces_existing_value():
    context = ExecutionContext()

    context.set("video_url", "https://example.com/old-video")
    context.set("video_url", "https://example.com/new-video")

    assert context.get("video_url") == "https://example.com/new-video"


def test_runtime_connection_state_is_not_writable_through_execution_context_api():
    context = ExecutionContext()

    assert not hasattr(context, "set_runtime_connections")
    with pytest.raises(KeyError):
        context.get_runtime_connections()
