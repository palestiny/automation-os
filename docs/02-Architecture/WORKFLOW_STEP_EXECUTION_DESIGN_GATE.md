# Phase 3 — Workflow Step Execution Design Gate

Status: Design baseline
Date: 2026-09-18
Issue: #51

## Purpose

Define the application boundary that executes one current WorkflowStep for an existing RUNNING Execution.

## Committed Decisions

### 1. Step execution is separate from execution creation

StartWorkflowExecution creates and starts the runtime Execution. A separate use case executes the current step.

### 2. The use case resolves both aggregates

The use case loads:
1. Execution by execution ID;
2. Workflow by the Execution workflow ID.

Missing resources are explicit application errors.

### 3. Execution must be RUNNING

A step cannot execute from CREATED, WAITING, RETRYING, COMPLETED, FAILED, or CANCELLED.

### 4. Current step is selected by Execution.current_step

The index maps directly to the ordered Workflow.steps collection. No second ordering model is introduced.

### 5. Optional Condition is evaluated before capability dispatch

If the step has no condition, it is eligible.

If the step has a condition, ConditionEvaluator evaluates it against the ExecutionContext.

A false condition means the step is skipped: no capability dispatch occurs, and the Execution advances by one step.

### 6. Capability dispatch is the execution boundary

For an eligible step, the use case delegates capability execution to the existing CapabilityDispatcher. It does not know provider implementation details.

### 7. Step progression happens only after successful handling

A dispatched capability must complete successfully before Execution.complete_step() is called.

Capability failure is not converted into success or step completion. The existing Execution failure lifecycle remains responsible for failure/retry transitions.

### 8. End-of-workflow behavior is not silently added

This first increment must define whether the current step is the final step without introducing a new Execution terminal transition accidentally.

The initial contract will report that the step was processed and whether more steps remain. A later application decision will own the transition from the final processed step to COMPLETED.

## Deferred

- automatic execution of all steps in one loop;
- scheduling/background workers;
- event publication;
- durable ExecutionContext;
- transaction/Unit of Work;
- parallel steps;
- branching/conditional workflow graphs;
- retry policy orchestration around dispatcher failures;
- final-step completion policy.

## First TDD Increment

Prove:
- rejects missing Execution;
- rejects missing Workflow;
- rejects non-RUNNING Execution;
- rejects an invalid current-step index;
- evaluates an optional condition;
- skips a false condition without dispatch;
- dispatches an eligible capability;
- advances the Execution only after successful dispatch;
- does not advance when dispatch fails.

The exact dispatcher interface and result contract must be verified against the existing implementation before coding.
