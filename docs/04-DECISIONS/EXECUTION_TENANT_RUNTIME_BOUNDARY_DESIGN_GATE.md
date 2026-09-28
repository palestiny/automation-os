# Execution Tenant Runtime Boundary Design Gate

## Status

OPEN

## Context

WorkflowVersion now declares provider-neutral ConnectionRequirement values, and runtime preparation resolves those requirements through ConnectionResolver and SecretProvider before capability execution.

The current implementation derives the preparation tenant from WorkflowVersion.tenant_id. That is not yet a sufficient runtime identity boundary because the runtime contract requires the tenant to be trusted from the execution context rather than reconstructed from the executable definition.

## Decision Questions

1. Should Execution carry tenant_id?
2. Where is tenant_id established?
3. Should StartWorkflowExecution require an explicit trusted tenant context?
4. How should legacy/system executions behave?
5. How should retries preserve tenant identity?
6. Should ExecutionContext expose tenant identity to capabilities?

## Proposed Direction

Add tenant_id: UUID | None to Execution. For tenant-owned workflows, StartWorkflowExecution derives and validates the tenant from trusted application authorization context and persisted Workflow/WorkflowVersion ownership. The value is persisted with the Execution and never taken from caller-controlled execution context.

System-owned/legacy workflows may continue with tenant_id=None, but system execution must be explicit; there is no implicit fallback.

ExecuteWorkflowStep should pass execution.tenant_id to runtime preparation. For tenant-owned WorkflowVersion, execution.tenant_id must equal workflow_version.tenant_id. A mismatch fails before connection resolution or capability invocation.

Connection requirements remain exclusively definition-owned by the immutable WorkflowVersion. The execution supplies only trusted tenant identity.

ExecutionContext is not an authority boundary. Do not expose tenant identity or connection-selection authority through generic ExecutionContext.set().

## Alternatives

### 1. Continue deriving tenant from WorkflowVersion

Avoids schema changes, but leaves execution without an explicit security identity and couples runtime authority to definition metadata. Not recommended.

### 2. Add tenant_id to Execution

Provides explicit durable execution identity, preserves identity across retry/resume, and makes invariant checking direct. Requires coordinated domain, persistence, start-path, and test changes. Recommended.

### 3. External execution tenant lookup

Avoids widening Execution but introduces another authority boundary and complicates retries and operational inspection. Not recommended.

## Implementation Gate

Before further production runtime wiring, tests must prove tenant_id persistence; trusted establishment; Workflow/WorkflowVersion/Execution tenant agreement; cross-tenant start rejection; retry preservation; runtime preparation using Execution.tenant_id; caller-controlled ExecutionContext cannot override tenant; requirements come only from WorkflowVersion; tenant mismatch prevents resolver invocation; missing/revoked connections prevent capability invocation; secret resolution failure prevents capability invocation; and no secret enters Workflow, WorkflowVersion, Execution, ExecutionEvent/history, ReviewDecision, marketplace artifacts, or logs.

## Non-goals

OAuth refresh/rotation, concrete secrets manager, credential marketplace/sharing, generic authorization framework, microservices/event bus, and capability-specific credential APIs.
