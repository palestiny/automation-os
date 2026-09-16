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
- [ ] Job manager integration
- [x] Clear execution state machine baseline
- [ ] Integration tests

### Phase 2 — Current Exit-Gate Status

Phase 2 is **in progress**, not complete.

The core execution orchestration path is implemented and covered by unit tests. Remaining work includes validating the execution engine through integration tests, deciding the role of JobManager, and completing any remaining architecture/documentation consolidation required by the Phase Exit Gate.

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
