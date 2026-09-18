# Phase 4 Exit Review — Capability / Plugin Architecture

Status: Complete baseline
Date: 2026-09-18

## Scope Reviewed

Phase 4 committed scope:

- Capability contract
- Plugin registry
- Plugin factory/instance strategy
- External provider isolation
- Capability lifecycle
- Failure/retry semantics

## Implementation Evidence

The current master branch contains the Phase 4 capability architecture together with its tests and architecture Design Gates.

The Capability protocol defines the executable boundary as `execute(context) -> CapabilityResult`. CapabilityResult represents the normal operation outcome and does not own Execution lifecycle.

CapabilityRegistry owns registration and resolution of already-constructed capability instances. CapabilityFactory owns application-composition construction and keeps provider-specific configuration outside the Workflow contract. The dispatcher resolves and invokes capabilities but does not construct them, retry them, or advance workflow execution.

Capability lifecycle is intentionally synchronous and instance-based for the current baseline. Capabilities are constructed during application composition and remain reusable application components. Cleanup and provider-specific lifecycle concerns remain outside the core capability contract.

WorkflowStep continues to reference a stable provider-neutral capability identifier. This keeps workflow definitions independent of provider implementation details and allows multiple implementations to fulfill the same capability identity.

Failure handling now has an explicit application/domain boundary. A handled `CapabilityResult.failure(...)` is translated by ExecuteWorkflowStep into `Execution.fail()`, persisted, and reported without advancing the current step. Unexpected capability exceptions also transition the Execution to FAILED, persist that state, and re-raise the original exception.

Retry remains an explicit Execution lifecycle operation. `Execution.retry()` transitions FAILED -> RETRYING and increments the attempt; `Execution.start()` then transitions RETRYING -> RUNNING. Capabilities do not own retry or Execution lifecycle.

## Architectural Understanding

Phase 4 is considered architecturally understood because:

1. Capability execution is an explicit application boundary rather than an implicit provider convention.
2. CapabilityResult describes operation outcome without becoming a second Execution state machine.
3. Registry, factory, and dispatcher have distinct responsibilities.
4. Capability construction occurs at application composition time rather than during dispatch.
5. Provider-specific dependencies remain behind implementation boundaries and do not leak into workflow definitions.
6. Capability lifecycle does not own workflow progression, retry, or terminal Execution state.
7. Handled capability failures and unexpected exceptions both preserve the Execution lifecycle invariant: failed processing does not advance the current step.
8. Execution remains the sole owner of its lifecycle transitions, while the application layer coordinates when those transitions are invoked.
9. Retry remains explicit; automatic retry orchestration, retry limits, backoff, and provider-specific failure classification are not part of the current contract.
10. AI implementations can participate as capabilities without becoming a required architectural dependency.

## Test and CI Gate

PR #67 introduced the failure/retry semantics increment and was merged only after GitHub Actions reported success.

The final verification run was GitHub Actions Tests run #169 on commit `f11d11a596c04ad495feedd6416db21a3c4ab30b`, with conclusion `success`.

PR #67 was squash-merged into `master` as commit `9174e0d84f7911db9b883a4131889fb335e06f6c`.

## Deferred Technical Scope

The following remain intentionally deferred and are not implied by the Phase 4 capability architecture:

- Automatic retry orchestration
- Retry limits, backoff, and jitter
- Provider-specific transient/permanent failure classification
- Retry queues and workers
- Background execution
- Idempotency and deduplication
- Extended retry history
- Observability and failure taxonomy
- Compensation/rollback
- Dynamic capability discovery
- Entry-point based loading
- Hot loading
- Remote plugins
- Sandboxing
- Version negotiation
- Permissions
- Health checks
- Circuit breakers
- Marketplace/ecosystem infrastructure
- Automatic provider selection
- Parallel workflow execution

These items require their own design decisions and must not silently expand the Phase 4 contract.

## Exit Decision

Phase 4 has satisfied the current committed roadmap scope and its implementation, testing, documentation, and architecture gates.

Phase 5 may now be planned through its own domain/design gate. No Phase 5 implementation should be treated as committed until its scope and architecture are explicitly established.
