# ADR-001 — Modular Monolith

## Status

Accepted

## Context

The platform requires strong separation between domain, application, capabilities and infrastructure.

A distributed microservice architecture would introduce complexity before the domain boundaries are mature.

## Decision

Use a Modular Monolith.

## Consequences

Positive:

- simple deployment;
- shared runtime;
- explicit module boundaries;
- easier local development;
- lower operational complexity.

Negative:

- boundaries must be enforced by discipline;
- modules can become coupled if architecture is neglected.

## Review Trigger

Reconsider only when scaling, deployment independence, organizational boundaries or operational requirements justify distribution.
