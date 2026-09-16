# Domain Language

These terms have architectural meaning and should be used consistently.

## Execution

A concrete attempt to run a workflow.

Execution owns runtime state such as:

- current step;
- state;
- attempt count;
- timestamps.

Execution also owns workflow step progression through its execution-step lifecycle.

## Workflow

A definition describing what should be executed.

A workflow is not itself an execution.

## Workflow Step

A single executable unit within a workflow.

## Capability

A business-meaningful ability that the system can invoke.

A capability should be independent of one specific implementation/provider.

## Capability Result

The application-level result of invoking a capability.

It represents:

- success or failure;
- successful output, when one exists;
- failure information, when execution fails.

It is a transport/result contract for capability invocation, not a domain replacement for `Asset` or `Outcome`.

## Execution Context

Application-level runtime data shared between capability executions within one orchestration.

Successful capability output is placed into the context by the orchestrator so later steps can consume it. The current context key for a step output is the `WorkflowStep` identifier.

`ExecutionContext` is not a domain entity and does not own workflow progression.

## Asset

A piece of data/resource used or produced by an execution.

Examples may include video, audio, subtitle, image or generated content.

## Outcome

The meaningful result produced by execution.

## Intent

The desired business objective expressed by a user or upstream system.

## Orchestrator

Application-level coordinator responsible for driving execution and moving successful capability outputs into the execution context.

## Plugin

A replaceable implementation of a capability.

## Rule

If a term is used differently in code and documentation, stop and resolve the terminology instead of silently introducing another meaning.
