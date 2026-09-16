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

The last locally verified baseline before the most recent context/output changes was:

```text
72 passed
```

After subsequent changes to CapabilityResult output propagation and ExecutionContext missing-value behavior, the local suite must be rerun before the next implementation milestone is considered verified.

Preferred command:

```powershell
python -m pytest
```

Do not claim a test result that has not actually been run.

## 6. Current Documentation Decisions

Relevant ADRs include:

- ADR-005 — Execution owns workflow-step progression.
- ADR-006 — CapabilityResult carries successful output and Orchestrator moves it into ExecutionContext.

These decisions deliberately defer Asset/Outcome transport semantics until those concepts have enough business meaning to justify a dedicated Design Gate.

## 7. Current Roadmap Position

Phase 0 — Foundation: complete.

Phase 1 — Documentation & Architecture Baseline: substantially complete; documentation consolidation and test-strategy work remain.

Phase 2 — Execution Engine: **in progress**.

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

Remaining Phase 2 work includes:

- JobManager integration decision/implementation
- integration-level verification
- remaining architecture/documentation consolidation
- Phase Exit Gate

## 8. JobManager Status

`app/core/job_manager.py` currently contains an older in-memory job-tracking implementation.

It is not yet integrated with the Execution aggregate or Orchestrator.

Do not redesign or integrate it silently. Its ownership, relationship to Execution, lifecycle mapping, and need for persistence/async execution require a Design Gate before implementation.

## 9. Next Design Gate

The next architectural question is the role of **JobManager**.

We need to decide whether JobManager is:

1. a thin application-facing progress/job adapter around Execution;
2. an application service that owns asynchronous execution lifecycle;
3. a legacy concern to defer/remove from the Execution Engine phase.

The decision must consider ownership, lifecycle mapping, synchronous versus asynchronous execution, persistence expectations, failure semantics, and trade-offs.

No JobManager integration should be implemented until this boundary is decided.

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
