# AutoReel AI — Project Context

> **Purpose:** This file is the operational memory of the project.
>
> It exists to prevent loss of context, architectural drift, repeated decisions, and forgetting the current position in the project.
>
> **Repository:** https://github.com/palestiny/automation-os.git

---

# 1. Project Identity

**Project Name:** AutoReel AI
**Repository:** `palestiny/automation-os`
**Architecture Direction:** Modular Monolith
**Primary Language:** Python
**Current Framework:** FastAPI
**Current Environment:** Python virtual environment (`.venv`)
**Current Branch:** `master`

The project started as a FastAPI application and is being evolved into an **Automation Operating System**.

---

# 2. Mission

> **Transform ideas into executable business workflows.**

---

# 3. Vision

AutoReel AI is not intended to remain a YouTube automation tool.

The long-term vision is an **Automation Platform / Automation Operating System** capable of transforming business ideas into repeatable, executable workflows.

AI is a capability of the system, not the system itself.

---

# 4. Core Principles

1. **AI is replaceable.**
2. **Workflow is not the product.**
3. **Execution is the core of the system.**
4. **Every capability should be pluggable.**
5. **Domain first.**
6. **Infrastructure second.**
7. **Business before technology.**

---

# 5. What We Are Building

We are building an:

> **Automation Operating System**

It is not:

- a collection of scripts
- a YouTube downloader
- a ChatGPT wrapper
- a collection of unrelated automation features

The system should eventually provide a general mechanism for converting intent into executable business workflows.

---

# 6. Long-Term Goals

Potential long-term capabilities include:

- Content Automation
- Trend Cloning
- News Automation
- Business Automation
- AI Agents
- Workflow Marketplace
- Plugin Ecosystem

These are **long-term goals**, not necessarily immediate implementation tasks.

---

# 7. Explicit Non-Goals / Anti-Coupling Rules

The core architecture must not become tightly coupled to:

- OpenAI
- YouTube
- TikTok
- Whisper
- any single AI provider
- any single external platform

External technologies should be replaceable behind capabilities, interfaces, adapters, or plugins where appropriate.

---

# 8. Target Business Flow

The conceptual target flow is:

```text
Idea
  ↓
Intent
  ↓
Intent Analysis
  ↓
Workflow Selection / Generation
  ↓
Execution
  ↓
Capability Dispatcher
  ↓
Capability / Plugin
  ↓
Asset Processing
  ↓
Outcome
  ↓
Business Result
```

The architecture should evolve toward this model without prematurely implementing unnecessary infrastructure.

---

# 9. Core Domain Concepts

The current conceptual domain language includes:

- Intent
- Workflow
- Workflow Step
- Execution
- Execution State
- Capability
- Capability Dispatcher
- Capability Registry
- Plugin
- Asset
- Outcome
- Execution Context
- Retry Policy
- Orchestrator

The important conceptual relationship is:

```text
Intent
  ↓
Workflow
  ↓
Execution
  ↓
Capability
  ↓
Asset
  ↓
Outcome
```

---

# 10. Execution Is the Core

The project deliberately treats **Execution** as a central domain concept.

Execution represents the lifecycle of running a workflow.

The execution lifecycle has evolved through explicit domain modeling and tests.

Current conceptual states include:

```text
CREATED
RUNNING
WAITING
RETRYING
COMPLETED
FAILED
CANCELLED
```

The exact transition rules must remain encoded in the domain model and protected by tests.

Execution retry behavior was explicitly implemented and tested.

---

# 11. Current Architectural Direction

The agreed architectural direction is:

> **Modular Monolith + Domain Driven Design + Clean Architecture principles + Plugin Architecture**

Engineering principles include:

- Clean Architecture
- Modular Monolith
- Domain Driven Design
- SOLID
- Event-driven thinking
- Plugin Architecture
- Testability First

We should not introduce distributed systems, microservices, message brokers, or other infrastructure merely because they are common enterprise technologies.

Architecture should evolve according to actual requirements.

---

# 12. Current Application Structure

The project currently contains concepts organized approximately around:

```text
app/
├── api/
├── application/
├── core/
│   ├── assets/
│   ├── capabilities/
│   └── workflow/
├── domain/
├── models/
├── schemas/
└── services/
```

Important application concepts currently include:

```text
application/
├── capability_dispatcher.py
├── capability_registry.py
├── capability_result.py
├── errors.py
├── execution_context.py
├── orchestrator.py
└── retry_policy.py
```

Domain concepts include:

```text
domain/
├── execution.py
└── workflow.py
```

This structure is expected to evolve.

The directory structure is **not itself the architecture**.

The architecture is defined by responsibilities, dependencies, boundaries, and domain rules.

---

# 13. Current Milestone

The project has completed the initial Execution domain lifecycle.

Git history currently shows:

```text
8ed162f docs: establish project documentation baseline
d0924bc Add execution retry lifecycle
dfcdd0b feat: complete execution lifecycle
1700bf1 feat: add execution state transitions
70eb4c4 feat: add execution domain and tests
4170d3b Initial FastAPI project
06821d8 Initial FastAPI project
```

The project has therefore moved beyond the initial FastAPI skeleton and into architectural/domain implementation.

---

# 14. Current Test Status

At the latest verified point:

```text
45 passed in 0.36s
```

The project previously encountered:

```text
ModuleNotFoundError: No module named 'app'
```

during direct `pytest -q`.

The issue was diagnosed as an environment/module-resolution issue.

The verified working command became:

```powershell
python -m pytest -q
```

with the project's `.venv` active.

Current rule:

> Prefer `python -m pytest` so the test runner is executed by the same Python interpreter currently being used by the project.

---

# 15. Git / GitHub Status

The project uses Git and GitHub as part of the engineering process.

The repository is:

```text
https://github.com/palestiny/automation-os.git
```

The agreed development model is:

```text
Issue
  ↓
Branch
  ↓
Implementation
  ↓
Tests
  ↓
Review
  ↓
Documentation
  ↓
Commit
  ↓
Push / Merge
```

The project owner should understand not only the commands but also **why each command is used**.

Git commands must therefore be explained during the learning process.

---

# 16. Learning Mission

This project is also a structured learning journey.

The developer is not merely trying to finish an application.

The learning objectives are to develop the ability to:

- think like a Software Architect
- think like a Tech Lead
- understand enterprise software design
- understand Domain Driven Design
- learn and apply Design Patterns
- understand architectural patterns
- understand Git deeply
- understand GitHub workflows
- understand testing strategies
- understand documentation practices
- understand requirements engineering
- understand refactoring
- understand code review
- understand CI/CD
- understand production-quality development
- use AI effectively as an engineering assistant
- learn how to evaluate AI-generated code rather than blindly accepting it

---

# 17. Design Patterns Learning Rule

Design Patterns are not to be studied only theoretically.

They should be introduced **when the project encounters a real problem that makes a pattern useful**.

For every important pattern encountered, the learning process should explain:

1. What problem exists?
2. Why the problem matters?
3. What solutions were considered?
4. Why the selected pattern fits?
5. What the pattern is called.
6. What the pattern's responsibilities are.
7. What trade-offs it introduces.
8. Where it appears in this project.
9. When the pattern should NOT be used.

The goal is to learn architectural thinking rather than memorizing pattern names.

---

# 18. Software Architecture Learning Rule

The developer should be trained to ask architectural questions before implementation.

Before creating significant components, consider:

```text
What problem are we solving?

Who owns this responsibility?

What is the domain rule?

What should depend on what?

What should remain replaceable?

What is the boundary?

What changes frequently?

What should remain stable?

What happens when this component fails?

How will we test it?

How will we replace it?

What happens when the system becomes 10x larger?
```

The goal is to learn to make decisions, not merely to write code.

---

# 19. AI Collaboration Agreement

The AI assistant is acting as a combination of:

- technical mentor
- software architect
- implementation assistant
- reviewer
- documentation assistant
- project planning assistant

However:

> **The AI is not the owner of the project.**

The developer must understand and approve important architectural decisions.

The AI should explain significant decisions instead of silently making them.

When appropriate, the AI should challenge an idea rather than automatically agreeing with it.

---

# 20. Important Learning Agreement

The developer explicitly wants to work on this project as if working inside a real software company.

Therefore the project should be used to teach:

- requirements
- planning
- architecture
- domain modeling
- design patterns
- Git
- GitHub
- branches
- issues
- commits
- pull requests
- code review
- testing
- documentation
- ADRs
- RFCs
- CI/CD
- refactoring
- debugging
- dependency management
- production considerations
- technical debt
- project management
- architectural trade-offs

The developer should not be expected to know what he does not yet know.

The mentor's responsibility is therefore also to identify missing concepts and introduce them at the appropriate time.

---

# 21. Documentation Rules

> **If it isn't documented, it doesn't exist.**

Documentation is part of the product.

Important decisions should not live only inside the chat conversation.

The repository should contain the durable project knowledge.

Documentation should answer:

```text
Why are we building this?
What are we building?
What are we not building?
What is the domain?
How is the system structured?
Why was this architecture selected?
What decisions were made?
What have we learned?
What mistakes occurred?
Where are we now?
What comes next?
```

---

# 22. Documentation Responsibilities

The AI is responsible for proposing and maintaining project documentation during the collaboration.

The developer is responsible for reviewing and approving important documented decisions.

Documentation must be kept synchronized with actual project state.

If implementation changes an architectural decision, the documentation should be updated.

If the roadmap changes, the roadmap should be updated.

If a major lesson is learned, it should be recorded.

---

# 23. Source of Truth

Different types of information have different sources of truth.

### Project Constitution

Defines:

- principles
- working agreement
- long-term rules
- learning mission

### Project Context

Defines:

- current project state
- current milestone
- current architecture state
- current next step
- active context

### Roadmap

Defines:

- planned milestones
- future direction
- sequence of major work

### Architecture Documentation

Defines:

- architectural structure
- modules
- boundaries
- technical decisions

### ADRs

Define:

- important architectural decisions
- alternatives
- reasoning
- consequences

### Tests

Define:

- executable behavioral expectations
- domain invariants

### Git History

Defines:

- what actually changed
- when it changed
- why through commit messages where available

---

# 24. Anti-Drift Rule

Before starting a significant new milestone, the AI should review:

```text
PROJECT_CONSTITUTION.md
PROJECT_CONTEXT.md
ROADMAP.md
relevant architecture documentation
relevant ADRs
relevant tests
current Git status/history
```

The purpose is to prevent:

- forgetting previous agreements
- repeating decisions
- architectural drift
- implementing unrelated features
- losing the current position
- abandoning the learning objectives

---

# 25. Current Immediate Direction

The next major technical area is:

> **Workflow → Execution Orchestration**

The relevant development branch is:

```text
feature/workflow-execution-orchestration
```

The objective is to evolve the system from having an Execution domain model toward actually orchestrating workflow execution.

Before implementation, the existing workflow, execution, capability, dispatcher, registry, execution context, retry policy, and related tests should be reviewed.

---

# 26. Immediate Next Steps

The current sequence should be:

```text
1. Review current repository state
2. Review current documentation
3. Review Workflow domain
4. Review Execution domain
5. Define orchestration responsibility
6. Identify boundaries
7. Define Orchestrator contract
8. Define tests / acceptance criteria
9. Implement minimal orchestration
10. Run tests
11. Review design
12. Document architectural decisions
13. Commit
14. Push
15. Update PROJECT_CONTEXT.md
16. Move to the next milestone
```

Do not skip directly from idea to large implementation.

---

# 27. Definition of Done

A significant feature is not considered complete merely because the code works.

A feature is complete when:

```text
Requirement understood
        ↓
Design understood
        ↓
Tests defined
        ↓
Implementation complete
        ↓
Tests passing
        ↓
Code reviewed
        ↓
Documentation updated
        ↓
Git commit created
        ↓
GitHub updated
        ↓
Project context updated
```

---

# 28. Working Style

The preferred working style is:

> **Small steps, explicit decisions, tests first where practical, continuous documentation, frequent verification.**

Avoid large uncontrolled changes.

When an unexpected problem appears:

```text
Stop
↓
Understand
↓
Explain
↓
Choose
↓
Implement
↓
Test
↓
Document
```

Do not hide errors merely to make tests pass.

---

# 29. Current Known Lesson

One important lesson already encountered:

Running:

```powershell
pytest -q
```

and running:

```powershell
python -m pytest -q
```

are not always equivalent from an environment/module-resolution perspective.

The project encountered:

```text
ModuleNotFoundError: No module named 'app'
```

when using the first form, while:

```powershell
python -m pytest -q
```

successfully discovered the application package and produced:

```text
45 passed
```

This is now part of the project's practical learning history.

---

# 30. Relationship Between Code and Documentation

Documentation should never become a fictional description of the project.

There are three acceptable states:

```text
Implemented
Planned
Proposed
```

These states must not be confused.

A planned architecture is not an implemented architecture.

A proposed capability is not an existing capability.

A documented decision should identify its status when necessary.

---

# 31. Final Project Principle

> **We are not merely writing code.**
>
> **We are designing a business platform while learning how professional software is engineered.**

The ultimate goal is therefore twofold:

```text
Build a serious Automation Platform
+
Become capable of designing serious software independently
```

---

# 32. Last Updated

**Status:** Active
**Purpose:** Persistent project context
**Repository:** https://github.com/palestiny/automation-os.git

This document should be updated whenever the project's strategic direction, architecture, milestone, learning objectives, or immediate next step materially changes.
