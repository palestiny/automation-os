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
- [x] Events/triggers
- [x] Execution persistence strategy
- [x] Workflow execution start use case
- [x] Workflow step execution boundary
- [x] Final-step completion semantics
- [x] Phase 3 exit review

## Phase 4 — Capability / Plugin Architecture

- [x] Capability contract
- [x] Plugin registry
- [x] Plugin factory/instance strategy
- [x] External provider isolation
- [x] Capability lifecycle
- [x] Failure/retry semantics
- [x] Phase 4 exit review

## Phase 5 — Content Automation

- [x] Content automation design gate
- [x] Provider-neutral content domain vocabulary
- [x] Content acquisition capability boundary
- [x] Transcript vocabulary and transcription capability boundary
- [x] Clip selection and extraction capability boundary
- [x] End-to-end source-to-clip workflow composition
- [x] YouTube ingestion adapter boundary
- [x] Concrete download capability adapter
- [x] Publishing design gate
- [x] Publication vocabulary
- [x] Publishing capability boundary
- [x] End-to-end publishing composition
- [x] Transcription
- [x] Clip extraction
- [x] Publishing
- [x] Scheduling application boundary
- [x] Execution progress projection
- [x] Scheduling/progress application composition
- [x] Phase 5 exit review

## Phase 6 — Platform Generalization

### Intent-driven execution

Phase 6 committed intent-analysis scope is complete. Remaining platform-generalization items are explicitly deferred below.

Phase 6 intent-driven execution is implemented through canonical goals, deterministic selection, parameter validation, and explicit execution outcomes.

- [x] Intent vocabulary
- [x] Intent analyzer application boundary
- [x] Deterministic workflow selection
- [x] Explicit selection outcomes: selected / no-match / ambiguous
- [x] Intent-to-execution composition
- [x] AI intent analyzer design gate
- [x] Concrete OpenAI intent analyzer adapter
- [x] Raw request → analyze → select → execute composition
- [x] Canonical intent goal catalog
- [x] Canonical goal validation before workflow execution
- [x] Goal catalog design gate accepted and implemented
- [x] Second-domain validation with Business Reporting

### Remaining platform generalization

- [x] Deterministic workflow parameter requirements
- [x] Workflow selection/generation (existing workflow selection; generation remains deferred) beyond exact canonical-goal matching
- [x] Multiple automation domains
- [x] Provider abstraction beyond the current capability/analyzer boundaries
- [x] Marketplace/ecosystem foundations (discovery, installation, listing publication lifecycle, deterministic search)

### Marketplace publication lifecycle

- [x] Marketplace listing lifecycle
- [x] Listing publication/withdrawal invariants
- [x] Lifecycle-aware discovery and installation
- [x] Marketplace listing publication exit review
- [x] Marketplace deterministic search
- [x] Marketplace deterministic search exit review
- [x] Phase 6 exit review
- [x] Workflow execution orchestration increment
- [x] Scheduled workflow execution completion increment
- [x] Execution cancellation application boundary
- [x] Execution resume application boundary
- [x] Resumed execution orchestration composition
- [x] Execution retry application boundary
- [x] Retried execution orchestration composition
- [x] Execution control API composition
- [x] Workflow execution start API composition

## Phase Exit Gate

A phase is complete only when its committed scope is implemented, tested, documented and architecturally understood. The next phase must not begin merely because code can be written for it.

## Rule

Only move to a later phase when the current phase is sufficiently documented, tested and architecturally understood.
