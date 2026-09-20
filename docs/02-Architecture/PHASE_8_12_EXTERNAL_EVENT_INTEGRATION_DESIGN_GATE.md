# Phase 8.12 — External Event Integration Design Gate

## Status

**APPROVED FOR IMPLEMENTATION — Option A selected by Project Owner**

## Objective

Introduce a stable inbound boundary for external events so external systems can submit events without coupling transport concerns to workflow matching or execution.

## Repository Evidence

The platform already has:
- immutable normalized `Event(event_type)`;
- deterministic `TriggerMatcher`;
- `TriggerInvocation` that matches published workflows and delegates to `StartWorkflowExecution`;
- durable persistence;
- idempotent execution-start semantics.

The missing boundary is transport/integration normalization. The current trigger layer should not become an HTTP/webhook implementation.

## Options

### Option A — Application-level External Event Intake Port **(recommended)**

External adapters translate transport-specific input into a normalized `Event` plus correlation/idempotency metadata, then call an application-level intake port.

Flow:

```
External Source
    ↓
Transport Adapter
    ↓
External Event Intake Port
    ↓
Normalized Event
    ↓
TriggerInvocation
    ↓
StartWorkflowExecution
```

Pros:
- keeps transport outside domain/application orchestration;
- reusable for webhook, queue, polling, and future adapters;
- preserves existing deterministic trigger boundary;
- allows external-event deduplication to be explicit;
- testable without HTTP infrastructure.

Trade-off:
- introduces one additional application boundary.

### Option B — Webhook Endpoint as the Integration Boundary

Expose HTTP directly and have the endpoint normalize and invoke triggers.

Pros:
- minimal first implementation;
- immediately usable for webhooks.

Trade-off:
- couples the core integration model to HTTP;
- makes queues/polling/other transports second-class;
- risks putting authentication, parsing, and orchestration together.

### Option C — Domain Event Bus

Introduce a general event bus and make external events publish into it.

Pros:
- broad event-driven architecture.

Trade-off:
- much larger scope;
- introduces delivery/subscription semantics not currently required;
- risks replacing the deterministic trigger invocation boundary with infrastructure complexity.

## Approved Decision

**Option A — Application-level External Event Intake Port** is approved.

External transport adapters remain replaceable. The application intake boundary accepts a normalized external-event command, validates it deterministically, and delegates matching/invocation only through the existing TriggerInvocation boundary.

Approved contract decisions:
- external event ID is first-class deduplication identity;
- payload is preserved as opaque structured data but does not affect trigger matching in this phase;
- authentication and authorization remain outside Phase 8.12;
- deduplication is scoped per matched workflow by reusing workflow-start idempotency;
- if neither external event ID nor explicit caller idempotency key exists, intake remains non-idempotent;
- no generic event bus is introduced.

## Proposed Phase 8.12 Contract

- external source identity is explicit;
- external event type is explicit;
- payload/context is opaque structured data and does not alter trigger matching in this phase;
- optional external event ID may provide deduplication;
- transport-specific authentication remains outside the domain;
- duplicate external events must not create duplicate executions when a stable external event ID is supplied;
- no event ID means normal non-idempotent behavior unless the caller explicitly supplies an idempotency key;
- trigger matching remains based on normalized event type;
- the intake boundary does not execute capabilities directly;
- failed validation is explicit;
- no generic event bus is introduced.

## Decision Questions

1. **Option A selected.**
2. **Yes — external event IDs are first-class deduplication keys.**
3. **Payload is preserved on ExternalEvent while normalized trigger matching remains event-type-only.**
4. **Yes — authentication/authorization remain outside this phase.**

## TDD RED Plan

1. valid external event normalizes deterministically;
2. invalid source/type is rejected;
3. intake delegates only through TriggerInvocation;
4. published matching workflows execute;
5. draft workflows do not execute;
6. same external event ID is deduplicated;
7. different external event IDs remain independent;
8. missing external event ID does not accidentally become globally idempotent;
9. payload is preserved or deliberately excluded according to the approved decision.

## Explicitly Deferred

- webhook framework/API endpoint;
- queue/broker infrastructure;
- polling adapters;
- external authentication implementation;
- signature verification;
- generic event bus;
- distributed delivery guarantees;
- event replay platform;
- analytics;
- multi-tenant isolation.
