# Architecture Decisions

This directory contains accepted architectural decisions (ADRs).

## Current ADRs

- `ADR-001-ModularMonolith.md` — the system is a modular monolith while domain boundaries mature.
- `ADR-002-CoreDomain.md` — Execution is the central runtime domain concept.
- `ADR-003-PluginArchitecture.md` — business capabilities are separated from replaceable implementations/providers.
- `ADR-004-ExecutionAggregateSemantics.md` — defines the lifecycle, progress, retry, waiting, timestamp, and completion-ownership semantics of the Execution aggregate.
- `ADR-005-ExecutionContext.md` — defines the runtime-data boundary, ownership, mutation model, and lifecycle relationship of Execution Context.

## ADR Rule

Create an ADR when a decision has lasting architectural consequences, affects module boundaries, introduces a major dependency, or reverses an existing decision.

An ADR should state:

- context;
- decision;
- rationale;
- consequences;
- review trigger when appropriate.

The roadmap and development journal may reference decisions, but they should not silently replace the ADR as the source of truth for the decision itself.
