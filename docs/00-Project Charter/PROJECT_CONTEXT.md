# Automation OS — Project Context

> Persistent operational memory for the project. Keep this synchronized with the actual repository state.

**Repository:** `palestiny/automation-os`
**Mission:** Transform ideas into executable business workflows.
**Architecture:** Modular Monolith with DDD and Clean Architecture principles.
**Primary language:** Python.
**Current branch:** `feature/workflow-execution-orchestration`.

## 1. Product Direction

The project evolved from the original AutoReel AI idea into **Automation OS**: a general platform for turning business ideas into repeatable executable workflows.

AI is replaceable. External providers are replaceable. Workflow is a means; execution is central.

The conceptual target is:

```text
Intent → Workflow → Execution → Capability → Asset → Outcome
```

Asset and Outcome remain conceptual models; they are not yet sufficiently defined to drive the current execution-engine transport contract.

## 2. Architecture Rules

- Domain owns business meaning and invariants.
- Application coordinates use cases and orchestration.
- Infrastructure/external providers must remain replaceable.
- Modular Monolith is the default until real requirements justify stronger distribution.
- Do not couple the core model to OpenAI, YouTube, TikTok, Whisper, or another single provider.
- Do not introduce abstractions merely because they may be useful later.
- Important architectural decisions require an explicit Design Gate and ADR.

## 3. Current Domain Model

### Workflow

A published Workflow is an executable plan made of ordered Workflow Steps. A Workflow Step identifies the capability to invoke.

### Execution

Execution is the concrete attempt to run a Workflow. It owns runtime lifecycle and workflow-step progression.

Current states:

```text
CREATED → RUNNING → WAITING / COMPLETED / FAILED / CANCELLED
                     ↓
                  RETRYING
```

Execution-level retry increments `Execution.attempt`.
Step-level retry increments `ExecutionStep.attempt` and does not increment the execution attempt.

### Capability

A business-meaningful ability invoked by the execution engine. A plugin/provider can implement the ability without becoming part of the domain model.

### CapabilityResult

Application-level invocation result containing:

- `succeeded`
- `output` for successful execution
- `error` for failed execution

It is not a replacement for the future Asset/Outcome domain concepts.

### ExecutionContext

Application-level runtime data shared between capabilities during one orchestration. The orchestrator stores successful step output in the context using the Workflow Step identifier as the current key.

## 4. Current Execution Engine

The current application path is:

```text
Workflow
   ↓
Orchestrator
   ↓
CapabilityDispatcher
   ↓
CapabilityRegistry
   ↓
Capability
   ↓
CapabilityResult
   ↓
ExecutionContext
   ↓
next Capability
```

Execution owns step progression; Orchestrator owns coordination.

Retry semantics are documented in the ADRs.

## 5. Current Test Baseline

The user has locally run the full test suite after the latest execution-engine changes with:

```text
79 passed
```

This is the current reported local verification baseline. Future implementation milestones must rerun the suite before claiming a newer verified result.

Preferred command:

```powershell
python -m pytest
```

## 6. Current Documentation Decisions

Relevant ADRs include:

- ADR-004 — Execution and step retry semantics.
- ADR-005 — Execution owns workflow-step progression.
- ADR-006 — CapabilityResult carries successful output and Orchestrator moves it into ExecutionContext.
- ADR-007 — JobManager maps operational jobs to Execution without owning Execution lifecycle.

These decisions deliberately defer Asset/Outcome transport semantics until those concepts have enough business meaning to justify a dedicated Design Gate.

## 7. Current Roadmap Position

Phase 0 — Foundation: complete.

Phase 1 — Documentation & Architecture Baseline: substantially complete; documentation consolidation and test-strategy work remain.

Phase 2 — Execution Engine: **in progress / approaching Exit Gate**.

Completed baseline areas:

- Execution aggregate
- execution state machine
- execution context baseline
- retry policy
- orchestrator baseline
- capability dispatcher
- capability registry
- capability result
- step-level retry semantics
- execution-owned step progression
- successful step-output propagation
- JobManager ownership decision and execution mapping baseline
- integration-level registry → dispatcher → orchestrator verification
- full local test-suite verification reported at 79 passed

Remaining Phase 2 work:

- decide and, if retained in scope, implement JobManager synchronization at the application boundary without making it a second Execution lifecycle;
- complete the applicable architecture/documentation consolidation;
- perform the formal Phase 2 Exit Gate after the remaining design decision is resolved.

## 8. JobManager Status

`app/core/job_manager.py` is an in-memory operational job tracker that stores an associated `execution_id`.

The committed decision is that JobManager is an application/runtime adapter, not a second execution lifecycle. Execution remains the authoritative owner of lifecycle, retries, completion, failure and cancellation.

The current implementation does **not** provide live synchronization from Orchestrator to JobManager. A future application-level coordination boundary may perform that synchronization if live job tracking becomes a real requirement.

Persistence, distributed workers, queues and durable job recovery remain deferred.

## 9. Phase 2 Exit Gate

Before declaring Phase 2 complete, verify:

1. Execution lifecycle and step progression remain owned by Execution.
2. Retry behavior is covered and documented.
3. Capability output flows through CapabilityResult → ExecutionContext.
4. Registry and Dispatcher participate in an integration-level execution path.
5. JobManager does not duplicate Execution lifecycle ownership.
6. No unnecessary infrastructure or abstraction was introduced.
7. Relevant architecture documentation and ADRs match the implementation.
8. Full test suite passes locally.
9. Project state is updated and pushed.

Current status: items 1–5 and 8 are evidenced by the current implementation, documentation and the reported 79-pass local run. Item 6–7 still require final review, and item 9 is part of the Exit-Gate completion work.

## 10. Working Method

Use:

```text
UNDERSTAND
→ MAP
→ DESIGN
→ DISCUSS TRADE-OFFS
→ DECIDE
→ TEST
→ IMPLEMENT
→ REVIEW
→ REFACTOR
→ DOCUMENT
→ COMMIT
→ PUSH
→ UPDATE PROJECT STATE
```

Small documentation corrections can be fixed directly. Changes affecting business meaning, architecture, ownership, or contracts require a Design Gate.

## 11. Git / Local Synchronization Rule

Before repository-dependent implementation, the local working copy must be synchronized with the relevant GitHub branch.

After meaningful completed work:

```text
Design → Implement → Test → Review → Document → Commit → Push → Update Project State
```

If branch divergence, uncommitted local work, merge/rebase risk, or another blocker is discovered, surface it immediately rather than silently changing direction.

## 12. Learning Mission

This project is also training for Tech Lead / Software Manager / Software Architect responsibilities.

The goal is not merely to make code work. The project should teach:

- domain modeling
- architecture and boundaries
- requirements and trade-offs
- TDD
- design patterns when a real problem justifies them
- Git/GitHub and professional workflows
- code review and refactoring
- CI/CD
- production considerations
- evaluating AI-generated implementation instead of blindly accepting it

## 13. Source of Truth

When resolving project state, review the relevant combination of:

- `PROJECT_CONSTITUTION.md`
- this `PROJECT_CONTEXT.md`
- roadmap/backlog
- architecture documentation
- ADRs
- implementation
- tests
- Git history

Code and documentation must not describe different realities.

## 14. Final Principle

> We are not merely writing code. We are designing a serious automation platform while learning how professional software is engineered.
