# Automation OS — Engineering Book

This is the long-form learning record of the project.

## How to Use It

The project should be understandable from its documentation without relying on memory of previous chat sessions.

The constitution explains the rules and engineering principles.

The charter explains the mission, scope and long-term direction.

The roadmap explains where we are going and what phase is currently active.

The architecture documents explain how the system is organized.

ADRs explain important architectural decisions and their trade-offs.

The development process explains how work is planned, implemented, tested and reviewed.

The Definition of Done explains when a milestone is actually complete.

The test strategy explains how behavior is verified.

The journal explains what happened and what comes next.

## Source of Truth Hierarchy

When documents appear to conflict:

1. Project Constitution — project-wide rules.
2. Project Charter — mission, scope and non-goals.
3. ADRs — committed architectural decisions.
4. Roadmap — current direction and phase scope.
5. Development Process — execution method.
6. Journal — historical record.
7. Learning notes — explanation and lessons.

A historical note must not silently override an accepted decision.

## Core Loop

Understand
→ Plan
→ Document
→ Implement
→ Test
→ Review
→ Commit
→ Reflect
→ Update Documentation
→ Continue

## Design Gate

Before major implementation, confirm that the problem, destination, domain model, boundaries, constraints and important trade-offs are sufficiently understood.

## Current State

Phase 0 — Foundation: complete.

Phase 1 — Documentation & Architecture Baseline: complete.

Phase 2 — Execution Engine: complete.

Phase 3 — Workflow Engine: complete.

Phase 4 — Capability / Plugin Architecture: complete.

Phase 5 — Content Automation: complete.

Phase 6 — Platform Generalization: complete for its committed scope.

The current platform boundary includes intent-driven execution across multiple domains plus marketplace discovery, publication, deterministic search and installation foundations.

The next milestone must be selected from a concrete capability with an explicit Design Gate. Deferred platform-generalization items are not automatically promoted into implementation.

The runtime now also has a synchronous scheduling composition boundary: a due scheduled request can start a RUNNING Execution and drive it through the existing multi-step orchestrator. Recurring scheduling, workers and background infrastructure remain explicitly deferred.

The runtime now also exposes an explicit cancellation application boundary: cancellation resolves the persisted Execution, delegates lifecycle rules to Execution.cancel(), and persists the cancelled result. Cancellation reasons, authorization, worker interruption, compensation, and distributed cancellation remain deferred.

The runtime now also exposes a resumed-execution composition boundary: a persisted WAITING Execution can be resumed through the existing domain lifecycle and then continued synchronously by the existing workflow orchestrator. Durable execution context, automatic wake-up and background infrastructure remain explicitly deferred.

The runtime now also exposes an explicit retry application boundary: a persisted FAILED Execution can transition to RETRYING through the existing Execution.retry() invariant and persist its incremented attempt. Automatic retry policy, backoff, scheduling and re-execution remain deferred.

The runtime now also exposes an explicit caller-requested retry composition boundary: a FAILED Execution can move through RETRYING to RUNNING and continue through the existing workflow orchestrator. The retry attempt receives a fresh in-memory ExecutionContext. Automatic retry policy, backoff, scheduling, workers, queues and durable retry context remain deferred.


The runtime now also has a thin HTTP execution-control boundary for progress, cancellation, resume, retry, and explicit retry-and-execute. It composes existing application use cases without introducing a second lifecycle model or background infrastructure. Authentication, durable persistence, and distributed control remain deferred.
