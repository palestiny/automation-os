# Connection Runtime Integration Design Gate

## Purpose
Define how tenant-owned Connections and protected secrets enter capability execution without coupling Workflow definitions to secret material or allowing client-controlled connection selection.

## Current foundation
- `Connection` is tenant-owned and stores only `secret_reference`.
- `ConnectionRepository` is tenant-scoped.
- `ConnectionResolver` validates tenant/provider/reference and rejects revoked connections.
- `SecretProvider` resolves protected secret material by secret reference.
- `ResolveRuntimeConnection` composes those boundaries.
- `CapabilityDispatcher` currently receives only `capability_id` and `ExecutionContext`.

## Decision questions
1. Where is the logical connection reference declared?
2. Who supplies the tenant identity used for resolution?
3. How does a capability receive resolved provider-ready authentication without querying repositories?
4. How do we prevent arbitrary caller input from selecting another connection?
5. How do we preserve immutable WorkflowVersion semantics?

## Proposed direction
1. A published WorkflowVersion declares provider-neutral connection requirements/references, never secret material.
2. At execution start, the application derives connection requirements from the persisted immutable WorkflowVersion.
3. Execution runtime context is enriched by an application-owned runtime preparation step using the execution tenant, workflow version requirements, ConnectionResolver, and SecretProvider.
4. The caller cannot directly inject a resolved connection or override a workflow's declared connection reference.
5. Capabilities receive only the provider-ready runtime object through ExecutionContext; they do not access ConnectionRepository or SecretProvider.
6. Connection resolution failure fails the execution before the capability is invoked; there is no credential fallback.
7. The runtime preparation boundary remains separate from publication and review.

## Alternatives
### A — Resolve inside CapabilityDispatcher
Pros: centralized; capabilities remain simple.
Cons: dispatcher must understand connection requirements and execution context conventions.

### B — Resolve before dispatch and enrich ExecutionContext
Pros: explicit runtime preparation; dispatcher stays capability/provider focused; easiest to test as a separate boundary.
Cons: requires a stable execution-context contract.

### C — Resolve inside each capability
Rejected: duplicates authorization/security logic and violates the credential boundary.

## Recommendation
Use **B**. Introduce an explicit runtime preparation service that consumes the persisted WorkflowVersion requirements and execution authorization context, resolves protected connections, and places only runtime-safe resolved values into an execution-scoped context. CapabilityDispatcher remains unaware of persistence and credentials.

## Required invariants
- No secret material in Workflow, WorkflowVersion, generated artifacts, review decisions, or marketplace artifacts.
- No client-controlled connection override.
- Tenant identity comes from trusted execution authorization context.
- No implicit tenant-to-system fallback.
- Revoked/missing/provider-mismatch/secret-resolution failure prevents capability invocation.
- Capabilities never access ConnectionRepository or SecretProvider directly.
- WorkflowVersion remains immutable after publication.
- Connection resolution never publishes or starts an execution.

## Implementation gate
Before runtime integration is merged, tests must prove:
- workflow/version connection requirements are immutable and secret-free;
- trusted tenant context is required;
- another tenant's connection cannot be resolved;
- revoked/missing connections fail before capability invocation;
- protected secret failure fails closed;
- capability receives resolved runtime authentication only through execution context;
- caller cannot override a persisted connection reference;
- retry/replay does not silently select a different connection;
- no secret values appear in execution history, logs, review decisions, or workflow persistence.

## Non-goals
- selecting a concrete secrets manager;
- OAuth refresh/rotation;
- changing Workflow publication/review semantics;
- marketplace credential sharing;
- microservices or event-bus extraction.
