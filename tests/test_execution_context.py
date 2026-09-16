import pytest

from app.domain.execution_context import ExecutionContext


def test_execution_context_stores_and_reads_inputs():
    context = ExecutionContext.create(inputs={"video_url": "https://example.com/video"})

    assert context.get_input("video_url") == "https://example.com/video"


def test_execution_context_can_store_and_read_working_data():
    context = ExecutionContext.create()

    context.set_working("transcript", "hello world")

    assert context.get_working("transcript") == "hello world"


def test_execution_context_can_store_and_read_runtime_outputs():
    context = ExecutionContext.create()

    context.set_output("duration_seconds", 42)

    assert context.get_output("duration_seconds") == 42


def test_execution_context_does_not_expose_raw_storage_as_domain_contract():
    context = ExecutionContext.create()

    assert not hasattr(context, "data")


def test_execution_context_raises_when_requested_input_is_missing():
    context = ExecutionContext.create()

    with pytest.raises(KeyError):
        context.get_input("missing")


def test_execution_context_raises_when_requested_working_data_is_missing():
    context = ExecutionContext.create()

    with pytest.raises(KeyError):
        context.get_working("missing")


def test_execution_context_raises_when_requested_output_is_missing():
    context = ExecutionContext.create()

    with pytest.raises(KeyError):
        context.get_output("missing")
