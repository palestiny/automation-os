# Credential / Provider Configuration Design Gate

**Status:** DESIGN GATE — proposed for implementation review  
**Date:** 2026-09-28

## 1. Purpose

Establish a safe, tenant-aware boundary between declarative workflow definitions and the external provider authentication/configuration required by executable capabilities.

This gate does not introduce a full secrets-management product, OAuth platform, broker, event bus, or autonomous credential provisioning system.

## 2. Current Architecture

The runtime currently resolves a stable capability identifier to a configured provider and dispatches the provider-created capability with an execution-scoped `ExecutionContext`.

The relevant boundary is:

`Workflow → WorkflowVersion → Execution → CapabilityDispatcher → CapabilityProviderResolver → Capability`

Credential resolution must remain outside Workflow/WorkflowVersion persistence and outside AI-generated workflow artifacts.

## 3. Problem

Capabilities that interact with external providers eventually require tenant-owned authentication/configuration. The current capability/provider boundary does not yet define:

- how a tenant identifies a configured external connection;
- how provider identity is bound to that connection;
- how credentials are referenced without storing secret material in workflow artifacts;
- how runtime resolves authentication;
- how revocation and failure are enforced;
- how tenant/system isolation is preserved.

## 4. Core Decision

Introduce **Connection** as the domain concept.

A Connection represents a tenant-owned configuration relationship with a provider. It may contain a reference to protected secret material, but it must never contain the secret value itself.

Conceptual model:

`Connection
- id
- tenant_id
- provider_id
- reference
- authentication_type
- secret_reference
- status
- created_at
- updated_at`

Exact field names remain implementation details until the domain contract is implemented.

## 5. Workflow Contract

A Workflow may declare a **connection requirement/reference**, but it does not own credentials.

Example:

`capability = youtube.publish`
`connection_ref = youtube.primary`

The reference is logical and tenant-scoped. A Workflow must not persist:

- API keys;
- passwords;
- access tokens;
- refresh tokens;
- client secrets;
- other secret material.

The same invariant applies to WorkflowVersion, MarketplaceListing, generated WorkflowCandidate, review decisions, and AI prompts/outputs.

## 6. Runtime Resolution Boundary

Resolution occurs at execution time.

Conceptual flow:

`Execution
 → CapabilityDispatcher
 → ConnectionResolver
 → tenant/provider/reference validation
 → protected SecretProvider
 → provider-ready authentication
 → Capability`

Capability implementations must not query ConnectionRepository or secret storage directly.

The dispatcher/runtime composition owns the resolution boundary.

## 7. Connection Identity

The workflow-facing identifier should be a logical reference such as:

`youtube.primary`

rather than a database UUID.

Resolution is scoped by:

`tenant_id + provider_id + connection_ref`

A logical reference is unique within its tenant scope. There is no implicit global connection fallback.

## 8. Ownership and Authorization

Tenant-owned Connections require explicit tenant authorization.

System-owned execution may use an explicit system context, following the same rule already established for human workflow review.

Missing tenant context must never silently become system context.

Cross-tenant resolution must fail closed.

## 9. Lifecycle

The first implementation slice defines:

- `ACTIVE`
- `REVOKED`

Runtime behavior:

| Connection state | Resolution |
|---|---|
| ACTIVE | allowed |
| REVOKED | rejected |
| missing | rejected |
| wrong tenant | rejected |
| wrong provider | rejected |

Expiration, rotation workflows, OAuth refresh lifecycle, and disabled states are deferred until a concrete requirement requires them.

## 10. Secret Storage

The domain stores only a protected secret reference.

Conceptual boundary:

`Connection → SecretReference → SecretProvider → SecretStore`

The application must depend on an abstraction rather than a specific Vault/cloud vendor.

The first implementation should not commit the architecture to AWS Secrets Manager, Azure Key Vault, HashiCorp Vault, or another external product.

A development/test implementation may exist only behind the same abstraction and must not weaken production authorization or leakage invariants.

## 11. AI Boundary

AI may propose declarative requirements such as:

- capability identity;
- provider identity;
- logical connection reference.

AI must not:

- read secret values;
- generate secret values for runtime use;
- publish credentials;
- mutate tenant Connections;
- select a different tenant's Connection;
- bypass ConnectionResolver;
- execute provider authentication outside the runtime boundary.

## 12. Failure Semantics

Credential resolution failures must be explicit and observable without exposing secrets.

Minimum semantic failures:

- `CONNECTION_NOT_FOUND`
- `CONNECTION_ACCESS_DENIED`
- `CONNECTION_REVOKED`
- `CONNECTION_PROVIDER_MISMATCH`
- `CONNECTION_RESOLUTION_FAILED`

There is no automatic fallback to another connection.

Authentication fallback could execute a workflow under an unintended external identity and is therefore prohibited by this gate.

## 13. Persistence

Connections require durable persistence in PostgreSQL for production tenant usage.

The persistence boundary should be represented by a repository abstraction.

Durable uniqueness should enforce the tenant-scoped logical reference invariant.

Secret values must not be written to the Connection table.

## 14. Idempotency

Connection registration should be idempotent at the application command boundary.

Repeated registration with the same idempotency key must deterministically replay the original result.

Conflicting reuse of an idempotency key must fail rather than silently overwrite configuration.

Secret rotation is a separate lifecycle concern and must not mutate an immutable WorkflowVersion.

## 15. Observability and Security

Operational evidence may include:

- connection id;
- tenant id;
- provider id;
- connection reference;
- status;
- resolution outcome;
- execution id.

Operational evidence must not include secret values or authorization headers.

Logs and error messages must be reviewed for accidental secret leakage.

## 16. Trade-offs

### Connection vs Credential

**Decision:** Connection.

Credential describes authentication material; Connection describes a tenant-owned provider relationship and can support multiple authentication mechanisms.

### UUID vs Logical Reference

**Decision:** Logical reference in workflow-facing configuration.

This keeps workflows portable and prevents workflow artifacts from becoming coupled to tenant database identifiers.

### Secret in domain vs secret reference

**Decision:** Secret reference only.

This keeps secret material outside business aggregates and allows infrastructure replacement.

### Provider-specific credential handling vs central resolution

**Decision:** Central application/runtime resolution with provider-specific adapters behind it.

This prevents every capability from inventing its own credential lookup/security behavior.

### Full secrets platform now vs abstraction first

**Decision:** Abstraction first.

We need a stable domain/application contract before selecting infrastructure.

## 17. Explicit Invariants

1. Secret material never enters Workflow.
2. Secret material never enters WorkflowVersion.
3. Secret material never enters AI-generated workflow artifacts.
4. Secret material never enters review decisions.
5. Secret material never enters marketplace artifacts.
6. Connection ownership is tenant-scoped.
7. Runtime resolution is tenant-aware.
8. Missing tenant context never implies system context.
9. Revoked Connections cannot execute.
10. No automatic credential fallback.
11. Capabilities do not directly access credential persistence.
12. AI cannot access secret material or mutate runtime credentials.
13. Connection resolution does not publish or execute workflows.
14. Review approval remains separate from publication and execution.
15. WorkflowVersion remains immutable after publication.

## 18. Implementation Gate

Implementation may begin only after tests are defined for:

- Connection domain validation;
- tenant ownership;
- logical reference uniqueness;
- provider binding;
- ACTIVE/REVOKED behavior;
- tenant isolation;
- explicit system context;
- secret-reference-only persistence;
- repository round-trip;
- idempotent registration;
- conflicting idempotency;
- runtime resolution;
- provider mismatch;
- revoked connection;
- missing connection;
- secret-provider failure;
- no fallback behavior;
- no secret leakage into logs/errors;
- AI/workflow artifact boundary;
- capability access only through runtime resolution.

## 19. Non-Goals

This gate does not implement:

- a general-purpose secrets manager;
- OAuth authorization UI;
- OAuth token refresh platform;
- credential marketplace;
- automatic credential discovery;
- credential sharing across tenants;
- autonomous credential creation;
- frontend connection management;
- microservice extraction;
- event bus;
- generic audit platform.

## 20. Exit Condition

The gate is closed when:

1. the Connection domain contract is approved;
2. application repository/resolver boundaries are defined;
3. authorization semantics are covered by tests;
4. PostgreSQL persistence is verified;
5. runtime resolution is verified;
6. secret leakage tests pass;
7. idempotency semantics are verified;
8. no Workflow/WorkflowVersion invariant regresses;
9. CI is green;
10. post-merge repository state is reconciled without claiming unverified merge-commit CI.

## 21. Next Implementation Slice

After this gate, implementation should proceed in this order:

`Connection domain → Repository contract → In-memory tests → PostgreSQL persistence → ConnectionResolver → runtime integration → security/leakage verification`

Provider-specific authentication adapters and real secret-store integrations follow only after this slice proves the boundary.
