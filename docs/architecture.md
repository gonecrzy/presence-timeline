# Architecture

## Goal

Build a private, self-hosted family location platform where parents can answer:

- Where is someone now?
- When were they there?
- Is anything safety-relevant happening?

## Boundaries

- Home Assistant Companion on Android produces live device location updates.
- Home Assistant remains the live event source for the first provider.
- `GpsTrack API` subscribes to provider events, normalizes them, stores independent history, computes trips and summaries, and exposes a stable REST API.
- The mobile app will speak only to the `GpsTrack API`.

## Backend components

### API layer

- FastAPI application
- Versioned REST routes under `/api/v1`
- No Home Assistant field names in public responses

### Domain layer

- `Family`
- `Member`
- `Device`
- `LocationPoint`
- `Trip`
- `DailySummary`
- `SafetyEvent`

These tables are provider-agnostic and represent backend-owned truth after normalization.

### Provider layer

- `LocationProvider` interface defines the contract for event-producing integrations.
- `HomeAssistantWebSocketProvider` is the first implementation.
- Provider-specific payloads are normalized into backend domain events before persistence.

### Storage

- PostgreSQL + PostGIS
- Raw points stored with timestamps, source/provider metadata, battery, and spatial fields
- Derived trips and daily summaries stored separately from raw history
- Retention controlled by `GPSTRACK_RETENTION_DAYS`, default `7`

## First milestone

This foundation milestone intentionally stops at:

- service bootstrap
- domain model definition
- provider seam definition
- Home Assistant event normalization
- local Docker runtime

It does not yet include:

- authentication
- ingestion worker orchestration
- computed trip pipeline
- public timeline/playback endpoints
- mobile client
