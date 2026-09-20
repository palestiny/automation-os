# Phase 8.7 — Execution Recovery Design Gate

## Status
**Accepted — Project Owner decisions recorded; implementation may proceed**

## Purpose
Define how Automation OS detects and handles executions left in non-terminal states after process or application failure now that durable persistence exists.

## Accepted Decisions

### 1. Recovery outcome
**Option A — Mark interrupted RUNNING executions as FAILED.** Recovery identifies stale RUNNING executions and transitions them through the existing lifecycle boundary to FAILED. It does not move executions directly to RETRYING.

Rationale: FAILED already represents an unsuccessful/interrupted attempt; existing explicit retry semantics can be reused; recovery does not implicitly re-execute side effects.

### 2. Stale detection
**Configurable timeout policy.** An execution is stale when its persisted RUNNING state and start/ownership timestamp exceed the configured recovery timeout. The timeout belongs to recovery/application policy, not a fixed domain constant.

### 3. Recovery policy ownership
**Recovery Policy/application configuration.** Execution remains responsible for lifecycle legality; Recovery Policy decides whether the persisted execution is stale.

### 4. Recovery does not execute workflow work
Recovery is state recovery only. It must not execute workflow steps, create an execution context for workflow execution, or invoke ExecuteWorkflow.

### 5. Recovery does not implicitly retry
Detecting a stale execution must never silently request another attempt. This protects against duplicate external side effects when a process may have crashed after an external action but before completion was persisted.

### 6. Invocation model
**Application recovery service without a new background worker.** Phase 8.7 introduces a recover-stale-execution application boundary. Scheduler loops, background workers, queues, and distributed coordinators are not introduced.

### 7. Batch recovery
**Deterministic sequential batch recovery.** A batch boundary may identify stale RUNNING executions and recover them one at a time. Parallel recovery is deferred.

### 8. Concurrency semantics
**Conditional persistence transition.** Recovery must only apply the transition when the execution is still RUNNING. A stale observation must not overwrite a concurrent transition to another state. PostgreSQL must enforce this at the persistence boundary.

### 9. Recovery evidence
**Record an auditable recovery reason.** History remains evidence and never becomes a second lifecycle authority.

### 10. WAITING executions
**Do not automatically convert WAITING to RUNNING or FAILED.** WAITING remains externally resumable through the existing resume boundary.

## Lifecycle Model
The accepted recovery path is: RUNNING → FAILED → RETRYING → RUNNING.

RUNNING → FAILED is performed by stale-execution recovery. FAILED → RETRYING requires the existing explicit retry boundary. RETRYING → RUNNING uses the existing retry-start lifecycle. Workflow execution remains owned by ExecuteWorkflow. No RECOVERING state is added.

## TDD RED Plan
1. Persisted RUNNING execution is detected as recoverable after restart.
2. Non-stale RUNNING execution is not recovered.
3. Recovery produces deterministic evidence/reason.
4. WAITING execution is not silently converted to RUNNING or FAILED.
5. Re-running recovery is idempotent.
6. Recovery does not create a second execution identity.
7. Existing retry flow remains legal after recovery.
8. Terminal executions are ignored.
9. Recovery does not execute workflow steps.
10. Concurrent recovery cannot overwrite a newer lifecycle state.
11. Batch recovery is deterministic and sequential.
12. Timeout configuration is respected and reference time is testable.

## Deferred
- Distributed leases.
- Heartbeats.
- Worker queues.
- Automatic retry/backoff.
- Cross-process execution ownership.
- Parallel/distributed recovery.
- Workflow versioning.
- Multi-tenancy and authorization.
- HA/replication operations.

## Decision Record
The Project Owner selected **Option A — RUNNING → FAILED** and accepted the associated decisions above.

The Design Gate is now **Accepted** and GREEN implementation may begin.