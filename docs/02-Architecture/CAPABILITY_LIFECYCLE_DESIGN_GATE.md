# Capability Lifecycle Design Gate

Status: Approved

## Purpose

Define the lifecycle responsibility of a Capability without introducing an asynchronous worker model or a second execution lifecycle.

## Decisions

1. Capability instances are constructed by the application composition boundary.
2. CapabilityRegistry owns registration and runtime resolution only.
3. CapabilityDispatcher owns invocation only.
4. Workflow Execution owns workflow lifecycle and progression.
5. A capability does not own Execution state, retry policy, workflow progression, or terminal execution state.
6. Initial capability lifecycle is synchronous and instance-based.
7. Construction and configuration happen before dispatch; dispatch does not construct provider instances.
8. Capabilities are reusable application components. The first lifecycle contract therefore requires no mandatory startup/shutdown hooks.
9. Cleanup is the responsibility of the composition/application owner for any provider resource that requires it; the core Capability contract does not require disposal.
10. Provider-specific lifecycle requirements remain behind the provider implementation and must not leak into Workflow, Execution, or domain objects.
11. Failure is represented by CapabilityResult when it is a handled capability outcome; unexpected exceptions remain exceptions and are not converted by the lifecycle layer.
12. Async lifecycle, hot loading, health checks, circuit breakers, remote plugins, sandboxing, and dynamic discovery remain deferred.

## Responsibility Boundary

Composition/Factory -> constructs/configures capability instances.

Registry -> stores and resolves already constructed instances.

Dispatcher -> invokes the resolved capability.

Capability -> performs its operation and returns CapabilityResult.

Execution/Application runtime -> interprets the result and owns workflow progression/retry decisions.

## Consequence

There is intentionally no start/stop/dispose method on the core Capability protocol in this increment. Adding lifecycle hooks later requires a concrete requirement that cannot be satisfied by composition ownership alone.

## TDD Scope

The implementation increment will verify:

- constructed capabilities can be registered and resolved;
- registration does not construct capabilities;
- dispatch does not construct capabilities;
- capability execution remains synchronous;
- lifecycle ownership does not alter Execution state semantics;
- provider-specific cleanup is not part of the core capability contract.

## Deferred Questions

- Whether long-lived providers need explicit application startup/shutdown hooks.
- Whether capability instances should be singleton, scoped, or per-execution for specific providers.
- Async capabilities and worker lifecycle.
- Resource health and circuit breaking.
