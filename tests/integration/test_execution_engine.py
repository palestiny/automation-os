from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.capability_registry import CapabilityRegistry
from app.application.capability_result import CapabilityResult
from app.application.orchestrator import Orchestrator
from app.application.retry_policy import RetryPolicy
from app.domain.workflow import Workflow, WorkflowStep


class ProducerCapability:
    def execute(self, context):
        return CapabilityResult.success({"value": 42})


class ConsumerCapability:
    def __init__(self):
        self.received = None

    def execute(self, context):
        self.received = context.get(producer_step_id)
        return CapabilityResult.success()


def test_execution_engine_integrates_registry_dispatcher_and_orchestrator():
    global producer_step_id

    producer_step = WorkflowStep.create("produce", "producer")
    consumer_step = WorkflowStep.create("consume", "consumer")
    producer_step_id = producer_step.id

    workflow = Workflow.create(
        "integration-workflow",
        [producer_step, consumer_step],
    )
    workflow.publish()

    registry = CapabilityRegistry()
    consumer = ConsumerCapability()
    registry.register("producer", ProducerCapability())
    registry.register("consumer", consumer)

    dispatcher = CapabilityDispatcher(registry)
    orchestrator = Orchestrator(dispatcher, RetryPolicy())

    execution = orchestrator.start(workflow)

    assert execution.current_step == 2
    assert execution.state.value == "completed"
    assert consumer.received == {"value": 42}
