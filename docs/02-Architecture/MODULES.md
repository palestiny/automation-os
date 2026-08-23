# Module Boundaries

## Current Direction

The system is a Modular Monolith.

Modules are separated by responsibility and domain meaning while remaining inside one deployable application.

## Main Areas

### Domain

Owns business concepts and business rules.

Examples:

- Execution
- Workflow
- WorkflowStep
- Asset

Domain code should not depend on FastAPI, YouTube, OpenAI, Whisper or other infrastructure details.

### Application

Coordinates use cases.

Examples:

- Orchestrator
- CapabilityDispatcher
- CapabilityRegistry
- ExecutionContext
- RetryPolicy
- CapabilityResult

Application code coordinates domain behavior but should not contain provider-specific implementation details.

### Core / Capabilities

Defines capability/plugin contracts and supporting mechanisms.

### Services

Contains infrastructure-facing implementations.

Examples:

- YouTube service
- Whisper service
- Publisher service
- Subtitle service

### API

Contains HTTP-facing adapters.

API routes should translate HTTP requests into application operations rather than becoming the business domain.

### Models / Schemas

Models represent transport or operational data where appropriate.

## Boundary Rule

A lower-level implementation must not leak its technology-specific concerns into the domain model.

Example:

The domain should express a capability such as "download asset", not "call yt-dlp with these exact options".
