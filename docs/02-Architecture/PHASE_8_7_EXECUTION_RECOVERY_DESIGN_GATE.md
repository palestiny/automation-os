# Phase 8.7 — Execution Recovery Design Gate

## Status

**Design Preparation — Project Owner decision required before implementation**

## Purpose

Define how Automation OS detects and handles executions left in non-terminal states after process or application failure now that durable persistence exists.

## Repository Evidence

Phase 8.6 provides durable Workflow and Execution state plus append-only lifecycle history. The existing Execution lifecycle remains the single authority for legal state transitions.

A process crash can leave persisted executions in states such as RUNNING or WAITING without an active in-memory worker/context. Durable persistence makes those states survive restart, but it does not itself define what recovery should mean.

## Goals

- Detect persisted executions that require recovery.
- Preserve Execution as lifecycle authority.
- Make recovery deterministic and auditable.
- Avoid silently inventing a second execution state machine.
- Preserve idempotency and execution identity across recovery.
- Define safe behavior for interrupted RUNNING executions.
- Define whether WAITING executions are recoverable automatically or remain externally resumed.

## Constraints

1. Recovery must use existing Execution lifecycle semantics or explicitly extend them through a Design Gate.
2. Recovery must not mutate history as a substitute for lifecycle state.
3. Recovery must not duplicate workflow execution orchestration.
4. Recovery decisions must be deterministic and testable.
5. Automatic retry, backoff, worker queues, and distributed leases are separate concerns unless explicitly selected.
6. Durable persistence remains the source of persisted execution identity and state.
7. No authorization, multi-tenancy, or workflow versioning is added here.

## Decision Dimensions

The critical question is:

**What should happen to an execution persisted as RUNNING after the process that owned its active execution context disappears?**

### Option A — Mark Interrupted RUNNING Executions as FAILED

Recovery identifies stale RUNNING executions and transitions them to FAILED through an explicit recovery boundary.

Advantages:
- Clear terminal evidence of the interrupted attempt.
- Reuses the existing FAILED state and retry boundary.
- Does not automatically re-execute work.

Trade-offs:
- Requires a definition of staleness/ownership.
- Recovery does not continue the interrupted step automatically.

### Option B — Move Interrupted RUNNING Executions to RETRYING

Recovery identifies stale RUNNING executions and prepares them for a later retry start.

Advantages:
- Directly connects crash recovery to the existing retry lifecycle.
- Makes the interrupted attempt explicit.

Trade-offs:
- Blends recovery with retry policy.
- Requires careful semantics for whether retry is automatic or only prepared.

### Option C — Add an Explicit RECOVERING Lifecycle State

Introduce a new domain lifecycle state for persisted executions undergoing recovery.

Advantages:
- Makes recovery visible as a first-class lifecycle phase.
- Can model richer recovery semantics.

Trade-offs:
- Changes the core Execution state model.
- Requires a broader lifecycle Design Gate and migration implications.
- Risks adding complexity before worker/lease semantics exist.

## Proposed Engineering Default — Not Yet Committed

Keep the existing lifecycle unchanged and recover stale RUNNING executions into FAILED, then reuse the explicit retry boundary when a retry is intentionally requested.

This minimizes new lifecycle semantics while making crash interruption explicit.

The proposal is not a project decision.

## TDD RED Plan

1. Persisted RUNNING execution is detected as recoverable after restart.
2. Non-stale RUNNING execution is not recovered.
3. Recovery produces deterministic evidence.
4. WAITING execution is not silently converted to RUNNING.
5. Re-running recovery is idempotent.
6. Recovery does not create a second execution identity.
7. Existing retry flow remains legal after recovery.
8. Terminal executions are ignored.
9. Recovery does not execute workflow steps by itself unless explicitly selected.

## Deferred

- Distributed leases.
- Heartbeats.
- Worker queues.
- Automatic retry/backoff.
- Cross-process execution ownership.
- Workflow versioning.
- Multi-tenancy and authorization.
- HA/replication operations.

## Decision Required

The Project Owner must choose A, B, or C before GREEN implementation of Phase 8.7 begins.
