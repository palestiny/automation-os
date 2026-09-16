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
- [ ] Job manager integration at the application boundary
- [x] Clear execution state machine baseline
- [x] Integration tests

### Phase 2 — Current Exit-Gate Status

Phase 2 is **in progress / approaching Exit Gate**, not complete.

The core execution orchestration path is implemented, the full local test suite has been reported at **79 passed**, and the registry → dispatcher → orchestrator path has integration-level coverage.

The remaining Phase 2 design question is the meaning of **JobManager integration**. JobManager currently stores the Execution reference but does not live-sync execution lifecycle/progress from the Orchestrator. Any implementation that introduces an application coordination boundary must preserve the existing ownership decision: Execution remains the authoritative lifecycle owner and JobManager remains an operational adapter.

Architecture/documentation consolidation also remains applicable to the broader project and must not be confused with the execution-engine behavior itself.

## Phase 3 — Workflow Engine

- [ ] Workflow definition
- [ ] Workflow steps
- [ ] Workflow builder
- [ ] Step validation
- [ ] Conditions
- [ ] Events/triggers
- [ ] Execution persistence strategy

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
