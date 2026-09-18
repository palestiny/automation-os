# Phase 4 — Capability / Plugin Architecture Design Gate

Status: Design baseline
Date: 2026-09-18
Issue: #59

## Purpose

Define the architecture for executable capabilities and their plugin/provider implementations before expanding the existing capability registry and dispatcher.

Phase 4 must preserve the project constitution:

- domain-first;
- providers are replaceable;
- explicit boundaries;
- TDD by default;
- Design Gate before major implementation;
- AI is replaceable and is not the core abstraction.

## Current Baseline

The current Phase 2/3 implementation already has:

- `CapabilityRegistry` for runtime registration and lookup;
- `CapabilityDispatcher` for resolving a capability and invoking `execute(context)`;
- `CapabilityResult` for success/failure representation;
- `ExecuteWorkflowStep` as the workflow-step application boundary;
- `WorkflowStep.capability` as a string capability identifier.

The current code intentionally leaves the capability contract implicit. Phase 4 makes that contract explicit without moving provider concerns into the domain.

## Architectural Model

A capability is a named executable behavior that a workflow step can request.

The architecture separates three concerns:

1. **Capability identity**
   - Stable provider-neutral identifier used by WorkflowStep.
   - Example: `video_download`.
   - This is workflow-facing and must not contain provider-specific implementation details.

2. **Capability contract**
   - Application/runtime boundary implemented by executable capability instances.
   - Receives execution-scoped input through `ExecutionContext`.
   - Returns an explicit `CapabilityResult`.
   - May raise an exception for an unexpected implementation failure; the dispatcher/application boundary decides how that becomes an execution failure.

3. **Provider/plugin implementation**
   - Infrastructure or integration code that fulfills a capability contract.
   - Provider-specific SDKs, HTTP clients, authentication, payload mapping, and operational details stay outside the domain.
   - Multiple implementations may exist for one capability identity when the application configuration selects a provider.

This prevents the Workflow model from knowing whether a capability is implemented by YouTube, a local process, an AI provider, an HTTP API, or another system.

## Committed Decisions

### 1. WorkflowStep stores a stable capability identifier

`WorkflowStep.capability` remains a string identifier.

The domain does not store a Python class, provider object, SDK object, or infrastructure dependency.

### 2. The capability contract is explicit

Introduce a small runtime protocol/interface for executable capabilities.

The minimum contract is conceptually:

- `execute(context: ExecutionContext) -> CapabilityResult`

The contract must remain small. Capability-specific input/output schemas are not part of the first common interface.

### 3. CapabilityResult is the normal outcome boundary

A capability returns a `CapabilityResult` for an expected operational success/failure.

The result must make success/failure explicit and carry an error value when failed.

The existing implementation's error annotation must be corrected so the contract matches actual behavior: failure currently accepts either an exception or an error value.

### 4. Dispatcher owns capability invocation, not business workflow progression

`CapabilityDispatcher` remains the application execution boundary.

It:

1. resolves a capability by identifier;
2. invokes the capability;
3. returns its result to the caller.

It does not advance `Execution`, complete steps, start executions, or own retry policy.

Those responsibilities remain with the surrounding application/domain boundaries already established in Phase 2/3.

### 5. Registry owns runtime resolution

`CapabilityRegistry` maps stable capability identifiers to executable capability instances.

It does not:

- create Execution objects;
- persist workflows/executions;
- execute workflows;
- implement provider-specific behavior.

Unknown identifiers remain explicit failures through `CapabilityNotFoundError`.

### 6. Registration and construction are separate concepts

The registry should resolve already-constructed capability instances.

Provider/plugin construction belongs to a separate factory/composition mechanism.

This keeps lookup simple and makes construction/configuration testable independently.

### 7. Factory responsibility is provider selection and construction

A future capability factory/composition boundary may:

- choose an implementation for a capability identifier;
- construct/configure it;
- inject provider dependencies;
- register the resulting instance.

The factory does not become a second registry or workflow engine.

The exact factory API is deferred until the first implementation TDD increment.

### 8. Provider-specific dependencies stay outside the domain

SDK clients, HTTP clients, credentials, filesystem/network adapters, AI SDKs, and provider payload models must not leak into Workflow, Execution, Trigger, Condition, or other domain aggregates/value objects.

Provider-specific implementations may depend on infrastructure adapters.

### 9. One capability identity may have multiple implementations

The architecture permits multiple implementations of the same capability contract.

Selection is a composition/configuration concern rather than a Workflow concern.

The first implementation may register one implementation per identifier; provider selection policy can be expanded later.

### 10. Capability lifecycle is initially instance-based and synchronous

For the first Phase 4 increment:

- capability instances are created during application composition;
- registry stores those instances;
- dispatcher invokes them synchronously;
- no worker pool, scheduler, async lifecycle, start/stop hooks, or resource leasing is introduced.

Long-running/background execution remains deferred.

### 11. Retry is not owned by the capability plugin

A capability reports its outcome.

Retry policy belongs to the execution/application runtime.

The capability contract must not mutate Execution state or decide how many times a workflow retries.

Provider-specific transient/permanent classification may be introduced later, but it is not required for the first contract.

### 12. Capability failure must not advance a workflow step

This preserves the existing Phase 3 rule.

A failed `CapabilityResult` or an unexpected capability exception must not cause `Execution.complete_step()` to run.

The surrounding application layer remains responsible for translating failures into the established execution lifecycle.

### 13. Plugins are adapters, not a second domain model

The term “plugin” describes an implementation extension mechanism.

Plugins do not define alternative Workflow or Execution models.

They implement the capability boundary and remain replaceable.

### 14. AI is just another provider/implementation

AI-backed capabilities must use the same capability boundary as non-AI capabilities.

The core platform must not require OpenAI, a specific model, or any AI SDK.

## Target Runtime Flow

Workflow definition:

`WorkflowStep(capability="video_download")`

Runtime:

`ExecuteWorkflowStep`
→ `CapabilityDispatcher`
→ `CapabilityRegistry.resolve("video_download")`
→ capability instance
→ provider/infrastructure dependencies
→ `CapabilityResult`
→ `ExecuteWorkflowStep`
→ step progression only on success

Construction/configuration is outside this execution flow:

`Application composition`
→ provider configuration
→ capability factory/construction
→ registry registration

## Failure Semantics

The initial failure categories are intentionally small:

### A. Unknown capability

Registry cannot resolve the identifier.

Result: explicit `CapabilityNotFoundError`; no step progression.

### B. Expected capability failure

Capability returns `CapabilityResult.failure(...)`.

Result: dispatcher returns the result; caller treats it as unsuccessful; no step progression.

### C. Unexpected implementation exception

Capability raises an exception outside the normal result contract.

Result: exception crosses the capability boundary to the application caller. It must not be converted silently into success.

Retry/Execution-state orchestration remains outside the capability.

### D. Invalid capability registration

The composition/registration layer should reject objects that do not satisfy the explicit capability contract.

This is a composition-time/configuration concern, not a Workflow domain validation rule.

## TDD Implementation Order

The first implementation increment should be narrow:

1. Add the explicit capability protocol/contract.
2. Make `CapabilityResult`'s error contract accurate and stable.
3. Make `CapabilityRegistry` type-safe around the capability contract.
4. Make `CapabilityDispatcher` type-safe around the same contract.
5. Add tests for:
   - valid capability implementation;
   - registry registration/resolution;
   - unknown capability;
   - dispatcher invocation;
   - successful result;
   - failed result;
   - unexpected exception propagation;
   - invalid registration.
6. Re-run the existing workflow-step tests to prove Phase 3 behavior is preserved.

Only after this contract is stable should provider factories/plugin discovery be implemented.

## Deferred

The following are explicitly outside this design gate's first implementation:

- dynamic module discovery;
- Python package/plugin entry points;
- hot loading/unloading;
- remote plugins;
- process isolation/sandboxing;
- plugin version negotiation;
- capability permission/security model;
- dependency graph management;
- capability input/output schemas;
- async/background execution;
- worker pools;
- scheduling;
- provider health checks;
- circuit breakers;
- provider-specific retry classification;
- observability/metrics/tracing;
- persistent plugin configuration;
- marketplace/plugin installation;
- automatic provider selection;
- parallel capability execution.

These can be designed when concrete requirements justify them.

## Trade-offs

### Explicit protocol vs duck typing

**Decision:** explicit protocol.

It gives the runtime boundary a documented contract while retaining structural typing and keeping implementations lightweight.

### Registry + factory vs registry that constructs everything

**Decision:** separate responsibilities.

A registry that also constructs providers would accumulate configuration and infrastructure concerns and become a service locator/factory hybrid.

### CapabilityResult vs exceptions only

**Decision:** use explicit result for expected operational outcomes, while allowing unexpected exceptions to propagate.

This makes normal capability failure visible to the workflow application boundary without hiding programming/configuration defects.

### Capability identity vs provider identity

**Decision:** WorkflowStep references capability identity, not provider identity.

This preserves provider replacement and keeps workflow definitions portable.

### Synchronous instance lifecycle vs async lifecycle

**Decision:** synchronous first.

The current Execution model is not yet a worker/scheduler runtime. Introducing async lifecycle now would couple Phase 4 to infrastructure concerns that are explicitly deferred.

## Design Gate Exit Criteria

Phase 4 design is considered complete when:

- capability identity and implementation contract are explicit;
- provider isolation is documented;
- registry/dispatcher/factory responsibilities are separated;
- failure/retry ownership is explicit;
- the first TDD implementation scope is bounded;
- deferred plugin concerns are recorded;
- the design does not introduce a second execution lifecycle;
- the architecture remains compatible with the existing Phase 2/3 decisions.

## Next Implementation Boundary

After this gate is committed, the next work item is the minimal explicit capability contract and its tests.

No dynamic plugin discovery or provider-specific implementation should be added until that contract passes its TDD gate.
