# GpsTrack

Private, self-hosted, Android-first family location tracking.

This repository currently contains the backend foundation:

- `backend/`: FastAPI service, normalized domain models, provider seams, tests
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

3. The API will be available at `http://localhost:8000`.

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
- Config-driven Home Assistant member bootstrap and ingestion worker
- Retention cleanup worker for expiring stored history
- Docker Compose runtime for API + PostGIS

Not implemented yet:

- Real family login flow
- Trip computation jobs
- Home Assistant dashboard publishing
- Android app

## Auth posture

The API currently runs in `open` auth mode for early development. Protected app routes already flow through a central auth dependency so they can later switch to an external OIDC provider such as Authentik without changing every route surface.

Planned future mode:

- `GPSTRACK_AUTH_MODE=oidc`
- issuer and client configuration via `.env`
- backend-issued family scoping derived from verified identity claims

## Home Assistant bootstrap

For live ingestion, seed the initial member-to-entity mapping with `GPSTRACK_HOME_ASSISTANT_BOOTSTRAP_MEMBERS` as JSON in `.env`:

```json
[{"display_name":"Sam","entity_id":"device_tracker.sam_phone","is_child":true,"device_label":"Sam Phone"}]
```

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
