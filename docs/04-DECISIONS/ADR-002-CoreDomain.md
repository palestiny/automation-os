# ADR-002 — Execution as Core Runtime Domain

## Status

Accepted

## Decision

Execution is the central runtime domain concept.

## Rationale

A workflow describes what should happen.

Execution represents what is actually happening, including state, progress, attempts and lifecycle transitions.

## Consequence

The architecture should preserve a clear distinction between workflow definition and execution runtime.
