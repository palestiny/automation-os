# Phase 8.12 — External Event Integration Design Gate

## Status

**DESIGN PREPARATION — Option A selected; remaining contract decisions pending**

## Purpose

Introduce an explicit boundary for receiving external events and translating them into the platform's existing normalized `Event` contract without making transport infrastructure an execution authority.

## Repository Evidence

The platform already has:
- `Event(event_type)` as the minimal normalized event value object;
- `TriggerMatcher` for deterministic matching;
- `TriggerInvocation` for matching published workflows and delegating to `StartWorkflowExecution`;
- durable PostgreSQL persistence and execution-start idempotency;
- scheduling/trigger boundaries that intentionally exclude external transport.

The missing boundary is the adapter between external event sources and the normalized internal event consumed by `TriggerInvocation`.

## Objective

Allow external systems to produce normalized events while preserving:
- transport independence;
- deterministic event normalization;
- existing trigger matching;
- existing execution-start idempotency;
- explicit failure semantics;
- no direct external control over Execution lifecycle.

## Scope

- external event ingestion port;
- source/provider identity;
- deterministic normalization into `Event`;
- validation of incoming event type;
- explicit handoff to `TriggerInvocation`;
- focused tests;
- transport-independent adapter contract;
- documentation and exit review.

## Out of Scope

- implementing a specific webhook vendor;
- message broker infrastructure;
- authentication/authorization;
- multi-tenancy;
- workflow recovery;
- AI event interpretation;
- marketplace behavior;
- replacing TriggerInvocation;
- arbitrary expression/payload routing.

## Options

### Option A — Application-level External Event Ingestion Port

Define a small application port that accepts an external event envelope and produces a normalized `Event`, then delegates to the existing `TriggerInvocation` boundary.

Pros:
- preserves transport independence;
- keeps normalization separate from execution;
- easy deterministic testing;
- allows webhook, queue, polling, or other adapters later;
- reuses existing trigger/idempotency semantics.

Trade-offs:
- introduces one explicit adapter boundary;
- source-specific authentication remains outside this capability unless separately integrated.

### Option B — Transport-specific Event Handlers

Add webhook/queue handlers directly around TriggerInvocation.

Pros:
- faster for one concrete integration.

Trade-offs:
- couples the application to transport details;
- encourages duplicate validation and event conversion paths;
- makes later transport expansion harder.

### Option C — Event Bus as the Core Boundary

Introduce a generic event bus and publish/subscribe model.

Pros:
- broad future extensibility.

Trade-offs:
- substantially larger scope;
- introduces delivery, ordering, retry, subscription, and operational semantics that are not required by the current problem;
- risks making infrastructure more authoritative than the existing trigger/execution boundaries.

## Recommended Direction

**Option A — Application-level External Event Ingestion Port**.

It is the smallest boundary that closes the architectural gap while preserving the existing deterministic TriggerInvocation contract.

This recommendation does not authorize GREEN implementation until the Project Owner approves the architecture.

## Remaining Decision Questions

Option A is approved. The following contract details still require an explicit decision before GREEN implementation:

1. Should the first version support one or multiple external event sources?
2. Should source identity be part of the normalized Event or remain envelope metadata?
3. Should duplicate external deliveries be deduplicated at this boundary, or should callers provide an idempotency key to the existing execution-start path?
4. What minimum external envelope is required beyond `event_type`?
5. Should normalization be one deterministic adapter contract or a registry of source-specific normalizers?
6. What failure is returned when an external event cannot be normalized?
7. Should transport authentication remain entirely outside this phase?

## Required RED Tests After Decision

- valid external envelope normalizes to Event;
- invalid/empty event type is rejected;
- source metadata does not alter trigger matching unless explicitly part of the decision;
- normalized event delegates only through TriggerInvocation;
- no matching workflow causes no execution;
- existing trigger/start idempotency semantics remain unchanged;
- normalization failure cannot create an execution.

## Exit Criteria

- Design decision recorded.
- RED tests define the selected contract.
- GREEN implementation passes focused tests.
- Existing full regression passes.
- Documentation and exit review are updated.
