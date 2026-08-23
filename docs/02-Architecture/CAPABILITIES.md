# Capabilities

A Capability describes something the Automation OS can do.

Examples:

- download video;
- transcribe audio;
- extract clip;
- publish content;
- schedule publication.

## Capability vs Service

Capability:

> What the system can do.

Service:

> How one implementation performs it.

For example:

`DownloadVideo` is a capability.

`YouTubeService` is one implementation/provider-oriented service.

## Goal

The system should be able to replace implementations without rewriting the domain model.

## Future

Capabilities may be backed by:

- local libraries;
- external APIs;
- AI providers;
- plugins;
- internal services.

The domain should not need to know which provider performed the operation.
