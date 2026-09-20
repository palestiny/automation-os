# Automation OS

Automation OS is a modular automation platform for turning business intent into repeatable, executable workflows.

It is **not** a single-purpose YouTube automation script and it is not coupled to one AI provider. AI is treated as a replaceable capability behind explicit boundaries.

## Current project state

The current source of truth for project position is [PROJECT_STATUS.md](PROJECT_STATUS.md).

**Current phase:** Phase 7 — Execution Reliability and Operational Visibility  
**Status:** Completed  
**Next major capability:** Not selected  
**Next gate:** [Post-Phase-7 Design Gate](docs/02-Architecture/POST_PHASE_7_DESIGN_GATE.md)

There is currently no committed Phase 8. A new major capability requires a Design Gate and explicit Project Owner selection before implementation.

## Core model

The platform is organized around the following conceptual flow:

~~~text
Idea
  ↓
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
~~~

Execution is the central runtime concern. Workflow selection, capabilities, providers, and AI integrations are kept behind explicit boundaries so they can evolve independently.

## Architecture principles

- Modular Monolith
- Domain-Driven Design principles
- Clean Architecture principles
- SOLID
- Explicit domain/application/infrastructure boundaries
- Capability and provider replaceability
- Testability first
- TDD for domain behavior
- Design Gates before major capability activation

## Current capabilities

The repository currently contains foundations for:

- intent analysis and canonical goals;
- deterministic workflow selection;
- workflow execution and lifecycle control;
- execution progress, discovery, cancellation, resume, and retry;
- workflow discovery and generation/validation boundaries;
- marketplace discovery, publication, and installation foundations;
- content-automation boundaries;
- execution reliability and operational evidence from Phase 7;\n- PostgreSQL durable persistence for workflows, executions, idempotency, and execution history.

See the detailed architecture and roadmap documents for authoritative behavior and boundaries.

## Phase 7

Phase 7 — Execution Reliability and Operational Visibility is complete.

It established:

- workflow-start idempotency;
- deterministic duplicate-request behavior;
- append-only execution history;
- bounded structured execution lifecycle events;
- execution/workflow correlation;
- explicit operational-evidence failure semantics.

The authoritative records are:

- [Design Gate](docs/02-Architecture/PHASE_7_EXECUTION_RELIABILITY_DESIGN_GATE.md)
- [Roadmap](docs/01-Roadmap/PHASE_7_EXECUTION_RELIABILITY.md)
- [Exit Review](docs/02-Architecture/PHASE_7_EXECUTION_RELIABILITY_EXIT_REVIEW.md)

## Development rules

The project follows:

~~~text
Understand
→ Map
→ Design
→ Trade-offs
→ Decide
→ TDD RED
→ GREEN
→ Verify
→ Refactor
→ Document
→ Review
→ Next task
~~~

The Project Owner retains authority over product direction, major architecture, capability selection, scope, priorities, and significant trade-offs.

Autonomous engineering may continue for safe maintenance, verification, tests, documentation, bug fixes, and consistency work. It must stop for the decision boundaries defined in [AUTONOMOUS_PROJECT_DEVELOPMENT_MODE.md](AUTONOMOUS_PROJECT_DEVELOPMENT_MODE.md).

## Running the project

Python 3.13 is used by the GitHub Actions test workflow.

Install dependencies:

~~~powershell
python -m pip install -r requirements.txt
~~~

Run the test suite:

~~~powershell
python -m pytest
~~~

Run the application locally:

~~~powershell
uvicorn app.main:app --reload
~~~

## Documentation map

| Need | Start here |
|---|---|
| Current project position | [PROJECT_STATUS.md](PROJECT_STATUS.md) |
| Engineering operating rules | [AGENTS.md](AGENTS.md) |
| Autonomous execution rules | [AUTONOMOUS_PROJECT_DEVELOPMENT_MODE.md](AUTONOMOUS_PROJECT_DEVELOPMENT_MODE.md) |
| Project constitution | [PROJECT_CONSTITUTION.md](PROJECT_CONSTITUTION.md) |
| Roadmap | [docs/01-Roadmap/](docs/01-Roadmap/) |
| Architecture and Design Gates | [docs/02-Architecture/](docs/02-Architecture/) |
| Decisions | [docs/04-DECISIONS/](docs/04-DECISIONS/) |
| Development history | [docs/06-Journal/DEVELOPMENT_HISTORY.md](docs/06-Journal/DEVELOPMENT_HISTORY.md) |

## Git workflow

The default feature workflow is:

~~~text
Issue
→ Branch
→ Implementation
→ Tests
→ Review
→ Merge
~~~

GitHub is the project's source of truth. Documentation that represents current project state must remain consistent with master.

## Long-term direction

The platform is intended to support multiple automation domains over time, including content automation, business automation, AI-assisted workflows, workflow marketplace capabilities, and a broader plugin/capability ecosystem.

Those are long-term directions, not automatically committed milestones.

## License

No project license has been declared yet.
