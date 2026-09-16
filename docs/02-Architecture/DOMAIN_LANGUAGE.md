# Domain Language

Status: Baseline

These terms have architectural meaning and should be used consistently.

## Intent

The desired business objective expressed by a user or upstream system. Intent describes what should be achieved, not which provider should be used.

## Workflow

A definition describing what should be executed. A workflow is a plan, not a runtime execution.

## Workflow Step

A single executable unit within a workflow definition.

## Execution

A concrete runtime instance of a workflow. Execution owns runtime state such as current step, state, attempt count and lifecycle timestamps.

## Capability

A business-meaningful ability that the system can invoke. A capability is independent of one specific implementation or provider.

## Plugin

A replaceable implementation or integration that provides a capability.

## Asset

A business-relevant data/resource used or produced by an execution. Examples include video, audio, subtitle, image or generated content.

## Outcome

The meaningful business result produced by an automation workflow.

## Execution Context

Runtime data required to execute a workflow. It is separate from the workflow definition and should not become an unstructured global state container.

## Orchestrator

An application-level coordinator responsible for driving execution. It coordinates domain objects and capabilities but does not replace domain rules.

## Attempt

One try within the lifecycle of an Execution. Retry behavior changes the attempt while preserving the execution identity.

## Terminology Rule

If a term is used differently in code and documentation, stop and resolve the terminology instead of silently introducing another meaning.
