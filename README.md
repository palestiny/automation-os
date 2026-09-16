# Automation OS

Automation OS is a modular automation platform for transforming ideas into executable business workflows.

## Mission

> Transform ideas into executable business workflows.

The current implementation focuses on the workflow and execution foundations that make an automation platform possible.

## Current Architecture

```text
Workflow (definition)
    |
    +-- WorkflowStep
    +-- Transition
    +-- Condition reference
    |
    v
Orchestrator
    |
    +-- ConditionEvaluator / ConditionRegistry
    +-- CapabilityDispatcher
    +-- ExecutionContext
    |
    v
Execution (runtime)
    |
    +-- ExecutionStep
    +-- runtime state / attempts
    +-- selected step progression
```

### Core boundaries

- **Workflow** owns the reusable definition, transitions, publication state, and structural validation.
- **Orchestrator** coordinates runtime capability execution, condition evaluation, and transition selection.
- **Execution** owns runtime lifecycle, step state, retries, context-related runtime progression, and application of the selected next step.
- **Capabilities** perform the actual work and remain replaceable implementation details.

## Current Phase

The project is currently in **Phase 3 — Workflow Engine**.

Implemented foundations include:

- Workflow definition and validation.
- WorkflowStep definitions.
- Minimal WorkflowBuilder.
- Explicit Transition routing.
- Named condition references.
- In-memory ConditionRegistry.
- ExecutionContext flow between capabilities.
- Explicit conditional routing with no-match/multiple-match errors.
- Workflow graph reachability validation.

The exact current test count is intentionally not stated here until it is re-verified by a local test run or CI.

See `docs/01-Roadmap/ROADMAP.md` for the authoritative project roadmap and the architecture/design documents under `docs/` for committed decisions and open questions.

## Engineering Approach

The project follows a domain-first, test-driven workflow:

```text
UNDERSTAND
    -> MAP
    -> DESIGN
    -> DISCUSS TRADE-OFFS
    -> DECIDE
    -> TEST
    -> IMPLEMENT
    -> REVIEW
    -> REFACTOR
    -> DOCUMENT
    -> COMMIT / PUSH
```

Project roles and collaboration rules are defined in `KHALED_ENGINEERING_WORKING_RULES.md`.

## Non-Goals

Automation OS is not tied to a single AI provider or external platform. Specific capabilities such as YouTube ingestion, transcription, publishing, and AI-powered processing are later implementation areas rather than the definition of the platform itself.
