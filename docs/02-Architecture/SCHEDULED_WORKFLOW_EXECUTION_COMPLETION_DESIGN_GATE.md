# Scheduled Workflow Execution Completion Design Gate

## Status

Accepted / Implemented

## Purpose

Define the application boundary that connects an already-due scheduled workflow start to the existing multi-step execution orchestrator.

## Committed Decisions

1. Scheduling remains responsible only for deciding whether a request is due.
2. StartDueWorkflowExecution remains responsible for creating a RUNNING Execution for a due published Workflow.
3. A new completion use case composes StartDueWorkflowExecution with ExecuteWorkflow.
4. The same ExecutionContext is created for one due execution and shared across all workflow steps.
5. A request that is not due returns None and does not create or execute an Execution.
6. A due request executes the workflow synchronously through ExecuteWorkflow.
7. Execution lifecycle, step execution, capability dispatch, conditions, retries, and persistence remain owned by their existing boundaries.
8. No scheduler loop, worker, queue, persistence model for schedules, recurring schedule semantics, or background infrastructure is introduced.

## Result Contract

For a due request:

**Scheduled Request → Due Check → Start RUNNING Execution → ExecuteWorkflow → COMPLETED or FAILED**

For a future request:

**Scheduled Request → Not Due → None**

## Deferred

- recurring schedules;
- schedule persistence;
- scheduler polling/worker;
- background execution;
- queues;
- distributed locking;
- durable ExecutionContext;
- automatic retries;
- parallel execution.

## Gate Result

The composition closes the currently implemented scheduling-to-runtime path without moving responsibilities between existing application boundaries.
