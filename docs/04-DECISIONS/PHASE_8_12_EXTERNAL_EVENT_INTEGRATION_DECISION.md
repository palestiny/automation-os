# Phase 8.12 External Event Integration Decision

Status: **APPROVED**

## Selected architecture

**Option A — Application-level External Event Intake Port**

External transport adapters normalize trusted transport input into ExternalEvent; the application intake boundary validates it and delegates to the existing TriggerInvocation boundary.

## Decisions

1. External event IDs are first-class deduplication keys.
2. Deduplication is scoped by source + external event ID + matched workflow ID.
3. The existing StartWorkflowExecution idempotency primitive remains the execution authority.
4. Events without an external event ID remain non-idempotent.
5. Structured payload/context is preserved on normalized Event.
6. Trigger matching remains based on event_type only in this phase.
7. Authentication, authorization, signature verification, and transport-specific trust remain adapter concerns and are deferred from this application boundary.
8. No generic event bus is introduced.

## Trade-off

Using the existing workflow-start idempotency primitive avoids creating a second deduplication store, but deduplication is intentionally scoped to execution starts. A future event-ingestion persistence layer can be introduced only if requirements demand replay, audit, or delivery guarantees beyond this boundary.

## Authority

The intake boundary never executes capabilities directly and never mutates execution lifecycle state itself. It only normalizes the external event and delegates to trigger invocation.
