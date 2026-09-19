# Resumed Execution Orchestration Design Gate

## Status

Accepted / Implemented

## Purpose

Define the application composition boundary for resuming a WAITING Execution and then continuing it through the existing workflow orchestrator.

## Committed Decisions

1. Resume remains owned by ResumeExecution.
2. Workflow execution remains owned by ExecuteWorkflow.
3. The composition use case calls ResumeExecution first, then ExecuteWorkflow with a new ExecutionContext for this invocation.
4. The resumed Execution must be RUNNING before orchestration begins.
5. The composition returns the final Execution.
6. A resume failure prevents orchestration.
7. Existing step, capability, condition, failure, and persistence boundaries remain unchanged.
8. No new Execution state or lifecycle transition is introduced.
9. No automatic scheduling, worker, queue, durable context, retry policy, or event bus is introduced.
10. The context is intentionally not durable; preserving context across WAITING periods remains deferred.

## Result Contract

WAITING Execution → ResumeExecution → RUNNING → ExecuteWorkflow → COMPLETED or FAILED.

## TDD Order

RED → GREEN → REFACTOR.

Tests prove successful resume-and-complete, capability failure after resume, and rejection of a non-WAITING execution.

## Explicitly Deferred

- automatic resume;
- durable ExecutionContext across suspension;
- scheduler/worker wake-up;
- resume authorization;
- distributed coordination;
- event publication;
- compensation for external side effects.
