# Phase 8.13 — Multi-tenant / Authorization Design Gate

## Status
**COMPLETED — Option A implemented and CI-verified**

## Goal
Introduce tenant ownership and authorization without making domain execution logic responsible for authentication or policy evaluation.

## Option A — Application Authorization Context + Tenant-Scoped Repository Boundary

Authenticated identity enters through an application-level context containing the principal and tenant. Application use cases authorize operations before repository access. Persistence adapters enforce tenant scoping for tenant-owned records.

```
Authenticated Request
        ↓
Application Authorization Context
        ↓
Use Case / Authorization Policy
        ↓
Tenant-scoped Repository
        ↓
Domain Entity
```

The domain lifecycle remains independent of authentication mechanisms.

## Alternatives

- **B — Tenant as a domain aggregate parent:** stronger domain modeling, but broad tenant coupling and migration.
- **C — Infrastructure-only middleware isolation:** lower domain impact, but authorization becomes implicit and harder to test at use-case boundaries.

## Approved Constraints

1. Tenant identity is explicit at application/persistence boundaries.
2. Domain entities remain independent of authentication providers.
3. Authorization decisions are explicit and testable.
4. Tenant-scoped reads/writes cannot cross tenant boundaries.
5. Missing tenant context is rejected for tenant-owned operations.
6. System operations are explicitly distinguished from tenant operations.
7. No implicit superuser bypass.
8. Authentication-provider integration is outside the first increment.
9. Existing single-tenant behavior must not silently become cross-tenant.
10. Execution lifecycle semantics remain unchanged.

## Current Increment

Implemented application authorization context:
- `TenantId`;
- `AuthorizationContext`;
- explicit system context;
- deterministic `AuthorizationPolicy`;
- cross-tenant and missing-context tests.

PR #279 was merged as `d05f358f9d8eaa731f115cfa24f50b1a62cba186`.

## Completed Implementation

PR #280 delivered the remaining durable tenant-scoping increment for representative Workflow, Execution, idempotency, and history persistence paths, plus explicit authorization-context persistence composition. Master CI run #1584 passed with 590 tests.

## Remaining Phase Scope

The implementation increment adds durable tenant scoping to representative Workflow and Execution repository paths, integrates authorization context into those application boundaries, and verifies cross-tenant isolation with PostgreSQL. No Phase 8.13 completion claim is made until durable isolation, authorization integration, and full regression verification are complete.

## Deferred

External identity providers, roles/permissions UI, invitations, billing, SSO/OAuth configuration, fine-grained ACLs, distributed policy engines, and security operations tooling.
