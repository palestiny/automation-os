# ADR-003 — Capability and Plugin Architecture

## Status

Accepted

## Decision

Separate business capabilities from their implementations.

## Rationale

External providers are replaceable.

The system must not make OpenAI, YouTube, Whisper or any other provider part of the core business model.

## Consequence

Provider integrations should live behind capability-oriented contracts and application boundaries.
