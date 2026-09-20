# Phase 8.13 — Multi-tenant / Authorization Design Gate

## Status
**APPROVED FOR IMPLEMENTATION — Option A selected by Project Owner**

## Goal
Introduce tenant ownership and authorization without making domain execution logic responsible for authentication or policy evaluation.

## Option A — Application Authorization Context + Tenant-Scoped Repository Boundary

Identity/authentication enters through an application-level request context. The context contains the authenticated principal and tenant identifier. Application use cases authorize the operation before repository access. Persistence adapters enforce tenant scoping for tenant-owned records.

Flow:

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

### B — Tenant as a domain aggregate parent
Stronger domain modeling, but introduces tenant coupling across existing entities and requires broad domain/persistence migration.

### C — Infrastructure-only middleware isolation
Minimal domain impact, but authorization can become implicit and individual application use cases are harder to reason about and test.

## Approved Constraints

1. Tenant identity is explicit at application/persistence boundaries.
2. Domain entities remain independent of authentication providers.
3. Authorization decisions are explicit and testable.
4. Tenant-scoped reads/writes cannot cross tenant boundaries.
5. Missing tenant context is rejected for tenant-owned operations.
6. System-level operations must be explicitly distinguished from tenant operations.
7. No implicit superuser bypass.
8. Authentication provider integration is outside this first increment.
9. Existing single-tenant behavior must not silently become cross-tenant.
10. Execution lifecycle semantics remain unchanged.

## Initial Scope

- tenant/principal application context;
- authorization policy boundary;
- tenant-scoped repository contract;
- one representative persistence path migrated end-to-end;
- deterministic cross-tenant rejection tests;
- composition wiring;
- documentation.

## Deferred

External identity provider integration, roles/permissions UI, organization invitations, billing, audit dashboard, SSO, OAuth configuration, fine-grained resource ACLs, distributed policy engines.

## TDD RED

- tenant context is required for tenant-owned operations;
- same tenant can access its own resource;
- different tenant cannot read/update another tenant resource;
- unauthorized principal is rejected;
- system operations require explicit system authorization;
- repository scoping cannot be bypassed by caller-supplied tenant IDs.

## Exit Criteria

Design boundaries implemented, focused tests pass, representative durable path is tenant-scoped, full regression passes, and exit review records deferred security capabilities.
