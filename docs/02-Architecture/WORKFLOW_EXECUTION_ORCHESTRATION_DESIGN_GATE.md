# Workflow Execution Orchestration Design Gate

## Status

Accepted / Implemented

## Purpose

Define the application boundary that drives a started Execution through its Workflow steps without creating a second execution lifecycle.

## Committed Decisions

1. The orchestration use case operates on an existing Execution identity.
2. The ExecutionRepository remains the lifecycle source of truth.
3. Each step is executed exclusively through the existing ExecuteWorkflowStep use case.
4. The same ExecutionContext instance is passed to every step in one orchestration call.
5. The orchestrator continues while the Execution remains RUNNING.
6. A successfully processed step advances the Execution. The final step transitions the Execution to COMPLETED through the existing step use case.
7. Capability failures and other step failures propagate unchanged; ExecuteWorkflowStep remains responsible for marking the Execution FAILED and persisting that state.
8. The orchestration use case does not implement capability dispatch, conditions, retries, cancellation, or new state transitions.
9. The orchestration use case does not execute an Execution that is not RUNNING.
10. No background worker, scheduling, transaction abstraction, durable ExecutionContext, or event bus is introduced by this increment.

## Result Contract

The use case returns the final Execution after all currently runnable steps have been processed.

For a successful finite Workflow:

**RUNNING Execution → step 1 → step 2 → ... → final step → COMPLETED**

For a failed capability:

**RUNNING Execution → failing step → FAILED**, with the original failure propagated.

## Deferred

- asynchronous/background execution;
- scheduling;
- durable context persistence;
- automatic retry policy;
- pause/resume orchestration;
- event publication;
- parallel workflow branches;
- dynamic workflow mutation;
- autonomous replanning.

## Gate Result

The boundary is narrow enough for deterministic TDD implementation because it composes an already-defined step execution use case rather than duplicating runtime behavior.
