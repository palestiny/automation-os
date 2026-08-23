# Decision Log

This is the short chronological record of important project decisions.

## Current Decisions

### D-001 — Modular Monolith

We use a Modular Monolith as the current architecture.

Reason:
We need strong module boundaries without prematurely introducing distributed-system complexity.

### D-002 — Execution as Core Runtime Concept

Execution is treated as the central runtime domain concept.

Reason:
The platform's value is not merely defining workflows; it is reliably executing them.

### D-003 — Plugin/Capability Direction

Capabilities are separated from provider implementations.

Reason:
AI providers and external platforms are replaceable.

### D-004 — Documentation as Engineering

Architecture, decisions, roadmap and learning outcomes are maintained as project artifacts.

Reason:
The project is both a product and a structured learning journey.

### D-005 — Tests as Specification

Behavioral tests are treated as executable specifications for domain transitions.

Reason:
Stateful domain behavior is easier to preserve when transitions are explicitly tested.
