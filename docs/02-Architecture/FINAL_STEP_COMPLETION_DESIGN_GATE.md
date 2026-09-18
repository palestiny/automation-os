# Phase 3 — Final Step Completion Design Gate

Status: Design baseline
Date: 2026-09-18
Issue: #53

## Decision

`ExecuteWorkflowStep` owns the terminal transition from `RUNNING` to `COMPLETED` when the processed step is the final WorkflowStep.

## Rationale

The step executor already owns the atomic application operation of processing the current step. It resolves the workflow definition, determines whether the step is eligible, delegates capability execution, advances the Execution, and persists the runtime change. Completion is a direct consequence of successfully processing the final step and does not require a second application call or a second lifecycle coordinator.

This keeps the runtime flow explicit without introducing a broader workflow runner prematurely.

## Semantics

1. A non-final successful step advances `current_step` and leaves the Execution `RUNNING`.
2. A false condition is a successfully processed/skipped step. If it is the final step, the Execution is completed.
3. A successful capability on the final step completes the Execution.
4. `Execution.complete()` remains the domain owner of the lifecycle transition and `finished_at` timestamp.
5. The repository persists the final state after the domain transition.
6. Capability failure never completes the Execution and never advances `current_step`.
7. Condition evaluation failure never completes or advances the Execution.
8. The Execution must already be `RUNNING`; no other state is made terminal by this use case.

## Result Contract

`StepExecutionResult` reports whether the step was processed and skipped. `has_more_steps` remains available for callers that want to know whether another step exists. For a final step it is `False` and the returned persisted Execution is `COMPLETED`.

## Deferred

- executing multiple steps in one call;
- background workers and scheduling;
- parallel execution;
- event publication;
- transaction/Unit of Work;
- automatic retry orchestration;
- branching workflow graphs.

## Trade-off

The application use case now contains a small amount of workflow-completion orchestration. The benefit is an explicit single-step runtime boundary with no extra coordinator. If future requirements introduce multi-step scheduling, pausing, events, or parallelism, the orchestration boundary can be revisited through a new design gate rather than expanded speculatively.
