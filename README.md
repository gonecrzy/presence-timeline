# Presence Timeline

Presence Timeline is a private, self-hosted Home Assistant location history stack. Home Assistant supplies live tracker events, while this repo keeps durable history, derives trips and stops, enriches places, and exposes the data back to Home Assistant through entities and a custom panel.

The current product shape is a sidecar model:

- Home Assistant installs `custom_components/presence_timeline/` through HACS or as a manual custom integration.
- The backend runs separately with Docker Compose and is reached over HTTP by the integration.
- PostgreSQL/PostGIS stores normalized location history, derived stays, trips, daily summaries, safety events, places, and reverse-geocode cache rows.
- Background workers handle Home Assistant ingestion and reverse geocoding so API reads do not block on external lookups.

## Repository Layout

- `backend/`: FastAPI service, SQLAlchemy/PostGIS models, Alembic migrations, Home Assistant provider, workers, and pytest suite.
- `custom_components/presence_timeline/`: Home Assistant custom integration, device tracker and sensor entities, panel API proxy, and frontend panel assets.
- `custom_components/presence_timeline/frontend/`: Browser panel source, map frame, utility modules, and Node test files.
- `docs/`: architecture notes and roadmap.
- `docker-compose.yml`: local API, PostGIS, migrator, ingestion worker, and geocoder worker runtime.
- `AGENTS.md`: repo-local workflow and verification rules for Codex-style agents.

## Current Capabilities

- FastAPI routes for health, members, member history, timeline, stops, trips, safety events, and places.
- Home Assistant summary, ingestion status, and member panel endpoints under `/api/v1/home-assistant`.
- Snapshot plus websocket ingestion from coordinate-bearing `device_tracker.*` states.
- Auto-discovery of Home Assistant trackers into backend members and devices.
- Optional bootstrap member config through `PRESENCE_TIMELINE_HOME_ASSISTANT_BOOTSTRAP_MEMBERS`.
- Device ignore support for hiding discovered trackers without removing config.
- Dedupe logic for near-duplicate stationary location samples.
- Derived stays, stop summaries, trips, trip routes, daily summaries, and safe-zone events.
- Cached reverse geocoding and address search.
- Home Assistant config flow with backend URL, optional access token, and polling interval.
- Home Assistant tracker entities, member battery/place/last-seen sensors, and ingestion diagnostic sensors.
- Home Assistant sidebar panel with current member status, map/history views, timeline, stops, and backend status.

## Current Limitations

- Backend auth defaults to `open` local-development mode. OIDC settings exist, but OIDC authentication is not implemented.
- The integration distributes the Home Assistant custom component only; HACS does not run the backend container.
- Production packaging is still undecided for users who want Home Assistant to manage the backend runtime.
- Home Assistant-native ingress/session trust boundaries are not implemented yet.
- HACS default-store readiness still needs brand assets, HACS validation, Hassfest, releases, and public repository hosting.

## Run The Backend

Copy `.env.example` to `.env` if you want to override defaults, then start the local stack:

```bash
docker compose up --build
```

The API is available at:

```text
http://localhost:${PRESENCE_TIMELINE_API_PORT:-8000}
```

The Compose stack includes:

- `db`: PostGIS database with persistent external volume `gpstrack_postgis_data`.
- `migrator`: one-shot Alembic migration job.
- `api`: FastAPI app served with Uvicorn.
- `ingestor`: Home Assistant snapshot and websocket ingestion worker.
- `geocoder`: reverse-geocode cache backfill worker.

## Install The Home Assistant Integration

For manual install, copy or mount `custom_components/presence_timeline/` into Home Assistant's `custom_components/` directory and restart Home Assistant.

For HACS custom repository install, the repository must be public and added as an `Integration` repository. The root `hacs.json` and integration `manifest.json` are present for that path.

After installation, add the `Presence Timeline` integration in Home Assistant and configure:

- backend base URL
- optional access token
- polling interval, from 15 to 3600 seconds

The integration polls the backend summary endpoint and proxies panel requests through Home Assistant:

- `/api/v1/home-assistant/summary`
- `/api/v1/home-assistant/status`
- `/api/v1/home-assistant/members/{member_id}/panel`

## Home Assistant Ingestion

To ingest live Home Assistant tracker data, enable the worker and provide a websocket URL plus long-lived access token:

```env
PRESENCE_TIMELINE_ENABLE_HOME_ASSISTANT_INGESTION=true
PRESENCE_TIMELINE_HOME_ASSISTANT_WS_URL=ws://homeassistant.local:8123/api/websocket
PRESENCE_TIMELINE_HOME_ASSISTANT_ACCESS_TOKEN=replace-me
```

On startup, the worker imports current coordinate-bearing `device_tracker.*` states from `/api/states`, then subscribes to websocket `state_changed` events. Mirrored Presence Timeline tracker entities are ignored so the integration does not ingest its own output.

Reverse geocoding runs separately:

- ingestion queues rounded coordinates into the cache table
- the `geocoder` worker resolves pending cache rows
- API responses prefer saved places, then cached geocode labels, then coordinate fallback

## Development

Backend setup from `backend/`:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
```

Backend verification from `backend/`:

```bash
pytest
ruff check .
```

Frontend panel tests from the repo root:

```bash
node --test custom_components/presence_timeline/frontend/*.test.mjs
```

Compose verification from the repo root:

```bash
docker compose config
```

## Database Lifecycle

Schema changes go through Alembic under `backend/alembic/versions/`.

Useful backend commands:

```bash
cd backend
. .venv/bin/activate
alembic upgrade head
python -m app.workers.retention
python -m app.workers.home_assistant
python -u -m app.workers.reverse_geocoding
```

## Planning Docs

See [docs/architecture.md](/root/gpstrack/docs/architecture.md) for the current architecture and [docs/home-assistant-roadmap.md](/root/gpstrack/docs/home-assistant-roadmap.md) for branch assessment and next slices.
