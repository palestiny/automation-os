# Publication / Outcome Persistence Design Gate

## Status

Proposed — design-only boundary.

## Problem

The current publishing flow stores Publication in ExecutionContext. That is sufficient for one execution, but it disappears with the execution context unless a later persistence mechanism is introduced.

Before adding a database or repository, the project must establish whether the business actually needs a durable record.

## Concrete business requirements

Durability becomes justified when the system needs to answer questions after execution completion, such as:

- Was this asset published?
- Where was it published?
- What external publication identifier was returned?
- Which execution produced the publication?
- Can a later workflow inspect the previous publication?
- Can the system reconcile provider state with its own record?
- Can reporting/analytics query historical publication results?

These requirements are business history, not execution runtime state.

## Decision

For the current Phase 5 slice, **do not add durable Publication/Outcome persistence yet**.

The current Publication remains an immutable business result carried through ExecutionContext.

An explicit persistence boundary will be introduced only when a use case requires post-execution querying or reconciliation.

## Why

Adding persistence now would create infrastructure and lifecycle complexity without a committed use case:

- repository interfaces;
- storage mapping;
- database schema;
- transaction/UoW decisions;
- migration strategy;
- identity/reconciliation semantics.

None of those are required to prove the current content publishing workflow.

## Future boundary

If durability becomes required, the intended shape is:

Publishing Capability → Publication → Application persistence boundary → Infrastructure repository

The repository would persist a business-level Publication record, not provider SDK objects and not Execution internals.

A future Outcome concept should be introduced only if the business result becomes broader than publication. It should not be created merely as a wrapper around Publication.

## Identity

The existing Publication.id is the business identity of the publication record.

Publication.external_reference remains the provider's external identity.

If durable persistence is introduced, the model must preserve both identities and the destination/provider context needed for reconciliation.

## Execution relationship

A durable Publication should reference the originating execution through an application-level association if the use case needs traceability.

It should not become part of the Execution state machine.

## Idempotency

Durability alone does not establish retry idempotency.

Once automatic retry or scheduling is introduced, a separate design gate must define:

- operation identity;
- duplicate detection;
- provider-side idempotency support;
- reconciliation after uncertain network outcomes.

## Outcome

No standalone Outcome aggregate is committed at this stage.

If future requirements include a workflow-level business result containing multiple artifacts/publications, Outcome can be evaluated then.

## Consequences

### Positive

- No premature database design.
- Current publishing path remains small and testable.
- Domain stays independent of persistence technology.
- Future persistence has a clear business trigger.

### Negative

- Completed publication history is not yet queryable.
- Analytics and reconciliation cannot rely on a durable Publication record.
- A later persistence increment will require an explicit repository and transaction design.

## Exit Criteria

This gate is complete when:

- the business reason for persistence is explicit;
- Publication is distinguished from Execution lifecycle;
- Outcome is not introduced speculatively;
- persistence is deferred without ambiguity;
- the trigger for reopening the decision is documented.

## Decision Record

**Decision:** Defer durable Publication/Outcome persistence.

**Reason:** No current Phase 5 use case requires post-execution publication history or reconciliation.

**Revisit when:** reporting, historical queries, downstream workflows, reconciliation, or durable business audit becomes an implemented requirement.
