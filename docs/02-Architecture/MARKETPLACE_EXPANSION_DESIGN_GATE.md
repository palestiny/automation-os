# Marketplace Expansion Design Gate

## Status

**APPROVED FOR IMPLEMENTATION — Option A selected by Project Owner**

## Objective

Expand the existing marketplace foundation into a durable, first-class catalog boundary without creating a second execution engine.

## Approved Architecture — Option A

**MarketplaceListing becomes a first-class catalog artifact with stable identity and repository-backed lifecycle.**

The marketplace remains metadata/discovery infrastructure around existing Workflow/WorkflowVersion artifacts.

Flow:

```
Workflow / WorkflowVersion
        ↓
MarketplaceListing
        ↓
MarketplaceRepository
        ↓
Discovery / Publication / Installation
        ↓
existing execution boundaries
```

### Committed decisions

1. MarketplaceListing receives a stable UUID identity.
2. Listing persistence is behind a domain repository contract.
3. PostgreSQL is the durable adapter; in-memory remains the test adapter.
4. Listing lifecycle remains DRAFT → PUBLISHED → WITHDRAWN.
5. Publication still requires a published Workflow.
6. Installation still returns an existing published Workflow; it never executes.
7. Listing references Workflow identity; version-specific marketplace negotiation is deferred.
8. Search remains deterministic metadata matching.
9. No remote executable plugins, payments, ratings, trust scoring, moderation, or authorization are introduced.
10. Existing execution remains the only execution path.

## Alternatives / Trade-offs

### Option A — First-class durable marketplace listing artifact
Pros: stable identity, restart survival, repository boundary, clean path to later marketplace ownership/ratings/version negotiation.
Trade-off: adds persistence and mapping work now.

### Option B — Keep listings ephemeral/in-memory
Pros: smallest implementation.
Trade-off: marketplace state disappears on restart and cannot support a durable ecosystem.

### Option C — Store marketplace metadata directly inside Workflow
Pros: fewer objects.
Trade-off: couples catalog concerns to the Workflow aggregate and makes future marketplace evolution harder.

Option A is approved.

## TDD / Exit Criteria

- stable listing identity;
- repository contract;
- in-memory behavior;
- PostgreSQL persistence/recreation;
- publication/discovery/installation preserve existing invariants;
- full regression;
- exit review and project status update.
