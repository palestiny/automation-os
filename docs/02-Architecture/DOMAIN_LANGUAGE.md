# Domain Language

These terms have architectural meaning and should be used consistently.

## Execution

A concrete attempt to run a workflow.

Execution owns runtime state such as:

- current step;
- state;
- attempt count;
- timestamps.

## Workflow

A definition describing what should be executed.

A workflow is not itself an execution.

## Workflow Step

A single executable unit within a workflow.

## Capability

A business-meaningful ability that the system can invoke.

A capability should be independent of one specific implementation/provider.

## Asset

A piece of data/resource used or produced by an execution.

Examples may include video, audio, subtitle, image or generated content.

## Outcome

The meaningful result produced by execution.

## Intent

The desired business objective expressed by a user or upstream system.

## Orchestrator

Application-level coordinator responsible for driving execution.

## Plugin

A replaceable implementation of a capability.

## Rule

If a term is used differently in code and documentation, stop and resolve the terminology instead of silently introducing another meaning.
