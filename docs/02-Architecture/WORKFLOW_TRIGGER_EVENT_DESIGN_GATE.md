# Phase 3 — Workflow Trigger and Event Design Gate

Status: Design baseline
Date: 2026-09-18
Issue: #55

## Purpose

Define the boundary between external events, Workflow trigger definitions, and Workflow execution without introducing provider-specific integrations or a second execution-start lifecycle.

## Committed Decisions

### 1. An external Event is an application input, not a Workflow aggregate

An Event represents something that happened outside the Workflow domain, such as an incoming application signal.

The initial boundary does not make Event a persistent domain entity or part of the Workflow aggregate.

The event payload belongs to the application/runtime input and must not be copied into Workflow definition state by default.

### 2. A Trigger is declarative Workflow definition

A Trigger expresses that a published Workflow may be started when an incoming Event matches its trigger criteria.

Trigger configuration belongs to the Workflow definition because it describes when that Workflow is eligible to start.

This means:

- draft Workflows may add or change triggers;
- published Workflow trigger definitions are immutable with the rest of the Workflow definition;
- a Workflow may have zero or more triggers;
- triggers do not own Execution lifecycle.

### 3. Initial Trigger identity is event type

The first trigger model uses a provider-neutral event type identifier.

The initial concept is intentionally small:

- event type;
- no provider-specific webhook schema;
- no expression DSL;
- no arbitrary payload filtering;
- no scheduling syntax.

If future requirements need source identifiers, payload filters, version constraints, or richer matching, they require a new design decision rather than implicit expansion.

### 4. Trigger matching belongs outside Workflow

Workflow stores trigger definitions but does not inspect incoming events and does not decide whether an external event matches.

Trigger matching belongs to an application-layer component.

The matcher receives an incoming Event and evaluates it against Workflow trigger definitions.

This keeps Workflow declarative and prevents external runtime concerns from leaking into the domain aggregate.

### 5. Trigger-driven execution must reuse StartWorkflowExecution

A successful trigger match requests workflow execution through the existing StartWorkflowExecution use case.

There must be one authoritative application path for:

Workflow ID → Execution.create() → persistence → Execution.start() → persistence.

Trigger handling must not construct or start Execution directly.

### 6. Trigger matching does not own Execution state

A trigger handler may determine that a Workflow should start, but it does not transition Execution states and does not become another lifecycle coordinator.

Execution remains the authoritative runtime aggregate.

### 7. Provider-specific event delivery stays outside the core

Webhooks, queues, cron systems, message brokers, polling adapters, authentication, signatures, retries, and provider-specific payload schemas are infrastructure/application concerns.

The core trigger boundary consumes a normalized application Event rather than depending on a provider SDK or transport.

### 8. Manual and trigger-driven starts share the same execution boundary

A Workflow may still be started directly through StartWorkflowExecution.

Trigger-driven start is an additional entry path into that use case, not a replacement for it.

This preserves one execution lifecycle contract regardless of how execution was requested.

## Initial Runtime Flow

External source
→ provider/application adapter
→ normalized Event
→ trigger matcher
→ matched Workflow ID
→ StartWorkflowExecution
→ persisted RUNNING Execution

The trigger path ends at execution start. Step processing remains owned by ExecuteWorkflowStep.

## Deferred

- Trigger implementation;
- Event/Trigger domain classes;
- workflow lookup/query APIs for matching triggers;
- trigger persistence schema;
- event bus/message broker;
- webhook adapters;
- scheduled/cron triggers;
- event payload filtering;
- nested trigger conditions;
- deduplication/idempotency;
- event delivery retries;
- background workers;
- automatic execution of multiple workflow steps;
- parallel workflow execution.

## Trade-offs

### Keep Event outside the Workflow aggregate

This avoids coupling Workflow definition to transient external data and avoids prematurely defining a general event domain model.

### Keep Trigger inside Workflow definition

This makes the eligibility rule part of the workflow contract and preserves published-workflow immutability.

### Match outside Workflow

This adds a small application boundary, but prevents the domain aggregate from becoming responsible for infrastructure/runtime concerns.

### Reuse StartWorkflowExecution

This avoids duplicate lifecycle behavior and keeps execution identity/state ownership centralized.

## First TDD Increment

Before implementation, the smallest useful increment should prove the trigger definition and matching boundary only.

It should establish:

- a trigger can be represented as part of a Workflow definition;
- trigger definitions remain part of the published Workflow contract;
- an incoming normalized Event can be matched against a trigger;
- a non-matching event does not request execution;
- a matching event resolves the target Workflow ID without constructing Execution.

Starting an Execution should remain covered by the existing StartWorkflowExecution tests and be integrated only after the trigger application boundary is separately understood.

## Gate Result

The Phase 3 events/triggers boundary is sufficiently defined for a focused implementation increment.

No provider integration, event bus, scheduler, or new execution lifecycle is justified by this design gate.
