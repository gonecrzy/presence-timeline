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
2. Start PostGIS and the API:

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
- SQLAlchemy/PostGIS domain model
- Provider abstraction for pluggable location sources
- Home Assistant event normalizer boundary
- Docker Compose runtime for API + PostGIS

Not implemented yet:

- Auth and family login flow
- Persistent ingestion worker
- Trip computation jobs
- Home Assistant dashboard publishing
- Android app
