# Workflow Graph Validation — Design Gate

- Status: Committed for the next Phase 3 implementation slice
- Phase: Phase 3 — Workflow Engine
- Scope: Structural validation of the Workflow transition graph
- Owner: Khaled (Project Owner / Decision Maker / Tech Lead)

## 1. Purpose

Define the minimum graph-level invariants that belong to the Workflow definition without turning the Workflow into a runtime graph engine.

## 2. Business Meaning

Once Workflow routing is represented explicitly by `Transition`, the Workflow is a directed graph of definition-level steps and transitions.

Graph validation answers only structural questions about the published definition. It must not evaluate runtime conditions or execute capabilities.

## 3. Ownership

### Workflow owns

- The set of WorkflowStep definitions.
- The set of Transition definitions.
- Structural validation of references and graph reachability.

### Orchestrator owns

- Runtime condition evaluation.
- Runtime transition eligibility.
- Selection of exactly one eligible transition.
- Coordination with Execution.

### Execution owns

- Runtime position and state.
- Applying the selected target.
- Runtime lifecycle and progression invariants.

## 4. Current Structural Baseline

`Workflow.add_transition()` already requires both source and target IDs to belong to the Workflow. A `Transition` also rejects self-transitions.

These checks protect individual transition validity but do not answer whether the complete Workflow graph is structurally coherent.

## 5. Committed First Validation Rule

For the first graph-validation slice:

> Every WorkflowStep must be reachable from the Workflow's first step through the declared transitions.

The first WorkflowStep is the entry point because Workflow step order remains part of the definition and the current Execution model starts at index `0`.

A Workflow with an unreachable step is structurally invalid for graph validation.

### Why

An unreachable step is part of the published definition but cannot be selected by the current routing model from the Workflow entry point. Keeping such a step silently would create dead definition that can never execute.

## 6. Validation Boundary

Graph validation should be an explicit Workflow/domain operation rather than hidden inside the Orchestrator.

The initial API should validate the definition without evaluating conditional transitions.

A conditional transition counts as a graph edge for reachability regardless of whether its runtime condition later evaluates to true or false. This is intentional: graph validation asks whether a structural path exists, not whether a particular runtime context will take that path.

## 7. What Is Deliberately Not Validated Yet

The first slice does **not** commit to:

- loop/cycle prohibition;
- guaranteed terminal reachability;
- condition satisfiability;
- mutually exclusive conditions;
- complete path coverage for runtime contexts;
- dead-end classification beyond ordinary terminal steps;
- parallel/joins;
- event-triggered graph entry;
- general graph optimization or normalization.

These require separate business requirements and design decisions.

## 8. Publication Boundary

Graph validation is not immediately made a mandatory replacement for the existing `publish()` contract in this slice.

Reason: existing direct Workflow construction can intentionally represent a definition before transitions are materialized, while the current builder creates explicit linear transitions. Making graph validation mandatory at publication without first defining the required construction lifecycle would silently change the existing Workflow contract.

The first implementation therefore introduces an explicit validation operation and tests it independently. Whether publication should require graph validation will be decided after this slice demonstrates the invariant and the project has a concrete construction lifecycle requirement.

## 9. Trade-offs

### Validate only transition references

- Pros: minimal and already implemented.
- Cons: allows unreachable definition steps.

### Validate reachability now

- Pros: catches definition dead content early; simple deterministic rule; does not require runtime condition evaluation.
- Cons: requires an explicit graph-validation operation and clear entry-point semantics.

### Introduce a full graph engine

- Pros: could support advanced analysis.
- Cons: far beyond current requirements and would introduce unnecessary graph semantics, cycle policies, joins, and path analysis.

The first slice chooses **reachability validation only**.

## 10. Test Intent

The implementation must cover at least:

1. A fully connected linear Workflow passes graph validation.
2. A branching Workflow whose targets are structurally connected passes graph validation.
3. An unreachable WorkflowStep is rejected.
4. Conditional transitions participate in structural reachability without being evaluated.
5. The validation does not mutate the Workflow.

## 11. Next Decision Boundary

After this slice, revisit whether graph validation should become a publication invariant. Do not add cycle/loop rules merely because graph traversal makes them technically possible.
