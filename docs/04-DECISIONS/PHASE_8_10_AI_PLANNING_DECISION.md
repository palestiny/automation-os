# Phase 8.10 — AI Planning Layer Decision

Status: **APPROVED**

The Project Owner selected **Option A — Application-level Planner Port**.

AI proposes a structured plan. Deterministic validation remains authoritative before a Workflow or WorkflowVersion is created. The domain and execution lifecycle remain independent of concrete AI providers.

```text
AI Planner → Proposal → Deterministic Validation → Workflow Artifact → Existing Runtime
```

Deferred: concrete LLM vendor, autonomous agent loops, tool calling, prompt management, memory, learning loops, and AI marketplace behavior.
