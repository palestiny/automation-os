# Runtime Connection Execution Dependency Gate

## Purpose

Define the missing composition boundary between tenant-owned Connection persistence and workflow execution.

The runtime preparation service consumes immutable WorkflowVersion connection requirements, but current application composition is process-global while ConnectionRepository is tenant-scoped. Wiring one global ConnectionResolver would risk weakening the tenant boundary.

## Current state

- WorkflowVersion declares immutable, provider-neutral ConnectionRequirement values.
- ConnectionRepository is tenant-scoped.
- ConnectionResolver requires an explicit tenant_id.
- ResolveRuntimeConnection resolves the declared connection and protected secret.
- PrepareWorkflowRuntimeConnections rejects a WorkflowVersion/execution tenant mismatch and writes only trusted runtime connection state.
- ExecutionContext reserves the runtime connection slot.
- ExecuteWorkflowStep prepares connections before capability dispatch.

## Decision

Runtime connection dependencies are **execution-scoped**, not process-global.

The execution layer obtains a tenant-bound runtime resolver for the execution persisted tenant_id. The caller does not supply provider/reference or select a connection.

Conceptually:

Execution tenant_id + persisted WorkflowVersion requirements -> tenant-bound RuntimeConnectionResolver -> SecretProvider -> PrepareWorkflowRuntimeConnections -> trusted ExecutionContext -> CapabilityDispatcher

The factory/composition boundary may construct a tenant-scoped ConnectionRepository for each execution or execution unit. The application service must not know PostgreSQL details.

## Why

### Option A — One global ConnectionResolver

Rejected because a global resolver would need an unscoped ConnectionRepository or hidden tenant selection, weakening the explicit tenant boundary.

### Option B — Build a tenant-bound resolver at runtime

Chosen. Persisted Execution supplies tenant identity. Composition creates a resolver bound to that tenant and the protected SecretProvider. Application code remains provider-neutral.

### Option C — Pass ConnectionRepository into every capability

Rejected because it would move credential persistence and secret access into capability implementations.

## Required invariants

1. Tenant identity comes from persisted Execution state, not request parameters or ExecutionContext.
2. Connection references come only from the persisted immutable WorkflowVersion.
3. Caller cannot override a connection requirement through ExecutionContext.
4. Cross-tenant connection resolution is prevented by the repository boundary.
5. Missing, revoked, provider-mismatched, or secret-resolution failures happen before capability invocation.
6. Capabilities receive runtime-ready connection data only through trusted runtime context.
7. Capabilities never receive ConnectionRepository or SecretProvider.
8. Secrets never enter Workflow, WorkflowVersion, review decisions, marketplace records, or execution history.
9. Runtime preparation does not publish, mutate, or start executions.
10. Absence of a configured protected SecretProvider fails closed.

## Implementation gate

The next implementation slice must prove tenant-bound resolver construction, persisted requirement immutability against caller override, preparation before dispatch, fail-closed connection and secret errors, revoked connection rejection, protected runtime context, and no secret leakage into execution evidence or persisted workflow artifacts.

## Non-goals

- concrete Vault/AWS/Azure implementation;
- OAuth refresh/rotation;
- connection management API;
- changing workflow publication/review;
- changing marketplace behavior;
- broad execution API authorization redesign.

## Exit condition

The gate is complete when the execution-scoped composition boundary is implemented and runtime security tests pass.