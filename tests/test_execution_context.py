from app.application.execution_context import ExecutionContext


def test_execution_context_can_store_and_get_value():
    context = ExecutionContext()

    context.set("video_url", "https://example.com/video")

    assert context.get("video_url") == "https://example.com/video"