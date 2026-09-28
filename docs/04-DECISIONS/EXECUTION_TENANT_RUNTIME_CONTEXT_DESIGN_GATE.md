# Execution Trusted Tenant Runtime Context Design Gate

## Status
OPEN — design gate before changing the Execution aggregate.

## Problem

Runtime connection preparation must resolve credentials using the trusted tenant of the execution, while the executable WorkflowVersion remains the immutable source of declared connection references.

The current preparation path derives the tenant from the WorkflowVersion itself. That preserves tenant ownership consistency but does not establish an independent execution-scoped trust boundary.

## Current flow

`Execution → WorkflowVersion → connection_requirements → ResolveRuntimeConnection → SecretProvider → ExecutionContext`

Current preparation checks that the supplied tenant matches the WorkflowVersion tenant.

## Proposed direction

Add an explicit tenant identity to the persisted Execution boundary.

1. A tenant-owned execution is created with its trusted tenant id from the already-authorized application context.
2. The tenant id becomes immutable execution identity.
3. Runtime preparation receives the Execution (or a typed execution runtime identity) and derives tenant identity from it.
4. WorkflowVersion remains the only source of connection requirements.
5. Caller-provided context cannot override tenant, provider, or connection reference.
6. System executions remain explicitly distinguishable; they do not silently inherit a tenant.
7. Tenant-scoped repositories continue enforcing storage isolation.
8. Resolved connection material remains execution-context runtime state and never becomes workflow/version/history/review persistence.

## Alternatives

### A — Continue deriving tenant from WorkflowVersion
Simple and minimal, but the runtime trust boundary is coupled to workflow definition data.

### B — Persist tenant on Execution
Makes execution ownership explicit and independently verifiable across retries/replays. Requires domain and persistence migration work.

### C — Pass trusted tenant only as an application runtime argument
Avoids schema change, but trust must be propagated correctly through every execution entry point and replay path.

## Decision

**Recommended: B.**

The execution is the runtime identity that actually performs work. Its tenant should therefore be explicit and persisted, especially for retries, asynchronous execution, and replay.

## Required implementation gate

Before implementation, tests must prove:

- tenant-owned execution requires tenant identity;
- execution tenant cannot differ from workflow/version tenant;
- retry/replay preserves the same tenant;
- runtime preparation uses execution tenant, not caller context;
- cross-tenant execution cannot resolve another tenant's connection;
- system context is explicit and cannot silently become a tenant;
- caller cannot override persisted connection requirements;
- missing/revoked/provider-mismatch/secret-resolution failure prevents capability invocation;
- no secret appears in Execution persistence, lifecycle events, history, logs, review decisions, WorkflowVersion, or marketplace artifacts.

## Non-goals

- OAuth refresh/rotation
- concrete secrets manager
- changing workflow publication/review
- credential sharing
- generic audit/event platform
