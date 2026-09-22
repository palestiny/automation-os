# Post-Roadmap Reliability Hardening — Design Gate Proposal

## Status

**PROPOSAL — not approved; no architecture change is activated by this document.**

This document prepares the next Project Owner decision boundary after the committed post-Phase-7 capability sequence.

## 1. Repository Evidence

Current master has tenant-aware durable persistence for:

- Workflow;
- Execution;
- Execution history;
- execution idempotency/start coordination.

Current WorkflowVersion persistence is **not tenant-scoped**:

- the WorkflowVersion domain has workflow_id but no tenant_id;
- workflow_versions has no tenant_id column;
- repository get/latest_published/all are not tenant-filtered.

Current MarketplaceListing persistence is only partially prepared for tenancy:

- marketplace_listings has a nullable tenant_id column;
- MarketplaceListing has no tenant_id domain field;
- PostgresMarketplaceListingRepository save/get/all do not use tenant_id.

Current retry behavior contains two concepts:

- explicit manual RetryExecution / RetryAndExecuteExecution;
- RetryPolicy infrastructure/application concepts.

There is not yet an explicit contract defining whether manual retry is constrained by the retry policy or can override it.

## 2. Decision A — WorkflowVersion Ownership

### Option A1 — Explicit tenant ownership

Add tenant identity to WorkflowVersion and its repository/persistence boundary.

Semantics:
- tenant-owned versions are visible only within their tenant;
- system/global versions are explicit rather than inferred;
- execution version lookup is tenant-scoped;
- workflow_id and tenant_id must agree.

**Benefits**
- consistent authorization boundary;
- direct database isolation;
- safer future version-aware APIs and marketplace usage.

**Costs**
- domain/schema/repository migration;
- legacy rows require an explicit migration/global classification rule;
- more context must flow through version-related application calls.

### Option A2 — Ownership derived from Workflow

Keep WorkflowVersion tenant-neutral and derive access through its parent Workflow.

**Benefits**
- smaller domain model;
- fewer schema changes;
- preserves current version identity model.

**Costs**
- every access must reliably validate the parent workflow;
- direct version lookup is easier to misuse;
- weaker database-level isolation;
- more complex joins/authorization checks later.

### Technical consideration

A1 gives the strongest and most auditable isolation boundary. A2 reduces migration cost but moves more correctness responsibility into application code.

## 3. Decision B — MarketplaceListing Ownership

### Option B1 — Tenant-owned listing

Add tenant identity to MarketplaceListing and require tenant-scoped repository operations.

Public publication remains possible as a visibility property, but ownership remains with the publishing tenant.

**Benefits**
- clear ownership and mutation authority;
- tenant isolation remains true even for public listings;
- aligns marketplace writes with authorization boundaries.

**Costs**
- domain/schema/repository change;
- public discovery must distinguish visibility from ownership.

### Option B2 — Global catalog artifact

Treat marketplace listings as global catalog resources and derive any workflow access from referenced workflow/version ownership.

**Benefits**
- simpler public marketplace semantics;
- natural global discovery model.

**Costs**
- ownership is indirect;
- listing mutation/deletion authorization becomes harder to reason about;
- tenant isolation cannot rely on listing identity alone.

### Technical consideration

B1 keeps ownership and visibility as separate concepts: **who owns it** versus **who can discover it**.

## 4. Decision C — Manual Retry vs RetryPolicy

### Option C1 — RetryPolicy is authoritative

Manual retry is allowed only when the same retryability/attempt policy permits another attempt.

**Benefits**
- one retry authority;
- predictable attempt limits;
- easier operational reasoning.

**Costs**
- operators cannot bypass a policy when exceptional recovery is justified;
- emergency intervention requires changing policy or adding a separate administrative mechanism.

### Option C2 — Manual retry may override policy

Automatic retries obey RetryPolicy. Manual retries may exceed the automatic limit when explicitly requested and must record the retry as manual, including actor/reason metadata where the application boundary supports it.

**Benefits**
- preserves automated safety limits;
- allows explicit human recovery;
- clear distinction between automation and intervention.

**Costs**
- two retry paths must be audited;
- requires additional metadata/authorization semantics;
- attempt limits are no longer a single absolute ceiling.

### Technical consideration

C1 maximizes determinism. C2 better separates **automation policy** from **human intervention**, but only if the manual path is explicitly authorized and auditable.

## 5. Recommended Direction for Decision

The technically coherent combination is:

- **A1** — explicit WorkflowVersion tenant ownership;
- **B1** — tenant-owned MarketplaceListing with separate public visibility;
- **C2** — RetryPolicy governs automatic retry while an explicitly authorized manual retry can override it with auditable manual context.

This is a recommendation for Project Owner review, not an implementation decision.

## 6. Non-Goals

This gate does not activate:

- a new product capability;
- a new marketplace provider;
- background workers/queues;
- distributed telemetry;
- AI authority changes;
- workflow migration tooling;
- automatic tenant backfill without an approved migration policy.

## 7. TDD Entry Point After Approval

If approved, implementation must begin with RED tests for:

1. cross-tenant WorkflowVersion isolation;
2. WorkflowVersion tenant/workflow ownership consistency;
3. cross-tenant MarketplaceListing isolation;
4. public listing visibility without ownership transfer;
5. automatic retry policy enforcement;
6. authorized manual retry override and audit evidence;
7. legacy/null-tenant migration behavior.

Then GREEN → REFACTOR → full regression → CI → exit review.

## 8. Exit Criteria

The gate is complete only when:

- the Project Owner selects the ownership/retry options;
- the selected semantics are recorded as committed decisions;
- domain/application/persistence contracts match the decision;
- migrations preserve legacy data safely;
- focused and full regression tests pass;
- GitHub CI verifies the final master state;
- PROJECT_STATUS.md and the exit review reflect the result.
