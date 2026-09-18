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

- [x] Finalize project constitution
- [x] Establish core domain language baseline
- [x] Establish current domain model baseline
- [x] Establish module-boundary baseline
- [x] Finalize project structure documentation baseline
- [x] Consolidate ADRs and remove duplicate/conflicting documentation
- [x] Establish GitHub issue/branch/PR workflow
- [x] Establish Definition of Done
- [x] Establish test strategy documentation
- [x] Establish development process and Design Gates
- [x] Establish development history journal

## Phase 2 — Execution Engine

- [x] Stable Execution aggregate
- [x] Explicit execution context
- [x] Retry policy
- [x] Orchestrator
- [x] Capability dispatcher
- [x] Capability registry
- [x] Capability result
- [x] Job manager
- [x] Clear execution state machine
- [x] Integration tests

## Phase 3 — Workflow Engine

- [x] Workflow definition
- [x] Workflow steps
- [x] Workflow builder
- [x] Step validation
- [x] Conditions
- [ ] Events/triggers
- [x] Execution persistence strategy
- [x] Workflow execution start use case
- [x] Workflow step execution boundary
- [x] Final-step completion semantics

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

## Phase Exit Gate

A phase is complete only when its committed scope is implemented, tested, documented and architecturally understood. The next phase must not begin merely because code can be written for it.

## Rule

Only move to a later phase when the current phase is sufficiently documented, tested and architecturally understood.
