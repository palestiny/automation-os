# Runtime Connection Preparation Boundary

## Purpose

Establish the security and execution boundary between an immutable published WorkflowVersion and provider-ready connection authentication.

## Current foundation

The system now has tenant-owned Connection records containing only a secret_reference, tenant/provider/reference resolution through ConnectionResolver, protected secret lookup through SecretProvider, immutable published WorkflowVersion.connection_requirements, ResolveRuntimeConnection, and PrepareWorkflowRuntimeConnections.

No workflow, workflow version, review decision, or marketplace artifact stores secret material.

## Required runtime flow

Execution -> persisted published WorkflowVersion -> connection_requirements -> PrepareWorkflowRuntimeConnections -> trusted execution tenant + ConnectionResolver + SecretProvider -> protected runtime connection data -> CapabilityDispatcher -> Capability.

The persisted version is authoritative. A caller cannot replace a connection requirement with a request-time provider/reference.

## Design decision

Runtime preparation remains a separate application service immediately before capability dispatch.

It must:
1. receive the persisted executable WorkflowVersion;
2. receive the trusted execution tenant;
3. resolve exactly the declared requirements;
4. fail closed on missing, revoked, mismatched, or secret-resolution failures;
5. expose resolved authentication only through execution-scoped runtime context;
6. never persist secret material;
7. never publish, mutate, or select another workflow/version.

CapabilityDispatcher remains unaware of ConnectionRepository and SecretProvider.

## ExecutionContext boundary

The existing generic ExecutionContext.set() is not sufficient as a long-term trust boundary because arbitrary callers can write arbitrary keys.

Before runtime integration, introduce a dedicated runtime-data channel so ordinary workflow inputs remain caller/application data while resolved connection data is written only by the runtime preparation boundary. Capabilities can read resolved runtime data but cannot resolve credentials themselves.

The implementation must avoid exposing raw secret values in repr, logs, or error messages.

## Failure semantics

Preparation must happen before capability invocation. Missing, revoked, mismatched, or secret-provider failures must prevent capability invocation and fail the execution. No credential fallback is permitted.

## Retry/replay invariant

A retry or idempotent replay must use the connection requirements of the persisted executable WorkflowVersion. It must not accept a new request-time connection reference.

## Security verification gate

Before integrating into ExecuteWorkflowStep, tests must prove resolution occurs before capability invocation; capabilities are not called when resolution fails; caller-supplied connection references cannot override persisted requirements; cross-tenant resolution is rejected; revoked connections fail closed; secret provider failures fail closed; secret material is absent from WorkflowVersion persistence, execution history, review decisions, and marketplace artifacts; and runtime wrappers do not expose secrets.

## Non-goals

OAuth refresh/rotation, a concrete external secret manager, credential sharing or marketplace, provider-specific authentication adapters, generic audit/event infrastructure, and frontend changes.
