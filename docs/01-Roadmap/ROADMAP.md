# Roadmap

Status: Living document

## Phase 0 — Foundation

- [x] Initial FastAPI project
- [x] Execution domain introduced
- [x] Execution state transitions
- [x] Execution lifecycle
- [x] Retry lifecycle
- [x] Initial capability abstractions
- [x] Workflow abstractions
- [x] Application-layer orchestration foundations
- [x] Initial automated tests

## Phase 1 — Documentation & Architecture Baseline

- [x] Establish project constitution
- [x] Establish domain language
- [x] Establish domain model baseline
- [x] Establish module boundaries
- [x] Establish project structure documentation
- [ ] Consolidate ADRs and remove duplicate/conflicting documentation
- [ ] Establish GitHub issue/branch/PR workflow as a documented project practice
- [x] Establish Definition of Done
- [ ] Establish test strategy documentation

## Phase 2 — Execution Engine

- [x] Stable Execution aggregate baseline
- [x] Explicit execution context baseline
- [x] Retry policy
- [x] Orchestrator baseline
- [x] Capability dispatcher
- [x] Capability registry
- [x] Capability result
- [x] Job manager ownership mapping and boundary
- [x] Clear execution state machine baseline
- [x] Integration tests

### Phase 2 — Exit Gate

**Status: COMPLETE**

Phase 2 is complete for the committed scope.

Verified baseline at Phase 2 closure:

- Full local test suite was reported at **86 passed**.
- Registry → Dispatcher → Orchestrator execution path has integration-level coverage.
- Execution remains the authoritative owner of lifecycle and step progression.
- Retry behavior is covered and documented.
- Successful capability output flows through `CapabilityResult → ExecutionContext`.
- JobManager maps operational jobs to Execution without becoming a second lifecycle owner.
- No live JobManager synchronization was introduced prematurely.
- ADR-008 explicitly defers live JobManager synchronization until a concrete product requirement exists.

Broader documentation consolidation, test strategy, CI/CD and other quality/infrastructure work remain tracked outside the completed Phase 2 execution scope.

## Phase 3 — Workflow Engine

- [x] Workflow definition
- [x] Workflow steps
- [x] Workflow builder
- [x] Step validation
- [x] Explicit transition routing
- [x] Named condition-reference semantics
- [x] Condition evaluator boundary
- [x] In-memory ConditionRegistry implementation
- [x] Conditional routing behavior and integration coverage
- [ ] Workflow graph validation beyond endpoint ownership
- [ ] Events/triggers
- [ ] Execution persistence strategy

### Phase 3 — Current Slice

**Status: Workflow definition, construction, explicit routing and the first condition-evaluation slice are implemented in the current branch.**

Implemented and covered by tests:

- Workflow definition invariants.
- WorkflowStep definition invariants.
- Ordered WorkflowStep collection.
- Published Workflow immutability.
- Minimal `WorkflowBuilder` construction API.
- Explicit `Transition` routing between workflow steps.
- Execution applies an explicitly selected target rather than falling back to list order.
- Named condition-reference semantics.
- `ConditionEvaluator` application boundary.
- In-memory `ConditionRegistry` with normalization, duplicate protection and explicit unknown-condition failure.
- Orchestrator integration with the registry using the same `ExecutionContext`.
- Explicit no-match and multiple-match routing errors.
- Conditional routing tests for true, false, missing evaluator and unregistered condition cases.

The exact current test count must be re-verified locally or through CI after the latest commits; this document intentionally does not claim a new count until it is verified.

### Phase 3 — Next Slice

The condition boundary is now sufficiently defined for the first implementation scope. Dedicated application exception types are intentionally deferred; current `ValueError` semantics are adequate until another consumer needs stable error categories.

Next implementation slice: **Workflow graph validation**. Before adding broader workflow-engine behavior, validate structural invariants that can be determined from the published workflow definition, while keeping runtime routing decisions in the existing Workflow → Orchestrator → Execution boundaries.

The graph-validation slice must have its own design gate/tests before implementation expands beyond the current routing model.

## Phase 4 — Capability / Plugin Architecture

- [ ] Capability contract
- [ ] Plugin registry
- [ ] Plugin factory/instance strategy
- [ ] External provider isolation
- [ ] Capability lifecycle
- [ ] Failure/retry semantics

## Phase 5 — Content Automation

- [ ] YouTube ingestion
- [ ] Download capability
- [ ] Transcription
- [ ] Clip extraction
- [ ] Publishing
- [ ] Scheduling
- [ ] Progress tracking

## Phase 6 — Platform Generalization

- [ ] Intent analysis
- [ ] Workflow selection/generation
- [ ] Multiple automation domains
- [ ] Provider abstraction
- [ ] Marketplace/ecosystem foundations

## Rule

Only move to a later phase when the current phase is sufficiently documented, tested and architecturally understood.
