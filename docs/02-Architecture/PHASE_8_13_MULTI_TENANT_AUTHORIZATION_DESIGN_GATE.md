# Phase 8.13 — Multi-tenant / Authorization Design Gate

## Status

**APPROVED FOR IMPLEMENTATION — Option A selected by Project Owner**

## Position

Phase 8.13 is the final capability in the current post-Phase-7 sequence.

## Objective

Introduce explicit ownership and authorization boundaries so Automation OS can safely isolate resources between tenants while preserving the existing domain/application architecture.

## Repository Evidence

The current platform already has durable PostgreSQL persistence, workflow/version identity, execution lifecycle, marketplace artifacts, external event intake, and operational metrics. The current status explicitly identifies tenant identity, authorization policy, persistence isolation, API enforcement, marketplace visibility, and cross-cutting security semantics as the next design boundary.

No tenant/authorization contract should be inferred from existing business identifiers. Tenant identity must become an explicit application/security concept.

## Committed Constraints

1. Authorization must not become domain lifecycle authority.
2. Tenant ownership must be enforced before resource mutation or disclosure.
3. Repository/application boundaries must prevent accidental cross-tenant reads and writes.
4. Database isolation must reinforce, not replace, application authorization.
5. Existing domain entities should not absorb HTTP/authentication concerns.
6. Authentication and authorization remain separate concepts.
7. Marketplace visibility must distinguish globally published artifacts from tenant-owned/private artifacts.
8. Execution, workflow, version, event, and metric access must obey tenant scope.
9. Cross-tenant administrative operations, if needed, must be explicit rather than accidental.
10. No external identity provider is selected by this gate.

## Architectural Options

### Option A — Application-level Tenant Context + Authorization Policy

Introduce an explicit request/application tenant context and authorization policy boundary. Use tenant-scoped repository methods/queries and require the application layer to authorize access before mutation/disclosure.

**Pros**
- Keeps domain objects independent from authentication infrastructure.
- Makes tenant scope explicit at use-case boundaries.
- Testable without a specific identity provider.
- Allows future JWT/OIDC/session providers without changing domain contracts.

**Trade-offs**
- Every tenant-sensitive use case must carry context.
- Repository contracts become more explicit and broader.
- Requires disciplined enforcement to avoid an unscoped access path.

### Option B — Persistence-first Row-Level Security

Make PostgreSQL Row-Level Security the primary tenant isolation mechanism and derive tenant scope from database session context.

**Pros**
- Strong database enforcement against accidental cross-tenant SQL access.
- Centralized isolation at the persistence boundary.

**Trade-offs**
- Couples the architecture more tightly to PostgreSQL/session mechanics.
- Application authorization semantics can become implicit.
- Testing and non-PostgreSQL adapters become more complex.
- Does not by itself define authentication or resource-level permissions.

### Option C — Domain-owned Tenant Identity and Access Rules

Put tenant ownership and access rules directly into domain entities/aggregates.

**Pros**
- Rules are close to the resources they protect.
- Some invariants can be expressed locally.

**Trade-offs**
- Risks coupling business entities to security/identity concepts.
- Repeats access semantics across aggregates.
- Makes infrastructure/authentication migration harder.

## Approved Decision

**Option A — Application-level Tenant Context + Authorization Policy** is approved.

Implementation decisions:
- Tenant scope is mandatory for tenant-owned application operations.
- System/global scope is explicit rather than represented by a null tenant.
- Initial authorization uses deterministic tenant-scoped roles: `OWNER` and `MEMBER`, with explicit permissions at the application boundary.
- Marketplace-public artifacts are explicitly public; tenant-private artifacts remain tenant-scoped.
- PostgreSQL Row-Level Security is deferred as defense-in-depth, not the primary policy boundary.
- Background and event-triggered execution must preserve the originating tenant context.
- No implicit cross-tenant administrative bypass is introduced.

## Recommended Direction

**Option A — Application-level Tenant Context + Authorization Policy** is the recommended starting architecture because it establishes explicit security boundaries without making PostgreSQL or authentication infrastructure the platform's architectural center.

A later implementation may add PostgreSQL Row-Level Security as defense-in-depth if a dedicated decision establishes the required session/connection model.

## Decision Questions

1. Should tenant scope be mandatory for tenant-owned application operations?
2. Should system/global resources use an explicit system scope rather than null tenant IDs?
3. What authorization model is required initially: owner/member roles, resource permissions, or both?
4. Should marketplace-public artifacts be readable cross-tenant while private artifacts remain tenant-scoped?
5. Should PostgreSQL RLS be part of the first implementation or deferred as defense-in-depth?
6. How should background/event-triggered execution obtain and preserve tenant context?
7. Which cross-tenant administrative operations, if any, are allowed?

## TDD RED Plan

- tenant context is required for tenant-owned operations;
- tenant A cannot read/update/delete tenant B resources;
- tenant-scoped workflow → version → execution access remains consistent;
- marketplace-public artifacts follow explicit visibility rules;
- external event intake cannot inject another tenant's scope;
- background execution preserves originating tenant scope;
- authorization denial is deterministic and auditable;
- system/global scope is explicit;
- unscoped legacy access paths are identified and removed or explicitly classified.

## Non-goals

- choosing an identity provider;
- UI/mobile authorization screens;
- billing/subscriptions;
- enterprise SSO;
- advanced policy languages;
- organization hierarchy beyond the minimum required model;
- replacing PostgreSQL transactions;
- rewriting domain lifecycle semantics.
