# Capability Failure and Retry Semantics Design Gate

Status: Approved
Date: 2026-09-18
Issue: #66

## Purpose

Define how capability outcomes cross the application boundary into the existing Execution lifecycle without moving retry or workflow lifecycle responsibilities into capabilities.

## Decisions

1. `CapabilityResult.failure(...)` is a handled capability outcome. It is not an Execution state and does not decide retry behavior.
2. `ExecuteWorkflowStep` is responsible for translating a failed capability outcome into the existing `Execution.fail()` transition.
3. A failed capability never calls `complete_step()`; `current_step` therefore remains unchanged.
4. The failed Execution is persisted before the application reports the failure to its caller.
5. Unexpected exceptions raised by a capability are not converted into `CapabilityResult.failure`. The application boundary marks the Execution FAILED, persists it, and re-raises the original exception.
6. Retry remains an explicit runtime operation: `Execution.retry()` transitions FAILED → RETRYING and increments `attempt`; a subsequent `Execution.start()` transitions RETRYING → RUNNING.
7. Capabilities never call `fail()`, `retry()`, `complete_step()`, or otherwise mutate Execution lifecycle.
8. No automatic retry loop, retry limit, provider-specific transient/permanent classification, or worker is introduced in this increment.
9. A capability failure does not set `finished_at`; FAILED remains retryable.
10. Successful capability handling retains the existing progression and final-step completion semantics.

## Runtime Flow

Successful outcome:

`ExecuteWorkflowStep` → dispatch → `CapabilityResult.success()` → `Execution.complete_step()` → persist → continue/complete.

Handled failure:

`ExecuteWorkflowStep` → dispatch → `CapabilityResult.failure(...)` → `Execution.fail()` → persist FAILED → report failure.

Unexpected exception:

`ExecuteWorkflowStep` → dispatch → exception → `Execution.fail()` → persist FAILED → re-raise original exception.

Explicit retry:

`FAILED` → `Execution.retry()` → `RETRYING` → `Execution.start()` → `RUNNING`.

The capability is not involved in the retry transition.

## Why the Application Boundary Owns Translation

The capability contract describes an operation's outcome. The Execution aggregate describes workflow lifecycle. Keeping translation in `ExecuteWorkflowStep` avoids making plugins aware of domain lifecycle and avoids introducing a second retry state machine.

The application boundary may invoke the domain transition, but it does not reproduce the transition rules. `Execution.fail()` remains the sole owner of RUNNING → FAILED validation.

## Failure Categories

### Handled capability failure

A capability returns `CapabilityResult.failure(error)`.

- Mark Execution FAILED.
- Persist the aggregate.
- Do not advance the step.
- Raise an application-level error to preserve the existing use-case contract.
- Leave `finished_at` unset.

### Unexpected capability exception

A capability raises an exception.

- Mark Execution FAILED.
- Persist the aggregate.
- Re-raise the same exception.
- Do not advance the step.
- Do not silently convert programming/configuration/provider defects into a normal result.

### Retry

Retry is explicit and separate from capability invocation.

- Only FAILED executions can retry.
- `retry()` increments `attempt` and enters RETRYING.
- `start()` returns RETRYING to RUNNING.
- The same `current_step` is retried because failed processing never advanced it.

## TDD Scope

The smallest implementation increment verifies:

- handled capability failure moves Execution to FAILED;
- handled capability failure is persisted;
- failed execution does not advance or complete;
- unexpected capability exception moves Execution to FAILED and is persisted;
- the original unexpected exception is re-raised;
- FAILED keeps `finished_at` unset;
- retry remains explicit through the existing Execution lifecycle;
- successful and skipped step behavior remains unchanged.

## Deferred

- Automatic retry orchestration.
- Retry limits/backoff/jitter.
- Provider-specific retry classification.
- Retry queues and workers.
- Background execution.
- Idempotency/deduplication.
- Retry persistence/history beyond the current Execution aggregate.
- Observability and failure taxonomy.
- Compensation/rollback.

## Exit Criteria

This gate is complete when failure translation, persistence, and retry ownership are covered by tests; the implementation does not duplicate Execution lifecycle rules; documentation and roadmap are updated; and CI passes.
