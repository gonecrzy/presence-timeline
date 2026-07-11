# GpsTrack

Private, self-hosted Home Assistant location history service and dashboard backend.

This branch is the Home Assistant-focused fork of the project. The Android app work is intentionally left behind on `feat/backend-foundation`.

## Repository layout

- `backend/`: FastAPI service, normalized domain models, Home Assistant provider, and tests
- `docs/`: architecture notes and branch roadmap
- `docker-compose.yml`: local API + PostGIS runtime

## Principles

- Home Assistant is the live event source.
- This service owns normalized history, derived trips, stop summaries, places, and safety events.
- The next product surface should be Home Assistant native: integration hooks, dashboard data, and HA-friendly UI delivery.

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
- Alembic-backed schema migration flow
- SQLAlchemy/PostGIS domain model for family location history
- Home Assistant snapshot + websocket ingestion with auto-discovered trackers
- Reverse geocoded places plus safe-zone-derived events
- Derived trips, trip routes, stop summaries, and daily summaries
- Docker Compose runtime for local development

Not implemented yet:

- Home Assistant custom integration packaging and config flow
- Home Assistant dashboard or panel UI
- Home Assistant-native auth, ingress, or session handling
- Production packaging choices for long-running ingestion plus durable storage

## Home Assistant ingestion

For live ingestion, enable the worker and provide a Home Assistant websocket URL plus long-lived access token. On startup the worker imports current coordinate-bearing `device_tracker.*` states from `/api/states`, then stays subscribed to websocket `state_changed` events.

Optional overrides:

- `GPSTRACK_HOME_ASSISTANT_BOOTSTRAP_MEMBERS` can pre-seed member metadata such as child/parent classification.
- Discovered devices can be hidden later through the member device ignore API instead of removing them from config.

Run the stack with:

```bash
docker compose up --build
```

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
