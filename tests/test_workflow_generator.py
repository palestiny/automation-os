from app.application.workflow_generation import WorkflowCandidate, WorkflowCandidateStep
from app.application.workflow_generator import WorkflowGenerator
from app.domain.intent import Intent


class FakeWorkflowGenerator:
    def generate(self, intent: Intent) -> WorkflowCandidate:
        return WorkflowCandidate.create(
            "Generated workflow",
            [intent.goal],
            capabilities=["content.acquire"],
            steps=[WorkflowCandidateStep.create("Acquire source", "content.acquire")],
        )


def test_workflow_generator_boundary_returns_candidate():
    generator: WorkflowGenerator = FakeWorkflowGenerator()
    candidate = generator.generate(Intent.create("create_short_video"))
    assert candidate.name == "Generated workflow"
    assert candidate.supported_goals == ("create_short_video",)
    assert candidate.capabilities == ("content.acquire",)


def test_workflow_generator_is_provider_neutral():
    generator: WorkflowGenerator = FakeWorkflowGenerator()
    assert hasattr(generator, "generate")
