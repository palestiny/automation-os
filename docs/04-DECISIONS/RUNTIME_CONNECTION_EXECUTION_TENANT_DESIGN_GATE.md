# Runtime Connection Execution Tenant Design Gate

## Purpose

Establish the trusted tenant boundary required before runtime connection preparation is integrated into workflow execution.

## Current State

- Published WorkflowVersion declares provider-neutral ConnectionRequirement values.
- Connection persistence is tenant-scoped.
- ResolveRuntimeConnection requires an explicit tenant_id.
- Runtime preparation currently receives a tenant_id explicitly.
- Execution currently does not persist its tenant identity.
- StartWorkflowExecution already has an optional tenant_id at the application boundary.

## Problem

Using WorkflowVersion.tenant_id as the runtime tenant would make the executable definition the source of authorization context. That is insufficient as the durable execution boundary: runtime authorization should be tied to the execution instance created under an explicit trusted tenant context.

A caller must not be able to override the connection requirement or choose a different tenant during execution.

## Decision

Add explicit tenant ownership to Execution.

The runtime chain becomes:

Trusted AuthorizationContext
→ StartWorkflowExecution(tenant_id)
→ Execution.tenant_id
→ persisted immutable WorkflowVersion requirements
→ Runtime Connection Preparation
→ ConnectionResolver(Execution.tenant_id, persisted provider/reference)
→ SecretProvider
→ capability

For legacy/system executions, tenant_id may remain null only where the existing explicit system execution semantics allow it. Tenant-owned workflows must create tenant-owned executions.

## Invariants

1. Tenant-owned WorkflowVersion and tenant-owned Execution must have the same tenant.
2. A tenant-owned execution cannot run a version owned by another tenant.
3. ConnectionRequirement comes only from the persisted WorkflowVersion.
4. Runtime tenant comes only from the persisted Execution.
5. No API/request field can override either value.
6. Missing tenant context for a tenant-owned runtime connection fails closed.
7. Connection resolution happens before capability invocation.
8. Resolution failures fail the execution and prevent capability invocation.
9. Resolved secret material never enters Workflow, WorkflowVersion, review decisions, marketplace artifacts, or execution history.
10. Retry/replay reuses the same persisted WorkflowVersion and Execution tenant boundary.

## Alternatives

### A — Derive tenant from WorkflowVersion

Rejected as the primary runtime authorization source. It couples authorization context to executable definition state and does not preserve the execution's ownership boundary explicitly.

### B — Pass tenant_id transiently through ExecuteWorkflow

Rejected. It leaves the execution record without durable ownership and allows a runtime caller to supply context independently of the persisted execution.

### C — Persist tenant_id on Execution

Selected. It makes execution ownership explicit, durable, auditable, and available to all runtime paths including retries.

## Implementation Gate

Before runtime integration is considered complete, tests must prove:

- Execution tenant validation.
- StartWorkflowExecution propagates tenant ownership.
- PostgreSQL execution persistence round-trip.
- In-memory execution behavior.
- WorkflowVersion/Execution tenant mismatch is rejected.
- System/legacy execution behavior remains explicit.
- Runtime preparation uses Execution.tenant_id.
- Caller cannot override persisted connection requirements.
- Missing/revoked/secret-provider failure prevents capability invocation.
- No secret appears in execution events/history.
- Retry preserves tenant and WorkflowVersion identity.

## Non-goals

- OAuth refresh/rotation.
- Concrete secret manager implementation.
- Provider-specific adapters.
- Credential sharing.
- Frontend changes.
- Microservices/event bus.
