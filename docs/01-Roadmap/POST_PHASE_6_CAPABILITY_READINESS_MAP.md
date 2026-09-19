# Post-Phase 6 Capability Readiness Map

## Status

Analysis artifact — not an architectural decision and not a Phase 7 commitment.

## Purpose

Map the current repository boundaries against the four post-Phase-6 capability areas so the next Design Gate can start from verified facts rather than assumptions.

## Current execution baseline

The current execution model has:

- `Execution` as the domain aggregate with explicit lifecycle state and attempt count.
- `ExecutionRepository` as the persistence boundary with save/get/all.
- `StartWorkflowExecution` creating and persisting an execution, then starting it.
- `GetExecutionProgress` projecting persisted execution state for reads.
- `DiscoverExecutions` providing deterministic collection filtering by workflow and state.
- HTTP control endpoints for start, cancel, resume, retry, and retry-and-execute.
- In-memory persistence wired through the current application composition root.
- No repository evidence of a dedicated idempotency contract.
- No repository evidence of a dedicated execution-history/audit model.
- No repository evidence of a structured execution-event model.
- No repository evidence of ownership/authorization models.
- No repository evidence of autonomous workflow generation or semantic workflow ranking.

The existing `ExecutionState` remains the authoritative execution lifecycle model. A future capability must not introduce a second competing state model without an explicit Design Gate.

## Capability A — Execution reliability and operational visibility

### Existing boundaries touched

- Domain: `Execution`
- Repository: `ExecutionRepository`
- Application: `StartWorkflowExecution`, retry/control use cases, progress/discovery
- Composition: execution dependencies
- API: execution start/control/read endpoints
- Tests: execution lifecycle and start behavior

### Natural extension points

- Define an explicit idempotency boundary around a concrete command/use case.
- Define history/event ownership separately from the current execution state projection if required.
- Preserve `ExecutionState` as the lifecycle authority.
- Add correlation identifiers only where they solve a defined operational requirement.

### Main design risks

- Turning telemetry into a second domain state model.
- Persisting every implementation detail without a defined query/use case.
- Adding idempotency without defining the command scope, key lifetime, and conflict semantics.
- Coupling domain events to a specific telemetry vendor or infrastructure.

### Required Design Gate questions

1. Which operation requires idempotency first?
2. What request/key identifies the same operation?
3. What is persisted as history versus derived as telemetry?
4. Which events are business/domain events and which are operational signals?
5. What failure semantics apply when persistence of operational data fails?

## Capability B — Platform ownership and authorization

### Existing boundaries touched

- Workflow and execution domain/application contracts.
- Marketplace listing lifecycle/discovery/installation boundaries.
- HTTP endpoints.
- Persistence contracts.

### Natural extension points

- Introduce ownership at the application/domain boundary rather than only in HTTP handlers.
- Make resource ownership explicit for workflows, executions, and marketplace resources if the product requires it.
- Keep authentication mechanism separate from authorization policy.

### Main design risks

- Adding user IDs to entities before deciding the ownership model.
- Implementing API-only authorization that can be bypassed by application use cases.
- Mixing single-user identity with a premature multi-tenant model.
- Creating security semantics without corresponding persistence isolation.

### Required Design Gate questions

1. Is the target model single-owner, multi-user, or multi-tenant?
2. Which resources are owned?
3. What operations require authorization?
4. Where is the authoritative policy evaluated?
5. What isolation guarantees must persistence enforce?

## Capability C — Autonomous planning / workflow generation

### Existing boundaries touched

- Intent analysis.
- Canonical goal validation.
- Workflow discovery.
- Workflow selection.
- Workflow definition/validation.
- Existing deterministic execution boundary.

### Natural extension points

A future planner could propose candidate workflows or parameters, but the existing deterministic selection/execution boundary should remain authoritative until a new Design Gate explicitly changes that contract.

### Main design risks

- Executing generated workflows before validation.
- Treating semantic similarity as authoritative compatibility.
- Allowing AI output to become domain state without validation.
- Introducing autonomous planning before safety/failure boundaries are defined.

### Required Design Gate questions

1. What exactly may AI generate?
2. What deterministic validation must every generated artifact pass?
3. Can generated workflows execute automatically, or only become candidates?
4. How are ambiguity and unsafe/incomplete plans represented?
5. How are model/provider failures isolated from domain execution?

## Capability D — Product/API foundation

### Existing boundaries touched

- Existing FastAPI routes.
- Application use cases.
- Resource identifiers and response schemas.
- Future authentication/authorization boundary.

### Natural extension points

- Formalize public API contracts only around stable domain capabilities.
- Add pagination/versioning when there is a concrete collection/use case requiring them.
- Keep dashboard concerns outside domain entities.

### Main design risks

- Freezing unstable domain contracts prematurely.
- Adding generic infrastructure without a concrete consumer.
- Introducing authentication without an authorization/resource-ownership model.

### Required Design Gate questions

1. Who is the concrete API consumer?
2. Which API contract is stable enough to publish?
3. What compatibility/versioning policy is required?
4. Which collections actually need pagination?
5. How does authentication relate to resource authorization?

## Cross-capability observations

- Execution reliability can build directly on the current execution lifecycle and repository boundary, but its semantics are currently undefined.
- Ownership/authorization crosses workflow, execution, and marketplace boundaries and therefore has a broader domain impact.
- Autonomous planning crosses intent, discovery, selection, and execution and requires the strongest explicit safety/determinism boundary before implementation.
- Product/API work should be driven by a concrete consumer and should not become generic infrastructure by default.
- None of these observations selects a milestone.

## Exit condition for this map

This map is complete when the next Design Gate can reference verified current boundaries and does not need to rediscover the existing execution, intent, marketplace, or API architecture.

The next committed change should be the selected capability's Design Gate, not implementation code.
