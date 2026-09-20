# Phase 8.12 — External Event Integration Design Gate

## Status

**APPROVED FOR IMPLEMENTATION — Option A selected**

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

Additional decisions for this increment:

1. External event IDs are first-class deduplication keys from the first implementation. Deduplication is scoped by external source identity plus external event ID.
2. Payload/context is preserved on the intake command for future adapters, but the normalized domain `Event` remains event-type-only in this phase. Payload does not affect trigger matching.
3. Authentication/authorization remains outside this phase; transport adapters are responsible for authenticating the source before calling the application port.
4. A supplied caller idempotency key remains an explicit alternative when no external event ID is available. No event ID/key means non-idempotent behavior.

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
2. **Yes.**
3. **Preserve opaque payload/context now; matching remains event-type-only.**
4. **Yes; transport trust/authentication remains outside this phase.**

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
