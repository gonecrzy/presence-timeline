# Architecture

## Goal

Build a private, self-hosted Home Assistant integration and dashboard stack that answers:

- Where is someone now?
- When were they there?
- Is anything safety-relevant happening?

## Current boundaries

- Home Assistant remains the live event source.
- `GpsTrack API` subscribes to Home Assistant state, normalizes it, stores independent history, and derives higher-level views.
- The current delivery surface is a standalone REST API plus workers, not yet a Home Assistant-native integration or dashboard.

## Current backend components

### API layer

- FastAPI application
- Versioned REST routes under `/api/v1`
- Current routes cover health, members, member history/timeline/stops/trips/safety, and places
- Responses already hide Home Assistant field names behind normalized schemas

### Domain layer

- `Family`
- `Member`
- `Device`
- `LocationPoint`
- `Place`
- `Trip`
- `DailySummary`
- `SafetyEvent`

These tables are still useful for the pivot because they already represent backend-owned history and derived views instead of raw Home Assistant payloads.

### Provider layer

- `LocationProvider` defines the ingestion contract.
- `HomeAssistantWebSocketProvider` snapshots `/api/states` and subscribes to websocket `state_changed` events.
- Provider payloads are normalized into backend events before persistence.
- The ingestion worker supports auto-discovery of Home Assistant trackers.

### Storage and derivation

- PostgreSQL + PostGIS
- Raw points include timestamps, source/provider metadata, battery, and spatial fields
- Derived trips, daily summaries, stop summaries, and safe-zone events are stored separately from raw history
- Retention is controlled by `GPSTRACK_RETENTION_DAYS`
- Schema evolution is managed through Alembic migrations

### Auth posture

- Current API mode is intentionally `open` for local development.
- There is an unused path toward external OIDC, but that is not the right end state for a Home Assistant-native product.
- A Home Assistant-focused branch should expect to replace or wrap the current request auth model with Home Assistant auth, ingress, or trusted internal service boundaries.

## Target shape after the pivot

The likely end state is a two-layer system:

1. A durable history/derivation service that keeps the current database and ingestion responsibilities.
2. A Home Assistant-facing integration surface that exposes entities, services, panels, cards, or API adapters inside Home Assistant.

That shape fits the current codebase better than forcing the entire service into a pure in-process Home Assistant integration.

## What is missing today

- No Home Assistant custom integration package under `custom_components/`
- No config-entry flow, options flow, or Home Assistant service registration
- No Lovelace card, dashboard bundle, or custom panel frontend
- No Home Assistant auth/ingress handling
- No packaging decision for database-backed deployment in a Home Assistant environment

## Current milestone status

The branch already has the hardest backend foundation pieces:

- provider ingestion
- normalized persistence
- geospatial derivation
- tested API views over the derived data

The next milestone should move from "standalone API with Home Assistant as input" to "Home Assistant product surface backed by this API."
