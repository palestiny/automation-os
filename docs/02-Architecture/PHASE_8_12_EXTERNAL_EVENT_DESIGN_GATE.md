# Phase 8.12 — External Event Integration Design Gate

## Status

**DESIGN PREPARATION — decision pending**

## Purpose

Connect real external event sources to the existing normalized trigger/invocation boundary without allowing transport-specific concerns to leak into workflow execution.

## Repository Baseline

The platform already has:

- normalized `Event` domain vocabulary;
- deterministic `TriggerMatcher`;
- application-level `TriggerInvocation`;
- reliable `StartWorkflowExecution`;
- workflow-start idempotency;
- durable PostgreSQL persistence;
- execution history and observability.

The missing boundary is external ingress.

## Architectural Principle

External systems produce transport-specific messages. Automation OS must normalize those messages before trigger matching.

```
External Source
   ↓
Ingress Adapter
   ↓
Normalized Event
   ↓
Trigger Invocation
   ↓
StartWorkflowExecution
   ↓
Execution
```

The external transport must never become the workflow execution authority.

## Options

### Option A — Application-level Event Ingress Port

Define a provider-neutral ingress port that accepts an authenticated/validated external event envelope, normalizes it into the existing `Event`, and delegates to the existing Trigger Invocation boundary.

**Pros**
- preserves current trigger architecture;
- transport/provider independent;
- deterministic and testable;
- allows webhooks, queues, polling, and future event sources behind adapters;
- keeps external concerns outside the domain.

**Trade-offs**
- adds one explicit application boundary;
- ingress authentication and deduplication must be designed separately from trigger matching.

### Option B — Transport-specific Trigger Adapters

Let each webhook/queue adapter directly invoke trigger matching.

**Pros**
- fewer abstractions initially;
- straightforward for one transport.

**Trade-offs**
- transport concerns leak into application orchestration;
- every new source repeats mapping/idempotency/error behavior;
- harder to maintain a single normalized event contract.

### Option C — Generic Event Bus First

Introduce a broker/event bus as the central integration mechanism.

**Pros**
- future scale and asynchronous fan-out;
- natural integration with many external sources.

**Trade-offs**
- substantially larger infrastructure;
- introduces delivery/order/replay semantics before the product requires them;
- risks making the bus a second architectural center.

## Recommendation

**Option A — Application-level Event Ingress Port** best preserves the existing architecture with the smallest new boundary.

This is a recommendation only; implementation requires Project Owner approval.

## Decision Questions

1. Should external ingress use the application-level Event Ingress Port (A), transport-specific adapters (B), or a generic event bus (C)?
2. Should external event deduplication be required before Trigger Invocation?
3. Should the first increment support webhook-style ingress only, or multiple source categories?
4. What minimum trust/authentication metadata must the normalized envelope carry?
5. Should event ordering be guaranteed, or explicitly left source-dependent?
6. What failure response/retry contract applies when Trigger Invocation or execution start fails?

## Scope After Decision

Expected first increment:

- provider-neutral ingress contract;
- normalized external event envelope;
- deterministic normalization/validation;
- deduplication semantics if approved;
- one concrete ingress adapter;
- delegation to existing Trigger Invocation;
- focused tests and full regression;
- exit review.

## Deferred

- generic event bus;
- distributed streaming;
- guaranteed global ordering;
- replay platform;
- event analytics;
- multi-tenant ingress isolation;
- arbitrary external code execution;
- provider-specific business logic in domain objects.
