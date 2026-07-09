# GpsTrack

Private, self-hosted, Android-first family location tracking.

This repository currently contains the backend foundation:

- `backend/`: FastAPI service, normalized domain models, provider seams, tests
- `android/`: Android-first parent app scaffold targeting the backend API
- `docs/`: architecture notes and implementation constraints
- `docker-compose.yml`: local API + PostGIS runtime

## Principles

- Home Assistant is the live source of truth today, but the backend owns normalized history.
- The mobile app consumes only our API and never sees Home Assistant internals.
- Every feature must answer one of three questions: where, when, or is safe.

## Local development

1. Copy `.env.example` to `.env` if you want to override defaults.
2. Start PostGIS, run migrations, and boot the API:

```bash
docker compose up --build
```

3. The API will be available at `http://localhost:${GPSTRACK_API_PORT:-8000}`.

## Android scaffold

The Android app currently targets local-first development with a configurable backend base URL and open auth mode.

See [android/README.md](/root/gpstrack/android/README.md) for:

- SDK prerequisites
- local backend URL setup
- local debug build instructions
- release APK publishing to git-hosted release targets

## Backend verification

From `backend/`:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest
```

## Current scope

This first milestone provides:

- FastAPI app scaffold with health and member routes
- Alembic-backed schema migration flow
- SQLAlchemy/PostGIS domain model
- Provider abstraction for pluggable location sources
- Open-by-default auth seam that can switch to OAuth/OIDC later
- Home Assistant event normalizer boundary
- Home Assistant snapshot + event ingestion worker with auto-discovered trackers
- Retention cleanup worker for expiring stored history
- Family places and geofence-derived safety events
- Derived trips and daily summaries from raw point history
- Docker Compose runtime for API + PostGIS

Not implemented yet:

- Real family login flow
- Home Assistant dashboard publishing
- Android app

## Auth posture

The API currently runs in `open` auth mode for early development. Protected app routes already flow through a central auth dependency so they can later switch to an external OIDC provider such as Authentik without changing every route surface.

Planned future mode:

- `GPSTRACK_AUTH_MODE=oidc`
- issuer and client configuration via `.env`
- backend-issued family scoping derived from verified identity claims

## Home Assistant discovery

For live ingestion, enable the worker and provide a Home Assistant websocket URL plus long-lived access token. On startup the worker imports current coordinate-bearing `device_tracker.*` states from `/api/states`, then stays subscribed to websocket `state_changed` events.

Optional overrides:

- `GPSTRACK_HOME_ASSISTANT_BOOTSTRAP_MEMBERS` can still pre-seed known metadata such as child/parent classification.
- Discovered devices can be hidden later through the member device ignore API instead of removing them from config.

Then run the API and ingestion worker:

```bash
docker compose up --build
```

## Database lifecycle

Schema changes now go through Alembic.

Useful commands:

```bash
cd backend
. .venv/bin/activate
alembic upgrade head
python -m app.workers.retention
```
