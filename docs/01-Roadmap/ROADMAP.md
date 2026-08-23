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

- [ ] Finalize project constitution
- [ ] Finalize domain language
- [ ] Finalize domain model
- [ ] Finalize module boundaries
- [ ] Finalize project structure documentation
- [ ] Consolidate ADRs and remove duplicate/conflicting documentation
- [ ] Establish GitHub issue/branch/PR workflow
- [ ] Establish Definition of Done
- [ ] Establish test strategy documentation

## Phase 2 — Execution Engine

- [ ] Stable Execution aggregate
- [ ] Explicit execution context
- [ ] Retry policy
- [ ] Orchestrator
- [ ] Capability dispatcher
- [ ] Capability registry
- [ ] Capability result
- [ ] Job manager
- [ ] Clear execution state machine
- [ ] Integration tests

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
