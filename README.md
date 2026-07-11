# GpsTrack

Private, self-hosted Home Assistant location history service and dashboard backend.

This branch is the Home Assistant-focused fork of the project. The Android app work is intentionally left behind on `feat/backend-foundation`.

## Repository layout

- `custom_components/gpstrack/`: Home Assistant custom integration intended for HACS delivery
- `backend/`: FastAPI service, normalized domain models, Home Assistant provider, and tests
- `docs/`: architecture notes and branch roadmap
- `docker-compose.yml`: local API + PostGIS runtime

## Architecture

This repo currently uses a sidecar model:

- Home Assistant installs `custom_components/gpstrack/` through HACS or as a manual custom integration.
- The backend still runs separately in Docker and is reached over HTTP by the integration.
- Home Assistant is the live event source; the backend owns normalized history, places, trips, stops, and safety derivation.

If you prefer HACS, this is the right direction. HACS distributes the integration only. It does not run the backend container for you.

## HACS status

The repo now has the root `hacs.json` expected by HACS custom repositories.

Remaining HACS packaging constraints:

- The repository must be public on GitHub for HACS to install it.
- If you want to pursue HACS default-store inclusion later, add brand assets, HACS validation, Hassfest, and GitHub releases.

HACS references:

- https://www.hacs.xyz/docs/publish/start/
- https://www.hacs.xyz/docs/publish/integration/

## Installation model

### 1. Run the backend

Start the API, database, migrations, and ingestion worker:

```bash
docker compose up --build
```

The API will be available at `http://localhost:${GPSTRACK_API_PORT:-8000}` by default.

### 2. Install the Home Assistant integration

Once the repo is on public GitHub, add it to HACS as a custom repository of type `Integration`, then install `GpsTrack`.

Current integration behavior:

- config entry asks for backend base URL
- optional access token
- configurable polling interval
- creates one tracker entity per tracked member
- exposes battery, place, and last-seen sensors

### 3. Connect Home Assistant to the backend

In Home Assistant, configure the integration with the backend URL. The integration polls:

- `/api/v1/home-assistant/summary`

The backend remains the history engine; the custom integration is the Home Assistant-facing wrapper.

## Local development

1. Copy `.env.example` to `.env` if you want to override defaults.
2. Start PostGIS, run migrations, and boot the API:

```bash
docker compose up --build
```

3. The API will be available at `http://localhost:${GPSTRACK_API_PORT:-8000}`.

## Backend verification

From `backend/`:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest
```

## Current branch scope

This branch currently provides:

- FastAPI routes for health, members, member history/timeline/stops/trips/safety, and places
- a Home Assistant summary endpoint for integration polling
- Alembic-backed schema migration flow
- SQLAlchemy/PostGIS domain model for family location history
- Home Assistant snapshot + websocket ingestion with auto-discovered trackers
- reverse geocoded places plus safe-zone-derived events
- derived trips, trip routes, stop summaries, and daily summaries
- a Home Assistant custom integration scaffold with config flow, coordinator, tracker, and sensors

Not implemented yet:

- Home Assistant dashboard or panel UI
- Home Assistant-native auth, ingress, or session handling
- production packaging choice if you want Home Assistant to also manage backend runtime

## Home Assistant ingestion

For live ingestion, enable the worker and provide a Home Assistant websocket URL plus long-lived access token. On startup the worker imports current coordinate-bearing `device_tracker.*` states from `/api/states`, then stays subscribed to websocket `state_changed` events.

Optional overrides:

- `GPSTRACK_HOME_ASSISTANT_BOOTSTRAP_MEMBERS` can pre-seed member metadata such as child/parent classification.
- Discovered devices can be hidden later through the member device ignore API instead of removing them from config.

## Database lifecycle

Schema changes go through Alembic.

Useful commands:

```bash
cd backend
. .venv/bin/activate
alembic upgrade head
python -m app.workers.retention
python -m app.workers.home_assistant
```

## Next-step planning

See [docs/architecture.md](/root/gpstrack/docs/architecture.md) for the current architecture and [docs/home-assistant-roadmap.md](/root/gpstrack/docs/home-assistant-roadmap.md) for the branch assessment and recommended next slices.
