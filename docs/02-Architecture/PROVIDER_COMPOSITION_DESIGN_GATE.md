# Provider Composition Design Gate

## Purpose

Extend provider abstraction beyond individual adapters without introducing provider-specific logic into the domain or creating an autonomous routing system.

## Decisions

1. Provider abstraction is expressed through existing application ports, not a generic mega-provider interface.
2. Capability implementations continue to be resolved by the existing CapabilityRegistry.
3. IntentAnalyzer implementations may be registered and resolved through a dedicated IntentAnalyzerRegistry.
4. Registry keys are explicit provider-neutral analyzer identifiers.
5. Registry resolution is deterministic and does not choose providers based on AI output.
6. Provider SDKs, credentials, model settings, retries, and fallback policies remain inside infrastructure/composition.
7. The application layer depends only on IntentAnalyzer.
8. No automatic provider fallback, model routing, health-based selection, or cost optimization is introduced.
9. A configured application composition chooses which analyzer implementation to inject.
10. Multiple analyzers may coexist without changing Intent, Workflow, or Execution.

## Shape

**IntentAnalyzerRegistry → IntentAnalyzer implementation → provider SDK**

The registry is a composition mechanism, not a policy engine.

## Failure Semantics

- Duplicate identifiers are rejected.
- Unknown identifiers are rejected.
- Registry resolution never invokes a provider.
- Provider failures retain existing IntentAnalyzer semantics.

## Deferred

- automatic fallback;
- model/provider routing;
- health checks;
- provider scoring;
- dynamic discovery;
- remote plugin loading;
- marketplace provider installation.

## Exit Criteria

- multiple analyzer providers can be registered;
- application code remains provider-neutral;
- resolution is deterministic;
- no provider SDK crosses the application/domain boundary.
